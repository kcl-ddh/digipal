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

    def get_option(self, option_name, default=None):
        return self.options.get(option_name, default)
    
    def get_all_records(self):
        return self.model.objects.all()
        
    def get_document_from_record(self, record):
        ret = {'id': u'%s' % record.id}
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
    
    def get_record_field_html(self, record, field_key):
        if not hasattr(field_key, 'get'):
            for field in self.fields:
                if field['key'] == field_key:
                    break
        
        ret = self.get_record_field(record, field)
        if field['type'] == 'url':
            ret = '<a href="%s">View</a>' % ret
        return ret
        
    def get_record_field(self, record, afield):
        '''
            returns the value of record.afield 
            where record is a model instance and afield is field name.
            afield and go through related objects.
            afield can also be a field definition (e.g. self.fields[0]).
            afield can also be a function of the object.
        '''
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
            if field.get('viewable', False):
                ret.append(field)
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

        #from whoosh.qparser import QueryParser
        
        search_phrase = request.GET.get('search_terms', '').strip()
        
        # make the query
        if search_phrase:
            #qp = QueryParser('content', schema=index.schema)
            qp = self.get_whoosh_parser(index)
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
            
            records = self.model.objects.all()
            if self.get_option('select_related'):
                records = records.select_related(*self.get_option('select_related'))
            if self.get_option('prefetch_related'):
                records = records.prefetch_related(*self.get_option('prefetch_related'))
            records = records.in_bulk(ids)
            
            if len(records) != len(ids):
                raise Exception("DB query didn't retrieve all Whoosh results.")
            
            # 'item_part__historical_items'
            ret = [records[int(id)] for id in ids]

            # TODO: make sure the order is preserved
            
            # get facets
                    
        return ret
    
    def get_whoosh_parser(self, index):
        from whoosh.qparser import MultifieldParser
        
        term_fields = []
        for field in self.fields:
            if field.get('viewable', False):
                term_fields.append(field['key'])
        parser = MultifieldParser(term_fields, index.schema)
        #parser = MultifieldParser(term_fields, index.schema)
        return parser
        
def get_types():
    image_options = {'key': 'image', 
                'label': 'Image',
                'model': Image,
                'fields': [
                           # label = the label displayed on the screen
                           # label_col = the label in the column in the result table
                           # viewable = True if the field can be displayed in the result set
                           # index = True to index the field
                           # type = the type of the field
                           # counts = True to show the number of hits for each possible value of the field (i.e. show facet options)
                           # filter = True to let the user filter by this field
                           # path = a field name (can go through a related object or call a function)
                           
                           {'key': 'url', 'label': 'Address', 'label_col': ' ', 'path': 'get_absolute_url', 'type': 'url', 'viewable': True},
                           #{'key': 'scribe', 'label': 'Scribe', 'path': 'hands__scribes__count', 'faceted': True, 'index': True},
                           #{'key': 'annotation', 'label': 'Annotations', 'path': 'annotations__count01', 'faceted': True, 'index': True},
                           #
                           {'key': 'repo_city', 'label': 'Repository City', 'path': 'item_part.current_item.repository.place.name', 'faceted': True, 'index': True, 'viewable': True, 'type': 'title'},
                           {'key': 'repo_place', 'label': 'Repository Place', 'path': 'item_part.current_item.repository.name', 'faceted': True, 'index': True, 'viewable': True, 'type': 'title'},
                           {'key': 'shelfmark', 'label': 'Shelfmark', 'path': 'item_part.current_item.shelfmark', 'index': True, 'viewable': True, 'type': 'code'},
                           {'key': 'locus', 'label': 'Locus', 'path': 'locus', 'index': True, 'viewable': True, 'type': 'code'},
                           {'key': 'hi_date', 'label': 'MS Date', 'path': 'item_part.historical_item.date', 'type': 'date', 'faceted': True, 'index': True, 'type': 'code'},
                           ],
                'select_related': ['item_part__current_item__repository__place'],
                'prefetch_related': ['item_part__historical_items'],
                }
    
    ret = [FacetedModel(image_options)]
    return ret

def search_whoosh_view(request, content_type='', objectid='', tabid=''):
    hand_filters.chrono('VIEW:')
    
    hand_filters.chrono('SEARCH:')

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
                       {'label': 'Phrase', 'type': 'textbox', 'key': 'search_terms', 'value': request.GET.get('search_terms', ''), 'id': 'search-terms'},
                        ]
    
    context['facets'].extend(ct.get_facets())
    
    context['cols'] = ct.get_columns()
    
    # add the results to the template 
    context['result'] = list(records)
    
    context['advanced_search_form'] = True
    
    hand_filters.chrono(':SEARCH')

    hand_filters.chrono('TEMPLATE:')
    
    ret = render_to_response('search/faceted/search_whoosh.html', context, context_instance=RequestContext(request))

    hand_filters.chrono(':TEMPLATE')

    hand_filters.chrono(':VIEW')
    
    return ret

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
    fields = {'id': ID(stored=True)}
    for field in ct.fields:
        fields[field['key']] = get_whoosh_field_type(field)
    
    print '\trecreate empty index'

    # recreate an empty index
    import os
    from whoosh.fields import Schema
    from digipal.utils import recreate_whoosh_index
    ret = recreate_whoosh_index(os.path.join(settings.SEARCH_INDEX_PATH, 'faceted'), ct.key, Schema(**fields))
    return ret        

def get_whoosh_field_type(field):
    '''
    Defines Whoosh field types used to define the schemas.
    See get_field_infos().
    '''
    
    # see http://pythonhosted.org/Whoosh/api/analysis.html#analyzers
    # see JIRA 165
    
    from whoosh.fields import TEXT, ID
    # TODO: shall we use stop words? e.g. 'A and B' won't work? 
    from whoosh.analysis import SimpleAnalyzer, StandardAnalyzer, StemmingAnalyzer, CharsetFilter
    from whoosh.support.charset import accent_map
    # ID: as is; SimpleAnalyzer: break into lowercase terms, ignores punctuations; StandardAnalyzer: + stop words + minsize=2; StemmingAnalyzer: + stemming
    # minsize=1 because we want to search for 'Scribe 2'
    
    # A paragraph or more.
    field_type = field['type']
    if field_type == 'id':
        # An ID (e.g. 708-AB)
        ret = ID(stored=True)
    elif field_type == 'code':
        # A code (e.g. K. 402, Royal 7.C.xii)
        # See JIRA 358
        ret = TEXT(analyzer=SimpleAnalyzer(ur'[.\s()\u2013\u2014-]', True), stored=True)
    elif field_type == 'title':
        # A title (e.g. British Library)
        ret = TEXT(analyzer=StemmingAnalyzer(minsize=1, stoplist=None) | CharsetFilter(accent_map), stored=True)
    elif field_type == 'short_text':
        # A few words.
        ret = TEXT(analyzer=StemmingAnalyzer(minsize=1) | CharsetFilter(accent_map), stored=True)
    else:
        ret = TEXT(analyzer=StemmingAnalyzer(minsize=1) | CharsetFilter(accent_map), stored=True)
        
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
    