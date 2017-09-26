"""Default variable filters."""

import re
import random as random_module
import unicodedata
from decimal import Decimal, InvalidOperation, Context, ROUND_HALF_UP
from functools import wraps
from pprint import pformat

from django.template.base import Variable, Library, VariableDoesNotExist
from mezzanine.conf import settings
from django.utils import formats
from django.utils.dateformat import format, time_format
from django.utils.encoding import force_unicode, iri_to_uri
from django.utils.html import (conditional_escape, escapejs,
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
from datetime import datetime

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


@register.filter()
def richfield(val):
    "Render a HTML field for the front end. Make it safe, make sure it is surrounded by <p>."
    import re

    if val is None:
        val = u''

    # trim the value from empty spaces and lines
    ret = re.sub(ur'(?usi)^\s+', '', val)
    ret = re.sub(ur'(?usi)\s+$', '', ret)

    if ret:
        is_xml = (val[0] == u'<')
        if not is_xml:
            # _italics_
            ret = re.sub(ur'(?musi)_(\w+)_', ur'<em>\1</em>', ret)
            # this is a plain text field
            # convert to HTML by surrounding lines with <p>
            ret = u'<p>%s</p>' % (u'</p><p>'.join(re.split(ur'[\r\n]+', ret)),)

    return mark_safe(ret)


@register.filter
def entities_to_unicode(value):
    from HTMLParser import HTMLParser
    parser = HTMLParser()
    return parser.unescape(value)

# TEI conversion


@register.filter
def hand_description(description, request=None):
    "Convert TEI field into XML"

    # TODO: convert tei_old into tei into new format (see function below)
    return mark_safe(description.get_description_html(request and request.user and request.user.is_staff))


@register.filter
def tei(value):
    "Convert TEI field into XML"
    import re

    # tei text transform
    value = re.sub(ur'(<title level="a">)(.*?)(</title>)', ur"'\1\2\3'", value)

    #     value = re.sub(ur'<\s*([^/])\s*>', ur'<span class="tei-\1">', value)
    # >>> re.findall(ur'(<\s*(\S+)' + ur'\s*(?:(\S+)="([^"]*)")?' * 5 + '>)', r' <t a1="v1" a2="v2">')
    # [('<t a1="v1" a2="v2">', 't', 'a1', 'v1', 'a2', 'v2', '', '', '', '', '', '')]
    elements = re.findall(
        ur'(<\s*(\w+)' + ur'\s*(?:(\S+)="([^"]*)")?' * 5 + '>)', value)
    for element in elements:
        if element[1][0] == '/':
            continue
        element_html = '<span class="tei-' + element[1]
        i = 2
        while i < len(element):
            if not element[i]:
                break
            element_html += ' tei-a-%s__%s' % (element[i], element[i + 1])
            i += 2
        element_html += '">'
        value = value.replace(element[0], element_html)

    value = re.sub(ur'<\s*/[^>]*>', ur'</span>', value)
    value = re.sub(ur'\r?\n', ur'<br/>', value)
    value = mark_safe(value)

    return value


@register.assignment_tag(takes_context=True)
def load_hands(context, var_name):
    '''
        Usage:
            {% load_hands hand_ids as hands %}

        Loads all the Hand (and preload child graphs and annotations) into the hands template variable.
    '''

    hands_ids = context[var_name]

    from digipal.models import Graph, Hand
    # get all the graphs
    #.prefetch_related('graphs', 'graphs__annotation')
    # get all the graphs
    graph_ids_current_page = []
    for ids in hands_ids:
        graph_ids_current_page.extend(ids[1:])

    # get all the graphs on this page
    graphs = Graph.objects.filter(id__in=graph_ids_current_page).select_related('annotation', 'annotation__image',
                                                                                'idiograph', 'idiograph__allograph__character', 'idiograph__allograph__character').order_by(
        #'hand__scribe__name', 'hand__id', 'id')
        # JIRA 539: sort the graphs alphabetically
        'hand__scribe__name', 'hand__id', 'idiograph__allograph__character__ontograph__sort_order')

    hands = Hand.objects.in_bulk([g.hand_id for g in graphs])
#     .select_related('scribe',
#         'item_part', 'item_part__current_item', 'item_part__current_item__repository',
#         'assigned_place', 'assigned_date').prefetch_related('item_part__historical_items', 'item_part__historical_items__catalogue_numbers')

    # now organise the output by hand and attach their graphs to it
    # this assumes that graphs are sorted by hand id
    ret = []
    hand = None
    for graph in graphs:
        if not hand or graph.hand_id != hand.id:
            hand = hands[graph.hand_id]
            ret.append(hand)
            hand.graphs_template = []
        hand.graphs_template.append(graph)

    return ret


from digipal.utils import dplog


@register.simple_tag
def chrono(label):
    '''
        Used to measure how much time is spent rendering parts of any template

        Usage:
            {% chrono:"before listing" %}
        In debug mode it will print this on the std output:
            before listing: CURRENT DATE TIME
    '''
    from digipal.utils import get_mem

    if getattr(settings, 'DEBUG_PERFORMANCE', False):
        t = datetime.now()
        d = t - chrono.last_time
        chrono.last_time = t

        if label.endswith(':'):
            chrono.last_times[label[:-1]] = t
        slice_duration = t - t
        if label.startswith(':'):
            k = label[1:]
            if k in chrono.last_times:
                slice_duration = t - chrono.last_times[k]

        message = '%5dMB %8.4f %8.4f %s' % (
            get_mem(), d.total_seconds(), slice_duration.total_seconds(), label)
        dplog(message)

    return''


chrono.last_time = datetime.now()
chrono.last_times = {}
