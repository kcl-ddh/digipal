from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
import re

register = Library()

@stringfilter
def spacify(value, autoescape=None):
    if autoescape:
	esc = conditional_escape
    else:
	esc = lambda x: x
    return mark_safe(re.sub('\s', '%20', esc(value)))
spacify.needs_autoescape = True
register.filter(spacify)

@register.filter(is_safe=True)
@stringfilter
def anchorify(value):
    """
    Like slugify() but preserves the unicode chars
    The problem with slugify is that it will return an empty string for
    a single special char, or identical slugs for strings where only one
    special char varies.
    """
    #value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub(ur'(?u)[^\w\s-]', u'', value).strip()
    return mark_safe(re.sub(u'[-\s]+', u'-', value))

@register.filter(is_safe=True)
def update_query_params(content, updates):
    ''' The query strings in the content are updated by the filter.
        In case of conflict, the parameters in the filter always win.
    '''
    return update_query_params_internal(content, updates)

@register.filter(is_safe=True)
def add_query_params(content, updates):
    ''' The query strings in the content are updated by the filter.
        In case of conflict, the parameters in the content always win.
    '''
    return update_query_params_internal(content, updates, True)

def update_query_params_internal(content, updates, url_wins=False):
    '''
        Update the query strings found in an HTML fragment.
        
        See update_query_string()
        
        E.g.
        
        >> update_query_string('href="http://www.mysite.com/path/?k1=v1&k2=v2" href="/home"', 'k2=&k5=v5')
        'href="http://www.mysite.com/path/?k1=v1&k5=v5" href="/home?k5=v5"'
        
    '''
    if len(content.strip()) == 0: return content
    
    # find all the URLs in content
    template = ur'%s'
    matches = []
    if '"' in content or "'" in content:
        template = ur'href="%s"'
        # we assume the content is HTML
        for m in re.finditer(ur'(?:src|href)\s*=\s*(?:"([^"]*?)"|\'([^\']*?)\')', content):
            matches.append(m)
    else:
        # we assume the content is a single URL
        m = re.search(ur'^(.*)$', content)
        if m:
            matches.append(m)
    
    from digipal.utils import update_query_string
    for m in matches[::-1]:
        url = max(m.groups())
        new_url = update_query_string(url, updates, url_wins)
        content = content[0:m.start()] + (template % new_url) + content[m.end():]
            
    return content

@register.filter
def plural(value, count=2):
    from digipal.utils import plural
    return plural(value, count)

@register.filter
def tag_phrase_terms(value, phrase=''):
    '''Wrap all occurrences of the terms of [phrase] found in value with a <span class="found-term">.'''
    import re
    
    # remove punctuation characters (but keep spaces and alphanums)
    phrase = re.sub(ur'[^\w\s]+', u' ', phrase)
    
    if len(phrase.strip()): 

        # get terms from the phrase
        terms = re.split(ur'\s+', phrase.lower().strip())
        
        # Surround the occurrences of those terms in the value with a span (class="found-term")
        # TODO: this should really be done by Whoosh instead of manually here to deal properly with special cases.
        # e.g. 'G*' should highlight g and the rest of the word
        # Here we have a simple implementation that look for exact and complete matches only.
        # TODO: other issue is highlight of non field values, e.g. (G.) added at the end each description
        #         or headings.
        from digipal.utils import get_regexp_from_terms
        re_terms = get_regexp_from_terms(terms)
        if re_terms:
            # a trick to prevent recursive substitution
            stop_keyword = 'AAAA'
            # The loop here is necessary because the matches overlap therefore only the last occurence is found each time
            while True:
                l = len(value)
                value = re.sub(ur'(?iu)(>[^<]*)('+re_terms+ur')', ur'\1<span class="found-term">\2' + stop_keyword + ur'</span>', u'>'+value)
                value = value[1:]
                if len(value) == l: break
            value = value.replace(stop_keyword, '')
            
        #for term in terms:
        #    value = re.sub(ur'(?iu)(>[^<]*)\b('+re.escape(term)+ur')\b', ur'\1<span class="found-term">\2</span>', u'>'+value)
        #    value = value[1:]
        
    return value

@register.assignment_tag
def get_records_from_ids(search_type, recordids):
    '''
        Prepare the records before they are displayed on the search page
         
        Usage:
            {% prepare_search_result search_type recordids %}
    '''
    return search_type.get_records_from_ids(recordids)
    
@register.assignment_tag
def reset_recordids():
    '''
        Reset a variable to []
        
        Use this before autopaginate, e.g. 
        
        {% reset_recordids as recordids %}
        {% autopaginate type.queryset 9 as recordids %}
        
        There is a bug in autopaginate. It won't reset recordids if we ask 
        for an empty page. Without this the result will try to show record 
        ids the previous tab. 
    '''
    return []

@register.simple_tag
def iip_img_a(iipfield, *args, **kwargs):
    '''
        Usage {% iip_img_a IIPIMAGE_FIELD [width=W] [height=H] [cls=HTML_CLASS] [lazy=0|1] %}
        
        Render a <a href=""><img src="" /></a> element with the url referenced 
        by the iipimage field.
        width and height are optional. See IIP Image for the way they 
        are treated. 
    '''
    return mark_safe(ur'<a href="%s&RST=*&QLT=100&CVT=JPG">%s</a>' % (iipfield.full_base_url, iip_img(iipfield, *args, **kwargs)))

@register.simple_tag
def iip_img(iipfield, *args, **kwargs):
    '''
        Usage {% iip_img IIPIMAGE_FIELD [width=W] [height=H] [cls=HTML_CLASS] [lazy=0|1] %}
        
        Render a <img src="" /> element with the url referenced by the 
        iipimage field.
        width and height are optional. See IIP Image for the way they 
        are treated. 
        If lazy is True the image will be loaded only when visible in 
        the browser. 
    '''
    return img(iip_url(iipfield, *args, **kwargs), *args, **kwargs)

@register.simple_tag
def annotation_img(annotation, *args, **kwargs):
    '''
        Usage {% annotation_img ANNOTATION [width=W] [height=H] [cls=HTML_CLASS] [lazy=0|1] %}
        
        See iip_img() for more information
    '''
    return img(annotation.get_cutout_url(), alt=annotation.graph, *args, **kwargs)

@register.simple_tag
def img(src, *args, **kwargs):
    more = ''
    
    if 'alt' in kwargs:
        more += ur' alt="%s" ' % kwargs['alt']
    
    if 'cls' in kwargs:
        more += ur' class="%s" ' % kwargs['cls']
    
    if kwargs.get('lazy', False):
        more += ur' data-lazy-img-src="%s" ' % src
        src = ur'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
        
        # default dimensions 
        size = {'width': kwargs.get('width', -1), 'height': kwargs.get('height', -1)}
        for d in size:
            s = size[d]
            if s == -1:
                s = max(size.values())
            more += ' %s="%s" ' % (d, s)
        
    ret = ur'<img src="%s" %s/>' % (src, more)
    return mark_safe(ret)    

@register.simple_tag
def iip_url(iipfield, *args, **kwargs):
    '''
        Usage {% iip_url IIPIMAGE_FIELD [width=W] [height=H] %}
        
        Render a url referenced by the iipimage field.
        width and height are optional. See IIP Image for the way they 
        are treated. 
    '''
    return mark_safe(iipfield.thumbnail_url(kwargs.get('height', None), kwargs.get('width', None)))
    
def escapenewline(value):
    """
    Adds a slash before any newline. Useful for loading a multi-line html chunk
    into a Javascript variable.
    """
    return value.replace('\n', '\\\n')
escapenewline.is_safe = True
escapenewline = stringfilter(escapenewline)
register.filter('escapenewline', escapenewline)

