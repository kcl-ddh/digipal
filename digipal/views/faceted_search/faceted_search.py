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
        ret = {'id': u'%s' % record.id, 'content': unicode(record)}
        for field in self.fields:
            ret[field['key']] = self.get_record_field(record, field)
        return ret

    def get_facets(self):
        ret = []
        for field in self.fields:
            if field.get('faceted', False):
                ret.append({'label': field['label'], 'key': field['key'], 'options': self.get_facet_options(field)})
        return ret        

    def get_facet_options(self, field):
        ret = []
        for k, v in self.whoosh_groups[field['key']].iteritems():
            ret.append({'key': k, 'label': k, 'count': v})
        ret = sorted(ret, key=lambda o: o['key'])
        return ret      
    
    def get_record_field(self, record, afield):
        '''
            returns the value of record.afield 
            where record is a model instance and afield is field name.
            afield and go through related objects.
            afield can also be a field definition (e.g. self.fields[0]).
            afield can also be a function of the object.
        '''
        if not hasattr(afield, 'get'):
            for field in self.fields:
                if field['key'] == afield:
                    afield = field
        
#         for field in self.fields:
#             if field['key'] == afield:
#                 if field['path'].endswith('()'):
#                     ret = getattr(record, field['path'][:-2], None)
#                     if callable(ret):
#                         ret = ret()
#                 if field.get('type', None) == 'url':
#                     ret = u'<a href="%s">view</a>' % ret
        #print record.id, afield['key'], afield['path']
        
        # split the path
        path = afield['path']
        v = record
        for part in path.split('.'):
            if not hasattr(v, part):
                raise Exception(u'Model path error: %s : %s, \'%s\' not found' % (self.key, path, part))
            v = getattr(v, part, None)
            if v is None:
                break
            if callable(v):
                v = v()
        ret = v

        return ret  

    def get_columns(self):
        ret = []
        for field in self.fields:
            if field.get('view', False):
                ret.append({'key': field['key'], 'label': field['label']})
        return ret
    
    def get_whoosh_facets(self):
        from whoosh import sorting
        return [sorting.FieldFacet(field['key'], maptype=sorting.Count) for field in self.fields if field.get('faceted', False)]
    
    def get_requested_records(self, request):
        # run the query with woosh
        # 
        from whoosh.index import open_dir
        import os
        index = open_dir(os.path.join(settings.SEARCH_INDEX_PATH, 'faceted', self.key))

        from whoosh.qparser import QueryParser
        
        search_phrase = request.GET.get('search_terms', '').strip()
        
        # make the query
        if search_phrase:
            qp = QueryParser('content', schema=index.schema)
            q = qp.parse(search_phrase)
        else:
            from whoosh.query.qcore import Every
            q = Every()
        
        with index.searcher() as s:
            # run the query
            facets = self.get_whoosh_facets()

            #ret = s.search_page(q, 1, pagelen=10, groupedby=facets)
            ret = s.search(q, groupedby=facets)
            
            self.whoosh_groups = {}
            for field in self.fields:
                if field.get('faceted', False):
                    self.whoosh_groups[field['key']] = ret.groups(field['key'])
        
            # convert the result into a list of model instances
            ids = [res['id'] for res in ret]
            
            records = self.model.objects.in_bulk(ids)
            ret = [records[int(id)] for id in ids]

            # TODO: make sure the order is preserved
            
            # get facets
                    
        return ret
        
def get_types():
    image_options = {'key': 'image', 
                'label': 'Image',
                'model': Image,
                'fields': [
                           #
                           {'key': 'url', 'label': 'Address', 'path': 'get_absolute_url', 'type': 'url', 'view': True},
                           #{'key': 'scribe', 'label': 'Scribe', 'path': 'hands__scribes__count', 'faceted': True, 'index': True},
                           #{'key': 'annotation', 'label': 'Annotations', 'path': 'annotations__count01', 'faceted': True, 'index': True},
                           #
                           {'key': 'repo_place', 'label': 'Repository Place', 'path': 'item_part.current_item.repository.place.name', 'faceted': True, 'index': True, 'view': True},
                           {'key': 'repo_city', 'label': 'Repository City', 'path': 'item_part.current_item.repository.name', 'faceted': True, 'index': True, 'view': True},
                           {'key': 'shelfmark', 'label': 'Shelfmark', 'path': 'item_part.current_item.shelfmark', 'index': True, 'view': True},
                           {'key': 'locus', 'label': 'Locus', 'path': 'locus', 'index': True, 'view': True},
                           {'key': 'hi_date', 'label': 'MS Date', 'path': 'item_part.historical_item.date', 'type': 'date', 'faceted': True, 'index': True},
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
    records = ct.get_requested_records(request)
    
    # add the search parameters to the template 
    context['facets'] = [
                       {'label': 'Phrase', 'type': 'textbox', 'key': 'search_terms', 'value': request.GET.get('search_terms', '')},
                        ]
    
    context['facets'].extend(ct.get_facets())
    
    context['cols'] = ct.get_columns()
    
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
    fields = {'id': ID(stored=True), 'content': TEXT()}
    for field in ct.fields:
        fields[field['key']] = TEXT()
    
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
    