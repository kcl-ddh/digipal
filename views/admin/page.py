# -*- coding: utf-8 -*-
from digipal.models import *
import re
from django import http, template
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy, ugettext as _ 
from django.utils.safestring import mark_safe
import htmlentitydefs

from django.http import HttpResponse, Http404

import logging
dplog = logging.getLogger( 'digipal_debugger')

@staff_member_required
def page_bulk_edit(request, url=None):
    context = {}
    context['folios'] = Page.objects.filter(id__in=request.GET.get('ids', '').split(',')).order_by('iipimage')
    context['folio_sides'] = []
    '''
    context['folio_sides'] = [
                              {'label': 'Unspecified', 'key': ''},
                              {'label': 'Recto', 'key': 'r'},
                              {'label': 'Verso', 'key': 'v'},
                              {'label': 'Verso and Recto', 'key': 'rv'},
                              ]
    '''
    context['manuscripts'] = ItemPart.objects.all().order_by('display_label')
    context['show_thumbnails'] = request.POST.get('thumbnails_set', 0)
    
    manuscript = request.POST.get('manuscript', None)
    if manuscript == '0': manuscript = None
    if manuscript:
        manuscript = ItemPart.objects.get(id=manuscript)
    
    page = request.POST.get('page_number', '').strip()
    if page != '':
        page = int(page)
        
    folio_number = request.POST.get('folio_number', '').strip()
    if folio_number != '':
        folio_number = int(folio_number)
    #folio_side = Folio_Side.objects.get(id=request.POST.get('folio_side', '1'))
    folio_side = request.POST.get('folio_side', '1').strip()
    #folio_sides = {}
    
#    for s in Folio_Side.objects.all():
#        folio_sides[s.id] = s
    
    recto = 'r'
    verso = 'v'
    unspecified_side = ''
    
    action = request.POST.get('action', '').strip()

    #if action == 'operations':

    
    if len(action):
        for folio in context['folios']:
            modified = False
            
            if action == 'operations':
                number = re.findall(r'(?i)0*(\d{1,3})\D*$', folio.iipimage.name)
                if str(request.POST.get('manuscript_set', '0')) == '1':
                    folio.item_part = manuscript
                    modified = True
                if str(request.POST.get('page_set', '0')) == '1':
                    folio.page = page
                    if page != '':
                        page = page + 1
                    modified = True
                if str(request.POST.get('folio_set', '0')) == '1':
                    folio.folio_number = folio_number
                    if folio_number != '' and folio_side in (verso, ''):
                        folio_number = folio_number + 1
                    folio.folio_side = folio_side
                    if folio_side == recto: 
                        folio_side = verso
                    elif folio_side == verso:
                        folio_side = recto
                    modified = True
                if str(request.POST.get('folio_number_set', '0')) == '1':
                    if len(number) > 0:
                        folio.folio_number = number[0]
                    else:
                        folio.folio_number = ''
                    modified = True
                if str(request.POST.get('folio_side_set', '0')) == '1':
                    if re.search('(?i)[^a-z]r$', folio.iipimage.name): 
                        folio.folio_side = recto
                    elif re.search('(?i)[^a-z]v$', folio.iipimage.name): 
                        folio.folio_side = verso
                    else: 
                        folio.folio_side = recto
                        #folio.folio_side = unspecified_side
                    modified = True
                if str(request.POST.get('page_number_set', '0')) == '1':
                    if len(number) > 0:
                        folio.page = number[0]
                    else:
                        folio.page = ''
                    modified = True
                if str(request.POST.get('archived_set', '0')) == '1':
                    folio.archived = True
                    modified = True
                if str(request.POST.get('unarchived_set', '0')) == '1':
                    folio.archived = False
                    modified = True
            
            if action == 'change_values':

                '''
                        <input class="txt-folio-number" type="text" name="fn-{{folio.id}}" value="{{folio.folio_number}}" />
                        <input type="radio" id="fs-{{folio.id}}-id" name="fs-{{folio.id}}" {% ifequal folio.folio_side.id side.id %}checked="checked"{% endifequal %} >
                        <input class="txt-folio-number" type="text" name="pn-{{folio.id}}" value="{{folio.page}}" />
                        <input type="checkbox" name="arch-{{folio.id}}" {% if folio.archived %}checked="checked"{% endif %} />
                        <textarea class="txta-folio-note" name="inotes-{{folio.id}}">{{ folio.internal_notes }}</textarea>
                '''                
                
                folio.folio_number = request.POST.get('fn-%s' % (folio.id,), '')
                #folio.folio_side = folio_sides[int(request.POST.get('fs-%s' % (folio.id,), 1))]
                folio.folio_side = request.POST.get('fs-%s' % (folio.id,), '').strip()
                #folio.page = request.POST.get('pn-%s' % (folio.id,), '')
                #folio.archived = (len(request.POST.get('arch-%s' % (folio.id,), '')) > 0)
                #folio.internal_notes = request.POST.get('inotes-%s' % (folio.id,), '')
                modified = True            
            
            if modified: folio.save()

            
    #return view_utils.get_template('admin/editions/folio_image/bulk_edit', context, request)
    from django.shortcuts import render
    return render(request, 'admin/page/bulk_edit.html', context)

