from django import forms
from search_content_type import SearchContentType
from digipal.models import *
from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.db.models import Q

class SearchManuscripts(SearchContentType):

    def get_fields_info(self):
        from whoosh.fields import TEXT, ID
        from whoosh.analysis import StemmingAnalyzer, SimpleAnalyzer
        stem_ana = StemmingAnalyzer()        
        simp_ana = SimpleAnalyzer()
        ret = super(SearchManuscripts, self).get_fields_info()
        ret['locus'] = {'whoosh': {'type': TEXT(analyzer=simp_ana), 'name': 'locus'}}
        ret['current_item__shelfmark'] = {'whoosh': {'type': TEXT(analyzer=simp_ana), 'name': 'shelfmark'}}
        ret['current_item__repository__name'] = {'whoosh': {'type': TEXT, 'name': 'repository'}, 'advanced': True}
        ret['historical_item__catalogue_number'] = {'whoosh': {'type': TEXT(analyzer=simp_ana), 'name': 'index', 'boost': 2.0}, 'advanced': True}
        ret['historical_item__description__description'] = {'whoosh': {'type': TEXT(analyzer=stem_ana), 'name': 'description'}, 'long_text': True}
        ret['historical_item__date'] = {'whoosh': {'type': TEXT, 'name': 'date'}, 'advanced': True}
        return ret

    def set_record_view_context(self, context):
        super(SearchManuscripts, self).set_record_view_context(context)
        context['item_part'] = ItemPart.objects.get(id=context['id'])
        context['pages'] = context['item_part'].pages.all().order_by('locus')
        context['hands'] = context['item_part'].hand_set.all().order_by('item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'descriptions__description','id')
    
    @property
    def form(self):
        return FilterManuscripts()
    
    @property
    def key(self):
        return 'manuscripts'
    
    @property
    def label(self):
        return 'Manuscripts'
    
    @property
    def label_singular(self):
        return 'Manuscript'
    
    def get_model(self):
        return ItemPart

    def build_queryset_django(self, request, term):
        type = self.key
        query_manuscripts = ItemPart.objects.filter(
                Q(locus__contains=term) | \
                Q(current_item__shelfmark__icontains=term) | \
                Q(current_item__repository__name__icontains=term) | \
                Q(historical_item__catalogue_number__icontains=term) | \
                Q(historical_item__description__description__icontains=term))
        
        repository = request.GET.get('repository', '')
        index_manuscript = request.GET.get('index', '')
        date = request.GET.get('date', '')
        
        self.is_advanced = repository or index_manuscript or date
    
        if date:
            query_manuscripts = query_manuscripts.filter(historical_item__date=date)
        if repository:
            query_manuscripts = query_manuscripts.filter(current_item__repository__name=repository)
        if index_manuscript:
            query_manuscripts = query_manuscripts.filter(historical_item__catalogue_number=index_manuscript)
            
        self._queryset = query_manuscripts.distinct().order_by('historical_item__catalogue_number', 'id')
        
        return self._queryset

class FilterManuscripts(forms.Form):

    index = forms.ModelChoiceField(
        queryset = HistoricalItem.objects.values_list('catalogue_number', flat=True).distinct(),
        widget = Select(attrs={'id':'index-select', 'class':'chzn-select', 'data-placeholder':"Choose an Index"}),
        label = "",
        empty_label = "Index",
        required = False)

    repository = forms.ChoiceField(
        choices = [("", "Repository")] + [(m.name, m.human_readable()) for m in Repository.objects.all().order_by('name').distinct()],
        label = "",
        required = False,
        widget = Select(attrs={'id':'placeholder-select', 'class':'chzn-select', 'data-placeholder':"Choose a Repository"}),
        initial = "Repository",
    )

    date = forms.ModelChoiceField(
        queryset = Date.objects.values_list('date', flat=True).order_by('date').distinct(),
        widget = Select(attrs={'id':'date-select', 'class':'chzn-select', 'data-placeholder':"Choose a Date"}),
        label = "",
        empty_label = "Date",
        required = False)

