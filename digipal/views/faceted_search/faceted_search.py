from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
import json
from digipal.models import Image
from digipal.forms import SearchPageForm

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from digipal.templatetags import hand_filters, html_escape
from digipal import utils
from django.utils.datastructures import SortedDict

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
    
    def get_views(self):
        return self.get_option('views', [])
    views = property(get_views)
    
    def get_selected_views_template(self):
        for view in self.views:
            if view.get('selected', False):
                ret = view.get('key', 'table')
                break
        
        return 'search/faceted/views/' + ret + '.html' 
    selected_view_template = property(get_selected_views_template)

    def get_all_records(self):
        return self.model.objects.all()
        
    def get_document_from_record(self, record):
        ret = {'id': u'%s' % record.id}
        for field in self.fields:
            if self.is_field_indexable(field):
                ret[field['key']] = self.get_record_field_whoosh(record, field)
        return ret

    def get_facets(self, request):
        ret = []
        
        # a filter for search phrase 
        phrase_facet = {'label': 'Phrase', 'type': 'textbox', 'key': 'search_terms', 'value': request.GET.get('search_terms', ''), 'id': 'search-terms', 'selected_options': []}
        if phrase_facet['value']:
            phrase_facet['selected_options'] = [{'label': phrase_facet['value'], 'key': phrase_facet['value'], 'count': '?', 'selected': True}]
        ret.append(phrase_facet)
        
        # facets based on faceted fields
        for field in self.fields:
            if field.get('count', False) or field.get('filter', False):
                facet = {'label': field['label'], 'key': field['key'], 'options': self.get_facet_options(field, request)}
                facet['selected_options'] = [o for o in facet['options'] if o['selected']]
                ret.append(facet)
        return ret        

    def get_facet_options(self, field, request):
        ret = []
        if not field.get('count', False):
            return ret
        selected_key = request.GET.get(field['key'], '')
        for k, v in self.whoosh_groups[field['key']].iteritems():
            ret.append({'key': k, 'label': k, 'count': v, 'selected': (selected_key == k) and (k)})
        ret = sorted(ret, key=lambda o: o['key'])
        return ret      
    
    def get_record_field_html(self, record, field_key):
        if not hasattr(field_key, 'get'):
            for field in self.fields:
                if field['key'] == field_key:
                    break
        
        ret = self.get_record_field(record, field)
        if field['type'] == 'url':
            ret = '<a href="%s" class="view_button">View</a>' % ret
        if field['type'] == 'image':
            # TODO: max_size as an argument for iip_img_a
            ret = html_escape.iip_img(ret, width=field.get('max_size', 50), lazy=1)
            
        if ret is None:
            ret = ''
            
        return ret
        
    def get_record_field_whoosh(self, record, afield):
        ret = self.get_record_field(record, afield)
        if ret is not None:
            ret = unicode(ret)
        
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
        if path:
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

    def get_summary(self, request):
        ret = u''
        for facet in self.get_facets(request):
            for option in facet['selected_options']:
                href = html_escape.update_query_params('?'+request.META['QUERY_STRING'], {'page': [1], facet['key']: []})
                ret += u'<a href="%s" title="%s = \'%s\'" data-toggle="tooltip"><span class="label label-default">%s</span></a>' % (href, facet['label'], option['label'], option['label']) 

        from django.utils.safestring import mark_safe
        
        if not ret.strip():
            ret = 'All' 
            
        return mark_safe(ret)

    def get_columns(self):
        ret = []
        for field in self.fields:
            if field.get('viewable', False):
                ret.append(field)
        return ret
    
    def get_whoosh_facets(self):
        from whoosh import sorting
        return [sorting.StoredFieldFacet(field['key'], maptype=sorting.Count) for field in self.fields if field.get('count', False)]
    
    @classmethod
    def is_field_indexable(cls, field):
        return field.get('search', False) or field.get('count', False) or field.get('filter', False)    
    
    def get_requested_records(self, request):
        selected = False
        selected_view_key = request.GET.get('view', '')
        if selected_view_key:
            for view in self.views:
                if view['key'] == selected_view_key:
                    view['selected'] = True
                    selected = True
                    break
        if self.views and not selected:
            self.views[0]['selected'] = True
        
        # run the query with Whoosh
        # 
        from whoosh.index import open_dir
        import os
        index = open_dir(os.path.join(settings.SEARCH_INDEX_PATH, 'faceted', self.key))

        #from whoosh.qparser import QueryParser
        
        search_phrase = request.GET.get('search_terms', '').strip()
        
        # make the query
        # get the field=value query from the selected facet options
        field_queries = u''
        for field in self.fields:
            value = request.GET.get(field['key'], '')
            if value:
                field_queries += u' %s:"%s" ' % (field['key'], value)
            
        # add the search phrase    
        if search_phrase or field_queries:
            qp = self.get_whoosh_parser(index)
            q = qp.parse(u'%s %s' % (search_phrase, field_queries))
        else:
            from whoosh.query.qcore import Every
            q = Every()
            
        with index.searcher() as s:
            # run the query
            facets = self.get_whoosh_facets()

            #
            # result returned by search_page doesn't support pagination
            # "'ResultsPage' object has no attribute 'groups'"
            # 
            # Two possible work-arounds:
            # 1. run two Whoosh searches (one for the groups/facets another for the specific page)
            # 2. run full faceted Whoosh search then paginate the ids
            #
            # TODO: check which one is the most efficient            
            # 
            #ret = s.search_page(q, 1, pagelen=10, groupedby=facets)
            ret = s.search(q, groupedby=facets)
            
            self.whoosh_groups = {}
            for field in self.fields:
                if field.get('count', False):
                    self.whoosh_groups[field['key']] = ret.groups(field['key'])
        
            # convert the result into a list of model instances
            from django.core.paginator import Paginator
            
            # paginate
            self.ids = ret
            self.paginator = Paginator(ret, self.get_page_size(request))
            current_page = utils.get_int(request.GET.get('page'), 1)
            if current_page < 1: current_page = 1
            if current_page > self.paginator.num_pages:
                current_page = self.paginator.num_pages 
            self.current_page = self.paginator.page(current_page)
            ids = [hit['id'] for hit in self.current_page.object_list]
            
            #ids = [res['id'] for res in ret]
            
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
    
    def get_total_count(self):
        '''returns the total number of records in the result set'''
        return len(self.ids)
    
    def get_paginator(self):
        return getattr(self, 'paginator', Paginator([], 10))
    
    def get_current_page(self):
        ret = self.current_page
        return ret

    def get_whoosh_parser(self, index):
        from whoosh.qparser import MultifieldParser
        
        # TODO: only active columns
        term_fields = [field['key'] for field in self.fields if field.get('search', False)]
        parser = MultifieldParser(term_fields, index.schema)
        return parser
    
    def get_selected_view(self):
        ret = self.views[0]
        for view in self.views:
            if view.get('selected', False):
                ret = view
                break
        return ret
    
    def get_page_size(self, request):
        ret = utils.get_int(request.GET.get('pgs'), 10)
        sizes = self.get_page_sizes()
        if ret not in sizes:
            ret = sizes[0]
        return ret     
    
    def get_page_sizes(self):
        ret = [10, 20, 50, 100]
        selected_view = self.get_selected_view()
        view_type = selected_view.get('type', 'list')
        if view_type == 'grid':
            ret = [9, 18, 30, 90]
        return ret
        
def get_types():
    image_options = {'key': 'image', 
                'label': 'Image',
                'model': Image,
                'fields': [
                           # label = the label displayed on the screen
                           # label_col = the label in the column in the result table
                           # type = the type of the field

                           # path = a field name (can go through a related object or call a function)
                           
                           # count = True to show the number of hits for each possible value of the field (i.e. show facet options)
                           # filter = True to let the user filter by this field
                           # search = True if the field can be searched on (phrase query)
                           # viewable = True if the field can be displayed in the result set

                           # index = True iff (search or filter or count)
                           
                           # e.g. ann: viewable, full_size: count, repo_city: viewable+count+search
                           # id: special
                           # Most of the times viewable => searchable but not always (e.g. ann.)
                           
                           {'key': 'url', 'label': 'Address', 'label_col': ' ', 'path': 'get_absolute_url', 'type': 'url', 'viewable': True},
                           #{'key': 'scribe', 'label': 'Scribe', 'path': 'hands__scribes__count', 'faceted': True, 'index': True},
                           #{'key': 'annotation', 'label': 'Annotations', 'path': 'annotations__count01', 'faceted': True, 'index': True},
                           #
                           {'key': 'full_size', 'label': 'Image', 'path': 'get_media_right_label', 'type': 'boolean', 'count': True, 'search': True},
                           {'key': 'hi_type', 'label': 'Type', 'path': 'item_part.historical_item.historical_item_type.name', 'type': 'code', 'viewable': True, 'count': True},
                           {'key': 'hi_format', 'label': 'Format', 'path': 'item_part.historical_item.historical_item_format.name', 'type': 'code', 'viewable': True, 'count': True},
                           {'key': 'repo_city', 'label': 'Repository City', 'path': 'item_part.current_item.repository.place.name', 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                           {'key': 'repo_place', 'label': 'Repository Place', 'path': 'item_part.current_item.repository.name', 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                           {'key': 'shelfmark', 'label': 'Shelfmark', 'path': 'item_part.current_item.shelfmark', 'search': True, 'viewable': True, 'type': 'code'},
                           {'key': 'locus', 'label': 'Locus', 'path': 'locus', 'search': True, 'viewable': True, 'type': 'code'},
                           {'key': 'hi_date', 'label': 'MS Date', 'path': 'item_part.historical_item.date', 'type': 'date', 'filter': True, 'viewable': True},
                           {'key': 'annotations', 'label_col': 'Ann.', 'label': 'Annotations', 'path': 'annotation_set.all.count', 'type': 'int', 'viewable': True},
                           {'key': 'thumbnail', 'label_col': 'Thumb.', 'label': 'Thumbnail', 'path': '', 'type': 'image', 'viewable': True, 'max_size': 70},
                           ],
                'select_related': ['item_part__current_item__repository__place'],
                'prefetch_related': ['item_part__historical_items'],
                'views': [
                          {'icon': 'th-list', 'label': 'List', 'key': 'list'},
                          {'icon': 'th', 'label': 'Grid', 'key': 'grid', 'type': 'grid'},
                          ],
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
    context['facets'] = ct.get_facets(request)
    
    context['cols'] = ct.get_columns()
    
    # add the results to the template 
    context['result'] = list(records)
    
    context['current_page'] = ct.get_current_page()

    context['summary'] = ct.get_summary(request)
    
    context['advanced_search_form'] = True
    
    context['page_sizes'] = ct.get_page_sizes()
    context['page_size'] = ct.get_page_size(request)
    context['hit_count'] = ct.get_total_count()
    context['views'] = ct.views
    
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
        if ct.is_field_indexable(field):
            fields[field['key']] = get_whoosh_field_type(field)
        
    print '\t' + ', '.join(key for key in fields.keys())
    
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
    