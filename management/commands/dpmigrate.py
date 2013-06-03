from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option
import utils
from utils import Logger  
from django.utils.datastructures import SortedDict
  
class Command(BaseCommand):
    help = """
Digipal database migration tools.
    
Commands:
    
  hand [--db DB_ALIAS] [--src SRC_DB_ALIAS] [--dry-run]
        
                        Copy all the records from SRC_DB_ALIAS.hand_* to 
                        DB_ALIAS.digipal_*
                        Existing records are removed. Preexisting table 
                        structures are preserved.

  copy [--db DB_ALIAS] [--src SRC_DB_ALIAS] [--table TABLE_FILTER] [--dry-run]
        
                        Copy all the records from SRC_DB_ALIAS.*TABLE_FILTER* 
                        to DB_ALIAS.*TABLE_FILTER*
                        Existing records are removed. Preexisting table 
                        structures are preserved.
                        
  stewart_import --src=CSV_FILE_PATH [--db DB_ALIAS] [--dry-run]

  stewart_integrate [--db DB_ALIAS] [--src SRC_DB_ALIAS] [--dry-run]
  
  stokes_catalogue_import --src=XML_FILE_PATH

"""
    
    args = 'hand'
    option_list = BaseCommand.option_list + (
        make_option('--db',
            action='store',
            dest='db',
            default='default',
            help='Name of the target database configuration (\'default\' if unspecified)'),
        make_option('--src',
            action='store',
            dest='src',
            default='hand',
            help='Name of the source database configuration (\'hand\' if unspecified)'),
        make_option('--table',
            action='store',
            dest='table',
            default='',
            help='Name of the tables to backup. This acts as a name filter.'),
        make_option('--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run, don\'t change any data.'),
        ) 

    migrations = ['0004_page_number_and_side', '0005_page_iipimage']
    
    def handle(self, *args, **options):
        
        self.logger = utils.Logger()
        
        self.log_level = 3
        
        self.options = options
        
        if len(args) < 1:
            raise CommandError('Please provide a command. Try "python manage.py help dpmigrate" for help.')
        command = args[0]
        
        known_command = False

        if command == 'hand':
            known_command = True
            self.migrateHandRecords(options)
            if not self.is_dry_run():
                c = utils.fix_sequences(options.get('db'), True)
                self.log('%s sequences fixed' % c)

        if command == 'copy':
            known_command = True
            self.migrateRecords(options)
            if not self.is_dry_run():
                c = utils.fix_sequences(options.get('db'), True)
                self.log('%s sequences fixed' % c)
                
        if command == 'stewart_import':
            known_command = True
            self.importStewart(options)

        if command == 'stewart_integrate':
            pass
        
        if command == 'stokes_catalogue_import':
            known_command = True
            self.importStokesCatalogue(options)
        
        if self.is_dry_run():
            self.log('Nothing actually written (remove --dry-run option for permanent changes).', 1)

    def importStokesCatalogue(self, options):
        from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
        
        xml_file = options.get('src', '')
        
        # <p><label>G.4-2</label>. Hand 2 (5r). This large, very rotund hand was written 
        # with a thick pen held quite flat and with a great deal of shading. Ascenders 
        # are thick, straight

        content = utils.readFile(xml_file)
        #hand_infos = re.findall(ur'(?uis)<p><label>\s*(.*?)\s*</label>(?:\s|\.)*(.*?)\s*\((.*?)\)\s*(.*?)\s*</p>', content)
        hand_infos = re.findall(ur'(?uis)<p><label>\s*(.*?)\s*</label>(?:\s|\.)*(.*?)\s*(?:\((.*?)\)|\.)\s*(.*?)\s*</p>', content)
        
        updated_hands = {}
        modified_hands = []
        tags = []
        
        for info in hand_infos:
            
            migrated = False
            
            self.logger.resetWarning()
            
            # G.65.5-1 => [G, 65.5, 1]
            hand_id, hand_label, loci, description = info
            label_parts = re.findall(ur'^(\w)\.([^-]+)(?:-(.*))?$', info[0])
            if label_parts:
                #self.log(u','.join([hand_id, hand_label, loci]), Logger.INFO)
                
                description = (re.sub(ur'^(\s|\.)*', '', description)).strip()
                
                if len(label_parts[0]) > 30: 
                    self.log(u','.join([hand_id, hand_label, loci]), Logger.INFO)
                    self.log(u'Labels is too long (%s)' % label_parts[0], Logger.WARNING, 1)
                    continue
                
                loci = loci.strip()
                catalogue, doc_number, hand_number = label_parts[0]
                if not hand_number: 
#                      print '\tWARNING: no hand number.'
                     hand_number = '1'
                
                # 1. find the Hand record
                from digipal.models import Hand
                
                hand_number_parts = (re.findall(ur'^(\d+)(.*)$', hand_number))[0]
                
                hands = Hand.objects.filter(num=hand_number_parts[0], item_part__historical_item__catalogue_numbers__number=doc_number, item_part__historical_item__catalogue_numbers__source__label='%s.' % catalogue)
                
                # 2. validation
#                    if hand_number_parts[1]:
#                        self.log('non numeric hand number', Logger.WARNING, 1)
                     
                     # 3 advanced matching:
                     # 3.1 No match at all
                if not hands:
                    self.log(u','.join([hand_id, hand_label, loci]), Logger.INFO)
                    self.log('Hand record not found', Logger.WARNING, 1)
                    # now try to find the description in the Hand records
                    same_hands = Hand.objects.filter(description__icontains=loci)
                    for hand in same_hands[:10]:
                        same = 'SAME '
                        self.log('%5s#%s, %s (%s)' % (same, hand.id, hand.description, hand.item_part.historical_item.catalogue_number), Logger.DEBUG, 1)
                    if same_hands.count() > 10:
                        self.log('     [...]', Logger.DEBUG, 1)
                    if same_hands.count() == 0:
                        self.log('no similar record', Logger.WARNING, 1)
                    if same_hands.count() > 1:
                        self.log('more than one similar record.', Logger.WARNING, 1)
                    if same_hands.count() == 1:
                        hands = same_hands
                     
                     # 3.2 More than one match
                if len(hands) > 1:
                    self.log(u','.join([hand_id, hand_label, loci]), Logger.INFO)
                    self.log('more than one matching Hand record', Logger.WARNING, 1)
                    same_hands = []
                    for hand in hands:
                        same = ''
                        if hand.description.lower().find(loci.lower()) != -1: 
                            same = 'SAME '
                            same_hands.append(hand)
                        self.log(u'%5s#%s, %s (%s)' % (same, hand.id, hand.description, hand.item_part.historical_item.catalogue_number), Logger.DEBUG, 1)
                    hands = same_hands
                    if len(hands) == 0:
                        self.log('no similar record', Logger.WARNING, 1)
                    if len(hands) > 1:
                        self.log('more than one similar record.', Logger.WARNING, 1)
                         
                # 4. update the Hand record
                for hand in hands:
                    new_description = hand_label
                    if loci: new_description += u' (%s)' % loci
                    
                    hand_desc_short = re.sub(ur'\(.*', '', hand.description.lower()).strip()
                    
                    new_desc_short = hand_label.lower().strip()
                    
                    #                      if hand_desc_short != new_desc_short:
                    #                          self.log(u'%s <> %s' % (hand.description, new_description), Logger.WARNING, 1)
                    
                    # 3. update the Hand record
                        
                    # hand.label = hand_description
                    if hand.label:
                        self.log(u'label is not empty: %s' % hand.label, Logger.WARNING, 1)
                    else:
                        hand.label = hand.description
                    
                    existing_hand_id = updated_hands.get(hand.id, '')
                    if existing_hand_id:
                        self.log(u'Hand #%s already updated from %s' % (hand.id, existing_hand_id), Logger.WARNING, 1)
                    else:
                        if self.logger.hasWarning():
                             self.log(u'Update Hand #%s' % hand.id, Logger.INFO, 1)
                        # hand.description = xml description
                        hand.description = re.sub(ur'(?iu)\s+', ' ', description).strip()
                        
                        modified_hands.append(hand)
                        updated_hands[hand.id] = hand_id
                        migrated = True
                 
                if not migrated:
                    self.log('DESCRIPTION NOT MIGRATED', Logger.WARNING, 1)

        # save only afterward sso there is no risk of messing things up during the migration
        if not self.is_dry_run():
            for hand in modified_hands:
                hand.save()

    def importStewart(self, options):
        from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS

        csv_path = options.get('src', '')
        if not csv_path or csv_path in ['default', 'hand']:
            raise CommandError('Please provide the path to a source CSV file with --src=PATH .')

        import csv
        
        dst_table = 'digipal_stewartrecord'
        
        with open(csv_path, 'rb') as csvfile:
            #line = csv.reader(csvfile, delimiter=' ', quotechar='|')
            csvreader = csv.reader(csvfile)
            
            con_dst = connections[options.get('db')]
            con_dst.enter_transaction_management()
            con_dst.managed()

            utils.sqlDeleteAll(con_dst, dst_table, self.is_dry_run())
            
            columns = None
            records = []
            c = 0
            stats = {}
            for line in csvreader:
                line = [v.decode('latin-1') for v in line]
                if not columns:
                    columns = line
                    for co in columns: stats[co] = 0 
                    continue
                
                rec = dict(zip(columns, line))
                
                for k,v in rec.iteritems():
                    if len(v) > stats[k]: stats[k] = len(v)
                                    
                records.append(rec)
                c += 1
                #if c > 10: exit()
                
            #print stats
            #exit() 
            
            self.copyTable(None, csv_path, con_dst, dst_table, records, {'Date': 'adate'})
                
            con_dst.commit()
            con_dst.leave_transaction_management()
    
    def is_dry_run(self):
        return self.options.get('dry-run', False)
    
    def migrateRecords(self, options):
        from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
        
        table_filter = options.get('table', '')
        if not table_filter:
            raise CommandError('Please provide a table filter using the --table option. To copy all tables, use --table ALL')
        if table_filter == 'ALL': table_filter = ''

        con_src = connections[options.get('src')]
        con_dst = connections[options.get('db')]
        
        con_dst.enter_transaction_management()
        con_dst.managed()

        self.log('MIGRATE tables (*%s*) from "%s" DB to "%s" DB.' % (table_filter, con_src.alias, con_dst.alias), 2)
        
        # 1. find all the remote tables starting with the prefix
        src_tables = con_src.introspection.table_names()
        dst_tables = con_dst.introspection.table_names()
        
        con_dst.disable_constraint_checking()
        
        for src_table in src_tables:
            if re.search(r'%s' % table_filter, src_table):
                if src_table in dst_tables:
                    utils.sqlDeleteAll(con_dst, src_table, self.is_dry_run())
                    self.copyTable(con_src, src_table, con_dst, src_table)
                else:
                    self.log('Table not found in destination (%s)' % src_table, 1)
        
        con_dst.commit()
        con_dst.leave_transaction_management()
    
    def reapplyDataMigrations(self):
        '''
            We have to re-apply the data migrations only.
            
            Why? 
            
            Because pouring data from an old datatabase structure to a new one is already a hack.
            
            It leaves the schema migration applied but reverses the data migrations.
            South does not allow you to reapply single data migration without reversing olders and this will
            break anyway as they are not necessarily reversible.
            So we hack it further and re-apply the two data migrations we know of:
                0004: foliation and numbering
                0005: new iipimage
        '''
        from digipal.models import Page
        orm = {'digipal.Page': Page}

        import importlib
        for migration_name in Command.migrations:
            self.log('Reapply the data migrations %s.' % migration_name, 2)
            migmodule = importlib.import_module('digipal.migrations.%s' % migration_name)
            mig = migmodule.Migration()
            mig.forwards(orm)
            self.log('done.', 2)
    
    def migrateHandRecords(self, options):
        from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS

        con_src = connections[options.get('src')]
        con_dst = connections[options.get('db')]
        
        con_dst.enter_transaction_management()
        con_dst.managed()

        self.log('MIGRATE Hands from "%s" DB to "%s" DB.' % (con_src.alias, con_dst.alias), 2)
        
        table_prefix_src = 'hand_'
        table_prefix_dst = 'digipal_'
        
        # 1. find all the remote tables starting with the prefix
        src_tables = con_src.introspection.table_names()
        dst_tables = con_dst.introspection.table_names()
        
        con_dst.disable_constraint_checking()
        
        for src_table in src_tables:
            dst_table = re.sub(r'^'+table_prefix_src, table_prefix_dst, src_table)
            if dst_table != src_table:
                if dst_table in dst_tables:
                    utils.sqlDeleteAll(con_dst, dst_table, self.is_dry_run())
                    self.copyTable(con_src, src_table, con_dst, dst_table)
                else:
                    self.log('Table not found in destination (%s)' % dst_table, 1)
        
        con_dst.commit()
        con_dst.leave_transaction_management()
        
    def normalisedField(self, name):
        name = name.lower()
        name = re.sub(ur'\s', '_', name)
        name = re.sub(ur'\W', '', name)
        return name
    
    def copyTable(self, con_src, src_table, con_dst, dst_table, src_records=[], partial_mapping = None):
        ret = True
        
        self.log('Copy from %s to %s ' %  (src_table, dst_table), 2)
        
        # 1 find all fields in source and destinations
        if con_src: 
            fields_src = con_src.introspection.get_table_description(con_src.cursor(), src_table)
            fnames_src = [f[0] for f in fields_src]
        else:
            fnames_src = src_records[0].keys()
        
        fields_dst = con_dst.introspection.get_table_description(con_dst.cursor(), dst_table)
        fnames_dst = [f[0] for f in fields_dst]
        
        # 2. find a mapping between the src and dst fields
        from django.utils.datastructures import SortedDict
        mapping = SortedDict()
        for fn in fnames_src:
            # try the suggested mapping
            if partial_mapping and fn in partial_mapping and partial_mapping[fn] in fnames_dst:
                mapping[fn] = partial_mapping[fn]
            else:
                # try case insensitive match
                for fn2 in fnames_dst:
                    if self.normalisedField(fn) == self.normalisedField(fn2): 
                        mapping[fn] = fn2
                                        
        missings = set(fnames_src) - set(mapping.keys())
        additionals = set(fnames_dst) - set(mapping.values()) 
        ##common = [fn for fn in fnames_src if fn in fnames_dst]
        if missings:
            self.log('Missing fields (%s)' % ', '.join(missings), 1)
        if additionals:
            self.log('Additional fields (%s)' % ', '.join(additionals), 1)
        common_str_src = ''
        if con_src:
            common_str_src = ', '.join([con_src.ops.quote_name(fn) for fn in mapping.keys()])
        common_str_dst = ', '.join([con_dst.ops.quote_name(fn) for fn in mapping.values()])
        params_str = ', '.join(['%s' for fn in mapping.values()])

        # hack...
        if dst_table == 'digipal_itempart' and src_table == 'hand_itempart':
            common_str_dst = common_str_dst + ', pagination'
            params_str = params_str + ', %s'
            
        # 3 copy all the records over
        recs_src = None
        if con_src:
            recs_src = utils.sqlSelect(con_src, 'SELECT %s FROM %s' % (common_str_src, src_table))
        c = 0
        l = -1
        while True:
            l += 1
            rec_src = None
            
            if recs_src:
                rec_src = recs_src.fetchone()
            else:
                if l < len(src_records):
                    rec_src = [src_records[l][fn] for fn in mapping.keys()]
                    
            if rec_src is None: break
            
            # hack...
            if dst_table == 'digipal_itempart' and src_table == 'hand_itempart':
                rec_src = list(rec_src)
                rec_src.append(False)
            
            utils.sqlWrite(con_dst, 'INSERT INTO %s (%s) VALUES (%s)' % (dst_table, common_str_dst, params_str), rec_src, self.is_dry_run())
            c = c + 1
            #break
            
        self.log('Copied %s records' % c, 2)
        if recs_src:
            recs_src.close()
        
        return ret
            
    def run_shell_command(self, command):
        ret = True
        try:
            os.system(command)
        except Exception, e:
            #os.remove(input_path)
            raise CommandError('Error executing command: %s (%s)' % (e, command))
        finally:
            # Tidy up by deleting the original image, regardless of
            # whether the conversion is successful or not.
            #os.remove(input_path)
            pass

    def log(self, *args, **kwargs):
        self.logger.log(*args, **kwargs)
