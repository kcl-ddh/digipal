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


from digipal.forms import ImageAnnotationForm, FilterManuscriptsImages
from digipal.models import Allograph, AllographComponent, Annotation, Hand, \
        GraphComponent, Graph, Component, Feature, Idiograph, Image, Repository, \
        has_edit_permission
import ast
from django import template

register = template.Library()



def get_features(request, image_id, graph_id, return_request=True):
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
    if return_request:
        return HttpResponse(simplejson.dumps(dict_features), mimetype='application/json')
    else:
        return dict_features

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
    hands_list = []
    hand = {}
    hands_object = Hand.objects.filter(images=image_id)

    for h in hands_object.values():
        if h['label'] == None:
            label = "None"
        else:
            label = mark_safe(h['label'])
            print label
        hand = {'id': h['id'], 'name': label.encode('cp1252')}
        hands_list.append(hand)

    image_link = urlresolvers.reverse('admin:digipal_image_change', args=(image.id,))
    form = ImageAnnotationForm()

    form.fields['hand'].queryset = image.hands.all()

    width, height = image.dimensions()
    image_server_url = image.zoomify

    is_admin = has_edit_permission(request, Image)

    from digipal.models import OntographType

    context = {
               'form': form, 'image': image, 'height': height, 'width': width,
               'image_server_url': image_server_url, 'hands_list': hands_list,
               'image_link': image_link, 'annotations': annotations,
               'hands': hands, 'is_admin': is_admin,
               'no_image_reason': image.get_media_unavailability_reason(request.user),
               'can_edit': has_edit_permission(request, Annotation),
               'ontograph_types': OntographType.objects.order_by('name'),
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

def image_annotations(request, image_id, annotations_page=True, hand=False):
    """Returns a JSON of all the annotations for the requested image."""
    if annotations_page:
        annotation_list = Annotation.objects.filter(image=image_id)
    else:
        annotation_list = Annotation.objects.filter(graph__hand=hand)

    data = {}
    for a in annotation_list:
        data[a.id] = {}
        data[a.id]['vector_id'] = a.vector_id
        data[a.id]['status_id'] = a.status_id
        data[a.id]['image_id'] = a.image.id
        data[a.id]['hidden_hand'] = a.graph.hand.id
        data[a.id]['character'] = a.graph.idiograph.allograph.character.name
        data[a.id]['hand'] = a.graph.hand_id
        data[a.id]['character_id'] = a.graph.idiograph.allograph.character.id
        features_list = get_features(request, a.image.id, a.graph_id, False)
        data[a.id]['num_features'] = len(features_list)
        data[a.id]['features'] = features_list
        #hands.append(data[a.id]['hand'])

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
                'vector_id': i.vector_id
            }
            annotations_list.append(annotation)
        return HttpResponse(simplejson.dumps(annotations_list), mimetype='application/json')
    else:
        return HttpResponse(False)

def image_allographs(request, image_id):
    """Returns a list of all the allographs/annotations for the requested
    image."""
    annotation_list = Annotation.objects.filter(image=image_id)
    image = Image.objects.get(id=image_id)
    image_link = urlresolvers.reverse('admin:digipal_image_change', args=(image.id,))
    form = ImageAnnotationForm()
    hands = []
    form.fields['hand'].queryset = image.hands.all()

    width, height = image.dimensions()
    image_server_url = image.zoomify

    #is_admin = request.user.is_superuser
    is_admin = has_edit_permission(request, Image)

    data = SortedDict()

    for annotation in annotation_list:
        hand = annotation.graph.hand
        hands.append(hand.id)
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
             'hands': list(set(hands)),
             'data': data,
             'form': form,
             'can_edit': has_edit_permission(request, Annotation)},
            context_instance=RequestContext(request))

def hands_list(request, image_id):
    hands_list = simplejson.loads(request.GET.get('hands', ''))
    hands = []
    for i in hands_list:
        h = Hand.objects.get(id=i)
        hands.append(h.display_label)
    return HttpResponse(simplejson.dumps(hands), mimetype='application/json')

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
        images = images.filter(item_part__current_item__repository__name=repository_name,item_part__current_item__repository__place__name=repository_place)
    if date:
        images = images.filter(hands__assigned_date__date = date)

    images = images.filter(item_part_id__gt = 0)
    images = Image.sort_query_set_by_locus(images)

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

    for page in page_list:
        page.view_thumbnail = page.thumbnail(None, 210)

    context = {}
    context['page_list'] = page_list
    context['filterImages'] = filterImages
    try:
        context['view'] = request.COOKIES['view']
    except:
        context['view'] = 'Images'

    return render_to_response('digipal/image_list.html', context, context_instance=RequestContext(request))

def images_lightbox(request):
    if request.is_ajax():
        if 'data' in request.POST and request.POST.get('data', ''):
            graphs = simplejson.loads(request.POST.get('data', ''))
            print graphs
            data = {}
            if 'annotations' in graphs:
                annotations = []
                for graph in graphs['annotations']:
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
                data['annotations'] = annotations
            if 'images' in graphs:
                images = []
                for img in graphs['images']:
                    image = Image.objects.get(id=img)
                    images.append([image.thumbnail(), image.id, image.display_label, list(image.item_part.hands.values_list('label'))])
                data['images'] = images
            return HttpResponse(simplejson.dumps(data), mimetype='application/json')



@login_required
@transaction.commit_manually
def save(request, image_id, vector_id):
    """Saves an annotation and creates a cutout of the annotation."""
    try:
        data = {'success': False}

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

            # attach the graph to a containing one
            annotation.set_graph_group()

            annotation.save()

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
