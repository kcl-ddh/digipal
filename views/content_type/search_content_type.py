class SearchContentType(object):
    
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
        ret = True
        if self.queryset: ret = self.queryset.count() == 0
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
        