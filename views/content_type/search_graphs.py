from django import forms
from search_content_type import SearchContentType
from digipal.models import *
from django.forms.widgets import Textarea, TextInput, HiddenInput, Select, SelectMultiple
from django.db.models import Q
from digipal.templatetags.hand_filters import chrono

class SearchGraphs(SearchContentType):

    def __init__(self):
        super(SearchGraphs, self).__init__()
        self.graphs_count = 0

    def get_fields_info(self):
        ''' See SearchContentType.get_fields_info() for a description of the field structure '''
        ret = super(SearchGraphs, self).get_fields_info()
        # TODO: new search field
        return ret
    
    @property
    def form(self):
        return FilterGraphs()
    
    @property
    def key(self):
        return 'graphs'
    
    @property
    def label(self):
        return 'Graphs'

    def is_slow(self):
        return True
    
    @property
    def count(self):
        '''
            Returns the number of records found.
            -1 if the no search was executed.
        '''
        ret = super(SearchGraphs, self).count
        if ret > 0:
            ret = self.graphs_count
        return ret


    def _build_queryset(self, request, term):
        """ View for Hand record drill-down """
        context = {}
        self.graphs_count = 0
        
        scribe = request.GET.get('scribes', '')
        # alternative names are for backward compatibility with old-style graph search page  
        script = request.GET.get('script', '')
        character = request.GET.get('character', '')
        allograph = request.GET.get('allograph', '')
        component = request.GET.get('component', '')
        feature = request.GET.get('feature', '')
        
        from datetime import datetime
        
        t0 = datetime.now()
        t4 = datetime.now()
        
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
                    Q(hand__item_part__historical_items__catalogue_number__icontains=term) | \
                    # JIRA 423
                    Q(hand__item_part__display_label__contains=term) | \
                    Q(hand__item_part__group__display_label__contains=term))
        else:
            graphs = Graph.objects.all()
            
        t1 = datetime.now()
        
        wheres = []
        if scribe:
            graphs = graphs.filter(hand__scribe__name__icontains=scribe)
        if script:
            graphs = graphs.filter(hand__script__name=script)
        if character:
            graphs = graphs.filter(
                idiograph__allograph__character__name=character)
        if allograph:
            graphs = graphs.filter(
                idiograph__allograph__name=allograph)
        if component:
            wheres.append(Q(graph_components__component__name=component) | Q(idiograph__allograph__allograph_components__component__name=component))
        if feature:
            wheres.append(Q(graph_components__features__name=feature))

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
        #graphs = graphs.distinct().order_by('hand__scribe__name', 'hand__id', 'idiograph__allograph__character__ontograph__sort_order')
        chrono('graph filter:')
        graphs = graphs.distinct().order_by('hand__scribe__name', 'hand__id')
        chrono(':graph filter')

        #print graphs.query
        chrono('graph values_list:')
        graph_ids = graphs.values_list('id', 'hand_id')
        chrono(':graph values_list')
        
#         chrono('len:')
#         l = len(graph_ids)
#         print graph_ids.query
#         chrono(':len')
        
        # Build a structure that groups all the graph ids by hand id
        # context['hand_ids'] = [[1, 101, 102], [2, 103, 104]]
        # In the above we have two hands: 1 and 2. For hand 1 we have Graph 101 and 102.
        chrono('hand_ids:')
        context['hand_ids'] = [[0]]
        last = 0
        for g in graph_ids:
            if g[1] != context['hand_ids'][-1][0]:
                context['hand_ids'].append([g[1]])
            context['hand_ids'][-1].append(g[0])
        del(context['hand_ids'][0])
        chrono(':hand_ids')

        t3 = datetime.now()

        self.graphs_count = len(graph_ids)
        
        t4 = datetime.now()
        
        #print 'search %s; hands query: %s + graph count: %s' % (t4 - t0, t3 - t2, t4 - t3)
            
        t5 = datetime.now()
        self._queryset = context['hand_ids']
        
        return self._queryset

    def results_are_recordids(self):
        # build_query_set does not return a list of record ids
        # so the standard processing will be bypassed
        return False

    def get_page_size(self):
        return 12
    
    def _get_available_views(self):
        ret = [
               {'key': 'images', 'label': 'Images', 'title': 'Change to Images view'},
               {'key': 'list', 'label': 'List', 'title': 'Change to list view'},
               ]
        return ret

class FilterGraphs(forms.Form):
    """ Represents the Hand drill-down form on the search results page """
    script = forms.ModelChoiceField(
        queryset=Graph.objects.values_list('hand__script__name', flat= True).order_by('hand__script__name').distinct(),
        widget=Select(attrs={'id':'script', 'class':'chzn-select', 'data-placeholder':"Choose a Script"}),
        label="",
        empty_label = "Script",
        required=False
    )
    character = forms.ModelChoiceField(
        queryset=Graph.objects.values_list('idiograph__allograph__character__name', flat= True).order_by('idiograph__allograph__character__ontograph__sort_order').distinct(),
        widget=Select(attrs={'id':'character', 'class':'chzn-select', 'data-placeholder':"Choose a Character"}),
        label='',
        empty_label = "Character",
        required=False
    )
    allograph = forms.ChoiceField(
        choices = [("", "Allograph")] + [(m.name, m.human_readable()) for m in Allograph.objects.filter(idiograph__graph__isnull=False).distinct()],
        #queryset=Allograph.objects.values_list('name', flat= True).order_by('name').distinct(),
        widget=Select(attrs={'id':'allograph', 'class':'chzn-select', 'data-placeholder':"Choose an Allograph"}),
        label='',
        initial='Allograph',
        required=False
    )
    component = forms.ModelChoiceField(
        queryset=Graph.objects.values_list('graph_components__component__name', flat= True).order_by('graph_components__component__name').distinct(),
        widget=Select(attrs={'id':'component', 'class':'chzn-select', 'data-placeholder':"Choose a Component"}),
        empty_label = "Component",
        label='',
        required=False
    )
    feature = forms.ModelChoiceField(
        queryset=Graph.objects.values_list('graph_components__features__name', flat= True).order_by('graph_components__features__name').distinct(),
        widget=Select(attrs={'id':'feature', 'class':'chzn-select', 'data-placeholder':"Choose a Feature"}),
        empty_label = "Feature",
        label='',
        required=False
    )    
