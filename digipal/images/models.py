from mezzanine.conf import settings
import os
import digipal.models
from django.db import transaction
from django.utils.text import slugify


class Image(digipal.models.Image):
    '''
    Extension of digipal.models.Image that offers more advanced operations to work with the images files and URLs.
    '''
    
    class Meta:
        proxy = True

    def get_img_size(self):
        ''' Returns the size of the full res. image as a list: [width, height] '''
        return self.dimensions()
        
        
        cached_sizes = getattr(self, 'cached_sizes', {})

        url = self.iipimage.full_base_url+'&OBJ=Max-size'
        if url not in cached_sizes:
            cached_sizes[url] = [0, 0]
            from digipal.management.commands.utils import web_fetch
            res = web_fetch(url)
            if not res['error']:
                import re
                matches = re.match(r'^.*?Max-size:(\d+)\s+(\d+).*?$', res['body'].strip())
                if matches:
                    cached_sizes[url] = [int(matches.group(1)), int(matches.group(2))]
    
            self.cached_sizes = cached_sizes
        
        return cached_sizes[url]
        
    def get_pil_img(self, ratio=1.0, cache=False, query='&QLT=100&CVT=JPG', grey=False):
        '''
            return a PIl image from the digipal image
            if not in cache, download from the image server
            
            The image returned by the image server may have different 
            dimensions than the one requested.
            This function will update actual_ratios with the actual X 
            and Y ratios.
        '''
        if ratio != 1.0:
            size = self.get_img_size()
            query = '&WID=%s&HEI=%s&%s' % (int(size[0] * ratio + 0.5), int(size[1] * ratio + 0.5), query)
        
        from django.utils.html import escape
        url = escape(self.iipimage.full_base_url)+query

        ret = self.get_pil_img_from_url(url, cache, grey)

        return ret

    @classmethod
    def get_pil_img_from_url(cls, url, cache=False, grey=False):
        '''
            Returns a PIL image instance from an image resource at the given URL
            cache=True to cache subsequent calls
            grey=True to return a greyscale image
        '''
        #print url
        ret = None
        from django.template.defaultfilters import slugify
        disk_path = os.path.join(settings.IMAGE_CACHE_ROOT, '%s.jpg' % slugify(url))
        if not cache or not os.path.exists(disk_path):
            from digipal.management.commands.utils import web_fetch, write_file
            #print '\tDL: %s' % url
            res = web_fetch(url)
            if res['body']:
                write_file(disk_path, res['body'])
    
        if os.path.exists(disk_path):        
            from PIL import Image
            ret = Image.open(disk_path)
            if grey:
                ret = ret.convert('L')
        
        # We resize the image to the requested size
        asked = []
        import re
        for d in [u'WID', u'HEI']:
            l = re.sub(ur'.*' + re.escape(d) + ur'=(\d+).*', ur'\1', url)
            if l != url:
                asked.append(int(l))
        if len(asked) == 2:
            import PIL
            ret = ret.resize(asked, PIL.Image.ANTIALIAS) 
        
        return ret
    
    def get_relative_coordinates(self, rgn):
        '''Returns relative coordinates from abolsute ones.
        Both the input and out have this format ((x0, y0), (x1, y1))
        which are the coordinates of the top left and bottom right corners'''
        size = self.get_img_size()
        ret = [
            [1.0 * rgn[0][0] / size[0], 1.0 * rgn[0][1] / size[1]], 
            [1.0 * (rgn[1][0] - rgn[0][0]) / size[0], 1.0 * (rgn[1][1] - rgn[0][1]) / size[1]] 
        ]
        return ret

    @classmethod
    def get_annotation_coordinates(cls, ann, annotation_image=None):
        ''' 
            Same as Annotation.get_coordinates() but return y values relative 
            to the TOP of the image. 
            
            annotation_image is optional, can be provided to avoid additional 
            request to get the image size
        '''
        ret = ann.get_coordinates()
        if not isinstance(annotation_image, Image):
            annotation_image = cls.from_digipal_image(ann.image)
        height = annotation_image.get_img_size()[1]
        return [[ret[0][0], height - ret[1][1]], [ret[1][0], height - ret[0][1]]]

    @classmethod
    def find_offsets_from_pil_images(cls, im_big, im_small, save=False):
        '''
            Input: two PIL images, the second if a crop of the first
            Returns (x, y), the offsets of the crop
        '''
        from PIL import ImageChops
        ims = [im_big, im_small]
        best = None
        #print '---'
        for x in range(0, ims[0].size[0] - ims[1].size[0] + 1):
            for y in range(0, ims[0].size[1] - ims[1].size[1] + 1):
                diff = ImageChops.difference(ims[0].crop((x + 0, y + 0, x + ims[1].size[0] - 1, y + ims[1].size[1] - 1)), ims[1])
                current = [
                    x, 
                    y, 
                    reduce(lambda a, b: a * 2 + b, diff.histogram()[::-1])
                ]
                #print '%3d, %3d : %60d' % (current[0], current[1], current[2]) 
                if (best is None) or (best[2] > current[2]):
                    best = current
                    if 0 and save:
                        print best

        save = 1
        if best and save:
            imcmb = im_big.convert('RGBA')
            #print repr(best[0:2])
            imcmb.paste(im_small.convert('RGBA'), box=tuple(best[0:2]))
            #imcmb = Image.alpha_composite(base, over)
            filename = slugify(unicode(repr(im_big.size) + repr(im_small.size)))
            disk_path = os.path.join(settings.IMAGE_CACHE_ROOT, '%s.jpg' % filename)
            imcmb.save(disk_path)
            #print 'saved %s' % disk_path
        
        #print 'offset'
        #print repr(best)
        
        return best[0:2]
    
    @classmethod
    def from_digipal_image(cls, digipal_image):
        if isinstance(digipal_image, digipal.models.Image):
            return Image.objects.get(id=digipal_image.id)
        if isinstance(digipal_image, Image):
            return digipal_image
        return None
    
    @transaction.atomic
    def replace_image_and_update_annotations(self, offsets, new_image):
        ret = True
        
        old_image_size = self.get_img_size()
        new_image = Image.from_digipal_image(new_image)
        new_image_size = new_image.get_img_size()
        
        self.iipimage = new_image.iipimage
        self.save()
        
        annotations = self.annotation_set.filter().distinct()
        if annotations.count():
            for annotation in annotations:
                print 'translate annotation #%s' % annotation.id
                annotation.geo_json = self.get_uncropped_geo_json(annotation, offsets, new_image_size, old_image_size)
                annotation.save()
        
        return ret
    
    def get_uncropped_geo_json(self, annotation, offsets=[0,0], image_size=[0,0], old_image_size=[0,0]):
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
            c[0] = int(c[0] + offsets[0])
            c[1] = int(image_size[1] + c[1] - old_image_size[1] - offsets[1])
            # y2 = h2 + y1 - h1 - offsety
            #print c[0], image_size[1] - c[1]
        
        # convert the coordinates
        ret = json.dumps(geo_json)
        
        return ret
    
    def compare_with(self, image2, downsample_ratio = 35.0):
        ret = {'scale': float(downsample_ratio), 'offsets': [0, 0]}

        digipal_images = [self, Image.from_digipal_image(image2)]
        
        # Get PIL images of the thumbnails
        ims = []
        for image in digipal_images:
            ims.append(image.get_pil_img(1.0/downsample_ratio, cache=True, grey=True))

        # Make sure the largest image is ims[0]
        sgn = -1
        reverse_order = False
        if ims[0].size[0] < ims[1].size[0]:
            sgn = 1
            ims = ims[::-1]
            digipal_images = digipal_images[::-1]
            reverse_order = True
        
        # -------------------
        # Step 1: Find the approximate crop offset using thumbnails 
        # -------------------
        offsets = self.find_offsets_from_pil_images(ims[0], ims[1])
        
        if offsets is None:
            return ret

        # convert the offset from the thumbnail size to the full size
        ret['offsets'] = [offset * downsample_ratio * sgn for offset in offsets]
        
        return ret
    
    def get_annotation_offset(self, ann, image2, diff):
        ret = {'scale': float(1), 'offsets': [0, 0], 'urls': []}
        
        # absolute max is 800 b/c image server won't return anything above that
        # now anything above 400 may be a bit too slow.
        # TODO: use this value
        max_sample_width = 400 
        
        # Calculate the search region (region_search):
        # start from the coordinates of the annotation in the first image (region)
        region = self.get_annotation_coordinates(ann, self)
        
        # 1 is original size in pixel of the annotation
        # But reduce to save time and not to show too big annotation on 
        # front end and avoid exceding image server limit
        ann_info = ann.get_cutout_url_info(fixlen=1.0/ret['scale'])
        #print ann.geo_json
        #print ann.get_cutout_url(fixlen=sample_factor)
        #print region
        
        # transpose the region in the new image using the approximate offsets
        region_search = [[point[0] + diff['offsets'][0], point[1] + diff['offsets'][1]] for point in region]
        
        # extend the search region by downsample_ratio/2 pixels in every direction 
        # (due to approximation of the first step - every pixel in thumbnail = 
        # downsample_ratio pixels in the original)
        #
        # Now add a bit more to that because of the rounding errors when asking for the 
        # thumbnail dimensions and other possible source of perturbation.
        # We take 50% (* 1.5) safety margin more on each side
        #
        safety_margin = 2.5
        search_margin = int((diff['scale'] / 2.0) * safety_margin + 0.5)
        region_search = [
            [region_search[0][0] - search_margin, region_search[0][1] - search_margin], 
            [region_search[1][0] + search_margin, region_search[1][1] + search_margin], 
        ]
        region_search_width = (region_search[1][0] - region_search[0][0])
        
        

        #print 'region search'
        #print region_search
        
        
        # Get the two images (annotation and search region) as PIL objects
        ann_im = self.get_pil_img_from_url(ann_info['url'], grey=True, cache=True)
        
        # iip img server only accepts relative coordinates, so convert them into relatives
        region_search_relative = image2.get_relative_coordinates(region_search)
        rgn_im = image2.get_pil_img( 
            query='&WID=%s&RGN=%1.6f,%1.6f,%1.6f,%1.6f&QLT=100&CVT=JPG' % (
                int(region_search_width / ret['scale']),
                region_search_relative[0][0], 
                region_search_relative[0][1], 
                region_search_relative[1][0], 
                region_search_relative[1][1]
            )
            , grey=True
            , cache=True
        )
        
        # Find the offsets by systematically looking for a match of the annotation within 
        # the search region
        offsets = self.find_offsets_from_pil_images(rgn_im, ann_im, save=True)
        
        # multiplying factor
        offsets = [int(v * ret['scale']) for v in offsets]
        
        # Now add local offset to the global estimate
        ret['offsets'] = [int(offsets[i] + diff['offsets'][i] - search_margin) for i in [0, 1]]
        
        # Get the URL of the reference annotation and the matching one in the other image
        ret['urls'].append(ann_info['url'])
         
        ret_relative = image2.get_relative_coordinates([[region[0][0] + ret['offsets'][0], region[0][1] + ret['offsets'][1]], [region[1][0] + ret['offsets'][0], region[1][1] + ret['offsets'][1]]])
        ret['urls'].append(image2.iipimage.full_base_url + \
            '&WID=%s&RGN=%1.6f,%1.6f,%1.6f,%1.6f&QLT=100&CVT=JPG' % (
                int(ann_info['dims'][0]),
                ret_relative[0][0], 
                ret_relative[0][1], 
                ret_relative[1][0], 
                ret_relative[1][1]
            )
        )
            
        return ret

    def find_image_offset(self, image2, downsample_ratio = 35.0):
        '''    
            Find and returns the crop offset and two sample annotations.
            
            return = {'offsets': [x,y], 'annotations': [a1, a2]}
            (x, y), how much do we have to move image1 to match image2
            a1 is the URL of one annotation, a2 the URL of the matching 
                annotation in the other image
            
            The offset is found using this tow-steps method:
            
            1. obtains a thumbnail of the images and use PIL to 
                scan all possible offsets and return the best match.
                Note that this is an approximate offset due to
                the downsampling made for creating the thumbnails. 
                
            2. the approximate is then refined by applying the same
                PIL matching operation on one annotation cutout from
                one image and the region where we expect to find it
                in the other image. 
                
                The smaller the thumbnail in step 1, the larger the
                search region in this step. 
                
            downsample_ratio specifies how small the thumbnail is compared
            to the original. Value above 35 may cause problems with our 
            images as the approximation in the first stage will be excessive.
        '''
        
        ret = {'offsets': [0,0], 'annotations': []}
        
        ans = self.annotation_set.exclude(type='text').order_by('?')
        
        diff = self.compare_with(image2)
        print diff
        limit = 5
        for an in ans[:limit]:
            print '#%s, %s' % (an.id, an)
            info = self.get_annotation_offset(an, image2, diff)
            ret['annotations'] += info['urls']
            ret['offsets'] = info['offsets']

        return ret
            
                    
    def find_image_offset_bk(self, image2, downsample_ratio = 35.0):
        '''    
            Find and returns the crop offset and two sample annotations.
            
            return = {'offsets': [x,y], 'annotations': [a1, a2]}
            (x, y), how much do we have to move image1 to match image2
            a1 is the URL of one annotation, a2 the URL of the matching 
                annotation in the other image
            
            The offset is found using this tow-steps method:
            
            1. obtains a thumbnail of the images and use PIL to 
                scan all possible offsets and return the best match.
                Note that this is an approximate offset due to
                the downsampling made for creating the thumbnails. 
                
            2. the approximate is then refined by applying the same
                PIL matching operation on one annotation cutout from
                one image and the region where we expect to find it
                in the other image. 
                
                The smaller the thumbnail in step 1, the larger the
                search region in this step. 
                
            downsample_ratio specifies how small the thumbnail is compared
            to the original. Value above 35 may cause problems with our 
            images as the approximation in the first stage will be excessive.
        '''
        
        ret = {'offsets': [0,0], 'annotations': []}
        
        if self.annotation_set.count() + image2.annotation_set.count() == 0:
            return ret

        # ...
        
        # -------------------
        # Step 2: Compare an annotation from one image with the containing region in the other image
        # -------------------
        
        # get one annotation (ann)
        ann = None
        deterministic = False
        for annotation_image_index in range(0, 2):
            anns = digipal_images[annotation_image_index].annotation_set.exclude(type='text')
            anns = anns.order_by('id' if deterministic else '?')
            if anns.count():
                ann = anns[0]
                from digipal.models import Annotation
                ann = Annotation.objects.get(id=123)
                break
        
        #print ann.id
        

        
        # Calculate the search region (region_search):
        # start from the coordinates of the annotation in the first image (region)
        region = self.get_annotation_coordinates(ann, digipal_images[annotation_image_index])

        #print 'ann'        
        # 1 is original size in pixel of the annotation
        # But reduce to save time and not to show too big annotation on 
        # front end and avoid exceding image server limit
        sample_factor = 0.5
        ann_info = ann.get_cutout_url_info(fixlen=sample_factor)
        #print ann.geo_json
        #print ann.get_cutout_url(fixlen=sample_factor)
        #print region
        
        region_search = []
        sign = 1
        if annotation_image_index == 0:
            sign = -1
        for pair in region:
            region_search.append([pair[0] + ret['offsets'][0] * sign, pair[1] + ret['offsets'][1] * sign])
        
        # extend the search region by downsample_ratio/2 pixels in every direction 
        # (due to approximation of the first step - every pixel in thumbnail = 
        # downsample_ratio pixels in the original)
        #
        # Now add a bit more to that because of the rounding errors when asking for the 
        # thumbnail dimensions and other possible source of perturbation.
        # We take 50% (* 1.5) safety margin more on each side
        #
        safety_margin = 2.5
        search_margin = int((downsample_ratio / 2.0) * safety_margin + 0.5)
        region_search = [
            [region_search[0][0] - search_margin, region_search[0][1] - search_margin], 
            [region_search[1][0] + search_margin, region_search[1][1] + search_margin], 
        ]
        region_search_width = (region_search[1][0] - region_search[0][0])

        #print 'region search'
        #print region_search
        
        # iip img server only accepts relative coordinates, so convert them into relatives
        region_search_relative = digipal_images[1-annotation_image_index].get_relative_coordinates(region_search)
        
        # Get the two images (annotation and search region) as PIL objects
        ann_im = self.get_pil_img_from_url(ann.get_cutout_url(fixlen=sample_factor), grey=True, cache=True)
        rgn_im = digipal_images[1-annotation_image_index].get_pil_img( 
            query='&WID=%s&RGN=%1.6f,%1.6f,%1.6f,%1.6f&QLT=100&CVT=JPG' % (
                int(sample_factor*region_search_width),
                region_search_relative[0][0], 
                region_search_relative[0][1], 
                region_search_relative[1][0], 
                region_search_relative[1][1]
            )
            , grey=True
            , cache=True
        )
        
        # Find the offsets by systematically looking for a match of the annotation within 
        # the search region
        #print ann_im
        #print rgn_im
        offsets = self.find_offsets_from_pil_images(rgn_im, ann_im, save=True)
        
        # multiplying factor
        offsets = [int(v / sample_factor) for v in offsets]
        
        print 'offsets'
        print offsets
        
        # Now add local offset to the global estimate
        ret['offsets'] = [offsets[0] + ret['offsets'][0] - search_margin, offsets[1] + ret['offsets'][1] - search_margin]
        
        # Get the URL of the reference annotation and the matching one in the other image 
        ret_relative = digipal_images[1-annotation_image_index].get_relative_coordinates([[region[0][0] + ret['offsets'][0], region[0][1] + ret['offsets'][1]], [region[1][0] + ret['offsets'][0], region[1][1] + ret['offsets'][1]]])
        ann_img_2_url = digipal_images[1-annotation_image_index].iipimage.full_base_url + \
            '&WID=%s&RGN=%1.6f,%1.6f,%1.6f,%1.6f&QLT=100&CVT=JPG' % (
                int(ann_info['dims'][0]),
                ret_relative[0][0], 
                ret_relative[0][1], 
                ret_relative[1][0], 
                ret_relative[1][1]
            )

        ret['annotations'] = [ann.get_cutout_url(fixlen=sample_factor), ann_img_2_url]
        
        # Adjust the crop signs
        if not reverse_order:
            ret['offsets'] = [-ret['offsets'][0], -ret['offsets'][1]]


        return ret    

    