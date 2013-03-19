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
			convert new images and create Page records
		update
			update the Page records	
		list:
			list the images on disk and if they are already uploaded
		deldb
			remove the images from the database (but leave them on disk)
	
	Options:
	
		--filter X
			select the images to be uploaded/listed/deleted by applying
			a filter on their name. Only files with X in their path or 
			filename will be selected.
	
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
		) 
	
	def handle(self, *args, **options):
		
		path = get_image_path()
		if not path:
			raise CommandError('Path variable IMAGE_SERVER_ROOT not set in your settings file.')
		if not isdir(path):
			raise CommandError('Image path not found (%s).' % path)
	
		if len(args) < 1:
			raise CommandError('Please provide a command. Try "python manage.py help dpdb" for help.')
		command = args[0]
		
		known_command = False

		if options['db'] not in settings.DATABASES:
			raise CommandError('Database settings not found ("%s"). Check DATABASE array in your settings.py.' % options['db'])

		db_settings = settings.DATABASES[options['db']]
		
		self.options = options
		
		if command in ('list', 'upload', 'deldb', 'update'):
			from digipal.models import Page
			pages = Page.objects.all()
			page_paths = {}
			for page in pages: page_paths[os.path.normcase(page.iipimage.name)] = page.id
			
			known_command = True
			# find all the images on disk
			current_path = path
			
			files = []
			files.extend([join(current_path, f) for f in listdir(current_path)])
			filtered_files = []
			all_files = [] 
			while files:
				file = files.pop(0)
				
				file = join(current_path, file)
				
				if isfile(file):
					(file_base_name, extension) = os.path.splitext(file)
					if extension.lower() in settings.IMAGE_SERVER_UPLOAD_EXTENSIONS:
						if options['filter'].lower() not in file.lower():
							continue
						file_relative = os.path.relpath(file, settings.IMAGE_SERVER_ROOT)
						all_files.append(file_relative)
						found_message = ''
						if not page_paths.has_key(os.path.normcase(file_relative)) or command == 'update':
							found_message = '[OFFLINE]'
							filtered_files.append(file_relative)
							
							if command in ('upload', 'update'):
								file_path, basename = os.path.split(file_relative)		
								new_file_name = os.path.join(file_path, re.sub(r'(\s|,)+', '_' , basename.lower()))
								
								if re.search(r'\s|,', new_file_name):
									found_message = '[UPLOAD FAILED: please remove spaces and commas from the directory names]'
								else:
									found_message = '[JUST UPLOADED]'
									if command in ('update',):
										found_message = '[JUST UPDATED]'
										page = Page.objects.get(id=page_paths[os.path.normcase(file_relative)])
									else:
										page = Page()
										page.iipimage = file_relative
									
									page = Page()
									page.image = 'x'
									page.caption = os.path.basename(file_relative)
									# todo: which rules should we apply here?
									page.display_label = os.path.basename(file_relative)

									# cpnvert the image to jp2
									if command == 'upload':
										error_message = self.convert_image(page)
										if error_message:
											found_message += ' ' + error_message
										else:
											found_message += ' [JUST CONVERTED]'
											page.save()
								
								# force the conversion to jp2
						elif command == 'deldb':
							found_message = '[JUST REMOVED]'
							page = Page.objects.get(id=page_paths[os.path.normcase(file_relative)])
							page.delete()
								
						else:
							found_message = '[ALREADY ONLINE]'
							
						if self.is_verbose():
							print '%s %s' % (file_relative, found_message)
				elif isdir(file):
					files.extend([join(file, f) for f in listdir(file)])
			
			print '%s pages in DB. %s image on disk. %s on disk only.' % (pages.count(), len(all_files), len(filtered_files))
			
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
		
		if page.iipimage.name != name:
			try:
				os.rename(os.path.join(settings.IMAGE_SERVER_ROOT, page.iipimage.name), os.path.join(settings.IMAGE_SERVER_ROOT, name))
				page.iipimage.name = name
				page.save()
			except Exception, e:
				ret_shell = [e, 'rename']
				
		if not ret_shell:
			from iipimage.storage import CONVERT_TO_TIFF, CONVERT_TO_JP2
			
			full_path = os.path.join(settings.IMAGE_SERVER_ROOT, page.iipimage.name)
			temp_file = full_path + '.tmp.tiff'
			
			# convert the image to tiff
			command = CONVERT_TO_TIFF % (full_path, temp_file)
			ret_shell = self.run_shell_command(command)
			
		if not ret_shell:
			# convert the image to jp2
			command = CONVERT_TO_JP2 % (temp_file, full_path)
			ret_shell = self.run_shell_command(command)
		
		if ret_shell:
			ret = '[CONVERSION ERROR: %s]' % (ret_shell[0], ret_shell[1])
			
		# remove the tmp file
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

