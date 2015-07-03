# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import re
from optparse import make_option

# pm dpxml convert exon\source\rekeyed\converted\EXON-1-493-part1.xml exon\source\rekeyed\conversion\xml2word.xslt > exon\source\rekeyed\word\EXON-word.html
# pm extxt wordpre exon\source\rekeyed\word\EXON-word.html exon\source\rekeyed\word\EXON-word2.html
# pandoc "exon\source\rekeyed\word\EXON-word2.html" -o "exon\source\rekeyed\word\EXON-word.docx"

class Command(BaseCommand):
    help = """
Text conversion tool
    
Commands:
    wordpre PATH_TO_XHTML OUTPUT_PATH
        Preprocess the MS Word document

"""
    
    args = 'locus|email'
    option_list = BaseCommand.option_list + (
        make_option('--db',
            action='store',
            dest='db',
            default='default',
            help='Name of the target database configuration (\'default\' if unspecified)'),
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
            print self.help
            exit()
        
        command = args[0]
        self.cargs = args[1:]
        
        known_command = False

        if command == 'wordpre':
            known_command = True
            self.word_preprocess()
        
        if known_command:
            print 'done'
            pass
        else:
            print self.help

    def get_unique_matches(self, pattern, content):
        ret = []
        
        ret = re.findall(pattern, content)
        print pattern, len(ret)
        print list(set(ret))
        
        return ret

    def word_preprocess(self):
        input_path = self.cargs[0]
        output_path = self.cargs[1]
        
        from digipal.utils import write_file, read_file
        
        content = read_file(input_path)
        
        # expansions
        # m_0 -> m[od]o_0
        #self.get_unique_matches(pattern, content)
        pattern = ur'(?mus)([^\w<>\[\]])(m<sup>0</sup>)([^\w<>\[\]])'
        content = re.sub(pattern, ur'\1m[od]o<sup>o</sup>\3', content)

        pattern = ur'(?mus)([^\w<>\[\]])(uocat<sup>r</sup>)([^\w<>\[\]])'
        content = re.sub(pattern, ur'\1uocat[u]r<sup>r</sup>\3', content)

        pattern = ur'(?mus)([^\w<>\[\]])(q<sup>1</sup>)([^\w<>\[])'
        content = re.sub(pattern, ur'\1q[u]i<sup>i</sup>\3', content)

        # numbers
        pattern = ur'(?mus)\.?(\s*)(\b[IVXl]+)\.([^\w<>\[\]])'
        content = re.sub(pattern, lambda pat: ur'%s.%s.%s' % (pat.group(1), pat.group(2).lower(), pat.group(3)), content)

        # write result
        write_file(output_path, content)
        
