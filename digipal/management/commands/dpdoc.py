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
from digipal.models import Text, CatalogueNumber, Description, TextItemPart, Collation
from digipal.models import Text
from digipal.models import HistoricalItem, ItemPart
from django.db.models import Q
from digipal.models import *

class Command(BaseCommand):
    help = """
Digipal documentation tools.

Commands:

  html2md PATH
                        Converts a html file to a md file 
    """
    
    args = 'backup|restore|list|tables|fixseq|tidyup1|checkdata1|pseudo_items|duplicate_ips'
    #help = 'Manage the Digipal database'
    option_list = BaseCommand.option_list + (
        make_option('--db',
            action='store',
            dest='db',
            default='default',
            help='Database alias'),
        make_option('--branch',
            action='store',
            dest='branch',
            default='',
            help='Branch name'),
        make_option('--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force changes despite warnings'),
        make_option('--table',
            action='store',
            dest='table',
            default='',
            help='Name of the table to backup'),
        make_option('--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run, don\'t change any data.'),
        )
    
                
    def handle(self, *args, **options):
        
        self.options = options
        self.args = args
        
        if len(args) < 1:
            raise CommandError('Please provide a command. Try "python manage.py help dpdb" for help.')
        command = args[0]
        
        known_command = False

        if command == 'html2md':
            known_command = True
            self.html2md()
            
        if not known_command:
            raise CommandError('Unknown command: "%s".' % command)
    
    def html2md(self):
        from digipal.utils import read_file
        
        if len(self.args) < 2:
            print 'ERROR: missing path. Check help.'
            exit()
            
        path = self.args[1]
        
        html = read_file(path)
        
        # convert to md
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html).prettify()
        ret = unicode(soup)
        
        # strip all unnecessary spaces
        ret = re.sub(ur'>\s+', ur'>', ret)
        ret = re.sub(ur'\s+<', ur'<', ret)
        
        # convert <hx> to #
        for i in range(1, 5):
            ret = re.sub(ur'<h%s>(.*?)</h%s>' % (i, i), ur'\n%s \1\n' % ('#' * i,), ret)
            
        # convert <p> to paragraphs
        ret = re.sub(ur'<p>(.*?)</p>\s*', ur'\1\n\n', ret)
        
        # convert <li>
        ret = re.sub(ur'\s*<li>(.*?)</li>\s*', ur'\n* \1', ret)

        #print repr(ret.encode('utf8', 'ignore'))
        print ret.encode('utf8', 'ignore')
        
        print 'done'
