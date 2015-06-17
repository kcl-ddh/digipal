from django import forms
from search_content_type import SearchContentType, get_form_field_from_queryset
from digipal.models import *
from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.db.models import Q

from digipal.utils import sorted_natural
class FilterScribes(forms.Form):
    scribe = get_form_field_from_queryset(Scribe.objects.values_list('name', flat=True).order_by('name').distinct(), 'Scribe')
    # Was previously called 'scriptorium'
    scriptorium = get_form_field_from_queryset(Scribe.objects.values_list('scriptorium__name', flat=True).order_by('scriptorium__name').distinct(), 'Place')
    # TODO: order the dates
    scribe_date = get_form_field_from_queryset(sorted_natural(list(Scribe.objects.filter(date__isnull=False).values_list('date', flat=True).order_by('date').distinct())), 'Date')
    chartype = get_form_field_from_queryset(Scribe.objects.values_list('idiographs__allograph__character__ontograph__ontograph_type__name', flat= True).order_by('idiographs__allograph__character__ontograph__ontograph_type__name').distinct(), 'Character Type', aid='chartype')
    character = get_form_field_from_queryset(Scribe.objects.values_list('idiographs__allograph__character__name', flat=True).order_by('idiographs__allograph__character__ontograph__sort_order').distinct(), 'Character', aid='character')
    component = get_form_field_from_queryset(Scribe.objects.values_list('idiographs__idiographcomponent__component__name', flat=True).order_by('idiographs__idiographcomponent__component__name').distinct(), 'Component')
    feature = get_form_field_from_queryset(Scribe.objects.values_list('idiographs__idiographcomponent__features__name', flat=True).order_by('idiographs__idiographcomponent__features__name').distinct(), 'Feature')

class SearchScribes(SearchContentType):

    def get_fields_info(self):
        ''' See SearchContentType.get_fields_info() for a description of the field structure '''
        
        ret = super(SearchScribes, self).get_fields_info()
        ret['name'] = {'whoosh': {'type': self.FT_CODE, 'name': 'scribe', 'boost': 3.0}, 'advanced': True}
        ret['scriptorium__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'scriptorium'}, 'advanced': True}
        ret['date'] = {'whoosh': {'type': self.FT_CODE, 'name': 'scribe_date', 'boost': 1.0}, 'advanced': True}
        
        ret['hands__item_part__current_item__shelfmark'] = {'whoosh': {'type': self.FT_CODE, 'name': 'shelfmark', 'boost': 0.3}}
        
        ret['hands__item_part__current_item__repository__place__name, hands__item_part__current_item__repository__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'repository', 'boost': 0.3}, 'advanced': True}
        ret['hands__item_part__historical_items__catalogue_number'] = {'whoosh': {'type': self.FT_CODE, 'name': 'index', 'boost': 0.3}, 'advanced': True}
        # TODO: display this field on the front-end
        #ret['historical_items__description__description'] = {'whoosh': {'type': TEXT(analyzer=stem_ana, stored=True), 'name': 'description'}, 'long_text': True}

        # we leave those fields out of the whoosh index otherwise the index would be far too long (> 100K)
        # filtering is done using the DB
        ret['idiographs__allograph__character__ontograph__ontograph_type__name'] = {'whoosh': {'type': self.FT_ID, 'name': 'chartype', 'ignore': True}, 'advanced': True}
        ret['idiographs__allograph__character__name'] = {'whoosh': {'type': self.FT_ID, 'name': 'character', 'ignore': True}, 'advanced': True}
        #ret['idiographs__allograph__allograph_components__component__name'] = {'whoosh': {'type': self.FT_CODE, 'name': 'component', 'ignore': True}, 'advanced': True}
        #ret['idiographs__allograph__allograph_components__component__features__name'] = {'whoosh': {'type': self.FT_CODE, 'name': 'feature', 'ignore': True}, 'advanced': True}
        ret['idiographs__idiographcomponent__component__name'] = {'whoosh': {'type': self.FT_CODE, 'name': 'component', 'ignore': True}, 'advanced': True}
        ret['idiographs__idiographcomponent__features__name'] = {'whoosh': {'type': self.FT_CODE, 'name': 'feature', 'ignore': True}, 'advanced': True}

        # MS
        ret['hands__item_part__historical_items__date'] = {'whoosh': {'type': self.FT_CODE, 'name': 'ms_date'}, 'advanced': True}
        ret['hands__item_part__group__historical_items__name, hands__item_part__historical_items__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'hi'}}
        
        # Hands
        ret['hands__assigned_place__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'hand_place'}, 'advanced': True}
        ret['hands__assigned_date__date'] = {'whoosh': {'type': self.FT_CODE, 'name': 'hand_date'}, 'advanced': True}
        ret['hands__script__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'script'}, 'advanced': True}
        
        return ret

    def get_sort_fields(self):
        ''' returns a list of django field names necessary to sort the results '''
        return ['name']

    def set_record_view_context(self, context, request):
        super(SearchScribes, self).set_record_view_context(context, request)
        context['scribe'] = Scribe.objects.get(id=context['id'])
        # TODO: naming is confusing here, check if the code still work
        context['idiograph_components'] = Idiograph.objects.filter(scribe_id=context['scribe'].id)
        # No longer needed?
        #context['graphs'] = Graph.objects.filter(idiograph__in=context['idiograph_components'])
        context['pages'] = []
        
        images = Image.filter_permissions_from_request(Image.objects.filter(hands__scribe=context['scribe']).prefetch_related('hands', 'annotation_set'), request)
        context['images'] = Image.sort_query_set_by_locus(images)
        
#         for hand in context['scribe'].hands.all():
#             for image in hand.images.all():
#                 context['pages'].append({'hand': hand, 'image': image})
    
    def get_model(self):
        return Scribe

    def get_form(self, request=None):
        initials = None
        if request:
            initials = request.GET
        return FilterScribes(initials)
    
    @property
    def key(self):
        return 'scribes'
    
    @property
    def label(self):
        return 'Scribes'
    
    @property
    def label_singular(self):
        return 'Scribe'
    
    def bulk_load_records(self, recordids):
        return (self.get_model()).objects.select_related('scriptorium').prefetch_related('hands__images').in_bulk(recordids)
    
    def _build_queryset_django(self, request, term):
        type = self.key
        query_scribes = Scribe.objects.filter(
                    Q(name__icontains=term) | \
                    Q(scriptorium__name__icontains=term) | \
                    Q(date__icontains=term) | \
                    Q(hand__item_part__current_item__shelfmark__icontains=term) | \
                    Q(hand__item_part__current_item__repository__name__icontains=term) | \
                    Q(hand__item_part__historical_item__catalogue_number__icontains=term))
    
        name = request.GET.get('name', '')
        scriptorium = request.GET.get('scriptorium', '')
        date = request.GET.get('date', '')
        character = request.GET.get('character', '')
        component = request.GET.get('component', '')
        feature = request.GET.get('feature', '')
        
        self.is_advanced = name or scriptorium or date or character or component or feature
        
        # TODO: the filters should be additive rather than replacing the previous one
        if name:
            query_scribes = query_scribes.filter(name=name)
        if scriptorium:
            query_scribes = query_scribes.filter(scriptorium__name=scriptorium)
        if date:
            query_scribes = query_scribes.filter(date=date)
        if character:
            query_scribes = query_scribes.filter(idiographs__allograph__character__name=character)
        if component:
            query_scribes = query_scribes.filter(idiographs__allograph__allographcomponent__component__name=component)
        if feature:
            query_scribes = query_scribes.filter(idiographs__allograph__allographcomponent__component__features__name=feature)
    
        self._queryset = query_scribes.distinct().order_by('name')
        
        return self._queryset

def scribe_details(request):
    """
    Get Idiograph, Graph, and Image data for a Scribe,
    for display in a record view
    """
    scribe = Scribe.objects.get(id=request.GET.get('id'))
    idiographs = Idiograph.objects.filter(scribe=scribe.id)
    graphs = Graph.objects.filter(idiograph__in=idiographs)
    return idiographs, graphs
