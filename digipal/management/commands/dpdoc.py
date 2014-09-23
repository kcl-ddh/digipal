# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import re
from optparse import make_option
import utils  
from digipal.models import *

class Command(BaseCommand):
    help = """
Digipal documentation tools.

Commands:

  html2md PATH
                        Returns Markdown output from a HTML file located at PATH 
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
        soup = BeautifulSoup(html)
        soup = soup.body
        
        # remove any line breaks within the <ul>s
        for tag in soup.find_all('ul'):
            tag_markup = unicode(tag)
            tag_markup = re.sub(ur'(?musi)<p>|</p>' , ur' ', tag_markup)
            tag_markup = re.sub(ur'(?musi)\s+' , ur' ', tag_markup)
            tag.replace_with(BeautifulSoup(tag_markup).ul)

        # images
        # <img src="./collections_files/col-management.png">
        # ![](/digipal/static/doc/col-management.png?raw=true)
        # copy the image file
        # convert the tag
        import digipal
        import shutil
        static_path = os.path.join(digipal.__path__[0], 'static/doc')
        for tag in soup.find_all('img'):
            file_name = re.sub('.*?([^/?]*)($|\?|#)', ur'\1', tag['src'])
            img_src = os.path.join(os.path.dirname(path), tag['src'])
            img_dst = os.path.join(static_path, file_name)
            imgmd = '![](/static/doc/%s?raw=true)' % file_name
            tag.replace_with(imgmd)
            shutil.copyfile(img_src, img_dst)
        
        # convert <li>s
        for tag in soup.find_all('li'):
            prefix = ''
            for parent in tag.parents:
                if parent.name in ('ul', 'ol'):
                    if not prefix:
                        if parent.name == 'ul':
                            prefix = '* '
                        if parent.name == 'ol':
                            prefix = '%s. ' % (len([s for s in tag.previous_siblings if s.name == 'li']) + 1)
                    else:
                        prefix = '#SPACE#' + prefix
            for tag_str in tag.strings:
                tag_str.insert_before(prefix)
                break
        
        # serialise into a string
        ret = unicode(soup)

        # Preserve the spaces and line breaks in <pre> tags
        pattern = re.compile(ur'(?musi)<pre>(.*?)</pre>')
        pos = 1
        while True:
            m = pattern.search(ret, pos - 1)
            if not m: break
            
            replacement = '#CR#```#CR#%s#CR#```#CR#' % m.group(1).replace('\n', '#CR#').replace(' ', '#SPACE#') 
            ret = ret[:m.start(0)] + replacement + ret[m.end(0):]
            pos = m.start(0) + len(replacement)
        
        # strip all unnecessary spaces
        #ret = re.sub(ur'(?musi)>\s+', ur'>', ret)
        #ret = re.sub(ur'(?musi)\s+<', ur'<', ret)
        ret = re.sub(ur'\s+', ur' ', ret)

        # convert <hx> to #
        for i in range(1, 5):
            ret = re.sub(ur'<h%s>(.*?)</h%s>' % (i, i), ur'\n%s \1\n' % ('#' * i,), ret)
        
        # convert <p> to paragraphs
        ret = re.sub(ur'(?musi)<p>(.*?)</p>\s*', ur'\1\n\n', ret)
        
        # convert strike-through
        ret = re.sub(ur'(?musi)<s>(.*?)</s>', ur'~~\1~~', ret)

        # convert italics
        ret = re.sub(ur'(?musi)<em>(.*?)</em>', ur'_\1_', ret)

        # convert <strong>
        ret = re.sub(ur'(?musi)<strong>(.*?)</strong>', ur'**\1**', ret)
        
        # convert <a href="">
        #ret = re.sub(ur'(?musi)<a>(.*?)</a>', ur'[]()', ret)
        pattern = re.compile(ur'(?musi)<a.*?href="([^"]*)".*?>(.*?)</a>')
        pos = 1
        while True:
            m = pattern.search(ret, pos - 1)
            if not m: break
            
            # if this is a link to a confluence page, convert it to a local link
            href = self.get_local_doc_url(m.group(1))
            
            replacement = '[%s](%s)' % (m.group(2), href) 
            ret = ret[:m.start(0)] + replacement + ret[m.end(0):]
            pos = m.start(0) + len(replacement)

        # convert <blockquote>
        #ret = re.sub(ur'(?musi)<blockquote>\s*(.*?)\s*</blockquote>', ur'\n> \1\n', ret)
        pattern = re.compile(ur'(?musi)<blockquote>\s*(.*?)\s*</blockquote>')
        pos = 1
        while True:
            m = pattern.search(ret, pos - 1)
            if not m: break
            
            replacement = '%s\n\n' % re.sub(ur'(?musi)^\s*', ur'> ', m.group(1)) 
            ret = ret[:m.start(0)] + replacement + ret[m.end(0):]
            pos = m.start(0) + len(replacement)

        # convert <pre>
        #ret = re.sub(ur'(?musi)<pre>\s*(.*?)\s*</pre>', ur'\n```\n\1\n```\n', ret)

        # add line break before bullet points
        ret = re.sub(ur'\s*<li>', ur'\n', ret)
        # add line break after block of bullet points
        # (only if not nested into another block) 
        ret = re.sub(ur'\s*</ul>(?!\s*</li>)', ur'\n', ret)

        ret = re.sub(ur'#SPACE#', ur' ', ret)
        ret = re.sub(ur'#CR#', ur'\n', ret)
        
        # remove remaining tags
        ret = re.sub(ur'<[^>]*>', ur' ', ret)

        print ret.encode('utf8', 'ignore')

    def get_local_doc_url(self, href):
        '''Returns the url of a local MD with the same name as in href.
            Returns href if not found.
        '''
        import digipal
        
        ret = href
        if 'confluence.dighum' in href.lower():
            file_name = href
            file_name = re.sub(ur'[#?].*$', '', file_name).strip('/')
            file_name = re.sub(ur'^.*/', '', file_name).lower()
            start_path = os.path.abspath(os.path.join(digipal.__path__[0], 'doc'))
            for root, dirs, files in os.walk(start_path):
                for file in files: 
                    if re.sub(ur'.md$', '', file).lower() == file_name:
                        ret = os.path.join(root, file).replace('\\', '/')
                        ret = '/doc/digipal/%s' % ret[len(start_path):].strip('/')
                        break
        return ret
    