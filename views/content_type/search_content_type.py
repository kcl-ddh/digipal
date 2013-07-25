from django.conf import settings

class SearchContentType(object):
    
    def get_model(self):
        import digipal.models
        ret = getattr(digipal.models, self.label[:-1])
        return ret
    
    def set_record_view_context(self, context):
        context['type'] = self

    def __init__(self):
        self.is_advanced = False
        self._queryset = []
    
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

        # TODO: optimise this, we should not have to retrieve the whole result 
        # to find prev and next record ids
        ret = {}
        if 'results' not in context:
            return
        
        query_string = '?' + request.META['QUERY_STRING']
        ret['total'] = context['results'].count()
        
        # index
        index = 0
        record = None
        for record in context['results']:
            if ('%s' % record.id) == ('%s' % context['id']): break
            index += 1
        
        # prev
        if index > 0:
            ret['previous_url'] = context['results'][index - 1].get_absolute_url() + query_string
        
        # next
        if index < (ret['total'] - 1):
            ret['next_url'] = context['results'][index + 1].get_absolute_url() + query_string
        
        # TODO: the URL of the search page shoudn't be hard-coded here
        ret['no_record_url'] = u'/digipal/search/' + query_string
        ret['index1'] = index + 1
        
        context['pagination'] = ret 

    def get_fields_info(self):
        from whoosh.fields import TEXT, ID
        ret = {}
        ret['id'] = {'whoosh': {'type': TEXT(stored=True), 'name': 'id', 'store_only': True}}
        ret['type'] = {'whoosh': {'type': TEXT(stored=True), 'name': 'type'}}
        return ret
    
    def write_index(self, writer):
        fields = self.get_fields_info()
        
        django_fields = [k for k in fields if k != 'type' and not fields[k]['whoosh'].get('ignore', False)]
        query = (self.get_model()).objects.all().values(*django_fields).distinct()
        ret = query.count()
        
        for record in query:
            document = {'type': u'%s' % self.key}
            for path, val in record.iteritems():
                if val is not None:
                    document[fields[path]['whoosh']['name']] = u'%s' % val
            if document:
                writer.add_document(**document)
        
        return ret
        
    def get_parser(self, index):
        from whoosh.qparser import MultifieldParser
        
        term_fields = []
        boosts = {}
        for field in self.get_fields_info().values():
            if not field['whoosh'].get('ignore', False) and not field['whoosh'].get('store_only', False):
                name = field['whoosh']['name']
                term_fields.append(name)
                boosts[name] = field['whoosh'].get('boost', 1.0)
        #parser = MultifieldParser(term_fields, index.schema, boosts)
        parser = MultifieldParser(term_fields, index.schema)
        return parser
        
    def build_queryset(self, request, term):
        # TODO: single search for all types.
        # TODO: optimisation: do the pagination here so we load only the records we show.
        # TODO: don't search for ID and type
        # TODO: if no search phrase then apply default sorting order
        term = term.strip()
         
        from datetime import datetime
        t0 = datetime.now()
        
        from whoosh.index import open_dir
        import os
        index = open_dir(os.path.join(settings.SEARCH_INDEX_PATH, 'unified'))
        with index.searcher() as searcher:
            # TODO: custom weight, e.g. less for description
            parser = self.get_parser(index)
            
            # teardrop-shaped worcester saec xi2
            # add the advanced fields
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

            # filter the type
            results = []
            from django.utils.datastructures import SortedDict
            records_dict = SortedDict()
            use_whoosh = term or query_advanced
            if use_whoosh:
                query = ('%s %s type:%s' % (term, query_advanced, self.key)).strip()
                query = parser.parse(query)
                        
                #ret['name'] = {'whoosh': {'type': TEXT, 'name': 'name'}, 'advanced': True}
                
                results = searcher.search(query, limit=None)
            
                t01 = datetime.now()
                
                # get all the ids in the right order and only once
                for result in results:
                    records_dict[result['id']] = 1
            
            resultids = records_dict.keys()
    
            t02 = datetime.now()
            
            #records = []
            records = QuerySetAsList()
            if django_filters or not use_whoosh:
                # additional django filters
                records_django = (self.get_model()).objects.filter(**django_filters)
                #print django_filters, records_django.count()
                if resultids:
                    records_django = records_django.filter(id__in=resultids)
                for record in records_django:
                    records_dict[unicode(record.id)] = record
                for k in records_dict:
                    if not isinstance(records_dict[k], int):
                        records.append(records_dict[k])
            else:
                # get all the records in one go 
                records_dict = (self.get_model()).objects.in_bulk(resultids)
                for id in resultids:
                    records.append(records_dict[int(id)])
            self._queryset = records
            # TODO: this is not always the most efficient way of doing it
            # If we have a queryset it's better to use count()
            #self._queryset.count = lambda :len(self._queryset)
            
        t1 = datetime.now()
        #print t1 - t0, t01 - t0, t02 - t01, t1 - t02
        
        return self._queryset
    
class QuerySetAsList(list):
    def count(self):
        return len(self) 
