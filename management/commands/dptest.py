from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option
from django.db import IntegrityError
from digipal.models import *
from digipal.utils import natural_sort_key

class Command(BaseCommand):
	help = """
Digipal blog management tool.
	
Commands:

	locus
	
	email
	
	validate	

"""
	
	args = 'locus|email'
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

		if command == 'locus':
			known_command = True
			self.test_locus(options)

		if command == 'natsort':
			known_command = True
			self.test_natsort(options)

		if command == 'email':
			known_command = True
			self.test_email(options)

		if command == 'rename_images':
			known_command = True
			self.rename_images(args[1])

		if command == 'img_info':
			known_command = True
			self.img_info(args[1])
	
		if command == 'img_compare':
			known_command = True
			self.img_compare(args[1], args[2])
			
		if command == 'adjust_offsets':
			self.adjust_offsets(args[1], args[2])

		if command == 'correct_annotations':
			known_command = True
			self.correct_annotations(args[1])

		if command == 'validate':
			known_command = True
			self.fetch_and_test(*args[1:])

	def fetch_and_test(self, root=None):
		from utils import web_fetch
		
		if not root:
			root = 'http://localhost/'
		print 'Base URL: %s' % root
		
		stats = []
		
		pages = [
				'',
				# main search
				'digipal/search/',
				'digipal/search/?terms=+&basic_search_type=manuscripts&ordering=&years=&result_type='
				# search graph
				'digipal/search/graph/?script_select=&character_select=&allograph_select=punctus+elevatus&component_select=&feature_select=&terms=&submitted=1&view=images',
				# browse images
				'digipal/page',
				# image
				'digipal/page/364/',
				'digipal/page/364/allographs',
				'digipal/page/364/copyright/',
				# static pages
				'about',
				'about/how-to-use-digipal/',
				'feedback/',
				# blog and news
				'blog/category/blog/',
				'blog/category/news/',
				'blog/bl-labs-launch-palaeographers-speak-with-forked-ascenders/',
				# records
				'digipal/hands/278/?basic_search_type=manuscripts&result_type=hands',
				'digipal/scribes/96/',
				'digipal/manuscripts/715/',
				# collection
				'http://localhost/digipal/page/lightbox/basket/',
				]
		
		#pages = ['digipal/search/graph/?script_select=&character_select=&allograph_select=punctus+elevatus&component_select=&feature_select=&terms=&submitted=1&view=images',]
		
		for page in pages:
			url = root + page

			sp = {'url': url, 'msgs': [], 'body': ''}
			stats.append(sp) 

			print 
			print 'Request %s' % url
			
			res = web_fetch(url)
			if res['status'] != '200':
				print 'ERROR: %s !!!!!!!!!!!!!!!!!!!' % res['status']
				continue
			if res['error']:
				print 'ERROR: %s !!!!!!!!!!!!!!!!!!!' % res['error']
				continue
			if res['body']:
				# prefix the line with numbers
				ln = 0
				lines = []
				sp['msgs'] = self.find_errors(res['body'])
				for line in res['body'].split('\n'):
					ln += 1
					lines.append('%6s %s' % (ln, line))
				sp['body'] = '\n'.join(lines)
			print '\n'.join(sp['msgs'])
			

	def find_errors(self, body):
		ret = []
		
		# custom validations
		ln = 0
		containers = 0
		print '\t %s KB' % (len(body) / 1024)
		for line in body.split('\n'):
			ln += 1
			msg = ''
			if line.find('<script') > -1 and line.find('src') == -1:
				msg = 'Inline script'
			if re.search('style\s*=\s*"', line):
				msg = 'Inline style'
			if re.search('class.+\Wcontainer\W', line):
				containers += 1
			if msg:
				ret.append('%6s: %s (%s)' % (ln, msg, line.strip()))
		if containers > 0:
			ret.append('%6s: %s containers' % ('', containers))
		
		# HTML validation
		import urllib2, time
		attempts = 0
		ok = True
		while True:
			attempts += 1
			ok = True
			from py_w3c.validators.html.validator import HTMLValidator
			vld = HTMLValidator()
			try:
				vld.validate_fragment(body)
			except urllib2.HTTPError:
				time.sleep(1)
				ok = False
			if ok: break
			if attempts > 2: break

		if ok:
			for info in vld.warnings:
				ret.append('%6s: [W3C WARNING] %s' % (info['line'], info['message']))
			for info in vld.errors:
				ret.append('%6s: [W3C ERROR  ] %s' % (info['line'], info['message']))
		else:
			ret.append('\tFailed to call W3C validation.')
		
		return ret

	def adjust_offsets(self, offset_path, target_path):
		# we calculate a better offset for the annotations by searching for a 
		# best match of one annotation along a line between the old (cropped) 
		# and new (uncropped) image.    
		# pm dptest adjust_offsets crop_offsets.json c:\vol\digipal2\images\originals\bl\backup_bl_from_server\bl
		
		###
		# UPDATE THE LOCAL DB FROM THE STG BEFORE RUNNING THIS!!!
		###
		
		import json
		from PIL import Image
		images = json.load(open(offset_path, 'rb'))
		c = -1
		ca = 0
		for rel_path, info in images['images'].iteritems():
			images['images'][rel_path]['offset'].append(images['images'][rel_path]['offset'][1])
			images['images'][rel_path]['offset'].append(images['images'][rel_path]['offset'][2])
			if images['images'][rel_path]['offset'][3] < 0: images['images'][rel_path]['offset'][3] = 0
			if images['images'][rel_path]['offset'][4] > 0: images['images'][rel_path]['offset'][4] = 0
			
			#if rel_path != ur'arundel_60\83v': continue
			#if rel_path != ur'add_46204\recto': continue
			#if rel_path != ur'cotton_caligula_axv\152v': continue
			#if rel_path != ur'harley_5915\13r': continue
			c += 1
			print '%s (%d left)' % (rel_path, len(images['images']) - c)
			
			src_path = os.path.join(images['root'], rel_path) + '.tif'
			dst_path = os.path.join(target_path, rel_path) + '.tif'
			if not os.path.exists(dst_path): 
				print '\tskipped (new image)'
				continue
			
			# find an annotation in the database
			a = Annotation.objects.filter(image__iipimage__endswith=rel_path.replace('\\', '/')+'.jp2')
			if a.count() == 0:
				print '\tskipped (no annotation)'
				continue
			a = a[0]

			if images['images'][rel_path]['offset'][2] != 0:
				print '\tskipped (y-crop <> 0)'
				print '\t!!!!!!!!!!!!! y-crop is not zero !!!!!!!!!!!!!!!'
				continue

			# open the images
			ca += 1
			src_img = Image.open(src_path)
			dst_img = Image.open(dst_path)
			sps = src_img.convert('L').load()
			dps = dst_img.convert('L').load()
			print '\tsrc: %s x %s; dst: %s x %s' % (src_img.size[0], src_img.size[1], dst_img.size[0], dst_img.size[1])
			
			# find the best match for this annotation region on the new image
			
			# We scan a whole line on the uncropped image to find the x value
			# that minimises the pixelwise difference of annotation regions.  
			box = a.get_coordinates(None, True)
			print '\tbox: %s' % repr(box)
			size = [(box[1][i] - box[0][i] + 1) for i in range(0, 1)]
			min_info = (0, 1e6)
			for x in range(0, src_img.size[0] - size[0]):
				diff = 0
				diff0 = None
				for ys in range(box[0][1], box[1][1] + 1):
					for xs in range(0, box[1][0] - box[0][0] + 1):
						if diff0 is None:
							diff0 = sps[x + xs, ys] - dps[box[0][0] + xs, ys]
							diff = abs(diff0)
						else:
							diff += abs(sps[x + xs, ys] - dps[box[0][0] + xs, ys] - diff0)
				if diff < min_info[1]:
					min_info = [x, diff]
			print '\tbest match at x = %s (diff = %s)' % (min_info[0], min_info[1])
			offsetx = min_info[0] - box[0][0]
			images['images'][rel_path]['offset'][3] = offsetx
			print '\toffset: %s; detected: %s' % (repr(info['offset']), offsetx)
			if info['offset'][1] != offsetx:
				print '\t******************************************'
				#if info['offset'][1] < 0 and offsetx != 0:
				#	print '\t!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
		
		print '%d images with annotations.' % ca
		
		print
		
		print json.dumps(images)
	
	def correct_annotations(self, info_path):
		import json
		images = json.load(open(info_path, 'rb'))
		
		counts = {'image': 0, 'annotation': 0} 
		for path, info in images['images'].iteritems():
			#if path != 'harley_5915\\13r': continue
			#if path != 'harley_585\\191v': continue
			#if path != 'arundel_60\\83v': continue
			offsets = info['offset']
			if offsets[0]:
				print path.replace('\\', '/')
				#continue
				print '\t%s' % repr(offsets)
				imgs = Image.objects.filter(iipimage__endswith=path.replace('\\', '/')+'.jp2')
				c = imgs.count()
				if c == 0:
					#print '\tWARNING: Image record not found.'
					continue
				if c > 1:
					#print '\tWARNING: More than one Image record not found.'
					continue
				
				annotations = imgs[0].annotation_set.filter().distinct()
				if annotations.count():
					counts['image'] += 1
					for annotation in annotations:
						counts['annotation'] += 1
						#print
						#print annotation.id, annotation.vector_id 
						#print annotation.cutout
						#print annotation.geo_json
						annotation.cutout = self.get_uncropped_cutout(annotation, info)
						annotation.geo_json = self.get_uncropped_geo_json(annotation, offsets)
						
						#print annotation.cutout
						#print annotation.geo_json
						annotation.save()
					print '\t%d annotations' % annotations.count()
				
		#print counts
		
	
	# TODO: remove, only temporary
	def get_uncropped_cutout(self, annotation, image_info):
		ret = annotation.cutout	
		
		offsets = image_info['offset']
		
		'''
			Correct the region parameter in the cutout URLs
			E.g. http://digipal-stg.cch.kcl.ac.uk/iip/iipsrv.fcgi?FIF=jp2/bl/cotton_vitellius_cv/248r.jp2&RST=*&HEI=1206&RGN=0.381031,0.334415,0.019381,0.023682&CVT=JPG
			
			0.381031,0.334415,0.019381,0.023682
			
			px,py,lx,ly
			
			px: x position of the top right corner of the box expressed as a ratio over the image width
			lx: the width of the box as a ratio over the image width
			
			Algorithm and formula for the conversion:
			
			for r in (px,py,lx,ly):
				nl = new image length in that axis			
				l = old image length in that axis
				o' = o = offset in that axis
				o' = 0 if r = lx or ly or o < 0
				r' = ((r * l) + o') / nl
		'''
		match = re.search(ur'RGN=([^,]+),([^,]+),([^,]+),([^,]+)&', ret)
		#size = annotation.image.iipimage._get_image_dimensions()
		size = (image_info['x'], image_info['y'])
		rgn = []
		for i in range(1, 5):
			r = float(match.group(i))

			# axis: 0 for x; 1 for y
			d = 0
			if i in (2, 4): d = 1
			offset = offsets[3 + d]
			nl = size[d]
			l = nl - abs(offset)
			#if (offset < 0) or (i > 2): offset = 0
			if (i > 2): offset = 0
			#if (i > 1): offset = 0

			r = ((r * l) + offset) / nl
			
			rgn.append(r)
		
		#print rgn 
		ret = re.sub(ur'RGN=[^&]+', ur'RGN=' + ','.join(['%.6f' % r for r in rgn]), ret)
		#print ret
		
		return ret
	
	def get_uncropped_geo_json(self, annotation, offsets):
		import json
		geo_json = annotation.geo_json

		'''
		{
			"type":"Feature",
			"properties":{"saved":1},
			"geometry":{"type":"Polygon",
						"coordinates":[
							[
								[1848,3957.3333740234],
								[1848,4103.3333740234],
								[1942,4103.3333740234],
								[1942,3957.3333740234],
								[1848,3957.3333740234]
							]
						]
						},
			"crs":{"type":"name","properties":{"name":"EPSG:3785"}}
		}
		'''

		# See JIRA-229, some old geo_json format are not standard JSON
		# and cause trouble with the deserialiser (json.loads()).
		# The property names are surrounded by single quotes
		# instead of double quotes.
		# simplistic conversion but in our case it works well
		# e.g. {'geometry': {'type': 'Polygon', 'coordinates':
		#	 Returns {"geometry": {"type": "Polygon", "coordinates":
		geo_json = geo_json.replace('\'', '"')

		geo_json = json.loads(geo_json)
		
		coo = geo_json['geometry']['coordinates'][0]
		for c in coo:
			#if offsets[1] > 0:
			c[0] = int(c[0] + offsets[3])
			#if offsets[2] > 0:
			#c[1] = int(c[1] - offsets[4])
		
		# convert the coordinates
		ret = json.dumps(geo_json)
		
		return ret
		
					
# 				
# 		
# 		from digipal.models import Annotation
# 		annotations = Annotation.objects.filter(image__id=590)
# 		offsets = [True, 0, 499]
# 		for a in annotations:
# 			a.get_uncropped_cutout(offsets)
# 			break

	def img_compare(self, path_src, path_dst):
		
		import json
		src = json.load(open(path_src, 'rb'))
		dst = json.load(open(path_dst, 'rb'))
		
		new = []
		different = []
		same = []
		
		# compare the two list of images
		for src_file in src['images']:
			src['images'][src_file]['offset'] = [False, 0, 0]
			src_info = src['images'][src_file]
			if src_file not in dst['images']:
				new.append(src_file)
			else:
				dst_info = dst['images'][src_file]
				if src_info['size'] != dst_info['size']:
					different.append(src_file)
				else:
					same.append(src_file)

# 		print '\nSame\n'
# 		same = sorted(same)
# 		for f in same:
# 			print f
# 
# 		print '\nNew\n'
# 		new = sorted(new)
# 		for f in new:
# 			print f
		
		print '\nDifferent\n'
		different = sorted(different)
		for f in different:
			#if not(f == 'add_46204\\recto'): continue
			src['images'][f]['offset'] = self.get_image_offset(src, dst, f)
			print f
			print '', src['images'][f]['offset']
			#print '', src['images'][f]['offset']
		
		# save the offsets
		print
		
		print json.dumps(src)
		
		print 
		
		print '\n'
		print '%d source images;  %d destination images' % (len(src['images']), len(dst['images']))
		print '%d new images; %d same images; %d different images' % (len(new), len(same), len(different))
		
	def get_image_offset(self, src, dst, f):
		'''
		 Given one image and its cropped version, returns where the crop was made.
		 We assume that at least one corner of the original image has not been cropped.
		
		 Input:
		 	src a dictionary as returned by get_info() on the source folder (uncropped)
		 	dst a dictionary as returned by get_info() on the dest. folder (cropped)
		 	f the relative path to the image, i.e. the key of the image in src and dst.
		 
		 Returns a tuple [found, x, y]
		 If found = True the dst image is a crop of the src image. Otherwise it is False and x, y can be ignored.
		 x >= 0 then x pixels have been discarded from the top of the original image to make the crop.
			x < 0 then -x pixels have been discarded from the bottom of the original image to make the crop.
		 y = same principle as for x but with left (> 0) and right (< 0).
		'''
		from PIL import Image

		cropped_path = os.path.join(dst['root'], f) + '.' + dst['images'][f]['ext']
		uncropped_path = os.path.join(src['root'], f) + '.' + src['images'][f]['ext']
		cropped_img = Image.open(cropped_path)
		uncropped_img = Image.open(uncropped_path)

		ret = [False, uncropped_img.size[0] - cropped_img.size[0], uncropped_img.size[1] - cropped_img.size[1]]
		
		corner_diffs = [self.are_corner_identical(cropped_img, uncropped_img, *pos) for pos in [[0,0],[-1,0],[-1,-1],[0,-1]]]
		min_index = corner_diffs.index(min(corner_diffs))
		if min_index == 0:
 			ret = [True, -ret[1], -ret[2]]
		if min_index == 1:
			ret = [True, ret[1], -ret[2]]
		if min_index == 2:
			ret = [True, ret[1], ret[2]]
		if min_index == 3:
			ret = [True, -ret[1], ret[2]]
			
		
		#print corner_diffs
		
# 		if self.are_corner_identical(cropped_img, uncropped_img, 0, 0):
# 			ret = [True, -ret[1], -ret[2]]
# 		elif self.are_corner_identical(cropped_img, uncropped_img, -1, 0):
# 			ret = [True, ret[1], -ret[2]]
# 		elif self.are_corner_identical(cropped_img, uncropped_img, -1, -1):
# 			ret = [True, ret[1], ret[2]]
# 		elif self.are_corner_identical(cropped_img, uncropped_img, 0, -1):
# 			ret = [True, -ret[1], ret[2]]

# 		ret = [False, 0, 0]
#  
# 		width_diff = src['images'][f]['y'] - dst['images'][f]['y'] 
# 		if src['images'][f]['y'] != dst['images'][f]['y']:
# 			if src['images'][f]['x'] != dst['images'][f]['x']:
# 				print '\tDifferent dimensions (%d x %d <> %d x %d)' % (src['images'][f]['x'], src['images'][f]['y'], dst['images'][f]['x'], dst['images'][f]['y'])
# 			else:
# 				print '\tDifferent widths %d <> %d' % (src['images'][f]['y'], dst['images'][f]['y'])
#  				
		
		return ret

	def are_corner_identical(self, cropped_img, uncropped_img, fromx=0, fromy=0):
		#ret = True
		ret = 0
		
		imgs = [cropped_img, uncropped_img]
		imgps = [img.load() for img in imgs]
		
		# scan direction for x and y dimensions
		dir = [fromx, fromy]
		if dir[0] == 0: dir[0] = 1
		if dir[1] == 0: dir[1] = 1
		
		# initial position in each image
		pos = [[fromx, fromy], [fromx, fromy]]
		
		# convert -1 pos (relative to right or bottom edge) to absolute position
		for i in (0, 1):
			for j in (0, 1):
				if pos[i][j] == -1: pos[i][j] = imgs[i].size[j] + pos[i][j]
				
		def is_color_identical(p0, p1):
			# not strictly true but it's a good approximation
			return sum(p0) == sum(p1)

		avgs = [[0,0,0], [0,0,0]]

		for k in range(0, 400):
			p0 = imgps[0][pos[0][0], pos[0][1]]
			p1 = imgps[1][pos[1][0], pos[1][1]]
			#ret += abs(p0[0] - p1[0]) + abs(p0[1] - p1[1]) + abs(p0[2] - p1[2])
			ret += abs(p0[0] - p1[0])
			pos[0][0] += dir[0]
			pos[0][1] += dir[1]
			pos[1][0] += dir[0]
			pos[1][1] += dir[1]

		#print sum([avgs[0]]) / 3.0 / 100.0
		
		return ret
		
	def img_info(self, path):
		
		ret = {'root': path}
		
		ret['images'] = self.get_image_info(path)
		
		import json
		print json.dumps(ret)
		
		#img_dst = self.get_image_info(target_path)
		
	def get_image_info(self, path):
		ret = {}
		from PIL import Image
		
		files = [os.path.join(path, f) for f in os.listdir(path)]
		while files:
			file = files.pop(0)
			
			file = os.path.join(path, file)
			
			if os.path.isfile(file):
				(file_base_name, extension) = os.path.splitext(file)
				if extension.lower() in settings.IMAGE_SERVER_UPLOAD_EXTENSIONS:
					file_relative = os.path.relpath(file, path)

					st = os.stat(file)
					key = re.sub(ur'\.[^.]+$', ur'', file_relative)
					ret[key] = {
								'ext': extension[1:],
								'size': st.st_size,
								'date': st.st_mtime,
								}
					try:
						im = Image.open(file)
						ret[key]['x'] = im.size[0]
						ret[key]['y'] = im.size[1]
					except:
						ret[key]['x'] = 0
						ret[key]['y'] = 0

			elif isdir(file):
				files.extend([os.path.join(file, f) for f in os.listdir(file)])
		
		return ret
	
	def rename_images(self, csv_path):
		print csv_path
		import csv
		import shutil
		
		with open(csv_path, 'rb') as csvfile:
			#line = csv.reader(csvfile, delimiter=' ', quotechar='|')
			csvreader = csv.reader(csvfile)
			base_dir = os.path.dirname(csv_path)
			first_line = True		
			for line in csvreader:
				if first_line:
					first_line = False
					continue
				file_name_old = line[0]
				matches = re.match(ur'(.*),(.*)', line[1])
				if not matches:
					matches = re.match(ur'(.*)(recto|verso)', line[1])
				if matches:
					dir_name = matches.group(1).lower()
					file_name = matches.group(2).lower().strip()
					
					file_name = re.sub(ur'^f\.\s*', '', file_name)
					file_name = file_name.replace('*', 'star')
					file_name = re.sub(ur'\s+', '_', file_name.strip())
					
					dir_name = re.sub(ur'\b(\w)\s?\.\s?', ur'\1', dir_name)
					dir_name = re.sub(ur'\s+', '_', dir_name.strip())
					dir_name = re.sub(ur'\.', '', dir_name).strip()
					
					# create the dir
					dir_name = os.path.join(base_dir, dir_name)
					#print dir_name, file_name
					if not os.path.exists(dir_name):
						os.mkdir(dir_name)
					file_name = os.path.join(dir_name, file_name) + re.sub(ur'^.*(\.[^.]+)$', ur'\1', file_name_old)
					if not os.path.exists(file_name):
						#shutil.copyfile(os.path.join(base_dir, file_name_old), file_name)
						print file_name
				else:
					print 'No match (%s)' % line[1]
				
	
	def test_natsort(self, options):
		#[ ItemPart.objects.filter(display_label__icontains='royal')]
		sms = ['A.897.abc.ixv', 'Hereford Cathedral Library O.IX.2', 'Hereford Cathedral Library O.VI.11']
		for s in sms:
			print s, natural_sort_key(s)
		print sorted(sms, key=lambda i: natural_sort_key(i))
		#print natural_sort_key('A.897.abc.ixv')
		#print natural_sort_key('Hereford Cathedral Library O.IX.2')
		#'Hereford Cathedral Library O.VI.11'
		return
	
# 		l = list(ItemPart.objects.filter(display_label__icontains='royal').order_by('display_label'))
# 			
# 		import re
# 
# 		_nsre = re.compile('([0-9]+)')
# 		def natural_sort_key(s):
# 			return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]
# 		l = sorted(l, key=lambda i: natural_sort_key(i.display_label))
# 		
# 		for i in l:
# 			print (i.display_label).encode('ascii', 'ignore')

	def test_email(self, options):
		#from django.core.mail import send_mail
	   	#send_mail('Subject here', 'Here is the message.', 'gnoelp@yahoo.com', ['gnoelp@yahoo.com'], fail_silently=False)
		# Import smtplib for the actual sending function
		import smtplib
		
		# Import the email modules we'll need
		from email.mime.text import MIMEText
		
		# Open a plain text file for reading.  For this example, assume that
		# the text file contains only ASCII characters.
		# Create a text/plain message
		msg = MIMEText('my message')
		
		# me == the sender's email address
		# you == the recipient's email address
		msg['Subject'] = 'Subject'
		msg['From'] = 'gnoelp@yahoo.com'
		msg['To'] = 'gnoelp@yahoo.com'
		
		# Send the message via our own SMTP server, but don't include the
		# envelope header.
		s = smtplib.SMTP('localhost')
		s.sendmail(msg['From'], msg['To'].split(', '), msg.as_string())
		s.quit()	   	
	
	def test_locus(self, options):
		from digipal.models import Image
		i = Image()
		for l in [
					('10r', ('10', 'r')), 
					('10v', ('10', 'v')), 
					('11', ('11', None)), 
					('', (None, None)), 
					(None, (None, None)), 
					('1 10 r', ('10', 'r')),
					('1 10 r 9 v8', ('9', 'v'))
				]:
			i.locus = l[0]
			i.update_number_and_side_from_locus()
			print '%s => %s, %s' % (i.locus, i.folio_number, i.folio_side)
			if i.folio_number != l[1][0] or i.folio_side != l[1][1]:
				print '\tERROR, expected %s, %s.' % (l[1][0], l[1][1])
		
