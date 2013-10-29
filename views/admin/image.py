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
from django.utils import simplejson
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.db import transaction

import logging
dplog = logging.getLogger( 'digipal_debugger')


#########

from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelForm
from django import forms

#####


@staff_member_required

def image_bulk_edit(request, url=None):
    context = {}
    context['folios'] = Image.objects.filter(id__in=request.GET.get('ids', '').split(',')).order_by('iipimage')
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
                folio.locus = folio.get_locus_label(True)
                modified = True

            if modified: folio.save()


    #return view_utils.get_template('admin/editions/folio_image/bulk_edit', context, request)
    return render(request, 'admin/page/bulk_edit.html', context)

@staff_member_required

def newScriptEntry(request):

    formsetScribe = formset_factory(ScribeAdminForm)

    formset = formsetScribe()

    onlyScribeForm = OnlyScribe()

    newContext = {
               'can_edit': has_edit_permission(request, Annotation), 'formset': formset,
               'scribeForm': onlyScribeForm
               }

    return render_to_response('admin/page/ScriptForm.html', newContext,
                              context_instance=RequestContext(request))


@staff_member_required

def get_idiographs(request):
        scribe_id = request.GET.get('scribe', '')
        idiographs = []
        scribe = Scribe.objects.get(id=scribe_id)
        idiographs_values = scribe.idiographs
        for idiograph in idiographs_values.all():
            num_features = Feature.objects.filter(idiographcomponent__idiograph=idiograph.id).count()
            object_idiograph = {
                'allograph_id': idiograph.allograph_id,
                'scribe_id': idiograph.scribe_id,
                'idiograph': idiograph.display_label,
                'id': idiograph.id,
                'num_features': num_features
            }
            idiographs.append(object_idiograph)

        return HttpResponse(simplejson.dumps(idiographs), mimetype='application/json')

@staff_member_required

def get_allographs(request):
    """Returns a JSON of all the features for the requested allograph, grouped
    by component."""
    if request.is_ajax():
        allograph_id = request.GET.get('allograph', '')
        allograph = Allograph.objects.get(id=allograph_id)
        allograph_components = \
                AllographComponent.objects.filter(allograph=allograph)

        data = []

        if allograph_components:
            for ac in allograph_components:
                ac_dict = {}
                ac_dict['id'] = ac.component.id
                ac_dict['name'] = ac.component.name
                ac_dict['features'] = []

                for f in ac.component.features.all():
                    ac_dict['features'].append({'id': f.id, 'name': f.name})

                data.append(ac_dict)

        return HttpResponse(simplejson.dumps(data), mimetype='application/json')
    else:
        return HttpResponseBadRequest()

@staff_member_required

def get_ideograph(request):
    if request.is_ajax():
        ideograph_id = request.GET.get('ideograph', '')
        ideograph_obj = Idiograph.objects.get(id=ideograph_id)
        ideograph = {}
        ideograph['scribe_id'] = ideograph_obj.scribe.id
        ideograph['allograph_id'] = ideograph_obj.allograph.id,
        ideograph['scribe'] = ideograph_obj.scribe.name
        ideograph_components = ideograph_obj.idiographcomponent_set.values()
        components = []
        for component in ideograph_components:
            feature_obj = Feature.objects.filter(idiographcomponent=component['id'])
            if feature_obj.count() > 0:
                features = []
                for obj in feature_obj.values():
                    feature = {}
                    feature['name'] = obj['name']
                    feature['id'] = obj['id']
                    component_id = Component.objects.filter(features=obj['id'], idiographcomponent=component['id']).values('id')[0]['id']
                    component_name = Component.objects.filter(features=obj['id'], idiographcomponent=component['id']).values('name')[0]['name']
                    features.append(feature)
                c = {
                    'id': component_id,
                    'name': component_name,
                    "features": features,
                    'idiograph_component': component['id']
                }
                components.append(c)
        ideograph['components'] = components
        return HttpResponse(simplejson.dumps([ideograph]), mimetype='application/json')
    else:
        return HttpResponseBadRequest()

@staff_member_required
@transaction.commit_on_success

def save_idiograph(request):
    response = {}
    try:
        scribe_id = int(request.POST.get('scribe', ''))
        allograph_id = int(request.POST.get('allograph', ''))
        data = simplejson.loads(request.POST.get('data', ''))
        allograph = Allograph.objects.get(id=allograph_id)
        scribe = Scribe.objects.get(id=scribe_id)
        idiograph = Idiograph(allograph=allograph, scribe=scribe)
        idiograph.save()
        for component in data:
            idiograph_id = Idiograph.objects.get(id=idiograph.id)
            component_id = Component.objects.get(id=component['id'])
            idiograph_component = IdiographComponent(idiograph = idiograph_id, component = component_id)
            idiograph_component.save()
            for features in component['features']:
                feature = Feature.objects.get(id=features['id'])
                idiograph_component.features.add(feature)
        response['errors'] = False
    except Exception as e:
        response['errors'] = ['Internal error: %s' % e.message]
    return HttpResponse(simplejson.dumps(response), mimetype='application/json')



@staff_member_required
@transaction.commit_on_success
def update_idiograph(request):
    response = {}
    try:
        allograph_id = int(request.POST.get('allograph', ''))
        idiograph_id = int(request.POST.get('idiograph_id', ''))
        data = simplejson.loads(request.POST.get('data', ''))
        allograph = Allograph.objects.get(id=allograph_id)
        idiograph = Idiograph.objects.get(id=idiograph_id)
        idiograph.allograph = allograph
        idiograph.save()
        for idiograph_component in data:
            if idiograph_component['idiograph_component'] != False:
                ic = IdiographComponent.objects.get(id=idiograph_component['idiograph_component'])
                ic.features.clear()
            else:
                ic = IdiographComponent()
            component = Component.objects.get(id=idiograph_component['id'])
            ic.idiograph = idiograph
            ic.component = component
            ic.save()
            for features in idiograph_component['features']:
                feature = Feature.objects.get(id=features['id'])
                ic.features.add(feature)
        response['errors'] = False
    except Exception as e:
        response['errors'] = ['Internal error: %s' % e.message]
    return HttpResponse(simplejson.dumps(response), mimetype='application/json')

@staff_member_required
@transaction.commit_on_success

def delete_idiograph(request):
    response = {}
    try:
        idiograph_id = int(request.POST.get('idiograph_id', ''))
        idiograph = Idiograph.objects.get(id=idiograph_id)
        idiograph.delete()
        IdiographComponent.objects.filter(idiograph=idiograph).delete()
        response['errors'] = False
    except Exception as e:
        response['errors'] = ['Internal error: %s' % e.message]
    return HttpResponse(simplejson.dumps(response), mimetype='application/json')
