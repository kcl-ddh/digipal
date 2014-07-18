from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
import json
from digipal.models import *
from digipal.forms import SearchPageForm

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from digipal.templatetags import hand_filters

import logging
dplog = logging.getLogger('digipal_debugger')


def search_haystack_view(request):
    context = {}
    
    
    
    return render_to_response('search/faceted/search.html', context, context_instance=RequestContext(request))
    

# ------------------------------------
# ------------------------------------
# ------------------------------------

def get_types():
    ret = []
    ret.append({'key': 'itempart', 
                'name': 'Manuscript',
                })
    ret.append({'key': 'image', 
                'name': 'Image',
                })
    ret.append({'key': 'scribe', 
                'name': 'Scribe',
                })
    return ret

def get_facet_from_types():
    ret = []
    types = get_types()
    for type in types:
        ret.append({'name': type['name'], 'key': type['key']})
    return ret

def search_view(request, content_type='', objectid='', tabid=''):
    context = {'tabid': tabid}
    
    context['facets'] = [
                       {'name': 'Phrase', 'input_text': 'scribe'},
                       {'name': 'Result Type', 'key': 'result_type', 'options': get_facet_from_types()},
                       {'name': 'field0', 'options': [{'name': 'option 0'}, {'name': 'option 1'}, ]},
                        ]
    context['cols'] = [
                       {'name': 'id'},
                       {'name': 'label'},
                       ]
    context['result'] = [
                       {'cols': ['0', 'record 0']},
                       {'cols': ['1', 'record 1']},
                        ]
    
    context['advanced_search_form'] = True
    
    return render_to_response('search/faceted/search_whoosh.html', context, context_instance=RequestContext(request))

