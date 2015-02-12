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
Digipal Text management tool.
    
Commands:
    
  copies    [IP_ID]
            List copies of the texts.
  
  restore   COPY_ID
            restore a copy
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
        self.args = args
        
        if len(args) < 1:
            print self.help
            return
        command = args[0]
        
        known_command = False

        if command == 'copies':
            known_command = True
            self.command_copies()
            
        if command == 'restore':
            known_command = True
            self.command_restore()
        
#         if self.is_dry_run():
#             self.log('Nothing actually written (remove --dry-run option for permanent changes).', 1)
            
        if not known_command:
            print self.help
    
    def command_copies(self):
        from digipal_text.models import TextContentXMLCopy
        copies = TextContentXMLCopy.objects.all().order_by('-id')
        if len(self.args) > 1:
            ipid = self.args[1]
            copies = copies.filter(source__text_content__item_part_id=ipid)
        
        for copy in copies:
            print ', '.join([str(v) for v in (copy.id, copy.source.text_content, copy.created, len(copy.content))])
            
    def command_restore(self):
        if len(self.args) < 2:
            print 'ERROR: please provide a copy ID.'
            return
        copyid = self.args[1]
        from digipal_text.models import TextContentXMLCopy
        copy = TextContentXMLCopy.objects.filter(id=copyid).first()
        if not copy:
            print 'ERROR: no copy with ID #%s.' % copyid
            return
        print 'Restore copy #%s, "%s"' % (copyid, copy.source.text_content)
        
        copy.restore()
        
        