from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.utils.datastructures import SortedDict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import sys

from digipal.forms import ImageAnnotationForm, FilterManuscriptsImages
from digipal.models import Allograph, AllographComponent, Annotation, \
        GraphComponent, Graph, Component, Feature, Idiograph, Image, Repository, \
        has_edit_permission
import ast
from django import template

register = template.Library()



def get_features(request, image_id, graph_id):
    dict_features = []
    graph_components = GraphComponent.objects.filter(graph_id = graph_id)
    for component in graph_components.values_list('id', flat=True):
        name_component = Component.objects.filter(graphcomponent=component)
        dict_features.append({'id': component, 'name': name_component.values('name')[0]['name'], 'feature': []})
    for feature in dict_features:
        features = Feature.objects.filter(graphcomponent = feature['id']).values_list('name',  flat=True)
        feature['feature'].append(features)
        for f in feature['feature']:
            feature['feature'] = list(f)
    return HttpResponse(simplejson.dumps(dict_features), mimetype='application/json')

def allograph_features(request, image_id, allograph_id):
    """Returns a JSON of all the features for the requested allograph, grouped
    by component."""
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

def image(request, image_id):
    """Returns a image annotation form."""
    image = Image.objects.get(id=image_id)
    annotations = image.annotation_set.values('graph').count()
    hands = image.hands.count()
    # Check for a vector_id in image referral, if it exists the request has
    # come via Scribe/allograph route
    vector_id = request.GET.get('vector_id', '')

    image_link = urlresolvers.reverse('admin:digipal_image_change', args=(image.id,))
    form = ImageAnnotationForm()

    form.fields['hand'].queryset = image.hands.all()

    width, height = image.dimensions()
    image_server_url = image.zoomify

    #is_admin = request.user.is_superuser
    is_admin = has_edit_permission(request, Image)
        
    context = {
               'form': form, 'image': image, 'height': height, 'width': width,
               'image_server_url': image_server_url,
               'image_link': image_link, 'annotations': annotations, 
               'hands': hands, 'is_admin': is_admin,
               'no_image_reason': image.get_media_unavailability_reason(request.user),
               'can_edit': has_edit_permission(request, Annotation)
               }
 
    if vector_id:
        context['vector_id'] = vector_id

    return render_to_response('digipal/image_annotation.html', context, 
                              context_instance=RequestContext(request))

def get_allograph(request, graph_id, image_id):
    """Returns the allograph id of a given graph"""
    g = Graph.objects.get(id=graph_id)
    allograph_id = g.idiograph.allograph_id
    data = {'id': allograph_id}
    return HttpResponse(simplejson.dumps(data), mimetype='application/json') 

def image_vectors(request, image_id):
    """Returns a JSON of all the vectors for the requested image."""
    annotation_list = Annotation.objects.filter(image=image_id)
    data = {}

    for a in annotation_list:
        data[a.vector_id] = ast.literal_eval(a.geo_json.strip())
        data[a.vector_id]['graph'] = a.graph_id
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')



def image_annotations(request, image_id):
    """Returns a JSON of all the annotations for the requested image."""
    annotation_list = Annotation.objects.filter(image=image_id)

    data = {}

    for a in annotation_list:
        data[a.id] = {}
        data[a.id]['vector_id'] = a.vector_id
        data[a.id]['status_id'] = a.status_id
        data[a.id]['hidden_hand'] = a.graph.hand.id

        if a.before:
            data[a.id]['before'] = '%d::%s' % (a.before.id, a.before.name)

        data[a.id]['hidden_allograph'] = '%d::%s' % (a.graph.idiograph.allograph.id,
            a.graph.idiograph.allograph.name)

        data[a.id]['feature'] = '%s' % (a.graph.idiograph.allograph)
        data[a.id]['graph'] = '%s' % (a.graph.id)

        if a.after:
            data[a.id]['after'] = '%d::%s' % (a.after.id, a.after.name)

        data[a.id]['display_note'] = a.display_note
        data[a.id]['internal_note'] = a.internal_note

        gc_list = GraphComponent.objects.filter(graph=a.graph)

        if gc_list:
            data[a.id]['features'] = []

            for gc in gc_list:
                for f in gc.features.all():
                    data[a.id]['features'].append('%d::%d' % (gc.component.id,
                        f.id))

    return HttpResponse(simplejson.dumps(data), mimetype='application/json')


def image_allographs(request, image_id):
    """Returns a list of all the allographs/annotations for the requested
    image."""
    annotation_list = Annotation.objects.filter(image=image_id)
    image = Image.objects.get(id=image_id)
    image_link = urlresolvers.reverse('admin:digipal_image_change', args=(image.id,))
    form = ImageAnnotationForm()

    form.fields['hand'].queryset = image.hands.all()

    width, height = image.dimensions()
    image_server_url = image.zoomify

    #is_admin = request.user.is_superuser
    is_admin = has_edit_permission(request, Image)
     
    data = SortedDict()

    for annotation in annotation_list:
        hand = annotation.graph.hand
        allograph_name = annotation.graph.idiograph.allograph

        if hand in data:
            if allograph_name not in data[hand]:
                data[hand][allograph_name] = []
        else:
            data[hand] = SortedDict()
            data[hand][allograph_name] = []

        data[hand][allograph_name].append(annotation)

    return render_to_response('digipal/image_allograph.html',
            {'image': image,
             'height': height, 
             'image_server_url': image_server_url,
             'width': width, 
             'data': data, 
             'form': form,
             'can_edit': has_edit_permission(request, Annotation)},
            context_instance=RequestContext(request))

def image_metadata(request, image_id):
    """Returns a list of all the allographs/annotations for the requested
    image."""
    context = {}
    image = Image.objects.get(id=image_id)
    context['image'] = image

    return render_to_response('pages/record_images.html',
            context,
            context_instance=RequestContext(request))

def image_copyright(request, image_id):
    context = {}
    image = Image.objects.get(id=image_id)
    #repositories = Repository.objects.filter(currentitem__itempart__images=image_id)
    #context['copyright'] = repository.values_list('copyright_notice', flat = True)
    # TODO: check this path
    context['repositories'] = Repository.objects.filter(currentitem__itempart__images=image_id)
    context['image'] = image
    return render_to_response('pages/copyright.html', context,
            context_instance=RequestContext(request))
    #page -> currentitem -> itempart -> repository.copyright_notice

def image_list(request):
    images = Image.objects.all()
    
    # Get Buttons

    town_or_city = request.GET.get('town_or_city', '')
    repository = request.GET.get('repository', '')

    date = request.GET.get('date', '')

    # Applying filters
    if town_or_city:
        images = images.filter(item_part__current_item__repository__place__name = town_or_city)
    if repository:
        repository_place = repository.split(',')[0]
        repository_name = repository.split(', ')[1]
        print repository_place
        print repository_name
        images = images.filter(item_part__current_item__repository__name=repository_name,item_part__current_item__repository__place__name=repository_place)
    if date:
        images = images.filter(hands__assigned_date__date = date)
        
    images = images.filter(item_part_id__gt = 0)

    paginator = Paginator(images, 24)
    page = request.GET.get('page')
    filterImages = FilterManuscriptsImages()

    try:
        page_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page_list = paginator.page(paginator.num_pages)

    context = {}
    context['page_list'] = page_list
    context['filterImages'] = filterImages
    try:
        context['view'] = request.COOKIES['view']
    except:
        context['view'] = 'Images'

    return render_to_response('digipal/image_list.html', context, context_instance=RequestContext(request))



@login_required
@transaction.commit_manually
def save(request, image_id, vector_id):
    """Saves an annotation and creates a cutout of the annotation."""
    try:
        data = {}

        image = Image.objects.get(id=image_id)

        get_data = request.GET.copy()
        geo_json = get_data['geo_json']

        annotation_list = Annotation.objects.filter(image=image,
                vector_id=vector_id)

        if annotation_list:
            annotation = annotation_list[0]
            graph = annotation.graph
        else:
            annotation = Annotation(image=image, vector_id=vector_id)
            graph = Graph()

        form = ImageAnnotationForm(data=get_data)

        if form.is_valid():
            clean = form.cleaned_data

            annotation.geo_json = geo_json
            annotation.display_note = clean['display_note']
            annotation.internal_note = clean['internal_note']
            annotation.author = request.user
            #annotation.before = clean['before']
            #annotation.after = clean['after']

            allograph = clean['allograph']
            hand = clean['hand']
            scribe = hand.scribe
            
            idiograph_list = Idiograph.objects.filter(allograph=allograph,
                    scribe=scribe)

            if idiograph_list:
                idiograph = idiograph_list[0]
                idiograph.id
            else:
                idiograph = Idiograph(allograph=allograph, scribe=scribe)
                idiograph.save()

            graph.idiograph = idiograph
            graph.hand = hand
            graph.save() # error is here

            feature_list = get_data.getlist('feature')
            graph.graph_components.all().delete()
            
            if feature_list:

                for value in feature_list:
                    cid, fid = value.split('::')

                    component = Component.objects.get(id=cid)
                    feature = Feature.objects.get(id=fid)
                    gc_list = GraphComponent.objects.filter(graph=graph,
                            component=component)

                    if gc_list:
                        gc = gc_list[0]
                    else:
                        gc = GraphComponent(graph=graph, component=component)

                    gc.save()
                    gc.features.add(feature)
                    gc.save()

            annotation.graph = graph
            annotation.save()

            transaction.commit()
            data.update({'success': True})
        else:
            transaction.rollback()
            data.update({'success': False})
            data.update({'errors': {}})
            data['errors'].update(form.errors)
    except Exception as e:
        transaction.rollback()
        data.update({'success': False})
        data.update({'errors': {}})
        data['errors'].update({'exception': e.message})
        print "Error:", e.message
        tb = sys.exc_info()[2]

        return HttpResponse(simplejson.dumps(data),
                mimetype='application/json')
    
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')


@login_required
@transaction.commit_manually
def delete(request, image_id, vector_id):
    """Deletes the annotation related with the `image_id` and `feature_id`."""
    data = {}

    try:
        image = get_object_or_404(Image, pk=image_id)

        try:
            annotation = Annotation.objects.get(image=image, vector_id=vector_id)
        except Annotation.DoesNotExist:
            pass
        else:
            annotation.delete()

    except Exception as e:
        transaction.rollback()
        data.update({'success': False})
        data.update({'errors': {}})
        data['errors'].update({'exception': e.message})
    else:
        transaction.commit()
        data.update({'success': True})

    return HttpResponse(simplejson.dumps(data), mimetype='application/json')
