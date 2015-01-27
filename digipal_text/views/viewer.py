# -*- coding: utf-8 -*-
from digipal.models import *
from digipal_text.models import *
import re
from django import http, template
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy, ugettext as _
from django.utils.safestring import mark_safe
import htmlentitydefs
from django.core import urlresolvers
from digipal.forms import ScribeAdminForm, OnlyScribe
from django.forms.formsets import formset_factory
import json
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.db import transaction
from django.utils.datastructures import SortedDict
from django.http import Http404

import logging
dplog = logging.getLogger( 'digipal_debugger')


def text_viewer_view(request, item_partid=0):
    
    from digipal.models import ItemPart
    context = {'item_partid': item_partid, 'item_part': ItemPart.objects.filter(id=item_partid).first()}    
    
    return render(request, 'digipal_text/text_viewer.html', context)

def text_api_view(request, item_partid, content_type, location_type, location):
    import json
    
    # get the content
    from digipal_text.models import TextContentType, TextContent, TextContentXML
    from digipal.models import ItemPart
    content_type = TextContentType.objects.filter(slug=content_type).first()
    text_content_xml = None
    if content_type:
        print 'content type %s' % content_type
        item_part = ItemPart.objects.filter(id=item_partid).first()
        if item_part:
            print 'item_part %s' % item_part
            # get or create the TextContent
            text_content, created = TextContent.objects.get_or_create(item_part=item_part, type=content_type)
            # get or create the TextContentXML
            text_content_xml, created = TextContentXML.objects.get_or_create(text_content=text_content)
    
    if not text_content_xml:
        raise Exception('Content not found')
    
    content = request.REQUEST.get('content', None)
    if content:
        text_content_xml.content = content
        text_content_xml.save()
    else:
        content = text_content_xml.content
        if content is None:
            content = ''
    
    response = {'content': content}
    
    return HttpResponse(json.dumps(response), mimetype='application/json')
    