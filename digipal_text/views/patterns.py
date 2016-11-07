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

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def patterns_view(request):
    hand_filters.chrono('PROCESS REQUEST:')
    ana = PatternAnalyser()
    ret = ana.process_request(request)
    hand_filters.chrono(':PROCESS REQUEST')
    return ret

class PatternAnalyser(object):

    patterns = {
        ur'<number>': ur'\b(duabus|aliam|dimid|dimidi%|unam|[iuxlcmd]+)\b',
    }

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

        context['advanced_search_form'] = 1
        context['variants'] = {}
        context['active_tab'] = request.REQUEST.get('active_tab', 'tab-units')

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
            self.segment_unit(unit, context, request)

            if unit.match_conditions:
                context['units'].append(unit)

        hand_filters.chrono(':units')

        variants = [{'text': variant, 'hits': context['variants'][variant]} for variant in sorted(context['variants'].keys())]
        context['variants'] = variants

        # stats
        stats['result_size'] = len(context['units'])
        stats['result_size_pc'] = int(100.0 * stats['result_size'] / stats['range_size']) if stats['range_size'] else 'N/A'
        for pattern in context['patterns'].values():
            pattern.unhits = stats['range_size'] - pattern.hits

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

    def segment_unit(self, unit, context, request):
        patterns = context['patterns']
        unit.patterns = []

        unit.match_conditions = True

        content_plain = self.get_plain_content_from_unit(unit)
        # remove . because in some entries they are all over the place
        content_plain = content_plain.replace('[---]', '')
        content_plain = content_plain.replace('v', 'u')
        content_plain = content_plain.replace('7', 'et')
        content_plain = content_plain.replace('.', ' ').replace(',', ' ').replace(':', ' ').replace('[', ' ').replace(']', ' ')
        content_plain = content_plain.replace(u'\u00C6', 'AE')
        content_plain = content_plain.replace(u'\u00E6', 'ae')
        content_plain = content_plain.replace(u'\u00A7', '')
        content_plain = re.sub('\s+', ' ', content_plain)
        content_plain = content_plain.strip()
        unit.plain_content = content_plain

        first_match_only = True

        for pattern_key, pattern in patterns.iteritems():
            if not pattern.id: continue
            if pattern.condition == 'ignore': continue

            # get regex from pattern
            rgx = self.get_regex_from_pattern(patterns, pattern_key)

            # apply regex to unit
            if rgx:
                found = False
                if 1:
                    for match in rgx.finditer(unit.plain_content):
                        found = True
                        unit.patterns.append([pattern_key, match.group(0)])
                        # mark it up
                        unit.plain_content = unit.plain_content[0:match.end()] + '</span>' + unit.plain_content[match.end():]
                        unit.plain_content = unit.plain_content[0:match.start()] + '<span class="m">' + unit.plain_content[match.start():]

                        if str(request.REQUEST.get('selected_patternid', 0)) == str(pattern.id):
                            variant = match.group(0)
                            variant = re.sub(self.patterns['<number>'], ur'<number>', variant)
                            variant = re.sub(ur'\b[A-Z]\w+\b', ur'<name>', variant)
                            context['variants'][variant] = context['variants'].get(variant, 0) + 1

                        if first_match_only: break

                if (pattern.condition == 'include' and not found) or (pattern.condition == 'exclude' and found):
                    unit.match_conditions = False
                if found:
                    pattern.hits += 1
                else:
                    unit.patterns.append([pattern_key, ''])


    def get_plain_content_from_unit(self, aunit):
        from django.core.cache import cache

        # get the plain contents from this object
        #print 'h1'

        ret = getattr(aunit, 'plain_content', None)
        if ret is None:
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
                if 0 and plain_content != ret:
                    print aunit.unitid
                    print repr(ret)
                    print repr(plain_content)
                ret = plain_content

            aunit.plain_content = ret

        return ret

    def get_regex_from_pattern(self, patterns, pattern_key):
        ret = None
        pattern = patterns.get(pattern_key, None)

        if pattern:
            ret = getattr(pattern, 'rgx', None)
            if ret is None:
                ret = pattern.pattern
                if ret:
                    # eg.  iii hidas et ii carrucas
                    # iiii hidis et i uirgata
                    # u hidis
                    # pro dimidia hida Hanc
                    # Ibi habet abbas ii hidas et dimidiam in dominio et ii carrucas et uillani dimidiam hidam
                    # hides:different units hid*: hida, uirgat*, ferdi*/ferlin*
                    # ? 47b1: et ui agris
                    # 41a2: iiii hidis et uirga et dimidia
                    ret = ret.replace(ur'<hides>', ur'<number> <hide>( et dimid%| et <number> <hide>)*')
                    ret = ret.replace(ur'<peasants>', ur'<number> <peasant>( et dimid%| et <number> <peasant>)*')
                    ret = ret.replace(ur'<livestocks>', ur'<number> <livestock>( et dimid%| et <number> <livestock>)*')
                    ret = ret.replace(ur'<moneys>', ur'<number> <money>( et dimid%| et <number> <money>)*')
                    
                    ret = ret.replace(ur'<title>', ur'\b(abbas|comes|capellanus|episcopus|frater|mater|presbiter|regina|rex|tagn%|taigni|tainn%|tangi|tangn%|tani|tanni%|tanorum|tanus|tegn%|teign%|teinorum|tenus|thesaurarius|uicecomes|uxor)\b')
                    ret = ret.replace(ur'<hide>', ur'(hid%|uirg%|urig%|fer.i%|agr%|car%c%)')
                    ret = ret.replace(ur'<peasant>', ur'(uillan%|bordar%|cott?ar%|costcet%|seru%)')
                    ret = ret.replace(ur'<livestock>', ur'(porc%|oues%|capra%|animal%|ronc%|runc%|uacas)')
                    ret = ret.replace(ur'<money>', ur'(solidos|libras)')

                    ret = ret.replace(ur'<number>', self.patterns['<number>'])
                    ret = ret.replace(ur'<person>', ur'\w\w%')
                    # !! How to remove Has? 28a1
                    ret = ret.replace(ur'<name>', ur'\w+(( et)? [A-Z]\w*)*')

                    #  e.g. x (<number>)? y
                    while True:
                        ret2 = ret
                        ret = re.sub(ur'( |^)(\([^)]+\))\?( |$)', ur'(\1\2)?\3', ret2)
                        if ret == ret2: break
                    # <person> habet <number> mansionem
                    ret = ret.replace(ur'%', ur'\w*')
                    # aliam = another
                    # unam = one
                    # dimidia = half
                    # duabus = two
                    ret = ret.replace(ur'7', ur'et')
                    if ret[0] not in [ur'\b', '^']:
                        ret = ur'\b' + ret
                    if not ret.endswith(ur'\b'):
                        ret = ret + ur'\b'
                    try:
                        pattern.pattern_converted = ret
                        ret = pattern.rgx = re.Regex(ret)
                    except Exception, e:
                        pattern.error = unicode(e)
                        ret = pattern.rgx = re.Regex('INVALID PATTERN')

        return ret

    def update_patterns_from_request(self, request, context):
        # get patterns from DB as as sorted dictionary
        # {key: TextPattern}
        action = request.REQUEST.get('action', '')

        print '-' * 80
        print 'UPDATE_PATTERNS_FROM_REQUEST'

        patterns = []
        fields = ['title', 'pattern', 'key', 'order', 'condition']

        pattern_list = list(TextPattern.objects.all())

        patternids = [p.id for p in pattern_list]
        for k,v in request.REQUEST.iteritems():
            pid = re.findall(ur'p_(\d+)_pattern', k)
            if pid and int(pid[0]) not in patternids:
                print pid[0]
                pattern_list.append(TextPattern.get_empty_pattern(aid=pid[0]))

        pattern_list.append(TextPattern.get_empty_pattern())

        for pattern in pattern_list:
            #print 'pattern #%s' % pattern.id
            pattern.condition = ''

            # modify the pattern from the request
            if action == 'update':
                modified = False
                pattern_in_request = False
                for field in fields:
                    value = request.REQUEST.get('p_%s_%s' % (pattern.id , field), '')
                    if field == 'key' and value:
                        value = slugify(value)
                    if field:
                        pattern_in_request = True
                    if unicode(value) != unicode(getattr(pattern, field, '')):
                        print '\t %s.%s = %s (<> %s)' % (pattern.key, field, repr(value), repr(getattr(pattern, field, '')))
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
                    if pattern.id and pattern_in_request:
                        #print '\t DELETE'
                        pattern.delete()
                    pattern = None

            # add the pattern to our list
            if pattern:
                patterns.append(pattern)

        # make sorted dict
        context['patterns'] = SortedDict()

        #print patterns
        patterns = sorted(patterns, key=lambda p: int(p.order or 0))
        print [p.key for p in patterns]
        #print patterns

        new_order = 0
        for pattern in patterns:
            new_order += 1
            pattern.order = new_order
            context['patterns'][pattern.key] = pattern

        # add new dummy pattern so user can extend the list on the front-end
        pattern = TextPattern.get_empty_pattern()
        if pattern.key not in context['patterns']:
            context['patterns'][pattern.key] = pattern

        for pattern in context['patterns'].values():
            pattern.hits = 0

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
