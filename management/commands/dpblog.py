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
Digipal blog management tool.
	
Commands:
	
  reformat
                        Fix the formatting errors after a Wordpress import 

  importtags
                        Import the tags from a Wordpress export 

"""
	
	args = 'reformat|importtags'
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

	def handle(self, *args, **options):
		
		self.log_level = 3
		
		self.options = options
		
		if len(args) < 1:
			raise CommandError('Please provide a command. Try "python manage.py help dpmigrate" for help.')
		command = args[0]
		
		known_command = False

		if command == 'reformat':
			known_command = True
			self.reformat(options)
			
		if command == 'importtags':
			known_command = True
			self.importTags(args, options)

		if self.is_dry_run():
			self.log('Nothing actually written (remove --dry-run option for permanent changes).', 1)
	
	def importTags(self, args, options, as_categories=False):
		# if as_categories is True, the tags will be imported as Mezzanine categories rather than keywords
		
		# <wp:tag><wp:term_id>20</wp:term_id><wp:tag_slug>about-digipal</wp:tag_slug><wp:tag_name><![CDATA[About DigiPal]]></wp:tag_name></wp:tag>
		
		if len(args) < 2:
			raise CommandError('Please provide the path of XML file as the first argument.')
		
		xml_file = args[1]
		
		# load and parse the xml file
		tags = {}
		namespaces = {'wp': 'http://wordpress.org/export/1.2/'}
		try:
			import lxml.etree as ET
			tree = ET.parse(xml_file)
			#tree.register_namespace('wp', 'http://wordpress.org/export/1.2/')
			root = tree.getroot()
		except Exception, e:
			raise CommandError('Cannot parse %s: %s' % (xml_file, e))
		
		# get the mezzanine categories
		from mezzanine.blog.models import BlogPost
		from mezzanine.generic.models import AssignedKeyword
		if as_categories:
			from mezzanine.blog.models import BlogCategory as CatOrKwd
		else:
			from mezzanine.generic.models import Keyword as CatOrKwd
		
		categories = {}
		for category in CatOrKwd.objects.all():
			categories[category.slug] = category
		
		model_name = CatOrKwd._meta.object_name
		if model_name == 'BlogCategory': model_name = 'Category'
		model_field_name = 'keywords'
		if as_categories: model_field_name = 'categories'
		category_domain = 'post_tag'
		if as_categories: category_domain = 'category'
			
		print '%d %s in Mezzanine' % (len(categories), model_name)
		
		# load all the WP tag names and ids
		# add the category if it doesn't already exists
		xml_tags = root.findall('.//wp:tag', namespaces)
		for xml_tag in xml_tags:
			xml_tag.findall('.//wp:tag', namespaces)
			tag = {
					'id': 	xml_tag.find('wp:term_id', namespaces).text,
					'slug': xml_tag.find('wp:tag_slug', namespaces).text,
					'name': xml_tag.find('wp:tag_name', namespaces).text,
					}
			tags[tag['id']] = tag
			
			# add the category if it doesn't already exists
			if tag['slug'] not in categories:
				print '\tAdd new %s to Mezzanine: %s' % (model_name, tag['slug'], )
				category = CatOrKwd(slug=tag['slug'], title=tag['name'], site_id=1)
				if not self.is_dry_run():
					category.save()
				categories[category.slug] = category
				
		print '%d tags in Wordpress' % len(xml_tags)
			
		# Tag the posts
		#
		# <item>
		#	<title>Text, Image and the Digital Research Environment</title>
		#	<category domain="post_tag" nicename="about-digipal"><![CDATA[About DigiPal]]></category>
		#
		xml_items = {}
		for xml_item in tree.findall('.//item', namespaces):
			xml_items[xml_item.find('title').text] = xml_item
		
		tag_count = 0
		modified_posts = {}
		for post in BlogPost.objects.all().order_by('id'):
			if post.title not in xml_items:
				print '\tWARNING: blog post #%s not found in Wordpress dump' % (post.id,)
				continue
			
			xml_item = xml_items[post.title]
			
			for xml_tag_slug in [c.get('nicename') for c in xml_item.findall('category[@domain=\'%s\']' % category_domain)]:
				#print getattr(post, model_field_name).all()
				
				if xml_tag_slug not in [c.slug for c in getattr(post, model_name.lower() + '_list')()]:
					object_to_add = categories[xml_tag_slug]
# 					keyword_id = Keyword.objects.get_or_create(title=keyword)[0].id
# 					page.keywords.add(AssignedKeyword(keyword_id=keyword_id))
					if not as_categories:
						object_to_add = AssignedKeyword(keyword=categories[xml_tag_slug])
					getattr(post, model_field_name).add(object_to_add)
					#print categories[xml_tag_slug].slug
					print '\tAdd %s %s to post %s' % (model_name, xml_tag_slug, post.slug)
					if not self.is_dry_run():
						post.save()
					tag_count += 1
					modified_posts[post.slug] = 1
		
		print 'Added %d %s to %d posts.' % (tag_count, model_name, len(modified_posts.keys()))
			#post.categories
			#xml_items = tree.findall('.//item[title/text()=\'%s\']' % (post.title,), namespaces)
			#print len(xml_items)
	
	def reformat(self, options):
		# e.g. https://digipal2.cch.kcl.ac.uk/blog/anglo-saxon-mss-online-ii-copenhagen-roy-lib-and-bav/
		from mezzanine.blog.models import BlogPost
		from digipal_django.redirects import get_redirected_url
		 
		#print get_redirected_url('http://www.digipal.eu/blogs/blog/the-problem-of-digital-dating-part-i/')
		#print get_redirected_url('/blogs/blog/the-problem-of-digital-dating-part-i/')
		uploaded_files = {}
		for file_info in self.find_all_files(settings.UPLOAD_IMAGES_ROOT):
			path, filename = os.path.split(file_info['path'])
			uploaded_files[filename] = file_info['path']
		
		for blog in BlogPost.objects.all().order_by('id'):
			content = blog.content
			print '#%s: %s' % (blog.id, blog.slug)
			if False:
				self.log('1. remove large empty spaces before a paragraph', 2)
				#content = re.sub(ur'(?musi)<p/>\s*<br/>', '<br/>', content)
				content = re.sub(ur'(?ui)<p/>', '', content)
				content = re.sub(ur'(?ui)<p>\s*</p>', '', content)
		
			#self.log('3. fix tables', 2)
			urls = re.findall(ur'(?ui)(?:["\'])(https?://www.digipal.eu[^\'"]+)', content)
			for url in urls:
				warning = 'WARNING, NOT FOUND: '
				new_url = get_redirected_url(url, True)
				
				path, filename = os.path.split(new_url)
				if filename in uploaded_files:
					new_url = '/media/' + settings.UPLOAD_IMAGES_URL + re.sub(r'\\', r'/', uploaded_files[filename])
				
				if new_url != url: warning = ''
				
				print '\t%s%s => %s' % (warning, url, new_url)
				content = content.replace(url, new_url)
			#content = re.sub(ur'(?ui)https?://[^\'"]+', '', content)
			
			if content != blog.content:
				self.log('\t#%d, %s, modified content' % (blog.id, blog.slug), 2)
				blog.content = content
				blog.save()
	
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

	def find_all_files(self, original_path):
		# scan the originals folder to find all the image files there
		from os import listdir
		from os.path import join, isfile

		files = [join(original_path, f) for f in listdir(original_path)]
		all_files = []
		while files:
			file = files.pop(0)
			
			file = join(original_path, file)
			
			if isfile(file):
				(file_base_name, extension) = os.path.splitext(file)
				if extension.lower() in settings.IMAGE_SERVER_UPLOAD_EXTENSIONS:
					file_relative = os.path.relpath(file, original_path)

					info = {
							'disk': 1,
							'path': file_relative
							}
					
					all_files.append(info)
			elif isdir(file):
				files.extend([join(file, f) for f in listdir(file)])
		return all_files		

	def fixSequences(self):
		from django.db import connections
		con = connections[self.options.get('db', 'default')]
		con.enter_transaction_management()
		con.managed()
		con.disable_constraint_checking()

		#from django.db import connection
		print '> Fix all sequences in the database'
		cursor = con.cursor()

		from django.contrib.contenttypes.models import ContentType
		types = ContentType.objects.all()
		c = 0
		for type in types:
			model = type.model_class()
			if model and model._meta.auto_field and model._meta.auto_field.column == 'id':
				c += 1
				#print model
				cmd = "select setval('%(table_name)s_%(seq_field)s_seq', (select max(%(seq_field)s) from %(table_name)s) )" % {'table_name': model._meta.db_table, 'seq_field': model._meta.auto_field.column}
				cursor.execute(cmd)

		con.commit()
		con.leave_transaction_management()

		print '\t%s sequences fixed' % c
		