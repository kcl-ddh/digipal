from django import forms
from search_content_type import SearchContentType
from digipal.models import *
from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.db.models import Q

class SearchScribes(SearchContentType):

    def get_fields_info(self):
        ret = super(SearchScribes, self).get_fields_info()
        ret['name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'name'}, 'advanced': True}
        ret['scriptorium__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'place'}, 'advanced': True}
        ret['date'] = {'whoosh': {'type': self.FT_CODE, 'name': 'date'}, 'advanced': True}
        ret['hands__item_part__current_item__shelfmark'] = {'whoosh': {'type': self.FT_CODE, 'name': 'shelfmark'}}
        ret['hands__item_part__current_item__repository__place__name, hands__item_part__current_item__repository__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'repository'}}
        ret['hands__item_part__historical_items__catalogue_number'] = {'whoosh': {'type': self.FT_CODE, 'name': 'index', 'boost': 1.0}}
        # TODO: display this field on the front-end
        #ret['historical_items__description__description'] = {'whoosh': {'type': TEXT(analyzer=stem_ana, stored=True), 'name': 'description'}, 'long_text': True}

        # we leave those fields out of the whoosh index otherwise the index would be far too long (> 100K)
        # filtering is done using the DB
        ret['idiographs__allograph__character__name'] = {'whoosh': {'type': self.FT_ID, 'name': 'character', 'ignore': True}, 'advanced': True}
        ret['idiographs__allograph__allograph_components__component__name'] = {'whoosh': {'type': self.FT_CODE, 'name': 'component', 'ignore': True}, 'advanced': True}
        ret['idiographs__allograph__allograph_components__component__features__name'] = {'whoosh': {'type': self.FT_CODE, 'name': 'feature', 'ignore': True}, 'advanced': True}
        return ret

    def set_record_view_context(self, context, request):
        super(SearchScribes, self).set_record_view_context(context, request)
        context['scribe'] = Scribe.objects.get(id=context['id'])
        # TODO: naming is confusing here, check if the code still work
        context['idiograph_components'] = Idiograph.objects.filter(scribe_id=context['scribe'].id)
        # No longer needed?
        #context['graphs'] = Graph.objects.filter(idiograph__in=context['idiograph_components'])
    
    def get_model(self):
        return Scribe

    @property
    def form(self):
        return FilterScribes()
    
    @property
    def key(self):
        return 'scribes'
    
    @property
    def label(self):
        return 'Scribes'
    
    @property
    def label_singular(self):
        return 'Scribe'    
    
    def build_queryset_django(self, request, term):
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

class FilterScribes(forms.Form):
    name = forms.ModelChoiceField(
        queryset = Scribe.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'name-select', 'class':'chzn-select', 'data-placeholder':"Choose a Name"}),
        label = "",
        empty_label = "Name",
        required = False)

    # Was previously called 'scriptorium'
    place = forms.ModelChoiceField(
        queryset = Institution.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'place-select', 'class':'chzn-select', 'data-placeholder':"Choose a Scriptorium"}),
        empty_label = "Scriptorium",
        label = "",
        required = False)

    date = forms.ModelChoiceField(
        queryset = Date.objects.values_list('date', flat=True).order_by('date').distinct(),
        widget = Select(attrs={'id':'date-select', 'class':'chzn-select', 'data-placeholder':"Choose a Date"}),
        label = "",
        empty_label = "Date",
        required = False)

    character = forms.ModelChoiceField(
        queryset = Character.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'character-select', 'class':'chzn-select', 'data-placeholder':"Choose a Character"}),
        label = "",
        empty_label = "Character",
        required = False)

    component = forms.ModelChoiceField(
        queryset = Component.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'component-select', 'class':'chzn-select', 'data-placeholder':"Choose a Component"}),
        label = "",
        empty_label = "Component",
        required = False)

    feature = forms.ModelChoiceField(
        queryset = Feature.objects.values_list('name', flat=True).order_by('name').distinct(),
        widget = Select(attrs={'id':'feature-select', 'class':'chzn-select', 'data-placeholder':"Choose a Feature"}),
        label = "",
        empty_label = "Feature",
        required = False)

def scribe_details(request):
    """
    Get Idiograph, Graph, and Image data for a Scribe,
    for display in a record view
    """
    scribe = Scribe.objects.get(id=request.GET.get('id'))
    idiographs = Idiograph.objects.filter(scribe=scribe.id)
    graphs = Graph.objects.filter(
        idiograph__in=idiographs)
    return idiographs, graphs
