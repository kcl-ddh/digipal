# -*- coding: utf-8 -*-
# from digipal_text.models import *
from digipal_text.models import TextContentXMLStatus, TextContent, TextContentXML
import re
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.db import transaction
from digipal import utils
from django.utils.datastructures import SortedDict
from django.conf import settings
from digipal import utils as dputils
from digipal_text.models import TextPattern
import json

import logging
from digipal.utils import sorted_natural, get_int_from_request_var
from digipal.templatetags.hand_filters import chrono
from django.db.utils import IntegrityError
from django.utils.text import slugify
dplog = logging.getLogger('digipal_debugger')

def patterns_view(request):

    from datetime import datetime

    t0 = datetime.now()

    # TODO: derive the info from the faceted_search settings.py or from a new
    # settings variable.
    from exon.customisations.digipal_text.models import Entry

    context = {}

    # arguments
    args = request.REQUEST
    context['units_limit'] = get_int_from_request_var(request, 'units_limit', 10)
    context['units_range'] = args.get('units_range', '') or '25a1-62b2,83a1-493b3'

    context['wide_page'] = True

    # Update the patterns from the request
    update_patterns_from_request(request, context)

    # Get the text units
    context['units'] = []
    stats = {'response_time': 0}

    cnt = 0
    for unit in Entry.objects.all():
        # only transcriptions...
        cx = unit.content_xml
        if cx.id != 4: continue

        if not is_unit_in_range(unit, context['units_range']): continue

        # only first X units
        #if context['units_limit'] > 0 and cnt >= context['units_limit']: break

        cnt += 1
        context['units'].append(unit)
    
    stats['result_size'] = len(context['units'])
    if context['units_limit'] > 0:
        context['units'] = context['units'][0:context['units_limit']]

    stats['response_time'] = (datetime.now() - t0).total_seconds()
    context['stats'] = stats

    template = 'digipal_text/patterns.html'
    if request.is_ajax():
        template = 'digipal_text/patterns_fragment.html'
    ret = render(request, template, context)

    return ret

def update_patterns_from_request(request, context):
    # get patterns from DB as as sorted dictionary
    # {key: TextPattern}
    action = request.REQUEST.get('action', '')

    patterns = []
    fields = ['title', 'pattern', 'key', 'order']
    for pattern in (list(TextPattern.objects.all()) + [TextPattern.get_empty_pattern()]):
        print 'pattern #%s' % pattern.id

        # modify the pattern from the request
        if action == 'update':
            modified = False
            for field in fields:
                value = request.REQUEST.get('p_%s_%s' % (pattern.id , field), '')
                if field == 'key' and value:
                    value = slugify(value)
                if value != getattr(pattern, field, ''):
                    print '\t %s = %s' % (field, repr(value))
                    setattr(pattern, field, value)
                    modified = True

            pattern.pattern = pattern.pattern.strip()
            if pattern.pattern:
                if modified:
                    print '\t SAVE'
                    try:
                        pattern.save()
                    except IntegrityError, e:
                        # title or key already used...
                        from datetime import datetime
                        pattern.title += ' (duplicate %s)' % datetime.now()
                        pattern.key += ' (duplicate %s)' % datetime.now()
                    except:
                        raise
            else:
                if pattern.id:
                    print '\t DELETE'
                    pattern.delete()
                pattern = None

        # add the pattern to our list
        if pattern:
            patterns.append(pattern)

    # make sorted dict
    context['patterns'] = SortedDict()
    new_order = 0
    print patterns
    patterns = sorted(patterns, key=lambda p: p.order)
    print patterns
    for pattern in patterns:
        new_order += 1
        pattern.order = new_order
        context['patterns'][pattern.key] = pattern

    # add new dummy pattern so user can extend the list on the front-end
    pattern = TextPattern.get_empty_pattern()
    if pattern.key not in context['patterns']:
        context['patterns'][pattern.key] = pattern

def is_unit_in_range(unit, ranges):
    ret = False

    unit_keys = dputils.natural_sort_key(unit.unitid)

    for range in ranges.split(','):
        parts  = range.split('-')
        if len(parts) == 2:
            ret = (unit_keys >= dputils.natural_sort_key(parts[0])) and (unit_keys <= dputils.natural_sort_key(parts[1]))
        else:
            ret = unit.unitid == parts[0]
        if ret: break

    return ret
