from django.contrib.admin.views.decorators import staff_member_required
from digipal.models import Feature, Idiograph, Component, Allograph, Scribe, IdiographComponent, Annotation, AllographComponent, has_edit_permission
from django.http import HttpResponse, HttpResponseBadRequest
from django.db import transaction
from django.forms.formsets import formset_factory
from digipal.forms import ScribeAdminForm, OnlyScribe
from django.shortcuts import render_to_response
from django.template import RequestContext
import json


@staff_member_required
def idiograph_editor(request):

    formsetScribe = formset_factory(ScribeAdminForm)

    formset = formsetScribe()

    onlyScribeForm = OnlyScribe()

    newContext = {
        'can_edit': has_edit_permission(request, Annotation), 'formset': formset,
        'scribeForm': onlyScribeForm
    }

    return render_to_response('admin/digipal/idiograph_editor.html', newContext,
                              context_instance=RequestContext(request))


@staff_member_required
def get_idiograph(request):
    if request.is_ajax():
        idiograph_id = request.GET.get('idiograph', '')
        idiograph_obj = Idiograph.objects.get(id=idiograph_id)
        idiograph = {}
        idiograph['scribe_id'] = idiograph_obj.scribe.id
        idiograph['allograph_id'] = idiograph_obj.allograph.id,
        idiograph['scribe'] = idiograph_obj.scribe.name
        idiograph_components = idiograph_obj.idiographcomponent_set.values()
        components = []
        for component in idiograph_components:
            feature_obj = Feature.objects.filter(
                idiographcomponent=component['id'])
            if feature_obj.count() > 0:
                features = []
                for obj in feature_obj.values():
                    feature = {}
                    feature['name'] = obj['name']
                    feature['id'] = obj['id']
                    component_id = Component.objects.filter(
                        features=obj['id'], idiographcomponent=component['id']).values('id')[0]['id']
                    component_name = Component.objects.filter(
                        features=obj['id'], idiographcomponent=component['id']).values('name')[0]['name']
                    features.append(feature)
                c = {
                    'id': component_id,
                    'name': component_name,
                    "features": features,
                    'idiograph_component': component['id']
                }
                components.append(c)
        idiograph['components'] = components
        return HttpResponse(json.dumps([idiograph]), content_type='application/json')
    else:
        return HttpResponseBadRequest()


@staff_member_required
@transaction.atomic
def save_idiograph(request):
    response = {}
    try:
        scribe_id = int(request.POST.get('scribe', ''))
        allograph_id = int(request.POST.get('allograph', ''))
        data = json.loads(request.POST.get('data', ''))
        allograph = Allograph.objects.get(id=allograph_id)
        scribe = Scribe.objects.get(id=scribe_id)
        idiograph = Idiograph(allograph=allograph, scribe=scribe)
        idiograph.save()
        for component in data:
            idiograph_id = Idiograph.objects.get(id=idiograph.id)
            component_id = Component.objects.get(id=component['id'])
            idiograph_component = IdiographComponent(
                idiograph=idiograph_id, component=component_id)
            idiograph_component.save()
            for features in component['features']:
                feature = Feature.objects.get(id=features['id'])
                idiograph_component.features.add(feature)
        response['errors'] = False
    except Exception as e:
        response['errors'] = ['Internal error: %s' % e.message]
    return HttpResponse(json.dumps(response), content_type='application/json')


@staff_member_required
@transaction.atomic
def update_idiograph(request):
    response = {}
    try:
        allograph_id = int(request.POST.get('allograph', ''))
        idiograph_id = int(request.POST.get('idiograph_id', ''))
        data = json.loads(request.POST.get('data', ''))
        allograph = Allograph.objects.get(id=allograph_id)
        idiograph = Idiograph.objects.get(id=idiograph_id)
        idiograph.allograph = allograph
        idiograph.save()
        for idiograph_component in data:
            if idiograph_component['idiograph_component'] != False:
                ic = IdiographComponent.objects.get(
                    id=idiograph_component['idiograph_component'])
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
    return HttpResponse(json.dumps(response), content_type='application/json')


@staff_member_required
@transaction.atomic
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
    return HttpResponse(json.dumps(response), content_type='application/json')


@staff_member_required
def get_idiographs(request):
    scribe_id = request.GET.get('scribe', '')
    idiographs = []
    scribe = Scribe.objects.get(id=scribe_id)
    idiographs_values = scribe.idiographs
    for idiograph in idiographs_values.all():
        num_features = Feature.objects.filter(
            idiographcomponent__idiograph=idiograph.id).count()
        object_idiograph = {
            'allograph_id': idiograph.allograph_id,
            'scribe_id': idiograph.scribe_id,
            'idiograph': idiograph.display_label,
            'id': idiograph.id,
            'num_features': num_features
        }
        idiographs.append(object_idiograph)

    return HttpResponse(json.dumps(idiographs), content_type='application/json')


@staff_member_required
def get_allographs(request):
    """Returns a JSON of all the features for the requested allograph, grouped
    by component."""
    if request.is_ajax():
        allograph_id = request.GET.get('allograph', '')
        allograph = Allograph.objects.get(id=allograph_id)
        allograph_components = AllographComponent.objects.filter(
            allograph=allograph)

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

        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        return HttpResponseBadRequest()
