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
from django.http.response import HttpResponse
from digipal.models import KeyVal
from datetime import datetime
dplog = logging.getLogger('digipal_debugger')

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
    ret = dputils.get_json_response(data)
    return ret

class PatternAnalyser(object):

    patterns_internal = {
        ur'<number>': ur'\b(duabus|aliam|dimid|dimidi%|unam|[ iuxlcmdMD]+( et [ iuxlcmdMD]+)?)\b',
    }
    
    def __init__(self):
        self.patterns = None
        self.segunits = None
        self.regexs = {}
        self.stats = {}
        self.messages = []
        self.namespace = 'default'
        self.options = {}

    def add_message(self, message, atype='info'):
        self.messages.append({'message': message, 'type': atype})
    
    def get_unit_model(self):
        from exon.customisations.digipal_text.models import Entry
        ret = Entry
        return ret

    def process_request_html(self, request):
        ret = {'context_js': dputils.json_dumps(self.process_request_api(request, 'patterns'))}
        ret['advanced_search_form'] = 1
        ret['wide_page'] = True

        return ret
        
    def process_request_api(self, request, root, path=''):
        t0 = datetime.now()
        
        self.options = request.GET.copy()

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
                    self.add_message('Change cancelled (this pattern was modified in the meantime)', 'error')
                else: 
                    data['updated'] = dputils.now()
                    patterns[i] = data
                    modified = True
                    
        if self.move_pattern(request, root, data): modified = True
        
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
                });
                modified = True
                
        if root == 'segunits':
            if request.method == 'POST':
                if data:
                    self.options.update(data)
        
        if modified:
            self.validate_patterns()
            self.save_patterns()

        # what to return?
        toreturn = request.REQUEST.get('ret', root).split(',')
        
        ret = {}
        
        if 'patterns' in toreturn:
            ret['patterns'] = self.get_patterns()
        if 'segunits' in toreturn:
            ret['segunits'] = self.get_json_from_segunits(toreturn)
        if 'stats' in toreturn:
            self.stats['duration_response'] = (datetime.now() - t0).total_seconds()
            ret['stats'] = self.stats
        ret['messages'] = self.messages

        return ret
    
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
                    if move[1] is not None: move[1] += 1
                if move[0] is not None and move[1] is not None:
                    copy = self.patterns[move[0]]
                    self.patterns.insert(move[1], copy)
                    del self.patterns[move[0] + (1 if move[0] > move[1] else 0)]
                    self.auto_correct_pattern_orders_and_numbers()
                    ret = True
                else:
                    self.add_message('Can\'t move pattern, one of the references is wrong', 'error')
        
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
                ret = self.get_pattern_index_from_key(group_key+'-1')

        return ret

    def get_group_key_from_pattern_key(self, pattern_key):
        ret = pattern_key
        
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
                item['patterns'] = [{'id': pattern[0], 'instance': pattern[1]} for pattern in unit.patterns if pattern[1]]
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
        
        return ret

    def segment_units(self):
        self.segunits = []

        t0 = datetime.now()

        # TODO: derive the info from the faceted_search settings.py or from a new
        # settings variable.

        context = {}
        context['variants'] = {}

        # arguments
        args = self.options
        context['ulimit'] = dputils.get_int(args.get('ulimit', 10), 10)
        #context['urange'] = args.get('urange', '') or '25a1-62b2,83a1-493b3'
        context['urange'] = args.get('urange', '')
        context['vpatternid'] = args.get('selected_patternid', 0)

        # Get the text units
        hand_filters.chrono('units:')
        self.stats = stats = {'duration_segmentation': 0, 'range_size': 0, 'patterns': {}, 'groups': {}}
        for pattern in self.get_patterns():
            group = re.sub(ur'-\d+$', '', pattern['key'])
            self.stats['groups'][group] = 0

        for unit in self.get_unit_model().objects.filter(content_xml__id=4).iterator():
            # only fief
            types = unit.get_entry_type()
            if not types or 'F' not in types: continue

            # only selected range
            if not self.is_unit_in_range(unit, context['urange']): continue

            stats['range_size'] += 1

            # segment the unit
            self.segment_unit(unit, context)

            if unit.match_conditions:
                self.segunits.append(unit)

        hand_filters.chrono(':units')

        variants = [{'text': variant, 'hits': context['variants'][variant]} for variant in sorted(context['variants'].keys())]
        context['variants'] = variants

        # stats
        stats['result_size'] = len(self.segunits)
        stats['result_size_pc'] = int(100.0 * stats['result_size'] / stats['range_size']) if stats['range_size'] else 'N/A'

        # limit size of returned result
        if context['ulimit'] > 0:
            self.segunits = self.segunits[0:context['ulimit']]

        stats['duration_segmentation'] = (datetime.now() - t0).total_seconds()
        context['stats'] = stats

    def get_condition(self, patternid):
        conditions = self.options.get('conditions', {})
        ret = conditions.get(patternid, '') 
        
        return ret

    def segment_unit(self, unit, context):
        patterns = self.get_patterns()
        unit.patterns = []
        found_groups = {}

        unit.match_conditions = True

        self.get_plain_content_from_unit(unit)

        first_match_only = True

        for pattern in patterns:
            patternid = pattern['id']
            if not patternid: continue
            condition = self.get_condition(patternid)
            # TODO: way to pass conditions in the request
            ##if pattern.condition == 'ignore': continue

            # get regex from pattern
            rgx = self.get_regex_from_pattern(patterns, patternid)

            # apply regex to unit
            if rgx:
                found = False
                if 1:
                    for match in rgx.finditer(unit.plain_content):
                        found = True
                        unit.patterns.append([patternid, match.group(0)])
                        # mark it up
                        unit.plain_content = unit.plain_content[0:match.end()] + '</span>' + unit.plain_content[match.end():]
                        unit.plain_content = unit.plain_content[0:match.start()] + '<span class="m">' + unit.plain_content[match.start():]

                        if str(context.get('selected_patternid', 0)) == str(pattern['id']):
                            variant = match.group(0)
                            variant = re.sub(self.patterns_internal['<number>'], ur'<number>', variant)
                            variant = re.sub(ur'\b[A-Z]\w+\b', ur'<name>', variant)
                            context['variants'][variant] = context['variants'].get(variant, 0) + 1

                        if first_match_only: break

                if (condition == 'include' and not found) or (condition == 'exclude' and found):
                    unit.match_conditions = False
                if found:
                    found_groups[re.sub(ur'-\d+$', '', pattern['key'])] = 1
                    dputils.inc_counter(self.stats['patterns'], pattern['id'], 1)
                else:
                    unit.patterns.append([patternid, ''])
        
        for group in found_groups:
            self.stats['groups'][group] += 1

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
                        # TODO: find a way to call this dynamically as it is project-specific
                        plain_contents[unit.unitid] = self.preprocess_plain_text_custom(unit.get_plain_content())
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
        content = content.replace('.', ' ').replace(',', ' ').replace(':', ' ').replace('[', ' ').replace(']', ' ')
        content = content.replace(u'\u00C6', 'AE')
        content = content.replace(u'\u00E6', 'ae')
        content = content.replace(u'\u00A7', '')
        content = re.sub('\s+', ' ', content)
        content = content.strip()
        return content

    def get_pattern_from_key(self, key):
        ret = None
        for pattern in self.get_patterns():
            if pattern['key'] == key:
                ret = pattern
                break
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
                    for keyword in 'hide,peasant,livestock,money'.split(','):
                        ret = ret.replace(ur'<'+keyword+ur's>', ur'<number> <'+keyword+ur'>( et dimid%| et <number> <'+keyword+ur'>| <number> minus| <number> <'+keyword+ur'> minus)*')
                        
#                     ret = ret.replace(ur'<hides>', ur'<number> <hide>( et dimid%| et <number> <hide>)*')
#                     ret = ret.replace(ur'<peasants>', ur'<number> <peasant>( et dimid%| et <number> <peasant>)*')
#                     ret = ret.replace(ur'<livestocks>', ur'<number> <livestock>( et dimid%| et <number> <livestock>)*')
#                     ret = ret.replace(ur'<moneys>', ur'<number> <money>( et dimid%| (et )?<number> <money>)*( minus)?')
                    
                    ret = ret.replace(ur'<title>', ur'\b(abbas|comes|capellanus|episcopus|frater|mater|presbiter|regina|rex|tagn%|taigni|tainn%|tangi|tangn%|tani|tanni%|tanorum|tanus|tegn%|teign%|teinorum|tenus|thesaurarius|uicecomes|uxor)\b')
                    ret = ret.replace(ur'<hide>', ur'\b(hid%|uirg%|urig%|fer.i%|agr%|car%c%)\b')
                    ret = ret.replace(ur'<peasant>', ur'\b(uillan%|bordar%|cott?ar%|costcet%|seru%)\b')
                    ret = ret.replace(ur'<livestock>', ur'\b(porc%|oues%|capra%|animal%|ronc%|runc%|uacas)\b')
                    ret = ret.replace(ur'<money>', ur'\b(solidos|libras|obolum|obolus|numm%|denar%)\b')

                    ret = ret.replace(ur'<number>', self.patterns_internal['<number>'])
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
                        #pattern.pattern_converted = ret
                        ret = re.Regex(ret)
                    except Exception, e:
                        pattern['error'] = unicode(e)
                        ret = re.Regex('INVALID PATTERN')
                    finally:
                        self.regexs[patternid] = ret

        return ret

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
