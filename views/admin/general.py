# -*- coding: utf-8 -*-
import re
from django import http, template
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.http import HttpResponse, Http404, HttpResponseBadRequest

import logging
dplog = logging.getLogger( 'digipal_debugger')


@staff_member_required

def context_view(request, app_label, model_name, object_id):
    from django.contrib.contenttypes.models import ContentType
    
    context = {}
    
    # get the object
    model_class = ContentType.objects.get(app_label=app_label, model=model_name).model_class()
    obj = model_class.objects.get(id=object_id)
    
    #context['obj_tree'] = get_obj_info(obj)
    context['tree_html'] = mark_safe(get_html_from_obj_tree(get_obj_info(obj)))
    
    return render(request, 'admin/digipal/context.html', context)

def get_html_from_obj_tree(element):
    ret = ur''
    
    if element:
        for child in element['children']:
            ret += get_html_from_obj_tree(child)
        if ret:    
            ret = ur'<ul>%s</ul>' % ret
        ret = ur'<li>%s%s</li>' % (element['html'], ret)
    
    return ret

def get_obj_info(obj, exclude_list=None):
    if exclude_list is None: exclude_list = {}
    
    ret = {
           'obj': obj, 
           'type': obj._meta.object_name, 
           'link': ur'/admin/%s/%s/%s/' % (obj._meta.app_label, obj._meta.module_name, obj.id), 
           'children': []
           }
    
    info = ''

    if obj._meta.module_name == 'historicalitem':
        info = '%s, %s' % (obj.historical_item_format, obj.historical_item_type)
        
    if info:
        info = ur'(%s) ' % info
     
    exclude_list[get_obj_key(obj)] = 1

    ret['html'] = ur'<a href="%s">%s #%s: %s %s</a>[<a href="%s">edit</a>]' % (ret['link']+ur'context/', ret['type'], obj.id, ret['obj'], info, ret['link'])

    for child in get_obj_children(obj):
        if get_obj_key(child) not in exclude_list: 
            obj_info = get_obj_info(child, exclude_list.copy())
            ret['children'].append(obj_info)

    if ret['children']:
        ret['html'] = ur'<a class="expandable" href="#">[ - ]</a> %s' % ret['html']
    
    return ret

def get_obj_key(obj):
    return ur'%s-%s' % (obj._meta.object_name, obj.id)

def get_obj_children(obj):
    ret = []
    
    if obj._meta.module_name == 'itempart':
        ret.extend((obj.current_item,))
        ret.extend(list(obj.historical_items.all().order_by('id')))
        ret.extend(list(obj.images.all().order_by('id')))
    
    if obj._meta.module_name == 'currentitem':
        ret.extend(list(obj.itempart_set.all().order_by('id')))

    if obj._meta.module_name == 'historicalitem':
        ret.extend(list(obj.item_parts.all().order_by('id')))

    return ret
