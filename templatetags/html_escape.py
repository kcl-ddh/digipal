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
    from digipal.utils import update_query_string
    for url in sorted(parts, key=lambda e: len(e), reverse=True):
        content = content.replace(url, update_query_string(url, updates, url_wins))
        
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
    phrase = re.sub(ur'[^\w\s]', u'', phrase)

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
    
