# Create your views here.
from django.template import RequestContext
from django.shortcuts import render_to_response
# Object models
from digipal.models import Graph
from mezzanine.conf import settings

def cookied_inputs(request):
    context = {'test': 'Yo!'}

    return render_to_response('test/cookied_inputs.html', context,
            context_instance=RequestContext(request))

def jqnotebook_view(request):
    context = {'test': 'Yo!'}

    return render_to_response('test/jqnotebook.html', context,
            context_instance=RequestContext(request))

def iipimage(request):
    context = {'iiphost': settings.IMAGE_SERVER_URL}
    
    from digipal.models import Annotation
    context['annotation'] = Annotation.objects.get(id=11827)

    return render_to_response('test/iipimage.html', context,
            context_instance=RequestContext(request))

def api_view(request):
    context = {'test': 'Yo!'}

    return render_to_response('test/api.html', context,
            context_instance=RequestContext(request))
    
def server_error_view(request):
    raise Exception('Test error')

def autocomplete_view(request):
    context = {}

    return render_to_response('test/autocomplete.html', context,
            context_instance=RequestContext(request))

def map_view(request):
    from digipal.models import ItemPart
    from django.db.models import Q
    context = {}
    
    # get all the item parts with coordinates
    context['q'] = request.GET.get('q', '')
    ip_objs = ItemPart.objects.filter(
                                  Q(display_label__icontains=context['q']) | Q(group__display_label__icontains=context['q']) | Q(owners__institution__place__name__icontains=context['q'])  | Q(owners__institution__place__region__name__icontains=context['q']),
                                  owners__institution__place__id__gt=0
                                ).order_by('display_label').distinct().prefetch_related('owners', 'owners__institution', 'owners__institution__place', 'images')
    
#     ips = ItemPart.objects.filter(
#                                   Q(display_label__icontains=context['q']) | Q(group__display_label__icontains=context['q']) | Q(owners__institution__place__name__icontains=context['q'])  | Q(owners__institution__place__region__name__icontains=context['q']),
#                                   owners__institution__place__id__gt=0
#                                 ).values(
#                                   'display_label',
#                                   'owners__institution__place__name',
#                                   'owners__institution__place__id',
#                                   'owners__institution__place__northings',
#                                   'owners__institution__place__eastings',
#                                   'owners__date',
#                                   'id'
#                                 ).order_by('display_label').distinct()
    ips = ip_objs.values(
                                  'display_label',
                                  'owners__institution__place__name',
                                  'owners__institution__place__id',
                                  'owners__institution__place__northings',
                                  'owners__institution__place__eastings',
                                  'owners__date',
                                  'id'
                                )
    
    context['records'] = ip_objs

    # group by location
    context['marks'] = {}
    for ip in ips:
        key = ip['owners__institution__place__id']
        if key not in context['marks']:
            context['marks'][key] = [ip['owners__institution__place__northings'], ip['owners__institution__place__eastings'], ip['owners__institution__place__name'], []]
        context['marks'][key][3].append([ip['display_label'], ip['owners__date']])
    #context['marks'] =

    import json
    context['marks'] = json.dumps(context['marks'])
    
    return render_to_response('test/map.html', context,
            context_instance=RequestContext(request))

def similar_graph_view(request):
    context = {}
    
    # get the query graph
    gid = id = request.GET.get('gid', 0)
    if gid:
        context['graphq'] = Graph.objects.get(id=gid)
    else:
        context['graphq'] = Graph.objects.filter(idiograph__allograph__character__name='b', graph_components__isnull=False)[2]
        
    # search for similar graphs
    from whoosh.index import open_dir
    from whoosh import sorting, scoring
    import os
    index = open_dir(os.path.join(settings.SEARCH_INDEX_PATH, 'graphs'))
    #searcher = index.searcher(weighting=scoring.Frequency())
    searcher = index.searcher()
    
    from whoosh.qparser import QueryParser
    from whoosh.qparser import syntax
    parser = QueryParser('description', schema=index.schema, group=syntax.OrGroup)
    query = parser.parse(context['graphq'].get_serialised_description())
    #query = parser.parse('(description:4_21 OR description:"4_69" OR description:"8_87")')
    print repr(query)
    #sortedby = [sorting.ScoreFacet()]
    print query
    #results = searcher.search(query, limit=20, sortedby=sortedby)
    results = searcher.search(query, limit=50)
    
    # fetch the results
    #print results[0]
    #gids = [r['gid'] for r in results]
    #print gids
    
    gids = [r['gid'] for r in results]
    print gids
    
    context['graphs'] = []
    graphs = {}
    for g in Graph.objects.filter(id__in=gids).prefetch_related('hand', 'annotation', 'annotation__image', 'annotation__image__item_part'):
        graphs[g.id] = g
    for r in results:
        g = graphs[int(r['gid'])]
        g.hit = r
        context['graphs'].append(g)
    
    # get the graphs from teh database
#     context['graphs'] = []
#     i = 0
#     for id, g in Graph.objects.in_bulk(gids).iteritems():
#         i += 1
#         print id, g
#         #g.hit = results[i]
#         context['graphs'].append(g)

    ret = render_to_response('test/similar_graph.html', context,
            context_instance=RequestContext(request))

    searcher.close()
    
    return ret

