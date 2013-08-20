from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.utils.datastructures import SortedDict
from digipal.models import *
from digipal.forms import DrilldownForm, SearchPageForm
from itertools import islice, chain
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings

import logging
dplog = logging.getLogger('digipal_debugger')

def get_search_types():
    from content_type.search_hands import SearchHands
    from content_type.search_manuscripts import SearchManuscripts
    from content_type.search_scribes import SearchScribes
    #from content_type.search_graphs import SearchGraphs
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

def record_view(request, content_type='', objectid=''):
    context = {}
    
    # We need to do a search to show the next and previous record
    # Only when we come from the the search image.
    set_search_results_to_context(request, allowed_type=content_type, context=context)
    
    for type in context['types']:
        if type.key == content_type:
            context['id'] = objectid
            type.set_record_view_context(context)
            type.set_record_view_pagination_context(context, request)
            break
    
    template = 'pages/record_' + content_type +'.html'
    
    return render_to_response(template, context, context_instance=RequestContext(request))

def search_page_view(request):
    # Backward compatibility.
    #
    # Previously all the record pages would go through this search URL and view
    # and their URL was: 
    #     /digipal/search/?id=1&result_type=scribes&basic_search_type=hands&terms=Wulfstan
    # Now we redirect those requests to the record page
    #     /digipal/scribes/1/?basic_search_type=hands&terms=Wulfstan+&result_type=scribes
    qs_id = request.GET.get('id', '')
    qs_result_type = request.GET.get('result_type', '')
    if qs_id and qs_result_type:
        from django.shortcuts import redirect
        # TODO: get digipal from current project name or current URL
        redirect_url = '/%s/%s/%s/?%s' % ('digipal', qs_result_type, qs_id, request.META['QUERY_STRING'])
        return redirect(redirect_url)
    
    # Actually run the searches
    context = {}
    set_search_results_to_context(request, context=context, show_advanced_search_form=True)

    # check if the search was executed or not (e.g. form not submitted or invalid form)
    if context.has_key('results'):
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
                    if type.key == context['search_type']:
                        break
        
        result_type = result_type or context['types'][0].key
        context['result_type'] = result_type

        # No result at all?
        for type in context['types']:
            if not type.is_empty:
                context['is_empty'] = False
        if context['is_empty']:
            context['search_help_url'] = get_cms_url_from_slug(getattr(settings, 'SEARCH_HELP_PAGE_SLUG', 'search_help'))

    # Initialise the search forms 
    from django.utils import simplejson
    context['drilldownform'] = DrilldownForm({'terms': context['terms'] or ''})
    context['search_page_options_json'] = simplejson.dumps(get_search_page_js_data(context['types'], 'from_link' in request.GET))
    
    from digipal.models import RequestLog
    RequestLog.save_request(request, sum([type.count for type in context['types']]))

    return render_to_response('search/search_page_results.html', context, context_instance=RequestContext(request))

def set_search_results_to_context(request, context={}, allowed_type=None, show_advanced_search_form=False):
    ''' Read the information posted through the search form and create the queryset
        for each relevant type of content (e.g. MS, Hand) => context['results']
        
        If the form was not valid or submitted, context['results'] is left undefined.
        
        Other context variables used by the search template are also set.        
    '''    
    
    # allowed_type: this variable is used to restrict the search to one content type only.
    # This is useful when we display a specific record page and we only
    # have to search for the related content type to show the previous/next links.
    #allowed_type = kwargs.get('allowed_type', None)
    #context = kwargs.get('context', {})
    
    context['terms'] = ''
    context['submitted'] = ('basic_search_type' in request.GET) or ('terms' in request.GET)
    context['can_edit'] = has_edit_permission(request, Hand)
    context['types'] = get_search_types()
    context['search_types_display'] = get_search_types_display(context['types'])
    context['is_empty'] = True

    advanced_search_form = SearchPageForm(request.GET)
    advanced_search_form.fields['basic_search_type'].choices = [(type.key, type.label) for type in context['types']]
    if show_advanced_search_form:
        context['advanced_search_form'] = advanced_search_form

    if context['submitted'] and advanced_search_form.is_valid():
        # Read the inputs
        # - term
        term = advanced_search_form.cleaned_data['terms']
        context['terms'] = term or ' '
        
        # - search type
        context['search_type'] = advanced_search_form.cleaned_data['basic_search_type']
        
        # Create the queryset for each allowed content type.
        # If allowed_types is None, search for each supported content type.
        for type in context['types']:
            if allowed_type in [None, type.key]:
                context['results'] = type.build_queryset(request, term)

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

def get_cms_url_from_slug(slug):
    from mezzanine.pages.models import Page as MPage 
    for page in MPage.objects.filter(slug__iendswith='how-to-use-digipal'):
        return page.get_absolute_url()
    return u'/%s' % slug

def allographHandSearch(request):
    """ View for Hand record drill-down """
    context = {}

    term = request.GET.get('terms', '').strip()
    script = request.GET.get('script_select', '')
    character = request.GET.get('character_select', '')
    allograph = request.GET.get('allograph_select', '')
    component = request.GET.get('component_select', '')
    feature = request.GET.get('feature_select', '')
    context['submitted'] = request.GET.get('submitted', '') or term or script or character or allograph or component or feature
    context['style']= 'allograph_list'
    context['term'] = term
    
    from datetime import datetime
    
    t0 = datetime.now()
    t4 = datetime.now()
    
    if context['submitted']:
        # .order_by('item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'descriptions__description','id')
        # Although we are listing hands on the front-end, we search for graphs and not for hand.
        # Two reasons: 
        #    searching for character and allograh at the same time through a Hand model would generate two separate joins to graph
        #        this would bring potentially invalid results and it is also much slower
        #    it is faster than excluding all the hands without a graph (yet another expensive join)
        #
        if term:
            graphs = Graph.objects.filter(
                    Q(hand__descriptions__description__icontains=term) | \
                    Q(hand__scribe__name__icontains=term) | \
                    Q(hand__assigned_place__name__icontains=term) | \
                    Q(hand__assigned_date__date__icontains=term) | \
                    Q(hand__item_part__current_item__shelfmark__icontains=term) | \
                    Q(hand__item_part__current_item__repository__name__icontains=term) | \
                    Q(hand__item_part__historical_items__catalogue_number__icontains=term))
        else:
            graphs = Graph.objects.all()
            
        t1 = datetime.now()
        
        combine_component_and_feature = True
    
        wheres = []
        if script:
            graphs = graphs.filter(hand__script__name=script)
            context['script'] = Script.objects.get(name=script)
        if character:
            graphs = graphs.filter(
                idiograph__allograph__character__name=character)
            context['character'] = Character.objects.get(name=character)
        if allograph:
            graphs = graphs.filter(
                idiograph__allograph__name=allograph)
            context['allograph'] = Allograph.objects.filter(name=allograph)
        if component:
            wheres.append(Q(graph_components__component__name=component) | Q(idiograph__allograph__allograph_components__component__name=component))
            context['component'] = Component.objects.get(name=component)
        if feature:
            wheres.append(Q(graph_components__features__name=feature))
            context['feature'] = Feature.objects.get(name=feature)

        # ANDs all the Q() where clauses together
        if wheres:
            where_and = wheres.pop(0)
            for where in wheres:
                where_and = where_and & where    
            
            graphs = graphs.filter(where_and)
        
        t2 = datetime.now()
    
        # Get the graphs then id of all the related Hands
        # We use values_list because it is much faster, we don't need to fetch all the Hands at this stage
        # That will be done after pagination in the template
        # Distinct is needed here.
        graphs = graphs.distinct().order_by('hand__scribe__name', 'hand__id')
        #print graphs.query
        graph_ids = graphs.values_list('id', 'hand_id')
        
        # Build a structure that groups all the graph ids by hand id
        # context['hand_ids'] = [[1, 101, 102], [2, 103, 104]]
        # In the above we have two hands: 1 and 2. For hand 1 we have Graph 101 and 102.
        context['hand_ids'] = [[0]]
        last = 0
        for g in graph_ids:
            if g[1] != context['hand_ids'][-1][0]:
                context['hand_ids'].append([g[1]])
            context['hand_ids'][-1].append(g[0])
        del(context['hand_ids'][0])

        t3 = datetime.now()

        context['graphs_count'] = len(graph_ids)
        
        t4 = datetime.now()
        
        #print 'search %s; hands query: %s + graph count: %s' % (t4 - t0, t3 - t2, t4 - t3)
        
    context['drilldownform'] = DrilldownForm()

    try:
        context['view'] = request.COOKIES['view']
    except:
        context['view'] = 'Images'

    t5 = datetime.now()
    
    ret = render_to_response(
        'pages/new-image-view.html',
        context,
        context_instance=RequestContext(request))
    
    t6 = datetime.now()
    
    #print 'hands values_list(id) %s' % (t5 - t4)
    #print 'template %s' % (t6 - t5)
    #print 'total %s' % (t6 - t0)

    return ret


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

def search_suggestions(request):
    from digipal.utils import get_json_response
    from content_type.search_content_type import SearchContentType
    query = request.GET.get('q', '')
    try:
        limit = int(request.GET.get('l'))
    except:
        limit = 8
    suggestions = SearchContentType().get_suggestions(query)
    return get_json_response(suggestions)
