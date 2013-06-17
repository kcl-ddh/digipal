from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option
import utils  

class Command(BaseCommand):
	help = """
Digipal database management tools.

Commands:

  backup [--table TABLE_NAME] [BACKUP_NAME]
                        Backup a database into a file.

  restore BACKUP_NAME
                        Restores a database from a backup. 

  list 
                        Lists backup files.
  
  tables [--db=DATABASE_ALIAS] [--table TABLE_NAME]  
                        Lists the tables in the database, their size and most recent change
                        Use --table PATTERN to select which table to display                           
  
  fixseq
                        Fix the postgresql sequences. 
                        Useful when you get a duplicate key violation on insert after restoring a database.
                        
  tidyup1 [--db=DATABASE_ALIAS]
                        Tidy up the data in the digipal tables (See Mantis issue #5532)
                        Refresh all the display_labels fields.
  
  checkdata1
                        Check for issues in the data (See Mantis issue #5532)
  
  cleanlocus ITEMPARTID1 [ITEMPARTID2 ...] [--force]
                        Remove the v/r from the Page.locus field.
                        For all pages where Page.item_part_id in (ITEMPARTID1 ITEMPARTID2 ...).
                        Use --force to also change Page.item_part.pagination to true.
                        Use checkdata1 to list the id of the pages and item_parts records.
	"""
	
	args = 'backup|restore|list|tables|fixseq|tidyup1|checkdata1'
	#help = 'Manage the Digipal database'
	option_list = BaseCommand.option_list + (
        make_option('--db',
            action='store',
            dest='db',
            default='default',
            help='Database alias'),
		make_option('--force',
			action='store_true',
			dest='force',
			default=False,
			help='Force changes despite warnings'),
		make_option('--table',
			action='store',
			dest='table',
			default='',
			help='Name of the table to backup'),
		make_option('--dry-run',
			action='store_true',
			dest='dry-run',
			default=False,
			help='Dry run, don\'t change any data.'),
		) 
	
	def showTables(self, options):
		from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
		
		table_filter = options.get('table', '')
		
		if table_filter == 'ALL': table_filter = ''

		con = connections[options.get('db')]
		
		# 1. find all the remote tables starting with the prefix
		tables = con.introspection.table_names()
		tables.sort()
		
		cursor = con.cursor()
		
		date_fields = ['last_login', 'modified', 'publish_date', 'submit_date', 'action_time', 'entry_time', 'applied']
		
		print '%10s%20s %s' % ('count(*)', 'Most recent', 'Table')
		
		table_displays = {}
		
		c = 0
		for table in tables:
			if re.search(r'%s' % table_filter, table):
				c += 1 
				count = utils.sqlSelectCount(con, table)
				# find datetime field
				table_desc = con.introspection.get_table_description(cursor, table)
				max_date = ''
				table_key = ''
				for field in table_desc:
					#field_type = con.introspection.data_types_reverse.get(field[1], '')
					#if re.search('(?i)datetime', field_type):
					#	print field[0]
					field_name = field[0]
					if field_name in date_fields:
						max_date = utils.sqlSelectMaxDate(con, table, field_name)
						if max_date:
							table_key = max_date.strftime("%Y%m%d%H%M%S")
							max_date = max_date.strftime("%d-%m-%y %H:%M:%S")
						else:
							max_date = ''
							 
						#print '%s = %s' % (field_name, max_date)
				table_display = '%10s%20s %s' % (count, max_date, table)
				print table_display
				
				if table_key:
					table_displays[table_key] = table_display
				
		print '\n%s tables' % c

		print '\nMost recently changed:'
		
		top_size = 0
		if c > 1:
			top_size = 1
		if c > 3:
			top_size = 3
		if c > 10:
			top_size = 10
			
		table_keys = table_displays.keys()
		table_keys.sort()
		for table_key in (table_keys[::-1])[0:top_size]:
			print table_displays[table_key]
		
		cursor.close()
		
	def checkData1(self, options):
		print 'Checkup after tidy up operations (See Mantis issue #5532)'
		
		# ----------------------------------------------
		
		print 'A. Remove \'f\' and \'r\' from Page.locus when page.item_part.pagination = true.'
		print 'To remove the f/v from the Page.locus, try python manage.py dpdb cleanlocus ITEMPARTID1 ITEMPARTID2 ...'
		
		print 
		from digipal.models import Page
		from django.db.models import Q
		pages = Page.objects.filter((Q(locus__endswith=r'v') | Q(locus__endswith=r'r')), item_part__pagination=True).order_by('item_part', 'id')
		if not pages:
			print 'No problem found.'
		for page in pages:
			if page.item_part:
				item_part_name = '[Encoding error]'
				try:
					item_part_name = u'%s' % page.item_part
					item_part_name = item_part_name.encode('ascii', 'xmlcharrefreplace')
				except:
					pass
				print 'Page# %-5s: %-8s (ItemPart #%s: %s)' % (page.id, page.locus.encode('ascii', 'xmlcharrefreplace'), page.item_part.id, item_part_name)
		
		# ----------------------------------------------
		
		print '3. Detect unnecessary commas from display labels (HistoricalItem, Scribe, ItemPart, Allograph and derived models)'
	
		import digipal.models
		model_class_names = [c for  c in dir(digipal.models) if re.search('^[A-Z]', c)]

		c = 0
		for model_class_name in model_class_names:
			c += 1 
			model_class = getattr(digipal.models, model_class_name)
			models = model_class.objects.all().order_by('id')
			print '\t(%d / %d, %d records)\t%s' % (c, len(model_class_names), len(models), model_class._meta.object_name)
			for model in models:
				try:
					name = u'%s' % model
					if re.search(ur'(;\s*$)|(;\s*;)', name):
						print u'%d %s' % (model.id, model)
					if re.search(ur'(:\s*$)|(:\s*:)', name):
						print u'%d %s' % (model.id, model)
					if re.search(ur'(,\s*$)|(,\s*,)', name):
						print u'%d %s' % (model.id, model)
					if re.search('(\.\s*\.)', name):
						print u'%d %s' % (model.id, model)
				except:
					# encoding error, ignore for now
					continue
				
	def cleanlocus(self, item_partids, options):
		if len(item_partids) < 1:
			raise CommandError('Please provide a list of item part IDs. e.g. dpdb cleanlocus 10 30')
		from digipal.models import Page 
		pages = Page.objects.filter(item_part__in = item_partids).order_by('id')
		c = 0
		for page in pages:
			page.locus = re.sub(ur'(.*)(r|v)$', ur'\1', page.locus)
			print 'Page #%s, locus = %s' % (page.id, page.locus.encode('ascii', 'xmlcharrefreplace'))
			if not page.item_part.pagination:
				if options.get('force', False):
					page.item_part.pagination = True
					page.item_part.save()
					print 'WARNING: forced page.item_part.pagination = true (item part %s)' % page.item_part.id
				else:
					print 'WARNING: Not saved as page.item_part.pagination = false (item part %s)' % page.item_part.id
				continue
			page.save()
			c += 1
		print '%s loci modified.' % c
		
	def tidyUp1(self, options):
		print 'Tidy up operations (See Mantis issue #5532)'
		
		print 'C. Import Evidence and Reference fields from legacy database.'
		
		from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
		con = connections['legacy']
		con_dst = connections[options.get('db', 'default')]
		con_dst.enter_transaction_management()
		con_dst.managed()
		con_dst.disable_constraint_checking()
		
		tables = con.introspection.table_names()
		tables.sort()
		
		cursor = con.cursor()
		cursor_dst = con_dst.cursor()
		
		migrate_fields = ['evidence', 'reference']
		table_mapping = {
							'charters': 		'digipal_historicalitem', # ref is a char (folio number)
							'date evidence': 	'digipal_dateevidence', # reference is a FK to reference, evidence char(128)
							'facsimiles': 		'', # ??? no table in dst
							'ms dates': 		'digipal_date', # evidence char
							'ms origins': 		'digipal_itemorigin', # evidence char
							'ms owners': 		'digipal_owner', # evidence char
							'place evidence': 	'digipal_placeevidence', # ref FK, evidence char
							'references': 		'', # 'digipal_reference', already imported 
							'scribes': 			'digipal_scribe', # ref char => legacy_reference
						}
		
		# NEW_DIGIPAL_REFERENCE_ID = reference_mapping[LEGACY_REFERENCE_ID]
		reference_mapping = {}		
		cur_dst = utils.sqlSelect(con_dst, 'select id, legacy_id from digipal_reference where legacy_id > 0')
		for ref in cur_dst.fetchall():
			reference_mapping[ref[1]] = ref[0]
		cur_dst.close()
		
		for table in tables:
			table_desc = con.introspection.get_table_description(cursor, table)
			for field in table_desc:
				#field_type = con.introspection.data_types_reverse.get(field[1], '')
				#if re.search('(?i)datetime', field_type):
				#	print field[0]
				field_name = field[0]
				if re.search('(?i)(reference|evidence)', field_name):
					print 'LEGACY.%s.%s' % (table, field_name)
					table_dst = table_mapping.get(table, '')
					if not table_dst:
						print 'WARNING: not mapping found in new Digipal database.'
						continue
					
					field_name_dst = field_name.lower()
					
					table_dest_desc = con_dst.introspection.get_table_description(cursor_dst, table_dst)
					table_dest_field_names = [f[0] for f in table_dest_desc]
					
					if field_name_dst == 'reference':
						if 'legacy_reference' in table_dest_field_names:
							field_name_dst = 'legacy_reference'
						if 'reference_id' in table_dest_field_names:
							field_name_dst = 'reference_id'
					
					if field_name_dst not in table_dest_field_names:
						print 'WARNING: target field not found (%s.%s)' % (table_dst, field_name_dst)
						
					print '\tcopy to %s.%s' % (table_dst, field_name_dst)
					
					# scan all the legacy records
					cur_src = utils.sqlSelect(con, 'select id, `%s` from `%s` order by id' % (field_name, table))
					recs_src = cur_src.fetchall()
					
					missing = 0
					written = 0
					
					if recs_src:
						select = 'select id, legacy_id, %s from %s where legacy_id > 0'
						if table_dst == 'digipal_historicalitem':
							select += ' and historical_item_type_id = 1'
						cur_dst = utils.sqlSelect(con_dst, select % (field_name_dst, table_dst))
						recs_dst = {}
						for rec_dst in cur_dst.fetchall():
							if rec_dst[1] in recs_dst:
								print 'More than one record with the same legacy_id %s %s' % (rec_dst[1], table_dst)
								exit()
							recs_dst[rec_dst[1]] = rec_dst
							
						if not recs_dst:
							print '\tWARNING: target table has no legacy records'
							continue
						
						for rec in recs_src:
							if rec[0] not in recs_dst:
								#'print '\tWARNING: records is missing (legacy_id #%s)' % rec[0]
								missing += 1
								continue
							(rec_dst_id, rec_dst_legacy_id, rec_dst_value) = recs_dst[rec[0]]
							
							#if rec_dst[2] and (u'%s' % rec_dst[2]).strip().lower() != (u'%s' % rec[1]).strip().lower():
							new_value = rec[1]
							if field_name_dst == 'reference_id':
								new_value = reference_mapping.get(new_value, None)
							else:
								if new_value is None:
									new_value = ''
							#print value_src
							
							if rec_dst_value and (rec_dst_value != new_value):
								print '\tWARNING: value is different (legacy_id #%s, "%s" <> "%s")' % (rec[0], rec[1], rec_dst_value)
								continue
							
							utils.sqlWrite(con_dst, ('update %s set %s = ' % (table_dst, field_name_dst)) + (' %s WHERE id = %s '), [new_value, rec_dst_id], self.is_dry_run())
							#print 'update %s set %s = %s WHERE id = %s ' % (table_dst, field_name_dst, new_value, rec_dst_id)
							written += 1
						
						print '\t%s records changed. %s missing legacy records ' % (written, missing)
							
					cur_src.close()
					cur_dst.close()
				
		con_dst.commit()
		con_dst.leave_transaction_management()
					
		# ----------------------------------------------
		
		print 'B. Remove incorrect \'face\' value in ItemPart.'
		from digipal.models import ItemPart
		c = 0
		for model in ItemPart.objects.filter(locus='face'):
			model.locus = ''
			model.save()
			c += 1
		print '\t%d records changed' % c

		# ----------------------------------------------
		
		print '2a. fix \'abbrev.stroke,\' => \'abbrev. stroke\' in Character to match the Allograph.name otherwise we\'ll still have plenty of duplicates.'

		# fix 'abbrev.stroke,' => 'abbrev. stroke' otherwise we'll still have duplicates
		from digipal.models import Character
		try:
			character = Character.objects.get(name='abbrev.stroke')
			character.name = 'abbrev. stroke'
			character.save()
		except Character.DoesNotExist:
			pass
		
		# ----------------------------------------------
		
		print '1., 2b., 3. Save all models to fix various labelling errors.'		
		import digipal.models

		#model_class_names = [c for  c in dir(digipal.models) if re.search('^[A-Z]', c)]
		
		# These model classes are in order of dependency of the display_label 
		# (B depends from A => A listed before B).
		model_class_names = '''
			Ontograph
			Allograph
			AllographComponent
			ScriptComponent
			Reference
			Owner
			CatalogueNumber
			HistoricalItem
			Description
			ItemOrigin
			Archive
			Repository
			CurrentItem
			Scribe
			Idiograph
			HistoricalItemDate
			ItemPart
			Page
			DateEvidence
			Graph
			PlaceEvidence
			Proportion
			'''
		model_class_names = re.findall('(\S+)', model_class_names)
		
		c = 0
		for model_class_name in model_class_names:
			c += 1 
			model_class = getattr(digipal.models, model_class_name)
			models = model_class.objects.all().order_by('id')
			print '\t(%d / %d, %d records)\t%s' % (c, len(model_class_names), len(models), model_class._meta.object_name)
			for model in models:
				model.save()

		print 'WARNING: A. to be implemented when the pagination field contains the correct value.'
		
		print 'Done'

	def is_dry_run(self):
		return self.options.get('dry-run', False)
	
	def test(self, options):
		print 'TEST'
		from digipal.models import *
		
		for hd in HandDescription.objects.all():
			desc = hd.description
#			if re.search(ur'^[^(]*\)', desc):
			if re.search(ur'^[^A-Z]', desc):
				print '-' * 80
				print 'HD: # %s, H: # %s' % (hd.id, hd.hand_id)
				print desc.encode('utf8')
					
		# ST.id=253 => H.id=1150
		
		#rec = StewartRecord.objects.get(id=253)
		#rec.import_steward_record()
		
		#print Hand.objects.filter(descriptions__description__contains='sema').count()
		

	def handle(self, *args, **options):
		
		self.options = options
		
		path = self.get_backup_path()
		if not path:
			raise CommandError('Path variable DP_BACKUP_PATH not set in your settings file.')
		if not isdir(path):
			raise CommandError('Backup path not found (%s).' % path)
	
		if len(args) < 1:
			raise CommandError('Please provide a command. Try "python manage.py help dpdb" for help.')
		command = args[0]
		
		known_command = False

		if options['db'] not in settings.DATABASES:
			raise CommandError('Database settings not found ("%s"). Check DATABASE array in your settings.py.' % options['db'])

		db_settings = settings.DATABASES[options['db']]
		
		if command == 'test':
			known_command = True
			self.test(options)
		
		if command == 'checkdata1':
			known_command = True
			self.checkData1(options)
		
		if command == 'tidyup1':
			known_command = True
			self.tidyUp1(options)

		if command == 'tables':
			known_command = True
			self.showTables(options)
		
		if command == 'cleanlocus':
			known_command = True
			args = list(args)
			args.pop(0)
			self.cleanlocus(args, options)			
			
		if command == 'fixseq':
			# fix the sequence number for auto incremental fields (e.g. id)
			# Unfortunately posgresql import does not update them so we have to run this after an import 
			known_command = True
			
			c = utils.fix_sequences(options.get('db', 'default'), True)
			print "%d sequences fixed." % c

		if command == 'list':
			known_command = True
			from os import listdir
			from os.path import isfile, join
			for file in listdir(path):
				if isfile(join(path, file)):
					(file_base_name, extension) = os.path.splitext(file)
					if extension == '.sql':
						print file_base_name

		if command == 'restore':
			known_command = True
			if len(args) < 2:
				raise CommandError('Please provide the name of the backup you want to restore. Use "pyhon manage.py dpdb list".')
			
			file_base_name = args[1]
			file = os.path.join(path, file_base_name) + '.sql'
			if not os.path.isfile(file):
				raise CommandError('Backup not found (%s).' % file)
			
			cmd = 'psql -q -U %s -h %s %s < %s > tmp' % (db_settings['USER'], db_settings['HOST'], db_settings['NAME'], file)
			self.run_shell_command(cmd)
			
		if command == 'user':
			# user: list the users
			# user pass USERNAME: reset the password to 'pass'
			known_command = True
			
			from django.contrib.auth.models import User
			
			if len(args) == 1:
				for user in User.objects.all():
					print '%s\t%s' % (user.id, user.username)

			if len(args) == 3:
				username = args[2]
				pwd = 'pass'
				if args[1] == 'pass':
					users = User.objects.filter(username=username)
					if users.count():
						user = users[0]
					else:
						user = User()
					user.username = username
					user.set_password(pwd)
					user.is_active = True
					user.is_staff = True
					user.is_superuser = True
					user.save()
					
					print 'User %s. Password reset to "%s".' % (username, pwd) 
			
		if command == 'backup':
			# backup
			known_command = True
			
			file_base_name = 'dp'
			if len(args) > 1:
				file_base_name = args[1]
				
			table_option = ''
			if options['table']:
				table_option = '--table=%s' % options['table']
			
			output_file = os.path.join(path, file_base_name + '.sql')
			cmd = 'pg_dump -c %s -U %s -h %s -f "%s" %s ' % (table_option, db_settings['USER'], db_settings['HOST'], output_file, db_settings['NAME'])
			self.run_shell_command(cmd)
			print 'Database saved to %s' % output_file
			
		if not known_command:
			raise CommandError('Unknown command: "%s".' % command)
	
	def get_backup_path(self):
		ret = getattr(settings, 'DB_BACKUP_PATH', None)
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
	