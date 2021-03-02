# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from dpbase import DPBaseCommand
from mezzanine.conf import settings
from os.path import isdir
import os
import sys
import shlex
import subprocess
import re
from optparse import make_option
from django.db import IntegrityError
from digipal.models import *
from digipal.utils import natural_sort_key
from digipal.templatetags.hand_filters import chrono
from django.template.defaultfilters import slugify
from time import sleep


class Command(DPBaseCommand):
    help = """
Digipal blog management tool.

Commands:

    locus

    email

    validate

    record_path
        Test the field extraction from record + path used by the faceted search module
        e.g. record_path manuscripts historical_item.historical_item_type.name 598

    dateconv [hi [HI_ID]]
        reports datse which cannot be parsed correctly
        if hi: check hi.get_date_sort() otherwise check dateevidence.date

    max_date_range FIELD
        e.g. max_date_range HistoricalItem.date
        returns the minimum and maximum of the date values among all HistoricalItem records

    date_prob
        report all HI dates with a very wide range (unrecognised, or open ended range)

    cs
        TODO
        collect static

    cpip REQ1 REQ2
        compare two PIP req files (pip freeze)

    download_images URL
        URL: e.g. "http://domain/path/to/image_{001_r,003_v}.jpg"

    unstatic
        Opposite of collectstatics
        It removes the copies of the assets
        This is only for dev env. when you are changing the js/css, ...
        Note that transpiled code can't be made dynamic (e.g. less, ts)

    jsdates
        test date conversion during json parsing
"""

    args = 'locus|email'
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

        if len(args) < 1:
            raise CommandError(
                'Please provide a command. Try "python manage.py help dpmigrate" for help.')
        command = args[0]

        known_command = False

        if command == 'test_admin':
            '''
            Send web request to all admin change list, add, and change_form pages
            Usage: DJANGO_SITE_ROOT_URL DJANGO_SESSIONID
            Example: http://localhost:8080 6o436pngqgpjg0bqd46fhge3a458t92x
            '''
            known_command = True

            if len(args) < 3:
                print 'Please provide a root URL, e.g. http://localhost:8080'
                print 'And a sesion id, e.g. 6o436pngqgpjg0bqd46fhge3a458t92x'
                exit()

            root_url = args[1]
            sessionid = args[2]

            from django.contrib import admin
            from django.core import urlresolvers
            from utils import web_fetch
            for amodel, aadmin in admin.site._registry.iteritems():
                print amodel, aadmin

                obj = amodel.objects.first()

                url_part = '%s_%s' % (amodel._meta.app_label,
                                      amodel._meta.model_name)

                urls = [
                    urlresolvers.reverse('admin:%s_add' % url_part),
                    urlresolvers.reverse('admin:%s_changelist' % url_part)
                ]
                if obj:
                    urls.append(urlresolvers.reverse(
                        'admin:%s_change' % url_part, args=(obj.pk,)))

                for url in urls:
                    url = root_url + url
                    res = web_fetch(url, sessionid=sessionid, noredirect=True)
                    if res['status'] != '200':
                        print 'WARNING: %s code returned by %s' % (res['status'], url)

        if command == 'hd':
            # 8546 </c> [1145, 1145, 1145, 1231, 1231, 1231, 1231, 1231, 1231, 1231]
            # 894 </foreign> [1145, 1231, 1231, 1225, 1225, 1225, 1225, 1225, 1225, 1225]
            # 13 </hi> [1226, 1226, 1226, 1226, 1226, 1226, 1226, 1226, 1226, 598]
            # 38 </note> [1227, 548, 13, 18, 21, 598, 604, 619, 621, 659]
            # 39 </title> [1227, 1227, 548, 13, 18, 21, 598, 604, 619, 619]
            # 2 <c/> [875, 408]
            # 8546 <c> [1145, 1145, 1145, 1231, 1231, 1231, 1231, 1231, 1231, 1231]
            # 894 <foreign> [1145, 1231, 1231, 1225, 1225, 1225, 1225, 1225, 1225, 1225]
            # 1 <hi rend="smallcap" > [1226]
            # 8 <hi rend="smallcap"> [1226, 1226, 1226, 1226, 1226, 1226, 1226, 1226]
            # 2 <hi rend="sup"> [598, 736]
            # 2 <hi> [853, 853]
            # 1 <note place="bottom" n="1"> [331]
            # 1 <note place="bottom" n="15"> [777]
            # 3 <note place="bottom" n="16"> [817, 1065, 1188]
            # 3 <title level="m" > [659, 887, 336]
            # 36 <title level="m"> [1227, 1227, 548, 13, 18, 21, 598, 604, 619,
            # 619]

            els = {}

            # hand description element list
            from digipal.models import HandDescription
            for hd in HandDescription.objects.all():
                desc = hd.description
                if desc and len(desc) > 0:
                    # print hd.id, len(desc)
                    for el in re.findall(ur'(?ui)<[^>]+>', desc):
                        v = els.get(el, [])
                        v.append(hd.hand.id)
                        els[el] = v

            for el in sorted(els.keys()):
                print len(els[el]), el, els[el][0:10]

        if command == 'record_path':
            known_command = True
            self.record_path(*args[1:])

        if command == 'download_images':
            known_command = True
            self.download_images(*args[1:])

        if command == 'jsdates':
            known_command = True
            d = {
                'd': {
                    'd1': 'v1',
                    'd2': '2016-10-28T13:27:38.944298+00:00',
                },
                'l': ['v1', '2016-10-28T13:27:38.944298+00:00'],
            }
            print repr(d)
            ds = dputils.json_dumps(d)
            print repr(ds)
            d2 = dputils.json_loads(ds)
            print repr(d2)

        if command == 'mem':
            known_command = True
            self.test_mem(*args[1:])

        if command == 'cmp_locus':
            known_command = True
            from digipal import utils as dputils

            cases = [
                ['1r', '2r', -1],
                ['2r', '1r', 1],
                ['1r', '1r', 0],
                ['1r', '1v', -1],
                ['1v', '2r', -1],
                ['15r', '2r', 1],
                ['15r', '20r', -1],
                ['235r', '235br', -1],
                ['235v', '235br', -1],
                ['235br', '235bv', -1],
                ['235br', '236r', -1],
            ]

            fail_count = 0
            for case in cases:
                res = dputils.cmp_locus(case[0], case[1])
                if res != case[2]:
                    fail_count += 1
                    print 'FAILED: %s, got %s' % (repr(case), res)

            print '%s / %s' % (len(cases) - fail_count, len(cases))

        if command == 'get_locuses':
            from digipal.models import Image
            existing_locations = dputils.sorted_natural(Image.objects.filter(
                item_part__display_label__icontains='ex').values_list('locus', flat=1), 0, 1)
            print '\n'.join(existing_locations)

        if command == 'date_prob':
            known_command = True
            self.date_prob(*args[1:])

        if command == 'multivalued':
            known_command = True
            self.multivalued(*args[1:])

        if command == 'cpip':
            known_command = True
            self.cpip(*args[1:])

        if command == 'unstatic':
            known_command = True
            self.unstatic()

        if command == 'chd':
            # convert hand desc from xml to html
            from digipal.models import HandDescription
            from digipal.utils import convert_xml_to_html
            for hd in HandDescription.objects.all():
                # if hd.hand.id != 1226: continue
                print '-' * 80
                print hd.id, hd.hand.id
                print repr(hd.description)
                print '- ' * 40
                hd.description = convert_xml_to_html(hd.description)
                hd.save()
                print repr(hd.description)

        if command == 'stint':
            from digipal.utils import expand_folio_range
            cases = [
                    ['140r20-1v2', ['140r', '140v', '141r', '141v']],
                    ['149v20-50v2', ['149v', '150r', '150v']],
                    ['149v20-51r2', ['149v', '150r', '150v', '151r']],
                    ['277r1-8', ['277r']],
                    ['277v1', ['277v']],
            ]
            for case in cases:
                result = expand_folio_range(case[0])
                if ';'.join(result) != ';'.join(case[1]):
                    print '[FAIL] %s' % case[0]
                    print '\t got : %s' % result
                    print '\t want: %s' % case[1]
                else:
                    print '[PASS] %s' % case[0]

        if command == 'max_date_range':
            known_command = True
            self.max_date_range(args[1])

        if command == 'locus':
            known_command = True
            self.test_locus(options)

        if command == 'natsort':
            known_command = True
            self.test_natsort(options)

        if command == 'email':
            known_command = True
            self.test_email(options)

        if command == 'rename_images':
            known_command = True
            self.rename_images(args[1])

        if command == 'img_info':
            known_command = True
            self.img_info(args[1])

        if command == 'img_compare':
            known_command = True
            self.img_compare(args[1], args[2])

        if command == 'adjust_offsets':
            self.adjust_offsets(args[1], args[2])

        if command == 'correct_annotations':
            known_command = True
            self.correct_annotations(args[1])

        if command == 'validate':
            known_command = True
            self.fetch_and_test(*args[1:])

        if command == 'catnum':
            known_command = True
            self.catnum(*args[1:])

        if command == 'autocomplete':
            known_command = True
            self.autocomplete(*args[1:])

        if command == 'dupim':
            known_command = True
            self.find_dup_im(*args[1:])

        if command == 'find_offset':
            known_command = True
            self.find_image_offset(*args[1:])

        if command == 'dateconv':
            known_command = True
            self.date_conv(*args[1:])

        if command == 'sources':
            known_command = True
            self.test_sources(*args[1:])

        if command == 'recim':
            known_command = True
            self.reconstruct_image(*args[1:])

        if command == 'race':
            known_command = True
            self.race(*args[1:])

        if command == 'img_size':
            known_command = True
            from digipal.models import Image
            print '0'
            #im0 = Image()
            # im0.save()
            print '1'
            im = Image.objects.get(id=400)
            im.iipimage = 'jp2/admin-upload/e/ebcf3583-dd40-431f-8327-92d6f7c1822b.jp2'
            print im.dimensions()
            print '2'
            print im.dimensions()
            im.save()
            print '3'
            print im.dimensions()
            print '4'
            im.iipimage = 'yo'
            im.save()
            print '5'
            print im.dimensions()
            print '6'
            #im.iipimage = 'jp2/bl/cotton_vitellius_axv/cotton_ms_vitellius_a_xv_f169r.jp2'
            im.iipimage = 'jp2/admin-upload/e/ebcf3583-dd40-431f-8327-92d6f7c1822b.jp2'
            print '7'
            im.save()
            print '8'
            print im.dimensions()

        if command == 'stress_search':
            known_command = True
            self.stress_search(*args[1:])

        if command == 'savean':
            known_command = True
            self.save_annotation(*args[1:])

        if command == 'adhoc':
            known_command = True
            self.adhoc_test(*args[1:])

        if not known_command:
            print self.help

    def unstatic(self):
        print 'unstatic'
        static_root = settings.STATIC_ROOT

        is_verbose = self.is_verbose()

        counts = {'deleted': 0, 'left': 0}
        if len(static_root) > 10:
            for root, subdirs, files in os.walk(static_root):
                for filename in files:
                    path = os.path.join(root, filename)

                    ext = re.sub(ur'^.*\.', '', filename)
                    if ext in ['less', 'ts']:
                        counts['left'] += 1
                        if is_verbose:
                            print 'WARNING: leave transpiled (%s)' % os.path.relpath(path, static_root)
                        continue

                    try:
                        os.unlink(path)
                        counts['deleted'] += 1
                    except Exception as e:
                        print 'WARNING: %s not deleted (%s)' % (path, e)

        print '%s deleted' % counts['deleted']
        print '%s left' % counts['left']

    def race(self, *args):
        '''
        test race condition on the text viewer opening new texts
        The view creates new TextContent and TextCOntentXML records if they don't aleady exist
        But if the text viewer calls this twice view in parallel (e.g. 2 panels open on Transcription)
        then a race condition can lead to the creation of a second CT or CTX records.
        '''

        # 1. find a IP without any texts
        from digipal.models import ItemPart
        from digipal_text.models import TextContent, TextContentType
        from django.contrib.auth import get_user_model

        tct = TextContentType.objects.first()

        ip = ItemPart.objects.exclude(id__in=TextContent.objects.all(
        ).values_list('item_part_id', flat=True)).first()

        print 'IP without text: %s' % ip

        if not ip:
            return

        if 0:
            TextContent(item_part=ip, type=tct).save()
            TextContent(item_part=ip, type=tct).save()

        # 2. simulate a call to the view that returns content for a text panel
        from digipal_text.views.viewer import text_api_view_text
        from digipal import utils

        args = (None, ip.id, tct.slug, 'default', '', tct)
        kwargs = {'user': True}
        utils.run_in_thread_advanced(
            text_api_view_text, args, kwargs, athreads=10, wait=True, print_results=True)

        # delete all the TC & TCX records for this IP
        TextContent.objects.filter(item_part=ip).delete()

    def date_prob(self, *args):
        from digipal.models import HistoricalItem
        from digipal.utils import MAX_DATE_RANGE, get_range_from_date, write_rows_to_csv

        file_path = 'date_prob.csv'

        rows = []

        for hi in HistoricalItem.objects.all():
            date = hi.get_date_sort()
            rg = get_range_from_date(date)
            if rg[0] in MAX_DATE_RANGE or rg[1] in MAX_DATE_RANGE:
                rows.append({
                            u'Document': u'%s' % hi.display_label,
                            u'Date': u'%s' % hi.get_date_sort(),
                            u'Record ID (MOA HI)': u'%s' % hi.id,
                            u'Evidence': u'%s' % u'| '.join([u'%s' % de.evidence for de in hi.date_evidences.all()]),
                            })
                # print date, hi.id, hi.display_label

        write_rows_to_csv(file_path, rows, encoding='utf-8')
        print 'Written %s' % file_path

    def cpip(self, *args):
        from digipal.utils import natural_sort_key
        fs = (args[0], args[1])

        fpkgs = []

        # read packages from two PIP req files
        from digipal.utils import read_file
        for f in fs:
            pkgs = {}
            for line in read_file(f).split('\n'):
                parts = line.strip().split('==')
                if len(parts) == 2:
                    pkgs[parts[0]] = parts[1]
            fpkgs.append(pkgs)

        # compare
        def get_version(fileindex, pkgname):
            return fpkgs[fileindex].get(pkgname, '')

        for pkg in sorted(
                list(set(fpkgs[0].keys() + fpkgs[1].keys())), key=lambda l: l.lower()):
            vers = (get_version(0, pkg), get_version(1, pkg))
            status = '='
            if vers[0] != vers[1]:
                status = '>'
                if natural_sort_key(vers[0]) < natural_sort_key(vers[1]):
                    status = '<'
            print '%3s %10s %10s %s' % (status, vers[0], vers[1], pkg)

    def multivalued(self, *args):
        ''' test Whoosh search on multi-valued documents'''
        from whoosh import fields
        from whoosh.filedb.filestore import RamStorage
        from whoosh import analysis, fields, index, qparser, query, searching, scoring

        schema = fields.Schema(id=fields.STORED, f1=fields.TEXT)
        storage = RamStorage()
        ix = storage.create_index(schema)

        writer = ix.writer()
        values = [u'Value One', u'Term Two', u'Value One;Term Two']
        i = 0

        def vf(v): return v.split(';')
        for value in values:
            i += 1
            writer.add_document(id=i, f1=vf(value))
        writer.commit()

        with ix.searcher() as s:

            print list(s.lexicon('f1'))

            qp = qparser.QueryParser('f1', schema)
            for i in range(0, 2):
                print '-' * 40
                print i, values[i]
                q = qp.parse(u'"%s"' % values[i])
                print repr(q)
                r = s.search(q)
                print [hit for hit in r]

    def record_path(self, *args):
        '''
            {'hi_date_max': -5000, 'hi_index_sortable': 287, 'hi_type': u'Charter',
            'hi_date': u'Probably early 13th century', 'hi_has_images': u'Without image', 'shelfmark_sortable': 0,
            'hi_type_sortable': 3,
            'image_name': [u'dorse', u'face'],
            'image_name_sortable': 1,
            'hi_date_min': -5000,
            'repo_place_sortable': 0, 'repo_place': u'Durham, Durham Cathedral Muniments',
            'hi_date_sortable': 101, 'shelfmark': u'1.1.Sacr.12',
            'hi_index': u'ND App., no. 167 POMS Document 3/93/2', 'repo_city': u'Durham',
            'id': u'598', 'repo_city_sortable': 7}
        '''
        ctype = args[0]
        path = args[1]
        recordid = args[2]

        from digipal.views.faceted_search.faceted_search import get_types
        types = get_types(None)
        fmodel = None
        for t in types:
            if t.get_key() == ctype:
                fmodel = t
        if not fmodel:
            print 'ERROR: content type not found "%s"' % ctype
            exit()

        record = fmodel.get_model().objects.get(id=recordid)
        #afield = {'key': 'locus', 'label': 'Locus', 'path': 'locus', 'search': True, 'viewable': True, 'type': 'code'}
        #afield['path'] = path
        #value = fmodel.get_record_path(record, afield)
        value = fmodel.get_record_path(record, path)
        print repr(value)

    def download_images(self, *args):
        if len(args) < 1:
            print 'ERROR: please provide a URL'
            return
        if len(args) < 2:
            print 'ERROR: please provide a path'
            return

        from utils import web_fetch
        from digipal.utils import write_file

        url = args[0]
        path = args[1]

        rng = re.sub(ur'^.*\{([^}]*)\}.*$', ur'\1', url)
        if rng == url:
            return 'ERROR: please specify a range in the URL. e.g. {1r-10v}'

        # e.g. ['001_R', '141_V']
        rng = rng.split(',')
        rng = [rng[0], rng[-1]]

        locus = rng[0]
        while True:
            aurl = re.sub(ur'\{[^}]*\}', locus, url)

            filename = os.path.join(path, locus)
            if not re.search(ur'\..{1,4}$', filename):
                filename += '.jpg'

            print 'downloading %s to %s' % (aurl, filename)
            # break

            res = web_fetch(aurl)
            if res['error']:
                print res['error']
            else:
                import json
                write_file(filename, res['body'], None)

            if locus == rng[-1]:
                break

            # increment
            inc = 1
            if 'r' in locus or 'R' in locus:
                locus = locus.replace('R', 'V').replace('r', 'v')
                inc = 0
            else:
                if 'v' in locus or 'V' in locus:
                    locus = locus.replace('V', 'R').replace('v', 'r')
            if inc:
                def incn(m):
                    # 0001
                    n = m.group(0)
                    return ('%0' + str(len(n)) + 'd') % (int(n) + 1)

                # increment number
                locus = re.sub(ur'\d+', incn, locus)

    def reconstruct_image(self, *args):
        from utils import web_fetch, write_file

        ret = []

        max_length = 2000

        # e.g. pm dptest recim
        # "http://xxxx/proxy?method=R&ark=btv1b6001165p.f320&l=6&r=5923,3407,731,1406&save"
        # 157v.png

        # download all the parts
        print 'download tiles...'
        tile_numbers = [0, 0]
        if len(args) in [1, 2]:
            url = args[0]
            dest_file = 'reconstructed.png'
            if len(args) > 1:
                dest_file = args[1]

            if 1:
                for x in range(0, 10):
                    for y in range(0, 10):
                        print '', x, y
                        url = re.sub(ur'\d+,\d+,\d+,\d+', '%d,%d,%d,%d' %
                                     (y * max_length, x * max_length, max_length, max_length), url)
                        # print url
                        info = web_fetch(url)
                        #warning = ('OK' if info['status'] == '200' else 'ERROR!!!!!!!!!!')
                        status = info['status']
                        # print status
                        if not status == '200':
                            #tile_file = info['body']
                            break
                        tile_name = '%d-%d.jpg' % (x, y)
                        write_file(tile_name, info['body'])
                        tile_numbers[0] = max(tile_numbers[0], x)
                        tile_numbers[1] = max(tile_numbers[1], y)
                    if y == 0:
                        break
            else:
                tile_numbers = [2, 3]

            # now reconstruct the full image
            # find the total size (by looking at the size of the last tile)
            last_tile = '%d-%d.jpg' % (tile_numbers[0], tile_numbers[1])
            from PIL import Image
            tile = Image.open(last_tile)
            size = [n * max_length for n in tile_numbers]
            size = size[0] + tile.size[0] + 1, size[1] + tile.size[1] + 1
            print '', 'Size: ', size

            # create the new image
            print 'Reconstruct full image'
            im = Image.new('RGB', size, 'white')
            for x in range(0, tile_numbers[0] + 1):
                for y in range(0, tile_numbers[1] + 1):
                    tile_name = '%d-%d.jpg' % (x, y)
                    panel = Image.open(tile_name).convert('RGB')

                    # paste that panel
                    box = [0, 0]
                    box.extend(panel.size)
                    crop = panel.crop(box)
                    target_area = (x * max_length, y * max_length, x *
                                   max_length + crop.size[0], y * max_length + crop.size[1])
                    print '', x, y, crop.size, target_area
                    im.paste(crop, target_area)

            print 'Save full image (%s)' % dest_file
            im.save(dest_file)
            print 'done'

        else:
            print 'ERROR: please specify a URL to the bottom right tile of an image'

        return ret

    def test_sources(self, *args):
        ret = []
        for keyword in ['ker', 'pelteret', 'gneuss', 'digipal',
                        'english manuscripts 1060', settings.SOURCE_SAWYER_KW, 'scragg', 'cla', 'davis']:
            print keyword, ' => ', repr(Source.get_source_from_keyword(keyword))

        return ret

    def max_date_range(self, *args):
        ret = [None, None]
        if not len(args) == 1:
            print 'ERROR: please provide a path to a date field. E.g. dptest max_date_range HistoricalItem.date'
            return

        path = args[0]
        print 'Path: %s' % path

        parts = path.split('.')
#         if len(parts) != 2:
#             print 'ERROR: please provide a correct path to a date field. E.g. dptest max_date_range HistoricalItem.date . A model name and a field name separated by a dot.'
#             return

        model_name = parts[0]
        path_name = '__'.join(parts[1:])
        import digipal.models
        model = getattr(digipal.models, model_name, None)
        if not model:
            print 'ERROR: Invalid model name. See digipal.models module.'
            return

        from digipal.utils import get_range_from_date
        for value in model.objects.values_list(path_name, flat=True):
            #value = getattr(obj, path_name)
            if value:
                rng = get_range_from_date(value)
                # print u'%30s %s' % (rng, value)
                if rng[0] and rng[0] > -5000:
                    if ret[0] is None:
                        ret[0] = rng[0]
                    else:
                        ret[0] = min(ret[0], rng[0])
                if rng[1] and rng[1] < 5000:
                    if ret[1] is None:
                        ret[1] = rng[1]
                    else:
                        ret[1] = max(ret[1], rng[1])

        print repr(ret)

    def date_conv(self, *args):
        from digipal.utils import get_range_from_date, get_range_from_date, MAX_DATE_RANGE
        from digipal.models import Date, HistoricalItem
        diff_count = 0
        unrec_count = 0

        if 'hi' in args:
            query = HistoricalItem.objects.all()
        else:
            query = Date.objects.all()
            # for d in Date.objects.filter(date__contains='Ca
            # ').order_by('id'):

        rid = None
        if len(args) == 2:
            rid = args[1]
            query = query.filter(id=rid)

        cnt = query.count()
        for rec in query.order_by('id'):
            d = rec.date
            status = '=='
            if not args:
                date_rgn = [rec.min_weight, rec.max_weight]
                rng = get_range_from_date(rec.date)
                if rng[0] in MAX_DATE_RANGE and rng[1] in MAX_DATE_RANGE:
                    status = '00'
                    unrec_count += 1
                    print '%4s %s %40s [%7s, %7s] [%7s, %7s]' % (rec.id, status, rec.date, date_rgn[0], date_rgn[1], rng[0], rng[1])
                else:
                    if not(rng[0] == date_rgn[0] and rng[1] == date_rgn[1]):
                        status = '<>'
                    if rid or status == '<>':
                        print '%4s %s %40s [%7s, %7s] [%7s, %7s]' % (rec.id, status, rec.date, date_rgn[0], date_rgn[1], rng[0], rng[1])
            if 'hi' in args:
                d = rec.get_date_sort()
                if rec.date:
                    rng = get_range_from_date(d)
                    if rng[0] in MAX_DATE_RANGE and rng[1] in MAX_DATE_RANGE:
                        status = '00'
                        unrec_count += 1
                    else:
                        if rid or (rng[0] == -5000 or rng[1] == 5000):
                            status = '<>'
                    if status != '==':
                        print '%4s %s %40s [%7s, %7s]' % (rec.id, status, d, rng[0], rng[1])
            if status != '==':
                diff_count += 1

        print '%s incorrect, %s correct, total %s' % (diff_count, cnt - diff_count, cnt)
        print '%s unrecognised, total %s' % (unrec_count, cnt)

    def adhoc_test(self, *args):
        from digipal import utils
        # print utils.get_plain_text_from_html('''<p>a</p><p>b<a
        # href="&gt;yo&lt;">c</a></p>''')
        d = '670 (? for 937) or 937'
        #d = 'c. 950x68'
        print d
        print utils.get_midpoint_from_date_range(d)

    def adhoc_test_old(self, *args):
        from digipal.templatetags import html_escape
        value = u'''<tr>
                <td>

                </td>
                <td>
                        G. 31
                </td>

                <td>Cambridge, Clare College</td>
                <td>17</td>
                <td></td>
                <td>
                    Smaragdus, Diadema monachorum : s. xi ex. or xii in… (G.)
                </td>
            </tr>

            <tr>
                <td>
                        G. 32
                </td>

                <td>Cambridge, Clare College</td>
                <td>18</td>
                <td></td>
                <td>
                    Orosius, Historiae adversus paganos ; Justinus, Epitome… (G.)
                </td>
            </tr>

        '''

        value = u'''\u00E6<td>Cambridge, n…  cambridge</td>'''

        ret = html_escape.tag_phrase_terms(value, unicode(args[0]))
        print '-' * 80
        print ret.encode('ascii', 'ignore')

    def annotation_test(self):
        #         ips = ItemOrigin.objects.values_list('id', 'place__name')
        #         print ips
        #         return
        #
        #         fields = [
        #             'current_item__repository__place__name',
        #             'current_item__repository__name', 'current_item__shelfmark', 'locus', 'historical_items__date', 'group__historical_items__name', 'historical_items__name', 'hands__scribe__scriptorium__name', 'hands__script__name', 'historical_items__description__description', 'id', 'historical_items__catalogue_number',
        #             'historical_items__itemorigin__place__name',
        #             'subdivisions__current_item__repository__place__name',
        #             'subdivisions__current_item__repository__name',
        #             'current_item__repository__place__name',
        #             'current_item__repository__name',
        #             'hands__assigned_place__name',
        #             'hands__scribe__date', 'hands__assigned_date__date', 'hands__scribe__name', 'locus', 'subdivisions__current_item__shelfmark', 'current_item__shelfmark']
        #         ips = ItemPart.objects.all().values_list(*fields)
        #         ips[0]
        from django.contrib.auth.models import User

        ans = []
        # create an editorial annotation with internal note
        gj = u'{"type":"Feature","properties":{"saved":1},"geometry":{"type":"Polygon","coordinates":[[[2737,1476],[2775,1476],[2775,1420],[2737,1420],[2737,1476]]]},"crs":{"type":"name","properties":{"name":"EPSG:3785"}}}'
        an = Annotation(image=Image.objects.all().first(), cutout='123',
                        vector_id='v0', geo_json=gj, author=User.objects.all().first())
        an.internal_note = 'int note'
        ans.append(an)

        # create an editorial annotation with display note
        gj = u'{"type":"Feature","properties":{"saved":1},"geometry":{"type":"Polygon","coordinates":[[[2737,1476],[2775,1476],[2775,1420],[2737,1420],[2737,1476]]]},"crs":{"type":"name","properties":{"name":"EPSG:3785"}}}'
        an = Annotation(image=Image.objects.all().first(), cutout='123',
                        vector_id='v0', geo_json=gj, author=User.objects.all().first())
        an.display_note = 'disp note'
        ans.append(an)

        # create a graph annotation
        gr = Graph()
        gr.idiograph = Idiograph.objects.all().first()
        gr.hand = Hand.objects.all().first()
        gr.save()
        gj = u'{"type":"Feature","properties":{"saved":1},"geometry":{"type":"Polygon","coordinates":[[[2737,1476],[2775,1476],[2775,1420],[2737,1420],[2737,1476]]]},"crs":{"type":"name","properties":{"name":"EPSG:3785"}}}'
        an = Annotation(image=Image.objects.all().first(), cutout='123',
                        vector_id='v0', geo_json=gj, author=User.objects.all().first())
        an.graph = gr
        ans.append(an)

        for a in ans:
            print 'save'
            a.save()

        # run queries
        print 'find all annotations'
        if Annotation.objects.all().filter(
                id__in=[a.id for a in ans]).count() == 3:
            print '\tok'
        else:
            print '\terror'

        print 'find editorial annotations'
        if Annotation.objects.all().editorial().filter(
                id__in=[ans[0].id, ans[1].id]).count() == 2:
            print '\tok'
        else:
            print '\terror'

        print 'find publicly visible annotations'
        if Annotation.objects.all().publicly_visible().filter(
                id__in=[ans[1].id, ans[2].id]).count() == 2:
            print '\tok'
        else:
            print '\terror'

        print 'find graph annotation'
        if Annotation.objects.all().with_graph().filter(
                id=ans[2].id).count() == 1:
            print '\tok'
        else:
            print '\terror'

        for a in ans:
            a.delete()

        gr.delete()

    def save_annotation(self):
        a = Annotation()
        a.image = Image.objects.all()[0]
        a.author_id = 6
        a.geo_json = u'{"type":"Feature","properties":{"saved":1},"geometry":{"type":"Polygon","coordinates":[[[2737,1476],[2775,1476],[2775,1420],[2737,1420],[2737,1476]]]},"crs":{"type":"name","properties":{"name":"EPSG:3785"}}}'
        a.save()

    def stress_search(self, count=1):
        ret = True
        from utils import web_fetch
        from datetime import datetime
        import time
        import threading

        url = 'http://www.digipal.eu/digipal/search/?from_link=true&s=1'
        #url = 'http://localhost/digipal/search/?from_link=true&s=1'

        print 'Stress test for the search page.'

        class FetchingThread(threading.Thread):
            def __init__(self, index):
                super(FetchingThread, self).__init__()
                self.index = index
                self.status = ''

            def run(self):
                now = datetime.now()
                # print '#%d %s Request' % (self.index, str(now))
                info = web_fetch(url)
                now = datetime.now()
                warning = ('OK' if info['status'] ==
                           '200' else 'ERROR!!!!!!!!!!')
                self.status = info['status']
                # print info['status']
                # print '#%d %s %s %s' % (self.index, str(now), info['status'],
                # warning)

        test_count = int(count)
        ts = []
        # start the threads
        for i in range(1, test_count + 1):
            t = FetchingThread(i)
            t.start()
            ts.append(t)

        # wait...
        alive_count = alive_count_old = test_count
        while alive_count:
            alive_count = sum([1 for t in ts if t.isAlive()])
            error_count = sum([1 for t in ts if t.status == '500'])
            if alive_count != alive_count_old:
                alive_count_old = alive_count
                print 'waiting (%d died, %d left, %d errors)' % (test_count - alive_count, alive_count, error_count)
#                 if error_count > 0:
#                     exit()
            if alive_count:
                time.sleep(0.5)

        return ret

    def find_dup_im(self, **kwargs):
        print 'duplicates'
        from digipal.models import Image
        print repr(Image.get_duplicates([744]))

    def autocomplete(self, phrase, **kwargs):
        from utils import readFile
        settings.DEV_SERVER = True
        # split into terms
        terms = re.split(ur'(?ui)[^\w*]+', phrase)

        chrono('search:')
        idx = readFile('ica.idx')
        matches = re.findall(
            ur'(?ui)\b%s(?:[^|]{0,40}\|\||\w*\b)' % re.escape(phrase), idx)
        chrono(':search')
        print (u'\n'.join(set(matches))).encode('ascii', 'ignore')
        print len(idx)

    def catnum(self, root=None):
        print '\nh1 NOCAT'
        hi1 = HistoricalItem(historical_item_type_id=1)
        hi1.save()
        print hi1.catalogue_number
        print hi1.catalogue_numbers.all()

        print '\nh1 NOCAT'
        hi1.save()
        hi1_id = hi1.id
        print hi1.catalogue_number
        print hi1.catalogue_numbers.all()

        print '\nh2'
        hi2 = HistoricalItem(historical_item_type_id=1)
        hi2.save()
        print hi2.catalogue_number
        print hi2.catalogue_numbers.all()

        print '\nh2'
        hi2.catalogue_numbers.add(CatalogueNumber.objects.all()[0])
        hi2.catalogue_numbers.add(CatalogueNumber.objects.all()[1])
        print hi2.catalogue_numbers.all()
        hi2.save()
        print hi2.catalogue_number
        print hi2.catalogue_numbers.all()

        print '\nh2 NOCAT'
        hi2.catalogue_numbers.clear()
        hi2.save()
        print hi2.catalogue_number
        print hi2.catalogue_numbers.all()

        print '\nh3'
        hi3 = HistoricalItem.objects.get(id=hi1_id)
        hi3.catalogue_numbers.add(CatalogueNumber.objects.all()[0])
        hi3.save()

        print hi3.catalogue_number
        print hi3.catalogue_numbers.all()

    def fetch_and_test(self, root=None):
        from utils import web_fetch
        from datetime import datetime

        if not root:
            root = 'http://localhost/'
        print 'Base URL: %s' % root

        stats = []

        pages = [
            '',
            # main search
            'digipal/search/',
            'digipal/search/?terms=+&basic_search_type=manuscripts&ordering=&years=&result_type=',
            # search graph
            'digipal/search/graph/?script_select=&character_select=&allograph_select=punctus+elevatus&component_select=&feature_select=&terms=&submitted=1&view=images',
            # browse images
            'digipal/page',
            # image
            'digipal/page/364/',
            'digipal/page/364/allographs',
            'digipal/page/364/copyright/',
            # static pages
            'about',
            'about/how-to-use-digipal/',
            'about/feedback/',
            # blog and news
            'blog/category/blog/',
            'blog/category/news/',
            'blog/bl-labs-launch-palaeographers-speak-with-forked-ascenders/',
            # records
            'digipal/hands/278/?basic_search_type=manuscripts&result_type=hands',
            'digipal/scribes/96/',
            'digipal/manuscripts/715/',
            # collection
            'digipal/lightbox/',
        ]

        #pages = ['digipal/search/graph/?script_select=&character_select=&allograph_select=punctus+elevatus&component_select=&feature_select=&terms=&submitted=1&view=images',]
        #pages = ['digipal/page/362/',]
        #pages = ['',]

        #pages = ['digipal/search/graph/?script_select=&character_select=&allograph_select=punctus+elevatus&component_select=&feature_select=&terms=&submitted=1&view=images',]
        #pages = ['digipal/hands/1195/graphs/']

        for page in pages:
            url = root + page

            sp = {'url': url, 'msgs': [], 'body': ''}
            stats.append(sp)

            print
            print 'Request %s' % url

            t0 = datetime.now()

            res = web_fetch(url)

            t1 = datetime.now()

            if res['status'] != '200':
                print 'ERROR: %s !!!!!!!!!!!!!!!!!!!' % res['status']
                continue
            if res['error']:
                print 'ERROR: %s !!!!!!!!!!!!!!!!!!!' % res['error']
                continue
            if res['body']:
                print '\t %s KB in %.4f s.' % (len(res['body']) / 1024, (t1 - t0).total_seconds())

                # prefix the line with numbers
                ln = 0
                lines = []
                sp['msgs'] = self.find_errors(res['body'])
                for line in res['body'].split('\n'):
                    ln += 1
                    lines.append('%6s %s' % (ln, line))
                sp['body'] = '\n'.join(lines)
            print '\n'.join([str(m) for m in sp['msgs']])

    def get_opening_tag(self, bs_element):
        ret = ''
        #ret = '<%s %s [..]' % (bs_element.name, ' '.join(['%s="%s"' % (k, v) for k,v in bs_element.attrs.iteritems()]))
        ret = re.sub(ur'(?musi)>.*', '', ('%s' % bs_element))
        return ret

    def find_errors(self, body):
        ret = []

        # custom validations
        sheets = {}
        scripts = {}
        ln = 0
        containers = 0
        script_open_line = None
        for line in body.split('\n'):
            ln += 1
            msg = ''

            sheets_names = re.findall(ur'''[^'"/]+\.css''', line)
            if sheets_names and sheets_names[0] in sheets:
                msg = 'Stylesheet included twice: %s' % sheets_names[0]
                sheets[sheets_names[0]] = 1

            if line.find('<script') > -1:
                if line.find('src') == -1:
                    script_open_line = ln
                else:
                    script_names = re.findall(ur'''[^'"/]+\.js''', line)
                    if script_names[0] in scripts:
                        msg = 'Script included twice: %s' % script_names[0]
                    scripts[script_names[0]] = 1
            if line.find('</script') > -1 and script_open_line is not None:
                msg = 'Inline script (%d lines, starts at %s)' % (
                    ln - script_open_line, script_open_line)
                script_open_line = None
            styles = re.findall(ur'''style\s*=\s*['"]([^"']*)''', line)
            for style in styles:
                style = re.sub(ur'(?:height|width)\s*:\s*[^;]*', ur'', style)
                style = style.replace(' ', '')
                style = style.replace(';', '')
                if style:
                    msg = 'Inline style'
#             if re.search('style\s*=(\s*)"', line):
#                 msg = 'Inline style'
            if re.search('class.+\Wcontainer\W', line):
                containers += 1
            if msg:
                ret.append('%6s: %s (%s)' % (ln, msg, line.strip()))
        if containers > 0:
            ret.append('%6s: %s containers' % ('', containers))

        # structural validation
        import bs4
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(body)
        print (' title: %s' % re.sub(ur'\s+', ' ',
                                     soup.title.string.replace('\n', ''))).encode('ascii', 'ignore')

        # find all the headers
        print 'heading:'
        for i in range(1, 7):
            for header in soup.find_all('h%s' % i):
                print '\t\t%s' % re.sub('\s+|\n', ' ', '%s' % header)

        # check that all rows are under a container
        for row in soup.find_all('div', class_='row'):
            has_container = False
            for parent in row.parents:
                classes = parent.get('class', [])
                if ('container' in classes) or ('container-fluid' in classes):
                    has_container = True
                    break

            if not has_container:
                print ('    ? : Bootstrap ERROR: Rows must be placed within a .container (fixed-width) or .container-fluid (full-width) for proper alignment and padding\n\t\t%s ' %
                       self.get_opening_tag(row)).encode('ascii', 'ignore')

        # check that all cols are under a row
        for col in soup.find_all('div'):
            cl = ' '.join(col.get('class', []))
            if re.search(ur'\bcol-\w\w-\d\b', cl):
                if col.parent.name != 'div' or (
                        'row' not in col.parent.get('class', [])):
                    print ('    ? : Bootstrap ERROR: Content should be placed within columns, and only columns may be immediate children of rows\n\t\t[ %s ] under [ %s ]' % (
                        self.get_opening_tag(col), self.get_opening_tag(col.parent))).encode('ascii', 'ignore')

        # HTML validation
        if 1:
            import urllib2
            import time
            attempts = 0
            ok = True
            while True:
                attempts += 1
                ok = True
                from py_w3c.validators.html.validator import HTMLValidator
                vld = HTMLValidator()
                try:
                    vld.validate_fragment(body)
                except urllib2.HTTPError:
                    time.sleep(1)
                    ok = False
                if ok:
                    break
                if attempts > 2:
                    break

            if ok:
                for info in vld.warnings:
                    ret.append('%6s: [W3C WARNING] %s' %
                               (info['line'], info['message']))
                for info in vld.errors:
                    ret.append('%6s: [W3C ERROR  ] %s' %
                               (info['line'], info['message']))
            else:
                ret.append('\tFailed to call W3C validation.')

        return ret

    def adjust_offsets(self, offset_path, target_path):
        # we calculate a better offset for the annotations by searching for a
        # best match of one annotation along a line between the old (cropped)
        # and new (uncropped) image.
        # pm dptest adjust_offsets crop_offsets.json
        # c:\vol\digipal2\images\originals\bl\backup_bl_from_server\bl

        ###
        # UPDATE THE LOCAL DB FROM THE STG BEFORE RUNNING THIS!!!
        ###

        import json
        from PIL import Image
        images = json.load(open(offset_path, 'rb'))
        c = -1
        ca = 0
        for rel_path, info in images['images'].iteritems():
            images['images'][rel_path]['offset'].append(
                images['images'][rel_path]['offset'][1])
            images['images'][rel_path]['offset'].append(
                images['images'][rel_path]['offset'][2])
            if images['images'][rel_path]['offset'][3] < 0:
                images['images'][rel_path]['offset'][3] = 0
            if images['images'][rel_path]['offset'][4] > 0:
                images['images'][rel_path]['offset'][4] = 0

            # if rel_path != ur'arundel_60\83v': continue
            # if rel_path != ur'add_46204\recto': continue
            # if rel_path != ur'cotton_caligula_axv\152v': continue
            # if rel_path != ur'harley_5915\13r': continue
            c += 1
            print '%s (%d left)' % (rel_path, len(images['images']) - c)

            src_path = os.path.join(images['root'], rel_path) + '.tif'
            dst_path = os.path.join(target_path, rel_path) + '.tif'
            if not os.path.exists(dst_path):
                print '\tskipped (new image)'
                continue

            # find an annotation in the database
            a = Annotation.objects.filter(
                image__iipimage__endswith=rel_path.replace('\\', '/') + '.jp2')
            if a.count() == 0:
                print '\tskipped (no annotation)'
                continue
            a = a[0]

            if images['images'][rel_path]['offset'][2] != 0:
                print '\tskipped (y-crop <> 0)'
                print '\t!!!!!!!!!!!!! y-crop is not zero !!!!!!!!!!!!!!!'
                continue

            # open the images
            ca += 1
            src_img = Image.open(src_path)
            dst_img = Image.open(dst_path)
            sps = src_img.convert('L').load()
            dps = dst_img.convert('L').load()
            print '\tsrc: %s x %s; dst: %s x %s' % (src_img.size[0], src_img.size[1], dst_img.size[0], dst_img.size[1])

            # find the best match for this annotation region on the new image

            # We scan a whole line on the uncropped image to find the x value
            # that minimises the pixelwise difference of annotation regions.
            box = a.get_coordinates(None, True)
            print '\tbox: %s' % repr(box)
            size = [(box[1][i] - box[0][i] + 1) for i in range(0, 1)]
            min_info = (0, 1e6)
            for x in range(0, src_img.size[0] - size[0]):
                diff = 0
                diff0 = None
                for ys in range(box[0][1], box[1][1] + 1):
                    for xs in range(0, box[1][0] - box[0][0] + 1):
                        if diff0 is None:
                            diff0 = sps[x + xs, ys] - dps[box[0][0] + xs, ys]
                            diff = abs(diff0)
                        else:
                            diff += abs(sps[x + xs, ys] -
                                        dps[box[0][0] + xs, ys] - diff0)
                if diff < min_info[1]:
                    min_info = [x, diff]
            print '\tbest match at x = %s (diff = %s)' % (min_info[0], min_info[1])
            offsetx = min_info[0] - box[0][0]
            images['images'][rel_path]['offset'][3] = offsetx
            print '\toffset: %s; detected: %s' % (repr(info['offset']), offsetx)
            if info['offset'][1] != offsetx:
                print '\t******************************************'
                # if info['offset'][1] < 0 and offsetx != 0:
                #    print '\t!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'

        print '%d images with annotations.' % ca

        print

        print json.dumps(images)

    def correct_annotations(self, info_path):
        import json
        images = json.load(open(info_path, 'rb'))

        counts = {'image': 0, 'annotation': 0}
        for path, info in images['images'].iteritems():
            # if path != 'harley_5915\\13r': continue
            # if path != 'harley_585\\191v': continue
            # if path != 'arundel_60\\83v': continue
            offsets = info['offset']
            if offsets[0]:
                print path.replace('\\', '/')
                # continue
                print '\t%s' % repr(offsets)
                imgs = Image.objects.filter(
                    iipimage__endswith=path.replace('\\', '/') + '.jp2')
                c = imgs.count()
                if c == 0:
                    # print '\tWARNING: Image record not found.'
                    continue
                if c > 1:
                    # print '\tWARNING: More than one Image record not found.'
                    continue

                annotations = imgs[0].annotation_set.filter().distinct()
                if annotations.count():
                    counts['image'] += 1
                    for annotation in annotations:
                        counts['annotation'] += 1
                        # print
                        # print annotation.id, annotation.vector_id
                        # print annotation.cutout
                        # print annotation.geo_json
                        annotation.cutout = self.get_uncropped_cutout(
                            annotation, info)
                        annotation.geo_json = self.get_uncropped_geo_json(
                            annotation, offsets)

                        # print annotation.cutout
                        # print annotation.geo_json
                        annotation.save()
                    print '\t%d annotations' % annotations.count()

        # print counts

    # TODO: remove, only temporary
    def get_uncropped_cutout(self, annotation, image_info):
        ret = annotation.cutout

        offsets = image_info['offset']

        '''
            Correct the region parameter in the cutout URLs
            E.g. http://digipal-stg.cch.kcl.ac.uk/iip/iipsrv.fcgi?FIF=jp2/bl/cotton_vitellius_cv/248r.jp2&RST=*&HEI=1206&RGN=0.381031,0.334415,0.019381,0.023682&CVT=JPG

            0.381031,0.334415,0.019381,0.023682

            px,py,lx,ly

            px: x position of the top right corner of the box expressed as a ratio over the image width
            lx: the width of the box as a ratio over the image width

            Algorithm and formula for the conversion:

            for r in (px,py,lx,ly):
                nl = new image length in that axis
                l = old image length in that axis
                o' = o = offset in that axis
                o' = 0 if r = lx or ly or o < 0
                r' = ((r * l) + o') / nl
        '''
        match = re.search(ur'RGN=([^,]+),([^,]+),([^,]+),([^,]+)&', ret)
        #size = annotation.image.iipimage._get_image_dimensions()
        size = (image_info['x'], image_info['y'])
        rgn = []
        for i in range(1, 5):
            r = float(match.group(i))

            # axis: 0 for x; 1 for y
            d = 0
            if i in (2, 4):
                d = 1
            offset = offsets[3 + d]
            nl = size[d]
            l = nl - abs(offset)
            #if (offset < 0) or (i > 2): offset = 0
            if (i > 2):
                offset = 0
            #if (i > 1): offset = 0

            r = ((r * l) + offset) / nl

            rgn.append(r)

        # print rgn
        ret = re.sub(ur'RGN=[^&]+', ur'RGN=' +
                     ','.join(['%.6f' % r for r in rgn]), ret)
        # print ret

        return ret

    def get_uncropped_geo_json(self, annotation, offsets):
        import json
        geo_json = annotation.geo_json

        '''
        {
            "type":"Feature",
            "properties":{"saved":1},
            "geometry":{"type":"Polygon",
                        "coordinates":[
                            [
                                [1848,3957.3333740234],
                                [1848,4103.3333740234],
                                [1942,4103.3333740234],
                                [1942,3957.3333740234],
                                [1848,3957.3333740234]
                            ]
                        ]
                        },
            "crs":{"type":"name","properties":{"name":"EPSG:3785"}}
        }
        '''

        # See JIRA-229, some old geo_json format are not standard JSON
        # and cause trouble with the deserialiser (json.loads()).
        # The property names are surrounded by single quotes
        # instead of double quotes.
        # simplistic conversion but in our case it works well
        # e.g. {'geometry': {'type': 'Polygon', 'coordinates':
        #     Returns {"geometry": {"type": "Polygon", "coordinates":
        geo_json = geo_json.replace('\'', '"')

        geo_json = json.loads(geo_json)

        coo = geo_json['geometry']['coordinates'][0]
        for c in coo:
            # if offsets[1] > 0:
            c[0] = int(c[0] + offsets[3])
            # if offsets[2] > 0:
            #c[1] = int(c[1] - offsets[4])

        # convert the coordinates
        ret = json.dumps(geo_json)

        return ret


#
#
#         from digipal.models import Annotation
#         annotations = Annotation.objects.filter(image__id=590)
#         offsets = [True, 0, 499]
#         for a in annotations:
#             a.get_uncropped_cutout(offsets)
#             break

    def img_compare(self, path_src, path_dst):

        import json
        src = json.load(open(path_src, 'rb'))
        dst = json.load(open(path_dst, 'rb'))

        new = []
        different = []
        same = []

        # compare the two list of images
        for src_file in src['images']:
            src['images'][src_file]['offset'] = [False, 0, 0]
            src_info = src['images'][src_file]
            if src_file not in dst['images']:
                new.append(src_file)
            else:
                dst_info = dst['images'][src_file]
                if src_info['size'] != dst_info['size']:
                    different.append(src_file)
                else:
                    same.append(src_file)

#         print '\nSame\n'
#         same = sorted(same)
#         for f in same:
#             print f
#
#         print '\nNew\n'
#         new = sorted(new)
#         for f in new:
#             print f

        print '\nDifferent\n'
        different = sorted(different)
        for f in different:
            # if not(f == 'add_46204\\recto'): continue
            src['images'][f]['offset'] = self.get_image_offset(src, dst, f)
            print f
            print '', src['images'][f]['offset']
            # print '', src['images'][f]['offset']

        # save the offsets
        print

        print json.dumps(src)

        print

        print '\n'
        print '%d source images;  %d destination images' % (len(src['images']), len(dst['images']))
        print '%d new images; %d same images; %d different images' % (len(new), len(same), len(different))

    # ------------------------------------------------------------------------------

    def find_image_offset(self, id1, id2):
        from digipal.images.models import Image
        settings.DEV_SERVER = True
        im1 = Image.objects.get(id=id1)
        im2 = Image.objects.get(id=id2)
        ret = im1.find_image_offset(im2)
        print ret
        return ret

    # ------------------------------------------------------------------------------

    def get_image_offset(self, src, dst, f):
        '''
         Given one image and its cropped version, returns where the crop was made.
         We assume that at least one corner of the original image has not been cropped.

         Input:
             src a dictionary as returned by get_info() on the source folder (uncropped)
             dst a dictionary as returned by get_info() on the dest. folder (cropped)
             f the relative path to the image, i.e. the key of the image in src and dst.

         Returns a tuple [found, x, y]
         If found = True the dst image is a crop of the src image. Otherwise it is False and x, y can be ignored.
         x >= 0 then x pixels have been discarded from the top of the original image to make the crop.
            x < 0 then -x pixels have been discarded from the bottom of the original image to make the crop.
         y = same principle as for x but with left (> 0) and right (< 0).
        '''
        from PIL import Image

        cropped_path = os.path.join(
            dst['root'], f) + '.' + dst['images'][f]['ext']
        uncropped_path = os.path.join(
            src['root'], f) + '.' + src['images'][f]['ext']
        cropped_img = Image.open(cropped_path)
        uncropped_img = Image.open(uncropped_path)

        ret = [False, uncropped_img.size[0] - cropped_img.size[0],
               uncropped_img.size[1] - cropped_img.size[1]]

        corner_diffs = [self.are_corner_identical(
            cropped_img, uncropped_img, *pos) for pos in [[0, 0], [-1, 0], [-1, -1], [0, -1]]]
        min_index = corner_diffs.index(min(corner_diffs))
        if min_index == 0:
            ret = [True, -ret[1], -ret[2]]
        if min_index == 1:
            ret = [True, ret[1], -ret[2]]
        if min_index == 2:
            ret = [True, ret[1], ret[2]]
        if min_index == 3:
            ret = [True, -ret[1], ret[2]]

        # print corner_diffs

#         if self.are_corner_identical(cropped_img, uncropped_img, 0, 0):
#             ret = [True, -ret[1], -ret[2]]
#         elif self.are_corner_identical(cropped_img, uncropped_img, -1, 0):
#             ret = [True, ret[1], -ret[2]]
#         elif self.are_corner_identical(cropped_img, uncropped_img, -1, -1):
#             ret = [True, ret[1], ret[2]]
#         elif self.are_corner_identical(cropped_img, uncropped_img, 0, -1):
#             ret = [True, -ret[1], ret[2]]

#         ret = [False, 0, 0]
#
#         width_diff = src['images'][f]['y'] - dst['images'][f]['y']
#         if src['images'][f]['y'] != dst['images'][f]['y']:
#             if src['images'][f]['x'] != dst['images'][f]['x']:
#                 print '\tDifferent dimensions (%d x %d <> %d x %d)' % (src['images'][f]['x'], src['images'][f]['y'], dst['images'][f]['x'], dst['images'][f]['y'])
#             else:
#                 print '\tDifferent widths %d <> %d' % (src['images'][f]['y'], dst['images'][f]['y'])
#

        return ret

    def are_corner_identical(
            self, cropped_img, uncropped_img, fromx=0, fromy=0):
        #ret = True
        ret = 0

        imgs = [cropped_img, uncropped_img]
        imgps = [img.load() for img in imgs]

        # scan direction for x and y dimensions
        dir = [fromx, fromy]
        if dir[0] == 0:
            dir[0] = 1
        if dir[1] == 0:
            dir[1] = 1

        # initial position in each image
        pos = [[fromx, fromy], [fromx, fromy]]

        # convert -1 pos (relative to right or bottom edge) to absolute
        # position
        for i in (0, 1):
            for j in (0, 1):
                if pos[i][j] == -1:
                    pos[i][j] = imgs[i].size[j] + pos[i][j]

        def is_color_identical(p0, p1):
            # not strictly true but it's a good approximation
            return sum(p0) == sum(p1)

        avgs = [[0, 0, 0], [0, 0, 0]]

        for k in range(0, 400):
            p0 = imgps[0][pos[0][0], pos[0][1]]
            p1 = imgps[1][pos[1][0], pos[1][1]]
            #ret += abs(p0[0] - p1[0]) + abs(p0[1] - p1[1]) + abs(p0[2] - p1[2])
            ret += abs(p0[0] - p1[0])
            pos[0][0] += dir[0]
            pos[0][1] += dir[1]
            pos[1][0] += dir[0]
            pos[1][1] += dir[1]

        # print sum([avgs[0]]) / 3.0 / 100.0

        return ret

    def img_info(self, path):

        ret = {'root': path}

        ret['images'] = self.get_image_info(path)

        import json
        print json.dumps(ret)

        #img_dst = self.get_image_info(target_path)

    def get_image_info(self, path):
        ret = {}
        from PIL import Image

        files = [os.path.join(path, f) for f in os.listdir(path)]
        while files:
            file = files.pop(0)

            file = os.path.join(path, file)

            if os.path.isfile(file):
                (file_base_name, extension) = os.path.splitext(file)
                if extension.lower() in settings.IMAGE_SERVER_UPLOAD_EXTENSIONS:
                    file_relative = os.path.relpath(file, path)

                    st = os.stat(file)
                    key = re.sub(ur'\.[^.]+$', ur'', file_relative)
                    ret[key] = {
                        'ext': extension[1:],
                        'size': st.st_size,
                        'date': st.st_mtime,
                    }
                    try:
                        im = Image.open(file)
                        ret[key]['x'] = im.size[0]
                        ret[key]['y'] = im.size[1]
                    except Exception:
                        ret[key]['x'] = 0
                        ret[key]['y'] = 0

            elif isdir(file):
                files.extend([os.path.join(file, f) for f in os.listdir(file)])

        return ret

    def rename_images(self, csv_path):
        print csv_path
        import csv
        import shutil

        with open(csv_path, 'rb') as csvfile:
            #line = csv.reader(csvfile, delimiter=' ', quotechar='|')
            csvreader = csv.reader(csvfile)
            base_dir = os.path.dirname(csv_path)
            first_line = True
            for line in csvreader:
                if first_line:
                    first_line = False
                    continue
                file_name_old = line[0]
                matches = re.match(ur'(.*),(.*)', line[1])
                if not matches:
                    matches = re.match(ur'(.*)(recto|verso)', line[1])
                if matches:
                    dir_name = matches.group(1).lower()
                    file_name = matches.group(2).lower().strip()

                    file_name = re.sub(ur'^f\.\s*', '', file_name)
                    file_name = file_name.replace('*', 'star')
                    file_name = re.sub(ur'\s+', '_', file_name.strip())

                    dir_name = re.sub(ur'\b(\w)\s?\.\s?', ur'\1', dir_name)
                    dir_name = re.sub(ur'\s+', '_', dir_name.strip())
                    dir_name = re.sub(ur'\.', '', dir_name).strip()

                    # create the dir
                    dir_name = os.path.join(base_dir, dir_name)
                    # print dir_name, file_name
                    if not os.path.exists(dir_name):
                        os.mkdir(dir_name)
                    file_name = os.path.join(
                        dir_name, file_name) + re.sub(ur'^.*(\.[^.]+)$', ur'\1', file_name_old)
                    if not os.path.exists(file_name):
                        #shutil.copyfile(os.path.join(base_dir, file_name_old), file_name)
                        print file_name
                else:
                    print 'No match (%s)' % line[1]

    def test_natsort(self, options):
        #[ ItemPart.objects.filter(display_label__icontains='royal')]
        sms = ['A.897.abc.ixv', 'Hereford Cathedral Library O.IX.2',
               'Hereford Cathedral Library O.VI.11']
        for s in sms:
            print s, natural_sort_key(s)
        print sorted(sms, key=lambda i: natural_sort_key(i))
        # print natural_sort_key('A.897.abc.ixv')
        # print natural_sort_key('Hereford Cathedral Library O.IX.2')
        #'Hereford Cathedral Library O.VI.11'
        return

#         l = list(ItemPart.objects.filter(display_label__icontains='royal').order_by('display_label'))
#
#         import re
#
#         _nsre = re.compile('([0-9]+)')
#         def natural_sort_key(s):
#             return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]
#         l = sorted(l, key=lambda i: natural_sort_key(i.display_label))
#
#         for i in l:
#             print (i.display_label).encode('ascii', 'ignore')

    def test_email(self, options):
        #from django.core.mail import send_mail
           #send_mail('Subject here', 'Here is the message.', 'gnoelp@yahoo.com', ['gnoelp@yahoo.com'], fail_silently=False)
        # Import smtplib for the actual sending function
        import smtplib

        # Import the email modules we'll need
        from email.mime.text import MIMEText

        # Open a plain text file for reading.  For this example, assume that
        # the text file contains only ASCII characters.
        # Create a text/plain message
        msg = MIMEText('my message')

        # me == the sender's email address
        # you == the recipient's email address
        msg['Subject'] = 'Subject'
        msg['From'] = 'gnoelp@yahoo.com'
        msg['To'] = 'gnoelp@yahoo.com'

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP('localhost')
        s.sendmail(msg['From'], msg['To'].split(', '), msg.as_string())
        s.quit()

    def test_locus(self, options):
        from digipal.models import Image
        i = Image()
        for l in [
            ('10r', ('10', 'r')),
            ('10v', ('10', 'v')),
            ('11', ('11', None)),
            ('', ('y', None)),
            (None, ('y', None)),
            ('10 r', ('10', 'r')),
            ('10 v 9 r', ('10', 'v')),
            ('fragment recto', (None, 'r')),
            ('fragment verso', (None, 'v')),
            ('seal', ('x', None)),
            (u'327(2)', ('327', None)),
            (u'327*(2)', ('327', None)),
            (u'46v–47r', ('46', 'v')),
            (u'D.xxvii, 25v', ('25', 'v')),
            (u'D.xxvii, 25r', ('25', 'r')),
        ]:
            i.locus = l[0]
            i.update_number_and_side_from_locus()
            print '%s => %s, %s' % (i.locus, i.folio_number, i.folio_side)
            if i.folio_number != l[1][0] or i.folio_side != l[1][1]:
                print '\tERROR, expected %s, %s.' % (l[1][0], l[1][1])

        if 1:
            print '\nDetect changes:'
            for im in Image.objects.filter(item_part__isnull=False):
                old_val = '(%s, %s)' % (im.folio_number, im.folio_side)
                n, s = im.update_number_and_side_from_locus()
                new_val = '(%s, %s)' % (n, s)
                if new_val != old_val:
                    print '#%s locus: %s, %s -> %s' % (im.id, im.locus, old_val, new_val)

    def test_mem(self):
        import gc
        objs = gc.get_objects()

        # total size
        print '%s used by %s objects in the GC' % (hs(sum(sys.getsizeof(o) for o in objs)), len(objs))

        # find biggest objects
        limit = 1000000
        l = 40

        def ostr(o):
            try:
                return '%s' % str(o)[:l]
            except Exception as e:
                return '??? %s' % type(e)

        def list_objs(objs):
            for i in range(0, min(limit, len(objs))):
                print '', i, hs(sys.getsizeof(objs[i])), type(objs[i]), ostr(objs[i])

        objs = sorted(objs, key=lambda o: sys.getsizeof(o), reverse=True)
        list_objs(objs)

        objs = sorted(objs, key=lambda o: ostr(o))
        list_objs(objs)


def hs(size):
    return '%.3f MB' % (1.0 * size / 1024.0 / 1024.0)
