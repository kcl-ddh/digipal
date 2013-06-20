from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.utils.datastructures import SortedDict
from digipal.models import *
from digipal.forms import DrilldownForm, FilterHands, FilterManuscripts, FilterScribes, SearchPageForm
from itertools import islice, chain
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import logging
dplog = logging.getLogger( 'digipal_debugger')

def search_page(request):
    advanced_search_form = SearchPageForm(request.GET)
    template = 'search/search_page_results.html'
    types = ['hands', 'manuscripts', 'scribes']
    
    context = {}
    context['terms'] = ''
    context['submitted'] = 'terms' in request.GET
    context['advanced_search_expanded'] = 'from_link' in request.GET
    context['can_edit'] = has_edit_permission(request, Hand)
    context['types'] = types
    for type in types:
        add_sub_form(type, request, context) 
    record_type = ''

    if context['submitted'] and advanced_search_form.is_valid():
        # TODO: if we are on the record page, don't do all the searches, only one
        # TODO: review the phrase search to make more flexible 
        
        # Read the inputs
        # - term
        term = advanced_search_form.cleaned_data['terms']
        context['terms'] = term or ' '
        
        # - search type
        search_type = advanced_search_form.cleaned_data['basic_search_type']
        context['type'] = search_type
        
        # - specific record
        if request.GET.get('record', '') or request.GET.get('id', ''):
            record_type = search_type
        
        # Searches by content types
        for type in types:
            get_query(type, request, context)

        # Tab Selection Logic =
        #     we pick the tab the user has selected
        #     if none, we pick the type of the advanced search
        #     if none, we select the first type with non empty result
        #     if none we select the first type
        #

        # TODO = ...
        selected_tab = request.GET.get('tab', '')
        selected_tab = selected_tab or search_type
        if not selected_tab:
            for type in types:
                if type in context and context.type.count():
                    selected_tab = type
                    break
        selected_tab = selected_tab or types[0]
        
        # Populate the context
        context['selected_tab'] = selected_tab

    # Distinguish between requests for one record, and full results
    if record_type:
        context['results'] = context[record_type]

        context['id'] = request.GET.get('id', '')
        context['record'] = request.GET.get('record', '')
        
        context['pages'] = Page.objects.filter(item_part=(request.GET.get('id')))
        context['item_part'] = ItemPart.objects.get(id=context['id'])

        if record_type == 'scribes':
            context['scribe'] = Scribe.objects.get(id=context['id'])
            context['idiograph_components'] = scribe_details(request)[0]
            context['graphs'] = scribe_details(request)[1]
            
        if record_type == 'hands':
            p = Hand.objects.get(id=request.GET.get('id', ''))
            c = p.graph_set.model.objects.get(id=p.id)
            annotation_list = Annotation.objects.filter(graph__hand__id=p.id)
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
                context['data'] = data
            context['result'] = p
        
        template = 'pages/record_' + record_type +'.html'
        
    if not record_type:         
        context['advanced_search_form'] = advanced_search_form
        context['drilldownform'] = DrilldownForm({'terms': context['terms'] or ''})
        add_search_page_json(context)
    
    return render_to_response(template, context, context_instance=RequestContext(request))

def add_search_page_json(context):
    from django.utils import simplejson

    filters = {}
    for type in context['types']:
        filter_name = 'filter_%s' % type
        if filter_name in context:
            html = context[filter_name].as_ul()
        else:
            html = ''
        filters[type] = {
                         'html': html,
                         'label': type.title()
                         }        
    
    ret = {
        'advanced_search_expanded': bool(context['advanced_search_expanded']),
        'filters': filters,
    };
    
    context['search_page_options_json'] = simplejson.dumps(ret)

def add_sub_form(type, request, context):
    name = 'Filter%s' % type.title()
    if name in globals():
        cls = globals()[name]
    if cls:
        context['filter_%s' % type] = cls()
    else:
        raise Exception('function %s() not found' % name)

def get_query(type, request, context):
    # Add a query set to the context.  
    # The query set correspond to one result of the advanced search.
    # Delegate the call to anothe function called get_query_[type]()
    name = 'get_query_%s' % type
    if name in globals():
        function = globals()[name]
    if function:
        function(type, request, context)
    else:
        raise Exception('function %s() not found' % name)
    
def get_query_hands(type, request, context):
    term = context['terms']
    query_hands = Hand.objects.filter(
                Q(descriptions__description__icontains=term) | \
                Q(scribe__name__icontains=term) | \
                Q(assigned_place__name__icontains=term) | \
                Q(assigned_date__date__icontains=term) | \
                Q(item_part__current_item__shelfmark__icontains=term) | \
                Q(item_part__current_item__repository__name__icontains=term) | \
                Q(item_part__historical_item__catalogue_number__icontains=term))
    
    scribes = request.GET.get('scribes', '')
    repository = request.GET.get('repository', '')
    place = request.GET.get('place', '')
    date = request.GET.get('date', '')
    
    context['advanced_search_expanded'] = context['advanced_search_expanded'] or repository or scribes or place or date
    
    if scribes:
        query_hands = query_hands.filter(scribe__name=scribes)
    if repository:
        query_hands = query_hands.filter(item_part__current_item__repository__name=repository)
    if place:
        query_hands = query_hands.filter(assigned_place__name=place)
    if date:
        query_hands = query_hands.filter(assigned_date__date=date)
    
    #context['hands'] = query_hands.distinct().order_by('scribe__name','id')
    context[type] = query_hands.distinct()
    if repository or scribes or place or date:
        context[type] = context[type].order_by('scribe__name','id')
    else:
        context[type] = context[type].order_by('item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'descriptions__description','id')

    context['filter_%s' % type] = FilterHands()

def get_query_manuscripts(type, request, context):
    term = context['terms']
    query_manuscripts = ItemPart.objects.filter(
            Q(locus__contains=term) | \
            Q(current_item__shelfmark__icontains=term) | \
            Q(current_item__repository__name__icontains=term) | \
            Q(historical_item__catalogue_number__icontains=term) | \
            Q(historical_item__description__description__icontains=term))
    
    repository = request.GET.get('repository', '')
    index_manuscript = request.GET.get('index', '')
    date = request.GET.get('date', '')
    
    context['advanced_search_expanded'] = context['advanced_search_expanded'] or repository or index_manuscript or date

    if date:
        query_manuscripts = query_manuscripts.filter(historical_item__date=date)
    if repository:
        query_manuscripts = query_manuscripts.filter(current_item__repository__name=repository)
    if index_manuscript:
        query_manuscripts = query_manuscripts.filter(historical_item__catalogue_number=index_manuscript)
        
    context[type] = query_manuscripts.distinct().order_by('historical_item__catalogue_number', 'id')
    
    context['filter_%s' % type] = FilterManuscripts()

def get_query_scribes(type, request, context):
    term = context['terms']
    query_scribes = Scribe.objects.filter(
                Q(name__icontains=term) | \
                Q(scriptorium__name__icontains=term) | \
                Q(date__icontains=term) | \
                Q(hand__item_part__current_item__shelfmark__icontains=term) | \
                Q(hand__item_part__current_item__repository__name__icontains=term) | \
                Q(hand__item_part__historical_item__catalogue_number__icontains=term))

    name = request.GET.get('name', '')
    scriptorium = request.GET.get('scriptorium', '')
    date = request.GET.get('date', '')
    character = request.GET.get('character', '')
    component = request.GET.get('component', '')
    feature = request.GET.get('feature', '')
    
    context['advanced_search_expanded'] = context['advanced_search_expanded'] or name or scriptorium or date or character or component or feature
    
    # TODO: the filters should be additive rather than replacing the previous one
    if name:
        query_scribes = query_scribes.filter(name=name)
    if scriptorium:
        query_scribes = query_scribes.filter(scriptorium__name=scriptorium)
    if date:
        query_scribes = query_scribes.filter(date=date)
    if character:
        query_scribes = query_scribes.filter(idiographs__allograph__character__name=character)
    if component:
        query_scribes = query_scribes.filter(idiographs__allograph__allographcomponent__component__name=component)
    if feature:
        query_scribes = query_scribes.filter(idiographs__allograph__allographcomponent__component__features__name=feature)

    context[type] = query_scribes.distinct().order_by('name')

    context['filter_%s' % type] = FilterScribes()



def searchDB(request):
    """
    View for search page
    Returns a blank page, or search results
    The first level can return
    - Manuscript data
    - Hand data
    - Scribe data
    """
    searchform = SearchForm(request.GET)
    if searchform.is_valid():
        context = {}

        context['can_edit'] = has_edit_permission(request, Annotation)

        term = searchform.cleaned_data['terms']
        if term:
            context['terms'] = term
        else:
            context['terms'] = ' '
        
        searchtype = searchform.cleaned_data['basic_search_type']
        
        context['type'] = searchtype
        # re-populate form with previous selections
        context['searchform'] = searchform
        # Distinguish between search types
        if searchtype == 'manuscripts':
            resultpage = "pages/results_manuscripts.html"

            # Get forms
            repository = request.GET.get('repository', '')
            index_manuscript = request.GET.get('index', '')
            date = request.GET.get('date', '')

            # Filter manuscripts
            manuscripts = ItemPart.objects.order_by(
                'historical_item__catalogue_number','id').filter(
                    Q(locus__contains=term) | \
                    Q(current_item__shelfmark__icontains=term) | \
                    Q(current_item__repository__name__icontains=term) | \
                    Q(historical_item__catalogue_number__icontains=term) | \
                    Q(historical_item__description__description__icontains=term))
            if date:
                manuscripts = manuscripts.filter(historical_item__date=date)
            if repository:
                manuscripts = manuscripts.filter(current_item__repository__name=repository)
            if index_manuscript:
                manuscripts = manuscripts.filter(historical_item__catalogue_number=index_manuscript)
            context['results'] = manuscripts

        elif searchtype == 'hands':
            resultpage = "pages/results_hands.html"

            # Filters Hands
            hands = Hand.objects.distinct().order_by(
                'item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'descriptions__description','id').filter(
                    Q(descriptions__description__icontains=term) | \
                    Q(scribe__name__icontains=term) | \
                    Q(assigned_place__name__icontains=term) | \
                    Q(assigned_date__date__icontains=term) | \
                    Q(item_part__current_item__shelfmark__icontains=term) | \
                    Q(item_part__current_item__repository__name__icontains=term) | \
                    Q(item_part__historical_item__catalogue_number__icontains=term))
            # Get forms
            scribes = request.GET.get('scribes', '')
            repository = request.GET.get('repository', '')
            place = request.GET.get('place', '')
            date = request.GET.get('date', '')

            if scribes:
                hands = hands.filter(scribe__name=scribes).order_by(
                'scribe__name','id')
            if repository:
                hands = hands.filter(item_part__current_item__repository__name=repository).order_by(
                'scribe__name','id')
            if place:
                hands = hands.filter(assigned_place__name=place).order_by(
                'scribe__name','id')
            if date:
                hands = hands.filter(assigned_date__date=date).order_by(
                'scribe__name','id')

            context['results'] = hands
            
        elif searchtype == 'scribes':

            # Get forms
            # Filter Scribes
            resultpage = "pages/results_scribes.html"
            scribes = Scribe.objects.order_by('name').filter(
                    Q(name__icontains=term) | \
                    Q(scriptorium__name__icontains=term) | \
                    Q(date__icontains=term) | \
                    Q(hand__item_part__current_item__shelfmark__icontains=term) | \
                    Q(hand__item_part__current_item__repository__name__icontains=term) | \
                    Q(hand__item_part__historical_item__catalogue_number__icontains=term))
            name = request.GET.get('name', '')
            scriptorium = request.GET.get('scriptorium', '')
            date = request.GET.get('date', '')
            character = request.GET.get('character', '')
            component = request.GET.get('component', '')
            feature = request.GET.get('feature', '')
            if name:
                scribes = Scribe.objects.filter(
                name=name).order_by('name')
            if scriptorium:
                scribes = Scribe.objects.filter(
                scriptorium__name=scriptorium).order_by('name')
            if date:
                scribes = Scribe.objects.filter(
                date=date).order_by('name')
            if character:
                scribes = Scribe.objects.filter(idiographs__allograph__character__name=character)
            if component:
                scribes = Scribe.objects.filter(idiographs__allograph__allographcomponent__component__name=component)
            if feature:
                scribes = Scribe.objects.filter(idiographs__allograph__allographcomponent__component__features__name=feature)


            context['results'] = scribes

        context['drilldownform'] = DrilldownForm({'terms': term})
        context['filterHands'] = FilterHands()
        context['filterManuscripts'] = FilterManuscripts()
        context['filterScribes'] = FilterScribes()

        
        # Distinguish between requests for one record, and full results
        if request.GET.get('record', ''):
            context['searchform'] = False
            context['id'] = request.GET.get('id', '')
            context['pages'] = Page.objects.filter(item_part=(
                request.GET.get('id')))
            context['item_part'] = ItemPart.objects.get(
                pk=(request.GET.get('id')))
            context['record'] = request.GET.get('record', '')
            if searchtype == 'scribes':
                context['scribe'] = Scribe.objects.get(id=context['id'])
                context['idiograph_components'] = scribe_details(request)[0]
                context['graphs'] = scribe_details(request)[1]
            if searchtype == 'hands':
                p = Hand.objects.get(id=request.GET.get('id', ''))
                c = p.graph_set.model.objects.get(id=p.id)
                #annotation_list = Annotation.objects.filter(page=c.id)
                annotation_list = Annotation.objects.filter(graph__hand__id=p.id)
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
                    context['data'] = data
                context['result'] = p
                
            return render_to_response(
                'pages/record_' + searchtype +'.html',
                context,
                context_instance=RequestContext(request))

        else :
            return render_to_response(
                resultpage,
                context,
                context_instance=RequestContext(request))
    else:
        # Failed validation, or initial request. Just return a blank form
        context = {}
        context['searchform'] = SearchForm()
        context['filterHands'] = FilterHands()
        context['filterManuscripts'] = FilterManuscripts()
        context['filterScribes'] = FilterScribes()
        return render_to_response(
            'search/search.html',
            context,
            context_instance=RequestContext(request))





















def quickSearch(request):
    searchform = QuickSearch(request.GET)
    if searchform.is_valid():
        context = {}
        term = searchform.cleaned_data['terms']
        result_page = 'search/quicksearch_results.html'
        context['terms'] = term
        query_manuscripts = ItemPart.objects.order_by(
                'historical_item__catalogue_number','id').filter(
                    Q(locus__contains=term) | \
                    Q(current_item__shelfmark__icontains=term) | \
                    Q(current_item__repository__name__icontains=term) | \
                    Q(historical_item__catalogue_number__icontains=term) | \
                    Q(historical_item__description__description__icontains=term))
        if query_manuscripts.count() >= 1:
            context['manuscripts'] = query_manuscripts
            count_m = query_manuscripts.count()
        else:
            context['manuscripts'] = "False"
            count_m = 0

        query_hands = Hand.objects.distinct().order_by(
                'item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'descriptions__description','id').filter(
                    Q(descriptions__description__icontains=term) | \
                    Q(scribe__name__icontains=term) | \
                    Q(assigned_place__name__icontains=term) | \
                    Q(assigned_date__date__icontains=term) | \
                    Q(item_part__current_item__shelfmark__icontains=term) | \
                    Q(item_part__current_item__repository__name__icontains=term) | \
                    Q(item_part__historical_item__catalogue_number__icontains=term))

        if query_hands.count() >= 1:
            context['hands'] = query_hands
            count_h = query_hands.count()
        else:
            context['hands'] = "False"
            count_h = 0

        query_scribes = Scribe.objects.order_by('name').filter(
                    Q(name__icontains=term) | \
                    Q(scriptorium__name__icontains=term) | \
                    Q(date__icontains=term) | \
                    Q(hand__item_part__current_item__shelfmark__icontains=term) | \
                    Q(hand__item_part__current_item__repository__name__icontains=term) | \
                    Q(hand__item_part__historical_item__catalogue_number__icontains=term))

        if query_scribes.count() >= 1:
            context['scribes'] = query_scribes
            count_s = query_scribes.count()
        else:
            context['scribes'] = "False"
            count_s = 0

        search_type = False
        if count_h >= 1:
            search_type = 'hands'
        else:
            if count_m >= 1:
                search_type = 'manuscripts'
            elif count_m == 0 and count_s >= 1:
                search_type = 'scribes'
            else:
                search_type = False


        context['search_type'] = search_type
        context['searchform'] = SearchForm()
        context['drilldownform'] = DrilldownForm({'terms': term})
        context['filterHands'] = FilterHands()
        context['filterManuscripts'] = FilterManuscripts()
        context['filterScribes'] = FilterScribes()
        context['can_edit'] = has_edit_permission(request, Hand)
        
        return render_to_response(result_page, context, context_instance=RequestContext(request))

    else:
        context = {}
        term = ''
        context['quicksearchform'] = QuickSearch()
        context['searchform'] = SearchForm()
        context['drilldownform'] = DrilldownForm({'terms': term})
        context['filterHands'] = FilterHands()
        context['filterManuscripts'] = FilterManuscripts()
        context['filterScribes'] = FilterScribes()
        context['can_edit'] = has_edit_permission(request, Hand)
        result_page = 'search/quicksearch_results.html'
        return render_to_response(result_page, context, context_instance=RequestContext(request))

def searchDB(request):
    """
    View for search page
    Returns a blank page, or search results
    The first level can return
    - Manuscript data
    - Hand data
    - Scribe data
    """
    searchform = SearchForm(request.GET)
    if searchform.is_valid():
        context = {}

        context['can_edit'] = has_edit_permission(request, Annotation)

        term = searchform.cleaned_data['terms']
        if term:
            context['terms'] = term
        else:
            context['terms'] = ' '
        searchtype = searchform.cleaned_data['basic_search_type']
        context['type'] = searchtype
        # re-populate form with previous selections
        context['searchform'] = searchform
        # Distinguish between search types
        if searchtype == 'manuscripts':
            resultpage = "pages/results_manuscripts.html"

            # Get forms
            repository = request.GET.get('repository', '')
            index_manuscript = request.GET.get('index', '')
            date = request.GET.get('date', '')

            # Filter manuscripts
            manuscripts = ItemPart.objects.order_by(
                'historical_item__catalogue_number','id').filter(
                    Q(locus__contains=term) | \
                    Q(current_item__shelfmark__icontains=term) | \
                    Q(current_item__repository__name__icontains=term) | \
                    Q(historical_item__catalogue_number__icontains=term) | \
                    Q(historical_item__description__description__icontains=term))
            if date:
                manuscripts = manuscripts.filter(historical_item__date=date)
            if repository:
                manuscripts = manuscripts.filter(current_item__repository__name=repository)
            if index_manuscript:
                manuscripts = manuscripts.filter(historical_item__catalogue_number=index_manuscript)
            context['results'] = manuscripts

        elif searchtype == 'hands':
            resultpage = "pages/results_hands.html"

            # Get forms
            scribes = request.GET.get('scribes', '')
            repository = request.GET.get('repository', '')
            place = request.GET.get('place', '')
            date = request.GET.get('date', '')
            # Filters Hands
            hands = Hand.objects.distinct().order_by(
                'item_part__current_item__repository__name', 'item_part__current_item__shelfmark', 'descriptions__description','id').filter(
                    Q(descriptions__description__icontains=term) | \
                    Q(scribe__name__icontains=term) | \
                    Q(assigned_place__name__icontains=term) | \
                    Q(assigned_date__date__icontains=term) | \
                    Q(item_part__current_item__shelfmark__icontains=term) | \
                    Q(item_part__current_item__repository__name__icontains=term) | \
                    Q(item_part__historical_item__catalogue_number__icontains=term))
            if scribes:
                hands = hands.filter(scribe__name=scribes).order_by(
                'scribe__name','id')
            if repository:
                hands = hands.filter(item_part__current_item__repository__name=repository).order_by(
                'scribe__name','id')
            if place:
                hands = hands.filter(assigned_place__name=place).order_by(
                'scribe__name','id')
            if date:
                hands = hands.filter(assigned_date__date=date).order_by(
                'scribe__name','id')

            context['results'] = hands
            
        elif searchtype == 'scribes':

            # Get forms
            name = request.GET.get('name', '')
            scriptorium = request.GET.get('scriptorium', '')
            date = request.GET.get('date', '')
            character = request.GET.get('character', '')
            component = request.GET.get('component', '')
            feature = request.GET.get('feature', '')
            # Filter Scribes
            resultpage = "pages/results_scribes.html"
            scribes = Scribe.objects.order_by('name').filter(
                    Q(name__icontains=term) | \
                    Q(scriptorium__name__icontains=term) | \
                    Q(date__icontains=term) | \
                    Q(hand__item_part__current_item__shelfmark__icontains=term) | \
                    Q(hand__item_part__current_item__repository__name__icontains=term) | \
                    Q(hand__item_part__historical_item__catalogue_number__icontains=term))
            if name:
                scribes = Scribe.objects.filter(
                name=name).order_by('name')
            if scriptorium:
                scribes = Scribe.objects.filter(
                scriptorium__name=scriptorium).order_by('name')
            if date:
                scribes = Scribe.objects.filter(
                date=date).order_by('name')
            if character:
                scribes = Scribe.objects.filter(idiographs__allograph__character__name=character)
            if component:
                scribes = Scribe.objects.filter(idiographs__allograph__allographcomponent__component__name=component)
            if feature:
                scribes = Scribe.objects.filter(idiographs__allograph__allographcomponent__component__features__name=feature)


            context['results'] = scribes

        context['drilldownform'] = DrilldownForm({'terms': term})
        context['filterHands'] = FilterHands()
        context['filterManuscripts'] = FilterManuscripts()
        context['filterScribes'] = FilterScribes()
       
        # Distinguish between requests for one record, and full results
        if request.GET.get('record', ''):
            context['searchform'] = False
            context['id'] = request.GET.get('id', '')
            context['pages'] = Page.objects.filter(item_part=(
                request.GET.get('id')))
            context['item_part'] = ItemPart.objects.get(
                pk=(request.GET.get('id')))
            context['record'] = request.GET.get('record', '')
            if searchtype == 'scribes':
                context['scribe'] = Scribe.objects.get(id=context['id'])
                context['idiograph_components'] = scribe_details(request)[0]
                context['graphs'] = scribe_details(request)[1]
            if searchtype == 'hands':
                p = Hand.objects.get(id=request.GET.get('id', ''))
                c = p.graph_set.model.objects.get(id=p.id)
                #annotation_list = Annotation.objects.filter(page=c.id)
                annotation_list = Annotation.objects.filter(graph__hand__id=p.id)
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
                    context['data'] = data
                context['result'] = p
                
            return render_to_response(
                'pages/record_' + searchtype +'.html',
                context,
                context_instance=RequestContext(request))

        else :
            return render_to_response(
                resultpage,
                context,
                context_instance=RequestContext(request))
    else:
        # Failed validation, or initial request. Just return a blank form
        context = {}
        context['searchform'] = SearchForm()
        context['filterHands'] = FilterHands()
        context['filterManuscripts'] = FilterManuscripts()
        context['filterScribes'] = FilterScribes()
        return render_to_response(
            'search/search.html',
            context,
            context_instance=RequestContext(request))


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


def scribe_details(request):
    """
    Get Idiograph, Graph, and Page data for a Scribe,
    for display in a record view
    """
    #scribe = Scribe.objects.get(id=request.GET.get('id'))
    #idiograph_components = IdiographComponent.objects.filter(
    #    idiograph__in=Scribe.objects.get(
    #        id=scribe.id).idiograph_set.distinct()).order_by('idiograph').all()
    #idiographs = list(set([ic.idiograph for ic in idiograph_components]))
    #graphs = Graph.objects.filter(
    #    idiograph__in=idiographs)
    #return idiograph_components, graphs


    scribe = Scribe.objects.get(id=request.GET.get('id'))
    idiographs = Idiograph.objects.filter(scribe=scribe.id)
    graphs = Graph.objects.filter(
        idiograph__in=idiographs)
    return idiographs, graphs


