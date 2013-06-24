# -*- coding: utf-8 -*-
from digipal.models import *
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

from django.http import HttpResponse, Http404

import logging
dplog = logging.getLogger( 'digipal_debugger')


#########

from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelForm
from django import forms

#####


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
    return render(request, 'admin/page/bulk_edit.html', context)

@staff_member_required

def newScriptEntry (request):
    page_id = 34
    """Returns a page annotation form."""
    page = Page.objects.get(id=page_id)
    annotations = page.annotation_set.values('graph').count()
    
    page_link = urlresolvers.reverse('admin:digipal_page_change', args=(page.id,))
    form = ScribeAdminForm()
    scribeField = OnlyScribe()

    width, height = page.dimensions()
    image_server_url = page.zoomify

    #is_admin = request.user.is_superuser
    is_admin = has_edit_permission(request, Page)
    
    context = {
               'form': form, 'page': page, 'height': height, 'width': width,
               'image_server_url': image_server_url,
               'page_link': page_link, 'annotations': annotations, 
               #'hands': hands, 'is_admin': is_admin,
               'no_image_reason': page.get_media_unavailability_reason(request.user),
               'can_edit': has_edit_permission(request, Annotation)
               }

    formsetScribe = formset_factory(ScribeAdminForm, extra=10)

    formset = formsetScribe()
        
    onlyScribeForm = OnlyScribe()

    newContext = {
               'form': form, 'page': page, 'height': height, 'width': width,
               'image_server_url': image_server_url, 'scribe': scribeField,
               'page_link': page_link, 'annotations': annotations, 
               'no_image_reason': page.get_media_unavailability_reason(request.user),
               'can_edit': has_edit_permission(request, Annotation), 'formset': formset,
               'scribeForm': onlyScribeForm
               }

    return render_to_response('admin/page/ScriptForm.html', newContext, 
                              context_instance=RequestContext(request))
    
@staff_member_required

def inserting (request):

    newContext = {}
    d = request.POST

    
    length = 10

    if(not(d['addedrows'])):
        print("a")
    else:
        length = length + int(d['addedrows'])
        
    array = [""] * length

    for elem in range(0,len(array)):
        array[elem] = ["","",[]]

    scribeVar = ""

    if(d['scribe']):
        scribeVar = d['scribe']

    for elem in d:
        if(not(elem == "csrfmiddlewaretoken") and not(elem == "scribe") and not (elem == "addedrows")):
            #print elem + " = " + d[elem]r
            numRegex = re.search("[0-9]", elem, flags = 0)
            typeRegex = re.search( "((allograph$)|(component$)|(feature$))", elem, flags = 0)
            #print(elem)
            if(typeRegex):
                if(typeRegex.group() == "allograph"):
                    array[int(numRegex.group())][0] = d[elem]
                elif(typeRegex.group() == "component") :
                    array[int(numRegex.group())][1] = d[elem]
                elif(typeRegex.group() == "feature"):
                    string = "form-"+numRegex.group()+"-feature"
                    arr = request.POST.getlist(string)
                    for index in arr:
                        array[int(numRegex.group())][2].append(index)
    newContext['insertedElements'] = "<table>"

    for row in array:
        if(row[0] != "" and row[1] != "" and len(row[2]) != 0):

            newContext['insertedElements'] += "<tr>"
            newContext['insertedElements'] += "<td>" + row[0] + "</td>" + "<td>" + row[1] + "</td>"
            newContext['insertedElements'] += "<td><ul>"
           
            for element in row[2]:
                "<li>" + element + "</li>"  

            newContext['insertedElements'] += "</ul></td>"
    
            newContext['insertedElements'] += "</tr>"

            
            results = Idiograph.objects.filter(allograph__id = row[0], scribe__id = scribeVar)

            if(not(results)):
                globalObj = Idiograph(allograph_id = row[0], scribe_id = scribeVar)    
                globalObj.save()

                idiogComp = IdiographComponent(idiograph = globalObj, component_id = row[1])
                idiogComp.save()
                for randomindex in row[2]:
                    idiogComp.features.add(randomindex)

            else:
                
                idiogCompResults = IdiographComponent.objects.filter(idiograph_id = results[0], component_id = row[1])
                
                if(not(idiogCompResults)):
                    idiogComp = IdiographComponent(idiograph = results[0], component_id = row[1])
                    idiogComp.save()
                    for randomindex in row[2]:
                        idiogComp.features.add(randomindex)
                else:
                    for randomindex in row[2]:
                        if(randomindex not in idiogCompResults[0].features.all()):
                            print(randomindex)
                            idiogCompResults[0].features.add(int(randomindex))

    newContext['insertedElements'] += "</table>"

    return render_to_response('admin/page/insertion.html', newContext, 
                              context_instance=RequestContext(request))
