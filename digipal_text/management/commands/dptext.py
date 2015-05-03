from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option
from django.db import IntegrityError

from exon.customisations.digipal_text import models

class Command(BaseCommand):
    help = """
Digipal Text management tool.
    
Commands:
    
  copies    [IP_ID]
            List copies of the texts.
  
  restore   COPY_ID
            restore a copy
            
  markup    CONTENT_ID
            auto-markup a content
            
  search    QUERY
            search content by query 
            
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

        if command == 'list':
            known_command = True
            self.command_list()

        if command == 'copies':
            known_command = True
            self.command_copies()
            
        if command == 'restore':
            known_command = True
            self.command_restore()
            
        if command == 'units':
            known_command = True
            self.command_units()
        
        if command == 'markup':
            known_command = True
            self.command_markup()

#         if self.is_dry_run():
#             self.log('Nothing actually written (remove --dry-run option for permanent changes).', 1)
            
        if not known_command:
            print self.help
            
    def command_units(self):
        from digipal_text.models import TextUnit
        rs = TextUnit.objects
        #print repr(rs)
        rs = rs.all()
        for r in rs:
            print r.id 

    def get_friendly_datetime(self, dtime):
        return re.sub(ur'\..*', '', unicode(dtime))

    def get_content_xml_summary(self, content_xml):
        return '#%4s %8s %20s %20s %20s' % (content_xml.id, content_xml.get_length(), 
                self.get_friendly_datetime(content_xml.created), self.get_friendly_datetime(content_xml.modified), content_xml.text_content)
            
    def command_list(self):
        from digipal_text.models import TextContentXML
        for content_xml in TextContentXML.objects.all().order_by('text_content__item_part__display_label', 'text_content__type__name'):
            print self.get_content_xml_summary(content_xml)
        
    def command_markup(self):
        from digipal_text.models import TextContentXML
        if len(self.args) > 1:
            content_xml = TextContentXML.objects.filter(id=self.args[1]).first()
            if content_xml:
                print self.get_content_xml_summary(content_xml)
                
                versions = [content_xml.content]
                
                content_xml.convert()
                
                #versions.append(content_xml.content)
                
                #print repr(content_xml.content)
                
                # 1a
                # 1b
                # 14b1
                # 16a1
                # 179, 379
                
#                 pattern = ur'(?musi)&lt;\s*(\w+a)\s*&gt;'
#                 for folio in re.findall(pattern, content_xml.content):
#                     print folio
                content_xml.save()
                
        else:
            pass
    
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
        
        