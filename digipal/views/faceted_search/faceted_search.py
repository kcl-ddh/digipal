from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
import json
from digipal.models import Image
from digipal.forms import SearchPageForm

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from digipal.templatetags import hand_filters

import logging
dplog = logging.getLogger('digipal_debugger')

class FacetedModel(object):
    
    def __init__(self, options):
        self.options = options
    
    def get_label(self):
        return self.options['label']
    label = property(get_label)

    def get_key(self):
        return self.options['key']
    key = property(get_key)
    
    def get_fields(self):
        return self.options['fields']
    fields = property(get_fields)
    
    def get_model(self):
        return self.options['model']
    model = property(get_model)

    def get_option(self, option_name):
        return self.options[option_name]
    option = property(get_option)
    
    def get_all_records(self):
        return self.model.objects.all()
        
    def get_document_from_record(self, record):
        ret = {'id': u'%s' % record.id}
        return ret

    def get_facets(self):
        ret = []
        for field in self.fields:
            if field.get('faceted', False):
                ret.append({'label': field['label'], 'key': field['key'], 'options': self.get_facet_options(field)})
        return ret        

    def get_facet_options(self, field):
        ret = []
        for i in range(0, 3):
            ret.append({'key': 'k%s' % i, 'label': '%s # %s' % (field['key'], i)})
        return ret        
        
def get_types():
    image_options = {'key': 'image', 
                'label': 'Image',
                'model': Image,
                'fields': [
                           {'key': 'shelfmark', 'label': 'Shelfmark', 'path': ''},
                           {'key': 'repo_place', 'label': 'Repository Place', 'path': '', 'faceted': True},
                           {'key': 'repo_city', 'label': 'Repository City', 'path': '', 'faceted': True},
                           {'key': 'hi_date', 'label': 'MS Date', 'path': '', 'faceted': True},
                           {'key': 'has_ann', 'label': 'Annotations', 'path': '', 'faceted': True},
                           ],
                }
    
    ret = [FacetedModel(image_options)]
    return ret

def search_whoosh_view(request, content_type='', objectid='', tabid=''):
    context = {'tabid': tabid}
    
    # select the content type 
    cts = get_types()
    ct_key = request.REQUEST.get('result_type', cts[0].key)
    for ct in cts:
        if ct.key == ct_key:
            break

    context['result_type'] = ct
    
    # run the search
    records = ct.get_all_records()
    
    # add the search parameters to the template 
    context['facets'] = [
                       {'label': 'Phrase', 'input_text': 'scribe'},
                        ]
    context['facets'].extend(ct.get_facets())
    
    context['cols'] = [
                       {'label': 'id'},
                       {'label': 'label'},
                       ]
    
    # add the results to the template 
    context['result'] = list(records)
    
    context['advanced_search_form'] = True
    
    return render_to_response('search/faceted/search_whoosh.html', context, context_instance=RequestContext(request))

def rebuild_index():
    for ct in get_types():
        index = create_index_schema(ct)
        if index:
            populate_index(ct, index)

def create_index_schema(ct):
    print '%s' % ct.key
    
    print '\tcreate schema'
    
    # create schema
    from whoosh.fields import TEXT, ID, NGRAM, NUMERIC, KEYWORD
    fields = {'id': ID(stored=True), 'description': TEXT()}
    
    print '\trecreate empty index'

    # recreate an empty index
    import os
    from whoosh.fields import Schema
    from digipal.utils import recreate_whoosh_index
    ret = recreate_whoosh_index(os.path.join(settings.SEARCH_INDEX_PATH, 'faceted'), ct.key, Schema(**fields))
    return ret        
    
def populate_index(ct, index):
    # Add documents to the index
    print '\tretrieve all records'
    writer = index.writer()
    rcs = ct.get_all_records()
    for record in rcs:
        writer.add_document(**ct.get_document_from_record(record))
    
    writer.commit()
    print '\tdone (%s records)' % rcs.count()
    