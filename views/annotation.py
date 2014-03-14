# -*- coding: utf-8 -*-

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
from django.utils.safestring import mark_safe


from digipal.forms import ImageAnnotationForm
from digipal.models import Allograph, AllographComponent, Annotation, Hand, \
        GraphComponent, Graph, Component, Feature, Idiograph, Image, Repository, \
        has_edit_permission
import ast
from django import template

register = template.Library()


def get_content_type_data(request, content_type, id, only_features=False):

    ids = str(id)
    if content_type == 'graph':
        data = get_features(ids, only_features)
    elif content_type == 'allograph':
        data = allograph_features(request, ids)
    elif content_type == 'hand':
        data = get_hands(ids)
    return HttpResponse(data, mimetype='application/json')

def get_features(graph_id, only_features=False):
    data = []
    graphs = str(graph_id).split(',')
    for graph in graphs:
        obj = {}
        dict_features = list([])
        g = Graph.objects.get(id=graph)
        graph_components = g.graph_components

        if not only_features:
            allograph = allograph_features(False, g.idiograph.allograph.id)

        vector_id = g.annotation.vector_id
        hand_id = g.hand.id
        allograph_id = g.idiograph.allograph.id
        image_id = g.annotation.image.id
        hands_list = []
        hands = g.annotation.image.hands.all()

        for hand in hands:
            h = {
                'id': hand.id,
                'label': hand.label
            }
            hands_list.append(h)

        for component in graph_components.values_list('id', flat=True):
            name_component = Component.objects.filter(graphcomponent=component)
            dict_features.append({"graph_component_id": component, 'component_id': name_component.values('id')[0]['id'], 'name': name_component.values('name')[0]['name'], 'feature': []})

        for feature in dict_features:
            features = Feature.objects.filter(graphcomponent = feature['graph_component_id']).values_list('name',  flat=True)
            if len(features) > 0:
                feature['feature'].append(features)
                for f in feature['feature']:
                    feature['feature'] = list(f)


        obj['features'] = dict_features
        if not only_features:
             obj['allographs'] = allograph
        obj['vector_id'] = vector_id
        obj['image_id'] = image_id
        obj['hand_id'] = hand_id
        obj['allograph_id'] = allograph_id
        obj['hands'] = hands_list
        obj['graph'] = g.id
        data.append(obj)

    return simplejson.dumps(data)


def allograph_features(request, allograph_id):
    """Returns a JSON of all the features for the requested allograph, grouped
    by component."""
    allographs = str(allograph_id).split(',')
    obj = {}
    data = []

    for allograph in allographs:
        allog = Allograph.objects.get(id=allograph)
        allograph_components = \
            AllographComponent.objects.filter(allograph=allog)

        allographs_list = []

        if allograph_components:
            for ac in allograph_components:
                ac_dict = {}
                ac_dict['id'] = ac.component.id
                ac_dict['name'] = ac.component.name
                ac_dict['features'] = []

                for f in ac.component.features.all():
                    ac_dict['features'].append({'id': f.id, 'name': f.name})

                allographs_list.append(ac_dict)
        obj['features'] = []
        obj['allographs'] = allographs_list
        data.append(obj)

    if request:
        return simplejson.dumps(data)
    else:
        return allographs_list

def image(request, image_id):
    """Returns a image annotation form."""
    try:
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        return render_to_response('errors/404.html', {'title': 'This Page record does not exist'},
                              context_instance=RequestContext(request))

    images = image.item_part.images.exclude(id=image.id)
    annotations_count = image.annotation_set.values('graph').count()
    annotations = image.annotation_set.all()
    dimensions = {
        'width': image.dimensions()[0],
        'height': image.dimensions()[1]
        }
    hands = image.hands.count()
    url = url = request.path
    url = url.split('/')
    url.pop(len(url) - 1)
    url = url[len(url) - 1]
    # Check for a vector_id in image referral, if it exists the request has
    # come via Scribe/allograph route
    vector_id = request.GET.get('vector_id', '')
    hands_list = []
    hand = {}
    hands_object = Hand.objects.filter(images=image_id)
    data_allographs = SortedDict()

    for h in hands_object.values():
        if h['label'] == None:
            label = "None"
        else:
            label = mark_safe(h['label'])
        hand = {'id': h['id'], 'name': label.encode('cp1252')}
        hands_list.append(hand)

    #annotations by allograph
    for a in annotations:
        hand_label = a.graph.hand
        allograph_name = a.graph.idiograph.allograph
        if hand_label in data_allographs:
            if allograph_name not in data_allographs[hand_label]:
                data_allographs[hand_label][allograph_name] = []
        else:
            data_allographs[hand_label] = SortedDict()
            data_allographs[hand_label][allograph_name] = []

        data_allographs[hand_label][allograph_name].append(a)


    image_link = urlresolvers.reverse('admin:digipal_image_change', args=(image.id,))
    form = ImageAnnotationForm(auto_id=False)
    form.fields['hand'].queryset = image.hands.all()

    width, height = image.dimensions()
    image_server_url = image.zoomify

    is_admin = has_edit_permission(request, Image)

    from digipal.models import OntographType
    context = {
               'form': form.as_ul(), 'dimensions': dimensions, 'images': images,
               'image': image, 'height': height, 'width': width,
               'image_server_url': image_server_url, 'hands_list': hands_list,
               'image_link': image_link, 'annotations': annotations_count,
               'annotations_list': data_allographs, 'url': url,
               'hands': hands, 'is_admin': is_admin,
               'no_image_reason': image.get_media_unavailability_reason(request.user),
               'can_edit': has_edit_permission(request, Annotation),
               'ontograph_types': OntographType.objects.order_by('name'),
               'repositories': Repository.objects.filter(currentitem__itempart__images=image_id)
               }

    if vector_id:
        context['vector_id'] = vector_id

    return render_to_response('digipal/image_annotation.html', context,
                              context_instance=RequestContext(request))

def get_allograph(request, graph_id):
    """Returns the allograph id of a given graph"""
    g = Graph.objects.get(id=graph_id)
    allograph_id = g.idiograph.allograph_id
    data = {'id': allograph_id}
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def image_vectors(request, image_id):
    """Returns a JSON of all the vectors for the requested image."""
    # Order the graph by the left edge to ensure that an openlayer feature
    # contained in another will be created later and therefore remain on top.
    # Otherwise nested graphs may not be selectable because they are covered
    # by their parent.

    annotation_list = list(Annotation.objects.filter(image=image_id))
    annotation_list = sorted(annotation_list, key=lambda a: a.get_coordinates()[0][0])

    data = SortedDict()

    for a in annotation_list:
        # TODO: suspicious call to eval. Should call json.loads() instead - GN
        data[a.vector_id] = ast.literal_eval(a.geo_json.strip())
        data[a.vector_id]['graph'] = a.graph_id

    return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def get_vector(request, image_id, graph):
    annotation = Annotation.objects.get(graph=graph)
    data = {}
    data['vector_id'] = ast.literal_eval(annotation.geo_json.strip())
    data['id'] = annotation.vector_id
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def image_annotations(request, image_id, annotations_page=True, hand=False):
    """Returns a JSON of all the annotations for the requested image."""

    if annotations_page:
        annotation_list = Annotation.objects.filter(image=image_id)
    else:
        annotation_list = Annotation.objects.filter(graph__hand=hand)

    data = {}
    hands = []
    for a in annotation_list:
        data[a.id] = {}
        data[a.id]['vector_id'] = a.vector_id
        data[a.id]['status_id'] = a.status_id
        data[a.id]['image_id'] = a.image.id
        data[a.id]['hidden_hand'] = a.graph.hand.id
        data[a.id]['character'] = a.graph.idiograph.allograph.character.name
        data[a.id]['hand'] = a.graph.hand_id
        data[a.id]['character_id'] = a.graph.idiograph.allograph.character.id
        features_list = simplejson.loads(get_features(a.graph.id, True))
        data[a.id]['num_features'] = len(features_list[0]['features'])
        data[a.id]['features'] = features_list
        #hands.append(data[a.id]['hand'])

        hand = a.graph.hand.label
        hands.append(a.graph.hand.id)
        allograph_name = a.graph.idiograph.allograph.name

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

    if annotations_page:
        return HttpResponse(simplejson.dumps(data), mimetype='application/json')
    else:
        return data

def get_allographs_by_graph(request, image_id, character_id, graph_id):
        graph = Graph.objects.get(id=graph_id)
        feature = graph.idiograph.allograph.name
        annotations = Annotation.objects.filter(graph__idiograph__allograph__name=feature, graph__idiograph__allograph__character__id=character_id, image=image_id)
        annotations_list = []
        if annotations:
            for i in annotations:
                hand = Hand.objects.filter(graphs__annotation=i.id)
                annotation = {
                    'hand': hand[0].id,
                    'hand_name': hand[0].label,
                    'image': i.thumbnail(),
                    'vector_id': i.vector_id
                }
                annotations_list.append(annotation)
            return HttpResponse(simplejson.dumps(annotations_list), mimetype='application/json')
        else:
            return HttpResponse(False)

def get_allographs_by_allograph(request, image_id, character_id, allograph_id):
    annotations = Annotation.objects.filter(graph__idiograph__allograph__id=allograph_id,graph__idiograph__allograph__character__id=character_id, image=image_id)
    annotations_list = []
    if annotations:
        for i in annotations:
            hand = Hand.objects.filter(graphs__annotation=i.id)
            annotation = {
                'hand': hand[0].id,
                'hand_name': hand[0].label,
                'image': i.thumbnail(),
                'image_id': i.image.id,
                'graph' : i.graph.id,
                'vector_id': i.vector_id
            }
            annotations_list.append(annotation)
        return HttpResponse(simplejson.dumps(annotations_list), mimetype='application/json')
    else:
        return HttpResponse(False)


def image_allographs(request, image_id):
    """Returns a list of all the allographs/annotations for the requested
    image."""
    annotations = Annotation.objects.filter(image=image_id)

    data_allographs = SortedDict()
    for a in annotations:
        hand_label = a.graph.hand
        allograph_name = a.graph.idiograph.allograph
        if hand_label in data_allographs:
            if allograph_name not in data_allographs[hand_label]:
                data_allographs[hand_label][allograph_name] = []
        else:
            data_allographs[hand_label] = SortedDict()
            data_allographs[hand_label][allograph_name] = []

        data_allographs[hand_label][allograph_name].append(a)

    context = {
        'annotations_list': data_allographs,
        'can_edit': has_edit_permission(request, Annotation)
    }

    return render_to_response('digipal/annotations.html', context, context_instance=RequestContext(request))

def hands_list(request, image_id):
    hands_list = simplejson.loads(request.GET.get('hands', ''))
    hands = []
    for i in hands_list:
        h = Hand.objects.get(id=i)
        hands.append(h.display_label)
    return HttpResponse(simplejson.dumps(hands), mimetype='application/json')

def get_hands(hands):
    hands_list = []
    hands = str(hands).split(',')
    for h in hands:
        hand = Hand.objects.filter(id=h)
        hands_list.append(hand.values())
    return hands_list

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

    return render_to_response('pages/copyright.html', context,
            context_instance=RequestContext(request))
    #page -> currentitem -> itempart -> repository.copyright_notice

def images_lightbox(request):
    if request.is_ajax():
        if 'data' in request.POST and request.POST.get('data', ''):
            graphs = simplejson.loads(request.POST.get('data', ''))
            data = {}

            if 'annotations' in graphs:
                annotations = []
                for graph in graphs['annotations']:
                    try:
                        annotation = Annotation.objects.get(graph=graph)
                        #annotation[thumbnail, graph_id, graph_label, hand_label, scribe_name, place_name, date_date, vector_id, image_id, hand_id, scribe_id, allograph, allogaph_name, character_name, manuscript]
                        try:
                            scribe = annotation.graph.hand.scribe.name
                            scribe_id = annotation.graph.hand.scribe.id
                            place_name = annotation.graph.hand.assigned_place.name
                            date = annotation.graph.hand.assigned_date.date
                        except:
                            scribe = 'Unknown'
                            scribe_id = 'Unknown'
                            place_name = 'Unknown'
                            date = 'Unknown'
                        annotations.append([annotation.thumbnail(), annotation.graph.id, annotation.graph.display_label, annotation.graph.hand.label, scribe, place_name, date, annotation.vector_id, annotation.image.id, annotation.graph.hand.id, scribe_id, annotation.graph.idiograph.allograph.human_readable(), annotation.graph.idiograph.allograph.name, annotation.graph.idiograph.allograph.character.name, annotation.image.display_label])

                    except:
                        continue

                data['annotations'] = annotations
            if 'images' in graphs:
                images = []
                for img in graphs['images']:
                    image = Image.objects.get(id=img)
                    images.append([image.thumbnail(), image.id, image.display_label, list(image.item_part.hands.values_list('label'))])
                data['images'] = images
            return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def form_dialog(request, image_id):
    image = Image.objects.get(id=image_id)
    form = ImageAnnotationForm(auto_id=False)
    form.fields['hand'].queryset = image.hands.all()
    return render_to_response('digipal/dialog.html', {'form': form}, context_instance=RequestContext(request))

@login_required
@transaction.commit_manually
def save(request, image_id, vector_id):
    """Saves an annotation and creates a cutout of the annotation."""
    try:

        data = {
            'success': False,
            'graphs': []
        }

        image = Image.objects.get(id=image_id)

        get_data = request.GET.copy()

        if 'geo_json' in get_data:
            geo_json = get_data['geo_json']
        else:
            geo_json = False
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

            if geo_json:
                annotation.geo_json = geo_json
            annotation.display_note = clean['display_note']
            annotation.internal_note = clean['internal_note']
            annotation.author = request.user
            #annotation.before = clean['before']
            #annotation.after = clean['after']

            allograph = clean['allograph']
            hand = clean['hand']

            if hand and allograph:
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

            feature_list_checked = get_data.getlist('feature')
            feature_list_unchecked = get_data.getlist('-feature')
            #graph.graph_components.all().delete()

            if feature_list_unchecked:

                for value in feature_list_unchecked:
                    print 'unchecked, ', value
                    cid, fid = value.split('::')

                    component = Component.objects.get(id=cid)
                    feature = Feature.objects.get(id=fid)
                    gc_list = GraphComponent.objects.filter(graph=graph,
                            component=component)

                    if gc_list:
                        gc = gc_list[0]
                        gc.features.remove(feature)
                        gc.save()

            if feature_list_checked:

                for value in feature_list_checked:
                    print 'checked, ', value
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

            # attach the graph to a containing one
            annotation.set_graph_group()

            annotation.save()
            new_graph = simplejson.loads(get_features(annotation.graph.id))
            data['graphs'] = new_graph

            transaction.commit()

            data['success'] = True
        else:
            transaction.rollback()
            data['errors'] = get_json_error_from_form_errors(form)
    except Exception as e:
        transaction.rollback()
        data['errors'] = ['Internal error: %s' % e.message]
        #tb = sys.exc_info()[2]

    return HttpResponse(simplejson.dumps(data), mimetype='application/json')


def get_json_error_from_form_errors(form):
    '''Returns a list of errors from a set of Django form errors.
        E.g. ['Allograph: this field is required.', 'Hand: this field is required.']
    '''
    ret = []
    for field_name in form.errors:
        ret.append('%s: %s' % (field_name.title(), form.errors[field_name].as_text()))
    return ret

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
            if annotation.graph:
                annotation.graph.delete()
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
