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
  
  parse_em_table --src=HTML_FILE_PATH
  
  fp7_import --src=XML_FILE_PATH
                        Where file.xml is a XML file exported from a FileMaker 
                        Pro 7 table.
                        This command will (re)create a table in the database 
                        and upload all the data from the XML file.
    
  esawyer_import
                        Import data from the filemaker table into the Text 
                        records

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
                
        if command == 'parse_em_table':
            known_command = True
            self.parse_em_table(options)
            
        if command == 'fp7_import':
            known_command = True
            self.fp7_import(options)
        
        if command == 'esawyer_import':
            known_command = True
            self.esawyer_import(options)
            
        if command == 'gen_em_table':
            known_command = True
            self.gen_em_table(options)

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

        if not known_command:
            raise CommandError('Unknown command: "%s".' % command)

    def gen_em_table(self, options):
        # TODO: update this query to work with the itempartitem table
        query = ur'''
                select distinct
                    'http://www.digipal.eu/digipal/manuscripts/' || ip.id || '/pages/' as "Digipal URL",
                    pc.page_count as "Pages",
                    pl.name as "Place", 
                    re.name as "Repository", 
                    ci.shelfmark as "Shelf Mark", 
                    ip.locus as "Locus", 
                    '[' || cn.number || ']' as "Ker", 
                    de.description as "Content", 
                    ori.name as "Origin", 
                    (case when length(hi.date) > 0 then hi.date else hand_date end) as "Date",
                    (case when length(regexp_replace(shelfmark, E'\\D','','g')) between 1 and 10 then regexp_replace(shelfmark, E'\\D','','g')::bigint else 0 end) as shelf_num
                from 
                    digipal_itempart ip 
                    join digipal_currentitem ci on ip.current_item_id = ci.id
                    join digipal_historicalitem hi on ip.historical_item_id = hi.id
                    join digipal_repository re on ci.repository_id = re.id
                    left join digipal_place pl on re.place_id = pl.id
                    left join digipal_description de on hi.id = de.historical_item_id
                    left join digipal_cataloguenumber cn on (cn.historical_item_id = hi.id and cn.source_id = 3)
                    left join (
                            select ip2.id as id, (case when max(pa.id) > 0 then count(*) else 0 end) as page_count
                            from 
                            digipal_itempart ip2 left join digipal_page pa on pa.item_part_id = ip2.id
                            group by ip2.id
                            order by page_count desc
                        ) pc on ip.id = pc.id
                    left join (
                            select io.historical_item_id as historical_item_id, (case when pl2.id > 0 then pl2.name when ins.id > 0 then ins.name else '' end) as name
                            from 
                                digipal_itemorigin io
                                left join digipal_place pl2 on (io.object_id = pl2.id and io.content_type_id = 43)
                                left join digipal_institution ins on (io.object_id = ins.id and io.content_type_id = 48)
                        ) ori on hi.id = ori.historical_item_id
                    left join (
                            select ha.item_part_id, max(da.date) as hand_date
                            from
                                digipal_hand ha
                                left join digipal_date da on ha.assigned_date_id = da.id
                            group by ha.item_part_id
                    ) ha on ha.item_part_id = ip.id
                order by
                    "Place", "Repository", shelf_num, "Shelf Mark", "Ker", "Locus"
        '''
        
        from django.db import connections
        con_src = connections[options.get('src')]
        
        cursor = con_src.cursor()
        cursor.execute(query)
        
        rows = [[col[0] for col in cursor.description]]
        for row in cursor.fetchall():
            row_latin_1 = [(u'%s' % v).encode('latin-1', 'ignore') for v in row]
            rows.append(row_latin_1)

        csv_path = 'digipal.csv'
        with open(csv_path, 'wb') as csvfile:
            import csv        
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(rows)
            
    def esawyer_import(self, options):
        # Copy fields from esawyer MSS-Esawyer relationship table
        # to the TextItemPart
        from django.db import connections
        con_dst = connections[options.get('db')]
        con_dst.enter_transaction_management()
        con_dst.managed()
        
        print '\n fm_sawyerdetails -> digipal_text\n' 
        
        from digipal.models import Text, CatalogueNumber, Description, Source        
        source_esawyer = Source.objects.get(name=settings.SOURCE_SAWYER) 
        
        es_descriptions = utils.fetch_all_dic(utils.sqlSelect(con_dst, 'select sawyer_num, title, king, kingdom, comments from fm_sawyerdetails'))

        es_text_item_parts0 = utils.fetch_all_dic(utils.sqlSelect(con_dst, '''
            select re.recordid, sd.sawyer_num, cm.shelfmark, cm.part, 
                    re.calculatefoliopagemembrane as locus, re.this_text_date
            from fm_chartermss cm , fm_sawyermssrelationships re , fm_sawyerdetails sd
            where re.sawyernumber = sd.sawyer_num
                and re.msid = cm.msid
            order by sd.sawyer_num
        '''))
        
        # Create a key/hash for every item part in eSawyer DB
        #
        # Two problems:
        #    1. cm.part can be missing, in this case reckey is null
        #    2. cm.part is only necessary when the text is in more than one item part of the same current item
        #
        # => we first try to match records using an exact key for our item part.
        #     if it does not work we try to match using a loose key: without cm.part 
        
        def get_key(code):
            return utils.get_simple_str(code).replace('_i_', '_1_').replace('_lat_', '_latin_').replace('_add_', '_additional_').replace('_f_', '_').replace('_fols_', '_').replace('_ff_', '_')
        
        es_text_item_parts = {}
        for key in es_text_item_parts0:
            es_text_item_part = es_text_item_parts0[key]
            if key is not None:
                es_text_item_parts[get_key('%s-%s-%s' % (es_text_item_part['sawyer_num'], es_text_item_part['shelfmark'], es_text_item_part['part']))] = es_text_item_part
                loose_key = get_key('%s-%s' % (es_text_item_part['sawyer_num'], es_text_item_part['shelfmark']))
                if loose_key not in es_text_item_parts:
                    es_text_item_parts[loose_key] = es_text_item_part
                else:
                    # The loose key cannot be used anymore as it corresponds to more than one item part
                    #print loose_key
                    es_text_item_parts[loose_key] = None
        
        #print '-' * 50
        
        # For each text with an eSawyer cat num
        # We update the text description from the matching record in eSawyer. 
        # Then find the item part matching those in eSawyer DB. 

        cat_nums = CatalogueNumber.objects.filter(number__in=es_descriptions.keys(), source=source_esawyer, text_id__isnull=False)
        for cat_num in cat_nums:
            # update the Text record from the esawyerdetails record 
            
            # Create/Update the Description
            es_desc = es_descriptions[cat_num.number]
            text = cat_num.text
            
            print 'Text %s' % utils.get_obj_label(text)
            
            descriptions = text.descriptions.filter(source=source_esawyer)
            if descriptions:
                print '\tUpdate description'
                description = descriptions[0]
            else:
                print '\tCreate description'
                description = Description(source=source_esawyer, text=text)
            
            if es_desc['title'] and es_desc['title'].strip(): 
                description.description = es_desc['title']
                print '\t\tUpdate description'
            if es_desc['comments'] and es_desc['comments'].strip(): 
                description.comments = es_desc['comments'] 
                print '\t\tUpdate comments'
            description.summary = ''
            
            description.save()
            
            # Update the textitempart record from the esawyer mssrelationship record
            for text_item_part in text.text_instances.all():
                # first try a precise match on the locus
                # if not found, try a match without locus
                key = get_key(u'%s-%s-%s' % (cat_num.number, text_item_part.item_part.current_item.shelfmark, text_item_part.item_part.locus))
                #print key
                es_text_item_part = None
                if key in es_text_item_parts:
                    es_text_item_part = es_text_item_parts[key]
                    #print 'Found an exact match'
                else:
                    key = get_key(u'%s-%s' % (cat_num.number, text_item_part.item_part.current_item.shelfmark))
                    if key in es_text_item_parts and es_text_item_parts[key] is not None:
                        #print 'Found a loose match'
                        es_text_item_part = es_text_item_parts[key]
                    else:
                        print (ur'\tWARNING: no matching item part for key: "%s", %s, %s' % (key, text.name, text_item_part.item_part)).encode('ascii', 'xmlcharrefreplace')
                
                if es_text_item_part:
                    print ('\tUpdate item part %s' % utils.get_obj_label(es_text_item_part)).encode('ascii', 'xmlcharrefreplace')
                    if es_text_item_part['locus']:
                        text_item_part.locus = es_text_item_part['locus']
                    if es_text_item_part['this_text_date']:
                        text_item_part.date = es_text_item_part['this_text_date']
                    text_item_part.save()
            
        print 'Updated %d Text records.' % cat_nums.count()

        if self.is_dry_run():
            con_dst.rollback()
            print 'Nothing actually written (remove --dry-run option for permanent changes).'
        else:
            con_dst.commit()
        con_dst.leave_transaction_management()

    def fp7_import(self, options):
        '''
        --src=file.xml
        
        Where file.xml is a XML file exported from a FileMaker Pro 7 table.
        This command will (re)create a table in the database and upload all 
        the date from the XML file. 
        
        '''
        import xml.etree.ElementTree as ET

        # open the file
        xml_file = options.get('src', '')
        ns = '{http://www.filemaker.com/fmpdsoresult}'
        try:
            import lxml.etree as ET
            tree = ET.parse(xml_file)
            #tree.register_namespace('wp', 'http://wordpress.org/export/1.2/')
            root = tree.getroot()
        except Exception, e:
            raise CommandError('Cannot parse %s: %s' % (xml_file, e))

        from django.db import connections
        con_dst = connections[options.get('db')]
        con_dst.enter_transaction_management()
        con_dst.managed()
        
        # get all the rows and fields and the max lengths
        fields = {}
        
        rows = []
        for row in root.findall('.//%sROW' % ns):
            arow = {}
            for col in list(row):
                field_name = utils.get_simple_str(re.sub(ur'\{[^}]*\}', '', col.tag))
                arow[field_name] = col.text
            for col, val in row.attrib.iteritems():
                field_name = utils.get_simple_str(re.sub(ur'\{[^}]*\}', '', col))
                arow[field_name] = val
            
            for field, val in arow.iteritems():
                if field not in fields:
                    fields[field] = [0, True, False]
                if val is not None:
                    fields[field][0] = max(fields[field][0], len(val))
                    fields[field][1] &= utils.is_int(val)
                fields[field][2] |= (val is None)
                 
            #print arow
            rows.append(arow)
            
        # (re)create the table
        table_name = 'fm_' + utils.get_simple_str(re.sub(ur'^.*[\\/]([^.]+).*$', ur'\1', xml_file))
        print table_name
        
        utils.sqlWrite(con_dst, 'DROP TABLE IF EXISTS %s' % table_name)
        
        def field_type(field, field_name):
            ret = 'int'
            if not field[1]: 
                ret = 'varchar(%s)' % field[0]
            if field_name == 'recordid':
                ret += ' PRIMARY KEY '
            if field[2]:
                ret += ' NULL '
            
            return ret
        
        fields_sql = ', '.join(['%s %s' % (f, field_type(fields[f], f)) for f in fields])
        
        create_table_sql = 'CREATE TABLE %s (%s)' % (table_name, fields_sql)
        
        #print create_table_sql
        
        utils.sqlWrite(con_dst, create_table_sql)
        
        # write the records
        fields_ordered = fields.keys()
        insert_sql = ur'INSERT INTO %s (%s) VALUES (%s)' % (table_name, ', '.join([f for f in fields_ordered]), ','.join([ur'%s'] * len(fields_ordered)))
        
        for row in rows:
            utils.sqlWrite(con_dst, insert_sql, [row[f] for f in fields_ordered])
            
        con_dst.commit()
        con_dst.leave_transaction_management()

        print 'Wrote %d records in table %s' % (len(rows), table_name)
        
        #print fields
    
    def parse_em_table(self, options):
        from digipal.utils import find_first
        import HTMLParser
        hp = HTMLParser.HTMLParser()
        
        csv_path = 'em.csv'

        with open(csv_path, 'wb') as csvfile:

            import csv        
            csvwriter = csv.writer(csvfile)
        
            xml_file = options.get('src', '')
            html = utils.readFile(xml_file)
            
            # extract the rows
            rows = re.findall(ur'<tr>(.*?)</tr>', html)
            
            csvwriter.writerow(['Digipal URL', 'Type', 'Place', 'Repository', 'Collection', 'Shelf Mark', 'Ker', 'Content', 'Place', 'Date', 'File Name', 'URL'])
            
            for row in rows:
                # extract the columns
                cols = re.findall(ur'<td>(.*?)</td>', row)
                
                # extract href from first column
                href = find_first(ur'href="(.*?)"', cols[0])
    
                # get the file name from the href
                href_file = find_first(ur'/([^/]+?)$', href)
                
                href_abs = ''
                if href_file:
                    href_abs = ur'http://www.le.ac.uk/english/em1060to1220/mss/%s' % href_file 
                
                # extract class
                ms_type = find_first(ur'class="(.*?)"', cols[0])
                
                # strip html from all columns
                # and decode html entities (e.g. &nbsp; &amp;)
                for i in range(0, len(cols)):
                    cols[i] = re.sub(ur'<.*?>', '', cols[i])
                    cols[i] = hp.unescape(cols[i])
                    
                # add extracted fields to the list of columns
                cols.extend([href_file, href_abs])
                cols.insert(0, ms_type)
                cols.insert(0, '')
                
                for i in range(0, len(cols)):
                    cols[i] = cols[i].encode('latin-1', 'ignore')
                
                # write this row to a CSV file
                #line = csv.reader(csvfile, delimiter=' ', quotechar='|')
                csvwriter.writerow(cols)
        
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
                
                # TODO: update this query to work with multiple historical_itemS for each item part
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
                    same_hands = Hand.objects.filter(descriptions__description__icontains=loci)
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
                    if hand.label and hand.label.strip() != hand.description.strip():
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
        if 0 and dst_table == 'blog_blogpost' and src_table == 'blog_blogpost':
            common_str_dst = common_str_dst + ', rating_sum'
            params_str = params_str + ', 0'
        if 0 and dst_table == 'generic_threadedcomment' and src_table == 'generic_threadedcomment':
            common_str_dst = common_str_dst + ', rating_average, rating_count, rating_sum'
            params_str = params_str + ', 0, 0, 0'
            
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
