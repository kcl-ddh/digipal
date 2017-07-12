from django.core.management.base import BaseCommand, CommandError
from mezzanine.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option

class Command(BaseCommand):
	help = """
Manage the Digipal urls
	
Commands:
	
  listurls --wgetfile FILEPATH
                        Lists the urls in FILEPATH
                        FILEPATH if obtained with the output of wget -r on a website
                        
  testurls --wgetfile FILEPATH --url BASEURL
                        test all the urls found in FILEPATH against the site starting with URL
                        FILEPATH if obtained with the output of wget -r on a website
"""
	
	args = 'listurls'
	option_list = BaseCommand.option_list + (
        make_option('--db',
            action='store',
            dest='db',
            default='default',
            help='Name of the database configuration'),
		make_option('--wgetfile',
			action='store',
			dest='wgetfile',
			default='',
			help='path to the file which contains output from wget -r'),
		make_option('--ignoreqs',
			action='store_true',
			dest='ignoreqs',
			default=False,
			help='ignore the query string part of the URL'),
		make_option('--url',
			action='store',
			dest='url',
			default=False,
			help='URL'),
		) 
	
	def testUrls(self, options):
		root = options.get('url', '')
		if not root:
			raise CommandError('Please provide a file path using --url URL')
		root = re.sub('/^', '', root)
			
		urls = self.listUrls(options)
		for url in urls:
			url = root + url
			status = self.testUrl(url)
			if not re.search(r'200$', status):
				print '[%8s] %s' % (status, url)
	
	def testUrl(self, url):
		status = '0'
		
		import urlparse
		parts = urlparse.urlsplit(url)
		import httplib
		try:
			conn = httplib.HTTPConnection(parts.hostname, parts.port)
			conn.request('HEAD', parts.path)
			res = conn.getresponse()
			headers = dict(res.getheaders()) 
			status = '%s' % res.status
			if headers.has_key('location') and headers['location'] != url:
				status = '%s+%s' % (status, self.testUrl(headers['location']))
		except StandardError, e:
			print e
			pass
		
		return status
		
	def listUrls(self, options):
		exclude_extensions = ['\.js|\.css|\.pdf|\.png|\.jpg']
		wgetfile = options.get('wgetfile', '')
		if not wgetfile:
			raise CommandError('Please provide a file path using --wgetfile FILEPATH')
		if not os.path.exists(wgetfile):
			raise CommandError('%s not found')
		
		content = self.read_file(wgetfile)
		
		urls = {}
		for url in re.findall(r'(https?:\S+)', content):
			# make it relative
			url = re.sub(r'^https?://[^/]*', '', url)
			# exclude list
			if re.search(r'%s(\?|$)' % exclude_extensions, url):
				continue
			if re.search('/feed|category|tag/', url):
				continue
			# remove query string part
			if options.get('ignoreqs', False):
				url = re.sub('\?.*$', '', url)
			urls[url] = 1

		urls = urls.keys()
		urls.sort()
		
		return urls		

	def handle(self, *args, **options):
		
		if len(args) < 1:
			raise CommandError('Please provide a command. Try "python manage.py help dpurls" for help.')
		command = args[0]
		
		known_command = False

		if command == 'listurls':
			known_command = True
			self.listUrls(options)
			for url in urls:
				print url
			
			print '%s urls' % len(urls)
			
		if command == 'testurls':
			known_command = True
			self.testUrls(options)

		if not known_command:
			raise CommandError('Unknown command: "%s".' % command)
	
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
		
	def read_file(self, file_path): 
	    ret = ''
	    try: 
	        text_file = open(file_path, 'r')
	        ret = text_file.read()
	        text_file.close()
	    except Exception, e:
	        pass
	    return ret
