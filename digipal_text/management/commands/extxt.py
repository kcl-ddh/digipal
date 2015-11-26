# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import re
from optparse import make_option

# pm dpxml convert exon\source\rekeyed\converted\EXON-1-493-part1.xml exon\source\rekeyed\conversion\xml2word.xslt > exon\source\rekeyed\word\EXON-word.html
# pm extxt wordpre exon\source\rekeyed\word\EXON-word.html exon\source\rekeyed\word\EXON-word2.html
# pandoc "exon\source\rekeyed\word\EXON-word2.html" -o "exon\source\rekeyed\word\EXON-word.docx"

import unicodedata
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
        
        if command == 'setoptorder':
            known_command = True
            self.setoptorder()
        
        if known_command:
            print 'done'
            pass
        else:
            print self.help

    def setoptorder(self):
        from django.db import connections
        wrapper = connections['default']
        
        shire = self.cargs[0]
        hundreds = self.cargs[1]
        
        hundreds = eval(hundreds)
        
        i = 0
        for hundred in hundreds:
            i += 1
            print hundred, i
            from digipal.management.commands.utils import sqlWrite, sqlSelect, dictfetchall
            
            find = '''SELECT * from exon_hundred
            WHERE lower(shire) = lower(%s)
            AND hundrednameasenteredintomasterdatabase = %s
            '''
            
            recs = dictfetchall(sqlSelect(wrapper, find, [shire, hundred]))
            
            if not recs:
                command = '''INSERT INTO exon_hundred
                (hundredalorderoptimal, shire, hundrednameasenteredintomasterdatabase)
                VALUES
                (%s, %s, %s)
                '''
                sqlWrite(wrapper, command, [i, shire, hundred], False)
            else:
                command = '''UPDATE exon_hundred
                SET hundredalorderoptimal = %s
                WHERE lower(shire) = lower(%s)
                AND hundrednameasenteredintomasterdatabase = %s
                '''
                sqlWrite(wrapper, command, [i, shire, hundred], False)
            
        wrapper.commit()
            

    def hundorder(self):
        shire = self.cargs[0]
        
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
                    if last_hundred is None or last_hundred != hundred:
                        tic['entries'].append(entry)
                    last_hundred = hundred
            # remove tic with only one entry
            tics = [tic for tic in tics if len(tic['entries']) > 1]

            
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
            
            seed.append([20, 0, 1, 9, 5, 7, 24, 27, 41, 38, 43, 46, 21, 2, 10, 11, 44, 30, 4, 12, 34, 25, 37, 39, 42, 33, 23, 22, 13, 28, 3, 14, 32, 15, 16, 45, 17, 8, 40, 6, 26, 18, 36, 29, 31, 35, 19])
            seed.append([44, 20, 45, 41, 37, 46, 0, 9, 5, 7, 24, 27, 21, 2, 4, 22, 34, 10, 25, 11, 30, 12, 13, 28, 3, 38, 23, 14, 16, 32, 43, 17, 40, 26, 42, 15, 8, 18, 36, 33, 29, 1, 31, 19, 35, 39, 6])
            seed.append([38, 36, 20, 0, 15, 1, 46, 42, 9, 44, 31, 5, 7, 39, 40, 24, 27, 21, 41, 2, 10, 11, 45, 34, 30, 35, 4, 33, 25, 12, 22, 23, 13, 6, 28, 3, 37, 14, 16, 43, 32, 17, 26, 8, 18, 29, 19])

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

[4, 25, 43, 40, 31, 5, 27, 9, 34, 33, 0, 37, 29, 6, 14, 16, 21, 41, 32, 10, 11, 28, 2, 19, 35, 39, 3, 12, 17, 23, 13, 22, 36, 24, 20, 38, 1, 42, 30, 7, 15, 8, 18, 26]
[u'Ailwood', u'Sixpenny', u'Loders', u'Canedone', u'Albretesberga', u'Bere', u'Brunsell', u'Badbury', u'Buckland Newton', u'Cogdean', u'Modbury', u'Stana', u'Puddletown', u'Charborough', u'Langeberga', u'Canendona', u'Beaminster', u'Hundesburge', u'Bridport', u'Combsditch', u'Cranborne', u'Chilbury', u'Cullifordtree', u'Gillingham', u'Goderthorne', u'Alvredesberge', u'Hasler', u'Hunesberga', u'Dorchester', u'Hilton', u'Knowlton', u'Tollerford', u'Langeburgh', u'Newton', u'Pimperne', u'Wareham', u'Uggescombe', u'Farrington', u'Sherborne', u'Eggardon', u'Whitchurch', u'Winfrith', u'Yetminster', u'Redhove']
Cost: 41; Len: 44

[13, 16, 10, 4, 40, 42, 43, 31, 0, 9, 21, 5, 39, 37, 27, 25, 34, 29, 33, 28, 30, 11, 2, 17, 7, 19, 32, 6, 35, 23, 3, 36, 14, 41, 12, 22, 24, 20, 1, 15, 8, 38, 18, 26]
[u'Knowlton', u'Canendona', u'Combsditch', u'Ailwood', u'Canedone', u'Farrington', u'Loders', u'Albretesberga', u'Modbury', u'Badbury', u'Beaminster', u'Bere', u'Alvredesberge', u'Stana', u'Brunsell', u'Sixpenny', u'Buckland Newton', u'Puddletown', u'Cogdean', u'Chilbury', u'Sherborne', u'Cranborne', u'Cullifordtree', u'Dorchester', u'Eggardon', u'Gillingham', u'Bridport', u'Charborough', u'Goderthorne', u'Hilton', u'Hasler', u'Langeburgh', u'Langeberga', u'Hundesburge', u'Hunesberga', u'Tollerford', u'Newton', u'Pimperne', u'Uggescombe', u'Whitchurch', u'Winfrith', u'Wareham', u'Yetminster', u'Redhove']
Cost: 45; Len: 44

[4, 5, 27, 9, 34, 26, 33, 0, 37, 29, 6, 14, 43, 31, 41, 16, 21, 32, 10, 28, 11, 39, 2, 19, 35, 3, 12, 17, 22, 23, 40, 13, 24, 36, 38, 20, 1, 30, 42, 7, 15, 8, 18, 25]
[u'Ailwood', u'Bere', u'Brunsell', u'Badbury', u'Buckland Newton', u'Redhove', u'Cogdean', u'Modbury', u'Stana', u'Puddletown', u'Charborough', u'Langeberga', u'Loders', u'Albretesberga', u'Hundesburge', u'Canendona', u'Beaminster', u'Bridport', u'Combsditch', u'Chilbury', u'Cranborne', u'Alvredesberge', u'Cullifordtree', u'Gillingham', u'Goderthorne', u'Hasler', u'Hunesberga', u'Dorchester', u'Tollerford', u'Hilton', u'Canedone', u'Knowlton', u'Newton', u'Langeburgh', u'Wareham', u'Pimperne', u'Uggescombe', u'Sherborne', u'Farrington', u'Eggardon', u'Whitchurch', u'Winfrith', u'Yetminster', u'Sixpenny']
Cost: 45; Len: 44

Somerset (82/62)
---------

[36, 10, 11, 19, 55, 37, 13, 20, 51, 52, 53, 56, 1, 12, 4, 57, 58, 59, 5, 2, 32, 14, 29, 27, 38, 60, 21, 16, 62, 15, 31, 34, 28, 24, 30, 39, 7, 61, 43, 49, 22, 44, 40, 17, 33, 25, 46, 18, 6, 45, 47, 8, 23, 35, 48, 9, 26, 0, 3, 54, 50,
 41, 42]
[u'Thurlbear', u'North Petherton', u'Cannington', u'South Petherton', u'Dulverton', u'Thornfalcon', u'Bulstone', u'Yeovil: Tintinhull', u'Sheriffs Brompton', u'Cutcombe', u'Minehead', u'Cleeve', u'Williton', u'Carhampton', u'Milverton', u'Winsford', u'Creech', u'North Curry', u'Abdick', u'Bruton: Blachethorna', u'Crewkerne', u'Andersfield', u'Wellington', u'Kingsbury', u'Milverton or Brompton Regis', u'Congresbury', u'Cheddar', u'Winterstoke', u'Martock', u'Taunton', u'Wells', u'Somerton', u'Wiveliscombe', u'Bedminster', u'Lydeard', u'Yeovil: Houndsborough', u'Bath', u'Coker', u'Lyatts', u'Pitminster', u'Chew', u'Loxley', u'Yeovil: Lyatts', u'Portbury', u'Reynaldsway', u'Hartcliffe', u'Monkton', u'Frome: Frome', u'Keynsham', u'Whitestone', u'South Brent', u'Frome: Wellow', u'Bempstone', u'Bruton: Wincanton', u'Frome: Frome/Downhead', u'Frome: Kilmersdon', u'Bruton: Bruton', u'Chewton', u'Milborne/Horethorne', u'Brompton Regis', u'Huntspill', u'Yeovil: Stone', u'Carhampton / Williton']
Cost: 62; Len: 63

[36, 10, 11, 19, 55, 37, 38, 20, 51, 52, 53, 56, 1, 12, 4, 57, 58, 59, 5, 2, 32, 14, 29, 27, 13, 60, 21, 16, 62, 15, 31, 34, 28, 24, 30, 39, 7, 61, 43, 49, 22, 44, 17, 40, 33, 25, 46, 18, 6, 45,
 47, 8, 23, 35, 48, 9, 26, 0, 3, 54, 50, 41, 42]
[u'Thurlbear', u'North Petherton', u'Cannington', u'South Petherton', u'Dulverton', u'Thornfalcon', u'Milverton or Brompton Regis', u'Yeovil: Tintinhull', u'Sheriffs Brompton', u'Cutcombe', u'Minehead', u'Cleeve', u'Williton', u'Carhampton', u'Milverton', u'Winsford', u'Creech', u'North Curry', u'Abdick', u'Bruton: Blachethorna', u'Crewkerne', u'Andersfield', u'Wellington', u'Kingsbury', u'Bulstone', u'Congresbury', u'Cheddar', u'Winterstoke', u'Martock', u'Taunton', u'Wells', u'Somerton', u'Wiveliscombe', u'Bedminster', u'Lydeard', u'Yeovil: Houndsborough', u'Bath', u'Coker', u'Lyatts', u'Pitminster', u'Chew', u'Loxley', u'Portbury', u'Yeovil: Lyatts', u'Reynaldsway', u'Hartcliffe', u'Monkton', u'Frome: Frome', u'Keynsham', u'Whitestone', u'South Brent', u'Frome: Wellow', u'Bempstone', u'Bruton: Wincanton', u'Frome: Frome/Downhead', u'Frome: Kilmersdon', u'Bruton: Bruton', u'Chewton', u'Milborne/Horethorne', u'Brompton Regis', u'Huntspill', u'Yeovil: Stone', u'Carhampton / Williton']
Cost: 63; Len: 63

[10, 11, 19, 1, 51, 52, 53, 12, 4, 5, 54, 13, 20, 55, 59, 56, 32, 30, 27, 57, 28, 58, 14, 62, 21,
 16, 29, 31, 15, 34, 49, 24, 44, 39, 22, 40, 60, 17, 61, 18, 25, 46, 33, 6, 7, 45, 8, 47, 23, 9, 35, 0, 50, 26, 38, 2, 42, 3, 48, 36, 41, 37, 43]
[u'North Petherton', u'Cannington', u'South Petherton', u'Williton', u'Sheriffs Brompton', u'Cutcombe', u'Minehead', u'Carhampton', u'Milverton', u'Abdick', u'Brompton Regis', u'Bulstone', u'Yeovil: Tintinhull', u'Dulverton', u'North Curry', u'Cleeve', u'Crewkerne', u'Lydeard', u'Kingsbury', u'Winsford', u'Wiveliscombe', u'Creech', u'Andersfield', u'Martock', u'Cheddar', u'Winterstoke', u'Wellington', u'Wells', u'Taunton', u'Somerton', u'Pitminster', u'Bedminster', u'Loxley', u'Yeovil: Houndsborough', u'Chew', u'Yeovil: Lyatts', u'Congresbury', u'Portbury', u'Coker', u'Frome:
 Frome', u'Hartcliffe', u'Monkton', u'Reynaldsway', u'Keynsham', u'Bath', u'Whitestone', u'Frome:
 Wellow', u'South Brent', u'Bempstone', u'Frome: Kilmersdon', u'Bruton: Wincanton', u'Chewton', u'Huntspill', u'Bruton: Bruton', u'Milverton or Brompton Regis', u'Bruton: Blachethorna', u'Carhampton / Williton', u'Milborne/Horethorne', u'Frome: Frome/Downhead', u'Thurlbear', u'Yeovil: Stone', u'Thornfalcon', u'Lyatts']
Cost: 67; Len: 63

[30, 1, 2, 5, 38, 4, 36, 13, 37, 10, 33, 11, 62, 12, 14, 49, 17, 57, 16, 55, 6, 27, 45, 23, 28, 32, 22, 60, 20, 25, 56, 15, 34, 35, 7, 61, 19, 39, 43, 18, 42, 44, 29, 47, 46, 51, 8, 50, 52, 26, 58, 40, 21, 0, 3, 41, 31, 48, 53, 24, 59, 54, 9]
[u'Lydeard', u'Williton', u'Bruton: Blachethorna', u'Abdick', u'Milverton or Brompton Regis', u'Milverton', u'Thurlbear', u'Bulstone', u'Thornfalcon', u'North Petherton', u'Reynaldsway', u'Cannington', u'Martock', u'Carhampton', u'Andersfield', u'Pitminster', u'Portbury', u'Winsford', u'Winterstoke', u'Dulverton', u'Keynsham', u'Kingsbury', u'Whitestone', u'Bempstone', u'Wiveliscombe', u'Crewkerne', u'Chew', u'Congresbury', u'Yeovil: Tintinhull', u'Hartcliffe', u'Cleeve', u'Taunton', u'Somerton', u'Bruton: Wincanton', u'Bath', u'Coker', u'South Petherton', u'Yeovil: Houndsborough', u'Lyatts', u'Frome: Frome', u'Carhampton / Williton', u'Loxley', u'Wellington', u'South Brent', u'Monkton', u'Sheriffs Brompton', u'Frome: Wellow', u'Huntspill', u'Cutcombe', u'Bruton: Bruton', u'Creech', u'Yeovil: Lyatts', u'Cheddar', u'Chewton', u'Milborne/Horethorne', u'Yeovil: Stone', u'Wells', u'Frome: Frome/Downhead', u'Minehead', u'Bedminster', u'North Curry', u'Brompton Regis', u'Frome: Kilmersdon']
Cost: 73; Len: 63


Wiltshire (None/6)
---------

[20, 0, 1, 9, 5, 7, 24, 27, 41, 38, 43, 46, 21, 2, 10, 11, 44, 30, 4, 12, 34, 25, 37, 39, 42, 33, 23, 22, 13, 28, 3, 14, 32, 15, 16, 45, 17, 8, 40, 6, 26, 18, 36, 29, 31, 35, 19]
[u'Alderbury', u'Amesbury', u'Bowcombe', u'Blagrove', u'Bradford', u'Branchbury', u'Cadworth', u'Calne', u'Came', u'Ramsbury', u'Malmesbury', u'Westbury', u'Cawdon', u'Chippenham', u'Cicementone', u'Cricklade', u'Marlborough', u'Downton', u'Dolesfield', u'Dunworth', u'Melksham', u'Dunley', u'Bishops Cannings', u'Wilton', u'Bath', u'Damerham', u'Frustfield', u'Elstub', u'Heytesbury', u'Highworth', u'Kingsbridge', u'Kinwardstone', u'Mere', u'Rowborough', u'Scipa', u'Salisbury', u'Selkley', u'Stowford', u'Staple', u'Whorwellsdown', u'Startley', u'Studfold', u'Thorngrove', u'Swanborough', u'Thornhill', u'Wonderditch', u'Warminster']
Cost: 6; Len: 47

[44, 20, 45, 41, 37, 46, 0, 9, 5, 7, 24, 27, 21, 2, 4, 22, 34, 10, 25, 11, 30, 12, 13, 28, 3, 38, 23, 14, 16, 32, 43, 17, 40, 26, 42, 15, 8, 18, 36, 33, 29, 1, 31, 19, 35, 39, 6]
[u'Marlborough', u'Alderbury', u'Salisbury', u'Came', u'Bishops Cannings', u'Westbury', u'Amesbury', u'Blagrove', u'Bradford', u'Branchbury', u'Cadworth', u'Calne', u'Cawdon', u'Chippenham', u'Dolesfield', u'Elstub', u'Melksham', u'Cicementone', u'Dunley', u'Cricklade', u'Downton', u'Dunworth', u'Heytesbury', u'Highworth', u'Kingsbridge', u'Ramsbury', u'Frustfield', u'Kinwardstone', u'Scipa', u'Mere', u'Malmesbury', u'Selkley', u'Staple', u'Startley', u'Bath', u'Rowborough', u'Stowford', u'Studfold', u'Thorngrove', u'Damerham', u'Swanborough', u'Bowcombe', u'Thornhill', u'Warminster', u'Wonderditch', u'Wilton', u'Whorwellsdown']
Cost: 14; Len: 47

[38, 36, 20, 0, 15, 1, 46, 42, 9, 44, 31, 5, 7, 39, 40, 24, 27, 21, 41, 2, 10, 11, 45, 34, 30, 35, 4, 33, 25, 12, 22, 23, 13, 6, 28, 3, 37, 14, 16, 43, 32, 17, 26, 8, 18, 29, 19]
[u'Ramsbury', u'Thorngrove', u'Alderbury', u'Amesbury', u'Rowborough', u'Bowcombe', u'Westbury', u'Bath', u'Blagrove', u'Marlborough', u'Thornhill', u'Bradford', u'Branchbury', u'Wilton', u'Staple', u'Cadworth', u'Calne', u'Cawdon', u'Came', u'Chippenham', u'Cicementone', u'Cricklade', u'Salisbury', u'Melksham', u'Downton', u'Wonderditch', u'Dolesfield', u'Damerham', u'Dunley', u'Dunworth', u'Elstub', u'Frustfield', u'Heytesbury', u'Whorwellsdown', u'Highworth', u'Kingsbridge', u'Bishops Cannings', u'Kinwardstone', u'Scipa', u'Malmesbury', u'Mere', u'Selkley', u'Startley', u'Stowford', u'Studfold', u'Swanborough', u'Warminster']
Cost: 19; Len: 47

[37, 19, 6, 39, 24, 0, 1, 44, 46, 43, 14, 33, 8, 41, 11, 13, 42, 29, 40, 27, 2, 15, 35, 47, 36, 16, 26, 7, 17, 34, 30, 28, 25, 10, 38, 45, 32, 3, 9, 18, 20, 4, 21, 12, 31, 22, 5, 23]
[u'Thorngrove', u'Rowborough', u'-', u'Ramsbury', u'Alderbury', u'Amesbury', u'Bowcombe', u'Bath', u'Marlborough', u'Westbury', u'Blagrove', u'Thornhill', u'Bradford', u'Staple', u'Branchbury', u'Calne', u'Came', u'Cadworth', u'Wilton', u'Cawdon', u'Chippenham', u'Cicementone', u'Melksham',
 u'Salisbury', u'Wonderditch', u'Cricklade', u'Downton', u'Dolesfield', u'Dunworth', u'Damerham',
 u'Dunley', u'Elstub', u'Frustfield', u'Heytesbury', u'Bishops Cannings', u'Malmesbury', u'Highworth', u'Kingsbridge', u'Whorwellsdown', u'Kinwardstone', u'Scipa', u'Mere', u'Selkley', u'Stowford', u'Startley', u'Studfold', u'Swanborough', u'Warminster']
Cost: 23; Len: 48
done

[20, 0, 41, 45, 23, 38, 42, 9, 5, 35, 7, 1, 8, 24, 21, 2, 10, 11, 28, 46, 39, 4, 6, 30, 12, 25, 37, 33, 22, 3, 14, 32, 15, 27, 16, 17, 43, 40, 13, 26, 18, 44, 36, 29, 19, 34, 31]
[u'Alderbury', u'Amesbury', u'Came', u'Salisbury', u'Frustfield', u'Ramsbury', u'Bath', u'Blagrove', u'Bradford', u'Wonderditch', u'Branchbury', u'Bowcombe', u'Stowford', u'Cadworth', u'Cawdon',
 u'Chippenham', u'Cicementone', u'Cricklade', u'Highworth', u'Westbury', u'Wilton', u'Dolesfield', u'Whorwellsdown', u'Downton', u'Dunworth', u'Dunley', u'Bishops Cannings', u'Damerham', u'Elstub', u'Kingsbridge', u'Kinwardstone', u'Mere', u'Rowborough', u'Calne', u'Scipa', u'Selkley', u'Malmesbury', u'Staple', u'Heytesbury', u'Startley', u'Studfold', u'Marlborough', u'Thorngrove', u'Swanborough', u'Warminster', u'Melksham', u'Thornhill']
Cost: 35; Len: 47
done


            '''
            
    
    def print_candidate(self, v1, tics, hundreds):
        print '-' * 10
        print v1
        print self.get_vector_labels(hundreds, v1)
        print 'Cost: %s; Len: %s' % (self.get_cost(tics, v1), len(v1))
        
    def get_cost(self, tics, v1):
        ret = 0
        
        for tic in tics:
            last_ho = None
            last_last_ho = None
            for entry in tic['entries']:
                ho = v1.index(entry['ho'])
                # 8 11 10 not ok
                # 10 11 10 OK
                if last_ho is not None and\
                    last_ho > ho and\
                    last_last_ho != ho:
                    ret += 1
                last_last_ho = last_ho
                last_ho = ho
        
        return ret
    
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
        
