from django import forms
from search_content_type import SearchContentType
from digipal.models import *
from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.db.models import Q

class SearchManuscripts(SearchContentType):

    def get_fields_info(self):
        ''' See SearchContentType.get_fields_info() for a description of the field structure '''

        ret = super(SearchManuscripts, self).get_fields_info()
        ret['locus'] = {'whoosh': {'type': self.FT_CODE, 'name': 'locus'}}
        ret['current_item__shelfmark'] = {'whoosh': {'type': self.FT_CODE, 'name': 'shelfmark', 'boost': 3.0}}
        ret['current_item__repository__place__name, current_item__repository__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'repository'}, 'advanced': True}
        ret['historical_items__itemorigin__place__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'place'}, 'advanced': True}
        ret['historical_items__catalogue_number'] = {'whoosh': {'type': self.FT_CODE, 'name': 'index', 'boost': 2.0}, 'advanced': True}
        # Boosting set to 0.3 so a 'Vespasian' will rank record with Vespasian shelfmark higher than those that have it in the description.
        ret['historical_items__description__description'] = {'whoosh': {'type': self.FT_LONG_FIELD, 'name': 'description', 'boost': 0.2}, 'long_text': True}
        ret['historical_items__date'] = {'whoosh': {'type': self.FT_CODE, 'name': 'date'}, 'advanced': True}
        return ret

    def get_sort_fields(self):
        ''' returns a list of django field names necessary to sort the results '''
        return ['current_item__repository__place__name', 'current_item__repository__name', 'current_item__shelfmark', 'locus']

    def set_record_view_context(self, context, request):
        super(SearchManuscripts, self).set_record_view_context(context, request)
        context['item_part'] = ItemPart.objects.get(id=context['id'])
        context['images'] = context['item_part'].images.all().order_by('-folio_number')
        context['hands'] = context['item_part'].hands.all().order_by('item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'descriptions__description','id')

    def get_index_records(self):
        ret = super(SearchManuscripts, self).get_index_records()
        # this greatly reduces the time to render all the records
        ret = ret.select_related('current_item', 'current_item__repository', 'current_item__repository__place')
        return ret
    
    def get_record_index_label(self, itempart, nolocus=False):
        ret = ''
        if itempart:
            ret = u'%s, %s, %s' % (itempart.current_item.repository.place.name, itempart.current_item.repository.name, itempart.current_item.shelfmark)
            if itempart.locus and not nolocus:
                ret += u', %s' % itempart.locus
        return ret

    def group_index_records(self, itemparts):
        # we group the records by current item
        itempart_group = None
        i = 0
        
        # The list is already sorted by CI so we can easily spot consecutive items to be grouped
        while i < len(itemparts):
            itempart = itemparts[i]
            if itempart_group and itempart.current_item == itempart_group.current_item:
                # The IP is the same as the previous one
                subrecords = getattr(itempart_group, 'subrecords', [])
                
                if not subrecords:
                    # second item in the group so we need to create the group,
                    # add the first item there and  
                    # remove its locus from the label of the group
                    subrecords.append({'get_absolute_url': itempart_group.get_absolute_url(), 'index_label': itempart_group.locus})
                    itempart_group.index_label = self.get_record_index_label(itempart_group, True)
                    itempart_group.subrecords = subrecords
                
                # then we add the item part to the group as well  
                itemparts[i].index_label = itemparts[i].locus
                subrecords.append(itemparts[i])
                del(itemparts[i])
            else:
                itempart_group = itempart
                i += 1

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
                Q(historical_items__catalogue_number__icontains=term) | \
                Q(historical_items__description__description__icontains=term))

        repository = request.GET.get('repository', '')
        index_manuscript = request.GET.get('index', '')
        date = request.GET.get('date', '')

        self.is_advanced = repository or index_manuscript or date

        if date:
            query_manuscripts = query_manuscripts.filter(historical_items__date=date)
        if repository:
            repository_place = repository.split(',')[0]
            repository_name = repository.split(', ')[1]
            query_manuscripts = query_manuscripts.filter(current_item__repository__name=repository_name, urrent_item__repository__place__name=repository_place)

        if index_manuscript:
            query_manuscripts = query_manuscripts.filter(historical_items__catalogue_number=index_manuscript)

        self._queryset = query_manuscripts.distinct().order_by('folio_number', 'historical_items__catalogue_number', 'id')

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
                historical_item = record.historical_item
                if historical_item:
                    description, location = self._get_best_description_location(historical_item.get_descriptions().all())
                    if description is None:
                        # no match in any description, so we select the beginning of the most important description
                        description, location = historical_item.get_display_description(), 0
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
        choices = [("", "Repository")] + [(m.human_readable(), m.human_readable()) for m in Repository.objects.all().order_by('name').distinct()],
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

