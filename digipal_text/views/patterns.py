# -*- coding: utf-8 -*-
# from digipal_text.models import *
from django.shortcuts import render
from digipal import utils as dputils
from digipal_text.models import TextPattern
import regex as re
from digipal.utils import get_int_from_request_var
from django.db.utils import IntegrityError
from django.utils.text import slugify
from django.core.cache.backends.base import InvalidCacheBackendError
from digipal.templatetags import hand_filters, html_escape
from django.http.response import HttpResponse
from digipal.models import KeyVal
from datetime import datetime
from mezzanine.conf import settings

from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def patterns_view(request):
    ana = PatternAnalyser()
    context = ana.process_request_html(request)
    template = 'digipal_text/patterns2.html'
    ret = render(request, template, context)
    return ret


@csrf_exempt
def patterns_api_view(request, root, path):
    ana = PatternAnalyser()
    data = ana.process_request_api(request, root, path)
    format = data.get('format', 'json')
    if format in ['csv']:
        now = datetime.now()
        file_name = 'segments-%s-%s-%s.csv' % (now.day, now.month, now.year)
        ret = dputils.get_csv_response_from_rows(data['csv'], headings=[
                                                 'unitid', 'pattern_group', 'pattern_key', 'segment', 'variant'], filename=file_name)
    else:
        ret = dputils.get_json_response(data)
    return ret


class PatternAnalyser(object):
    def __init__(self):
        self.patterns = None
        self.segunits = None
        self.regexs = {}
        self.stats = {}
        self.toreturn = []
        self.messages = []
        self.namespace = 'default'
        self.options = {}
        self.variants = {}

    def add_message(self, message, atype='info'):
        self.messages.append({'message': message, 'type': atype})

    def get_unit_model(self):
        from exon.customisations.digipal_text.models import Entry
        ret = Entry
        return ret

    def process_request_html(self, request):
        ret = {'context_js': dputils.json_dumps(
            self.process_request_api(request, 'patterns'))}
        ret['advanced_search_form'] = 1
        ret['wide_page'] = True

        return ret

    def process_request_api(self, request, root, path=''):
        t0 = datetime.now()

        self.options = request.GET.copy()

        # what to return?
        toreturn = dputils.get_request_var(request, 'ret', root).split(',')
        self.toreturn = toreturn

        # make sure this is called AFTER self.options is set
        patterns = self.get_patterns()

        params = path.strip('/').split('/')

        data = None
        if request.body:
            data = dputils.json_loads(request.body)

        request_pattern = None
        request_patterni = None
        if root == 'patterns':
            if len(params) == 1:
                patternid = params[0]
                for i in range(0, len(patterns)):
                    if patterns[i]['id'] == patternid:
                        request_patterni = i
                        request_pattern = patterns[i]
                        break

        # Manages modifications
        modified = False

        if request.method == 'DELETE':
            if request_pattern:
                del patterns[request_patterni]
                modified = True

        if request.method == 'PUT':
            if request_pattern:
                if data['updated'] < request_pattern['updated']:
                    self.add_message(
                        'Change cancelled (this pattern was modified in the meantime)', 'error')
                else:
                    data['updated'] = dputils.now()
                    reorder = (patterns[i]['key'] != data['key'])
                    patterns[i] = data
                    self.auto_correct_pattern(patterns[i])
                    if reorder:
                        self.auto_correct_pattern_orders_and_numbers()
                    modified = True

        if self.move_pattern(request, root, data):
            modified = True

        # add new pattern if missing and client asked for it
        # TODO: not restful to change data on GET!
        # turn this into separate POST request.
        if 1:
            title_new = 'New Pattern'
            if not patterns or patterns[-1]['title'] != title_new:
                print 'ADD new pattern'
                patterns.append({
                    'id': dputils.get_short_uid(),
                    'key': slugify(unicode(title_new)),
                    'title': title_new,
                    'updated': dputils.now(),
                    'pattern': '',
                })
                modified = True

        if root == 'segunits':
            if request.method == 'POST':
                if data:
                    self.options.update(data)
                self.get_segunits()

        if modified:
            self.validate_patterns()
            self.save_patterns()

        pattern_errors = sum(
            [1 for pattern in self.patterns if 'error' in pattern])
        if pattern_errors:
            self.add_message('%s invalid patterns' % pattern_errors, 'warn')

        ret = {}

        if 'patterns' in toreturn:
            ret['patterns'] = self.get_patterns()
        if 'segunits' in toreturn:
            ret['segunits'] = self.get_json_from_segunits(toreturn)
        if 'variants' in toreturn:
            ret['variants'] = self.variants
        if 'stats' in toreturn:
            self.stats['duration_response'] = (
                datetime.now() - t0).total_seconds()
            ret['stats'] = self.stats
        ret['messages'] = self.messages
        ret['format'] = self.options.get('format', 'json')

        if ret['format'] == 'csv':
            ret['csv'] = self.get_csv_from_segunits()

        return ret

    def get_csv_from_segunits(self):
        ret = []
        for unit in self.get_segunits():
            for pattern in unit.patterns:
                if pattern[1]:
                    definition = self.get_pattern_from_id(pattern[0])
                    row = {
                        'unitid': unit.unitid,
                        'pattern_group': self.get_group_key_from_pattern_key(definition['key']),
                        'pattern_key': definition['key'],
                        'segment': pattern[1],
                        'variant': self.get_variant_from_segment(pattern[1]),
                    }
                    ret.append(row)
        return ret

    def get_variant_from_segment(self, segment):
        variant = segment
        for k, rgx in self.variant_patterns.iteritems():
            variant = rgx.sub(ur'<%s>' % k, variant)
        return variant

    def auto_correct_pattern(self, pattern):
        pattern['key'] = pattern.get('key', '').strip()
        pattern['title'] = pattern.get('title', '').strip()
        # if no key, slugify the title
        pattern['key'] = pattern['key'] or slugify(unicode(pattern['title']))
        # if no title, unslugify the key
        pattern['title'] = pattern['title'] or pattern['key'].replace(
            '_', ' > ').replace('-', '').title()
        # trim pattern
        pattern['pattern'] = pattern.get('pattern', '').strip()
        if not pattern.get('id', '').strip():
            pattern['id'] = dputils.get_short_uid()

    def move_pattern(self, request, root, data):
        ret = False
        if root == 'move_pattern' and data:
            if request.method == 'POST':
                move = [None, None]
                move[0] = self.get_pattern_index_from_key(data['pattern'])
                if data['previous'] == '':
                    move[1] = 0
                else:
                    move[1] = self.get_pattern_index_from_key(data['previous'])
                    if move[1] is not None:
                        move[1] += 1
                if move[0] is not None and move[1] is not None:
                    copy = self.patterns[move[0]]
                    self.patterns.insert(move[1], copy)
                    del self.patterns[move[0] +
                                      (1 if move[0] > move[1] else 0)]
                    self.auto_correct_pattern_orders_and_numbers()
                    ret = True
                else:
                    self.add_message(
                        'Can\'t move pattern, one of the references is wrong', 'error')

        return ret

    def get_pattern_index_from_key(self, pattern_key):
        ret = None

        for i in range(0, len(self.patterns)):
            if self.patterns[i]['key'] == pattern_key:
                ret = i
                break

        # not found? perhaps it's a group name
        if ret is None:
            group_key = self.get_group_key_from_pattern_key(pattern_key)
            if group_key == pattern_key:
                ret = self.get_pattern_index_from_key(group_key + '-1')

        return ret

    def get_group_key_from_pattern_key(self, pattern_key):
        ret = pattern_key

        if ret:
            ret = re.sub('-\d+$', '', ret)

        return ret

    def auto_correct_pattern_orders_and_numbers(self):
        '''
        Fix the order of the patterns and their numbers so:
            1. all patterns within a group are next to each other
            2. there are no gaps in the numbers
            3. order of appearance dictate the number

        e.g.
        p-3, q-4, p-2, q1
        =>
        p-1, p-2, q-1, q-2

        NOTE: we change self.patterns IN PLACE. This means that references
        to self.patterns outside this method are updated as well.
        '''
        # find the sequence of groups (groups)
        # and the sequence of patterns within each group (group_patterns)
        group_patterns = {}
        groups = []
        i = 0
        for p in self.patterns:
            i += 1
            group_key = self.get_group_key_from_pattern_key(p['key'])
            if group_key not in groups:
                groups.append(group_key)
                group_patterns[group_key] = []
            group_patterns[group_key].append(p)

        # group patterns together and renumber them
        i = 0
        for g in groups:
            j = 0
            for p in group_patterns[g]:
                j += 1
                self.patterns[i] = p
                if len(group_patterns[g]) == 1:
                    p['key'] = '%s' % g
                else:
                    p['key'] = '%s-%s' % (g, j)
                i += 1

        # trim the rest of the list
        while i < len(self.patterns):
            del self.patterns[i]

    def validate_patterns(self):
        patterns = self.get_patterns()
        for pattern in patterns:
            self.get_regex_from_pattern(patterns, pattern['id'])

    def get_json_from_segunits(self, toreturn):
        ret = []
        for unit in self.get_segunits():
            item = {
                'unit': '',
                'unitid': unit.unitid,
                'patterns': [],
            }
            if 'segunits.patterns' in toreturn:
                item['patterns'] = [{'id': pattern[0], 'instance': pattern[1]}
                                    for pattern in unit.patterns if pattern[1]]
            if 'segunits.unit' in toreturn:
                item['unit'] = unit.plain_content
            ret.append(item)
        return ret

    def get_segunits(self):
        if self.segunits is None:
            self.segment_units()
        return self.segunits

    def get_patterns(self):
        return self.patterns or self.load_patterns()

    def save_patterns(self):
        self.load_or_save_patterns(self.patterns)

    def load_patterns(self):
        if self.options.get('legacy', False) or not self.load_or_save_patterns():
            self.add_message('Reset legacy patterns', 'info')
            # not found, try legacy...
            self.load_or_save_patterns(self.load_patterns_legacy())

        return self.patterns

    def load_or_save_patterns(self, patterns=None):
        ''' Get (if patterns is None) or Set the patterns in the database
            in & out = dictionary
        '''
        key = 'api.textseg.%s.patterns' % slugify(unicode(self.namespace))
        if patterns:
            KeyVal.setjs(key, patterns)
        else:
            patterns = KeyVal.getjs(key)
        self.patterns = patterns
        return patterns

    def load_patterns_legacy(self):
        ret = []

        for pattern in TextPattern.objects.all().order_by('order'):
            ret.append({
                'id': dputils.get_short_uid(pattern.created),
                'key': pattern.key,
                'title': pattern.title,
                'pattern': pattern.pattern,
                'updated': pattern.modified,
            })

        helpers = [
            ('', ur''),
            ('number',
             ur'\b(duabus|duae|duas|due|duo|duorum|duos|dve|dimid|dimidi%|dimd%|centum|mill%|decem|nonaginta|nouem|octo|octoginta|quadringentis|quattuor|quatuor|quindecim|quinquaginta|quinque|sex|tres|tribus|uiginti|unam|uno|unius|unum|unus|[iuxlcmdMD]+(( | et )[iuxlcmdMD]+)?)\b'),
            ('measurement', ur'<number> <PATTERN>( et dimid%| et <number> <PATTERN>| <number> minus| <number> <PATTERN> minus)*'),
            ('person', ur'\w\w%'),
            ('name', ur'\w+(( et)? [A-Z]\w*)*'),
            ('money', ur'\b(solidos|libras|obolum|obolus|numm%|denar%)\b'),
            ('title', ur'\b(abbas|comes|capellanus|episcopus|frater|mater|presbiter|regina|rex|tagn%|taigni|tainn%|tangi|tangn%|tani|tanni%|tanorum|tanus|tegn%|teign%|teinorum|tenus|thesaurarius|uicecomes|uxor)\b'),
            ('hide', ur'\b(hid%|uirg%|urig%|fer.i%|agr%|car%c%)\b'),
            ('peasant', ur'\b(uillan%|bordar%|cott?ar%|costcet%|seru%)\b'),
            ('livestock', ur'\b(porc%|oues%|capra%|animal%|ronc%|runc%|uacas)\b'),
        ]
        for key, pattern in helpers:
            ret.append({
                'id': dputils.get_short_uid(),
                'key': 'helper_%s' % key,
                'title': key.title(),
                'pattern': pattern,
                'updated': dputils.now(),
            })

        return ret

    def init_variant_patterns(self):
        self.variant_patterns = {
            'name': ur'[A-Z]\w+(( et)? [A-Z]\w*)*',
        }
        for k in 'number'.split(','):
            p = self.get_pattern_from_key('helper_%s' % k)
            if p:
                p = p['pattern']
            else:
                p = k.upper()
            self.variant_patterns[k] = p
        for k, p in self.variant_patterns.iteritems():
            self.variant_patterns[k] = re.compile(p)

    def segment_units(self):
        self.segunits = []

        self.init_variant_patterns()

        t0 = datetime.now()

        # TODO: derive the info from the faceted_search settings.py or from a new
        # settings variable.

        # arguments
        args = self.options
        # unpack hilite
        args['hilite'] = args.get('hilite', '').split(',')
        args['hilite_groups'] = [self.get_group_key_from_pattern_key(self.get_pattern_from_id(
            pid)['key']) for pid in args['hilite'] if pid and self.get_pattern_from_id(pid)]
        args['ignore'] = args.get('ignore', '')
        args['exclude'] = args.get('exclude', '')

        args['ulimit'] = dputils.get_int(args.get('ulimit', 10), 10)
        args['urange'] = args.get('urange', '')

        # Get the text units
        hand_filters.chrono('units:')
        self.stats = stats = {'duration_segmentation': 0,
                              'range_size': 0, 'patterns': {}, 'groups': {}}
        for pattern in self.get_patterns():
            group = re.sub(ur'-\d+$', '', pattern['key'])
            self.stats['groups'][group] = 0

        for unit in self.get_unit_model().objects.filter(content_xml__id=4).iterator():
            # only fief
            types = unit.get_entry_type()
            if not types or 'F' not in types:
                continue

            # only selected range
            if not dputils.is_unit_in_range(unit.unitid, args['urange']):
                continue

            stats['range_size'] += 1

            # segment the unit
            self.segment_unit(unit, args)

            if unit.match_conditions:
                self.segunits.append(unit)

        hand_filters.chrono(':units')

        self.variants = [{'text': variant, 'hits': self.variants[variant]}
                         for variant in sorted(self.variants.keys())]

        # stats
        stats['result_size'] = len(self.segunits)
        stats['result_size_pc'] = int(
            100.0 * stats['result_size'] / stats['range_size']) if stats['range_size'] else 'N/A'

        # limit size of returned result
        if args['ulimit'] > 0:
            self.segunits = self.segunits[0:args['ulimit']]

        stats['duration_segmentation'] = (datetime.now() - t0).total_seconds()

    def get_condition(self, pattern):
        if pattern['key'].startswith('helper_'):
            return 'ignore'
        conditions = self.options.get('conditions', {})
        ret = conditions.get(pattern['id'], '')

        if pattern['id'] not in self.options['hilite']:
            if self.options['ignore'] == 'other_patterns':
                ret = 'ignore'
            elif self.options['ignore'] == 'other_groups':
                if self.get_group_key_from_pattern_key(pattern['key']) not in self.options['hilite_groups']:
                    ret = 'ignore'
            if self.options['exclude'] == 'this_group':
                if self.get_group_key_from_pattern_key(pattern['key']) in self.options['hilite_groups']:
                    ret = 'exclude'

        return ret

    def segment_unit(self, unit, args):
        patterns = self.get_patterns()
        unit.patterns = []
        found_groups = {}

        rgx_matched = re.compile(ur'[_<>]')

        unit.match_conditions = True

        self.get_plain_content_from_unit(unit)

        for pattern in patterns:
            patternid = pattern['id']
            if not patternid:
                continue
            condition = self.get_condition(pattern)
            if condition == 'ignore':
                continue

            # get regex from pattern
            rgx = self.get_regex_from_pattern(patterns, patternid)
            hilited = patternid in self.options['hilite']

            def markup_segment(match):
                segment = match.group(0)
                if rgx_matched.search(segment, 1):
                    return segment

                # mark it up
                span = '<span class="m ms">' if hilited else '<span class="m">'
                unit.patterns.append([patternid, segment])
                rep = ur'%s%s</span>' % (span, segment.replace(' ', '_'))

                # add variant
                if hilited and ('variants' in self.toreturn):
                    variant = self.get_variant_from_segment(segment)
                    self.variants[variant] = self.variants.get(variant, 0) + 1

                return rep

            # apply regex to unit
            if rgx:
                len_before = len(unit.plain_content)
                unit.plain_content, found = rgx.subn(
                    markup_segment, unit.plain_content, 1)
                found = len(unit.plain_content) != len_before

                if (condition == 'include' and not found) or (condition == 'exclude' and found):
                    unit.match_conditions = False
                if found:
                    found_groups[re.sub(ur'-\d+$', '', pattern['key'])] = 1
                    dputils.inc_counter(
                        self.stats['patterns'], pattern['id'], 1)
                else:
                    unit.patterns.append([patternid, ''])

        for group in found_groups:
            self.stats['groups'][group] += 1

        if found_groups:
            unit.plain_content = unit.plain_content.replace('_', ' ')

    def get_plain_content_from_unit(self, aunit):
        from django.core.cache import cache

        # get the plain contents from this object
        # print 'h1'

        ret = getattr(aunit, 'plain_content', None)
        if ret is None:
            plain_contents = getattr(self, 'plain_contents', None)

            if not plain_contents:
                # get the plain contents from the cache
                try:
                    from digipal.utils import get_cache
                    cache = get_cache('digipal_text_patterns')
                    plain_contents = cache.get('plain_contents')
                    #plain_contents = None
                except InvalidCacheBackendError, e:
                    pass
                if not plain_contents:
                    print 'REBUILD PLAIN CONTENT CACHE'
                    plain_contents = {}
                    for unit in self.get_unit_model().objects.filter(content_xml__id=4).iterator():
                        # TODO: find a way to call this dynamically as it is
                        # project-specific
                        plain_contents[unit.unitid] = self.preprocess_plain_text_custom(
                            unit.get_plain_content())
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

    def preprocess_plain_text_custom(self, content):
        # remove . because in some entries they are all over the place
        content = content.replace('[---]', '')
        content = content.replace('v', 'u')
        content = content.replace('7', 'et')
        content = content.replace('.', ' ').replace(',', ' ').replace(
            ':', ' ').replace('[', ' ').replace(']', ' ')
        content = content.replace(u'\u00C6', 'AE')
        content = content.replace(u'\u00E6', 'ae')
        content = content.replace(u'\u00A7', '')
        content = re.sub('\s+', ' ', content)
        content = content.strip()
        return content

    def get_pattern_from_key(self, key, try_helper=False):
        ret = None
        for pattern in self.get_patterns():
            if pattern['key'] == key:
                ret = pattern
                break
        if not ret and try_helper and not key.startswith('helper_'):
            ret = self.get_pattern_from_key('helper_%s' % key)

        return ret

    def get_pattern_from_id(self, patternid):
        ret = None
        for pattern in self.get_patterns():
            if pattern['id'] == patternid:
                ret = pattern
                break
        return ret

    def get_regex_from_pattern(self, patterns, patternid):
        ret = None
        pattern = self.get_pattern_from_id(patternid)

        if pattern:
            ret = self.regexs.get(patternid, None)
            if ret is None:
                if 'error' in pattern:
                    del pattern['error']
                ret = pattern['pattern']
                if ret:
                    # eg.  iii hidas et ii carrucas
                    # iiii hidis et i uirgata
                    # u hidis
                    # pro dimidia hida Hanc
                    # Ibi habet abbas ii hidas et dimidiam in dominio et ii carrucas et uillani dimidiam hidam
                    # hides:different units hid*: hida, uirgat*, ferdi*/ferlin*
                    # ? 47b1: et ui agris
                    # 41a2: iiii hidis et uirga et dimidia
                    #
                    # c bordarios x minus
                    # iiii libras et iii solidos i denarium minus
                    #

                    measurement = self.get_pattern_from_key(
                        'helper_measurement')

                    def replace_reference(match):
                        rep = match.group(0)
                        ref = match.group(1)
                        if ref == 'PATTERN':
                            return rep
                        # TODO: try other than helper_, not now as it might have
                        # accidental match
                        ref_pattern = self.get_pattern_from_key(
                            'helper_' + ref)
                        if ref_pattern:
                            rep = ref_pattern['pattern']
                        else:
                            if measurement:
                                # try singular helper
                                if ref.endswith('s'):
                                    ref_pattern = self.get_pattern_from_key(
                                        ('helper_%s' % ref)[0:-1])
                                    if ref_pattern:
                                        # let's apply measurement to this
                                        rep = ref_pattern['pattern']
                                        rep = measurement['pattern'].replace(
                                            '<PATTERN>', rep)

                        if not ref_pattern:
                            pattern['error'] = 'Reference to an unknown pattern: <%s>. Check the spelling.' % ref

                        return rep

                    i = 0
                    while 'error' not in pattern:
                        i += 1
                        before = ret
                        ret = re.sub(ur'<([^>]+)>', replace_reference, ret)
                        if i > 100:
                            pattern['error'] = 'Detected circular references in the pattern. E.g. p1 = <p2>; p2 = <p1>.'
                            break
                        if ret == before:
                            break

                    # LOW LEVEL SYNTACTIC SUGAR
                    if not 'error' in pattern:
                        #  e.g. x (<number>)? y
                        while True:
                            ret2 = ret
                            ret = re.sub(
                                ur'( |^)(\([^)]+\))\?( |$)', ur'(\1\2)?\3', ret2)
                            if ret == ret2:
                                break
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
                            ret = re.Regex(ret)
                        except Exception, e:
                            pattern['error'] = unicode(e)
                        finally:
                            self.regexs[patternid] = ret

                if 'error' in pattern:
                    ret = re.Regex('INVALID PATTERN')

        return ret
