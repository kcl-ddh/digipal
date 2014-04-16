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
from django.utils.datastructures import SortedDict

import logging
dplog = logging.getLogger( 'digipal_debugger')


#########

from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelForm
from django import forms

#####


def get_ms_id_from_image_names(manuscripts, folios):
    '''
        Returns (ret, suggested_shelfmark)
        ret = the id of the itempart which matches the most the given images
        suggested_shelfmark = a suggested shelfmark
        The matching is based on similarity of the name (shelfmark) and locus
    '''
    ret = None

    # a term is part of the search pattern if its frequency is above the threshold
    threshold = 0.75
    
    # find a pattern among the image paths
    pattern = SortedDict()
    
    folio_count = folios.count()
    for folio in folios:
        im_path = folio.iipimage.name
        
        # remove the extension
        im_path = re.sub(ur'\.[^.]{2,4}$', '', im_path)
        
        # only keep the image file name and the parent folder
        parts = im_path.split('/')
        for i in range(max(0, len(parts) - 2), len(parts)):
            part = parts[i]
            for term in re.findall(ur'[^\W_]+', part):
                pattern[term] = pattern.get(term, 0) + 1            
    
    # keep only the terms with frequency > threshold
    search_terms = [term for term in pattern if pattern[term] > threshold * folio_count]
    
    suggested_shelfmark = ' '.join(search_terms)
    
    # find the best match 
    for manuscript in manuscripts:
        match = True
        for term in search_terms:
            if term.lower() not in manuscript.display_label.lower().replace('.', ''):
                match = False
        if match and (not ret or len(manuscript.display_label) < len(ret.display_label)):
            ret = manuscript
    
    # find the nearest match in the list of item parts
    if ret:
        return ret.id, suggested_shelfmark
    else:
        return 0, suggested_shelfmark

def get_requested_itempart(request):
    item_part = None
    
    if str(request.POST.get('manuscript_set', '0')) == '1':
        current_item = None
        item_part = request.POST.get('manuscript', None)
        if item_part == '0': item_part = None
        if item_part:
            item_part = ItemPart.objects.get(id=item_part)
            current_item = item_part.current_item
        
        if request.POST.get('itempart_shelfmark', ''):
            # we need to create a new Current Item with the specified shelfmark
            new_shelfmark = request.POST.get('itempart_shelfmark_text', '')
            current_item = CurrentItem(shelfmark=new_shelfmark, repository=Repository.objects.get(id=request.POST.get('itempart_repo', 0)))
            current_item.save()

        if current_item and (request.POST.get('itempart_shelfmark', '') or request.POST.get('itempart_locus', '')):
            # we need to create a new Item Part with the specified locus
            new_locus = request.POST.get('itempart_locus_text', '')
            item_part = ItemPart(current_item=current_item, locus=new_locus)
            item_part.save()
            # create a new default hand for that part
            hand = Hand(item_part=item_part, num=1, label='Default Hand')
            hand.save()
    
    return item_part

def process_bulk_image_ajax(request):
    data = {'result': 'success'}
    
    action = request.GET.get('action', '')
    if action == 'test_replace_image':
        iids = [request.GET.get('image1', ''), request.GET.get('image2', '')]
        if iids[0] and iids[1]:
            from digipal.images.models import Image
            image = Image.objects.get(id=iids[0])
            data = image.find_image_offset(Image.objects.get(id=iids[1]))
            data['image1'] = iids[0];
            data['image2'] = iids[1];
    
    #find_image_offset
    
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')

@staff_member_required
def image_bulk_edit(request, url=None):
    '''
        This is the view for the bulk editing of the images.
        It helps with cataloguing a selection of of images.
    '''
    if request.is_ajax():
        return process_bulk_image_ajax(request)            
    
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
    # Determine the Item Part to set to those images
    # Create the Item Part, Current Item and default Hand if needed
    manuscript = get_requested_itempart(request)

    context['manuscripts'] = ItemPart.objects.all().order_by('display_label')
    
    context['repos'] = Repository.objects.all().order_by('short_name', 'name')
    
    context['title'] = 'Bulk Edit Images'
    
    #context['show_thumbnails'] = request.POST.get('thumbnails_set', 0)
    context['show_duplicates'] = request.POST.get('duplicate_set', 0)

    # read the selected foliation/pagination options
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

    if action == 'change_values' and context['show_duplicates']:
        # change image
        for key, val in request.POST.iteritems():
            image_id = re.sub(ur'^replace-image-(\d+)$', ur'\1', key)
            if image_id != key:
                new_image_id = val
                if image_id != new_image_id:
                    import digipal.images.models
                    im1 = digipal.images.models.Image.objects.get(id=image_id)
                    im2 = digipal.images.models.Image.objects.get(id=new_image_id)
                    offset_info = im1.find_image_offset(im2)
                    if sum(offset_info['offsets']) > 0:
                        im1.replace_image_and_update_annotations(offset_info['offsets'], im2)

    if len(action):
        
        handid = str(request.POST.get('hand', '0'))
        for folio in context['folios']:
            modified = False

            if action == 'operations':
                name = folio.iipimage.name
                # remove file extension
                name = re.sub(ur'\.\w\w\w$', ur'', name)
                number = re.findall(r'(?i)0*(\d{1,3})\D*$', name)
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
                    if folio.item_part and folio.item_part.pagination:
                        folio.folio_side = ''
                    else:
                        if re.search('(?i)[^a-z]r([^a-z]|$)', name):
                            folio.folio_side = recto
                        elif re.search('(?i)[^a-z]v([^a-z]|$)', name):
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
                if str(request.POST.get('hand_set', '0')) == '1':
                    if handid == '-2':
                        if folio.item_part:                                
                            hand = Hand(item_part=folio.item_part, num=1, label='Default Hand')
                            hand.save()
                            handid = hand.id
                    if handid != '0':
                        if handid == '-1':
                            folio.hands.through.objects.filter(image=folio).delete()
                        else:
                            folio.hands.add(Hand.objects.get(id=handid))
                    modified = True
                

            if action == 'change_values':

                '''
                        <input class="txt-folio-number" type="text" name="fn-{{folio.id}}" value="{{folio.folio_number}}" />
                        <input type="radio" id="fs-{{folio.id}}-id" name="fs-{{folio.id}}" {% ifequal folio.folio_side.id side.id %}checked="checked"{% endifequal %} >
                        <input class="txt-folio-number" type="text" name="pn-{{folio.id}}" value="{{folio.page}}" />
                        <input type="checkbox" name="arch-{{folio.id}}" {% if folio.archived %}checked="checked"{% endif %} />
                        <textarea class="txta-folio-note" name="inotes-{{folio.id}}">{{ folio.internal_notes }}</textarea>
                '''
                if not context['show_duplicates']:
                    folio.folio_number = request.POST.get('fn-%s' % (folio.id,), '')
                    #folio.folio_side = folio_sides[int(request.POST.get('fs-%s' % (folio.id,), 1))]
                    folio.folio_side = request.POST.get('fs-%s' % (folio.id,), '').strip()
                    #folio.page = request.POST.get('pn-%s' % (folio.id,), '')
                    #folio.archived = (len(request.POST.get('arch-%s' % (folio.id,), '')) > 0)
                    #folio.internal_notes = request.POST.get('inotes-%s' % (folio.id,), '')
                    modified = True

            if modified:
                folio.locus = folio.get_locus_label(True)
                folio.save()

    context['selected_manuscript_id'], context['suggested_shelfmark'] = get_ms_id_from_image_names(context['manuscripts'], context['folios'])

    # common_item_part: the Item Part in common among all the selected images
    # None if none or more than one
    common_item_part = None
    for image in context['folios']:
        if image.item_part and image.item_part != common_item_part:
            if common_item_part is None: 
                common_item_part = image.item_part
            else:
                common_item_part = None
                break
            
    if common_item_part:
        context['can_set_hand'] = True
        context['hands'] = common_item_part.hands.all().order_by('num')
        context['selected_manuscript_id'], context['suggested_shelfmark'] = common_item_part.id, ''
    else:
        context['hands'] = None

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
