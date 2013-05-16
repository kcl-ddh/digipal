"""Default variable filters."""

import re
import random as random_module
import unicodedata
from decimal import Decimal, InvalidOperation, Context, ROUND_HALF_UP
from functools import wraps
from pprint import pformat

from django.template.base import Variable, Library, VariableDoesNotExist
from django.conf import settings
from django.utils import formats
from django.utils.dateformat import format, time_format
from django.utils.encoding import force_unicode, iri_to_uri
from django.utils.html import (conditional_escape, escapejs, fix_ampersands,
    escape, urlize as urlize_impl, linebreaks, strip_tags)
from django.utils.http import urlquote
#from django.utils.text import Truncator, wrap, phone2numeric
from django.utils.safestring import mark_safe, SafeData, mark_for_escaping
from django.utils.timesince import timesince, timeuntil
from django.utils.translation import ugettext, ungettext
from django.utils.text import normalize_newlines
from django.template.defaultfilters import stringfilter
from urllib import unquote
from hashlib import sha1

register = Library()

@register.filter
def remove_item(ls, itm):
    """ remove item itm from list ls) """
    return ls.remove(itm)

@register.filter
def split_facet(facet):
    return facet.split(':')

@register.filter
def uniq(inp):
    """
    This allows us to generate valid unique class and ID names
    """
    return "DP_" + str(sha1(inp.encode('utf-8')).hexdigest())

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def unquote_string(value):
    return unquote(value)

@register.filter
def querystring(facets):
    s = ''
    for item in sorted(facets):
        spl = item.split(':')
        s += "%s=%s&" % (spl[0], spl[1])
    return s

# Some extra mathematical tags

@register.filter()
def div(value, arg):
    "Divides the value by the arg and rounds up if needed"
    absoluteVal = float(value) / float(arg)
    integerVal = int(value) / int(arg)
    if (absoluteVal - integerVal) > 0:
        return integerVal + 1
    else:
        return integerVal
        
        
@register.filter()
def multiply(value, arg):
    "Divides the value by the arg and rounds up if needed"
    val = float(value) * float(arg)
    return int(val)

# TEI conversion

@register.filter()
def tei(value):
    "Convert TEI field into XML"
    import re
    
    # tei text transform
    value = re.sub(ur'(<title level="a">)(.*?)(</title>)', ur"'\1\2\3'", value)

    #     value = re.sub(ur'<\s*([^/])\s*>', ur'<span class="tei-\1">', value)
    # >>> re.findall(ur'(<\s*(\S+)' + ur'\s*(?:(\S+)="([^"]*)")?' * 5 + '>)', r' <t a1="v1" a2="v2">')
    # [('<t a1="v1" a2="v2">', 't', 'a1', 'v1', 'a2', 'v2', '', '', '', '', '', '')]
    elements = re.findall(ur'(<\s*(\w+)' + ur'\s*(?:(\S+)="([^"]*)")?' * 5 + '>)', value)
    for element in elements:
        if element[1][0] == '/': continue
        element_html = '<span class="tei-' + element[1]
        i = 2
        while i < len(element):
            if not element[i]: break
            element_html += ' tei-a-%s__%s' % (element[i], element[i+1])
            i += 2
        element_html += '">'
        value = value.replace(element[0], element_html)
        
    value = re.sub(ur'<\s*/[^>]*>', ur'</span>', value)
    value = re.sub(ur'\r?\n', ur'<br/>', value)
    value = mark_safe(value)
    
    print value
    
    return value
