from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
import utils
from optparse import make_option
from os import listdir
from os.path import isfile, join
from digipal.models import Image

def get_originals_path():
	ret = join(getattr(settings, 'IMAGE_SERVER_ROOT', ''), getattr(settings, 'IMAGE_SERVER_ORIGINALS_ROOT', ''))
	return ret

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
		
		fetch URL [LINK_NAMES]
	
	"""
	
	args = 'list|upload'
	help = ''' Manage the Digipal images

----------------------------------------------------------------------

 ORIGINAL images are found under:

  %s

 IMAGE STORE (converted images) is found under:

  %s

----------------------------------------------------------------------

 To upload your document images in the database:

 1. manually copy your original images somewhere under the ORIGINAL folder:
	
 2. copy the original images to the IMAGE STORE (image files managed by the 
    image server) with this command:
	
    python manage.py dpim copy
	
 3. convert your images in the image store to the JPEG 2000 and upload them
    into the database:
	
    python manage.py dpim upload
	
 Image files can be processed selectively. Read the documentation below for 
 more details.

 WARNING: please do not leave your original images in the IMAGE STORE, they 
    might be deleted. Use the ORIGINAL folder instead (see above).

----------------------------------------------------------------------

 Commands:

    Working with the image store:

        list
            Lists the images on disk and if they are already uploaded

        upload
            Converts new images to JPEG 2000 and create the corresponding 
            Image records
		
        unstage
            Removes the images from the database (but leave them on disk)
	
    Dealing with orignal images:
	
        copy
            Copies the all the original images to the image store.
            Also converts the names so they are compatible with the image 
            server.
            Selection is made with the --filter option.
            Recommended to use 'originals' comamnd to test the selection.
			
        originals
            list all the original images,
            Selection is made with the --filter option.
    
    Database Image records:
    	
    	update_dimensions
    		Read the width and height and size of the images and save them in the database 

 Options:

    --filter X
        Select the images to be uploaded/listed/deleted by applying
        a filter on their name. Only files with X in their path or 
        filename will be selected.

    --offline
        Select only the images which are on disk an not in the DB

    --missing
        Select only the images which are on the DB and not on disk
		
 Examples:

    python manage.py dpim --filter canterbury upload
        upload all the images which contain 'canterbury' in their name
		
    python manage.py dpim --filter canterbury unstage
        remove from the database the Image records which point to
        an image with 'canterbury' in its name.
		
    python manage.py dpim --offline list
        list all the image which are only on disk and not in the DB
		
    python manage.py dpim --missing --filter canterbury list
        list all the image which are only in the database and not 
        on disk and which name contains 'canterbury'

----------------------------------------------------------------------

	''' % (get_originals_path(), get_image_path())
	
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
		make_option('--links',
			action='store',
			dest='links',
			default='',
			help='Link names'),
		make_option('--op',
			action='store',
			dest='out_path',
			default='.',
			help='out path'),
		make_option('--links_file',
			action='store',
			dest='links_file',
			default='',
			help='Link names'),
		make_option('--missing',
			action='store_true',
			dest='missing',
			default='',
			help='Only list images which are missing from disk'),
		) 
	
	def get_all_files(self, root):
		# Scan all the image files on disk (under root) and in the database.
		# Returns an array of file informations. For each file we have: 
		# 	{'path': path relative to settings.IMAGE_SERVER_ROOT, 'disk': True|False, 'image': Image object|None}
		ret = []

		all_images = Image.objects.all()
		image_paths = {}
		images = {}
		for image in all_images: 
			image_paths[os.path.normcase(image.iipimage.name)] = image.id
			images[image.id] = image
		
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

					id = image_paths.get(os.path.normcase(file_relative), 0)

					info = {
							'image': images.get(id, None),
							'disk': 1,
							'path': file_relative
							}
					
					if id:
						del images[id]
					
					ret.append(info)
			elif isdir(file):
				files.extend([join(file, f) for f in listdir(file)])
		
		# find the images in DB but not on disk
		for image in images.values():
			file_name = ''
			if image.iipimage:
				file_name = image.iipimage.name
			info = {
					'disk': os.path.exists(join(getattr(settings, 'IMAGE_SERVER_ROOT', ''), file_name)), 
					'path': file_name, 
					'image': image
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
		if command == 'fetch':
			known_command = True
			self.fetch(*args, **options)
			
		if command == 'update_dimensions':
			known_command = True
			self.update_dimensions(*args)
		
		if command in ('list', 'upload', 'unstage', 'update', 'remove'):
			known_command = True

			for file_info in self.get_all_files(root):
				file_relative = file_info['path']
				found_message = ''

				online = (file_info['image'] is not None)
				imageid = 0
				if online:
					imageid = file_info['image'].id
					
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
						image = None
						if command in ('update',):
							found_message = '[JUST UPDATED]'
							image = file_info['image']
						else:
							found_message = '[JUST UPLOADED]'
							image = Image()
							image.iipimage = file_relative
							image.image = 'x'
							image.caption = os.path.basename(file_relative)
							# todo: which rules should we apply here?
							image.display_label = os.path.basename(file_relative)

						# convert the image to jp2
						if command == 'upload':
							error_message = self.convert_image(image)
							if error_message:
								found_message += ' ' + error_message
								image = None
							else:
								found_message += ' [JUST CONVERTED]'
						
						if image: 
							image.save()
							imageid = image.id
						
				if command == 'remove' and file_info['disk']:
					file_abs_path = join(settings.IMAGE_SERVER_ROOT, file_relative)
					print file_abs_path
					if os.path.exists(file_abs_path):
						os.unlink(file_abs_path)
						found_message = '[REMOVED FROM DISK]'
					else:
						found_message = '[NOT FOUND]'
					processed = True
					
				if command == 'unstage' and online:
					processed = True
					
					found_message = '[JUST REMOVED FROM DB]'
					file_info['image'].delete()
						
				if self.is_verbose() or command == 'list' or processed:
					extra = ''
					if not file_info['disk'] and online and file_info['image'].image is not None and len(file_info['image'].image.name) > 2: 
						extra = file_info['image'].image.name
					print '#%s\t%-20s\t%s\t%s' % (imageid, found_message, file_relative, extra)
				
			print '%s images in DB. %s image on disk. %s on disk only. %s missing from DB.' % (counts['online'], counts['disk'], counts['disk_only'], counts['missing'])
			
		if command in ['copy', 'originals', 'copy_convert']:
			known_command = True
			self.processOriginals(args, options)

		if not known_command:
			raise CommandError('Unknown command: "%s".' % command)
	
	def update_dimensions(self, *args):
		options = self.options
		root = get_image_path()
		for file_info in self.get_all_files(root):
			file_relative = file_info['path']
			if options['filter'].lower() not in file_relative.lower():
				continue
			if file_info['disk']:
				file_path = os.path.join(settings.IMAGE_SERVER_ROOT, file_info['image'].path())
				if os.path.exists(file_path):
					file_info['image'].size = os.path.getsize(file_path)
			file_info['image'].dimensions()
			file_info['image'].save()
	
	def fetch(self, *args, **options):
		out_path = options['out_path']

		if len(args) > 1:
			base_url = args[1]
			i = 5177135
			# 5177311
			for i in range(5177218, 5177311 + 1):
				href = 'http://zzz/j2k/jpegNavMain.jsp?filename=Page%203&pid=' + str(i) + '&VIEWER_URL=/j2k/jpegNav.jsp?&img_size=best_fit&frameId=1&identifier=770&metsId=5176802&application=DIGITOOL-3&locale=en_US&mimetype=image/jpeg&DELIVERY_RULE_ID=770&hideLogo=true&compression=90'
				i += 1  
				print i
				found = self.download_images_from_webpage(href, out_path, str(i) + '.jpg')
				if not found: break
				

	def fetch_old(self, *args, **options):
		'''
			fetch http://zzz//P3.html --links-file "bible1" --op=img1
			
			Will save all the jpg images found at that address into a directory called img1.
			We first download the index from that address then follow each link with a name listed in bible1 file.
			Download all all the jpg images found in those sub-pages.
		'''
		out_path = options['out_path']

		if len(args) > 1:
			url = args[1]
			print url

			if options['links']:
				links = options['links'].split(' ')

			if options['links_file']:
				f = open(options['links_file'], 'rb')
				links = f.readlines()
				f.close()
				links = [link.strip() for link in links]
				
			if links:
				html = utils.wget(url)
				if not html:
					print 'ERROR: request to %s failed.' % url
				else:
					for link in links:
						print link 
						href = re.findall(ur'<a [^>]*href="([^"]*?)"[^>]*>\s*' + re.escape(link) + '\s*<', html)
						if href:
							href = href[0]
							href = re.sub(ur'/[^/]*$', '/' + href, url)
							print href
							
							self.download_images_from_webpage(href, out_path)
	
	def download_images_from_webpage(self, href, out_path=None, img_name=None):
		ret = False
		print href
		sub_html = utils.wget(href)
		
		if not sub_html:
			print 'WARNING: request to %s failed.' % sub_html
		else:
			ret = True
			# get the jpg image in the page
			#image_urls = re.findall(ur'<img [^>]*src="([^"]*?\.jpg)"[^>]*>', sub_html)
			#print sub_html
			image_urls = re.findall(ur'<img [^>]*src\s*=\s*"([^"]*?)"[^>]*?>', sub_html)
			print image_urls
			for image_url in image_urls:
				if not image_url.startswith('/'):
					image_url = re.sub(ur'/[^/]*$', '/' + image_url, href)
				else:
					image_url = re.sub(ur'^(.*?//.*?/).*$', r'\1' + image_url, href)
				print image_url
				
				# get the image
				image = utils.wget(image_url)
				
				if not image:
					print 'WARNING: request to %s failed.' % image_url
				else:
					# save it
					image_path = os.path.join(out_path, img_name or re.sub(ur'^.*/', '', image_url)) + ''
					print image_path
					utils.write_file(image_path, image)
		
		return ret
	
	def processOriginals(self, args, options):
		''' List or copy the original images. '''
		import shutil
		command = args[0]
		
		original_path = get_originals_path()
		jp2_path = get_image_path()
		
		all_files = []
		
		# scan the originals folder to find all the image files there
		files = [join(original_path, f) for f in listdir(original_path)]
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

		# list or copy the files
		for file_info in all_files:
			file_relative = file_info['path']
			if options['filter'].lower() not in file_relative.lower():
				continue

			file_relative_normalised = self.getNormalisedPath(file_relative)
			(file_relative_base, extension) = os.path.splitext(file_relative)
			(file_relative_normalised_base, extension) = os.path.splitext(file_relative_normalised)
			
			copied = False
			
			target = join(jp2_path, file_relative_normalised_base + extension)
			
			if isfile(target) or \
				isfile(join(jp2_path, file_relative_normalised_base + settings.IMAGE_SERVER_EXT)) \
				:
				copied = True

			status = ''
			if copied: status = 'COPIED'				
			print '[%6s] %s' % (status, file_relative)

			if command in ['copy', 'copy_convert']:
				# create the folders
				path = os.path.dirname(target)
				if not os.path.exists(path):
					os.makedirs(path)
					
				# copy the file
				if command == 'copy':
					print '\tCopy to %s' % target
					shutil.copyfile(join(original_path, file_relative), target)
					
				if command == 'copy_convert':
					# convert the file jp2
					status = 'COPIED+CONVERTED'
					
					from iipimage.storage import CONVERT_TO_TIFF, CONVERT_TO_JP2
					shell_command = CONVERT_TO_JP2 % (join(original_path, file_relative), re.sub(ur'\.[^.]+$', ur'.'+settings.IMAGE_SERVER_EXT, target))
 					ret_shell = self.run_shell_command(shell_command)
 					if ret_shell:
 						status = 'CONVERSION ERROR: %s (command: %s)' % (ret_shell[0], ret_shell[1])
	
	def getNormalisedPath(self, path):
		from digipal.utils import get_normalised_path
		return get_normalised_path(path)

	def is_verbose(self):
		return self.options['verbosity'] >= 2
	
	def get_verbosity(self):
		# 0: minimal output, 1: normal output, 2: verbose, 3: very verbose
		return self.options['verbosity']

	def convert_image(self, image):
		ret = None
		
		# normalise the image path and rename so iipimage server doesn't complain
		name = os.path.normpath(image.iipimage.name)
		path, basename = os.path.split(name)		
		name = os.path.join(path, re.sub(r'(\s|,)+', '_' , basename.lower()))
		path, ext = os.path.splitext(name)
		name = path + ur'.' + settings.IMAGE_SERVER_EXT
		
		ret_shell = []
		
		# rename the file to .jp2
		if image.iipimage.name != name:
			try:
				os.rename(os.path.join(settings.IMAGE_SERVER_ROOT, image.iipimage.name), os.path.join(settings.IMAGE_SERVER_ROOT, name))
				image.iipimage.name = name
				image.save()
			except Exception, e:
				ret_shell = [e, 'rename']
		else:
			# assume the file is already a jpeg 2k, return
			#return ret
			pass
				
		# convert the image to tiff
		if not ret_shell:
			from iipimage.storage import CONVERT_TO_TIFF, CONVERT_TO_JP2
			
			full_path = os.path.join(settings.IMAGE_SERVER_ROOT, image.iipimage.name)
			temp_file = full_path + '.tmp.tiff'
			
			command = CONVERT_TO_TIFF % (full_path, temp_file)
			ret_shell = self.run_shell_command(command)
			
		# convert the image to jp2
		if not ret_shell:
			command = CONVERT_TO_JP2 % (temp_file, full_path)
			ret_shell = self.run_shell_command(command)
		
		if ret_shell:
			ret = '[CONVERSION ERROR: %s (command: %s)]' % (ret_shell[0], ret_shell[1])
			
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

