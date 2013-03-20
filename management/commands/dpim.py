from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option
from os import listdir
from os.path import isfile, join
from digipal.models import Page

def get_image_path():
	ret = join(getattr(settings, 'IMAGE_SERVER_ROOT', ''), getattr(settings, 'IMAGE_SERVER_UPLOAD_ROOT', ''))
	return ret

class Command(BaseCommand):
	"""
	Digipal image management tools.
	
	Commands:
	
		list
	
		upload
		
		update
	
	"""
	
	args = 'list|upload'
	help = '''Manage the Digipal images
	
	----------------------------------------------------------------------
	
	To upload your document images in the database:
	
	1. copy your images to:
		"%s" 
		(see settings.py:IMAGE_SERVER_UPLOAD_ROOT)
	2. python manage.py dpim -v 2 upload
	
	This command will automatically convert new images to jp2 and create
	a new Page record in the database for it.
	
	Note that the converted images will replace the original images so 
	make sure you have a copy of your images somewhere else.
	
	The folders containing the images should not contain spaces or commas
	please remove them or replace them before uploading the images.
	
	----------------------------------------------------------------------
	
	Commands:
	
		upload:
			convert new images to JPEG 2000 and create the corresponding 
			Page records
			
		list:
			list the images on disk and if they are already uploaded
			
		unstage
			remove the images from the database (but leave them on disk)
	
	Options:
	
		--filter X
			select the images to be uploaded/listed/deleted by applying
			a filter on their name. Only files with X in their path or 
			filename will be selected.

		--offline
			select only the images which are on disk an not in the DB

		--missing
			select only the images which are on the DB and not on disk
	
	Examples:
	
		python manage.py dpim --filter canterbury upload
			upload all the images which contain 'test' in their name
			
		python manage.py dpim --filter canterbury unstage
			remove from the database the Page records which point to
			an image with 'canterbury' in its name.
			
		python manage.py dpim --offline list
			list all the image which are only on disk and not in the DB
			
		python manage.py dpim --missing --filter canterbury list
			list all the image which are only in the database and not 
			on disk and which name contains 'canterbury'
	
	----------------------------------------------------------------------
	
	''' % get_image_path()
	
	option_list = BaseCommand.option_list + (
        make_option('--db',
            action='store',
            dest='db',
            default='default',
            help='Name of the database configuration'),
#		make_option('--verbose',
#			action='store_true',
#			dest='verbose',
#			default=False,
#			help='Verbose mode'),
		make_option('--filter',
			action='store',
			dest='filter',
			default='',
			help='Only treat image names that contain the given string'),
		make_option('--offline',
			action='store_true',
			dest='offline',
			default='',
			help='Only list images which are offline'),
		make_option('--missing',
			action='store_true',
			dest='missing',
			default='',
			help='Only list images which are missing from disk'),
		) 
	
	def get_all_files(self, root):
		# Scan all the image files on disk (under root) and in the database.
		# Returns an array of file informations. For each file we have: 
		# 	{'path': path relative to settings.IMAGE_SERVER_ROOT, 'disk': True|False, 'page': Page object|None}
		ret = []

		all_pages = Page.objects.all()
		page_paths = {}
		pages = {}
		for page in all_pages: 
			page_paths[os.path.normcase(page.iipimage.name)] = page.id
			pages[page.id] = page
		
		# find all the images on disk
		current_path = root
		
		files = [join(current_path, f) for f in listdir(current_path)]
		while files:
			file = files.pop(0)
			
			file = join(current_path, file)
			
			if isfile(file):
				(file_base_name, extension) = os.path.splitext(file)
				if extension.lower() in settings.IMAGE_SERVER_UPLOAD_EXTENSIONS:
					file_relative = os.path.relpath(file, settings.IMAGE_SERVER_ROOT)

					id = page_paths.get(os.path.normcase(file_relative), 0)

					info = {
							'page': pages.get(id, None),
							'disk': 1,
							'path': file_relative
							}
					
					if id:
						del pages[id]
					
					ret.append(info)
			elif isdir(file):
				files.extend([join(file, f) for f in listdir(file)])
		
		# find the images in DB but not on disk
		for page in pages.values():
			file_name = ''
			if page.iipimage:
				file_name = page.iipimage.name
			info = {
					'disk': os.path.exists(join(getattr(settings, 'IMAGE_SERVER_ROOT', ''), file_name)), 
					'path': file_name, 
					'page': page
					}
			if file_name == '':
				info['disk'] = False
			ret.append(info)
		
		return ret
	
	def handle(self, *args, **options):
		
		root = get_image_path()
		if not root:
			raise CommandError('Path variable IMAGE_SERVER_ROOT not set in your settings file.')
		if not isdir(root):
			raise CommandError('Image path not found (%s).' % root)
		if len(args) < 1:
			raise CommandError('Please provide a command. Try "python manage.py help dpdb" for help.')
		command = args[0]
		if options['db'] not in settings.DATABASES:
			raise CommandError('Database settings not found ("%s"). Check DATABASE array in your settings.py.' % options['db'])

		db_settings = settings.DATABASES[options['db']]
		
		self.options = options
		
		known_command = False
		counts = {'online': 0, 'disk': 0, 'disk_only': 0, 'missing': 0}
		if command in ('list', 'upload', 'unstage', 'update'):
			known_command = True

			for file_info in self.get_all_files(root):
				file_relative = file_info['path']
				found_message = ''

				online = (file_info['page'] is not None)
				pageid = 0
				if online:
					pageid = file_info['page'].id
					
				if options['filter'].lower() not in file_relative.lower():
					continue
				
				if options['offline'] and online:
					continue

				if options['missing'] and file_info['disk']:
					continue
				
				if not online:
					found_message = '[OFFLINE]'
				elif not file_info['disk']:
					found_message = '[MISSING FROM DISK]'
				else:
					found_message = '[ONLINE]'
					
				if online:
					counts['online'] += 1
				if file_info['disk']:
					counts['disk'] += 1
				if file_info['disk'] and not online:
					counts['disk_only'] += 1
				if not file_info['disk'] and online:
					counts['missing'] += 1
					
				processed = False
				
				if (command == 'upload' and not online) or (command == 'update' and online):
					processed = True
					
					file_path, basename = os.path.split(file_relative)		
					new_file_name = os.path.join(file_path, re.sub(r'(\s|,)+', '_' , basename.lower()))
					if re.search(r'\s|,', new_file_name):
						found_message = '[FAILED: please remove spaces and commas from the directory names]'
					else:
						page = None
						if command in ('update',):
							found_message = '[JUST UPDATED]'
							page = file_info['page']
						else:
							found_message = '[JUST UPLOADED]'
							page = Page()
							page.iipimage = file_relative
							page.image = 'x'
							page.caption = os.path.basename(file_relative)
							# todo: which rules should we apply here?
							page.display_label = os.path.basename(file_relative)

						# cpnvert the image to jp2
						if command == 'upload':
							error_message = self.convert_image(page)
							if error_message:
								found_message += ' ' + error_message
								page = None
							else:
								found_message += ' [JUST CONVERTED]'
						
						if page: 
							page.save()
							pageid = page.id
						
				if command == 'unstage' and online:
					processed = True
					
					found_message = '[JUST REMOVED FROM DB]'
					file_info['page'].delete()
						
				if self.is_verbose() or command == 'list' or processed:
					extra = ''
					if not file_info['disk'] and online and file_info['page'].image is not None and len(file_info['page'].image.name) > 2: 
						extra = file_info['page'].image.name
					print '#%s\t%-20s\t%s\t%s' % (pageid, found_message, file_relative, extra)
				
			print '%s pages in DB. %s image on disk. %s on disk only. %s missing from DB.' % (counts['online'], counts['disk'], counts['disk_only'], counts['missing'])
			
		if not known_command:
			raise CommandError('Unknown command: "%s".' % command)
	
	def is_verbose(self):
		return self.options['verbosity'] >= 2
	
	def get_verbosity(self):
		# 0: minimal output, 1: normal output, 2: verbose, 3: very verbose
		return self.options['verbosity']

	def convert_image(self, page):
		ret = None
		
		# normalise the image path and rename so iipimage server doesn't complain
		name = os.path.normpath(page.iipimage.name)
		path, basename = os.path.split(name)		
		name = os.path.join(path, re.sub(r'(\s|,)+', '_' , basename.lower()))
		path, ext = os.path.splitext(name)
		name = path + '.jp2'
		
		ret_shell = []
		
		# rename the file to .jp2
		if page.iipimage.name != name:
			try:
				os.rename(os.path.join(settings.IMAGE_SERVER_ROOT, page.iipimage.name), os.path.join(settings.IMAGE_SERVER_ROOT, name))
				page.iipimage.name = name
				page.save()
			except Exception, e:
				ret_shell = [e, 'rename']
		else:
			# assume the file is already a jpeg 2k, return
			return ret
				
		# convert the image to tiff
		if not ret_shell:
			from iipimage.storage import CONVERT_TO_TIFF, CONVERT_TO_JP2
			
			full_path = os.path.join(settings.IMAGE_SERVER_ROOT, page.iipimage.name)
			temp_file = full_path + '.tmp.tiff'
			
			command = CONVERT_TO_TIFF % (full_path, temp_file)
			ret_shell = self.run_shell_command(command)
			
		# convert the image to jp2
		if not ret_shell:
			command = CONVERT_TO_JP2 % (temp_file, full_path)
			ret_shell = self.run_shell_command(command)
		
		if ret_shell:
			ret = '[CONVERSION ERROR: %s]' % (ret_shell[0], ret_shell[1])
			
		# remove the tiff file
		try:
			os.remove(temp_file)
		except:
			pass
		
		return ret
		
	def run_shell_command(self, command):
		ret = None
		if self.get_verbosity() >= 2:
			print '\t' + command
		try:
			os.system(command)
		except Exception, e:
			#os.remove(input_path)
			#raise CommandError('Error executing command: %s (%s)' % (e, command))
			ret = [e, command]
		finally:
			# Tidy up by deleting the original image, regardless of
			# whether the conversion is successful or not.
			#os.remove(input_path)
			pass
		return ret

