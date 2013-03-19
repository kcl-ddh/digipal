from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.utils.datastructures import SortedDict
from digipal.models import *
from digipal.forms import SearchForm, DrilldownForm, FilterHands, FilterManuscripts, FilterScribes, QuickSearch
from itertools import islice, chain

class QuerySetChain(object):
    """
    Chains multiple subquerysets (possibly of different models) and behaves as
    one queryset.  Supports minimal methods needed for use with
    django.core.paginator.
    """

    def __init__(self, *subquerysets):
        self.querysets = subquerysets

    def count(self):
        """
        Performs a .count() for all subquerysets and returns the number of
        records as an integer.
        """
        return sum(qs.count() for qs in self.querysets)

    def _clone(self):
        "Returns a clone of this queryset chain"
        return self.__class__(*self.querysets)

    def _all(self):
        "Iterates records in all subquerysets"
        return chain(*self.querysets)

    def __getitem__(self, ndx):
        """
        Retrieves an item or slice from the chained set of results from all
        subquerysets.
        """
        if type(ndx) is slice:
            return list(islice(self._all(), ndx.start, ndx.stop, ndx.step or 1))
        else:
            return islice(self._all(), ndx, ndx+1).next()

def quickSearch(request, search_type):
    searchform = QuickSearch(request.GET)
    if searchform.is_valid():
        context = {}
        term = searchform.cleaned_data['terms']
        result_page = 'search/quicksearch_results.html'
        context['terms'] = term
        context['search_type'] = search_type
        if search_type == 'manuscripts':
            query = ItemPart.objects.order_by(
                'historical_item__catalogue_number','id').filter(
                    Q(locus__contains=term) | \
                    Q(current_item__shelfmark__icontains=term) | \
                    Q(current_item__repository__name__icontains=term) | \
                    Q(historical_item__catalogue_number__icontains=term) | \
                    Q(historical_item__description__description__icontains=term))
        elif search_type == 'hands':
            query = Hand.objects.distinct().order_by(
                'scribe__name','id').filter(
                    Q(scribe__name__icontains=term) | \
                    Q(assigned_place__name__icontains=term) | \
                    Q(assigned_date__date__icontains=term) | \
                    Q(item_part__current_item__shelfmark__icontains=term) | \
                    Q(item_part__current_item__repository__name__icontains=term) | \
                    Q(item_part__historical_item__catalogue_number__icontains=term))
        else:
            query = Scribe.objects.filter(
                name__icontains=term).order_by('name')
        context['results'] = query
        context['searchform'] = SearchForm()
        context['drilldownform'] = DrilldownForm({'terms': term})
        context['filterHands'] = FilterHands()
        context['filterManuscripts'] = FilterManuscripts()
        context['filterScribes'] = FilterScribes()
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

            # Filter scribes
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
                'scribe__name','id').filter(
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
            scribes = Scribe.objects.filter(
                name__icontains=term).order_by('name')
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
                annotation_list = Annotation.objects.filter(page=c.id)
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
            idiograph__allograph__name=allograph).order_by('hand')
        context['allograph'] = Allograph.objects.get(name=allograph)
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

    return render_to_response(
        'pages/image-view.html',
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


