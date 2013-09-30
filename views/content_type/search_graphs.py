from django import forms
from search_content_type import SearchContentType
from digipal.models import *
from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.db.models import Q

'''
    TODO: to be implemented. See the allographHandSearch(Graphs)() view. 
'''

class SearchGraphs(SearchContentType):

    def set_record_view_context(self, context):
        from django.utils.datastructures import SortedDict
        p = Hand.objects.get(id=context['id'])
        #c = p.graph_set.model.objects.get(id=p.id)
        annotation_list = Annotation.objects.filter(graph__hand__id=p.id)
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
        context['result'] = p
    
    @property
    def form(self):
        return FilterGraphs()
    
    @property
    def key(self):
        return 'graphs'
    
    @property
    def label(self):
        return 'Graphs'

    def build_queryset(self, request, term):
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
            repository_place = repository.split(', ')[0]
            repository_name = repository.split(', ')[1]
            query_hands = query_hands.filter(item_part__current_item__repository__name=repository_name, item_part__current_item__repository__place__name=repository_place)
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

class FilterGraphs(forms.Form):
    scribes = forms.ModelChoiceField(
        queryset = Scribe.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'scribes-select', 'class':'chzn-select', 'data-placeholder':'Choose a Scribe'}),
        label = "",
        empty_label = "Scribe",
        required = False)

    repository = forms.ChoiceField(
        choices = [("", "Repository")] + [(m.name, m.human_readable()) for m in Repository.objects.all().order_by('name').distinct()],
        label = "",
        required = False,
        widget = Select(attrs={'id':'placeholder-select', 'class':'chzn-select', 'data-placeholder':"Choose a Repository"}),
        initial = "Repository",
    )


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

