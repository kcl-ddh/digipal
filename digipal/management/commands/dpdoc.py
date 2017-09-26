# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from mezzanine.conf import settings
import os
import re
from optparse import make_option
from digipal import utils  
from digipal.models import *
from digipal.utils import get_cms_page_from_title

class Command(BaseCommand):
    help = """
Digipal documentation tools.

Commands:

  html2md PATH
                        Returns Markdown output from a HTML file located at PATH 

  md2cms PATH --filter FILTER
                        Create or update CMS pages from .md files
                        Only process the .md files found under   
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
        make_option('--filter',
            action='store',
            dest='filter',
            default='',
            help='Filter'),
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
        
        if command == 'md2cms':
            known_command = True
            self.md2cms()

        if command == 'html2md':
            known_command = True
            self.html2md()
            
        if not known_command:
            raise CommandError('Unknown command: "%s".' % command)
    
    def html2md(self):
        if len(self.args) < 2:
            print 'ERROR: missing path. Check help.'
            exit()
            
        path = self.args[1]
        
        from digipal.views import doc
        from django.utils.text import slugify

        for path in utils.get_all_files_under(path, file_types='f', filters=self.options['filter'], extensions=['html', 'htm'], can_return_root=True):
            info = doc.get_md_from_html(path)
            target = os.path.join(doc.get_doc_root_path('digipal'), slugify(info['title']))+'.md'
            if 'confluence-workbox' in target:
                continue
            utils.write_file(target, info['md'])
            print '%s\n  => %s' % (path, target)
            for f in info['files']:
                print '   + %s' % f 
            
            #self.update_cms_page(doc_slug, slug, html)

        #print ret.encode('utf8', 'ignore')

    def md2cms(self):
        from digipal.views import doc
        
        doc_slug = 'doc'
        self.update_cms_page(doc_slug, draft=True)
        
        for path in utils.get_all_files_under(doc.get_doc_root_path('digipal'), file_types='f', filters=self.options['filter'], extensions='md', can_return_root=True):
            print path
            info = doc.get_doc_from_md(utils.read_file(path))
            page = None
            if info:
                content = u'<div class="mddoc">%s</div>' % info['content']
                page = self.update_cms_page(info['title'], content, doc_slug)
            if page:
                print '  => # %s (%s)' % (page.id, page.slug)

    def update_cms_page(self, title=None, content='', parent_title=None, draft=False):
        if not title:
            title = 'Untitled'
        
        from mezzanine.pages.models import Page, RichTextPage
        
        page = get_cms_page_from_title(title)
        
        in_menus = [2,3]
        
        # create the page
        from mezzanine.core.models import CONTENT_STATUS_PUBLISHED, CONTENT_STATUS_DRAFT
        
        if not page:
            parent_page = get_cms_page_from_title(parent_title)
            page = RichTextPage(title=title, content_model='richtextpage', parent=parent_page, content=content, status=CONTENT_STATUS_PUBLISHED)
            page.save()
            page.status = CONTENT_STATUS_DRAFT if draft else CONTENT_STATUS_PUBLISHED
            page.in_menus = in_menus
        else:
            # Can't find an easy way to edit page.richtextpage.content, so let's write directly to the DB!
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute('''update pages_richtextpage set content = %s where page_ptr_id = %s''', [content, page.id])
            
        page.save()
        
        return page
    