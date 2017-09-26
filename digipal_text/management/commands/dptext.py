# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from mezzanine.conf import settings
import re
from digipal import utils as dputils
from optparse import make_option
from digipal.utils import re_sub_fct, get_int
from digipal_text.models import TextContentXML
from lib2to3.pgen2.tokenize import tabsize

# Apply project specific patches
try:
    # TODO: SHOULD NOT be here! design a better way to import custom models
    from exon.customisations.digipal_text import models
except Exception, e:
    pass

class Command(BaseCommand):
    help = """
Digipal Text management tool.

Commands:

  download  CONTENT_XML_ID [UNITID]

  copies    [IP_ID]
            List copies of the texts.

  restore   COPY_ID
            restore a copy

  markup    CONTENT_XML_ID
            auto-markup a content

  upload    XML_PATH IP_ID CONTENT_TYPE [XPATH]
            upload a XML file into the database
            e.g. upload 'mytext.xml' 13 'transcription'

  process   OPERATION IP_ID CONTENT_TYPE [OPTIONS]
            Transform a content.
            OPERATION =
                pb2locus    convert pb to locus
                    OPTIONS = START_NUMBER

  unit      [CTXID [LOCATION_TYPE [LOCATION]]]
            List the units from a text
            e.g. unit 1 entry 104b1

  fixids
            See MOA-247 + 260: convert the wrong markup ids
            to the correct ones. For all texts.

  stats CONTENT_TYPE
            Returns number of XML tags and attributes used in all the text of type
            CONTENT_TYPE (e.g. translation)
            
  autoconvert [--dry-run]
            Auto markup of all the texts, PLEASE TEST CAREFULLY before running.
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

        if command == 'autoconvert':
            known_command = True
            self.command_autoconvert()

        if command == 'list':
            known_command = True
            self.command_list()

        if command == 'copies':
            known_command = True
            self.command_copies()

        if command == 'restore':
            known_command = True
            self.command_restore()

        if command == 'unit':
            known_command = True
            self.command_unit()

        if command == 'markup':
            known_command = True
            self.command_markup()

        if command == 'upload':
            known_command = True
            self.command_upload()

        if command == 'download':
            known_command = True
            self.command_download()

        if command == 'process':
            known_command = True
            self.command_process()

        if command == 'clauses':
            known_command = True
            self.command_clauses()

        if command == 'fixids':
            known_command = True
            self.command_fixids()

        if command == 'search':
            known_command = True
            self.command_search()

        if command == 'stats':
            known_command = True
            self.command_stats()

#         if self.is_dry_run():
#             self.log('Nothing actually written (remove --dry-run option for permanent changes).', 1)

        if not known_command:
            print self.help
        else:
            print 'done'

    def command_autoconvert(self):
        dry = self.is_dry_run()
        
        from digipal_text.models import TextContentXML, TextAnnotation
        from digipal_text.views import viewer
        before = ur''
        after = ur''
        total = 0
        converted = 0
        for tcx in TextContentXML.objects.filter(text_content__type__slug='transcription').order_by('id'):
            total += 1
            content = tcx.content
            if not content: continue
            tcx.convert()
            if content != tcx.content:
                converted += 1
                text_name = u'#%s: %s [length diff = %s]' % (tcx.id, tcx, abs(len(content) - len(tcx.content)))
                print text_name
                
                before += u'\n\n'
                before += text_name
                before += u'\n\n'
                before += content.replace('\r', '\n')
                
                after += u'\n\n'
                after += text_name
                after += u'\n\n'
                after += tcx.content.replace('\r', '\n')

                if 0:
                    html = ''
                    from difflib import HtmlDiff
                    diff = HtmlDiff(tabsize=2)
                    d = diff.make_table([content], [tcx.content])
                    
                    html += u'<h2>%s</h2>' % text_name
                    html += d
                    
                if not dry:
                    tcx.save()
 
                #break
                
            #tcx.save()
        
        dputils.write_file('before.txt', before)
        dputils.write_file('after.txt', after)
        
        print '%s converted out of %s texts' % (converted, total)
        
        if dry:
            print 'DRY RUN: no data was changed in the database.'

    def command_fixids(self):
        from digipal_text.models import TextContentXML, TextAnnotation
        from digipal_text.views import viewer
        for tcx in TextContentXML.objects.filter(text_content__type__slug='transcription').order_by('id'):
            # if tcx.text_content.item_part_id != 598: continue

            '''
            Before
            [[(u'', u'clause'), (u'type', u'address'), ['@text', u'walt']], [(u'', u'clause'), (u'type', u'salutation'), ['@text', u'salutem']], [(u'', u'clause'), (u'type', u'disposition')], [(u'', u'clause'), (u'type', u'witnesses')]]
            After
            [[(u'', u'clause'), (u'type', u'address'), ['@text', u'walt']], [(u'', u'clause'), (u'type', u'salutation'), ['@text', u'salutem']], [(u'', u'clause'), (u'type', u'disposition')], [(u'', u'clause'), (u'type', u'witnesses')]]
            '''

            content = tcx.content
            if not content or len(content) < 5: continue
            print 'TA #%s IP #%s' % (tcx.id, tcx.text_content.item_part.id)
            import json

            elementss = []
            # elementss.append([json.dumps(aid[0]) for aid in viewer.get_text_elements_from_content_bugged(content)])
            elementss.append([json.dumps(aid[0]) for aid in viewer.get_text_elements_from_content(content)])

            if len(elementss[0]) != len(elementss[1]):
                print '\tWARNING: Different number of elements!'

            for i in range(len(elementss[0])):
                if elementss[0][i] != elementss[1][i]:
                    pass
                    # print u'\t%s <> %s' % (elementss[0][i], elementss[1][i])

            # get elements from TI annotation
            tas = TextAnnotation.objects.filter(annotation__image__item_part_id=tcx.text_content.item_part_id)
            for ta in tas:
                i = -1
                if ta.elementid in elementss[0]:
                    i = elementss[0].index(ta.elementid)
                if i < 0:
                    print '\tWARNING: Annotation id not found in text (%s)' % ta.elementid
                    if ta.elementid in elementss[1]:
                        print '\tINFO: Found in new ids'
                        i = elementss[1].index(ta.elementid)
                    else:
                        i = len(elementss[0])
                        while i > 0:
                            i -= 1
                            if elementss[0][i].startswith(ta.elementid[:-1]):
                                print '\tINFO: Partial match (%s)' % elementss[0][i]
                                break
                if i >= 0:
                    newid = elementss[1][i]
                    if newid != ta.elementid:
                        print '\tCONVERT %s -> %s' % (ta.elementid, elementss[1][i])
                        ta.elementid = elementss[1][i]
                        ta.save()
                else:
                    print '\tERROR: Annotation id not found in text (%s)' % ta.elementid


    def get_textcontentxml(self, ip_id, content_type_name):
        from django.utils.text import slugify
        from digipal_text.models import TextContentType, TextContent, TextContentXML
        content_type = TextContentType.objects.filter(slug=slugify(unicode(content_type_name))).first()
        if not content_type:
            print 'Content Type "%s" not found' % content_type_name
            return None
        tc, created = TextContent.objects.get_or_create(item_part__id=ip_id, type=content_type)
        tcx, created = TextContentXML.objects.get_or_create(text_content=tc)
        return tcx

    def command_download(self):
        ret = ur''

        recordid = self.args[1]
        unitid = ''
        if len(self.args) > 2: unitid = self.args[2]
        from digipal_text.models import TextContentXML
        from digipal_text.views.viewer import get_fragment_extent, get_all_units
        text_content_xml = TextContentXML.objects.get(id=recordid)
        content = text_content_xml.content
        

        suffix = ''
        if unitid:
            suffix = '-unit'
            units = get_all_units(content, 'entry')
            for unit in units:
                if unit['unitid'] == unitid:
                    ret = ur'<root>%s</root>' % unit['content']
        else:
            ret = content

        import regex

        if ret is None:
            ret = u''

        # print repr(ret)
        file_name = 'tcx%s%s.xml' % (text_content_xml.id, suffix)
        from digipal.utils import write_file
        write_file(file_name, ret)
        print 'Written file %s ' % file_name

    def command_search(self):
        if len(self.args) < 3:
            raise CommandError('Convert requires 2 arguments')

        from digipal.management.commands.utils import get_stats_from_xml_string
        from digipal_text.views.viewer import get_fragment_extent, get_all_units

        pattern = unicode(self.args[3])
        #pattern = ur'.{1,30}ħ.{1,30}'
        pattern = ur'(?musi)#MSTART#(.*?)#MEND#'

        stats = {}
        cnt = 0
        import regex as re
        all_entries = []
        for tcx in TextContentXML.objects.filter(text_content__item_part_id=self.args[1], text_content__type__slug=self.args[2]):
            if 1:
                for match in re.findall(pattern, tcx.content):
                    cnt += 1
                    if len(re.findall(ur'<p>', match)) > 1:
                        print '>1'
                    entries = re.findall(ur'"entry">(.*?)<', match)
                    if entries:
                        all_entries.extend(entries)
            if 0:
                units = get_all_units(tcx.content, 'entry')
                for unit in units:
                    for match in re.findall(pattern, unit['content']):
                        #print unit['unitid'], repr(match)
                        #print repr(match)
                        #print re.findall(ur'<p>', match)
                        cnt += 1
        
        print ','.join(all_entries)
        
        print '%s occurences' % cnt

    def command_stats(self):
        if len(self.args) < 2:
            raise CommandError('Convert requires 1 arguments')

        from digipal.management.commands.utils import get_stats_from_xml_string

        stats = {}
        for tcx in TextContentXML.objects.filter(text_content__type__slug=self.args[1]):
            xml_string = tcx.content
            if xml_string:
                get_stats_from_xml_string(xml_string, 'TCX #%s (IP #%s)' % (tcx.id, tcx.text_content.item_part_id), stats)
            #break

        for tag in sorted(stats.keys()):
            print '%10d [%s] %s' % (stats[tag]['count'], tag, stats[tag]['text'])


    def command_upload(self):
        '''upload    XML_PATH IP_ID CONTENT_TYPE [XPATH]
            pm dptext upload exon\source\rekeyed\converted\EXON-1-493.xhtml 1 transcription
        '''
        if len(self.args) < 4:
            print 'upload requires 3 arguments'
            return

        xml_path, ip_id, content_type_name = self.args[1:4]

        xpath = None
        if len(self.args) > 4:
            xpath = self.args[4]

        # I find the TextContentXML record (or create it)
        tcx = self.get_textcontentxml(ip_id, content_type_name)
        if not tcx:
            print 'ERROR: could not find record (%s, %s)' % (ip_id, content_type_name)
            return

        # II load the file and convert it
        from digipal.utils import read_file, get_xml_from_unicode
        xml_string = read_file(xml_path)

        # III get the XML into a string
        if xpath:
            xml = get_xml_from_unicode(xml_string, add_root=True)
            els = xml.xpath(xpath)
            if len(els) > 0:
                root = els[0]
            else:
                raise Exception(u'No match for XPATH "%s"' % xpath)
            from lxml import etree
            #content = etree.tostring(root, encoding="UTF-8")
            content = dputils.get_unicode_from_xml(etree, remove_root=True)
        else:
            content = xml_string
#         print type(root)
#         print dir(root)
#         content = str(root)

        if '&#361;' in content:
            print 'Numeric entity'
            exit()

        # IV convert the xml tags and attribute to HTML-TEI
        # content = self.get_xhtml_from_xml(content)

        # save the content into the TextContentXML record
        tcx.content = content
        tcx.save()

        from django.template.defaultfilters import filesizeformat
        print 'Uploaded %s into record #%s' % (filesizeformat(tcx.get_length()), tcx.id)


    def get_xhtml_from_xml(self, xml_string):
        # IV convert the xml tags and attribute to HTML-TEI

        # remove comments
        content = re.sub(ur'(?musi)<!--.*?-->', ur'', xml_string)
        #
        self.c = 0
        self.conversion_cache = {}

        def replace_tag(match):
            if match.group(0) in self.conversion_cache:
                return self.conversion_cache[match.group(0)]

            self.c += 1
            if self.c > 10e6:
                exit()

            ret = match.group(0)

            tag = match.group(2)

            # don't convert <p>
            if tag in ['p', 'span']:
                return ret

            # any closing tag is /span
            if '/' in match.group(1):
                return '</span>'

            if tag == 'pb':
                print self.c

            # tag -
            ret = ur'<span data-dpt="%s"' % tag
            # attribute - assumes " for attribute values
            attrs = (re.sub(ur'(?ui)(\w+)(\s*=\s*")', ur'data-dpt-\1\2', match.group(3))).strip()
            if attrs:
                ret += ' ' + attrs
            ret += match.group(4)

            # print '', ret

            self.conversion_cache[match.group(0)] = ret

            return ret

        from digipal.utils import re_sub_fct
        content = re_sub_fct(content, ur'(?musi)(<\s*/?\s*)(\w+)([^>]*?)(/?\s*>)', replace_tag)

        return content

    def get_arg(self, i, default=None):
        if len(self.args) > i:
            return self.args[i]
        else:
            return default

    def command_unit(self):
        # from digipal_text.models import TextUnit
        # rs = TextUnit.objects
        from digipal_text.models import TextContentXML
        from digipal_text.views.viewer import get_fragment_extent, get_all_units
        rid = self.get_arg(1)
        fitler = {}
        if rid:
            fitler = {'id': rid}
        ctx = TextContentXML.objects.filter(**fitler).first()

        cnt = 0

        if ctx:
            print ctx
            location_type = self.get_arg(2, 'locus')

            location = self.get_arg(3, None)
            units = get_all_units(ctx.content, location_type)
            
            for unit in units:
                if location is None or dputils.is_unit_in_range(unit['unitid'], location):
                    cnt += 1
                    print '%-10s %-5s %-10s' % (unit['unitid'], len(unit['content']), repr(unit['content'][:10]))
                    if location:
                        print repr(unit['content'])

            print '%s units' % cnt
            # fragment = get_fragment_extent(ctx.content, self.args[2], self.args[3])

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
        # call the auto-markup function on a text
        from digipal_text.models import TextContentXML
        if len(self.args) > 1:
            content_xml = TextContentXML.objects.filter(id=self.args[1]).first()
            if content_xml:
                print self.get_content_xml_summary(content_xml)

                versions = [content_xml.content]

                content_xml.convert()

                # versions.append(content_xml.content)

                # print repr(content_xml.content)

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

    def command_process(self):
        if len(self.args) < 4:
            print 'upload requires 3 arguments'
            return

        operation, ip_id, content_type_name = self.args[1:4]

        options = []
        if len(self.args) > 4:
            options = self.args[4:]

        # I find the TextContentXML record (or create it)
        tcx = self.get_textcontentxml(ip_id, content_type_name)
        if not tcx:
            return

        content = tcx.content

        len0 = len(content)

        if operation == 'pb2locus':
            content = self.operation_pb2locus(options, content)

        if operation == 'foliate':
            content = self.operation_foliate(options, content)

        if operation == 'addentries':
            content = self.operation_addentries(options, content)

        if content and len(content) != len0:
            tcx.content = content
            print repr(content)
            content = tcx.save()
            print 'Saved new content'
        else:
            print 'Nothing done. Did you call the right operation?'

    def operation_addentries(self, options, content):
        first, last = options[0].split('..')

        content = u'';

        for i in range(int(first), int(last)):
            for s in ['r', 'v']:
                content += u'<p><span data-dpt="location" data-dpt-loctype="locus">%s%s</span></p>\n\n' % (i, s)

        return content

    def operation_foliate(self, options, content):
        '''
            <span data-dpt="margin">fol. 1. b</span>[...]

            =>

            <p><span data-dpt="location" data-dpt-loctype="locus">1v</span><p>
        '''
        self._next_locus = u'1r'

        def replace(match):
            ret = match.group(0)

            locus = match.group(1)

            parts = re.match(ur'(?musi)^\s?(\d+)\.?\s*(b?)\.?$', locus)
            if not parts:
                print 'WARNING: no match [%s]' % repr(locus)
            else:
                lo = parts.group(1)
                lon = lo
                if parts.group(2) == 'b':
                    lon = u'%sr' % (int(lo) + 1,)
                    lo += 'v'
                else:
                    lon = lo + 'v'
                    lo += 'r'

                print '%s ("%s")' % (lo, locus)

                if lo != self._next_locus:
                    print 'WARNING: locus out of sequence, expected %s, got %s' % (self._next_locus, lo)

                self._next_locus = lon

                ret = u'</p><p><span data-dpt="location" data-dpt-loctype="locus">%s</span></p><p>' % lo

            return ret

        content = re_sub_fct(content, ur'(?musi)<span data-dpt="margin">\s*fol.([^<]*)</span>', replace)

        return content

    def operation_pb2locus(self, options, content):
        start_page = 1
        if options:
            start_page = int(options[0])

        self.rep_option = start_page
        def replace(match):
            # !!! ASSUME pb is not in <p> or anything else

            number = re.sub(ur'^.*"([^"]+)".*$', ur'\1', match.group(1))
            if len(number) == len(match.group(1)):
                number = self.rep_option

            ret = u'<p><span data-dpt="location" data-dpt-loctype="locus">%s</span></p>' % number

            self.rep_option = get_int(number, default=self.rep_option) + 1

            return ret

        content = re_sub_fct(content, ur'<span\s+data-dpt\s*=\s*"pb"([^>]*)>', replace)

        return content

    def is_dry_run(self):
        return self.options.get('dry-run', False)

