from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.utils.datastructures import SortedDict
from digipal.models import *
from digipal.forms import DrilldownForm, SearchPageForm
from itertools import islice, chain
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import logging
dplog = logging.getLogger('digipal_debugger')

def get_search_types():
    from content_type.search_hands import SearchHands
    from content_type.search_manuscripts import SearchManuscripts
    from content_type.search_scribes import SearchScribes
    ret = [SearchHands(), SearchManuscripts(), SearchScribes()]
    return ret

def get_search_types_display(content_types):
    ''' returns the content types as a string like this:
        'Hands', 'Scribes' or 'Manuscripts' 
    '''
    ret = ''
    for type in content_types:
        if ret:
            if type == content_types[-1]:
                ret += ' or '
            else:
                ret += ', '        
        ret += '\'%s\'' % type.label
    return ret

def search_page(request):
    template = 'search/search_page_results.html'
    
    context = {}
    context['terms'] = ''
    context['submitted'] = ('basic_search_type' in request.GET) or ('terms' in request.GET)
    context['can_edit'] = has_edit_permission(request, Hand)
    context['types'] = get_search_types()
    context['search_types_display'] = get_search_types_display(context['types'])
    record_type = ''

    advanced_search_form = SearchPageForm(request.GET)
    advanced_search_form.fields['basic_search_type'].choices = [(type.key, type.label) for type in context['types']]

    if context['submitted'] and advanced_search_form.is_valid():
        # TODO: if we are on the record page, don't do all the searches, only one
        # TODO: review the phrase search to make more flexible 
        
        # Read the inputs
        # - term
        term = advanced_search_form.cleaned_data['terms']
        context['terms'] = term or ' '
        
        # - search type
        search_type = advanced_search_form.cleaned_data['basic_search_type']
        context['search_type'] = search_type
        
        # - specific record
        #if request.GET.get('record', '') or request.GET.get('id', ''):
        if request.GET.get('id', ''):
            record_type = request.GET.get('result_type', '')
        
        # Searches by content types
        for type in context['types']:
            if record_type in ['', type.key]:
                context['results'] = type.build_queryset(request, term)

        # Tab Selection Logic =
        #     we pick the tab the user has selected
        #     if none, we select a tab with non empty result
        #        with preference for already selected tab 
        #     if none we select the first type
        result_type = request.GET.get('result_type', '')
        if not result_type:
            for type in context['types']:
                if not type.is_empty:
                    result_type = type.key
                    if type.key == search_type:
                        break
                    
        result_type = result_type or context['types'][0].key
        context['result_type'] = result_type

    # Distinguish between requests for one record and search results
    if record_type:
        context['id'] = request.GET.get('id', '')
        #context['record'] = request.GET.get('record', '')
        
        for type in context['types']:
            if type.key == record_type:
                type.set_record_view_context(context)
                type.set_record_view_pagination_context(context, request)
        
        template = 'pages/record_' + record_type +'.html'
        
    if not record_type:
        from django.utils import simplejson
        context['advanced_search_form'] = advanced_search_form
        context['drilldownform'] = DrilldownForm({'terms': context['terms'] or ''})
        context['search_page_options_json'] = simplejson.dumps(get_search_page_js_data(context['types'], 'from_link' in request.GET))
    
    return render_to_response(template, context, context_instance=RequestContext(request))

def get_search_page_js_data(content_types, expanded_search=False):
    filters = []
    for type in content_types:
        filters.append({
                         'html': type.form.as_ul(),
                         'label': type.label
                         })        
    
    ret = {
        'advanced_search_expanded': expanded_search or any([type.is_advanced_search for type in content_types]),
        'filters': filters,
    };
    
    return ret




def allographHandSearch(request):
    """ View for Hand record drill-down """
    term = request.GET.get('terms', '')
    allograph = request.GET.get('allograph_select', '')
    character = request.GET.get('character_select', '')
    # Adding 2 new filter values...
    feature = request.GET.get('feature_select', '')
    component = request.GET.get('component_select', '')

    context = {}
    context['style']= 'allograph_list'
    context['term'] = term

    hand_ids = Hand.objects.order_by('item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'descriptions__description','id').filter(
            Q(descriptions__description__icontains=term) | \
            Q(scribe__name__icontains=term) | \
            Q(assigned_place__name__icontains=term) | \
            Q(assigned_date__date__icontains=term) | \
            Q(item_part__current_item__shelfmark__icontains=term) | \
            Q(item_part__current_item__repository__name__icontains=term) | \
            Q(item_part__historical_item__catalogue_number__icontains=term))
    handlist = []
    for h in hand_ids:
        handlist.insert(0, h.id)

    graphs = Graph.objects.filter(hand__in=handlist).order_by('hand')

    if allograph:
        graphs = graphs.filter(
            idiograph__allograph__name=allograph).order_by('hand')
        context['allograph'] = Allograph.objects.filter(name=allograph)
    if feature:
        graphs = graphs.filter(
            graph_components__features__name=feature).order_by('hand')
        context['feature'] = Feature.objects.get(name=feature)
    if character:
        graphs = graphs.filter(
            idiograph__allograph__character__name=character).order_by('hand')
        context['character'] = Character.objects.get(name=character)
    if component:
        graphs = graphs.filter(
            graph_components__component__name=component).order_by('hand')
        context['component'] = Component.objects.get(name=component)

    graphs = graphs.order_by('hand__scribe__name','hand__id')
    context['drilldownform'] = DrilldownForm()
    context['graphs'] = graphs

    page = request.GET.get('page')
  
    paginator = Paginator(graphs, 24)

    try:
        page_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page_list = paginator.page(paginator.num_pages)

    context['page_list'] = page_list

    try:
        context['view'] = request.COOKIES['view']
    except:
        context['view'] = 'Images'

    return render_to_response(
        'pages/new-image-view.html',
        context,
        context_instance=RequestContext(request))


def allographHandSearchGraphs(request):
    """ View for Hand record drill-down """
    allograph = request.GET.get('allograph_select', '')
    character = request.GET.get('character_select', '')
    # Adding 2 new filter values...
    feature = request.GET.get('feature_select', '')
    component = request.GET.get('component_select', '')

    context = {}
    context['style']= 'allograph_list'
    
    hand_ids = Hand.objects.order_by('item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'description','id')
    
    handlist = []
    for h in hand_ids:
        handlist.insert(0, h.id)

    graphs = Graph.objects.filter(hand__in=handlist).order_by('hand')

    if allograph:
        graphs = graphs.filter(
            idiograph__allograph__name=allograph).order_by('hand')
        context['allograph'] = Allograph.objects.filter(name=allograph)
    if feature:
        graphs = graphs.filter(
            graph_components__features__name=feature).order_by('hand')
        context['feature'] = Feature.objects.get(name=feature)
    if character:
        graphs = graphs.filter(
            idiograph__allograph__character__name=character).order_by('hand')
        context['character'] = Character.objects.get(name=character)
    if component:
        graphs = graphs.filter(
            graph_components__component__name=component).order_by('hand')
        context['component'] = Component.objects.get(name=component)

    graphs = graphs.order_by('hand__scribe__name','hand__id')
    context['drilldownform'] = DrilldownForm()
    context['graphs'] = graphs

    page = request.GET.get('page')
  
    paginator = Paginator(graphs, 24)

    try:
        page_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page_list = paginator.page(paginator.num_pages)

    context['page_list'] = page_list

    try:
        context['view'] = request.COOKIES['view']
    except:
        context['view'] = 'Images'

    return render_to_response(
        'pages/graphs-list.html',
        context,
        context_instance=RequestContext(request))

def graphsSearch(request):
    context = {}

    context['style']= 'allograph_list'
    
    context['drilldownform'] = DrilldownForm()

    return render_to_response(
        'pages/graphs.html',
        context,
        context_instance=RequestContext(request))

