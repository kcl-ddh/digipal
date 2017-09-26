from django import forms
from search_content_type import SearchContentType, get_form_field_from_queryset
from digipal.models import *
from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.db.models import Q

from digipal.utils import sorted_natural


class FilterHands(forms.Form):
    scribe = get_form_field_from_queryset(Hand.objects.values_list(
        'scribe__name', flat=True).order_by('scribe__name').distinct(), 'Scribe')
    repository = get_form_field_from_queryset([m.human_readable() for m in Repository.objects.filter(
        currentitem__itempart__hands__isnull=False).order_by('place__name', 'name').distinct()], 'Repository')
    hand_place = get_form_field_from_queryset(Hand.objects.values_list(
        'assigned_place__name', flat=True).order_by('assigned_place__name').distinct(), 'Place')
    # renamed from date
    hand_date = get_form_field_from_queryset(Hand.objects.all().filter(assigned_date__isnull=False).values_list(
        'assigned_date__date', flat=True).order_by('assigned_date__sort_order').distinct(), 'Date')


class SearchHands(SearchContentType):

    def get_fields_info(self):
        ''' See SearchContentType.get_fields_info() for a description of the field structure '''

        ret = super(SearchHands, self).get_fields_info()
        # TODO: new search field
        ret['label'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'label'}}
        ret['descriptions__description'] = {'whoosh': {
            'type': self.FT_LONG_FIELD, 'name': 'description', 'boost': 0.3}, 'long_text': True}
        # Use FT_CODE instead of FT_TITLE because we have numbers in the field
        # e.g. "Digipal Hand 1" woudln't return anything with FT_TITLE
        ret['scribe__name'] = {'whoosh': {
            'type': self.FT_CODE, 'name': 'scribe', 'boost': 0.3}, 'advanced': True}
        # JIRA 358: we need to search by the hand name
        ret['pk'] = {'whoosh': {'type': self.FT_CODE,
                                'name': 'hand', 'format': settings.ARCHETYPE_HAND_ID_PREFIX + '%s'}}

        ret['assigned_place__name'] = {'whoosh': {
            'type': self.FT_TITLE, 'name': 'hand_place'}, 'advanced': True}
        ret['item_part__current_item__shelfmark'] = {'whoosh': {
            'type': self.FT_CODE, 'name': 'shelfmark', 'boost': 3.0}}
        ret['item_part__current_item__repository__place__name, item_part__current_item__repository__name'] = {
            'whoosh': {'type': self.FT_TITLE, 'name': 'repository'}, 'advanced': True}
        ret['item_part__historical_items__catalogue_number'] = {'whoosh': {
            'type': self.FT_CODE, 'name': 'index', 'boost': 2.0}, 'advanced': True}
        # renamed from date
        ret['assigned_date__date'] = {'whoosh': {
            'type': self.FT_CODE, 'name': 'hand_date'}, 'advanced': True}

        ret['script__name'] = {'whoosh': {
            'type': self.FT_TITLE, 'name': 'script'}, 'advanced': True}

        # MS
        ret['item_part__historical_items__date'] = {'whoosh': {
            'type': self.FT_CODE, 'name': 'ms_date'}, 'advanced': True}
        ret['item_part__group__historical_items__name, item_part__historical_items__name'] = {
            'whoosh': {'type': self.FT_TITLE, 'name': 'hi'}}

        # Scribe
        ret['scribe__scriptorium__name'] = {'whoosh': {
            'type': self.FT_TITLE, 'name': 'scriptorium'}, 'advanced': True}
        ret['scribe__date'] = {'whoosh': {
            'type': self.FT_CODE, 'name': 'scribe_date', 'boost': 1.0}, 'advanced': True}

        return ret

    def get_headings(self):
        return [
            {'label': 'Hand', 'key': 'hand', 'is_sortable': False},
            {'label': 'Repository', 'key': 'repository',
                'is_sortable': True, 'title': 'Repository and Shelfmark'},
            {'label': 'Shelfmark', 'key': 'shelfmark', 'is_sortable': False},
            {'label': 'Description', 'key': 'description', 'is_sortable': False},
            {'label': 'Place', 'key': 'description', 'is_sortable': False},
            {'label': 'Date', 'key': 'description', 'is_sortable': False},
            {'label': 'Catalogue Number', 'key': 'description', 'is_sortable': False},
        ]

    def get_default_ordering(self):
        return 'repository'

    def get_sort_fields(self):
        ''' returns a list of django field names necessary to sort the results '''
        return ['item_part__current_item__repository__place__name', 'item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'num']

    def set_record_view_context(self, context, request):
        super(SearchHands, self).set_record_view_context(context, request)

        context['can_edit'] = request and has_edit_permission(
            request, Annotation)

        from collections import OrderedDict
        current_hand = Hand.objects.get(id=context['id'])

        # hand > allograph > graph
        annotations = Annotation.objects.filter(graph__hand__id=current_hand.id).exclude_hidden(
            context['can_edit']).select_related('image', 'image__media_permission')
        data = OrderedDict()

        context['annotations_count'] = 0

        for annotation in annotations:
            if annotation.image.is_private_for_user(request):
                continue

            context['annotations_count'] += 1

            hand = annotation.graph.hand
            allograph_name = annotation.graph.idiograph.allograph

            if hand in data:
                if allograph_name not in data[hand]:
                    data[hand][allograph_name] = []
            else:
                data[hand] = OrderedDict()
                data[hand][allograph_name] = []

            data[hand][allograph_name].append(annotation)

            context['annotations_list'] = data

        # image list (filtered by permission)
        images = Image.filter_permissions_from_request(
            current_hand.images.all().prefetch_related('hands', 'annotation_set'), request)
        context['images'] = Image.sort_query_set_by_locus(images)

        if context['images'].count():
            image = context['images'][0]
            context['width'], context['height'] = image.dimensions()
            context['image_erver_url'] = image.zoomify

        context['hands_page'] = True
        context['result'] = current_hand

    def get_form(self, request=None):
        initials = None
        if request:
            initials = request.GET
        return FilterHands(initials)

    @property
    def key(self):
        return 'hands'

    @property
    def label(self):
        return 'Hands'

    @property
    def label_singular(self):
        return 'Hand'

    def bulk_load_records(self, recordids):
        return (self.get_model()).objects.select_related('item_part__current_item__repository__place', 'assigned_place', 'assigned_date').prefetch_related('images', 'item_part__historical_items__catalogue_numbers').in_bulk(recordids)
