from compressor.filters.base import CompilerFilter
from compressor.filters.css_default import CssAbsoluteFilter

from digipal.templatetags import hand_filters

# Add this keyword to your LESS file to prevent errors due to imports.
KEYWORD_ALLOW_IMPORT = 'ALLOW_IMPORT'

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
        
        #raise Exception('BACK TRACE')
        
        hand_filters.chrono('input:')
        
        # LESSC
        content = super(LessAndCssAbsoluteFilter, self).input(**kwargs)

        self.validate_input()
        
        # CssAbsoluteFilter
        hand_filters.chrono('\t %s' % repr(kwargs))
        kwargs['filename'] = self.init_filename
        ret = CssAbsoluteFilter(content).input(**kwargs)
        
        hand_filters.chrono(':input')
        
        return ret
        
        
    def validate_input(self):
        '''Raises an exception if the LESS file contains @import and not the
            KEYWORD_ALLOW_IMPORT keyword.'''
        from digipal import utils
        content = None
        try:
            content = utils.read_file(self.infile.name)
        except:
            pass
        if content:
            if '@import' in content and KEYWORD_ALLOW_IMPORT not in content:
                raise Exception('@import not supported in LESS file as changes in nested LESS files are not detected by django-compressor (%s).' % self.infile.name)
        
            
def compressor_patch():
    '''Make sure the cache is always used.
        Even with COMPRESSOR_ENABLED == False
        Note that if a file has changed, all the files within the compress
        template block will be recompiled!
    '''

    from compressor.templatetags.compress import CompressorMixin
    
    from compressor.cache import (cache_get, get_templatetag_cachekey)
    
    def render_cached(self, compressor, kind, mode, forced=False):
        """
        If enabled checks the cache for the given compressor's cache key
        and return a tuple of cache key and output
        """
        cache_key = get_templatetag_cachekey(compressor, mode, kind)
        cache_content = cache_get(cache_key)
        return cache_key, cache_content
    
    CompressorMixin.render_cached = render_cached
