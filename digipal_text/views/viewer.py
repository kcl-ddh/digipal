# -*- coding: utf-8 -*-
from digipal_text.models import *
import re
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils.safestring import mark_safe
from django.core import urlresolvers
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.db import transaction
from django.http import Http404
from digipal import utils

import logging
dplog = logging.getLogger( 'digipal_debugger')


def text_viewer_view(request, item_partid=0):
    
    from digipal.models import ItemPart
    context = {'item_partid': item_partid, 'item_part': ItemPart.objects.filter(id=item_partid).first()}
    
    return render(request, 'digipal_text/text_viewer.html', context)

def text_api_view(request, item_partid, content_type, location_type, location):
    response = None
    
    # delegate to a custom function if it exists
    
    # Look up the content_type in the function name
    # e.g. text_api_view_image
    function = globals().get('text_api_view_' + content_type,  None)
    
    # Look up the content_type in the TextContentType table
    if function:
        response = function(request, item_partid, content_type, location_type, location)
    else:
        from digipal_text.models import TextContentType
        content_type_record = TextContentType.objects.filter(slug=content_type).first()
        
        if content_type_record:
            response = text_api_view_text(request, item_partid, content_type, location_type, location, content_type_record)
    
    # we didn't find a custom function for this content type
    if response is None:
        response = {'content': '', 'error': 'Invalid Content Type (%s)' % content_type}
    
    import json
    return HttpResponse(json.dumps(response), mimetype='application/json')

def text_api_view_text(request, item_partid, content_type, location_type, location, content_type_record):
    text_content_xml = None
    
    #print 'content type %s' % content_type_record
    from digipal.models import ItemPart
    item_part = ItemPart.objects.filter(id=item_partid).first()
    if item_part:
        #print 'item_part %s' % item_part
        # get or create the TextContent
        from digipal_text.models import TextContent, TextContentXML
        text_content, created = TextContent.objects.get_or_create(item_part=item_part, type=content_type_record)
        # get or create the TextContentXML
        text_content_xml, created = TextContentXML.objects.get_or_create(text_content=text_content)
    
    if not text_content_xml:
        raise Exception('Content not found')
    
    content = request.REQUEST.get('content', None)
    
    # we make a copy if the new content removes 10% of the content
    # this might be due to a bug in the UI
    from django.utils.html import strip_tags
    #if not re.search(ur'\w', strip_tags(content)):

    if (content is not None) and text_content_xml.content and (len(content) < 0.9 * len(text_content_xml.content)):
        print 'Auto copy (blank content)'
        text_content_xml.save_copy()
        
    # now save the new content
    convert = utils.get_int_from_request_var(request, 'convert')
    save_copy = utils.get_int_from_request_var(request, 'save_copy')
    
    if content is not None:
        text_content_xml.content = content
        if convert:
            text_content_xml.convert()
            content = text_content_xml.content
        # make a copy if user asked for it
        if save_copy:
            text_content_xml.save_copy()
        text_content_xml.save()
    else:
        content = text_content_xml.content
        if content is None:
            content = ''
    
    return {'content': content}

def text_api_view_image(request, item_partid, content_type, location_type, location):
    '''
        location = an identifier for the image. Relative to the item part
                    '#1000' => image with id = 1000
                    '1r'    => image with locus = 1r attached to selected item part
    '''
    ret = {}
    
    from digipal.templatetags.html_escape import iip_img
    from digipal.models import Image
    
    # return the locus of the images under this item part
    # return #ID for images which have no locus
    if utils.get_int(request.REQUEST.get('load_locations', 0)):
        ret['locations'] = ['%s' % (rec[0] or '#%s' % rec[1]) for rec in Image.sort_query_set_by_locus(Image.objects.filter(item_part_id=item_partid)).values_list('locus', 'id')]
        
    # find the image
    image = None
    if location:
        imageid = re.sub(ur'^#(\d+)$', ur'\1', location)
        if imageid and imageid != location:
            image = Image.objects.filter(id=imageid).first()
        else:
            image = Image.objects.filter(item_part_id=item_partid, locus=location).first()
    if not image:
        image = Image.objects.filter(item_part_id=item_partid).first()
    
    # image dimensions
    options = {}
    layout = request.REQUEST.get('layout', '')
    if layout == 'width':
        options['width'] = request.REQUEST.get('width', '100')
    
    ret['content'] = iip_img(image, **options)
    
    return ret

