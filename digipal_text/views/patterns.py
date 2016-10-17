# -*- coding: utf-8 -*-
# from digipal_text.models import *
from django.shortcuts import render
from django.utils.datastructures import SortedDict
from digipal import utils as dputils
from digipal_text.models import TextPattern
import regex as re
import logging
from digipal.utils import get_int_from_request_var
from django.db.utils import IntegrityError
from django.utils.text import slugify
from django.core.cache.backends.base import InvalidCacheBackendError
from digipal.templatetags import hand_filters, html_escape
dplog = logging.getLogger('digipal_debugger')

def patterns_view(request):
    hand_filters.chrono('PROCESS REQUEST:')
    ana = PatternAnalyser()
    ret = ana.process_request(request)
    hand_filters.chrono(':PROCESS REQUEST')
    return ret

class PatternAnalyser(object):
    
    def get_unit_model(self):
        from exon.customisations.digipal_text.models import Entry
        ret = Entry
        return ret

    def process_request(self, request):
        self.request = request

        from datetime import datetime

        t0 = datetime.now()

        # TODO: derive the info from the faceted_search settings.py or from a new
        # settings variable.

        context = {}

        context['conditions'] = [
            {'key': '', 'label': 'May have'},
            {'key': 'include', 'label': 'Must have'},
            {'key': 'exclude', 'label': 'Must not have'},
            {'key': 'ignore', 'label': 'Ignore'},
        ]

        # arguments
        args = request.REQUEST
        context['units_limit'] = get_int_from_request_var(request, 'units_limit', 10)
        #context['units_range'] = args.get('units_range', '') or '25a1-62b2,83a1-493b3'
        context['units_range'] = args.get('units_range', '')

        context['wide_page'] = True

        # Update the patterns from the request
        hand_filters.chrono('patterns:')
        self.update_patterns_from_request(request, context)
        hand_filters.chrono(':patterns')

        # Get the text units
        hand_filters.chrono('units:')
        context['units'] = []
        stats = {'response_time': 0, 'range_size': 0}

        for unit in self.get_unit_model().objects.filter(content_xml__id=4).iterator():
            #cx = unit.content_xml

            # only transcription
            #if cx.id != 4: continue

            # only fief
            types = unit.get_entry_type()
            #print unit.unitid, types
            if not types or 'F' not in types: continue

            # only selected range
            if not self.is_unit_in_range(unit, context['units_range']): continue

            stats['range_size'] += 1

            # segment the unit
            self.segment_unit(unit, context)

            if unit.match_conditions:
                context['units'].append(unit)

        hand_filters.chrono(':units')

        # stats
        stats['result_size'] = len(context['units'])
        stats['result_size_pc'] = int(100.0 * stats['result_size'] / stats['range_size']) if stats['range_size'] else 'N/A'

        # limit size of returned result
        if context['units_limit'] > 0:
            context['units'] = context['units'][0:context['units_limit']]

        stats['response_time'] = (datetime.now() - t0).total_seconds()
        context['stats'] = stats

        # render template
        template = 'digipal_text/patterns.html'
        if request.is_ajax():
            template = 'digipal_text/patterns_fragment.html'

        hand_filters.chrono('template:')
        ret = render(request, template, context)
        hand_filters.chrono(':template')

        return ret

    def segment_unit(self, unit, context):
        patterns = context['patterns']
        unit.patterns = []
        unit.match_conditions = True
        
        content_plain = self.get_plain_content_from_unit(unit)

        for pattern_key, pattern in patterns.iteritems():
            if not pattern.id: continue
            if pattern.condition == 'ignore': continue

            # get regex from pattern
            rgx = self.get_regex_from_pattern(patterns, pattern_key)

            # apply regex to unit
            if rgx:
                found = False
                if 1:
                    for match in rgx.finditer(content_plain):
                        found = True
                        unit.patterns.append([pattern_key, match.group(0)])
                if (pattern.condition == 'include' and not found) or (pattern.condition == 'exclude' and found):
                    unit.match_conditions = False

    def get_plain_content_from_unit(self, aunit):
        from django.core.cache import cache

        # get the plain contents from this object
        #print 'h1'
        plain_contents = getattr(self, 'plain_contents', None)

        if not plain_contents:
            # get the plain contents from the cache
            try:
                from django.core.cache import get_cache
                cache = get_cache('digipal_text_patterns')
                plain_contents = cache.get('plain_contents')
                #plain_contents = None
            except InvalidCacheBackendError, e:
                pass
            if not plain_contents:
                print 'REBUILD PLAIN CONTENT CACHE'
                plain_contents = {}
                for unit in self.get_unit_model().objects.filter(content_xml__id=4).iterator():
                    plain_contents[unit.unitid] = unit.get_plain_content()
                    if unit.unitid in ['25a2', '25a2']:
                        print unit.unitid, repr(plain_contents[unit.unitid][0: 20])
                cache.set('plain_contents', plain_contents, None)
            setattr(self, 'plain_contents', plain_contents)

        ret = plain_contents.get(aunit.unitid, None)
        if ret is None:
            plain_content = aunit.get_plain_content()
#             if plain_content != ret:
#                 print aunit.unitid
#                 print repr(ret)
#                 print repr(plain_content)
            ret = plain_content

        return ret

    def get_regex_from_pattern(self, patterns, pattern_key):
        ret = None
        pattern = patterns.get(pattern_key, None)

        if pattern:
            ret = getattr(pattern, 'rgx', None)
            if ret is None:
                ret = pattern.pattern
                if ret:
                    # <person> habet <number> mansionem
                    ret = ret.replace(ur'<person>', ur'\w+')
                    ret = ret.replace(ur'<number>', ur'\.?[ivxlcm]+\.?')
                    print ret
                    ret = pattern.rgx = re.Regex(ret)

        return ret

    def update_patterns_from_request(self, request, context):
        # get patterns from DB as as sorted dictionary
        # {key: TextPattern}
        action = request.REQUEST.get('action', '')

        patterns = []
        fields = ['title', 'pattern', 'key', 'order', 'condition']
        for pattern in (list(TextPattern.objects.all()) + [TextPattern.get_empty_pattern()]):
            #print 'pattern #%s' % pattern.id
            pattern.condition = ''

            # modify the pattern from the request
            if action == 'update':
                modified = False
                for field in fields:
                    value = request.REQUEST.get('p_%s_%s' % (pattern.id , field), '')
                    if field == 'key' and value:
                        value = slugify(value)
                    if unicode(value) != unicode(getattr(pattern, field, '')):
                        #print '\t %s = %s (<> %s)' % (field, repr(value), repr(getattr(pattern, field, '')))
                        setattr(pattern, field, value)
                        if field != 'condition':
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
                        #print '\t DELETE'
                        pattern.delete()
                    pattern = None

            # add the pattern to our list
            if pattern:
                patterns.append(pattern)

        # make sorted dict
        context['patterns'] = SortedDict()
        new_order = 0
        #print patterns
        patterns = sorted(patterns, key=lambda p: p.order)
        #print patterns
        for pattern in patterns:
            new_order += 1
            pattern.order = new_order
            context['patterns'][pattern.key] = pattern

        # add new dummy pattern so user can extend the list on the front-end
        pattern = TextPattern.get_empty_pattern()
        if pattern.key not in context['patterns']:
            context['patterns'][pattern.key] = pattern

    def is_unit_in_range(self, unit, ranges):
        ret = False

        ranges = ranges.strip()

        if not ranges: return True

        unit_keys = dputils.natural_sort_key(unit.unitid)

        for range in ranges.split(','):
            parts  = range.split('-')
            if len(parts) == 2:
                ret = (unit_keys >= dputils.natural_sort_key(parts[0])) and (unit_keys <= dputils.natural_sort_key(parts[1]))
            else:
                ret = unit.unitid == parts[0]
            if ret: break

        return ret
