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


def text_edit_view(request, item_partid=0, type=''):
    
    if not type:
        type = TextContentType.objects.first()
        if not type:
            type = TextContentType(name='Transcription')
            type.save()
        # now redirect
        from django.shortcuts import redirect
        return redirect('/admin/digipal/itempart/%s/edit/%s/' % (item_partid, type.slug))
    else:
        type = TextContentType.objects.filter(slug=type.lower().strip()).first()
        if not type:
            raise Http404('Content type %s does not exist.' % type)
    
    text_content, created = TextContent.objects.get_or_create(item_part=ItemPart.objects.get(id=item_partid), type=type)
    print created, item_partid, type, text_content.id
    text_content_xml = text_content.text_content_xmls.first()
    if text_content_xml is None:
        text_content_xml = TextContentXML(text_content=text_content)
        text_content_xml.save()
    
    if request.is_ajax():
        return text_edit_view_ajax(request, text_content_xml)
    
    context = {'text_content_xml': text_content_xml, 'item_part': text_content.item_part, 'content_types': TextContentType.objects.all()}    
    
    return render(request, 'admin/text_edit.html', context)

def text_edit_view_ajax(request, text_content_xml):
    data = {
            'status': 'info',
            'message': '',
            }
    
    def set_message(message, status='info'):
        data['message'] = message
        data['status'] = status
    
    action = request.GET.get('action', '')
    if action == 'load_text':
        data['text'] = text_content_xml.content
        set_message('Text loaded')
    if action == 'save_text':
        text_content_xml.content = request.GET.get('text')
        text_content_xml.save()
        
        set_message('Text saved')
    
    return HttpResponse(json.dumps(data), mimetype='application/json')
    