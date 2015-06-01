# -*- coding: utf-8 -*-
#from digipal_text.models import *
from digipal_text.models import TextContentXMLStatus, TextContent, TextContentXML
import re
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.db import transaction
from digipal import utils
from django.utils.datastructures import SortedDict

import logging
dplog = logging.getLogger( 'digipal_debugger')


def text_viewer_view(request, item_partid=0):
    
    from digipal.utils import is_model_visible
    if not is_model_visible('textcontentxml', request):
        raise Http404('Text view not enabled')
    
    from digipal.models import ItemPart
    context = {'item_partid': item_partid, 'item_part': ItemPart.objects.filter(id=item_partid).first()}
    
    # Define the content of content type and location type drop downs
    # on top of each panel
    context['dd_content_types'] = [
        {'key': 'transcription', 'label': 'Transcription', 'icon': 'align-left', 'attrs': [['data-class', 'Text']]},
        {'key': 'translation', 'label': 'Translation', 'icon': 'indent-left', 'attrs': [['data-class', 'Text']]},
        {'key': 'image', 'label': 'Image', 'icon': 'picture', 'attrs': [['data-class', 'Image']]},
    ]
    context['dd_location_types'] = [
        {'key': 'whole', 'label': 'Whole text', 'icon': 'book'},
        {'key': 'locus', 'label': 'Locus', 'icon': 'file'},
        {'key': 'entry', 'label': 'Entry', 'icon': 'entry'},
        {'key': 'section', 'label': 'Section', 'icon': 'section'},
        {'key': 'sync', 'label': 'Synchronise with', 'icon': 'magnet'},
    ]
    context['statuses'] = TextContentXMLStatus.objects.all().order_by('sort_order')
    
    update_viewer_context(context, request)
    
    return render(request, 'digipal_text/text_viewer.html', context)

def update_viewer_context(context, request):
    ''' To be overridden '''
    # TODO: design a better overriding model
    pass

def text_api_view(request, item_partid, content_type, location_type, location):
    
    from digipal.utils import is_model_visible
    if not is_model_visible('textcontentxml', request):
        raise Http404('Text view not enabled')

    response = None
    
    # delegate to a custom function if it exists
    
    # Look up the content_type in the function name
    # e.g. content_type = image => text_api_view_image
    function = globals().get('text_api_view_' + content_type,  None)
    
    if function:
        response = function(request, item_partid, content_type, location_type, location)
    else:
        # Look up the content_type in the TextContentType table
        # e.g. content_type = translation or transcription, we assume it must be a TextContentXML
        from digipal_text.models import TextContentType
        content_type_record = TextContentType.objects.filter(slug=content_type).first()
        
        if content_type_record:
            response = text_api_view_text(request, item_partid, content_type, location_type, location, content_type_record)
    
    # we didn't find a custom function for this content type
    if response is None:
        response = {'status': 'error', 'message': 'Invalid Content Type (%s)' % content_type}
    
    import json
    return HttpResponse(json.dumps(response), mimetype='application/json')

def text_api_view_text(request, item_partid, content_type, location_type, location, content_type_record):
    ret = {}
    
    max_fragment_size = 100000
    
    text_content_xml = None
    
    #print 'content type %s' % content_type_record
    # 1. Fetch or Create the necessary DB records to hold this text
    from digipal.models import ItemPart
    item_part = ItemPart.objects.filter(id=item_partid).first()
    if item_part:
        #print 'item_part %s' % item_part
        # get or create the TextContent
        with transaction.atomic():
            text_content, created = TextContent.objects.get_or_create(item_part=item_part, type=content_type_record)
            # get or create the TextContentXML
            text_content_xml, created = TextContentXML.objects.get_or_create(text_content=text_content)
    
    if not text_content_xml:
        ret['message'] = 'Content not found'
        ret['status'] = 'error'
        return ret

    record_content = text_content_xml.content or ''
    
    # 2. Load the list of possible location types and locations
    # return the locus of the entries
    if location_type == 'default' or utils.get_int_from_request_var(request, 'load_locations'):
        # whole
        ret['locations'] = SortedDict()
        
        # whole
        if len(record_content) <= max_fragment_size:
            ret['locations']['whole'] = []
        
        # entry
        for ltype in ['entry', 'locus']:
            ret['locations'][ltype] = []
            if text_content_xml.content:
                for entry in re.findall(ur'(?:<span data-dpt="location" data-dpt-loctype="'+ltype+'">)([^<]+)', text_content_xml.content):
                    ret['locations'][ltype].append(entry)
            if not ret['locations'][ltype]: del ret['locations'][ltype]
    
    # resolve 'default' location request
    location_type, location = resolve_default_location(location_type, location, ret)
            
    # 3. Save the user fragment
    new_fragment = request.REQUEST.get('content', None)
    
    convert = utils.get_int_from_request_var(request, 'convert')
    save_copy = utils.get_int_from_request_var(request, 'save_copy')
    
    ret['content_status'] = text_content_xml.status.id
    
    extent = get_fragment_extent(record_content, location_type, location)
    ret['message'] = ''
    dry_run = 0
    if extent:
        # make sure we compare with None, as '' is a different case
        if new_fragment is not None:
            ret['message'] = 'Content saved'

            # insert user fragment
            len_previous_record_content = len(record_content)
            # TODO: UNCOMMENT!!!!!!!!!!!!!!!!!!!!!!!!!!
            if not dry_run:
                record_content = record_content[0:extent[0]]+new_fragment+record_content[extent[1]:]
    
            # we make a copy if the new content removes 10% of the content
            # this might be due to a bug in the UI
            if len(record_content) < (0.9 * len_previous_record_content):
                print 'Auto copy (smaller content)'
                text_content_xml.save_copy()
                
            # set the new content
            text_content_xml.content = record_content
            
            # auto-markup
            if convert:
                text_content_xml.convert()
                record_content = text_content_xml.content
                ret['message'] = 'Content converted and saved'
            
            # make a copy if user asked for it
            if save_copy:
                text_content_xml.save_copy()
                ret['message'] = 'Content backed up'
            
            # save the new content
            # TODO: UNCOMMENT!!!!!!!!!!!!!!!!!!!!!!!!!!
            if not dry_run:
                text_content_xml.save()
            
            # update the extent
            # note that extent can fail now if the user has remove the marker for the current location
            extent = get_fragment_extent(record_content, location_type, location)

    # 4. now the loading part (we do it in any case, even if saved first)
    if not extent:
        if ret['message']:
            ret['message'] += ' then '
        ret['message'] += 'location not found: %s %s' % (location_type, location)
        ret['status'] = 'error'
    else:
        if (extent[1] - extent[0]) > max_fragment_size:
            if ret['message']:
                ret['message'] += ' then '
            ret['message'] += 'text too long (> %s bytes)' % (max_fragment_size)
            ret['status'] = 'error'
        else:
            ret['content'] = record_content[extent[0]:extent[1]]
            if new_fragment is None:
                ret['message'] = 'Content loaded'

    # we return the location of the returned fragment
    # this may not be the same as the requested location
    # e.g. if the requested location is 'default' we resolve it
    ret['location_type'] = location_type
    ret['location'] = location
        
    return ret

def resolve_default_location(location_type, location, response):
    if location_type == 'default':
        locations = response['locations']
        # grab the first available location
        for ltype in locations.keys():
            location_type = ltype
            location = ''
            if locations[ltype]:
                location = locations[ltype][0]
            break
    return location_type, location

def get_fragment_extent(content, location_type, location):
    ret = None
    
    content = content or ''
    
    if location_type == 'whole':
        ret = [0, len(content)]
    else:
        # extract the requested fragment
        # ASSUMES: root > p > span
        # ASSUME order of the attributes in the span (OK)
        # ... <p> </p> <p>...<span data-dpt="location" data-dpt-loctype="locus">1r</span>...</p> <p> </p> ... <p> <span data-dpt="location" data-dpt-loctype="locus">1r</span>
        span0 = content.find('<span data-dpt="location" data-dpt-loctype="'+location_type+'">'+location+'<')
        if span0 > -1:
            p0 = content.rfind('<p>', 0, span0)
            if p0 > -1:
                span1 = content.find('<span data-dpt="location" data-dpt-loctype="'+location_type+'">', span0 + 1)
                if span1 == -1:
                    ret = [p0, len(content)]
                else:
                    p1 = content.find('</p>', span1)
                    ret = [p0, p1]

    return ret

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
    if location_type == 'default' or utils.get_int_from_request_var(request, 'load_locations'):
        ret['locations'] = SortedDict()
        ret['locations']['locus'] = ['%s' % (rec[0] or '#%s' % rec[1]) for rec in Image.sort_query_set_by_locus(Image.objects.filter(item_part_id=item_partid)).values_list('locus', 'id')]

    # resolve 'default' location request
    location_type, location = resolve_default_location(location_type, location, ret)
        
    # find the image
    image = None
    if location:
        imageid = re.sub(ur'^#(\d+)$', ur'\1', location)
        if imageid and imageid != location:
            # e.g. location = #100
            image = Image.objects.filter(id=imageid).first()
        else:
            # e.g. location = 13r
            image = Image.objects.filter(item_part_id=item_partid, locus=location).first()
            
            # e.g. location = 54b2 (entry number)
            # => convert to 54v
            if not image:
                locus = get_locus_from_location(location_type, location)
                if locus:
                    image = Image.objects.filter(item_part_id=item_partid, locus=locus).first()
    
    # Image not found, display the first one
    if not image:
        image = Image.objects.filter(item_part_id=item_partid).first()
    
    # image dimensions
    options = {}
    layout = request.REQUEST.get('layout', '')
    if layout == 'width':
        options['width'] = request.REQUEST.get('width', '100')
    
    # we return the location of the returned fragment
    # this may not be the same as the requested location
    # e.g. if the requested location is 'default' we resolve it
    ret['location_type'] = location_type
    ret['location'] = location

    #ret['content'] = iip_img(image, **options)
    ret['zoomify_url'] = image.zoomify()
    ret['width'] = image.width
    ret['height'] = image.height
    
    return ret

def get_locus_from_location(location_type, location):
    ret = None
    
    # e.g. location = 54b2 (entry number)
    # => convert to 54v
    # TODO: check location_type
    # TODOL this is a customisation for EXON,
    # unlikely to be relevant for other projects
    parts = re.match('(\d+)([abrv]?)(\d*)', location)
    if parts:
        number = parts.group(1)
        side = 'r'
        if parts.group(2) and parts.group(2) == 'b': side = 'v'
        ret = number+side
        
    return ret

def text_api_view_search(request, item_partid, content_type, location_type, location):
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
    if location_type == 'default' or utils.get_int_from_request_var(request, 'load_locations'):
        ret['locations'] = SortedDict()
        ret['locations']['locus'] = ['%s' % (rec[0] or '#%s' % rec[1]) for rec in Image.sort_query_set_by_locus(Image.objects.filter(item_part_id=item_partid)).values_list('locus', 'id')]

    # resolve 'default' location request
    location_type, location = resolve_default_location(location_type, location, ret)
    
    query = request.REQUEST.get('query', '')
    entries = ''
    hit_count = 0
    if query:
        tcx = TextContentXML.objects.filter(text_content__type__slug='translation', text_content__item_part__id=item_partid).first()
        if tcx:
            for hit in get_entries_from_query(query):
                hit_count += 1
                entries += '<li><a data-location-type="entry" href="%s">%s</a><br/>%s</li>' % (hit['entryid'], hit['entryid'], hit['snippets'])
            
            #import re
            #match = re.search()
            #tcx.content
            #print tcx
        
    # e.g. if the requested location is 'default' we resolve it
    from django.utils.html import escape
    ret['location_type'] = location_type
    ret['location'] = location

    ret['content'] = ur'''<form class="text-search-form" method="GET">
        <p>Query: <input type="text" name="query" value="%s"/><input type="submit" name="s" value="Search"/></p>
        <p>%s entries</p>
        <ul>
            %s
        </ul>
    </form>''' % (escape(query), hit_count, entries)
    
    return ret

def get_entries_from_query(query):

    # run the query with Whoosh
    from django.conf import settings
    from whoosh.index import open_dir
    import os
    index = open_dir(os.path.join(settings.SEARCH_INDEX_PATH, 'faceted', 'textunits'))

    #from whoosh.qparser import QueryParser
    
    search_phrase = query
    
    # make the query
    # get the field=value query from the selected facet options
    field_queries = u''
    
    # add the search phrase
    if search_phrase or field_queries:
        qp = get_whoosh_parser(index)
        q = qp.parse(u'%s %s' % (search_phrase, field_queries))
    else:
        from whoosh.query.qcore import Every
        q = Every()
           
    ret = []
    
    with index.searcher() as s:
        # run the query
        #facets = self.get_whoosh_facets()

        hits = s.search(q, limit=1000000, sortedby='entryid_sortable')
        hits.fragmenter.charlimit = None
        
        # get highlights from the hits
        for hit in hits:
            ret.append({'entryid': hit['entryid'], 'snippets': hit.highlights('content', top=10)})
        #print '%s hits.' % len(hits)
                
    return ret

def get_whoosh_parser(index):
    from whoosh.qparser import MultifieldParser, GtLtPlugin
    
    # TODO: only active columns
    term_fields = ['content', 'entryid']
    parser = MultifieldParser(term_fields, index.schema)
    parser.add_plugin(GtLtPlugin)
    return parser

