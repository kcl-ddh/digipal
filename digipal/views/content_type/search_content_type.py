from mezzanine.conf import settings
from django import forms
from digipal.templatetags.hand_filters import chrono
from digipal import utils


class SearchContentType(object):

    def __init__(self):
        self.is_advanced = False
        # None if no search has run
        self._queryset = None
        self._init_field_types()
        self.desired_view = ''
        self.ordering = None
        self.set_page_size()

    def is_slow(self):
        # return True if this search is noticeably slower than the other
        # in this case this search will be triggered only when necesary
        return False

    def _init_field_types(self):
        '''
        Defines Whoosh field types used to define the schemas.
        See get_field_infos().
        '''

        # see http://pythonhosted.org/Whoosh/api/analysis.html#analyzers
        # see JIRA 165

        from whoosh.fields import TEXT, ID
        # TODO: shall we use stop words? e.g. 'A and B' won't work?
        from whoosh.analysis import SimpleAnalyzer, StandardAnalyzer, StemmingAnalyzer, CharsetFilter
        from whoosh.support.charset import accent_map
        # ID: as is; SimpleAnalyzer: break into lowercase terms, ignores punctuations; StandardAnalyzer: + stop words + minsize=2; StemmingAnalyzer: + stemming
        # minsize=1 because we want to search for 'Scribe 2'

        # JIRA 508 - don't ignore *, that's the best I can do as a field won't
        # work well with both stemming and exact phrase search
        from whoosh.util.text import rcompile
        default_pattern = rcompile(r"\*|\w+(\.?\w+)*")

        # A paragraph or more.
        self.FT_LONG_FIELD = TEXT(analyzer=StemmingAnalyzer(
            minsize=1, expression=default_pattern) | CharsetFilter(accent_map))
        # A few words.
        self.FT_SHORT_FIELD = TEXT(analyzer=StemmingAnalyzer(
            minsize=1, expression=default_pattern) | CharsetFilter(accent_map))
        # A title (e.g. British Library)
        self.FT_TITLE = TEXT(analyzer=StemmingAnalyzer(
            minsize=1, stoplist=None, expression=default_pattern) | CharsetFilter(accent_map))
        # A code (e.g. K. 402, Royal 7.C.xii)
        # See JIRA 358
        self.FT_CODE = TEXT(analyzer=SimpleAnalyzer(
            ur'[.\s()\u2013\u2014-]', True))
        # An ID (e.g. 708-AB)
        self.FT_ID = ID()

    def get_headings(self):
        return []

    def get_default_ordering(self):
        return 'relevance'

    def set_ordering(self, requested_ordering=None):
        self.ordering = self.get_default_ordering()
        if requested_ordering == 'relevance':
            self.ordering = requested_ordering
        else:
            for heading in self.get_headings():
                if heading['key'] == requested_ordering and heading['is_sortable']:
                    self.ordering = requested_ordering
                    break

    def get_ordering(self):
        return self.ordering

    def get_model(self):
        import digipal.models
        ret = getattr(digipal.models, self.label[:-1])
        return ret

    def process_record_view_request(self, context, request):
        ret = 'pages/record_' + self.key + '.html'
        self.set_record_view_context(context, request)
        self.set_record_view_pagination_context(context, request)
        return ret

    def set_record_view_context(self, context, request):
        context['type'] = self
        from digipal.models import has_edit_permission
        if has_edit_permission(request, self.get_model()):
            context['can_edit'] = True

    def set_index_view_context(self, context, request):
        ''' Populate the given [context] dictionary with those entries:
                'records': a list of record instances
                'content_type': content type object e.g. SearchManuscripts
                'message': an intro message e.g. 'list of manuscript with images' 
                'active_letters': a list of letters for the pagination. 
                    If we have records starting with b then ('b' in context['active_letters'])
        '''
        ret = context

        ret['content_type'] = self

        # get all the records
        ret['records'] = self.get_index_records()

        # sort the result
        ret['records'] = self.get_sorted_records(ret['records'])

        # Add a label to each record
        # Filter by the letter of the current result page
        # Find all the letters which have at least one record
        page_letter = request.GET.get('pl', '').lower()
        ret['active_letters'] = {'': len(ret['records'])}
        recs = ret['records']
        ret['records'] = []
        for record in recs:
            # generate a label for the record
            record.index_label = getattr(
                record, 'index_label', self.get_record_index_label(record))
            letter = ''
            # find active letters
            if record.index_label:
                letter = record.index_label[0].lower()
                ret['active_letters'][letter] = 1
            # filtering by letter/page
            if (not page_letter) or (letter == page_letter):
                ret['records'].append(record)

        ret['message'] = self.get_index_message(context, request)

        self.group_index_records(ret['records'])

        ret['active_letters'] = ret['active_letters'].keys()

        return ret

    def get_index_message(self, context, request):
        ret = ''
        return ret

    def group_index_records(self, records):
        pass

    def get_index_records(self):
        return self.get_model().objects.all()

    def get_record_index_label(self, record):
        ret = u'%s' % (record or '')
        return ret

    @property
    def result_type_qs(self):
        return "result_type=%s" % self.key

    @property
    def template_path(self):
        return 'search/content_type/%s.html' % self.key

    @property
    def is_advanced_search(self):
        return self.is_advanced

    @property
    def queryset(self):
        '''Returns a list of recordids'''
        return self._queryset or []

    @property
    def is_empty(self):
        '''None is returned if no search has been run yet.'''
        if self._queryset is None:
            return None
        return self.count == 0

    @property
    def count(self):
        '''
            Returns the number of records found.
            -1 if the no search was executed.
        '''
        if self._queryset is None:
            ret = -1
        else:
            ret = 0
            if self.queryset:
                if isinstance(self.queryset, list):
                    ret = len(self.queryset)
                else:
                    # assume query set
                    ret = self.queryset.count()
        return ret

    def set_record_view_pagination_context(self, context, request):
        '''
            set context['navigation'] = {'total': , 'index1': , 'previous_url': , 'next_url':, 'no_record_url': }
            This entries are used by the record.html template to show the navigation above the record details
        '''
        import re

        # TODO: optimise this, we should not have to retrieve the whole result
        # to find prev and next record ids
        ret = {}
        if 'results' not in context:
            return

        web_path = request.META['PATH_INFO']
        query_string = '?' + request.META['QUERY_STRING']
        ret['total'] = self.count

        # index (of the requested record in the full result)
        if int(context['id']) in context['results']:
            index = context['results'].index(int(context['id']))

            # prev
            if index > 0:
                ret['previous_url'] = re.sub(
                    ur'\d+', '%s' % context['results'][index - 1], web_path) + query_string

            # next
            if index < (ret['total'] - 1):
                ret['next_url'] = re.sub(
                    ur'\d+', '%s' % context['results'][index + 1], web_path) + query_string

            # TODO: the URL of the search page shoudn't be hard-coded here
            ret['index1'] = index + 1
            ret['no_record_url'] = u'/digipal/search/' + query_string

        else:
            ret = {}

        context['pagination'] = ret

    def get_fields_info(self):
        '''
            Returns a dictionary of searchable fields.
            It is a mapping between the fields in the Django Data Model and 
            the Whoosh index.

            Format:

                ret['field_path'] = {'whoosh': {
                                                'type': self.FT_TITLE
                                                , 'name': 'whoosh_field_name'
                                                , 'store_only': True
                                                , 'ignore': False
                                                , 'boost': 2.0
                                                , 'virtual': False
                                                }
                                    , 'advanced': True
                                    , 'long_text': True
                                    }

            Where:

                field_path: is a django query set path from the current model 
                    instance to the desired field
                    e.g. display_label or related_record__display_label

                whoosh: sub dictionary tells Whoosh how to index or query the field
                    type: one of the predefined types declared in _init_field_types()
                    name: the name of the field in Whoosh schema
                    boost: optional parameter to boost the importance of a field (1.0 is normal, 
                            2.0 is twice as important). Boosting is applied at query time only;
                            not at indexing time.
                            Convention:
                                3.0 for default sorting field
                                0.3 which are not displayed
                                2.0 for cat num
                                1.0 otherwise
                    ignore: optional; if True the field is searched using the DB
                            rather than indexed by Whoosh
                    virtual: optional; if True the field does not exist in the DB.
                            e.g. 'type' or 'sort_order'
                    store_only: optional parameter; if True the field is stored 
                            in the Whoosh index but not searchable

                advanced: optional; if True the field can be searched on using the 
                            value from the HTTP request GET parameter with the 
                            same name. 
                            E.g. ...?whoosh_field_name=123

                long_text: optional; if True, the value will be broken into 
                    separate terms by the indexer; False to treat the value as 
                    a whole. This is used for the autocomplete index only.                  
        '''

        ret = {}
        from whoosh.fields import TEXT, ID, NUMERIC
        ret['id'] = {'whoosh': {'type': TEXT(
            stored=True), 'name': 'id', 'store_only': True}}
        ret['type'] = {'whoosh': {'type': TEXT(
            stored=True), 'name': 'type', 'virtual': True}}
        ret['sort_order'] = {'whoosh': {'type': NUMERIC(
            stored=False, sortable=True), 'name': 'sort_order', 'store_only': True, 'virtual': True}}
        return ret

    def get_qs_all(self):
        ''' returns a django query set with all the instances of this content type '''
        return (self.get_model()).objects.all()

    def get_sort_fields(self):
        ''' returns a list of django field names necessary to sort the results '''
        return []

    def get_sorted_records(self, records):
        ''' Returns a list of django records with all the searchable instances 
            of this content type.
            The order of the returned list will influence the order of 
            display on the result sets.
        '''
        import re
        from digipal.utils import natural_sort_key

        sort_fields = self.get_sort_fields()

        if sort_fields:
            # Natural sort order based on a concatenation of the sort fields
            # obtained from get_sort_fields()
            def sort_order(record):
                if isinstance(record, dict):
                    sort_key = ' '.join([ur'%s' % record[field]
                                         for field in sort_fields])
                else:
                    sort_key = ' '.join(
                        [ur'%s' % eval('record.' + field.replace('__', '.')) for field in sort_fields])
                # remove non-words characters at the beginning
                # e.g. 'Hemming' -> Hemming
                sort_key = re.sub(ur'(?u)^\W+', ur'', sort_key)
                return natural_sort_key(sort_key, True)
            records = sorted(records, key=lambda record: sort_order(record))

        return records

    def write_index(self, writer, verbose=False, aci={}):
        import re
        from django.utils.html import (
            conditional_escape, escapejs, escape, urlize as urlize_impl, linebreaks, strip_tags)

        fields = self.get_fields_info()

        records = self.get_all_records_sorted()
        ret = len(records)

        # For each record, create a Whoosh document
        sort_order = 0
        for record in records:
            sort_order += 1
            document = {'type': u'%s' % self.key, 'sort_order': sort_order}

            # The document is made of the Content Type Schema where
            # The django fields in the schema entries are replaced by their
            # value in the database record.
            #
            for k in fields:
                if not fields[k]['whoosh'].get('ignore', False) and not fields[k]['whoosh'].get('virtual', False):
                    val = u'%s' % k
                    for field_name in re.findall(ur'\w+', k):
                        if isinstance(record, dict):
                            v = record[field_name]
                        else:
                            v = eval('record.' + field_name.replace('__', '.'))

                        if v is None:
                            v = ''
                        val = val.replace(field_name, u'%s' % v)
                    if len(val):
                        val = strip_tags(val)
                        format = fields[k]['whoosh'].get('format', '')
                        if format:
                            val = format % val
                        document[fields[k]['whoosh']['name']] = val

                        # JIRA 508 - Add an ID counterpart to allow exact phrase search
#                         if fields[k].get('long_text', False):
#                             document[fields[k]['whoosh']['name']+'_iexact'] = val

                        # build autocomplete index
                        val2 = val
                        if id(fields[k]['whoosh']['type']) not in [id(self.FT_LONG_FIELD)]:
                            val2 += '|'
                        aci[val2] = 1

            if document:
                if verbose:
                    print document
                writer.add_document(**document)

        return ret

    def get_all_records_sorted(self):
        ''' Returns an array with all the records
            Each record is an dictionary of field_name -> value
            The output is sorted according to get_sort_fields
            and natural sort. 
        '''
        import re

        fields = self.get_fields_info()

        # extract all the fields names from the content type schema
        # Note that a schema entry can be an expressions made of multiple field names
        # e.g. "current_item__repository__place__name,
        # current_item__repository__name"
        django_fields = self.get_sort_fields()
        for k in fields:
            if not fields[k]['whoosh'].get('ignore', False) and not fields[k]['whoosh'].get('virtual', False):
                django_fields.extend(re.findall(ur'\w+', k))

        # Retrieve all the records from the database
        # Values turns individual results into dictionary of requested fields names and values
        # print str(records.query)
        records = self.get_qs_all().values(*django_fields).distinct()

        # GN: 11/02/2014
        #
        # Now force all joins to be LEFT JOINS
        #
        # Explanation:
        #
        # Django will usually generate LEFT joins except for non-nullable foreign keys.
        # This causes issue when we search for scribes an retrieve fields from the repository.
        # Scribes without hands will not be returned even though there is a left join to hand,
        # that's because there will be a inner join from CI to repository. Scribes without hands
        # have no CI and therefore no repository.
        #
        # So this might be considered as a Django bug because once part of a query path is
        # on left join longer paths based on it should de facto be also left joined.
        #
        from digipal.utils import set_left_joins_in_queryset
        set_left_joins_in_queryset(records)
        # for alias in records.query.alias_map:
        #records.query.promote_alias(alias, True)

        ret = self.get_sorted_records(records)
        return ret

    def get_parser(self, index):
        from whoosh.qparser import MultifieldParser, SingleQuotePlugin

        term_fields = []
        boosts = {}
        if self.__class__ == SearchContentType:
            # return all the fields in the schema
            # TODO: remove type and ID!
            term_fields = index.schema.names()
        else:
            for field in self.get_fields_info().values():
                if not field['whoosh'].get('ignore', False) and not field['whoosh'].get('store_only', False):
                    name = field['whoosh']['name']
                    term_fields.append(name)
                    boosts[name] = field['whoosh'].get('boost', 1.0)
        parser = MultifieldParser(term_fields, index.schema, boosts)
        # parser.add_plugin(SingleQuotePlugin())
        #parser = MultifieldParser(term_fields, index.schema)
        return parser

    def get_suggestions(self, query, limit=8):
        chrono('suggestions:')
        ret = []
        #query = query.lower()
        query_parts = query.split()

        # Search Logic:
        #
        # If query = 'Wulfstan British L'
        # We first try "Wulfstan British L"*
        # Then, if we don't have [limit] results we try also "British L"*
        # Then, ..., we also try "L"*
        #
        prefix = u''
        while query_parts and len(ret) < limit:
            query = u' '.join(query_parts).lower()
            ret.extend(self.get_suggestions_single_query(
                query, limit - len(ret), prefix, ret))
            if query_parts:
                prefix += query_parts.pop(0) + u' '
        chrono(':suggestions')
        return ret

    def get_suggestions_single_query(self, query, limit=8, prefix=u'', exclude_list=[]):
        ret = []

        #settings.suggestions_index = None

        if not getattr(settings, 'suggestions_index_canonical', None):
            chrono('load:')
            path = self.get_autocomplete_path()
            if path:
                import os
                if os.path.exists(path):
                    from digipal.management.commands.utils import readFile
                    # we have to remove combining marks otherwise
                    # len(settings.suggestions_index_canonical) < len(settings.suggestions_index)
                    settings.suggestions_index = utils.remove_combining_marks(
                        readFile(path))
                    settings.suggestions_index_canonical = utils.remove_accents(
                        settings.suggestions_index)
            chrono(':load')

        if not settings.suggestions_index_canonical:
            return ret

        if query and limit > 0:
            import re
            from django.utils.html import strip_tags
            phrase = query

            chrono('regexp:')
            ret = {}
            exclude_list_lower = [strip_tags(s.lower()) for s in exclude_list]

            for m in re.finditer(ur'(?ui)\b%s(?:[^|]{0,40}\|\||[\w-]*\b)' % re.escape(utils.remove_accents(phrase)), settings.suggestions_index_canonical):
                m = settings.suggestions_index[m.start(0):m.end(0)]
                m = m.strip('|')
                if m.endswith(')') and '(' not in m:
                    m = m[:-1]
                if m.endswith(']') and '[' not in m:
                    m = m[:-1]
                if ur'%s%s' % (prefix, m.lower()) not in exclude_list_lower:
                    ret[m.lower()] = m
            ret = ret.values()
            chrono(':regexp')

            # sort the results by length then by character
            chrono('sort:')

            def comp(a, b):
                d1 = len(a) - len(b)
                if d1 < 0:
                    return -1
                if d1 > 0:
                    return 1
                return cmp(a, b)

            ret.sort(comp)
            chrono(':sort')

            # print ret
            if len(ret) > limit:
                ret = ret[0:limit]

            # Add the prefix to all the results
            ret = [(ur'%s<strong>%s</strong>' % (prefix, r)) for r in ret]

        return ret

    def get_suggestions_single_query_old(self, query, limit=8, prefix=u''):
        ret = []
        # TODO: set a time limit on the search.
        # See
        # http://pythonhosted.org/Whoosh/searching.html#time-limited-searches
        if query and limit > 0:

            # Run a whoosh search
            whoosh_query = ur'"%s"*' % query
            results = self.search_whoosh(
                whoosh_query, matched_terms=True, index_name='autocomplete')
            terms = {}
            if results.has_matched_terms():
                # e.g. set([('scribes', 'hand'), ('label', 'hands'), ('type',
                # 'hands'), ('description', 'handbook'), ('description',
                # 'hand'), ('name', 'hand'), ('description', 'handsom'),
                # ('label', 'hand')])
                for term_info in results.matched_terms():
                    t = term_info[1].decode('utf-8')
                    terms[t] = 1
            self.close_whoosh_searcher()
            ret = terms.keys()

            # sort the results by length then by character
            ql = len(query)

            def key(k):
                ret = len(k) * 100000
                if len(k) > ql:
                    ret += ord(k[ql]) * 10000
                if len(k) > ql + 1:
                    ret += ord(k[ql + 1])
                return ret
            ret = sorted(ret, key=key)
            if len(ret) > limit:
                ret = ret[0:limit]

            # Add the prefix to all the results
            #ret = [ur'%s%s' % (prefix, r.decode('utf8')) for r in ret]
            ret = [(ur'%s%s' % (prefix, r)).title() for r in ret]

        return ret

    def get_autocomplete_path(self, can_create_path=False):
        ''' returns the path of the autocomplete index on the filesystem'''
        ret = None
        index_name = 'autocomplete'
        import os.path
        path = settings.SEARCH_INDEX_PATH
        if not os.path.exists(path):
            if can_create_path:
                os.mkdir(path)
            else:
                return ret
        path = os.path.join(path, index_name)
        if not os.path.exists(path):
            if can_create_path:
                os.mkdir(path)
            else:
                return ret

        path = os.path.join(path, index_name + '.idx')

        return path

    def get_whoosh_index(self, index_name='unified'):
        from whoosh.index import open_dir
        import os
        return open_dir(os.path.join(settings.SEARCH_INDEX_PATH, index_name))

    def search_whoosh(self, query=None, matched_terms=False, index_name='unified'):
        '''
            Run a search with the provided query using Whoosh.
        '''
        self.close_whoosh_searcher()
        index = self.get_whoosh_index(index_name=index_name)
        self.searcher = index.searcher()

        parser = self.get_parser(index)
        query = parser.parse(query)

        # See http://pythonhosted.org/Whoosh/facets.html
        from whoosh import sorting
        sortedby = [sorting.FieldFacet("sort_order")]
        if self.get_ordering() == 'relevance':
            sortedby.insert(0, sorting.ScoreFacet())
        ret = self.searcher.search(
            query, limit=None, terms=matched_terms, sortedby=sortedby)

        return ret

    def close_whoosh_searcher(self):
        searcher = getattr(self, 'searcher', None)
        if searcher:
            searcher.close()
            self.searcher = None

    def _get_available_views(self):
        ''' Returns a list of available tabs to display on the search result.
            Can be overridden. 

            Example:
                ret = [
                       {'key': 'images', 'label': 'Images', 'title': 'Change to Images view'},
                       {'key': 'list', 'label': 'List', 'title': 'Change to list view'},
                       ]
        '''
        return []

    def get_views(self):
        ''' Like get_available_views() 
            but also sets a field 'active' = True|False to each view in the list.
        '''
        ret = self._get_available_views()
        # now set the active view
        found = False
        for view in ret:
            if view['key'] == self.desired_view:
                view['active'] = True
                found = True
                break
        if not found and ret:
            ret[0]['active'] = True
        return ret
    views = property(get_views)

    def set_desired_view(self, view_key):
        '''Select a search result view we want to show on the front-end.
            view_key is the key of the desired view.
            Note that this content type may not support the desired view.
            In this case it will resort to a default view.
        '''
        self.desired_view = view_key

    def build_queryset(self, request, term, force_search=False):
        ret = []
        self.set_ordering(request.GET.get('ordering'))
        term = SearchContentType.expand_query(term)
        # only run slow searches if that tab is selected or forced search;
        # always run other searches
        if force_search or not(self.is_slow()) or (request.GET.get('result_type', '') == self.key) or (request.GET.get('basic_search_type', '') == self.key):
            ret = self._build_queryset(request, term)
        return ret

    @classmethod
    def get_term_expansions(cls):
        # load expansions and cache them
        expansions = getattr(cls, 'expansions', {})
        if not expansions:
            # load from DB
            from digipal.models import Repository
            for repo in Repository.objects.all():
                if repo.short_name and (repo.short_name == repo.short_name.upper()):
                    expansions[repo.short_name] = repo.human_readable()
            cls.expansions = expansions

        return expansions

    @classmethod
    def expand_query(cls, query):
        ''' Expand terms in the query. E.g. BL => British Library'''
        # TODO: don't expand if surrounded by quotes
        # TODO: expand place name? otherwise it may be ambiguous (e.g. CCCC ==
        # OCCC)

        expansions = cls.get_term_expansions()

        # expand
        import re
        for k in expansions:
            query = re.sub(ur'\b(%s)\b' % re.escape(
                k), ur'(\1 OR "%s")' % expansions[k], query)

        return query

    def _build_queryset(self, request, term):
        '''
            Returns an ordered list or record ids that match the query in the http request.
            The ids are retrieved using Whoosh or Django QuerySet or both.            
        '''

        # TODO: single search for all types.
        # TODO: optimisation: do the pagination here so we load only the records we show.
        # TODO: if no search phrase then apply default sorting order

        # print '------- %s' % self.__class__

        term = term.strip()
        self.query_phrase = term

        from datetime import datetime
        t0 = datetime.now()

        # Convert the search fields into:
        # * Django query filters (django_filters)
        # * Whoosh query (query_advanced)
        query_advanced = ''
        # django_filters is used for post-whoosh filtering using django
        # queryset
        django_filters = {}
        infos = self.get_fields_info()
        for field_path in self.get_fields_info():
            info = infos[field_path]
            if info.get('advanced', False):
                name = info['whoosh']['name']
                val = request.GET.get(name, '')
                if val:
                    self.is_advanced = True
                    if info['whoosh'].get('ignore', False):
                        django_filters['%s__iexact' % field_path] = val
                    else:
                        query_advanced += ' %s:"%s"' % (name, val)

        # Run the Whoosh search (if there is a query phrase or query_advanced)
        results = []
        from collections import OrderedDict
        whoosh_dict = OrderedDict()
        use_whoosh = term or query_advanced

        # The code was originally designed to work without Whoosh if we can
        # retrieve the information from the database.
        # However now we use whoosh in every case because we need to retrieve
        # the proper sort order this may change in the future if we sort the
        # result using the DB/Django but keep in mind that the sort order is
        # not trivial (see get_sort_fields() and search_whoosh()).
        sort_with_whoosh = True
        if sort_with_whoosh:
            use_whoosh = True

        if use_whoosh:
            # Build the query
            # filter the content type (e.g. manuscripts) and other whoosh
            # fields
            query = ur''
            if term or query_advanced:
                query = (ur'%s %s' % (term, query_advanced)).strip()
            query = (query + ur' type:%s' % self.key).strip()

            # Run the search
            results = self.search_whoosh(query)
            ##results = self.search_whoosh(query, True)

            t01 = datetime.now()

            # Get all the ids in the right order and only once
            # TODO: would it be faster to return the hits only?
            for hit in results:
                whoosh_dict[int(hit['id'])] = hit
                # print '\t%s %s %s' % (hit.rank, hit.score, hit['id'])
                #terms = hit.matched_terms()

        self.whoosh_dict = whoosh_dict

        ret = []
        if django_filters or not use_whoosh:
            from django.db.models import Q
            # We need to search using Django
            #ret = (self.get_model()).objects.filter(**django_filters).values_list('id', flat=True).distinct()
            # We use Q(q1) & Q(q2) & Q(q3) here as it is more correct (share the joins so it is a real AND rather then kind-of-AND)
            # and faster (less joins) than just filter(q1, q2, q3)
            ret = (self.get_model()).objects.filter(
                Q(**django_filters)).values_list('id', flat=True).distinct()

            if use_whoosh:
                # Intersection between Whoosh results and Django results.
                # We can't do .filter(id__in=whooshids) because it would
                # ignore the order stored in whooshids.
                ret = list(ret)
                l = len(ret)
                for i in range(l - 1, -1, -1):
                    if ret[i] not in self.whoosh_dict:
                        del(ret[i])
            else:
                # Pure Django search
                # We convert the result into a list
                ret = list(ret)
        else:
            # Pure Whoosh search
            ret = self.whoosh_dict.keys()

        # Cache the result
        self._queryset = ret

        t1 = datetime.now()
        # print t1 - t0, t01 - t0, t02 - t01, t1 - t02

        self.close_whoosh_searcher()

        return self._queryset

    def results_are_recordids(self):
        return True

    def set_page_size(self, page_size=10):
        self.page_size = page_size

    def get_page_size(self):
        return self.page_size

    def bulk_load_records(self, recordids):
        '''Read all the records from the database
            This can be overridden to significantly optimise the template 
            rendering by pre-fetching the related records.  
        '''
        return (self.get_model()).objects.in_bulk(recordids)

    def get_records_from_ids(self, recordids):
        # TODO: preload related objects?
        # Fetch all the records from the DB
        records = self.bulk_load_records(recordids)
        # Make sure they are in the desired order
        # 'if id in records' is important because of ghost recordids
        # returned by a stale whoosh index.
        chrono('group:')
        ret = [records[id] for id in recordids if id in records]
        chrono(':group')
        return ret

    def get_whoosh_dict(self):
        ''' 
            Returns a sorted dictionary of hits from the last search
            OrderedDict ret such that ret[record.id] = hit
        '''
        return getattr(self, 'whoosh_dict', None)

    def _get_query_terms(self, lowercase=False):
        '''
            Returns a list of tokens found in the search query. 
        '''
        from digipal.utils import get_tokens_from_phrase
        ret = get_tokens_from_phrase(self.query_phrase, lowercase)
        return ret

    def add_field_links(self, links):
        '''Add associations between pairs of input fields to [links]'''
        pass

    def get_field_link(self, source_input, target_input, queryset, update_source=False):
        '''Returns a new association between two input fields
            e.g.
                {
                    'fields': ['chartype', 'character'],
                    'values': {'accent': ['accent'], 'letter': ['a', 'b', ...], ...}
                }
            if update_source is True, changing the target will also update the source
        '''
        ret = {}

        for record in queryset:
            ret[record[0]] = ret.get(record[0], [])
            ret[record[0]].append(record[1])

        ret = {
            'fields': [source_input, target_input],
            'values': ret,
            'update_source': update_source
        }
        return ret


class QuerySetAsList(list):
    def count(self):
        return len(self)


from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.template.defaultfilters import slugify


def get_form_field_from_queryset(values, label, is_model_choice_field=False, aid=None, other_choices=[], is_key_id=False):
    ''' Returns a choice field from a set of values
        If is_model_choice_field is True a forms.ModelChoiceField is returned, 
        otherwise a forms.ChoiceField is returned.
        Note that forms.ModelChoiceField will run the query each time the form is rendered.
        Whereas forms.ChoiceField will have its choices effectively cached for the whole 
        duration of the web application lifetime. Which is more efficient but might be
        an issue if the applicaiton is not restarted after a database update.
    '''
    label_prefix = 'a'
    if label[0] in ['a', 'e', 'i', 'o', 'u', 'y']:
        label_prefix = 'an'

    if not aid:
        aid = '%s-select' % slugify(label)

    options = {
        'widget': Select(attrs={'id': aid, 'class': 'chzn-select', 'data-placeholder': 'Choose %s %s' % (label_prefix, label)}),
        'label': '',
        'required': False
    }
    if is_model_choice_field:
        ret = forms.ModelChoiceField(
            #queryset = Hand.objects.values_list('assigned_place__name', flat=True).order_by('assigned_place__name').distinct(),
            queryset=values,
            empty_label=label,
            **options
        )
    else:
        if is_key_id:
            choices = [(d.id, d) for d in values]
        else:
            choices = [(d, d) for d in values]
        ret = forms.ChoiceField(
            #choices = [('', 'Date')] + [(d, d) for d in list(Hand.objects.all().filter(assigned_date__isnull=False).values_list('assigned_date__date', flat=True).order_by('assigned_date__sort_order').distinct())],
            choices=[('', label)] + other_choices + choices,
            initial=label,
            **options
        )
    return ret
