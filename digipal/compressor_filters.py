from compressor.filters.base import CompilerFilter
from compressor.filters.css_default import CssAbsoluteFilter

class LessAndCssAbsoluteFilter(CompilerFilter):
    '''
        Less compilation followed by CssAbsoluteFilter filter
        Why?
            We need that filter otherwise the fonts referenced by bootstrap
            won't be copied to the compressor CACHE.
            And they will be missing from the front end.
            The problem is that filters are not processed when
            COMPRESS_ENABLED == False (but precompilers like LESS are).
            And we don't want to enable it in debug mode as we don't want
            files to be combined; only on production server.
        Solution
            We combine the two operations in this custom precompile class
        Adapted from work around suggested on
            https://github.com/django-compressor/django-compressor/pull/331
            
        GN: 2015/05/20
    '''
    
    def __init__(self, content, attrs, **kwargs):
        self.init_filename = kwargs.get('filename', '')
        super(LessAndCssAbsoluteFilter, self).__init__(content, command='lessc {infile}', **kwargs)

    def input(self, **kwargs):
        content = super(LessAndCssAbsoluteFilter, self).input(**kwargs)
        kwargs['filename'] = self.init_filename
        c1 = CssAbsoluteFilter(content).input(**kwargs
            )
        return c1
        
        
