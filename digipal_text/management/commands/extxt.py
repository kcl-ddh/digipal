# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import re
from optparse import make_option
from digipal.utils import sorted_natural

# pm dpxml convert exon\source\rekeyed\converted\EXON-1-493-part1.xml exon\source\rekeyed\conversion\xml2word.xslt > exon\source\rekeyed\word\EXON-word.html
# pm extxt wordpre exon\source\rekeyed\word\EXON-word.html exon\source\rekeyed\word\EXON-word2.html
# pandoc "exon\source\rekeyed\word\EXON-word2.html" -o "exon\source\rekeyed\word\EXON-word.docx"

import unicodedata
from xhtml2pdf.pisa import showLogging
def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

class Command(BaseCommand):
    help = """
Text conversion tool
    
Commands:
    wordpre PATH_TO_XHTML OUTPUT_PATH
        Preprocess the MS Word document

    pattern PATH_TO_XHTML PATTERN
        Test a regexp pattern on a XHTML file

    upload PATH_TO_XHTML CONTENTID
        Import XHTML file
        
    hundorder SHIRE
        Find the best order for hundreds in a shire
        
    setoptorder SHIRE HUNDRED
        Set the optimal order for a shire

"""
    
    args = 'locus|email'
    option_list = BaseCommand.option_list + (
        make_option('--db',
            action='store',
            dest='db',
            default='default',
            help='Name of the target database configuration (\'default\' if unspecified)'),
        make_option('--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run, don\'t change any data.'),
        )

    def handle(self, *args, **options):
        
        self.log_level = 3
        
        self.options = options
        
        if len(args) < 1:
            print self.help
            exit()
        
        command = args[0]
        self.cargs = args[1:]
        
        known_command = False

        if command == 'wordpre':
            known_command = True
            self.word_preprocess()

        if command == 'pattern':
            known_command = True
            self.pattern()
        
        if command == 'upload':
            known_command = True
            self.upload()
            
        if command == 'hundorder':
            known_command = True
            self.hundorder()
        
        if command == 'hundorderga':
            known_command = True
            self.hundorderga()
        
        if command == 'setoptorder':
            known_command = True
            self.setoptorder_command()
        
        if command == 'handentry':
            known_command = True
            self.handentry_command()

        if known_command:
            print 'done'
            pass
        else:
            print self.help

    def handentry_command(self):
        from digipal_text.models import TextContentXML
        
        #hands = TextContentXML.objects.filter(text_content__type__slug=='codicology')
        
        stints = self.get_stints()
        
        # entries = self.get_entries()
        
        pages = {}
        for sinfo in stints:
            for number in self.get_page_numbers_from_stint(sinfo):
                number = str(number)
                if number not in pages:
                    pages[number] = {}
                pages[number][sinfo['hand']] = 1
                
        for number in sorted_natural(pages.keys()):
            print number, pages[number].keys()
        
        print '%s pages, %s with single hand.' % (len(pages.keys()), len([p for p in pages.values() if len(p.keys()) > 1])) 
        
    def get_page_numbers_from_stint(self, sinfo):
        # {'note': u'opens and ends quire', 'x': [[u'353', u'r', u'1'], [u'355', u'v', u'9']], 'extent': u'353r1-5v9', 'hand': 'theta'}
        # => ['353r', '353v', '354r', '354v', '355r', '355v']        
        ret = []
        for n in range(int(sinfo['x'][0][0]), int(sinfo['x'][1][0]) + 1):
            ret.append(str(n) + 'r')
            ret.append(str(n) + 'v')
        
        if sinfo['x'][0][1] == 'v':
            ret.pop(0)
        if sinfo['x'][1][1] == 'r':
            ret.pop()
            
        return ret

    def get_entries(self):
        # Get all entry numbers from the translation
        print 'get entries'
        ret = []
        
        from digipal_text.models import TextContentXML
        text = TextContentXML.objects.filter(text_content__type__slug='translation').first()
        
        for entry in re.findall(ur'<span data-dpt="location" data-dpt-loctype="entry">(\d+)([ab])(\d+)</span>', text.content):
            entry = list(entry)
            entry[1] = 'r' if entry[0] == 'a' else 'v'
            ret.append({'entry': ''.join(entry), 'x': entry})
        
        return ret
    
    def get_stints(self):
        ''' get the stints info from the hand descriptions
            [
                [{'note': u'ends and opens quire', 'extent': u'502v11-3v18', 'x': [[502, v, 11], [503, v, 18]], 'hand': 'alpha'}, ...],
                ...
            ]
        '''
        from django.core.cache import get_cache
        cache = get_cache('digipal_compute')
        
        stints = cache.get('stints')
        
        if stints is not None: return stints
        
        print 'get stints'
        
        from digipal.models import HandDescription
        hdescs = HandDescription.objects.all().select_related('hand')
        #hdescs = hdescs.filter(hand__label='mu')

        stints = []
        
        # <span data-dpt="stint" data-dpt-cat="chars">493v4-6</span><
        stint_pattern = re.compile(ur'(?musi)<span data-dpt="stint" data-dpt-cat="chars">\s*([^<]+)\s*</span>(?:\s*\[([^\]]*)\])?')
        for hdesc in hdescs:
            print '-' * 50
            hlabel = ('%s' % hdesc.hand)
            print hlabel
            description = hdesc.description
            
            # Extract the stints section from the description
            desc = re.sub(ur'(?musi).*What does he write(.*?)data-dpt="heading".*', ur'\1', description)
 
            stints += self.extract_stints_info_from_desc(desc, hlabel, stint_pattern)

            desc = re.sub(ur'(?musi).*Previously unidentified(.*?)data-dpt="heading".*', ur'\1', description)
            
            stints += self.extract_stints_info_from_desc(desc, hlabel, stint_pattern)
            
            #print desc
            #exit()
            
        cache.set('stints', stints)
            
        return stints

    def extract_stints_info_from_desc(self, desc, hlabel, stint_pattern):
        ret = []
        
        # Extract the stints: {}
        for stint in stint_pattern.findall(desc):
            # e.g.
            # {'note': u'ends and opens quire', 'extent': u'502v11-3v18', 'hand': 'alpha'}
            sinfo = {'hand': hlabel, 'extent': stint[0], 'note': stint[1]}
            #print sinfo
            sinfo = self.expand_stint_extent(sinfo)
            if sinfo:
                ret.append(sinfo)
            
        return ret

    def expand_stint_extent(self, sinfo):
        # eg. sinfo = {'note': u'ends and opens quire', 'extent': u'502v11-3v18', 'hand': 'alpha'}
        # out= sinfo = {'note': u'ends and opens quire', 'extent': u'502v11-3v18', 'x': [[502, v, 11], [3, v, 18]], 'hand': 'alpha'}
        extent = sinfo['extent']
        sinfo['x'] = []
        parts = extent.split('-')
        if parts == 1:
            parts.append(parts[0])
        show = ''
        for part in parts:
            # e.g. 502v11
            ps = re.findall(ur'^(\d+)?([rv])?(\d+)?$', part)
            for p in ps:
                # e.g.  [(u'496', u'v', u'18'), (u'19', u'', u'')], 'extent': u'496v18-19'
                if len(p[0]) == len(''.join(p)):
                    # => [(u'496', u'v', u'18'), (u'', u'', u'19')], 'extent': u'496v18-19'
                    p = p[::-1] 
#                 if ('' in p):
#                     show = 'implicit'
                sinfo['x'].append(list(p))

        if len(sinfo['x']) == 0:
            show = 'Invalid format'
        else:
            if len(sinfo['x']) == 1:
                #show = 'Only one part'
                sinfo['x'].append(sinfo['x'][0][:])
            
            #print sinfo
            
            if sinfo['x'][1][1] == '':
                sinfo['x'][1][1] = sinfo['x'][0][1]
            
            copy_len = len(sinfo['x'][0][0]) - len(sinfo['x'][1][0])
            if copy_len > 0:
                #show = 'Relative folio number'
                sinfo['x'][1][0] = sinfo['x'][0][0][0:copy_len] + sinfo['x'][1][0]
        
            if int(sinfo['x'][1][0]) > 600:
                show = 'Folio number too large'
        
        if show:
            print show
            print sinfo
            sinfo = None
        
        return sinfo 
        
    def setoptorder_command(self):
        
        shire = self.cargs[0]
        hundreds = self.cargs[1]
        
        hundreds = eval(hundreds)
        
        self.setoptorder(shire, hundreds, column='optimal')
    
    def setoptorder(self, shire, hundreds, column='optimal'):
        from digipal.management.commands.utils import sqlWrite, sqlSelect, dictfetchall
        from django.db import connections
        wrapper = connections['default']

        command = '''UPDATE exon_hundred
        SET hundredalorder''' + column + ''' = %s
        WHERE lower(shire) = lower(%s)
        '''
        sqlWrite(wrapper, command, ['', shire], False)

        i = 0
        for hundred in hundreds:
            i += 1
            print hundred, i
            
            find = '''SELECT * from exon_hundred
            WHERE lower(shire) = lower(%s)
            AND hundrednameasenteredintomasterdatabase = %s
            '''
            
            recs = dictfetchall(sqlSelect(wrapper, find, [shire, hundred]))
            
            if not recs:
                command = '''INSERT INTO exon_hundred
                (hundredalorder''' + column + ''', shire, hundrednameasenteredintomasterdatabase)
                VALUES
                (%s, %s, %s)
                '''
                sqlWrite(wrapper, command, [i, shire, hundred], False)
            else:
                command = '''UPDATE exon_hundred
                SET hundredalorder''' + column + ''' = %s
                WHERE lower(shire) = lower(%s)
                AND hundrednameasenteredintomasterdatabase = %s
                '''
                sqlWrite(wrapper, command, [i, shire, hundred], False)
            
        wrapper.commit()

    def hundorder(self):
        shire = self.cargs[0]
        tics = self.get_tics_from_shire(shire)
        
        print
        for tic in tics:
            print '%s (%s): %s' % (tic['name'], len(tic['entries']), ', '.join([entry['hundred'] for entry in tic['entries']]))

        # create adjacency matrix of the 'before' graph
        # bm[hundred1][hundred2] = 3 means that hundred1 precedes hundred2 3 times
         
        bm = {}
        def add_count(h1, h2):
            if h1 not in bm:
                bm[h1] = {}
            if h2 not in bm[h1]:
                bm[h1][h2] = 0
            bm[h1][h2] += 1
            
         
        for tic in tics:
            i = 0
            treated = {}
            for entry in tic['entries']:
                if entry['hundred'] in treated: continue
                h = entry['hundred']
                if h not in bm: bm[h] = {}
                for entry2 in tic['entries'][i+1:]:
                    add_count(h, entry2['hundred'])
                i += 1
                treated[entry['hundred']] = 1
        
        print
        for h1 in bm:
            print h1, bm[h1]

        print '\nReenterance'
        for r in sorted([(h1, bm[h1][h1]) for h1 in bm if h1 in bm[h1]], key=lambda r: r[1], reverse=True):
            print r[1], r[0]

        print '\nConflicts'
        from copy import deepcopy
        sbm = deepcopy(bm)
        for h1 in bm:
            print h1
            for h2 in bm[h1]:
                
                if h1 == h2:
                    # remove self references
                    del sbm[h1][h2]
                else:
                    if h2 in bm and h1 in bm[h2]:
                        print '', bm[h1][h2], h2, bm[h2][h1]
                        
                        if bm[h1][h2] * 3 <= bm[h2][h1]:
                            del sbm[h1][h2]
                        else:
                            if not (bm[h2][h1] * 3 <= bm[h1][h2]):
                                if sbm[h2] and h1 in sbm[h2]: del sbm[h2][h1]
                                if sbm[h1] and h2 in sbm[h1]: del sbm[h1][h2]
        
        # create a new order
        hs = []
        while True:
            if len(sbm.keys()) == 0:
                break
            sbmo = sorted(sbm.keys(), key=lambda h: len(sbm[h]))
            hs.insert(0, sbmo[0])
            
            for h in sbm:
                if sbmo[0] in sbm[h]: del sbm[h][sbmo[0]]
            
            del sbm[sbmo[0]]
        
        print
        print hs
        print 'cost: ', self.get_cost_from_hundreds(tics, hs)
        self.setoptorder(shire, hs, column='')

        
        
    def hundorderga(self):
        shire = self.cargs[0]
        tics = self.get_tics_from_shire(shire)

        
        # vr is numerical hundredal order supplied by the team
        vr = {}
        none_counter = 1000
        
        # hundreds is an arbitrary numerical mapping for the hundred names
        # eg. hundreds = {A: 0, B: 1}
        hundreds = {}
        
        l = -1
        for tic in tics:
            for entry in tic['entries']:
                h = entry['hundred']
                
                # create 'vr'
                if entry['hundredalorder'] is None:
                    # None => assign a large number
                    if h not in vr.values():
                        none_counter += 1
                        vr['%s' % none_counter] = h
                else:
                    vr[entry['hundredalorder']] = h
                
                # create 'hundreds'
                if h not in hundreds:
                    l += 1
                    hundreds[h] = l
                
                # add hundred index/order into the data struct
                # e.g. entry['hundred'] == B => entry['ho'] = 1
                entry['ho'] = hundreds[h]

        # convert vr into a standard candidate solution
        from digipal.utils import sorted_natural
        # vr = [B, A]
        vr = [vr[k] for k in sorted_natural(vr.keys())]
        # vr = [1, 0]
        #vr = [u'Winnianton', u'Tybesta', u'Rillaton', u'Connerton', u'Rialton', u'Pawton', u'Stratton', u'Fawton']
        #vr = [u'Lifton', u'South Tawton', u'Black Torrington', u'Hartland', u'Merton', u'Fremington', u'North Tawton', u'Crediton', u'Exminster', u'Braunton', u'Bampton', u'Shirwell', u'South Molton', u'Cliston', u'Silverton', u'Hemyock', u'Ottery St Mary', u'Molland', u'Wonford', u'Budleigh', u'Witheridge', u'Tiverton', u'Halberton', u'Kerswell', u'Axminster', u'Alleriga', u'Colyton', u'Chillington', u'Axmouth', u'Teignbridge', u'Ermington', u'unknown', u'Diptford', u'Plympton', u'Walkhampton']

        vr = [hundreds[label] for label in vr]
        vr = range(0, len(vr))
        seed = [vr]
        
        #seed.append([12, 32, 7, 21, 13, 17, 18, 31, 2, 8, 26, 22, 4, 15, 34, 10, 5, 24, 23, 25, 19, 0, 33, 27, 20, 11, 29, 14, 30, 28, 6, 9, 16, 1, 3])
        #seed.append([12, 32, 7, 21, 13, 17, 18, 31, 2, 8, 22, 4, 15, 10, 5, 24, 34, 23, 25, 19, 0, 27, 33, 20, 11, 3, 14, 29, 30, 6, 9, 28, 16, 1, 26])
        
#             seed.append([13, 31, 16, 38, 10, 4, 42, 9, 5, 27, 43, 0, 14, 39, 35, 21, 28, 25, 37, 32, 36, 29, 34, 6, 7, 40, 11, 41, 23, 2, 33, 17, 19, 3, 24, 12, 22, 26, 20, 1, 30, 15, 8, 18])
#
#             seed.append([26, 27, 31, 43, 0, 37, 42, 41, 9, 16, 34, 29, 33, 11, 28, 21, 12, 2, 19, 4, 24, 6, 20, 10, 17, 39, 14, 1, 40, 7, 35, 30, 3, 22, 5, 15, 13, 38, 8, 36, 18, 32, 25, 23])
#             seed.append([43, 13, 9, 21, 0, 5, 11, 42, 19, 31, 20, 41, 29, 23, 24, 32, 16, 39, 30, 27, 14, 28, 34, 26, 2, 25, 4, 6, 33, 1, 35, 10, 17, 40, 7, 3, 37, 38, 15, 8, 12, 22, 18, 36])

        #seed.append([4, 5, 27, 9, 34, 26, 33, 0, 37, 29, 6, 14, 43, 31, 41, 16, 21, 32, 10, 28, 11, 39, 2, 19, 35, 3, 12, 17, 22, 23, 40, 13, 24, 36, 38, 20, 1, 30, 42, 7, 15, 8, 18, 25])
        #seed.append([13, 31, 16, 38, 10, 4, 42, 9, 5, 27, 43, 0, 14, 39, 35, 21, 28, 25, 37, 32, 36, 29, 34, 6, 7, 40, 11, 41, 23, 2, 33, 17, 19, 3, 24, 12, 22, 26, 20, 1, 30, 15, 8, 18])
        
        #seed.append([20, 0, 1, 9, 5, 7, 24, 27, 41, 38, 43, 46, 21, 2, 10, 11, 44, 30, 4, 12, 34, 25, 37, 39, 42, 33, 23, 22, 13, 28, 3, 14, 32, 15, 16, 45, 17, 8, 40, 6, 26, 18, 36, 29, 31, 35, 19])
        #seed.append([44, 20, 45, 41, 37, 46, 0, 9, 5, 7, 24, 27, 21, 2, 4, 22, 34, 10, 25, 11, 30, 12, 13, 28, 3, 38, 23, 14, 16, 32, 43, 17, 40, 26, 42, 15, 8, 18, 36, 33, 29, 1, 31, 19, 35, 39, 6])
        #seed.append([38, 36, 20, 0, 15, 1, 46, 42, 9, 44, 31, 5, 7, 39, 40, 24, 27, 21, 41, 2, 10, 11, 45, 34, 30, 35, 4, 33, 25, 12, 22, 23, 13, 6, 28, 3, 37, 14, 16, 43, 32, 17, 26, 8, 18, 29, 19])

        self.print_candidate(vr, tics, hundreds)
                
        # v1 = 1,0  means B,A
        v1 = range(0, len(hundreds))
        
        self.print_candidate(v1, tics, hundreds)
        
        from digipal.optimiser import Optimiser
        
        optimiser = Optimiser()
        optimiser.reset(seed=seed, costfn=lambda v: self.get_cost(tics, v), printfn=lambda v: self.print_candidate(v, tics, hundreds))
        optimiser.start()
        vs = optimiser.getSolution()
        
        self.print_candidate(vs, tics, hundreds)
            
        '''
Cornwall (16/9)
--------

Many possible solutions

[2, 5, 7, 3, 0, 4, 6, 1]
[u'Pawton', u'Connerton', u'Rialton', u'Stratton', u'Winnianton', u'Rillaton', u'Fawton', u'Tybesta']
Cost: 9; Len: 8
done

[7, 2, 3, 4, 0, 1, 5, 6]
[u'Rialton', u'Pawton', u'Stratton', u'Rillaton', u'Winnianton', u'Tybesta', u'Connerton', u'Fawton']
Cost: 9; Len: 8
done

Devon (104/62)
---------

[13, 29, 32, 18, 14, 15, 10, 8, 9, 2, 16, 17, 4, 6, 5, 19, 11, 0, 7, 28, 20, 21, 3, 22, 12, 23, 24, 30, 31, 1, 25, 26, 27]
[u'Lifton', u'South Tawton', u'Molland', u'Cliston', u'Black Torrington', u'Hartland', u'Merton', u'Fremington', u'North Tawton', u'Exminster', u'Braunton', u'Bampton', u'Shirwell', u'South Molton', u'Silverton', u'Wonford', u'Witheridge', u'Teignbridge', u'Ermington', u'Crediton', u'Hemyock', u'Budleigh', u'Plympton', u'Tiverton', u'Halberton', u'Kerswell', u'Axmouth', u'Walkhampton', u'Ottery St Mary', u'Diptford', u'Axminster', u'Colyton', u'Chillington']
Cost: 71; Len: 33


[u'Lifton', u'South Molton', u'South Tawton', u'Black Torrington', u'Hartland', u'Merton', u'North Tawton', u'Axmouth', u'Fremington', u'Exminster', u'Crediton', u'Shirwell', u'Bampton', u'Silverton', u'Hemyock', u'Braunton', u'Diptford', u'Budleigh', u'Kerswell', u'Walkhampton', u'Molland', u'Cliston', u'Colyton', u'Plympton', u'Witheridge', u'Halberton', u'Teignbridge', u'Wonford', u'Ottery St Mary', u'Axminster', u'Tiverton', u'Ermington', u'Chillington']
126

[u'Alleriga', u'Lifton', u'South Molton', u'South Tawton', u'Black Torrington', u'Hartland', u'Merton', u'North Tawton', u'Axmouth', u'Fremington', u'Exminster', u'Crediton', u'Shirwell', u'Bampton', u'Silverton', u'Hemyock', u'Braunton', u'Diptford', u'Walkhampton', u'Budleigh', u'Molland', u'Cliston', u'Kerswell', u'Colyton', u'Plympton', u'Witheridge', u'Halberton', u'Teignbridge', u'Wonford', u'Ottery St Mary', u'Axminster', u'Tiverton', u'Ermington', u'Chillington', u'unknown']


[12, 32, 7, 34, 21, 13, 17, 18, 31, 2, 8, 4, 22, 15, 10, 5, 24, 23, 25, 19, 0, 27, 20, 11, 29, 30, 28, 6, 33, 9, 16, 1, 26, 3, 14]
[u'Lifton', u'South Tawton', u'Black Torrington', u'Molland', u'Hartland', u'Merton', u'Fremington', u'North Tawton', u'Crediton', u'Exminster', u'Braunton', u'Shirwell', u'Bampton', u'South Molton', u'Cliston', u'Silverton', u'Hemyock', u'Wonford', u'Budleigh', u'Witheridge', u'Teignbridge', u'Tiverton', u'Halberton', u'Kerswell', u'Axminster', u'Colyton', u'Axmouth', u'Alleriga', u'Ottery St Mary', u'Chillington', u'Ermington', u'Diptford', u'unknown', u'Plympton', u'Walkhampton']
Cost: 62; Len: 35

Gen 2000. Cost 66. Best: 66. Pop: 105
[12, 32, 6, 7, 21, 13, 17, 18, 31, 2, 8, 22, 4, 15, 10, 5, 34, 16, 26, 24, 23, 25, 19, 0, 1, 33, 27, 20, 11, 29, 30, 3, 14, 28, 9]
[u'Lifton', u'South Tawton', u'Alleriga', u'Black Torrington', u'Hartland', u'Merton', u'Fremington', u'North Tawton', u'Crediton', u'Exminster', u'Braunton', u'Bampton', u'Shirwell', u'South Molton', u'Cliston', u'Silverton', u'Molland', u'Ermington', u'unknown', u'Hemyock', u'Wonford', u'Budleigh', u'Witheridge', u'Teignbridge', u'Diptford', u'Ottery St Mary', u'Tiverton', u'Halberton', u'Kerswell', u'Axminster', u'Colyton', u'Plympton', u'Walkhampton', u'Axmouth', u'Chillington']
Cost: 66; Len: 35

Gen 2000. Cost 66. Best: 66. Pop: 105
[12, 32, 7, 21, 13, 17, 18, 31, 2, 8, 4, 34, 22, 15, 10, 5, 24, 23, 25, 19, 27, 20, 11, 33, 29, 30, 28, 6, 9, 0, 16, 1, 3, 14, 26]
[u'Lifton', u'South Tawton', u'Black Torrington', u'Hartland', u'Merton', u'Fremington', u'North Tawton', u'Crediton', u'Exminster', u'Braunton', u'Shirwell', u'Molland', u'Bampton', u'South Molton', u'Cliston', u'Silverton', u'Hemyock', u'Wonford', u'Budleigh', u'Witheridge', u'Tiverton', u'Halberton', u'Kerswell', u'Ottery St Mary', u'Axminster', u'Colyton', u'Axmouth', u'Alleriga', u'Chillington', u'Teignbridge', u'Ermington', u'Diptford', u'Plympton', u'Walkhampton', u'unknown']

[12, 32, 7, 21, 13, 17, 18, 31, 2, 8, 26, 22, 4, 15, 34, 10, 5, 24, 23, 25, 19, 0, 33, 27, 20, 11, 29, 14, 30, 28, 6, 9, 16, 1, 3]
[12, 32, 7, 21, 13, 17, 18, 31, 2, 8, 22, 4, 15, 10, 5, 24, 34, 23, 25, 19, 0, 27, 33, 20, 11, 3, 14, 29, 30, 6, 9, 28, 16, 1, 26]
[u'Lifton', u'South Tawton', u'Black Torrington', u'Hartland', u'Merton', u'Fremington', u'North Tawton', u'Crediton', u'Exminster', u'Braunton', u'Bampton', u'Shirwell', u'South Molton', u'Cliston', u'Silverton', u'Hemyock', u'Molland', u'Wonford', u'Budleigh', u'Witheridge', u'Teignbridge', u'Tiverton', u'Ottery St Mary', u'Halberton', u'Kerswell', u'Plympton', u'Walkhampton', u'Axminster', u'Colyton', u'Alleriga', u'Chillington', u'Axmouth', u'Ermington', u'Diptford', u'unknown']
Cost: 68; Len: 35

[12, 32, 7, 21, 13, 17, 18, 31, 2, 34, 8, 22, 4, 15, 10, 5, 24, 23, 19, 25, 27, 20, 11, 30, 6, 9,
 28, 0, 16, 26, 1, 3, 33, 14, 29]
[u'Lifton', u'South Tawton', u'Black Torrington', u'Hartland', u'Merton', u'Fremington', u'North Tawton', u'Crediton', u'Exminster', u'Molland', u'Braunton', u'Bampton', u'Shirwell', u'South Molton', u'Cliston', u'Silverton', u'Hemyock', u'Wonford', u'Witheridge', u'Budleigh', u'Tiverton', u'Halberton', u'Kerswell', u'Colyton', u'Alleriga', u'Chillington', u'Axmouth', u'Teignbridge', u'Ermington', u'unknown', u'Diptford', u'Plympton', u'Ottery St Mary', u'Walkhampton', u'Axminster']
Cost: 71; Len: 35


Dorset (None/41)
---------

NO REF TO ENTRY NUMBERS => NO ORDER!!!!


Somerset (82/62)
---------

[61, 39, 49, 30, 19, 44, 1, 40, 53, 2, 33, 3, 4, 13, 21, 51, 54, 10, 58, 52, 11, 12, 5, 14, 16, 24, 22, 15, 17, 62, 43, 27, 25, 6, 60, 23, 18, 59, 35, 41, 47, 55, 45, 57, 46, 38, 7, 36, 50, 32, 42,
 20, 0, 34, 28, 48, 8, 29, 37, 31, 56, 9, 26]
[u'Coker', u'Yeovil: Houndsborough', u'Pitminster', u'Lydeard', u'South Petherton', u'Loxley', u'Williton', u'Yeovil: Lyatts', u'Minehead', u'Bruton: Blachethorna', u'Reynaldsway', u'Milborne/Horethorne', u'Milverton', u'Bulstone', u'Cheddar', u'Sheriffs Brompton', u'Brompton Regis', u'North Petherton', u'Creech', u'Cutcombe', u'Cannington', u'Carhampton', u'Abdick', u'Andersfield', u'Winterstoke', u'Bedminster', u'Chew', u'Taunton', u'Portbury', u'Martock', u'Lyatts', u'Kingsbury', u'Hartcliffe', u'Keynsham', u'Congresbury', u'Bempstone', u'Frome: Frome', u'North Curry', u'Bruton: Wincanton', u'Yeovil: Stone', u'South Brent', u'Dulverton', u'Whitestone', u'Winsford', u'Monkton', u'Milverton or Brompton Regis', u'Bath', u'Thurlbear', u'Huntspill', u'Crewkerne', u'Carhampton / Williton', u'Yeovil: Tintinhull', u'Chewton', u'Somerton', u'Wiveliscombe', u'Frome: Frome/Downhead', u'Frome: Wellow', u'Wellington', u'Thornfalcon', u'Wells', u'Cleeve', u'Frome: Kilmersdon', u'Bruton: Bruton']
Cost: 77; Len: 63

[1, 5, 60, 2, 38, 4, 62, 54, 27, 55, 10, 33, 13, 11, 24, 14, 12, 16, 22, 15, 17, 25, 6, 28, 20, 57, 58, 23, 56, 7, 36, 43, 45, 9, 37, 51, 59, 34, 18, 32, 0, 29, 47, 35, 52, 39, 48, 50, 53, 19, 61, 42, 8, 49, 21, 44, 26, 31, 3, 46, 30, 40, 41]
[u'Williton', u'Abdick', u'Congresbury', u'Bruton: Blachethorna', u'Milverton or Brompton Regis', u'Milverton', u'Martock', u'Brompton Regis', u'Kingsbury', u'Dulverton', u'North Petherton', u'Reynaldsway', u'Bulstone', u'Cannington', u'Bedminster', u'Andersfield', u'Carhampton', u'Winterstoke', u'Chew', u'Taunton', u'Portbury', u'Hartcliffe', u'Keynsham', u'Wiveliscombe', u'Yeovil: Tintinhull', u'Winsford', u'Creech', u'Bempstone', u'Cleeve', u'Bath', u'Thurlbear', u'Lyatts', u'Whitestone', u'Frome: Kilmersdon', u'Thornfalcon', u'Sheriffs Brompton', u'North Curry', u'Somerton', u'Frome: Frome', u'Crewkerne', u'Chewton', u'Wellington', u'South Brent', u'Bruton: Wincanton', u'Cutcombe', u'Yeovil: Houndsborough', u'Frome: Frome/Downhead', u'Huntspill', u'Minehead', u'South Petherton', u'Coker', u'Carhampton / Williton', u'Frome: Wellow', u'Pitminster', u'Cheddar', u'Loxley', u'Bruton: Bruton', u'Wells', u'Milborne/Horethorne', u'Monkton', u'Lydeard', u'Yeovil: Lyatts', u'Yeovil: Stone']
Cost: 70; Len: 63

Wiltshire (None)
---------

NO REF TO ENTRY NUMBERS => NO ORDER!!!!

            '''
    def get_tics_from_shire(self, shire):
        ret = []
        
        from exon.customisations.digipal_lab.views.hundreds import get_hundreds_view_context
        
        class MyRequest:
            def __init__(self, request):
                self.REQUEST = request
        
        context = get_hundreds_view_context(MyRequest({'oc': ''}))
        
        info = {}
        for shire_data in context['shires']:
            if shire_data['name'].lower() == shire:
                info = shire_data
                break
        
        print 'optimise... %s' % shire

        if info:
            # 1. get all the hundreds in a list

            tics = info['tics']

            # remove redundant hundreds in entries list
            for tic in tics:
                tic['entries_all'] = tic['entries'][:]
                tic['entries'] = []
                last_hundred = None
                for entry in tic['entries_all']:
                    hundred = entry['hundred']
                    # discard '-'
                    if len(hundred) < 2: continue
                    # discard missing ellis number
                    if entry['ellisref'] in [None, '-', '']: continue
                    
                    if last_hundred is None or last_hundred != hundred:
                        tic['entries'].append(entry)
                    last_hundred = hundred
            
            # remove tic with only one entry
            tics = [tic for tic in tics if len(tic['entries']) > 1]
            
            ret = tics

        return ret
            
    
    def print_candidate(self, v1, tics, hundreds):
        print '-' * 10
        print v1
        print self.get_vector_labels(hundreds, v1)
        print 'Cost: %s; Len: %s' % (self.get_cost(tics, v1), len(v1))
        
    def get_cost_from_function(self, tics, get_hhunber_from_entry):
        ''' Returns a cost for out-of-seq hundreds for a given
        hundredal numbering. get_hhunber_from_entry takes an entry dict
        and returns a number for that entry'''
        ret = 0
        
        for tic in tics:
            last_ho = None
            last_last_ho = None
            for entry in tic['entries']:
                #ho = v1.index(entry['ho'])
                ho = get_hhunber_from_entry(entry)
                
                # 8 11 10 not ok
                # 10 11 10 OK
                if last_ho is not None and\
                    last_ho > ho and\
                    last_last_ho != ho:
                    ret += 1
                last_last_ho = last_ho
                last_ho = ho
        
        return ret

    def get_cost_from_hundreds(self, tics, hs):
        ''' hs = [first_hundred_name, second_hundred_name, ...] '''
        return self.get_cost_from_function(tics, lambda entry: hs.index(entry['hundred']))
        
    def get_cost(self, tics, v1):
        ''' v1 = [first_hundred_entry_ho, ...] '''
        return self.get_cost_from_function(tics, lambda entry: v1.index(entry['ho']))
    
    def get_vector_labels(self, hundreds, v1):
        hr = {}
        for k, v in hundreds.iteritems():
            hr[v] = k
        return [hr[i] for i in v1]

    def get_unique_matches(self, pattern, content):
        ret = re.findall(pattern, content)
        
        import json

        print repr(pattern)

        matches = {}
        for match in ret:
            key = json.dumps(match)
            matches[key] = matches.get(key, 0) + 1
            
        for key, freq in sorted([(key, freq) for key, freq in matches.iteritems()], key=lambda item: item[1]):
            print '%3d %s' % (freq, key)
        
        print len(ret)
        
        return ret

    def pattern(self):
        input_path = self.cargs[0]
        pattern = self.cargs[1]
        
        from digipal.utils import read_file
        
        content = read_file(input_path)

        print
        self.get_unique_matches(pattern, content)
        
        print

    def upload(self):
        input_path = self.cargs[0]
        recordid = self.cargs[1]
        
        import regex
        from digipal.utils import re_sub_fct
        from digipal.utils import read_file
        content = read_file(input_path)
        
        # extract body
        l0 = len(content)
        content = regex.sub(ur'(?musi).*<body*?>(.*)</body>.*', ur'<p>\1</p>', content)
        if len(content) == l0:
            print 'ERROR: could not find <body> element'
            return

        # unescape XML tags coming from MS Word
        # E.g. &lt;margin&gt;Д‘ mМѓ&lt;/margin&gt;
        content = regex.sub(ur'(?musi)&lt;(/?[a-z]+)&gt;', ur'<\1>', content)

        # convert &amp; to #AMP#
        content = content.replace('&amp;', '#AMP#')
        
        # line breaks from MS
        content = regex.sub(ur'(?musi)\|', ur'<span data-dpt="lb" data-dpt-src="ms"></span>', content)

        # line breaks from editor
        content = regex.sub(ur'(?musi)<br/>', ur'<span data-dpt="lb" data-dpt-src="prj"></span>', content)

        # <st>p</st> => ṕ
        content = regex.sub(ur'(?musi)<st>\s*p\s*</st>', ur'ṕ', content)
        # <st>q</st> => ƣ
        content = regex.sub(ur'(?musi)<st>\s*q\s*</st>', ur'ƣ', content)

        # <del>de his</del> =>
        content = regex.sub(ur'(?musi)<del>(.*?)</del>', ur'', content)

        # Folio number
        # [fol. 1. b.] or [fol. 1.]
        # TODO: check for false pos. or make the rule more strict
        #content = re.sub(ur'(?musi)\[fol.\s(\d+)\.(\s*(b?)\.?)\]', ur'</p><span data-dpt="location" data-dpt-loctype="locus">\1\3</span><p>', content)
        self.sides = {'': 'r', 'b': 'v', 'a': 'r'}
        def get_side(m):
            side = self.sides.get(m.group(3), m.group(3))
            ret = ur'</p><span data-dpt="location" data-dpt-loctype="locus">%s%s</span><p>' % (m.group(1), side)
            return ret
        content = re_sub_fct(content, ur'(?musi)\[fol.\s(\d+)\.(\s*(b?)\.?)\]', get_side, regex)

        # Entry number
        # [1a3]
        # TODO: check for false pos. or make the rule more strict
        content = regex.sub(ur'(?musi)(§?)\[(\d+(a|b)\d+)]', ur'</p><p>\1<span data-dpt="location" data-dpt-loctype="entry">\2</span>', content)

        # <margin></margin>
        content = content.replace('<margin>', '<span data-dpt="note" data-dpt-place="margin">')
        content = content.replace('</margin>', '</span>')
         
        # to check which entities are left
        ##ocs = set(regex.findall(ur'(?musi)(&[#\w]+;)', content))

        self.c = 0

        def markup_expansions(match):
            m = match.group(0)
            ret = m

            #if '[' not in m: return m
            
            # don't convert if starts with digit as it's most likely a folio or entry number
            if m[0] <= '9' and m[0] >= '0':
                return m
            
            self.c += 1
            #if self.c > 100: exit()
            
            # ũ[ir]g̃[a]
            # abbr =
            
            # ABBR
            abbr = regex.sub(ur'\[.*?\]', ur'', m)
            
            # o<sup>o</sup> -> <sup>o</sup>
            abbr = regex.sub(ur'(\w)(<sup>\1</sup>|<sub>\1</sub>)', ur'\2', abbr)
            
            # EXP
            exp = regex.sub(ur'\[(.*?)\]', ur'<i>\1</i>', m)
            # b
            exp = regex.sub(ur'\u1d6c', ur'b', exp)
            # l/ -> l
            exp = regex.sub(ur'\u0142', ur'l', exp)
            # d- -> d
            exp = regex.sub(ur'\u0111', ur'd', exp)
            # h
            exp = regex.sub(ur'\u0127', ur'h', exp)
            # e.g. hid4as
            exp = regex.sub(ur'\d', ur'', exp)

            ##exp = regex.sub(ur'ṕ', ur'p', exp)
            exp = regex.sub(ur'ƣ', ur'q', exp)
            
            
            # Remove abbreviation signs
            # ! we must make sure that the content no longer contains entities!
            # E.g. &amp; => &
            # ;
            exp = regex.sub(ur';', ur'', exp)
            # :
            exp = regex.sub(ur':', ur'', exp)
            # ÷
            exp = regex.sub(ur'÷', ur'', exp)
            # ʇ
            exp = regex.sub(ur'ʇ', ur'', exp)
            # e.g. st~
            exp = remove_accents(exp)
            
            # remove sub/sup from the expanded form as it usually contains abbreviation mark
            # Exception: hiđ4[ae]ϛ {ϛ 7 dim̃[idia] uirga.}
            # here we keep ϛ because it is used as an insertion sign
            ###exp = regex.sub(ur'<su(p|b)>.*?</su(p|b)>', ur'', exp)
            # general removal
            exp = regex.sub(ur'<su(p|b)>.*?</su(p|b)>', ur'', exp)
            
            if abbr != exp and exp:
#                 if len(abbr) > len(exp):
#                     # potentially spurious expansions
#                     print repr(abbr), repr(exp)
                ret = ur'<span data-dpt="abbr">%s</span><span data-dpt="exp">%s</span>' % (abbr, exp)
            
            ##print repr(m), repr(ret)
            
            return ret
        
        content = re_sub_fct(content, ur'(?musi)(:|;|÷|\w|(<sup>.*?</sup>)|(<sub>.*?</sub>)|\[|\])+', markup_expansions, regex)

        # Bal〈dwini〉 =>
        content = regex.sub(ur'(?musi)(〈[^〈〉]{1,30}〉)', ur'<span data-dpt="exp">\1</span>', content)
        
        # sup
        content = regex.sub(ur'(?musi)<sup>', ur'<span data-dpt="hi" data-dpt-rend="sup">', content)

        # sub
        content = regex.sub(ur'(?musi)<sub>', ur'<span data-dpt="hi" data-dpt-rend="sub">', content)
        content = regex.sub(ur'(?musi)</sup>|</sub>', ur'</span>', content)

        # convert #AMP# to &amp;
        content = content.replace('#AMP#', '&amp;')

        # import
        from digipal_text.models import TextContentXML
        text_content_xml = TextContentXML.objects.get(id=recordid)
        text_content_xml.content = content
        
        #print repr(content)
        
        text_content_xml.save()

    def word_preprocess(self):
        input_path = self.cargs[0]
        output_path = self.cargs[1]
        
        from digipal.utils import write_file, read_file
        
        # regex will consider t̃ as \w, re as \W
        import regex as re
        
        content = read_file(input_path)
        
        # expansions
        # m_0 -> m[od]o_0
        #self.get_unique_matches(pattern, content)
        pattern = ur'(?mus)([^\w<>\[\]])(m<sup>0</sup>)([^\w<>\[\]&])'
        content = re.sub(pattern, ur'\1m[od]o<sup>o</sup>\3', content)

        pattern = ur'(?mus)([^\w<>\[\]])(uocat<sup>r</sup>)([^\w<>\[\]&])'
        content = re.sub(pattern, ur'\1uocat[u]r<sup>r</sup>\3', content)

        pattern = ur'(?mus)([^\w<>\[\]])(q<sup>1</sup>)([^\w<>\[&])'
        content = re.sub(pattern, ur'\1q[u]i<sup>i</sup>\3', content)
        
        # These involve the superscript 9s and 4s, with a few 2s caught up with
        # the fours and one recurrent subscript 4. 4 seems to be the commonest
        # number, and my suggested list will allow us to make inroads
        
        # -e<sub>4</sub> -> e cauda
        # ! rekeyers have somtimes used <sub> BEFORE the e (28 vs 3630)
        pattern = ur'(?mus)(e<sub>4</sub>)([^\w<>\[\]&])'
        content = re.sub(pattern, ur'ę\2', content)

        # he4c -> hęc
        pattern = ur'(?mus)([^\w<>\[\]/;](h|H))(e<sub>4</sub>)(c[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1ę\4', content)

        # e<sub>9</sub> ->
        # 6599 occurrences
        pattern = ur'(?mus)([\w<>\[\]/;]+)(<sup>9</sup>)([^\w<>\[\]&])'
        content = re.sub(pattern, ur'\1\2[us]\3', content)
        
        # most frequent 9 within word: nem9culi (199 out of 237 occurences)
        pattern = ur'(?mus)([^\w<>\[\]/;]nem)(<sup>9</sup>)((culi|cłi)[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[us]\3', content)

        # 2: stands for different symbols: u (-> ar / ra); a -> ua

        # q2drag4 -> q[ua]2drag4[enarias]
        pattern = ur'(?mus)([^\w<>\[\]/;])(q<sup>2</sup>drag<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1q[u]a<sup>a</sup>drag<sup>4</sup>[enarias]\3', content)
        # q2drag̃ -> q[ua]2drag[enarias]
        pattern = ur'(?mus)([^\w<>\[\]/;])(q<sup>2</sup>)(drag̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1q[u]a<sup>a</sup>\3[enarias]\4', content)
        # q2dragenar~ -> q[ua]2dragenar~[ias]
        pattern = ur'(?mus)([^\w<>\[\]/;])(q<sup>2</sup>)(dragenar̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1q[u]a<sup>a</sup>\3[ias]\4', content)
        # q2dragenarias -> q[ua]2dragenarias
        pattern = ur'(?mus)([^\w<>\[\]/;])(q<sup>2</sup>)(dragenarias[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1q[u]a<sup>a</sup>\3', content)
        
        # q2ndo -> q[u]a2do
        pattern = ur'(?mus)([^\w<>\[\]/;]q)(<sup>2</sup>)(ndo[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[u]a<sup>a</sup>\3', content)

        # cap2s -> cap2[ra]s
        pattern = ur'(?mus)([^\w<>\[\]/;]cap)(<sup>2</sup>)(s[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ra]\3', content)
        # cap2 -> cap[ra]a !?
        pattern = ur'(?mus)([^\w<>\[\]/;]cap)(<sup>2</sup>)([^\w<>\[\]/&])'
        #content = re.sub(pattern, ur'\1[r]a<sup>a</sup>\3', content)
        content = re.sub(pattern, ur'\1<sup>2</sup>[ra]\3', content)

        # p2ti -> p2[ra]ti
        pattern = ur'(?mus)([^\w<>\[\]/;]p)(<sup>2</sup>)(ti[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ra]\3', content)

        # ext2 = ext[ra]
        pattern = ur'(?mus)([^\w<>\[\]/;]ext)(<sup>2</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ra]\3', content)

        # eq2s = eq[u]a2s
        pattern = ur'(?mus)([^\w<>\[\]/;]eq)(<sup>2</sup>)(s[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[u]a<sup>a</sup>\3', content)

        # q2 = q[u]a2
        pattern = ur'(?mus)([^\w<>\[\]/;]q)(<sup>2</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[u]a<sup>a</sup>\3', content)

        # sup2dicta =
        pattern = ur'(?mus)([^\w<>\[\]/;]sup)(<sup>2</sup>)(dict(ã|a)s?[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ra]\3', content)

        # s;
        pattern = ur'(?mus)([^\w<>\[\]/;]s;)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[ed]\2', content)

        # 4: stands for bolt which is a very generic abbreviation

        # porc4 -> porc4[os]
        pattern = ur'(?mus)([^\w<>\[\]/;]porc)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[os]\3', content)

        # recep4 -> recep4[it]
        pattern = ur'(?mus)([^\w<>\[\]/;]rece)(p̃|p<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[it]\3', content)

        # ag4 -> ag[ros]
        pattern = ur'(?mus)([^\w<>\[\]/;]a)(g̃|g<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ros]\3', content)

        # hid4 -> hid[e<sup>e</sup>]
        pattern = ur'(?mus)([^\w<>\[\]/;]hid)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ę]\3', content)
        
        # den4 -> den4[arios]
        pattern = ur'(?mus)([^\w<>\[\]/;]den)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[arios]\3', content)

        # dim4 -> den4[idiam]
        pattern = ur'(?mus)([^\w<>\[\]/;]di)(m̃|m<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[idiam]\3', content)
        
        # inlong4 -> inlong4[itudine]
        pattern = ur'(?mus)([^\w<>\[\]/;]inlong)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[itudine]\3', content)

        # long4 -> long4[itudine]
        pattern = ur'(?mus)([^\w<>\[\]/;]long)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[itudine]\3', content)

        # longitud4 -> longitud4[itudine]
        pattern = ur'(?mus)([^\w<>\[\]/;]longitud)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ine]\3', content)

        # lat4 -> lat4[itudine]
        pattern = ur'(?mus)([^\w<>\[\]/;]lat)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[itudine]\3', content)

        # latit4 -> lat4[itudine]
        pattern = ur'(?mus)([^\w<>\[\]/;]latit)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[udine]\3', content)

        # nemor4 -> nemor4[is]
        pattern = ur'(?mus)([^\w<>\[\]/;]nemor)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[is]\3', content)

        # quadrag4 -> quadrag4[enarias]
        pattern = ur'(?mus)([^\w<>\[\]/;])(quadrag<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1quadrag<sup>4</sup>[enarias]\3', content)

        # seru4 -> seru4[um]
        pattern = ur'(?mus)([^\w<>\[\]/;]seru)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[um]\3', content)

        # ten -> ten4[uit]
        pattern = ur'(?mus)([^\w<>\[\]/;]ten)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[uit]\3', content)

        # carr4 -> carr4[ucas]
        pattern = ur'(?mus)([^\w<>\[\]/;]carr)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ucas]\3', content)
        # car4r -> carr4[ucas] (correct error from rekeyers)
        pattern = ur'(?mus)([^\w<>\[\]/;]car)(<sup>4</sup>)r([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1r\2[ucas]\3', content)
        # carr~ -> carr~[ucas]
        pattern = ur'(?mus)([^\w<>\[\]/;])(carr̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ucas]\3', content)

        # bord4 -> bord4[arios]
        pattern = ur'(?mus)([^\w<>\[\]/;]bord)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[arios]\3', content)

        # mans4 -> mans4[arios]
        pattern = ur'(?mus)([^\w<>\[\]/;]man)(s̃|s<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ionem]\3', content)

        # 9 1
        
        # un9qisq: / un9q1sq -> un9[us]q[u]1isq:[ue]
        pattern = ur'(?mus)([^\w<>\[\]/;])(un<sup>9</sup>)(q<sup>(i|1)</sup>)(sq:?)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[us]q[u]<sup>i</sup>i\5[ue]\6', content)

        # d-
        # d- -> denarios
        pattern = ur'(?mus)([^\w<>\[\]/;])(đ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[enarios]\3', content)

        # redđ -> redd[idit]
        pattern = ur'(?mus)([^\w<>\[\]/;]red)(đ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[idit]\3', content)

        # hiđ -> hiđ[as]
        pattern = ur'(?mus)([^\w<>\[\]/;]hi)(đ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[as]\3', content)

        # hunđ -> hunđ[reto]
        pattern = ur'(?musi)([^\w<>\[\]/;]hun)(đ|d<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[reto]\3', content)
        
        # d: -> q:[ui]
        pattern = ur'(?mus)([^\w<>\[\]/;]q)(:)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ui]\3', content)

        # ĩ -> ĩ[n]
        pattern = ur'(?mus)([^\w<>\[\]/;]ĩ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[n]\2', content)

        # st~
        # st~ -> s[un]t~
        pattern = ur'(?mus)([^\w<>\[\]/;]s)(t̃[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[un]\2', content)

        # rex E -> rex Edwardus
        pattern = ur'(?musi)([^\w<>\[\]/;])(rex\.? E)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[dwardus]\3', content)

        # regis E -> regis Edwardi
        pattern = ur'(?musi)([^\w<>\[\]/;])(regis\.? e)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[dwardi]\3', content)

        # E regis ->
        pattern = ur'(?musi)([^\w<>\[\]/;]e)\.?( regis[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[dwardi]\2', content)

        # rex G
        pattern = ur'(?musi)([^\w<>\[\]/;])(rex\.? G)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ildum]\3', content)

        # viłł[anos]
        pattern = ur'(?musi)([^\w<>\[\]/;])(viłł|uiłł)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[anos]\3', content)
        
        # ũg̃ -> u[ir]g[as]
        pattern = ur'(?musi)([^\w<>\[\]/;]ũ)(g̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[ir]\2[as]\3', content)

        # uirg̃ -> u[ir]g[as]
        pattern = ur'(?musi)([^\w<>\[\]/;]uirg̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[as]\2', content)

        # ht̃ -> h[abe]t̃
        pattern = ur'(?musi)([^\w<>\[\]/;]h)(t̃|t<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[abe]\2\3', content)

        # hñt -> h[abe]ñt
        pattern = ur'(?musi)([^\w<>\[\]/;]h)(ñt|nt<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[abe]\2\3', content)

        # borđ -> borđ[arios]
        pattern = ur'(?musi)([^\w<>\[\]/;]borđ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[arios]\2', content)

        # qñ -> q[ua]n[do]
        pattern = ur'(?musi)([^\w<>\[\]/;]q)(ñ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[ua]\2[do]\3', content)

        # dnĩo -> d[omi]nĩo
        pattern = ur'(?musi)([^\w<>\[\]/;]d)(nĩo[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[omi]\2', content)

        # ẽ -> ẽ[st]
        pattern = ur'(?musi)([^\w<>\[\]/;]ẽ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[st]\2', content)
        
        # ep̃s ->
        pattern = ur'(?musi)([^\w<>\[\]/;])(ep̃|ep<sup>4</sup>)(s[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[iscopu]\3', content)
        
        # porc̃
        pattern = ur'(?musi)([^\w<>\[\]/;]porc̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[os]\2', content)

        # ep̃s ->
#         pattern = ur'(?musi)([^\w<>\[\]/;])(animł|aĩalia|ãalia)([^\w<>\[\]/&])'
#         content = re.sub(pattern, ur'\1\2[iscopu]\3', content)

        # r

        # nescit^r -> nescitur^r
        pattern = ur'(?mus)([^\w<>\[\]/;]nescit)(<sup>r</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[u]r\2\3', content)

        # numbers
        pattern = ur'(?mus)\.?(\s*)(\b[IVXl]+)\.([^\w<>\[\]])'
        content = re.sub(pattern, lambda pat: ur'%s.%s.%s' % (pat.group(1), pat.group(2).lower(), pat.group(3)), content)

        # write result
        write_file(output_path, content)
        
