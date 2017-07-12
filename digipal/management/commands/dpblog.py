from django.core.management.base import BaseCommand, CommandError
from mezzanine.conf import settings
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

  importtags [PATH_TO_WORDPRESS_EXPORT_XML_FILE]
                        Import the tags from a Wordpress export
                        
  fixdqpaths
                        Fix the Disqus comment paths from the old WP site to 
                        the new one  

  fix_keywords
  						Fix the blog keywords.
  						Convert lower case to upper case. Merge if necessary.
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
			raise CommandError('Please provide a command. Try "python manage.py help dpblog" for help.')
		command = args[0]
		
		known_command = False

		if command == 'reformat':
			known_command = True
			self.reformat(options)
			
		if command == 'importtags':
			known_command = True
			self.importTags(args, options)
		
		if command == 'geturlmapping':
			known_command = True
			self.getUrlMapping(args, options)

		if command == 'fix_keywords':
			known_command = True
			self.fix_keywords(args, options)

		if self.is_dry_run():
			self.log('Nothing actually written (remove --dry-run option for permanent changes).', 1)
			
		if not known_command:
			print self.help
	
	def rename_keyword(self, keyword, new_name, new_keyword=None):
		from mezzanine.generic.models import Keyword, AssignedKeyword
		for ak in AssignedKeyword.objects.filter(keyword=keyword):
			post = ak.content_object
			print u'\tused in #%s %s (%s)' % (post.id, unicode(post)[0:15], post.keywords_string)
			post.keywords_string = post.keywords_string.replace(keyword.title, new_name)
			if new_keyword:
				ak.keyword = new_keyword
				ak.save()
		if new_keyword:
			print u'\tmerge with %s' % new_keyword.title
			keyword.delete()				
		else:
			keyword.title = new_name
			print '\trename into %s' % keyword.title
			keyword.save()
			
	def fix_keywords(self, args, options):
		# JIRA 338
		# 1. find all keywords
		from mezzanine.generic.models import Keyword, AssignedKeyword
		for kw in Keyword.objects.all():
			if kw.title[0].islower():
				print kw.title
				kw_target = Keyword.objects.filter(title__iexact=kw.title).exclude(id=kw.id)
				if kw_target:
					kw_target = kw_target[0]
					self.rename_keyword(kw, kw_target.title, kw_target) 
				else:
					self.rename_keyword(kw, kw.title.title())
		
	def getDQComments(self):
		# http://disqus.com/api/docs/posts/list/
		# https://github.com/disqus/disqus-python
 		from disqusapi import DisqusAPI
 		from mezzanine.conf import settings
 		settings.use_editable()
 		
 		disqus = DisqusAPI(settings.COMMENTS_DISQUS_API_SECRET_KEY, settings.COMMENTS_DISQUS_API_PUBLIC_KEY)
 		posts = disqus.forums.listPosts(forum='digipal')
 		for post in posts:
 			print post
 		print posts
		
	
	def getUrlMapping(self, args, options, as_categories=False):
		# Two modes: 
		#	1. convert from WP to Django / Mezzanine blog with all the correct urls and paths
		#		Just leave old_domain = '' or None
		#	2. convert from one Django / Mezzanine blog to another (simple domain mapping)
		#		Set old_domain to the source django domain
		
		old_domain = ur'digipal2-dev.cch.kcl.ac.uk'
		#old_domain = ''
		new_domain = ur'www.digipal.eu'
		
		# no way to update the posts using the API as of May 2013		
		if len(args) < 2:
			raise CommandError('Please provide the path of XML file as the first argument.')
		
		xml_file = args[1]
		
		# load and parse the xml file
		wp_name_space = '{http://wordpress.org/export/1.2/}'
		try:
			import lxml.etree as ET
			tree = ET.parse(xml_file)
		except Exception, e:
			raise CommandError('Cannot parse %s: %s' % (xml_file, e))

		from digipal_django.redirects import get_redirected_url
		for link in tree.findall('//item/link'):
			old_url = link.text
			if re.search(r'/attachment/|\?', old_url): continue
			if re.search(r'\?', old_url):
				continue
			
			new_url = get_redirected_url(old_url, True, True)
			
			new_url = re.sub(ur'^([^/]+://)[^/]+(.*)$', r'\1%s\2' % new_domain, new_url)
			if old_domain:
				old_url = re.sub(ur'^([^/]+://)[^/]+(.*)$', r'\1%s\2' % old_domain, new_url)
			
			print ur'%s, %s' % (old_url, new_url)
	
	def importTags(self, args, options, as_categories=False):
		# if as_categories is True, the tags will be imported as Mezzanine categories rather than keywords
		
		# <wp:tag><wp:term_id>20</wp:term_id><wp:tag_slug>about-digipal</wp:tag_slug><wp:tag_name><![CDATA[About DigiPal]]></wp:tag_name></wp:tag>
		
		if len(args) < 2:
			raise CommandError('Please provide the path of XML file as the first argument.')
		
		xml_file = args[1]
		
		# load and parse the xml file
		tags = {}
		#namespaces = {'wp': 'http://wordpress.org/export/1.2/'}
		wp_name_space = '{http://wordpress.org/export/1.2/}'
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
		#xml_tags = root.findall('.//%stag' % wp_name_space, namespaces)
		xml_tags = root.findall('.//%stag' % wp_name_space)
		for xml_tag in xml_tags:
			xml_tag.findall('.//%stag' % wp_name_space)
			tag = {
					'id': 	xml_tag.find('%sterm_id' % wp_name_space).text,
					'slug': xml_tag.find('%stag_slug' % wp_name_space).text,
					'name': xml_tag.find('%stag_name' % wp_name_space).text,
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
		for xml_item in tree.findall('.//item'):
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
# 					image.keywords.add(AssignedKeyword(keyword_id=keyword_id))
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
				
# 				if warning:
# 					print '> ' + filename
# # 					for f in uploaded_files.keys():
# # 						print '%-50s %s' % (f, uploaded_files[f])
# 					return
				
				content = content.replace(url, new_url)
			#content = re.sub(ur'(?ui)https?://[^\'"]+', '', content)
			
			if content != blog.content:
				self.log('\t#%d, %s, modified content' % (blog.id, blog.slug), 2)
				blog.content = content
				blog.save()
	
	def is_dry_run(self):
		return self.options.get('dry-run', False)
	
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
				#if extension.lower() in settings.IMAGE_SERVER_UPLOAD_EXTENSIONS:
				file_relative = os.path.relpath(file, original_path)

				info = {
						'disk': 1,
						'path': file_relative
						}
				
				all_files.append(info)
			elif isdir(file):
				files.extend([join(file, f) for f in listdir(file)])
		return all_files		

