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
        ret['historical_item__description__description'] = {'whoosh': {'type': TEXT(analyzer=stem_ana, stored=True), 'name': 'description'}, 'long_text': True}
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

    def get_records_from_ids(self, recordids):
        ret = super(SearchManuscripts, self).get_records_from_ids(recordids)
        # Generate a meaningful snippet for each description,
        # one that includes the search terms.
        # See JIRA 132. Basically we have to show a snippet of a description.
        # We choose the description with the best snippet.
        # If no match at all, we use the normal description selection.
        whoosh_dict = self.get_whoosh_dict()
        for record in ret:
            # Shoosh snippets temporary disabled, see reason below
            if 0:
                description = record.historical_item.get_display_description().description
                if whoosh_dict:
                    hit = whoosh_dict[record.id]
                    description = 'test wulfstan'
                    # This call crashes, 
                    # see https://bitbucket.org/mchaput/whoosh/issue/341/single-segment-buffer-object-expected
                    #record.description_snippet = hit.highlights('description')
                else:
                    record.description_snippet = description[0:min(len(description), 50)]
            else:
                # Do the snippeting ourselves
                snippet_length = 50
                description, location = self._get_best_description_location(record.historical_item.get_descriptions().all())
                if description is None:
                    # no match in any description, so we select the beginning of the most important description 
                    description, location = record.historical_item.get_display_description(), 0
                # get the description text
                if description:
                    text = description.description
                    # truncate around the location
                    record.description_snippet = self._truncate_text(text, location, snippet_length)
                    # add the description author (e.g. ' (G.)' for Gneuss)
                    record.description_snippet += u' (%s)' % description.source.get_authors_short()
        return ret
    
    def _get_best_description_location(self, descriptions):
        '''
            Returns the first description that matches one term in the query
            and the location of the first match in the string.
            
            TODO: prefer a description and location which contains multiple terms
                next to each other.
        '''
        desc = None
        location = 0
        terms = [t.lower() for t in self._get_query_terms() if t not in [u'or', u'and', u'not']]
        from digipal.utils import get_regexp_from_terms
        re_terms = get_regexp_from_terms(terms)
        
        if re_terms:
            # search the descriptions
            for adesc in descriptions:
                m = re.search(ur'(?ui)' + re_terms, adesc.description)
                if m:
                    location = m.start()
                    desc = adesc
                    break
        return desc, location

    def _truncate_text(self, text, location, snippet_length):
        # Select the text around the given location
        # The snippet should have snippet_length characters
        # The snippet should not go over the boundaries of the text
        start = max(0, min(location - snippet_length / 2, len(text) - snippet_length))
        end = min(start + snippet_length, len(text))
        
        # Extends the selection a bit to include full words at both ends
        # TODO: optimise with regexp search
        # start -= len(re.sub(ur'^.*?(\w*)$', ur'\1', text[0:start])) 
        while start > 0 and re.match(ur'\w', text[start]):
            start -= 1 
        while end < len(text) and re.match(ur'\w', text[end]):
            end += 1 
        return text[start:end]

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

