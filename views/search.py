from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
from digipal.models import *
from digipal.forms import SearchForm, DrilldownForm


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
        term = searchform.cleaned_data['terms']
        searchtype = searchform.cleaned_data['basic_search_type']
        context = {}
        context['type'] = searchtype
        context['terms'] = term
        # re-populate form with previous selections
        context['searchform'] = searchform
        # Distinguish between search types
        if searchtype == 'manuscripts':
            resultpage = "pages/results_manuscripts.html"
            context['results'] = ItemPart.objects.order_by(
                'historical_item__catalogue_number','id').filter(
                    Q(locus__contains=term) | \
                    Q(current_item__shelfmark__icontains=term) | \
                    Q(current_item__repository__name__icontains=term) | \
                    Q(historical_item__catalogue_number__icontains=term) | \
                    Q(historical_item__description__description__icontains=term))
        elif searchtype == 'hands':
            context['drilldownform'] = DrilldownForm({'terms': term})
            resultpage = "pages/results_hands.html"
            context['results'] = Hand.objects.distinct().order_by(
                'scribe__name','id').filter(
                    Q(scribe__name__icontains=term) | \
                    Q(assigned_place__name__icontains=term) | \
                    Q(assigned_date__date__icontains=term) | \
                    Q(item_part__current_item__shelfmark__icontains=term) | \
                    Q(item_part__current_item__repository__name__icontains=term) | \
                    Q(item_part__historical_item__catalogue_number__icontains=term))
        elif searchtype == 'scribes':
            resultpage = "pages/results_scribes.html"
            context['results'] = Scribe.objects.filter(
                name__icontains=term).order_by('name')

        # Distinguish between requests for one record, and full results
        if request.GET.get('record', ''):
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
        return render_to_response(
            'pages/databasepage.html',
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
    context['style']='allograph_list'
    context['term'] = term

    hand_ids = Hand.objects.order_by('scribe__name','id').filter(
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
            idiograph__allograph__id=allograph).order_by('hand')
        context['allograph'] = Allograph.objects.get(id=allograph)
    if feature:
        graphs = graphs.filter(
            graph_components__features__id=feature).order_by('hand')
        context['feature'] = Feature.objects.get(id=feature)
    if character:
        graphs = graphs.filter(
            idiograph__allograph__character__id=character).order_by('hand')
        context['character'] = Character.objects.get(id=character)
    if component:
        graphs = graphs.filter(
            graph_components__component__id=component).order_by('hand')
        context['component'] = Component.objects.get(id=component)

    graphs = graphs.order_by('hand__scribe__name','hand__id')

    context['graphs'] = graphs

    return render_to_response(
        'pages/image-view.html',
        context,
        context_instance=RequestContext(request))


def scribe_details(request):
    """
    Get Idiograph, Graph, and Page data for a Scribe,
    for display in a record view
    """
    scribe = Scribe.objects.get(id=request.GET.get('id'))
    idiograph_components = IdiographComponent.objects.filter(
        idiograph__in=Scribe.objects.get(
            id=scribe.id).idiograph_set.distinct()).order_by('idiograph').all()
    idiographs = list(set([ic.idiograph for ic in idiograph_components]))
    graphs = Graph.objects.filter(
        idiograph__in=idiographs)
    return idiograph_components, graphs
