# Create your views here.
from django.template import RequestContext
from django.shortcuts import render_to_response
# Object models
from digipal.models import Graph


#def dictfetchall(cursor):
#    """Returns all rows from a cursor as a dictionary."""
#    desc = cursor.description

#    return [dict(zip([col[0] for col in desc], row))
#            for row in cursor.fetchall()]

#results = [{'index_text': 'index_test1', 'repository':'rep_test1',
#    'shelfmark': 'shelf_test1', 'folios': 'folio_test1',
#    'description': 'desc_test1'}, {'index_text': 'index_test2',
#    'repository': 'rep_test2', 'shelfmark': 'shelf_test2',
#    'folios': 'folio_test2', 'description': 'desc_test2'}]


def image(request):
    style = request.GET.get('style', '')
    q_id = request.GET.get('id', '')
    context = {}

    #Check for blank search
    if not style:
        style = 'list' 

    context['results'] = Graph.objects.filter(hand=q_id)
    
    context['style'] = style

    return render_to_response('pages/image-view.html', context,
            context_instance=RequestContext(request))
