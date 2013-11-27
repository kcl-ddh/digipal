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
		
