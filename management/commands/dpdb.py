from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option

class Command(BaseCommand):
	"""
	Digipal database management tools.
	
	Commands:
	
		backup [--table TABLE_NAME] [BACKUP_NAME]
			Backup a database into a file.
	
		restore BACKUP_NAME
			Restores a database from a backup. 
	
		list
			Lists backup files.
		
		tables
			Lists the tables in the database, their size and most recent change
			Use --table PATTERN to select which table to display 			
		
		fixseq
			Fix the postgresql sequences. 
			Useful when you get a duplicate key violation on insert after restoring a database.  
	
	Options:
	
		--db DATABASE_SETTINGS_NAME
	
	"""
	
	args = 'backup|restore|list|tables|fixseq'
	help = 'Manage the Digipal database'
	option_list = BaseCommand.option_list + (
        make_option('--db',
            action='store',
            dest='db',
            default='default',
            help='Name of the database configuration'),
		make_option('--table',
			action='store',
			dest='table',
			default='',
			help='Name of the table to backup'),
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
				count = self.sqlSelectCount(con, table)
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
						max_date = self.sqlSelectMaxDate(con, table, field_name)
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

	def sqlSelect(self, wrapper, command, arguments=[]):
		''' return a cursor,
			caller need to call .close() on the returned cursor 
		'''
		cur = wrapper.cursor()
		cur.execute(command, arguments)
		
		return cur

	def sqlSelectMaxDate(self, con, table, field):
		ret = None
		cur = self.sqlSelect(con, 'select max(%s) from %s' % (field, table))
		rec = cur.fetchone()
		if rec and rec[0]:
			ret = rec[0]
		cur.close()
		
		return ret

	def sqlSelectCount(self, con, table):
		ret = 0
		cur = self.sqlSelect(con, 'select count(*) from %s' % table)
		rec = cur.fetchone()
		ret = rec[0]
		cur.close()
		
		return ret

	def handle(self, *args, **options):
		
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
		
		if command == 'tables':
			known_command = True
			self.showTables(options)
			
		if command == 'fixseq':
			# fix the sequence number for auto incremental fields (e.g. id)
			# Unfortunately posgresql import does not update them so we have to run this after an import 
			known_command = True
			
			from django.db import connection
			cursor = connection.cursor()

			from django.contrib.contenttypes.models import ContentType
			types = ContentType.objects.all()
			for type in types:
				model = type.model_class()
				if model and model._meta.auto_field and model._meta.auto_field.column == 'id':
					print model
					cmd = "select setval('%(table_name)s_%(seq_field)s_seq', (select max(%(seq_field)s) from %(table_name)s) )" % {'table_name': model._meta.db_table, 'seq_field': model._meta.auto_field.column}
					cursor.execute(cmd)
		
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
	