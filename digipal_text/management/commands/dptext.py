from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import re
from optparse import make_option
from digipal.utils import re_sub_fct, get_int

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
            
  upload    XML_PATH IP_ID CONTENT_TYPE [XPATH]
            upload a XML file into the database
            e.g. upload 'mytext.xml' 13 'transcription'

  process   OPERATION IP_ID CONTENT_TYPE [OPTIONS]
            Transform a content.
            OPERATION =
                pb2locus    convert pb to locus
                    OPTIONS = START_NUMBER
                    
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

        if command == 'upload':
            known_command = True
            self.command_upload()
            
        if command == 'process':
            known_command = True
            self.command_process()

#         if self.is_dry_run():
#             self.log('Nothing actually written (remove --dry-run option for permanent changes).', 1)
            
        if not known_command:
            print self.help
        else:
            print 'done'

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
            return

        # II load the file and convert it
        from digipal.utils import read_file, get_xml_from_unicode
        xml_string = read_file(xml_path)
        
        # III get the XML into a string
        xml = get_xml_from_unicode(xml_string)
        if xpath:
            els = xml.xpath(xpath)
            if len(els) > 0:
                root = els[0]
            else:
                raise Exception(u'No match for XPATH "%s"' % xpath)
        else:
            root = xml.getroot()
        from lxml import etree
        content = etree.tostring(root, encoding="UTF-8")
#         print type(root)
#         print dir(root)
#         content = str(root)
        
        if '&#361;' in content:
            print 'Numeric entity'
            exit()
        
        # don't keep root element tag
        content = re.sub(ur'(?musi)^.*?>(.*)<.*?$', ur'\1', content)
        
        # IV convert the xml tags and attribute to HTML-TEI
        #content = self.get_xhtml_from_xml(content)
        
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
            
            #print '', ret
            
            self.conversion_cache[match.group(0)] = ret
            
            return ret
            
        from digipal.utils import re_sub_fct
        content = re_sub_fct(content, ur'(?musi)(<\s*/?\s*)(\w+)([^>]*?)(/?\s*>)', replace_tag)
        
        return content
        
        
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
        # call the auto-markup function on a text
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
                    lon = u'%sr' % (int(lo)+1, )
                    lo += 'v'
                else:
                    lon = lo+'v'
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
        
        
