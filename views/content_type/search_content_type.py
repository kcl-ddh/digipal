from django.conf import settings

class SearchContentType(object):
    
    def get_model(self):
        import digipal.models
        ret = getattr(digipal.models, self.label[:-1])
        return ret
    
    def set_record_view_context(self, context, request):
        context['type'] = self
        from digipal.models import has_edit_permission
        if has_edit_permission(request, self.get_model()):
            context['can_edit'] = True

    def __init__(self):
        self.is_advanced = False
        self._queryset = []
        self._init_field_types()
        
    def _init_field_types(self):
        '''
        Defines Whoosh field types used to define the schemas.
        See get_field_infos().
        '''
        
        # see http://pythonhosted.org/Whoosh/api/analysis.html#analyzers
        # see JIRA 165
        
        from whoosh.fields import TEXT, ID
        # TODO: shall we use stop words? e.g. 'A and B' won't work? 
        from whoosh.analysis import SimpleAnalyzer, StandardAnalyzer, StemmingAnalyzer
        # ID: as is; SimpleAnalyzer: break into terms, ignores punctuations; StandardAnalyzer: + stop words + minsize=2; StemmingAnalyzer: + stemming
        # minsize=1 because we want to search for 'Scribe 2'
        
        # A paragraph or more. 
        self.FT_LONG_FIELD = TEXT(analyzer=StemmingAnalyzer(minsize=1))
        # A few words.
        self.FT_SHORT_FIELD = TEXT(analyzer=StemmingAnalyzer(minsize=1))
        # A title (e.g. British Library)
        self.FT_TITLE = TEXT(analyzer=StemmingAnalyzer(minsize=1, stoplist=None))
        # A code (e.g. K. 402)
        self.FT_CODE = TEXT(analyzer=SimpleAnalyzer())
        # An ID (e.g. 708-AB)
        self.FT_ID = ID()
    
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
        return self._queryset
    
    @property
    def is_empty(self):
        return self.count == 0

    @property
    def count(self):
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
        from digipal.utils import update_query_string
        import re

        # TODO: optimise this, we should not have to retrieve the whole result 
        # to find prev and next record ids
        ret = {}
        if 'results' not in context:
            return
        
        web_path = request.META['PATH_INFO']
        query_string = '?' + request.META['QUERY_STRING']
        ret['total'] = self.count
        
        # index
        index = context['results'].index(int(context['id']))
        
        # prev
        if index > 0:
            ret['previous_url'] = re.sub(ur'\d+', '%s' % context['results'][index - 1], web_path) + query_string
        
        # next
        if index < (ret['total'] - 1):
            ret['next_url'] = re.sub(ur'\d+', '%s' % context['results'][index + 1], web_path) + query_string
        
        # TODO: the URL of the search page shoudn't be hard-coded here
        ret['no_record_url'] = u'/digipal/search/' + query_string
        ret['index1'] = index + 1
        
        context['pagination'] = ret 

    def get_fields_info(self):
        ret = {}
        from whoosh.fields import TEXT, ID
        ret['id'] = {'whoosh': {'type': TEXT(stored=True), 'name': 'id', 'store_only': True}}
        ret['type'] = {'whoosh': {'type': TEXT(stored=True), 'name': 'type'}}
        return ret
    
    def write_index(self, writer):
        fields = self.get_fields_info()
        
        # extract all the fields names from the content type schema
        # Note that a schema entry can be an expressions made of multiple field names
        # e.g. "current_item__repository__place__name, current_item__repository__name"
        import re 
        django_fields = []
        for k in fields: 
            if k != 'type' and not fields[k]['whoosh'].get('ignore', False):
                django_fields.extend(re.findall(ur'\w+', k))
        
        # Retrieve all the records from the database
        query = (self.get_model()).objects.all().values(*django_fields).distinct()
        ret = query.count()
        
        # For each record, create a Whoosh document
        for record in query:
            document = {'type': u'%s' % self.key}
            
            # The document is made of the Content Type Schema where
            # The django fields in the schema entries are replaced by their
            # value in the database record.
            #
            for k in fields:
                if k != 'type' and not fields[k]['whoosh'].get('ignore', False):
                    val = u'%s' % k
                    for field_name in re.findall(ur'\w+', k):
                        v = record[field_name]
                        if v is None: v = ''
                        val = val.replace(field_name, u'%s' % v)
                    if len(val):
                        document[fields[k]['whoosh']['name']] = val
                    
            if document:
                writer.add_document(**document)
        
        return ret
        
    def get_parser(self, index):
        from whoosh.qparser import MultifieldParser
        
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
        #parser = MultifieldParser(term_fields, index.schema, boosts)
        parser = MultifieldParser(term_fields, index.schema)
        return parser
    
    def get_suggestions(self, query, limit=8):
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
            ret.extend(self.get_suggestions_single_query(query, limit - len(ret), prefix))
            if query_parts: 
                prefix += query_parts.pop(0) + u' '
        return ret

    def get_suggestions_single_query(self, query, limit=8, prefix=u''):
        ret = []
        # TODO: set a time limit on the search.
        # See http://pythonhosted.org/Whoosh/searching.html#time-limited-searches
        if query and limit > 0:
            
            # Run a whoosh search
            whoosh_query = ur'"%s"*' % query
            results = self.search_whoosh(whoosh_query, matched_terms=True, index_name='autocomplete')
            terms = {}
            if results.has_matched_terms():
                # e.g. set([('scribes', 'hand'), ('label', 'hands'), ('type', 
                # 'hands'), ('description', 'handbook'), ('description', 
                # 'hand'), ('name', 'hand'), ('description', 'handsom'), 
                # ('label', 'hand')])
                for term_info in results.matched_terms():
                    terms[term_info[1].title()] = 1
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
            ret = [ur'%s%s' % (prefix, r.decode('utf8')) for r in ret]

        return ret
    
    def get_whoosh_index(self, index_name='unified'):
        from whoosh.index import open_dir
        import os
        return open_dir(os.path.join(settings.SEARCH_INDEX_PATH, index_name))
    
    def search_whoosh(self, query, matched_terms=False, index_name='unified'):
        ret = []
        
        self.close_whoosh_searcher()
        index = self.get_whoosh_index(index_name=index_name)
        self.searcher = index.searcher()
        
        # TODO: custom weight, e.g. less for description
        parser = self.get_parser(index)
        query = parser.parse(query)
        ret = self.searcher.search(query, limit=None, terms=matched_terms)
        
        return ret
    
    def close_whoosh_searcher(self):
        searcher = getattr(self, 'searcher', None)
        if searcher:
            searcher.close()
            self.searcher = None
    
    def build_queryset(self, request, term):
        
        # TODO: single search for all types.
        # TODO: optimisation: do the pagination here so we load only the records we show.
        # TODO: if no search phrase then apply default sorting order
        
        term = term.strip()
        self.query_phrase = term
         
        from datetime import datetime
        t0 = datetime.now()
        
        # Convert the search fields into: 
        # * Django query filters (django_filters)
        # * Whoosh query (query_advanced)        
        query_advanced = ''
        # django_filters is used for post-whoosh filtering using django queryset
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
        from django.utils.datastructures import SortedDict
        whoosh_dict = SortedDict()
        use_whoosh = term or query_advanced
        if use_whoosh:
            # Build the query
            # filter the content type (e.g. manuscripts) and other whoosh fields
            query = ('%s %s type:%s' % (term, query_advanced, self.key)).strip()

            # Run the search
            ## TODO: uncomment
            ##results = self.search_whoosh(query)
            results = self.search_whoosh(query, True)

            t01 = datetime.now()
            
            # Get all the ids in the right order and only once
            # TODO: would it be faster to return the hits only?
            for hit in results:
                whoosh_dict[int(hit['id'])] = hit
                terms = hit.matched_terms()
                
        self.whoosh_dict = whoosh_dict
        
        ret = []
        if django_filters or not use_whoosh:
            # We need to search using Django
            ret = (self.get_model()).objects.filter(**django_filters).values_list('id', flat=True).distinct()
            # TODO: sort the django results! (if pure django search)
            
            if use_whoosh:
                # Intersection between Whoosh results and Django results.
                # We can't do .filter(id__in=whooshids) because it would 
                # ignore the order stored in whooshids.
                l = len(ret)
                for i in range(l-1, -1, -1):
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
        #self._queryset = records
        self._queryset = ret
            
        t1 = datetime.now()
        #print t1 - t0, t01 - t0, t02 - t01, t1 - t02
        
        self.close_whoosh_searcher()
        
        return self._queryset
    
    def get_records_from_ids(self, recordids):
        # TODO: preload related objects?
        # Fetch all the records from the DB
        records = (self.get_model()).objects.in_bulk(recordids)
        # Make sure they are in the desired order
        # 'if id in records' is important because of ghost recordids 
        # returned by a stale whoosh index.
        ret = [records[id] for id in recordids if id in records]
        return ret
    
    def get_whoosh_dict(self):
        return getattr(self, 'whoosh_dict', None)

    def _get_query_terms(self):
        phrase = self.query_phrase
        # remove punctuation characters (but keep spaces and alphanums)
        import re
        phrase = re.sub(ur'[^\w\s]', u'', phrase)
    
        # get terms from the phrase
        terms = re.split(ur'\s+', phrase.lower().strip())
        return terms
    
class QuerySetAsList(list):
    def count(self):
        return len(self) 

