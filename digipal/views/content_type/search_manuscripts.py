from django import forms
from search_content_type import SearchContentType, get_form_field_from_queryset
from digipal.models import *
from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.db.models import Q
from mezzanine.conf import settings

from digipal.utils import sorted_natural
class FilterManuscripts(forms.Form):
    index = get_form_field_from_queryset(sorted_natural(
                            '%s' % cn for cn in CatalogueNumber.objects.filter(historical_item__item_parts__isnull=False).distinct()
                        ), 'Catalogue Number')
    repository = get_form_field_from_queryset([m.human_readable() for m in Repository.objects.filter(currentitem__itempart__isnull=False).order_by('place__name', 'name').distinct()], 'Repository')
    ms_date = get_form_field_from_queryset(sorted_natural(list(ItemPart.objects.filter(historical_items__date__isnull=False, historical_items__date__gt='').values_list('historical_items__date', flat=True).order_by('historical_items__date').distinct())), 'Date')

class SearchManuscripts(SearchContentType):

    def get_fields_info(self):
        ''' See SearchContentType.get_fields_info() for a description of the field structure '''

        ret = super(SearchManuscripts, self).get_fields_info()
        ret['locus'] = {'whoosh': {'type': self.FT_CODE, 'name': 'locus'}}
        ret['subdivisions__current_item__shelfmark current_item__shelfmark'] = {'whoosh': {'type': self.FT_CODE, 'name': 'shelfmark', 'boost': 3.0}}
        
        ret['subdivisions__current_item__repository__place__name subdivisions__current_item__repository__name current_item__repository__place__name current_item__repository__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'repository'}, 'advanced': True}
        ret['historical_items__itemorigin__place__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'place'}, 'advanced': True}
        ret['historical_items__catalogue_number'] = {'whoosh': {'type': self.FT_CODE, 'name': 'index', 'boost': 2.0}, 'advanced': True}
        # Boosting set to 0.3 so a 'Vespasian' will rank record with Vespasian shelfmark higher than those that have it in the description.
        ret['historical_items__description__description'] = {'whoosh': {'type': self.FT_LONG_FIELD, 'name': 'description', 'boost': 0.2}, 'long_text': True}
        ret['historical_items__date'] = {'whoosh': {'type': self.FT_CODE, 'name': 'ms_date'}, 'advanced': True}

        ret['hands__scribe__name'] = {'whoosh': {'type': self.FT_CODE, 'name': 'scribe', 'boost': 0.3}, 'advanced': True}
        
        # MS
        ret['group__historical_items__name, historical_items__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'hi'}}
        
        # Hand
        ret['hands__assigned_place__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'hand_place'}, 'advanced': True}
        ret['hands__assigned_date__date'] = {'whoosh': {'type': self.FT_CODE, 'name': 'hand_date'}, 'advanced': True}
        ret['hands__script__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'script'}, 'advanced': True}
        
        # Scribe
        ret['hands__scribe__scriptorium__name'] = {'whoosh': {'type': self.FT_TITLE, 'name': 'scriptorium'}, 'advanced': True}
        ret['hands__scribe__date'] = {'whoosh': {'type': self.FT_CODE, 'name': 'scribe_date', 'boost': 1.0}, 'advanced': True}
        
        return ret

    def get_headings(self):
        ret = [
                    {'label': 'Index', 'key': 'index', 'is_sortable': False},
                    {'label': 'Repository', 'key': 'repository', 'is_sortable': True, 'title': 'Repository and Shelfmark'},
                    {'label': 'Shelfmark', 'key': 'shelfmark', 'is_sortable': False},
                    {'label': 'Folio(s)', 'key': 'folio', 'is_sortable': False},
                    {'label': 'Description', 'key': 'description', 'is_sortable': False},
                ]
        return getattr(settings, 'SEARCH_ITEM_PART_HEADINGS', ret)
    
    def get_default_ordering(self):
        return 'repository'
    
    def get_sort_fields(self):
        ''' returns a list of django field names necessary to sort the results '''
        return ['current_item__repository__place__name', 'current_item__repository__name', 'current_item__shelfmark', 'locus']

    def set_record_view_context(self, context, request):
        super(SearchManuscripts, self).set_record_view_context(context, request)
        context['item_part'] = ItemPart.objects.get(id=context['id'])
        images = Image.filter_permissions_from_request(context['item_part'].images.all().prefetch_related('hands', 'annotation_set'), request)
        context['images'] = Image.sort_query_set_by_locus(images)
        context['hands'] = context['item_part'].hands.all().order_by('num')
        from digipal_text.models import TextContentXML
        context['text_content_xmls'] = TextContentXML.get_public_only(context['can_edit']).filter(text_content__item_part=context['item_part']).order_by('text_content__type__name')

    def get_index_records(self):
        recs = super(SearchManuscripts, self).get_index_records()
        # this greatly reduces the time to render all the records
        recs = recs.select_related('current_item', 'current_item__repository', 'current_item__repository__place', 'current_item__repository__media_permission')
        recs = recs.prefetch_related('images', 'images__media_permission')
        recs = recs.filter(id__in=(Image.get_all_public_images()).values_list('item_part_id', flat=True))
        return recs
    
    def get_record_index_label(self, itempart, nolocus=False):
        ret = ''
        if itempart and itempart.current_item:
            ret = u'%s, %s, %s' % (itempart.current_item.repository.place.name, itempart.current_item.repository.name, itempart.current_item.shelfmark)
            if itempart.locus and not nolocus:
                ret += u', %s' % itempart.locus
        return ret

    def group_index_records(self, itemparts):
        # We group the IP into CIs
        # and list all the images under each group
        i = 0
        
        public_images = {}
        for image in Image.sort_query_set_by_locus(Image.get_all_public_images(), True):
            try:
                key = image.item_part.current_item.id
                if key not in public_images: public_images[key] = []
                public_images[key].append({'index_label': '%s' % image.locus, 'get_absolute_url': image.get_absolute_url()})
            except:
                pass
        
        last_ci = None
        while i < len(itemparts):
            ip = itemparts[i]

            same_ci_as_previous = (last_ci and last_ci == ip.current_item)
            if not same_ci_as_previous:
                last_ci = ip.current_item
                last_ci.subrecords = []
                
                # define the label of the CI
                last_ci.index_label = u'%s, %s, %s' % (last_ci.repository.place.name, last_ci.repository.name, last_ci.shelfmark)

                # add all the images as subrecords
                last_ci.subrecords = public_images[last_ci.id]

            itemparts[i] = last_ci

            # Same CI, no need to keep it
            if same_ci_as_previous:
                del(itemparts[i])
                continue
            
            i += 1
        
    def get_index_message(self, context, request):
        ret = 'List of manuscripts with images'
        return ret

    def get_form(self, request=None):
        initials = None
        if request:
            initials = request.GET
        return FilterManuscripts(initials)

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

    def _build_queryset_django(self, request, term):
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
    
    def bulk_load_records(self, recordids):
        return (self.get_model()).objects.select_related('current_item').prefetch_related('historical_items__catalogue_numbers', 'historical_items__description_set', 'images', 'current_item__repository').in_bulk(recordids)

    def get_records_from_ids(self, recordids):
        ret = super(SearchManuscripts, self).get_records_from_ids(recordids)
        # Generate a meaningful snippet for each description,
        # one that includes the search terms.
        # See JIRA 132. Basically we have to show a snippet of a description.
        # We choose the description with the best snippet.
        # If no match at all, we use the normal description selection.
        whoosh_dict = self.get_whoosh_dict()
        for record in ret:
            # Whoosh snippets temporary disabled, see reason below
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
                    description, location = self._get_best_description_location(historical_item.get_descriptions())
                    if description is None:
                        # no match in any description, so we select the beginning of the most important description
                        description, location = historical_item.get_display_description(), 0
                    # get the description text
                    if description:
                        text = description.get_description_plain_text()
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
        #terms = [t.lower() for t in self._get_query_terms() if t not in [u'or', u'and', u'not']]
        from digipal.utils import get_regexp_from_terms
        #terms = get_tokens_from_phrase(descriptions)
        terms = self._get_query_terms(True)
        re_terms = get_regexp_from_terms(terms)

        if re_terms:
            # search the descriptions
            for adesc in descriptions:
                m = re.search(ur'(?ui)' + re_terms, adesc.get_description_plain_text())
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
            
        ret = text[start:end].strip()
        
        if start > 0: ret = u'\u2026' + ret
        if end < len(text): ret += u'\u2026'
        
        return ret

