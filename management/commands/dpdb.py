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
	
		restore BACKUP_NAME
	
		list
		
		fixseq
			Fix the postgresql sequences. 
			Useful when you get a duplicate key violation on insert after restoring a database.  
	
	Options:
	
		--db DATABASE_SETTINGS_NAME
	
	"""
	
	args = 'backup|restore|list'
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
	