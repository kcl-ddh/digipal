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
    if '"' in content or "'" in content:
        # we assume the content is HTML
        parts = re.findall(ur'(?:src|href)="([^"]*?)"', content)
        parts += re.findall(ur"(?:src|href)='([^']*?)'", content)
    else:
        # we assume the content is a single URL
        parts = [content]
    
    # update all the urls found in content    
    for url in sorted(parts, key=lambda e: len(e), reverse=True):
        content = content.replace(url, update_query_string(url, updates, url_wins))
        
    return content

def update_query_string(url, updates, url_wins=False):
    '''
        Replace parameter values in the query string of the given URL.
        If url_wins is True, the query string values in [url] will always supersede the values from [updates].
        
        E.g.
        
        >> _update_query_string('http://www.mysite.com/about?category=staff&country=UK', 'who=bill&country=US')
        'http://www.mysite.com/about?category=staff&who=bill&country=US'

        >> _update_query_string('http://www.mysite.com/about?category=staff&country=UK', {'who': ['bill'], 'country': ['US']})
        'http://www.mysite.com/about?category=staff&who=bill&country=US'
        
    '''
    show = url == '?page=2&amp;terms=%C3%86thelstan&amp;repository=&amp;ordering=&amp;years=&amp;place=&amp;basic_search_type=hands&amp;date=&amp;scribes=&amp;result_type=' and updates == 'result_type=manuscripts'
    
    ret = url.strip()
    if ret and ret[0] == '#': return ret

    from urlparse import urlparse, urlunparse, parse_qs
    
    # Convert string format into a dictionary
    if isinstance(updates, basestring):
        updates_dict = parse_qs(updates, True)
    else:
        from copy import deepcopy
        updates_dict = deepcopy(updates)
    
    # Merge the two query strings (url and updates)
    # note that urlparse preserves the url encoding (%, &amp;)
    parts = [p for p in urlparse(url)]
    # note that parse_qs converts u'terms=%C3%86thelstan' into u'\xc3\x86thelstan'
    # See http://stackoverflow.com/questions/16614695/python-urlparse-parse-qs-unicode-url
    # for the reaon behind the call to encode('ASCII') 
    query_dict = parse_qs(parts[4].encode('ASCII'))
    if url_wins:
        updates_dict.update(query_dict)
        query_dict = updates_dict
    else:
        query_dict.update(updates_dict)
    
    # Now query_dict is our updated query string as a dictionary 
    # Parse and unparse it again to remove the empty values
    query_dict = parse_qs(urlencode(query_dict, True))
    
    # Convert back into a string    
    parts[4] = urlencode(query_dict, True)
    
    # Place the query string back into the URL
    ret = urlunparse(parts)
    
    return ret

def urlencode(dict, doseq=0):
    ''' This is a unicode-compatible wrapper around urllib.urlencode()
        See http://stackoverflow.com/questions/3121186/error-with-urlencode-in-python
    '''
    import urllib
    d = {}
    for k,v in dict.iteritems():
        d[k] = []
        for v2 in dict[k]:
            if isinstance(v2, unicode):
                v2 = v2.encode('utf=8')
            d[k].append(v2)
    ret = urllib.urlencode(d, doseq)
    return ret

@register.filter
def plural(value, count=2):
    from utils import plural
    return plural(value, count)

@register.filter
def tag_phrase_terms(value, phrase=''):
    '''Wrap all occurrences of the terms of [phrase] found in value with a <span class="found-term">.'''
    import re

    # get terms from the phrase
    terms = re.split(ur'\s+', phrase.lower().strip())
    
    # Surround the occurrences of those terms in the value with a span (class="found-term")
    # TODO: this should really be done by Whoosh instead of manually here to deal properly with special cases.
    # e.g. 'G*' should highlight g and the rest of the word
    # Here we have a simple implementation that look for exact and complete matches only.
    # TODO: other issue is highlight of non field values, e.g. (G.) added at the end each description
    #         or headings.
    for term in terms:
        value = re.sub(ur'(?iu)(>[^<]*)\b('+re.escape(term)+ur')\b', ur'\1<span class="found-term">\2</span>', u'>'+value)
        value = value[1:]
    
    return value
