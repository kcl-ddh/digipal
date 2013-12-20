from django import forms
from search_content_type import SearchContentType
from digipal.models import *
from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.db.models import Q

class SearchHands(SearchContentType):

    def get_fields_info(self):
        ''' See SearchContentType.get_fields_info() for a description of the field structure '''
        
        ret = super(SearchHands, self).get_fields_info()
        # TODO: new search field
        ret['label'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'label'}}
        ret['descriptions__description'] = {'whoosh': {'type': self.FT_LONG_FIELD, 'name': 'description', 'boost': 0.3}, 'long_text': True}
        ret['scribe__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'scribes', 'boost': 0.3}, 'advanced': True}
        ret['assigned_place__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'place'}, 'advanced': True}
        ret['item_part__current_item__shelfmark'] = {'whoosh': {'type': self.FT_CODE, 'name': 'shelfmark', 'boost': 3.0}}
        ret['item_part__current_item__repository__place__name, item_part__current_item__repository__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'repository'}, 'advanced': True}
        ret['item_part__historical_items__catalogue_number'] = {'whoosh': {'type': self.FT_CODE, 'name': 'index', 'boost': 2.0}}
        ret['assigned_date__date'] = {'whoosh': {'type': self.FT_CODE, 'name': 'date'}, 'advanced': True}
        return ret

    def get_sort_fields(self):
        ''' returns a list of django field names necessary to sort the results ''' 
        return ['item_part__current_item__repository__place__name', 'item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'num']

    def set_record_view_context(self, context, request):
        super(SearchHands, self).set_record_view_context(context, request)

        from django.utils.datastructures import SortedDict
        current_hand = Hand.objects.get(id=context['id'])
        
        #c = current_hand.graphs_set.model.objects.get(id=current_hand.id)
        annotation_list = Annotation.objects.filter(graph__hand__id=current_hand.id)
        data = SortedDict()
        for annotation in annotation_list:
            hand = annotation.graph.hand
            allograph_name = annotation.graph.idiograph.allograph

            if hand in data:
                if allograph_name not in data[hand]:
                    data[hand][allograph_name] = []
            else:
                data[hand] = SortedDict()
                data[hand][allograph_name] = []

            data[hand][allograph_name].append(annotation)
            
            context['data'] = data
        
        # GN: ???
        context['can_edit'] = request and has_edit_permission(request, Annotation)

        images = current_hand.images.all()
        if images.count():
            image = images[0]            
            context['width'], context['height'] = image.dimensions()
            context['image_erver_url'] = image.zoomify
        
        context['hands_page'] = True
        context['result'] = current_hand
    
    @property
    def form(self):
        return FilterHands()
    
    @property
    def key(self):
        return 'hands'
    
    @property
    def label(self):
        return 'Hands'
    
    @property
    def label_singular(self):
        return 'Hand'

    def build_queryset_django(self, request, term):
        type = self.key
        query_hands = Hand.objects.filter(
                    Q(descriptions__description__icontains=term) | \
                    Q(scribe__name__icontains=term) | \
                    Q(assigned_place__name__icontains=term) | \
                    Q(assigned_date__date__icontains=term) | \
                    Q(item_part__current_item__shelfmark__icontains=term) | \
                    Q(item_part__current_item__repository__name__icontains=term) | \
                    Q(item_part__historical_items__catalogue_number__icontains=term))
        
        scribes = request.GET.get('scribes', '')
        repository = request.GET.get('repository', '')
        place = request.GET.get('place', '')
        date = request.GET.get('date', '')
        
        self.is_advanced = repository or scribes or place or date
        if scribes:
            query_hands = query_hands.filter(scribe__name=scribes)
        if repository:
            query_hands = query_hands.filter(item_part__current_item__repository__name=repository)
        if place:
            query_hands = query_hands.filter(assigned_place__name=place)
        if date:
            query_hands = query_hands.filter(assigned_date__date=date)
        
        #context['hands'] = query_hands.distinct().order_by('scribe__name','id')
        query_hands = query_hands.distinct()
        if repository or scribes or place or date:
            query_hands = query_hands.order_by('scribe__name','id')
        else:
            query_hands = query_hands.order_by('item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'descriptions__description','id')
    
        self._queryset = query_hands
        
        return self._queryset

class FilterHands(forms.Form):
    scribes = forms.ModelChoiceField(
        queryset = Scribe.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'scribes-select', 'class':'chzn-select', 'data-placeholder':'Choose a Scribe'}),
        label = "",
        empty_label = "Scribe",
        required = False)

    repository = forms.ChoiceField(
        choices = [("", "Repository")] + [(m.human_readable(), m.human_readable()) for m in Repository.objects.all().order_by('name').distinct()],
        label = "",
        required = False,
        widget = Select(attrs={'id':'placeholder-select', 'class':'chzn-select', 'data-placeholder':"Choose a Repository"}),
        initial = "Repository",)

    place = forms.ModelChoiceField(
        queryset = Place.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'place-select', 'class':'chzn-select', 'data-placeholder':"Choose a Place"}),
        label = "",
        empty_label = "Place",
        required = False)

    date = forms.ModelChoiceField(
        queryset = Date.objects.values_list('date', flat=True).order_by('date').distinct(),
        widget = Select(attrs={'id':'date-select', 'class':'chzn-select', 'data-placeholder':"Choose a Date"}),
        label = "",
        empty_label = "Date",
        required = False)

