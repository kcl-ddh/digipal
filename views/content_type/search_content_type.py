from django.conf import settings

class SearchContentType(object):
    
    def get_fields_info(self):
        return {}
    
    def write_index(self, writer):
        fields = self.get_fields_info()
        query = (self.get_model)().objects.all().values(*fields.keys())
        ret = query.count()
        for record in query:
            document = {}
            for path, val in record.iteritems():
                if val is not None:
                    document[fields[path]['whoosh']['name']] = u'%s' % val
            if document:
                writer.add_document(**document)
        
        return ret
        
    def get_model(self):
        import digipal.models
        ret = getattr(digipal.models, self.label[:-1])
        return ret
    
    def set_record_view_context(self, context):
        context['type'] = self.key

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
        if self.queryset: ret = self.queryset.count()
        return ret

    def set_record_view_pagination_context(self, context, request):
        '''
            set context['navigation'] = {'total': , 'index1': , 'previous_url': , 'next_url':, 'no_record_url': }
            This entries are used by the record.html template to show the navigation above the record details
        '''
        from digipal.templatetags.html_escape import update_query_string

        # TODO: optimise this, we should not have to retrieve the whole result 
        # to find prev and next record ids
        ret = {}
        base_url = '?' + request.META['QUERY_STRING']
        ret['total'] = context['results'].count()
        
        # index
        index = 0
        for r in context['results']:
            if ('%s' % r.id) == ('%s' % context['id']): break
            index += 1
        
        # prev
        if index > 0:
            ret['previous_url'] = update_query_string(base_url, 'id=%s' % context['results'][index - 1].id)
        
        # next
        if index < (ret['total'] - 1):
            ret['next_url'] = update_query_string(base_url, 'id=%s' % context['results'][index + 1].id)
        
        ret['no_record_url'] = update_query_string(base_url, 'id=')
        ret['index1'] = index + 1
        
        context['pagination'] = ret 

    def build_queryset(self, request, term):
        # TODO: single search for all types
        from whoosh.index import open_dir
        import os
        index = open_dir(os.path.join(settings.SEARCH_INDEX_PATH, 'unified'))
        with index.searcher() as searcher:
            from whoosh.qparser import MultifieldParser
            
            field_names = [field['whoosh']['name'] for field in self.get_fields_info().values()]
            
            parser = MultifieldParser(field_names, index.schema)
            query = parser.parse(term)            
            results = searcher.search(query, limit=None)
            resultids = [result['id'] for result in results]
        
            self._queryset = (self.get_model()).objects.filter(id__in=resultids)
        