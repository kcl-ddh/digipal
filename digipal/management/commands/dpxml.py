# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from mezzanine.conf import settings
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

  convert PATH_TO_XML PATH_TO_XSLT [OUTPUT_PATH]

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
        from utils import get_stats_from_xml_string
        stats = get_stats_from_xml_string(xml_string)

        print repr(stats)

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
        out_file = self.cargs[3] if len(self.cargs) > 3 else None 

        xml_string = utils.readFile(xml_path)
        xml_string = re.sub(ur'\bxmlns=', ur'xmlns2=', xml_string)

        # TODO: remove this hack, only for odt conversion
        # position 33% is like 'super' style
        xml_string = re.sub(ur'"-33%', ur'"sub', xml_string)
        xml_string = re.sub(ur'"33%', ur'"super', xml_string)

        xslt_string = utils.readFile(xslt_path)

        # replacements in the XSLT
        comments, xslt_string = self.parse_xslt_directives(xslt_string, xml_string)

        ret = str(dputils.get_xslt_transform(xml_string, xslt_string))

        if out_file:
            dputils.write_file(out_file, str(comments) + ret, encoding=None)
        else:
            print str(comments) + ret

        return ret

    def parse_xslt_directives(self, xslt_string, xml_string):
        '''
            Substitute some of our own directives in the XSLT string
            E.g. {% class super %} => @class='T1' or @class='T2' or @class='T6'
        '''

        import regex
        
        meta = {'comments': []}

        classes_used = {}

        def repl(match):
            comments = meta['comments']
            # e.g. match.group(0) = {% style italic text-line-through-type="double" %}
            unknown = True
            directive = match.group(1)
            ret = match.group(0)
            parts = [p.strip() for p in directive.split(' ') if p.strip()]
            if parts:
                if parts[0] == 'style':
                    unknown = False

                    classes_intersection = None
                    for term in parts[1:]:
                        # e.g. term = 'italic'
                        # e.g. term = 'text-line-through-type="double"'
                        classes = []
                        # Find the name of the styles that contains <term> (e.g. super).
                        # <style:style style:name="T3" style:family="text">
                        #     <style:text-properties
                        #         style:text-position="super 58%" />
                        # </style:style>
                        #
                        # => T3
                        for style in regex.findall(ur'(?musi)<style:style style:name="(.*?)"[^>]*>(.*?)</style:style>', xml_string):
                            if term in style[1]:
                                classes.append(style[0])

                        if not classes:
                            comments.append('<!-- WARNING:: style not found %s -->' % term)

                        if classes_intersection is None:
                            classes_intersection = classes
                        else:
                            # only keep the classes/styles that contains all keywords (AND)
                            classes_intersection = set(classes).intersection(set(classes_intersection))

                    # now remove styles which we have already used
                    already_used_warning = set(classes_intersection).intersection(set(classes_used.keys()))
                    if already_used_warning:
                        comments.append('<!-- INFO: Already used classes/styles: %s (see above) -->' % ', '.join(list(already_used_warning)))
                    classes_intersection = set(classes_intersection).difference(set(classes_used.keys()))
                    
                    if classes_intersection:
                        # Generate the XPATH (e.g. @text:style-name='T3' or @text:style-name='T6')
                        ret = ' or '.join([ur"@text:style-name='%s'" % cls for cls in classes_intersection])
                        # update the classes_used
                        for cls in classes_intersection:
                            classes_used[cls] = 1
                        comments.append('<!-- %s => %s -->' % (' '.join(parts), ret))
                    else:
                        ret = 'NOTFOUND'
                        comments.append('<!-- WARNING: styles not found together: %s -->' % ' '.join(parts[1:]))

            if unknown:
                raise Exception('ERROR: unknown directive "%s"' % match.group(0))

            return ret

        ret = regex.sub(ur'\{%(.*?)%\}', repl, xslt_string)

        return '\n'.join(meta['comments']), ret

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

        return ret


