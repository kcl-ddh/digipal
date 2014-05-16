# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.db import transaction
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.utils.datastructures import SortedDict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import sys, re
from django import template
from django.template import Context
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import ensure_csrf_cookie


from digipal.forms import ImageAnnotationForm
from digipal.models import Allograph, AllographComponent, Annotation, Hand, \
        GraphComponent, Graph, Component, Feature, Idiograph, Image, Repository, \
        has_edit_permission
import ast
from django import template
from django.conf import settings
from digipal.templatetags.hand_filters import chrono


register = template.Library()

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def get_content_type_data(request, content_type, ids=None, only_features=False):
    ''' General handler for API requests.
        if @callback=X in the query string a JSONP response is returned
    '''
    mimetype = 'application/json'

    data = None

    # Support for JSONP responses
    jsonpcallback = request.REQUEST.get('@callback', None)
    if jsonpcallback is not None:
        if not re.match(ur'(?i)^\w+$', jsonpcallback):
            # invalid name format for the callback
            data = {'success': False, 'errors': ['Invalid JSONP callback name format.'], 'results': []}
            import json
            data = json.dumps(data)
            jsonpcallback = None

    if not data:
        if ids: ids = str(ids)
        if content_type == 'graph':
            data = get_features(ids, only_features)
        elif content_type == 'allograph':
            data = allograph_features(request, ids)
        elif content_type == 'hand':
            data = get_hands(ids)
        else:
            from digipal.api.generic import API
            data = API.process_request(request, content_type, ids)

    # JSON -> JSONP
    if jsonpcallback:
        data = u';%s(%s);' % (jsonpcallback, data)
        mimetype = 'text/javascript'

    return HttpResponse(data, mimetype=mimetype)

def get_list_from_csv(csv):
    '''Returns a list of numbers from a comma separated string.
        Empty values are ignored.
        E.g. get_list_from_csv('1,2') => [1, 2]
            get_list_from_csv('') => []
    '''
    ret = []

    if csv:
        ret = [int(v) for v in csv.split(',') if v]

    return ret

def get_features(graph_id, only_features=False):
    data = []
    allographs_cache = []
    graphs_ids = str(graph_id).split(',')
    graphs = Graph.objects.filter(id__in=graphs_ids).select_related('graph_components', 'hand', 'idiograph', 'image')
    for graph in graphs:
        obj = {}
        dict_features = list([])
        a = graph.idiograph.allograph.id
        graph_components = graph.graph_components

        if not only_features and not a in allographs_cache:
            allograph = allograph_features(False, a)
            obj['allographs'] = allograph
            allographs_cache.append(a)

        vector_id = graph.annotation.vector_id
        hand_id = graph.hand.id
        allograph_id = graph.idiograph.allograph.id
        image_id = graph.annotation.image.id
        hands_list = []
        item_part = graph.annotation.image.item_part.id
        hands = graph.annotation.image.hands.all()

        for hand in hands:
            h = {
                'id': hand.id,
                'label': hand.label
            }
            hands_list.append(h)

        for component in graph_components.all():
            name_component = component.component.name
            if component.features.count > 0:
                for feature in component.features.all():
                    dict_features.append({"graph_component_id": component.id, 'component_id': component.component.id, 'name': name_component, 'feature': [feature.name]})

        obj['features'] = dict_features
        obj['vector_id'] = vector_id
        obj['image_id'] = image_id
        obj['hand_id'] = hand_id
        obj['allograph_id'] = allograph_id
        obj['hands'] = hands_list
        obj['graph'] = graph.id
        obj['item_part'] = item_part
        data.append(obj)

    return simplejson.dumps(data)


def allograph_features(request, allograph_id):
    """Returns a JSON of all the features for the requested allograph, grouped
    by component."""
    allographs_ids = str(allograph_id).split(',')
    obj = {}
    data = []
    allographs = Allograph.objects.filter(id__in=allographs_ids).select_related('allograph_components__component')
    for allograph in allographs:
        allograph_components = allograph.allograph_components.all()
        allographs_list = []
        if allograph_components:
            for ac in allograph_components:
                ac_dict = {}
                ac_dict['id'] = ac.component.id
                ac_dict['name'] = ac.component.name
                ac_dict['features'] = []
                ac_dict['default'] = []
                for f in ac.component.features.all():
                    ac_dict['features'].append({'id': f.id, 'name': f.name})
                    if f.componentfeature_set.all()[0].set_by_default:
                        ac_dict['default'].append({'component': f.componentfeature_set.all()[0].component.id, 'feature': f.componentfeature_set.all()[0].feature.id})
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

    images = Image.sort_query_set_by_locus(image.item_part.images.exclude(id=image.id), True)
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
    zoom_levels = settings.ANNOTATOR_ZOOM_LEVELS
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
               'zoom_levels': zoom_levels,
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

    if request:
        return HttpResponse(simplejson.dumps(data), mimetype='application/json')
    else:
        return simplejson.dumps(data)

def get_vector(request, image_id, graph):
    annotation = Annotation.objects.get(graph=graph)
    data = {}
    data['vector_id'] = ast.literal_eval(annotation.geo_json.strip())
    data['id'] = annotation.vector_id
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def image_annotations(request, image_id, annotations_page=True, hand=False):
    """Returns a JSON of all the annotations for the requested image."""

    if annotations_page:
        annotation_list = Annotation.objects.filter(image=image_id).select_related('image', 'graph')
    else:
        annotation_list = Annotation.objects.filter(graph__hand=hand).select_related('image', 'graph')

    vectors = simplejson.loads(image_vectors(False, image_id))
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
        data[a.id]['allograph_id'] = a.graph.idiograph.allograph.id
        features_list = simplejson.loads(get_features(a.graph.id, True))
        data[a.id]['num_features'] = len(features_list[0]['features'])
        data[a.id]['features'] = features_list
        if vectors[a.vector_id]:
            data[a.id]['geo_json'] = vectors[a.vector_id]['geometry']

        #hands.append(data[a.id]['hand'])

        hand = a.graph.hand.label
        hands.append(a.graph.hand.id)

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

def get_allographs_by_graph(request, image_id, graph_id):
        graph = Graph.objects.get(id=graph_id)
        feature = graph.idiograph.allograph.name
        character_id = graph.idiograph.allograph.character.id
        annotations = Annotation.objects.filter(graph__idiograph__allograph__name=feature, graph__idiograph__allograph__character__id=character_id, image=image_id).select_related('graph', 'graph__hand').order_by('id')
        annotations_list = []
        if annotations:
            for i in annotations:
                annotation = {
                    'hand': i.graph.hand.id,
                    'hand_name': i.graph.hand.label,
                    'image': i.thumbnail(),
                    'id': i.graph.id,
                    'vector_id': i.vector_id
                }
                annotations_list.append(annotation)
            return HttpResponse(simplejson.dumps(annotations_list), mimetype='application/json')
        else:
            return HttpResponse(False)

def get_allographs_by_allograph(request, image_id, character_id, allograph_id):
    annotations = Annotation.objects.filter(graph__idiograph__allograph__id=allograph_id, graph__idiograph__allograph__character__id=character_id, image=image_id).select_related('graph', 'graph__hand').order_by('id')
    annotations_list = []
    if annotations:
        for i in annotations:
            annotation = {
                'hand': i.graph.hand.id,
                'hand_name': i.graph.hand.label,
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
    annotations = Annotation.objects.filter(image=image_id).select_related('graph')

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
    hands_ids = simplejson.loads(request.GET.get('hands', ''))
    hands_list = Hand.objects.filter(id__in=hands_ids)
    hands = []
    for h in hands_list:
        hands.append(h.display_label)
    return HttpResponse(simplejson.dumps(hands), mimetype='application/json')

def get_hands(hands):
    hands_list = []
    hands_ids = str(hands).split(',')
    hands = Hand.objects.filter(id__in=hands_ids)
    for h in hands:
        hands_list.append(h.values())
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
    #image = Image.objects.get(id=image_id)
    #repositories = Repository.objects.filter(currentitem__itempart__images=image_id)
    #context['copyright'] = repository.values_list('copyright_notice', flat = True)
    # TODO: check this path

    return render_to_response('pages/copyright.html', context,
            context_instance=RequestContext(request))
    #page -> currentitem -> itempart -> repository.copyright_notice

@ensure_csrf_cookie
def images_lightbox(request, collection_name):
    data = {}
    if 'data' in request.POST and request.POST.get('data', ''):
        graphs = simplejson.loads(request.POST.get('data', ''))
        if 'annotations' in graphs:
            annotations = []
            annotations_list = Annotation.objects.filter(graph__in=graphs['annotations'])
            for annotation in annotations_list:
                try:
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
            images_list = Image.objects.filter(id__in=graphs['images'])
            for image in images_list:
                images.append([image.thumbnail(100, 100), image.id, image.display_label, list(image.item_part.hands.values_list('label'))])
            data['images'] = images
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')

def form_dialog(request, image_id):
    image = Image.objects.get(id=image_id)
    form = ImageAnnotationForm(auto_id=False)
    form.fields['hand'].queryset = image.hands.all()
    return render_to_response('digipal/dialog.html', {'form': form, 'edit_annotation_shape': getattr(settings, 'EDIT_ANNOTATION_SHAPE', False)}, context_instance=RequestContext(request))

@login_required
@transaction.commit_manually
def save(request, graphs):

    """Saves an annotation and creates a cutout of the annotation."""

    if settings.REJECT_HTTP_API_REQUESTS:
        transaction.rollback()
        raise Http404
    else:

        data = {
            'success': False,
            'graphs': []
        }

        try:

            graphs = graphs.replace('/"', "'")
            graphs = simplejson.loads(graphs)

            for gr in graphs:
                graph_object = False

                if 'id' in gr:
                    graph_object = Graph.objects.get(id=gr['id'])

                image = Image.objects.get(id=gr['image'])
                annotation_is_modified = False
                if graph_object:
                    annotation = graph_object.annotation
                    graph = graph_object
                else:
                    graph = Graph()
                    annotation = Annotation(image=image, vector_id=gr['vector_id'])

                get_data = request.GET.copy()

                if 'geoJson' in gr:
                    geo_json = str(gr['geoJson'])
                else:
                    geo_json = False


                form = ImageAnnotationForm(data=get_data)
                if form.is_valid():
                    clean = form.cleaned_data
                    if geo_json:
                        annotation.geo_json = geo_json
                        annotation_is_modified = True
                    # set the note (only if different) - see JIRA DIGIPAL-477
                    for f in ['display_note', 'internal_note']:
                        if getattr(annotation, f) != clean[f]:
                            setattr(annotation, f, clean[f])
                            annotation_is_modified = True
                    if not annotation.id:
                        # set the author only when the annotation is created
                        annotation.author = request.user
                    #annotation.before = clean['before']
                    #annotation.after = clean['after']
                    allograph = clean['allograph']
                    hand = clean['hand']
                    if hand and allograph:

                        scribe = hand.scribe

                        # GN: if this is a new Graph, it has no idiograph yet, so we test this first
                        if graph.id and (allograph.id != graph.idiograph.allograph.id):
                            graph.graph_components.all().delete()

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


                    if feature_list_unchecked:

                        for value in feature_list_unchecked:

                            cid, fid = value.split('::')

                            component = Component.objects.get(id=cid)
                            feature = Feature.objects.get(id=fid)
                            gc_list = GraphComponent.objects.filter(graph=graph,
                                    component=component)

                            if gc_list:
                                gc = gc_list[0]
                                gc.features.remove(feature)
                                gc.save()

                                if not gc.features.all():
                                    gc.delete()

                    if feature_list_checked:

                        for value in feature_list_checked:

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

                    # attach the graph to a containing one
                    if geo_json:
                        annotation.set_graph_group()
                    # Only save the annotation if it has been modified (or new one)
                    # see JIRA DIGIPAL-477
                    if annotation_is_modified or not annotation.id:
                        annotation.graph = graph
                        annotation.save()
                    new_graph = simplejson.loads(get_features(graph.id))
                    data['graphs'].append(new_graph[0])

                    transaction.commit()
                    data['success'] = True
                else:
                    transaction.rollback()
                    data['success'] = False
                    data['errors'] = get_json_error_from_form_errors(form)

        except Exception as e:
            transaction.rollback()
            data['success'] = False
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

    if settings.REJECT_HTTP_API_REQUESTS:
        transaction.rollback()
        raise Http404

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
