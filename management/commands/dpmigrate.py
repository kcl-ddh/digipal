from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option
from django.db import IntegrityError

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
				self.reapplyDataMigrations()

		if command == 'copy':
			known_command = True
			self.migrateRecords(options)
		
		if self.is_dry_run():
			self.log('Nothing actually written (remove --dry-run option for permanent changes).', 1)
	
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
					self.sqlDeleteAll(con_dst, src_table)
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
					self.sqlDeleteAll(con_dst, dst_table)
					self.copyTable(con_src, src_table, con_dst, dst_table)
				else:
					self.log('Table not found in destination (%s)' % dst_table, 1)
		
		con_dst.commit()
		con_dst.leave_transaction_management()
	
	def copyTable(self, con_src, src_table, con_dst, dst_table):
		ret = True
		
		self.log('Copy from %s to %s ' %  (src_table, dst_table), 2)
		
		# 1 find all fields in source and destinations
		fields_src = con_src.introspection.get_table_description(con_src.cursor(), src_table)
		fields_dst = con_dst.introspection.get_table_description(con_dst.cursor(), dst_table)

		fnames_src = [f[0] for f in fields_src]
		fnames_dst = [f[0] for f in fields_dst]
		
		missings = [fn for fn in fnames_src if fn not in fnames_dst]
		additionals = [fn for fn in fnames_dst if fn not in fnames_src]
		common = [fn for fn in fnames_src if fn in fnames_dst]
		if missings:
			self.log('Missing fields (%s)' % ', '.join(missings), 1)
		if additionals:
			self.log('Additional fields (%s)' % ', '.join(additionals), 1)
		common_str_src = ', '.join([con_src.ops.quote_name(i) for i in common])
		common_str_dst = ', '.join([con_dst.ops.quote_name(i) for i in common])
		params_str = ', '.join(['%s' for i in common])

		# hack...
		if dst_table == 'digipal_itempart' and src_table == 'hand_itempart':
			common_str_dst = common_str_dst + ', pagination'
			params_str = params_str + ', %s'
			
		# 2 copy all the records over
		recs_src = self.sqlSelect(con_src, 'SELECT %s FROM %s' % (common_str_src, src_table))
		c = 0
		while True:
			rec_src = recs_src.fetchone()
			if rec_src is None: break
			# hack...
			if dst_table == 'digipal_itempart' and src_table == 'hand_itempart':
				rec_src = list(rec_src)
				rec_src.append(False)
			self.sqlWrite(con_dst, 'INSERT INTO %s (%s) VALUES (%s)' % (dst_table, common_str_dst, params_str), rec_src)
			c = c + 1
			#break
		self.log('Copied %s records' % c, 2)
		recs_src.close()
		
		return ret
			
	def sqlDeleteAll(self, con, table):
		ret = True
		
		try:
			self.sqlWrite(con, 'delete from %s' % table)
		except IntegrityError, e:
			print e
			ret = False
			
		return ret
	
	def sqlWrite(self, wrapper, command, arguments=[]):
		if not self.is_dry_run():
			cur = wrapper.cursor()
	
			#print command
			cur.execute(command, arguments)
			#wrapper.commit()
			cur.close()

	def sqlSelect(self, wrapper, command, arguments=[]):
		''' return a cursor,
			caller need to call .close() on the returned cursor 
		'''
		cur = wrapper.cursor()
		cur.execute(command, arguments)
		
		return cur

	def sqlSelectCount(self, con, table):
		ret = 0
		cur = self.sqlSelect(con, 'select count(*) from %s' % table)
		rec = cur.fetchone()
		ret = rec[0]
		cur.close()
		
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

	def log(self, message, log_level=3):
		''' log_level:
				0: fatal error
				1: warning
				2: info
				3: debug
		'''
		if log_level <= self.log_level:
			prefixes = ['ERROR: ', 'WARNING: ', '', ''] 
			from datetime import datetime
			timestamp = datetime.now().strftime("%y-%m-%d %H:%M:%S")
			try:
				print u'[%s] %s%s' % (timestamp, prefixes[log_level], message)
			except UnicodeEncodeError:
				print '???'
	