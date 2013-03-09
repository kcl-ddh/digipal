from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.utils.datastructures import SortedDict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from digipal.forms import PageAnnotationForm, FilterManuscriptsImages
from digipal.models import Allograph, AllographComponent, Annotation, \
        GraphComponent, Graph, Component, Feature, Idiograph, Page
import ast
from django import template
from django.views.generic import DetailView

register = template.Library()

def allograph_features(request, page_id, allograph_id):
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

def page(request, page_id):
    """Returns a page annotation form."""
    page = Page.objects.get(id=page_id)
    annotations = page.annotation_set.values('graph').count()
    hands = page.hand_set.count()
    # Check for a vector_id in page referral, if it exists the request has
    # come via Scribe/allograph route
    vector_id = request.GET.get('vector_id', '')

    page_link = urlresolvers.reverse('admin:digipal_page_change', args=(page.id,))
    form = PageAnnotationForm()

    form.fields['hand'].queryset = page.hand_set.all()

    width, height = page.dimensions()
    image_server_url = page.zoomify

    if request.user.is_superuser:
        isAdmin = True
    else:
        isAdmin = False

    if vector_id:
        return render_to_response('digipal/page_annotation.html',
                {'vector_id': vector_id, 'form': form, 'page': page,
                    'height': height, 'width': width,
                    'image_server_url': image_server_url,
                    'page_link': page_link, 'annotations': annotations, 'hands': hands, 'isAdmin': isAdmin},
                context_instance=RequestContext(request))
    else:
        return render_to_response('digipal/page_annotation.html',
                {'form': form, 'page': page, 'height': height, 'width': width,
                    'image_server_url': image_server_url,
                    'page_link': page_link, 'annotations': annotations, 'hands': hands, 'isAdmin': isAdmin},
                context_instance=RequestContext(request))


def page_vectors(request, page_id):
    """Returns a JSON of all the vectors for the requested page."""
    annotation_list = Annotation.objects.filter(page=page_id)

    data = {}

    for a in annotation_list:
        data[a.vector_id] = ast.literal_eval(a.geo_json.strip())

    return HttpResponse(simplejson.dumps(data), mimetype='application/json')


def page_annotations(request, page_id):
    """Returns a JSON of all the annotations for the requested page."""
    annotation_list = Annotation.objects.filter(page=page_id)

    data = {}

    for a in annotation_list:
        data[a.id] = {}
        data[a.id]['vector_id'] = a.vector_id
        data[a.id]['status_id'] = a.status_id
        data[a.id]['hand_id'] = a.graph.hand.id

        if a.before:
            data[a.id]['before'] = '%d::%s' % (a.before.id, a.before.name)

        data[a.id]['allograph'] = '%d::%s' % (a.graph.idiograph.allograph.id,
            a.graph.idiograph.allograph.name)

        data[a.id]['feature'] = '%s' % (a.graph.idiograph.allograph)

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


def page_allographs(request, page_id):
    """Returns a list of all the allographs/annotations for the requested
    page."""
    annotation_list = Annotation.objects.filter(page=page_id)
    page = Page.objects.get(id=page_id)
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

    return render_to_response('digipal/page_allograph.html',
            {'page': page, 'data': data},
            context_instance=RequestContext(request))

def page_metadata(request, page_id):
    """Returns a list of all the allographs/annotations for the requested
    page."""
    context = {}
    page = Page.objects.get(id=page_id)
    context['page'] = page

    return render_to_response('pages/record_pages.html',
            context,
            context_instance=RequestContext(request))

def page_copyright(request, page_id):
    context = {}
    page = Page.objects.get(id=page_id)
    context['page'] = page
    return render_to_response('pages/copyright.html', context,
            context_instance=RequestContext(request))

def page_list(request):
    pages = Page.objects.all()
    
    # Get Buttons

    town_or_city = request.GET.get('town_or_city', '')
    repository = request.GET.get('repository', '')
    date = request.GET.get('date', '')

    # Applying filters
    if town_or_city:
        pages = pages.filter(hand__assigned_place__name = town_or_city)
    if repository:
        pages = pages.filter(item_part__current_item__repository__name = repository)
    if date:
        pages = pages.filter(hand__assigned_date__date = date)

    paginator = Paginator(pages, 24)
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

    return render_to_response('digipal/page_list.html', context, context_instance=RequestContext(request))



@login_required
@transaction.commit_manually
def save(request, page_id, vector_id):
    """Saves an annotation and creates a cutout of the annotation."""
    try:
        data = {}

        page = Page.objects.get(id=page_id)

        get_data = request.GET.copy()
        geo_json = get_data['geo_json']

        annotation_list = Annotation.objects.filter(page=page,
                vector_id=vector_id)

        if annotation_list:
            annotation = annotation_list[0]
            graph = annotation.graph
        else:
            annotation = Annotation(page=page, vector_id=vector_id)
            graph = Graph()

        form = PageAnnotationForm(data=get_data)

        if form.is_valid():
            clean = form.cleaned_data

            annotation.geo_json = geo_json
            annotation.display_note = clean['display_note']
            annotation.internal_note = clean['internal_note']
            annotation.author = request.user
            annotation.before = clean['before']
            annotation.after = clean['after']

            allograph = clean['allograph']
            hand = clean['hand']
            scribe = hand.scribe

            idiograph_list = Idiograph.objects.filter(allograph=allograph,
                    scribe=scribe)

            if idiograph_list:
                idiograph = idiograph_list[0]
            else:
                idiograph = Idiograph(allograph=allograph, scribe=scribe)
                idiograph.save()

            graph.idiograph = idiograph
            graph.hand = hand
            graph.save()

            feature_list = get_data.getlist('feature')

            if feature_list:
                graph.graph_components.all().delete()

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

        return HttpResponse(simplejson.dumps(data),
                mimetype='application/json')

    return HttpResponse(simplejson.dumps(data), mimetype='application/json')


@login_required
@transaction.commit_manually
def delete(request, page_id, vector_id):
    """Deletes the annotation related with the `page_id` and `feature_id`."""
    data = {}

    try:
        page = get_object_or_404(Page, pk=page_id)

        try:
            annotation = Annotation.objects.get(page=page, vector_id=vector_id)
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
