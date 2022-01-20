from django.core.management.base import CommandError
from dpbase import DPBaseCommand as BaseCommand
from mezzanine.conf import settings
from os.path import isdir
import os
import re
import utils
from optparse import make_option
from os import listdir
from os.path import isfile, join
from digipal.models import Image

def get_originals_path():
    ret = join(getattr(settings, 'IMAGE_SERVER_ROOT', ''), getattr(settings, 'IMAGE_SERVER_ORIGINALS_ROOT', ''))
    return ret

def get_image_path():
    ret = join(getattr(settings, 'IMAGE_SERVER_ROOT', ''), getattr(settings, 'IMAGE_SERVER_UPLOAD_ROOT', ''))
    return ret

class Command(BaseCommand):
    args = 'list|upload'
    help = ''' Manage the Digipal images

----------------------------------------------------------------------

 ORIGINAL images are found under:

  %s

 IMAGE STORE (converted images) is found under:

  %s

----------------------------------------------------------------------

 To upload your document images in the database:

 1. manually copy your original images somewhere under the ORIGINAL folder:

 2. copy the original images to the IMAGE STORE (image files managed by the
    image server) with this command:

    python manage.py dpim copy

 3. convert your images in the image store to the JPEG 2000 and upload them
    into the database:

    python manage.py dpim upload

 Image files can be processed selectively. Read the documentation below for
 more details.

 WARNING: please do not leave your original images in the IMAGE STORE, they
    might be deleted. Use the ORIGINAL folder instead (see above).

----------------------------------------------------------------------

 Commands:

    Working with the image store:

        list
            Lists the images on disk and if they are already uploaded

        upload
            Converts new images to JPEG 2000 and create the corresponding
            Image records

        unstage
            Removes the images from the database (but leave them on disk)

    Dealing with original images:

        copy
            Copies the all the original images to the image store.
            Also converts the names so they are compatible with the image
            server.
            Selection is made with the --filter option.
            Recommended to use 'originals' comamnd to test the selection.

        originals
            list all the original images,
            Selection is made with the --filter option.

        pocket PATH [QUALITY] [PAUSE] [--FILTER=X]
            Convert original images to a smaller, portable, size
            PATH: output filesystem path
            PAUSE: number of seconds to wait between each conversion (default is 0)
            QUALITY: percentage of image compression (default is 50)

        convert

    Database Image records:

        update_dimensions
            Read the width and height and size of the images and save them in the database

 Options:

    --filter X
        Select the images to be uploaded/listed/deleted by applying
        a filter on their name. Only files with X in their path or
        filename will be selected.
        --filter="a b, cd e,#195"
        Select images with (a AND b in the name) OR (cd and e in the name)
        OR image.id = 195
        
    --cdt X
        The action will apply only to images which meet the condition X
        X is a Django Queryset filter, e.g. --cdt 'id=6040'

    --offline
        Select only the images which are on disk an not in the DB

    --missing
        Select only the images which are in the DB and not on disk

 Examples:

    python manage.py dpim --filter canterbury upload
        upload all the images which contain 'canterbury' in their name

    python manage.py dpim --filter canterbury unstage
        remove from the database the Image records which point to
        an image with 'canterbury' in its name.

    python manage.py dpim --offline list
        list all the image which are only on disk and not in the DB

    python manage.py dpim --missing --filter canterbury list
        list all the image which are only in the database and not
        on disk and which name contains 'canterbury'

----------------------------------------------------------------------

    ''' % (get_originals_path(), get_image_path())

    option_list = BaseCommand.option_list + (
        make_option('--db',
            action='store',
            dest='db',
            default='default',
            help='Name of the database configuration'),
        make_option('--offline',
            action='store_true',
            dest='offline',
            default='',
            help='Only list images which are offline'),
        make_option('--links',
            action='store',
            dest='links',
            default='',
            help='Link names'),
        make_option('--op',
            action='store',
            dest='out_path',
            default='.',
            help='out path'),
        make_option('--links_file',
            action='store',
            dest='links_file',
            default='',
            help='Link names'),
        make_option('--missing',
            action='store_true',
            dest='missing',
            default='',
            help='Only list images which are missing from disk'),
        make_option('--cdt',
            action='store',
            dest='cdt',
            default='',
            help=''),
    )

    def get_all_files(self, root):
        # Scan all the image files on disk (under root) and in the database.
        # Returns an array of file informations. For each file we have:
        #     {'path': path relative to settings.IMAGE_SERVER_ROOT, 'disk': True|False, 'image': Image object|None}
        ret = []

        all_images = Image.objects.all()

        cdt = self.options.get('cdt', None)
        if cdt:
            all_images = eval('all_images.filter({})'.format(cdt))

        image_paths = {}
        images = {}
        for image in all_images:
            image_paths[os.path.normcase(image.iipimage.name)] = image.id
            images[image.id] = image

        # find all the images on disk
        current_path = root

        files = [join(current_path, f) for f in listdir(current_path)]
        while files:
            file = files.pop(0)

            file = join(current_path, file)

            if isfile(file):
                (_, extension) = os.path.splitext(file)
                if extension.lower() in settings.IMAGE_SERVER_UPLOAD_EXTENSIONS and not ('.tmp' in file and '.bmp' in file):
                    file_relative = os.path.relpath(file, settings.IMAGE_SERVER_ROOT)

                    id = image_paths.get(os.path.normcase(file_relative), 0)

                    info = {
                            'image': images.get(id, None),
                            'disk': 1,
                            'path': file_relative
                            }

                    if id:
                        del images[id]

                    ret.append(info)
            elif isdir(file):
                files.extend([join(file, f) for f in listdir(file)])

        # find the images in DB but not on disk
        for image in images.values():
            file_name = ''
            if image.iipimage:
                file_name = image.iipimage.name
            info = {
                    'disk': os.path.exists(join(getattr(settings, 'IMAGE_SERVER_ROOT', ''), file_name)),
                    'path': file_name,
                    'image': image
                    }
            if file_name == '':
                info['disk'] = False
            ret.append(info)

        return ret

    def handle(self, *args, **options):

        root = get_image_path()
        if not root:
            raise CommandError('Path variable IMAGE_SERVER_ROOT not set in your settings file.')
        if not isdir(root):
            raise CommandError('Image path not found (%s).' % root)
        if len(args) < 1:
            raise CommandError('Please provide a command. Try "python manage.py help dpdb" for help.')
        command = args[0]
        if options['db'] not in settings.DATABASES:
            raise CommandError('Database settings not found ("%s"). Check DATABASE array in your settings.py.' % options['db'])

        db_settings = settings.DATABASES[options['db']]

        self.args = args

        self.options = options

        known_command = False
        counts = {'online': 0, 'disk': 0, 'disk_only': 0, 'missing': 0}
        if command == 'fetch':
            known_command = True
            self.fetch(*args, **options)

        if command == 'update_dimensions':
            known_command = True
            self.update_dimensions(*args)

        if command == '_2jp2':
            known_command = 1
            for im in Image.objects.all():
                if im.iipimage.name.endswith('tif'):
                    im.iipimage.name = im.iipimage.name[:-3] + 'jp2'
                    im.save()

        if command == 'move_annotations':
            known_command = True
            self.move_annotations()

        if command == 'jp2tif':
            known_command = True
            self.jp2tif()

        if command == 'setdims':
            known_command = True
            self.setdims()

        if command == 'enlarge':
            known_command = True
            self.enlarge()

        if command in ('list', 'upload', 'unstage', 'update', 'remove', 'crop'):
            known_command = True

            for file_info in self.get_all_files(root):
                file_relative = file_info['path']
                found_message = ''

                online = (file_info['image'] is not None)
                imageid = 0
                if online:
                    imageid = file_info['image'].id

                if not self.is_filtered_in(file_info):
                    continue

                if options['offline'] and online:
                    continue

                if options['missing'] and file_info['disk']:
                    continue

                if not online:
                    found_message = '[OFFLINE]'
                elif not file_info['disk']:
                    found_message = '[MISSING FROM DISK]'
                else:
                    found_message = '[ONLINE]'

                if online:
                    counts['online'] += 1
                if file_info['disk']:
                    counts['disk'] += 1
                if file_info['disk'] and not online:
                    counts['disk_only'] += 1
                if not file_info['disk'] and online:
                    counts['missing'] += 1

                processed = False

                if (command == 'crop' and online):
                    self.crop_image(file_info)
                    processed = True

                if (command == 'upload' and not online) or (command == 'update' and online):
                    processed = True

                    file_path, basename = os.path.split(file_relative)
                    new_file_name = os.path.join(file_path, re.sub(r'(\s|,)+', '_' , basename.lower()))
                    if re.search(r'\s|,', new_file_name):
                        found_message = '[FAILED: please remove spaces and commas from the directory names]'
                    else:
                        image = None
                        if command in ('update',):
                            found_message = '[JUST UPDATED]'
                            image = file_info['image']
                        else:
                            found_message = '[JUST UPLOADED]'
                            image = Image()
                            image.iipimage = file_relative
                            image.image = 'x'
                            image.caption = os.path.basename(file_relative)
                            # todo: which rules should we apply here?
                            image.display_label = os.path.basename(file_relative)

                        # convert the image to jp2/tif
                        if command == 'upload':
                            error_message = self.convert_image(image)
                            if error_message:
                                found_message += ' ' + error_message
                                image = None
                            else:
                                found_message += ' [JUST CONVERTED]'

                        if image:
                            image.save()
                            imageid = image.id

                if command == 'remove' and file_info['disk']:
                    file_abs_path = join(settings.IMAGE_SERVER_ROOT, file_relative)
                    print file_abs_path
                    if os.path.exists(file_abs_path):
                        os.unlink(file_abs_path)
                        found_message = '[REMOVED FROM DISK]'
                    else:
                        found_message = '[NOT FOUND]'
                    processed = True

                if command == 'unstage' and online:
                    processed = True

                    found_message = '[JUST REMOVED FROM DB]'
                    file_info['image'].delete()

                if self.is_verbose() or command == 'list' or processed:
                    extra = ''
                    if not file_info['disk'] and online and file_info['image'].image is not None and len(file_info['image'].image.name) > 2:
                        extra = file_info['image'].image.name
                    print '#%s\t%-20s\t%s\t%s' % (imageid, found_message, file_relative, extra)

            print '%s images in DB. %s image on disk. %s on disk only. %s not on disk.' % (counts['online'], counts['disk'], counts['disk_only'], counts['missing'])

        if command in ['copy', 'originals', 'copy_convert', 'pocket']:
            known_command = True
            self.processOriginals(args, options)

        if not known_command:
            raise CommandError('Unknown command: "%s".' % command)

    def move_annotations(self):
        if len(self.args) != 3:
            print 'Error: please prove two image ids, SOURCE and TARGET of the annotation migrations.'
            return
        
        import digipal.images.models
        ims = [digipal.images.models.Image.objects.get(id=v) for v in self.args[1:3]]
        ans = ims[0].annotation_set.filter()
        print 'Move %s annotations from %s to %s' % (ans.count(), ims[0], ims[1])
        
        diff = ims[0].compare_with(ims[1])
        print diff
        for an in ans:
            print '#%s, %s' % (an.id, an)
            info = ims[0].get_annotation_offset(an, ims[1], diff)
            if info and info['offsets']:
                an.image = ims[1]
                an.geo_json = ims[0].get_uncropped_geo_json(an, info['offsets'], image_size=ims[1].get_img_size(), old_image_size=ims[0].get_img_size())
                print an.geo_json
                an.save()
#             if sum(offset_info['offsets']) > 0:
#                 im1.replace_image_and_update_annotations(offset_info['offsets'], im2)
            

        #if self.is_dry_run():

    def is_filtered_in(self, file_info):
        '''e.g. "ab cd, ef gh"
            => image CDAB and 1EeF9GH are returned
            => so , means OR and space means AND
        '''
        ret = False
        file_relative = file_info['path']
        for condition in self.options['filter'].lower().split(','):
            met = True
            for part in condition.split(' '):
                part = part.strip()
                if part:
                    if part.startswith('#'):
                        if not file_info['image'] or ('#%s' % file_info['image'].id) != str(part):
                            met = False
                            break
                    else:
                        if part not in file_relative.lower():
                            met = False
                            break
            if met:
                ret = True
                break

        return ret

    def crop_image(self, info):
        # height of the image to request from the image server
        # taller  => better approximations of the boundaries
        # but bigger & slower download and processing.
        height = 500
        image = info['image']
        if not image:
            return

        print image.dimensions()

        file_path = self.get_image_path(image, height)
        if not file_path: return

        import cv2
        img = cv2.imread(file_path)
        if img is None:
            return
        path_out = '%s.png' % file_path

        bg_color = None
        # The background color, leave None for a more adaptive method
        # Using a bg color is more reliable
        bg_color = (183, 182, 182)

        # naive cropping technique:
        import numpy as np
        dims = img.shape[:2]
        Z = img.reshape((-1,3))
        Z = np.float32(Z)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        K = 10
        _,label,center=cv2.kmeans(Z,K,criteria,10,cv2.KMEANS_RANDOM_CENTERS)

        # Now convert back into uint8, and make original image
        center = np.uint8(center)

        # Find the nearest color to our typical grey background
        if bg_color:
            bg_index = 0
            best_diff = None
            i = 0
            import math
            for c in center:
                diff = math.sqrt(sum([math.pow(abs(c[d] - bg_color[d]),2) for d in [0,1,2]]))
                #print i, c, diff
                if best_diff is None or best_diff > diff:
                    best_diff = diff
                    bg_index = i
                i += 1
            print center[bg_index]

        #print center
        res = center[label.flatten()]
        res2 = res.reshape((img.shape))

        # image of centroid indices (one int per 'pixel')
        center2 = np.array(range(0, K))
        imgk = center2[label.flatten()]
        imgk = imgk.reshape(*dims)

        bests = []
        for d in [0, 1]:
            imgk = np.transpose(imgk)

            dims = imgk.shape[:2]

            defaults = [0, dims[1]]
            bests.append(defaults[:])

            if not bg_color:
                pc = 0.95
                if d == 0:
                    pc = 0.75
            else:
                pc = 0.90
                if d == 0:
                    pc = 0.7

            #pc = 0.7

            l = dims[0]
            c = dims[1] / 2
            th = int(pc * l)

            #print dims, l, c, dims[1]
            for x in xrange(0, dims[1]):
                line = imgk[:, x]
                cs, cts = np.unique(line, return_counts=True)
                if not bg_color:
                    m = cts.max()
                else:
                    m = 0
                    for i in xrange(0, len(cs)):
                        if cs[i] == bg_index:
                            m = cts[i]
#                     print cs
#                     print cts
#                     print m
                    #exit()
                    #bgi = cs.

                #print x, m, th
                #print x, m, l
                if m > th:
                    bi = 1 if (x > c) else 0
                    if abs(x - c) < abs(bests[d][bi] - c):
                        bests[d][bi] = x
            #print bests[d]

            # discard if crop is too small in dim d
            if (bests[d][1] - bests[d][0]) < (0.4 * dims[1]):
                bests[d] = defaults[:]

        # save relative boundaries in the image record
        def short_ratio(position, length, decimals=5):
            return round(1.0*position/length, decimals)
        boundaries = [
            [short_ratio(bests[1][0], dims[1]), short_ratio(bests[0][0], dims[0])],
            [short_ratio(bests[1][1], dims[1]), short_ratio(bests[0][1], dims[0])]
        ]
        print boundaries
        image.set_page_boundaries(boundaries)
        image.save()

        def get_margined(crop_points, dims, margin=2):
            margin = 2
            ret = [(max(crop_points[i][0] - margin, 0), min(crop_points[i][1] + margin, dims[i] - 1)) for i in [0, 1]]
            return ret

        # add margin to the boundaries
        bestsm = get_margined(bests, dims, margin=2)

        # create cropped image (with margin)
        path_out_cropped = '%s.cropped.png' % file_path
        img_cropped = img[bestsm[0][0]:bestsm[0][1], bestsm[1][0]:bestsm[1][1]]
        cv2.imwrite(path_out_cropped, img_cropped)

        # save uncropped image with red boundaries
        bests = get_margined(bests, dims, margin=0)
        img[:,bests[1]] = [0,0,255]
        img[bests[0],:] = [0,0,255]
        print '\t%s' % path_out
        #cv2.imwrite(path_out, res2)
        cv2.imwrite(path_out, img)

    def get_image_path(self, image, height):
        # returns a file path from the image model instance
        # image is downloaded from image server the first time
        ret = None

        dir_path = os.path.join(settings.IMAGE_SERVER_ROOT, 'tmp')
        if not os.path.exists(dir_path):
            print 'Create path'
            os.makedirs(dir_path)
        file_path = os.path.join(settings.IMAGE_SERVER_ROOT, 'tmp', 'i%s-h%s.jpg' % (image.id, height))
        if not os.path.exists(file_path):
            print 'Download image'
            url = image.thumbnail_url(height=height,uncropped=True)
            res = utils.web_fetch(url)
            if not res['error']:
                utils.write_file(file_path, res['body'])
            else:
                print 'ERROR downloading image %s' % res['error']

        if os.path.exists(file_path):
            ret = file_path

        return ret

    def update_dimensions(self, *args):
        options = self.options
        root = get_image_path()
        for file_info in self.get_all_files(root):
            if not self.is_filtered_in(file_info):
                continue
            if file_info['disk']:
                file_path = os.path.join(settings.IMAGE_SERVER_ROOT, file_info['image'].path())
                if os.path.exists(file_path):
                    file_info['image'].size = os.path.getsize(file_path)
            file_info['image'].dimensions()
            file_info['image'].save()

    def fetch(self, *args, **options):
        out_path = options['out_path']

        if len(args) > 1:
            base_url = args[1]
            i = 5177135
            # 5177311
            for i in range(5177218, 5177311 + 1):
                href = 'http://zzz/j2k/jpegNavMain.jsp?filename=Page%203&pid=' + str(i) + '&VIEWER_URL=/j2k/jpegNav.jsp?&img_size=best_fit&frameId=1&identifier=770&metsId=5176802&application=DIGITOOL-3&locale=en_US&mimetype=image/jpeg&DELIVERY_RULE_ID=770&hideLogo=true&compression=90'
                i += 1
                print i
                found = self.download_images_from_webpage(href, out_path, str(i) + '.jpg')
                if not found: break


    def fetch_old(self, *args, **options):
        '''
            fetch http://zzz//P3.html --links-file "bible1" --op=img1

            Will save all the jpg images found at that address into a directory called img1.
            We first download the index from that address then follow each link with a name listed in bible1 file.
            Download all all the jpg images found in those sub-pages.
        '''
        out_path = options['out_path']

        if len(args) > 1:
            url = args[1]
            print url

            if options['links']:
                links = options['links'].split(' ')

            if options['links_file']:
                f = open(options['links_file'], 'rb')
                links = f.readlines()
                f.close()
                links = [link.strip() for link in links]

            if links:
                html = utils.wget(url)
                if not html:
                    print 'ERROR: request to %s failed.' % url
                else:
                    for link in links:
                        print link
                        href = re.findall(ur'<a [^>]*href="([^"]*?)"[^>]*>\s*' + re.escape(link) + '\s*<', html)
                        if href:
                            href = href[0]
                            href = re.sub(ur'/[^/]*$', '/' + href, url)
                            print href

                            self.download_images_from_webpage(href, out_path)

    def download_images_from_webpage(self, href, out_path=None, img_name=None):
        ret = False
        print href
        sub_html = utils.wget(href)

        if not sub_html:
            print 'WARNING: request to %s failed.' % sub_html
        else:
            ret = True
            # get the jpg image in the page
            #image_urls = re.findall(ur'<img [^>]*src="([^"]*?\.jpg)"[^>]*>', sub_html)
            #print sub_html
            image_urls = re.findall(ur'<img [^>]*src\s*=\s*"([^"]*?)"[^>]*?>', sub_html)
            print image_urls
            for image_url in image_urls:
                if not image_url.startswith('/'):
                    image_url = re.sub(ur'/[^/]*$', '/' + image_url, href)
                else:
                    image_url = re.sub(ur'^(.*?//.*?/).*$', r'\1' + image_url, href)
                print image_url

                # get the image
                image = utils.wget(image_url)

                if not image:
                    print 'WARNING: request to %s failed.' % image_url
                else:
                    # save it
                    image_path = os.path.join(out_path, img_name or re.sub(ur'^.*/', '', image_url)) + ''
                    print image_path
                    utils.write_file(image_path, image)

        return ret

    def processOriginals(self, args, options):
        ''' List or copy the original images. '''
        import shutil
        command = args[0]

        original_path = get_originals_path()
        jp2_path = get_image_path()

        all_files = []

        # scan the originals folder to find all the image files there
        files = [join(original_path, f) for f in listdir(original_path)]
        while files:
            file = files.pop(0)

            file = join(original_path, file)

            if isfile(file):
                (file_base_name, extension) = os.path.splitext(file)
                if extension.lower() in settings.IMAGE_SERVER_UPLOAD_EXTENSIONS:
                    file_relative = os.path.relpath(file, original_path)

                    info = {
                            'disk': 1,
                            'path': file_relative
                            }

                    all_files.append(info)
            elif isdir(file):
                files.extend([join(file, f) for f in listdir(file)])

        # list or copy the files
        for file_info in all_files:
            file_relative = file_info['path']
            if not self.is_filtered_in(file_info):
                continue

            file_relative_normalised = self.getNormalisedPath(file_relative)
            (file_relative_base, extension) = os.path.splitext(file_relative)
            (file_relative_normalised_base, extension) = os.path.splitext(file_relative_normalised)

            copied = False

            target = join(jp2_path, file_relative_normalised_base + extension)

            if isfile(target) or \
                isfile(join(jp2_path, file_relative_normalised_base + settings.IMAGE_SERVER_EXT)) \
                :
                copied = True

            status = ''
            if copied: status = 'COPIED'
            print '[%6s] %s' % (status, file_relative)

            if command == 'pocket':
                import time
                from digipal.models import Image

                outpath = self.get_arg(1, '', 'You must specify an output path')
                quality = self.get_arg(2, 50)
                pause = self.get_arg(3, 0)

                iipimage = self.getNormalisedPath(re.sub(ur'[^.]+$', '', file_relative)).replace('\\', '/')
                recs = Image.objects.filter(iipimage__icontains=iipimage, item_part__isnull=False)
                rec = None

                fileout = file_relative

                if len(recs) > 1:
                    print 'WARNING: more than one image records for this file (%s)' % iipimage
                if len(recs) < 1:
                    print 'WARNING: image record not found (%s)' % iipimage
                else:
                    rec = recs[0]

                if rec:
                    fileout = self.getNormalisedPath('%s' % rec.display_label).lower() + '.jpg'

                filein = join(get_originals_path().replace('/', os.sep), file_relative)
                fileout = join(outpath, re.sub(ur'[^.]*$', 'jpg', os.path.basename(fileout)))
                if not os.path.exists(fileout):
                    cmd = 'convert -quiet -quality %s %s[0] %s' % (quality, filein, fileout)
                    if not self.is_dry_run():
                        ret_shell = self.run_shell_command(cmd)
                    else:
                        print cmd

                    time.sleep(float(pause))

            if command in ['copy', 'copy_convert']:
                # create the folders
                path = os.path.dirname(target)
                if not os.path.exists(path):
                    os.makedirs(path)

                # copy the file
                if command == 'copy':
                    print '\tCopy to %s' % target
                    shutil.copyfile(join(original_path, file_relative), target)

                if command == 'copy_convert':
                    # convert the file jp2
                    status = 'COPIED+CONVERTED'

                    from iipimage.storage import CONVERT_TO_TIFF, CONVERT_TO_JP2
                    shell_command = CONVERT_TO_JP2 % (join(original_path, file_relative), re.sub(ur'\.[^.]+$', ur'.'+settings.IMAGE_SERVER_EXT, target))
                    ret_shell = self.run_shell_command(shell_command)
                    if ret_shell:
                        status = 'CONVERSION ERROR: %s (command: %s)' % (ret_shell[0], ret_shell[1])

    def getNormalisedPath(self, path):
        from digipal.utils import get_normalised_path
        return get_normalised_path(path)

    def convert_image_deprecated(self, image):
        ret = None

        # normalise the image path and rename so iipimage server doesn't complain
        name = os.path.normpath(image.iipimage.name)
        path, basename = os.path.split(name)
        name = os.path.join(path, re.sub(r'(\s|,)+', '_' , basename.lower()))
        path, ext = os.path.splitext(name)
        name = path + ur'.' + settings.IMAGE_SERVER_EXT

        ret_shell = []

        # rename the file to .jp2
        if image.iipimage.name != name:
            try:
                os.rename(os.path.join(settings.IMAGE_SERVER_ROOT, image.iipimage.name), os.path.join(settings.IMAGE_SERVER_ROOT, name))
                image.iipimage.name = name
                image.save()
            except Exception, e:
                ret_shell = [e, 'rename']
        else:
            # assume the file is already a jpeg 2k, return
            #return ret
            pass

        # convert the image to tiff
        if not ret_shell:
            from iipimage.storage import CONVERT_TO_TIFF, CONVERT_TO_JP2

            full_path = os.path.join(settings.IMAGE_SERVER_ROOT, image.iipimage.name)
            temp_file = full_path + '.tmp.tiff'

            command = CONVERT_TO_TIFF % (full_path, temp_file)
            ret_shell = self.run_shell_command(command)

        # convert the image to jp2
        if not ret_shell:
            command = CONVERT_TO_JP2 % (temp_file, full_path)
            ret_shell = self.run_shell_command(command)

        if ret_shell:
            ret = '[CONVERSION ERROR: %s (command: %s)]' % (ret_shell[0], ret_shell[1])

        # remove the tiff file
        try:
            os.remove(temp_file)
        except:
            pass

        return ret

    def convert_image(self, image):
        ret = None

        # normalise the image path so iipimage server doesn't complain
        name_src = name = os.path.normpath(image.iipimage.name)

        path, basename = os.path.split(name)
        name = os.path.join(path, re.sub(r'(\s|,)+', '_' , basename.lower()))
        path_name, ext = os.path.splitext(name)

        name_tmp = path_name + ur'.tmp.bmp'

        name_dst = path_name + ur'.' + settings.IMAGE_SERVER_EXT

        def absp(rel_path):
            return os.path.join(settings.IMAGE_SERVER_ROOT, rel_path)

        dir_path = absp(path)

        ret_shell = []

        if name_src != name_dst:

            # 1. convert the image to temporary format
            # kdu_compress is sensitive to some TIFF but never complained about BMP
            ret_shell = self.run_shell_command('convert -quiet %s -compress None %s' % (absp(name_src), absp(name_tmp)))

            if not ret_shell:
                # we take the largest output from that conversion
                # in case the source had multiple images (each comverted into separate bmps)
                # name_tmp = the rel path to the largest tmp file
                max_size = 0
                for f in listdir(dir_path):
                    if f.endswith('.bmp') and '.tmp' in f:
                        size = os.path.getsize(os.path.join(dir_path, f))
                        if size > max_size:
                            max_size = size
                            name_tmp = os.path.join(path, f)

                # 2. convert the tmp image to target format (pyramidal and 256-tiled)
                if max_size:
                    from iipimage.storage import CONVERT_TO_JP2
                    CONVERT_TO_JP2 = CONVERT_TO_JP2.replace('kdu_compress', 'kdu_compress -quiet')
                    command = CONVERT_TO_JP2 % (absp(name_tmp), absp(name_dst))
                    ret_shell = self.run_shell_command(command)

        # convert error message from command line error (if any)
        if ret_shell:
            ret = '[CONVERSION ERROR: %s (command: %s)]' % (ret_shell[0], ret_shell[1])

        # Remove the tmp files
        for f in listdir(dir_path):
            if f.endswith('.bmp') and '.tmp' in f:
                try:
                    os.remove(os.path.join(dir_path, f))
                except:
                    pass

        if not ret:
            #  update the file name in the image record
            image.iipimage.name = name_dst
            image.save()

            # Remove the src file (if conversion went well)
            if name_src != name_dst:
                try:
                    os.remove(absp(name_src))
                except:
                    pass

        return ret

    def run_shell_command(self, command):
        ret = None
        if self.get_verbosity() >= 2:
            print '\t' + command
        try:
            status = os.system(command)
            if status > 0:
                ret = [status, command]
        except Exception, e:
            #os.remove(input_path)
            #raise CommandError('Error executing command: %s (%s)' % (e, command))
            ret = [e, command]
        finally:
            # Tidy up by deleting the original image, regardless of
            # whether the conversion is successful or not.
            #os.remove(input_path)
            pass
        return ret

    def transform_image(self, image_info, operations):
        '''
        Runs a series of operations (image transform shell commands)
            on the jp2/tif image file pointed by image_info
            each intermediate output is saved into /tmp/dpim-X.EXT
            final output replaces the original file.
        image_info: an info structure like the ones returned by get_all_files()
        operations: a list of operations and their target filenames
            [['command {0} {1}', 'extension'], ...]
        '''
        ret = None

        path_src = os.path.join(settings.IMAGE_SERVER_ROOT, image_info['path'])
        path_original = path_src
        pid = os.getpid()
        for i, op in enumerate(operations):
            op[0] = op[0].replace('%s', '{}')
            ret = '/tmp/dpim-{}-{}.{}'.format(pid, i, op[1])
            if os.path.exists(ret): os.remove(ret)
            command = op[0].format(path_src, ret)
            ret_shell = self.run_shell_command(command)
            if ret_shell or not os.path.exists(ret):
                print('WARNING: Error during conversion %s' % ret_shell)
                ret = None
                break
            path_src = ret

        if ret:
            ret_ext = re.sub(r'^.*\.', r'.', ret)
            ret = re.sub(r'\.[^.]+$', ret_ext, path_original)
            image_info['path'] = ret
            image_info['image'].iipimage.name = re.sub(r'\.[^.]+$', ret_ext, image_info['image'].iipimage.name)

            # move the image
            import shutil
            shutil.move(path_src, ret)

            # update the image record (width & height) and save it
            dims = self.reset_image_dimensions(image_info)

            # remove original image
            if dims[0]*dims[1]:
                if path_original != ret:
                    os.remove(path_original)
            else:
                ret = None

        return ret

    def setdims(self):
        root = get_image_path()
        files = self.get_all_files(root)

        for info in files:
            if self.is_filtered_in(info) and info.get('disk', False) and info['image']:
                self.reset_image_dimensions(info)

    def reset_image_dimensions(self, image_info):
        '''reset .width & .height from the dimensions read from the file.
        Save updated Image record in the database.
        Returns new dimensions (width, height).
        On error: returns (0, 0) and don't save anything.
        '''
        dims = self.get_image_dimensions(image_info)
        if dims[0]:
            image_info['image'].width = dims[0]
            image_info['image'].height = dims[1]
            image_info['image'].save()

        return dims

    def get_image_dimensions(self, image_info):
        '''Returns (width, height)
        Method: imagemagick identify
        Why: because iipsrv caches the results and we need fresh values
        '''
        ret = (0, 0)

        out_file = '/tmp/dpim_identify.log'
        path = os.path.join(settings.IMAGE_SERVER_ROOT, image_info['path'])
        command = 'identify -quiet {}[0] > {}'.format(path, out_file)
        # images/pim/jp2/1.bmp[0]=>images/pim/jp2/1.bmp BMP 1100x1134 1100x1134+0+0 8-bit sRGB 3.742MB 0.000u 0:00.000
        ret_shell = self.run_shell_command(command)
        if ret_shell is None:
            content = utils.readFile(out_file)
            dimss = re.findall(r' (\d+)x(\d+)\b', content)
            if dimss:
                ret = [int(d) for d in dimss[0]]
        else:
            print('WARNING: can\'t read dimensions of {}'.format(path))

        return ret

    def enlarge(self):
        '''enlarge image width by 50px, and height to preserve aspect ratio.
        Transform the annotations accordingly.
        '''
        root = get_image_path()
        files = self.get_all_files(root)
        extra_size = 50

        for info in files:
            if self.is_filtered_in(info) and info.get('disk', False) and info['image']:
                operations = []
                print(info['image'].pk, info['path'])
                # jp2 -> tif
                if info['path'].endswith('.jp2'):
                    operations.append([
                        'opj_decompress -quiet -i {0} -OutFor TIF -o {1}',
                        'tif'
                    ])

                # tif -> png (resized)
                factor = 1 + (float(extra_size) / info['image'].width)
                dims = [
                    int(info['image'].width * factor),
                    int(info['image'].height * factor)
                ]
                operations.append([
                    'convert {0}[0] -resize %sx%s {1}' % (dims[0], dims[1]),
                    'png'
                ])

                # png -> tif/jp2
                operations.append([
                    self.get_convert_command(),
                    settings.IMAGE_SERVER_EXT
                ])

                res = self.transform_image(info, operations)

                if res:
                    # now transform the annotations
                    for a in info['image'].annotation_set.all():
                        path = a.get_shape_path()
                        for pair in path:
                            pair[0] = int(pair[0] * factor)
                            pair[1] = int(pair[1] * factor)
                        a.set_shape_path(path)
                        a.save()

    def get_convert_command(self):
        from iipimage.storage import CONVERT_TO_JP2
        ret = CONVERT_TO_JP2.replace(
            'kdu_compress', 'kdu_compress -quiet'
        )
        return ret

    def jp2tif(self):
        '''Converts jp2 images to tif.
        Useful when moving the a native/legacy archetype instance to
        a more modern/dockerise version.
        The tif files are compressed at 90 quality.
        They are layered and tiled.

        Method: opj_decompress for jp2 -> png
            then 'convert' for png to tif.
        We use png as an intermediate format because it works better than any
        other, including BMP (convert complains about bmp done by opj_compress).
        '''
        root = get_image_path()
        files = self.get_all_files(root)
        i = 0

        stats = {
            'total': 0,
            'converted': 0,
            'errors': 0,
        }

        from time import time

        for info in files:
            if self.is_filtered_in(info) and info.get('disk', False) and info['image'] and getattr(info['image'], 'pk') > 0:
                if not info['path'].endswith(settings.IMAGE_SERVER_EXT):
                    stats['total'] += 1
                    print(int(time()), stats['total'], info['image'].pk, info['path'])

                    operations = [
                        ['opj_decompress -quiet -i {} -OutFor TIF -o {}', 'png'],
                        [self.get_convert_command(), settings.IMAGE_SERVER_EXT],
                    ]
                    res = self.transform_image(info, operations)

                    if res:
                        stats['converted'] += 1
                    else:
                        stats['errors'] += 1

        print('SUMMARY: %s jp2, %s converted to tif, %s errors.' % (
            stats['total'],
            stats['converted'],
            stats['errors'],
        ))
