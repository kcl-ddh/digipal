# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option
import utils
from digipal import utils as dputils
from digipal.models import Text, CatalogueNumber, Description, TextItemPart, Collation
from digipal.models import Text
from digipal.models import HistoricalItem, ItemPart
from django.db.models import Q
from digipal.models import *

class Command(BaseCommand):
    help = """
Digipal XML management tool

Commands:

  convert PATH_TO_XML PATH_TO_XSLT

  validate PATH_TO_XML [PATH_TO_DTD]
  
  stats PATH_TO_XML
  
  html2xml PATH_TO_HTML
  
"""
    
    args = 'backup|restore|list|tables|fixseq|tidyup1|checkdata1|pseudo_items|duplicate_ips'
    #help = 'Manage the Digipal database'
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run, don\'t change any data.'),
        )
    
    def handle(self, *args, **options):
        
        self.options = options
        self.cargs = args
        
        command = ''
        known_command = False
        if len(args) > 0:
            command = args[0]
            if command == 'convert':
                known_command = True
                self.convert()

            if command == 'val':
                known_command = True
                self.val()

            if command == 'stats':
                known_command = True
                self.stats()
                
            if command == 'html2xml':
                known_command = True
                self.html2xml()
            
        if not known_command:
            raise CommandError('Unknown command: "%s".' % command)
    
    def stats(self):
        if len(self.cargs) < 2:
            raise CommandError('Convert requires 1 arguments')

        xml_path = self.cargs[1]
        xml_string = utils.readFile(xml_path)
        
        print 'Count - Tag'
        print
        
        elements = re.findall(ur'<(\w+)', xml_string)
        for el in set(elements):
            print '%8d %s' % (elements.count(el), el)
            
        print
        print 'Unique tag-attributes'
        print
        els = {}
        elements = re.findall(ur'<([^>]+)>', xml_string)
        for el in elements:
            el = el.strip()
            if el[0] not in ['/', '?', '!']:
                els[el] = 1
        for el in sorted(els):
            print el
        
    def val(self):
        if len(self.cargs) < 2:
            raise CommandError('Convert requires 1 arguments')
        
        xml_path = self.cargs[1]
        val_path = None
        if len(self.cargs) > 2:
            val_path = self.cargs[2]
        
        xml_string = utils.readFile(xml_path)
        
        import lxml.etree as ET
        try:
            dom = dputils.get_xml_from_unicode(xml_string)
            
            if val_path:
                from io import StringIO
                dtd = ET.DTD(open(val_path, 'rb'))
                valid = dtd.validate(dom)

                if not valid:
                    for error in dtd.error_log.filter_from_errors():
                        print error
            
        except ET.XMLSyntaxError as e:
            print u'XML Syntax Error %s' % e

    def convert(self):
        if len(self.cargs) < 3:
            raise CommandError('Convert requires 2 arguments')
        
        xml_path = self.cargs[1]
        xslt_path = self.cargs[2]
        
        xml_string = utils.readFile(xml_path)
        xml_string = re.sub(ur'\bxmlns=', ur'xmlns2=', xml_string)
        xslt_string = utils.readFile(xslt_path)
        
        ret = dputils.get_xslt_transform(xml_string, xslt_string)
        
        print str(ret)
            
        return ret

    def html2xml(self):
        if len(self.cargs) < 2:
            raise CommandError('Convert requires 1 arguments')
        
        html_path = self.cargs[1]
        
        html_string = utils.readFile(html_path)
        
        import re
        
        html_string = re.sub(ur'.*(?musi)(<body.*/body>).*', ur'\1', html_string)
        
        from BeautifulSoup import BeautifulSoup
        soup = BeautifulSoup(html_string, 'html.parser')
        ret = soup.prettify()
        
        print ret
        
        #print str(ret)
            
        return ret
        
        
