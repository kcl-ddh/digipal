class SearchContentType(object):
    
    def set_record_view_context(self, context):
        context['type'] = self.key
        pass

    def __init__(self):
        self.is_advanced = False
        self._queryset = []
    
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

