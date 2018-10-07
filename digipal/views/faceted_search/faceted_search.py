from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
import json
from digipal.forms import SearchPageForm
from django.utils.safestring import mark_safe

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from mezzanine.conf import settings
from digipal.templatetags import hand_filters, html_escape
from digipal import utils
from digipal.templatetags.hand_filters import chrono
import re


class FacetedModel(object):

    def __init__(self, options):
        self.options = options
        self.faceted_model_group = None
        from digipal.views.faceted_search.settings import FacettedType
        self.settings = FacettedType(options)
        # a instance cache to avoid calculating things many times
        self.icache = {}

    def set_faceted_model_group(self, faceted_model_group=None):
        self.faceted_model_group = faceted_model_group

    def get_label(self):
        return self.options['label']
    label = property(get_label)

    def get_label_plural(self):
        return self.get_option('label_plural', html_escape.plural(self.label))
    label_plural = property(get_label_plural)

    def get_key(self):
        return self.options['key']
    key = property(get_key)

    def get_fields(self):
        return self.options['fields']
    fields = property(get_fields)

    def get_model(self):
        return self.settings.getModelClass()
    model = property(get_model)

    def get_option(self, option_name, default=None):
        return self.options.get(option_name, default)

    def get_views(self):
        ret = self.settings.getViewsEnabled()

        found = False
        if hasattr(self, 'request'):
            view_key = self.request.GET.get('view')
            for view in ret:
                selected = view['key'] == view_key
                found = found or selected
                if selected:
                    ret[0]['selected'] = False
                view['selected'] = selected
        if not found:
            #raise Exception('Yo!')
            ret[0]['selected'] = True

        return ret
    views = property(get_views)

    def get_record_label_html(self, record, request):
        ret = u''.join([u'<tr><td>%s</td><td>%s</td></tr>' % (field['label'], self.get_record_field(record, field))
                        for field in self.get_columns(request) if field['type'] in ['id', 'code', 'title', 'date']])
        #ret = u''.join([u'<tr><td>%s</td><td>%s</td></tr>' % (field['label'], self.get_record_field(record, field)) for field in self.get_fields() if field['type'] in ['id', 'code', 'title', 'date']])

        return ret

    def get_selected_views_template(self):
        for view in self.views:
            if view.get('selected', False):
                ret = view.get('template', view.get('key', 'table'))
                break

        mobile = utils.is_display_narrow(self.request)
        if ret == 'list' and mobile:
            ret += '_narrow'

        ret = 'search/faceted/views/' + ret + '.html'
        return ret
    selected_view_template = property(get_selected_views_template)

    def get_all_records(self, prefetch=False):
        ret = self.model.objects.filter(
            **self.get_option('django_filter', {})).order_by('id')
        if prefetch:
            if self.get_option('select_related'):
                ret = ret.select_related(*self.get_option('select_related'))
            if self.get_option('prefetch_related'):
                ret = ret.prefetch_related(
                    *self.get_option('prefetch_related'))

        return ret

    @classmethod
    def _get_sortable_whoosh_field(cls, field):
        '''Returns the name of the whoosh field that we can use to sort the given field
            Returns None if field is not sortable
        '''
        ret = None

        if field and cls.is_field_indexable(field) and field.get('viewable', False):
            ret = field['key']
            if field['type'] in ['id', 'code', 'title', 'date']:
                ret += '_sortable'

        return ret

    def get_result_heading(self):
        return self.options.get('result_heading', None)

    def is_toolbar_hidden(self):
        return self.options.get('toolbar_hidden', False)

    def get_sort_info(self, request):
        key = request.GET.get('sort', '')
        reverse = key.startswith('-')
        if reverse:
            key = key[1:]
        if key == '0':
            key = ''
        return key, reverse

    def get_model_from_field(self, field):
        '''
            Return the model and property name at the end of the given path/field
            self.get_model_from_field(<FacetedModel on ItemPart>, 'current_item__repo__place__name')
            =>
            <Place>, 'name'
        '''
        ret = self.model
        parts = field['path'].split('.')
        while parts:
            part = parts.pop(0)
            part_obj = getattr(ret, part, None)
            if hasattr(part_obj, 'get_queryset'):
                ret = part_obj.get_queryset().model
            else:
                parts.insert(0, part)
                break
        path = '.'.join(parts)

        return ret, path

    def clear_value_rankings(self):
        '''Clear the value rankings cache to liberate memory
            Can save up to 100MB
        '''
        self.value_rankings = {}
        utils.gc_collect()

    def prepare_value_rankings(self, callback=None):
        ''' populate self.value_rankings dict
            It generates a ranking number for each value in each sortable field
            This will be stored in the index as a separate field to allow sorting by any column

            callback = a function that takes a value between 0.0 and 1.0,
                representing the progress
        '''
        self.clear_value_rankings()

        #records = self.get_all_records(False)
        #records = self.get_all_records(True).order_by('id')
        # print '\t\t%d records' % records.count()

        indexable_fields = []
        for field in self.fields:
            if self.is_field_indexable(field):
                indexable_fields.append(field)

        i = 0
        for field in indexable_fields:
            i += 1
            whoosh_sortable_field = self._get_sortable_whoosh_field(field)
            if whoosh_sortable_field and whoosh_sortable_field != field['key']:

                print '\t\t' + field['key']

                # get all the values for that field in the table
                self.value_rankings[whoosh_sortable_field], sorted_values = self.get_field_value_ranking(
                    field)

                if callback:
                    callback(1.0 * i / len(indexable_fields))

    def get_field_value_ranking(self, field):
        # get all the values for that field in the table
        value_rankings = {}
        # We call iterator() here to avoid fetching all the records at ones
        # which causes this query to crash on the Linux VM due to excessive
        # memory consumption.
        # for record in records.iterator():

        # get unique values

        hand_filters.chrono('%s:' % field['key'])

        # print 'h1'

        model, path = self.get_model_from_field(field)
        sort_function = field.get('sort_fct', None)
        value_rankings[None] = u''
        value_rankings['None'] = u''
        value_rankings[u''] = u''

        # add the values from the mapping
        for k, v in field.get('mapping', {}).iteritems():
            value_rankings[v] = v

        # print model, path
        i = 0
        # print repr(model), utils.get_mem()
        for record in model.objects.all().order_by('id').iterator():
            if i == 0:
                pass
                # print path
                # print utils.get_mem()
            i += 1
            value = ''
            value = self.get_record_path(record, path)
            value = self.get_sortable_hash_value(value, field)

            v = value
            if sort_function:
                v = sort_function(record)
            v = v or u''

            value_rankings[value] = v

        # convert dates to numbers
        if field['type'] == 'date':
            for k, v in value_rankings.iteritems():
                v = utils.get_midpoint_from_date_range(v)
                value_rankings[k] = v or 10000
            sorted_values = sorted(value_rankings.values())
            # #print sorted_values
            # exit()
        else:
            # sort by natural order
            sorted_values = utils.sorted_natural(value_rankings.values(), True)

        # now assign the ranking to each value
        for k, v in value_rankings.iteritems():
            value_rankings[k] = sorted_values.index(v)

        hand_filters.chrono(':%s' % field['key'])

        # print '', utils.get_mem()
        return value_rankings, sorted_values
        # return 0

    def get_sortable_hash_value(self, value, field):
        if field.get('multivalued', False) and hasattr(value, 'split'):
            value = value.split('|')
        return utils.get_sortable_hash_value(value)

    def get_document_from_record(self, record):
        '''
            Returns a Whoosh document from a Django model instance.
            The list of instance fields to extract come from the content type
            definition (see settings.py).
            Multivalued fields are turned into a list of unicode values.
        '''
        ret = {'id': u'%s' % record.id}
        for field in self.fields:
            if self.is_field_indexable(field):
                fkey = field['key']
                value = self.get_record_field_whoosh(record, field)

                # generate associated sort field
                whoosh_sortable_field = self._get_sortable_whoosh_field(field)
                if whoosh_sortable_field and whoosh_sortable_field != fkey:
                    ret[whoosh_sortable_field] = self.value_rankings[whoosh_sortable_field][self.get_sortable_hash_value(
                        value, field)]

                # value conversions
                if field['type'] == 'boolean':
                    value = int(bool(value) and ('%s' % value).lower()
                                not in ['0', 'false', 'none'])

                if field['type'] == 'xml':
                    value = self.get_plain_text_from_xml(value)

                if field['type'] == 'date':
                    from digipal.utils import get_range_from_date, is_max_date_range
                    rng = get_range_from_date(value)
                    ret[fkey + '_min'] = rng[0]
                    ret[fkey + '_max'] = rng[1]
                    ret[fkey + '_diff'] = abs(rng[1] - rng[0])
                    if is_max_date_range(rng):
                        # we don't want the empty dates and invalid dates to be
                        # found
                        ret[fkey + '_max'] = ret[fkey + '_min']

                ret[fkey] = value

        return ret

    def get_plain_text_from_xml(self, value):
        '''Returns a plain text version of the XML <value>.
            For indexing purpose.
            Strip tags, remove some abbreviations, ...
        '''
        from digipal import utils as dputils
        return dputils.get_plain_text_from_xmltext(value)

    def get_field_by_key(self, key):
        # todo: think about caching this
        for field in self.fields:
            if field['key'] == key:
                return field
        return None

    def get_filter_field_keys(self):
        ''' Returns a list of fields keys in the order they should appear in the filter panel '''
        ret = self.get_option('filter_order', None)
        if ret is None:
            ret = [field['key']
                   for field in self.fields if self.settings.isFieldAFacet(field)]
        return ret
    filter_field_keys = property(get_filter_field_keys)

    def get_facets(self, request):
        ret = self.icache.get('get_facets', [])
        if ret:
            return ret

        # a filter for search phrase
        phrase_facet = {'label': 'Keywords', 'type': 'textbox', 'key': 'terms', 'value': request.GET.get(
            'terms', ''), 'id': 'search-terms', 'removable_options': []}
        if getattr(settings, 'AUTOCOMPLETE_PUBLIC_USER', True):
            phrase_facet['classes'] = ' autocomplete '

        if phrase_facet['value']:
            phrase_facet['removable_options'] = [
                {'label': phrase_facet['value'], 'key': phrase_facet['value'], 'count': '?', 'selected': True}]
        ret.append(phrase_facet)

        # a filter for the content types
        if self.faceted_model_group and len(self.faceted_model_group) > 1:
            # ct_facet = {'label': 'Type', 'key': 'result_type', 'value': request.GET.get('result_type', ''), 'removable_options': [], 'options': []}
            ct_facet = {'label': 'Result Type', 'key': 'result_type',
                        'value': self.key, 'removable_options': [], 'options': [], 'expanded': 2}
            for faceted_model in self.faceted_model_group:
                selected = faceted_model.key == ct_facet['value']
                option = {'label': faceted_model.label_plural,
                          'key': faceted_model.key, 'count': '', 'selected': selected}
                option['href'] = html_escape.update_query_params(
                    '?' + request.META['QUERY_STRING'], {'page': [1], ct_facet['key']: [option['key']]})
                ct_facet['options'].append(option)
            ret.append(ct_facet)

        # facets based on faceted fields
        hand_filters.chrono('fielfds:')

        from copy import deepcopy
        for key in self.filter_field_keys:
            hand_filters.chrono('Field %s' % key)
            field = self.get_field_by_key(key)
            if field is None:
                raise Exception('Content type "%s" has no field named "%s". Check filters.' % (
                    self.get_key(), key))
            facet = deepcopy(field)
            facet['sorted_by'] = request.GET.get('_st_' + field['key'], 'c')
            facet['options'] = self.get_facet_options(
                field, request, facet['sorted_by'])

            facet['value'] = request.GET.get(field['key'], '')
            facet['value_diff'] = request.GET.get(field['key'] + '_diff', '')
            facet['value_diff_op'] = request.GET.get(
                field['key'] + '_diff_op', '')

            if field['type'] == 'date':
                if facet['value']:
                    from digipal.utils import get_range_from_date
                    facet['values'] = get_range_from_date(facet['value'])
                facet['ops'] = [
                    {'key': 'lte', 'label': 'at most'},
                    {'key': 'gte', 'label': 'at least'},
                ]

            facet['removable_options'] = []
            if facet['options']:
                facet['removable_options'] = [
                    o for o in facet['options'] if o['selected']]
            else:
                if facet['value']:
                    facet['removable_options'] = [
                        {'label': facet['value'], 'key': facet['value'], 'count': '?', 'selected': True}]
                if facet['value_diff']:
                    facet['removable_options'] = [
                        {'label': facet['value_diff'], 'key': facet['value_diff'], 'count': '?', 'selected': True}]
            ret.append(facet)

        for facet in ret:
            # Set facet expansion from the query string
            facet['expanded'] = utils.get_int_from_request_var(
                request, '_xp_' + facet['key'], facet.get('expanded', 0))

        hand_filters.chrono(':fielfds')

        self.icache['get_facets'] = ret

        return ret

    def get_facet_options(self, field, request, sorted_by='c'):
        from urllib import quote_plus
        ret = []
        if not self.settings.areFieldOptionsShown(field):
            return ret
        selected_key = unicode(request.GET.get(field['key'], ''))

        keyword = 'REPLACEME'
        # this fct is expensive, we moved it out of the loop below
        href = html_escape.update_query_params(
            '?' + request.META['QUERY_STRING'], {'page': [1], field['key']: [keyword]})
        labels = field.get('labels', {0: 'No', 1: 'Yes'})
        is_bool = field['type'] == 'boolean'

        # http://localhost:8080/digipal/search/facets/?entry_type=TO&page=1&pgs=10&wr=0&result_type=entries&view=list
        is_count_needed = field.get('count', False)
        if hasattr(self, 'whoosh_groups'):
            for k, v in self.whoosh_groups[field['key']].iteritems():
                label = k
                if is_bool:
                    label = labels[int(utils.get_bool_from_string(k))]
                option = {'key': k, 'label': label, 'selected': (
                    selected_key == unicode(k)) and (k is not None)}
                if is_count_needed:
                    option['count'] = v
                option['href'] = mark_safe(href.replace(keyword, quote_plus(
                    '' if option['selected'] else (u'%s' % option['key']).encode('utf=8'))))
                ret.append(option)

        # sort the options (by count then key or the opposite)
        # TODO: optimise by doing this first, then limiting (if facet is
        # collapsed), then running the loop above
        if is_count_needed:
            def sort_fct(o): return [-o['count'], o['key']]
            if sorted_by == 'o':
                def sort_fct(o): return [o['key'], -o['count']]
        else:
            def sort_fct(o): return o['key']
        ret = sorted(ret, key=sort_fct)

        return ret

    def get_record_field_html(self, record, field_key):
        if not hasattr(field_key, 'get'):
            for field in self.fields:
                if field['key'] == field_key:
                    break

        ret = self.get_record_field(record, field, True)
        if isinstance(ret, list):
            ret = '; '.join(sorted(ret))

        if field['type'] == 'url':
            ret = '<a href="%s" class="btn btn-default btn-sm" title="" data-toggle="tooltip">View</a>' % ret

        if field['type'] == 'image':
            if 'Annotation' in str(type(ret)):
                if 'Graph' in str(type(record)):
                    ret = html_escape.annotation_img(ret, lazy=1, a_title=record.get_short_label(
                    ), a_data_placement="bottom", a_data_toggle="tooltip", a_data_container="body", wrap=record, link=record)
                else:
                    ret = html_escape.annotation_img(
                        ret, lazy=1, fixlen=800, wrap=record, link=record)
            else:
                # GN: we used to link to the page for the record shown in the result
                # now we link to the image web page.
                # This works well for both image & text result types.

                link = ret
                if field.get('link_to_record', False):
                    link = record
                ret = html_escape.iip_img(ret, width=field.get(
                    'max_size', 50), lazy=1, wrap=link, link=link)
        if ret is None:
            ret = ''

        return ret

    def get_record_field_whoosh(self, record, afield):
        ret = self.get_record_field(record, afield)

        # convert to unicode (or list of unicode)
        # if ret is not None:
        if isinstance(ret, list):
            #ret = [unicode(v) for v in ret]
            ret = u'|'.join([unicode(v) for v in ret])
        else:
            ret = unicode(ret)

        return ret

    def get_record_field(self, record, afield, use_path_result=False):
        '''
            returns the value of record.afield
            where record is a model instance and afield is field name.
            afield and go through related objects.
            afield can also be a field definition (e.g. self.fields[0]).
            afield can also be a function of the object.
            table_value = True we show the field as is should appear in the result table
        '''
        # split the path
        path = afield['path']
        if use_path_result and 'path_result' in afield:
            path = afield['path_result']

        ret = self.get_record_path(record, path, afield)

        # value mapping
        # TODO: make it work with multi-valued fields (ret is an array)
        mapping = afield.get('mapping')
        if_list = isinstance(ret, list)
        if if_list and len(ret) == 0:
            ret = u''
        if mapping and not isinstance(ret, list):
            ret = mapping.get(ret, ret)

        return ret

    def get_record_path(self, record, path, afield=None):
        '''
            Return one or more values related to a record
            by following the given path through the data model.
            See get_record_field
            e.g. get_record_path(ItemPart.objects.get(id=598), 'images.all.id')
            => [3200, 3201]

            afield is an optional field defition (see settings.py)
        '''
        from django.db.models.manager import BaseManager

        v = record
        if path not in (None, ''):
            from django.core.exceptions import ObjectDoesNotExist
            from django.db.models.query import QuerySet
            parts = path.split('.')
            path_done = []
            while parts:
                part = parts.pop(0)
                try:
                    v = getattr(v, part)
                except ObjectDoesNotExist, e:
                    v = None
                except Exception, e:
                    raise Exception(u'Model path not found. Record = [%s:%s], path = %s, part = %s, value = %s' % (
                        type(record), repr(record), path, part, repr(v)))

                # Django 1.7, RelatedManager.__call__() is defined
                # but we don't want to call it.
                if callable(v) and not isinstance(v, BaseManager):
                    if len(parts) == 0 and afield and afield.get('request', False):
                        # the method needs a request object
                        v = v(self.request)
                    else:
                        try:
                            v = v()
                        except Exception, e:
                            print u'Model path not found. Record = [%s:%s], path = %s, part = %s, value = %s' % (
                                type(record), repr(record), path, part, repr(v))
                            print path_done
                            print parts
                            print part
                            print repr(v)
                            raise e

                if v is None:
                    break

                # We fork the path finding b/c we have a result set
                # e.g. person.cars.color => we fork at cars and will eventually return [blue, red]
                # Second part of the condition is for the case when we want to call
                # a fct on the queryset, e.g. person.cars.all.count
                # we don't want to fork in that case.
                if isinstance(v, QuerySet) and not(parts and hasattr(v, parts[0])):
                    # print v, parts
                    rec = v
                    v = []
                    for item in rec:
                        subitems = self.get_record_path(item, '.'.join(parts))
                        # flatten the lists
                        if isinstance(subitems, list):
                            v += subitems
                        else:
                            v.append(subitems)
                    v = list(set(v))
                    break

                path_done.append(part)

        ret = v

        return ret

    def get_summary(self, request, passive=False):
        ret = u''
        for facet in self.get_facets(request):
            for option in facet['removable_options']:
                href = html_escape.update_query_params(
                    '?' + request.META['QUERY_STRING'], {'page': [1], facet['key']: []})
                ret += u'<a href="%s" title="%s = \'%s\'" data-toggle="tooltip"><span class="label label-default">%s</span></a>' % (
                    href, facet['label'], option['label'], option['label'])

        if passive:
            ret = re.sub(ur'<[^>]*>', ur' ', ret)

        if not ret.strip():
            ret = 'All'

        return mark_safe(ret)

    def get_columns(self, request):
        ret = []
        keys = self.get_option('column_order', None)
        if keys is None:
            ret = [field for field in self.fields if field.get(
                'viewable', False)]
        else:
            #             for key in keys:
            #                 #print key, self.get_field_by_key(key)
            ret = [self.get_field_by_key(key) for key in keys]
        for field in ret:
            field['sortable'] = self._get_sortable_whoosh_field(field)
            field['line'] = field.get('line', 0)

        return ret

    def get_whoosh_facets(self):
        from whoosh import sorting
        # #print [field['key'] for field in self.fields if field.get('count', False)]
        # return []

        ret = []
        for field in self.fields:
            if self.settings.areFieldOptionsShown(field):
                field_facet = sorting.StoredFieldFacet(
                    field['key'],
                    maptype=sorting.Count if field.get(
                        'count', False) else sorting.UnorderedList,
                    # It tells whoosh that the a record can have more than one value
                    # for that facet
                    # Without it whoosh crashes trying to count using a list as
                    # a key
                    allow_overlap=field.get('multivalued', False),
                )
                # We do this to avoid errors trying to split using split() on list
                # See why it is NOT done in the constructor:
                # https://bitbucket.org/mchaput/whoosh/issues/425/split_fn-ignored-in-storedfieldfacet
                if field.get('multivalued', False):
                    #field_facet.split_fn = lambda v: (v if isinstance(v, list) else [])
                    field_facet.split_fn = lambda v: v if isinstance(
                        v, list) else unicode(v).split('|')
                ret.append(field_facet)

        return ret

    @classmethod
    def is_field_indexable(cls, field):
        ret = field.get('search', False) or field.get(
            'count', False) or field.get('filter', False)
        return ret

    def get_whoosh_sortedby(self, request):
        from whoosh import sorting
        key, reverse = self.get_sort_info(request)
        return [sorting.FieldFacet(field, reverse=reverse) for field in self.get_sorted_fields_from_request(request, True)]

    def get_sorted_fields_from_request(self, request, whoosh_fields=False):
        '''Returns a list of field keys to sort by.
            e.g. ('repo_city', 'repo_place')
            The list will combine the sort fields from the request with the default sort fields.
            E.g. request ('c', 'd'); default is ('a', 'b', 'c') => ('c', 'd', 'a', 'b')

            if whoosh_fields is True, returns the whoosh_field keys, e.g. ('a_sortable', 'b')
        '''
        ret = self.get_option('sorted_fields', [])[:]
        # for field in request.GET.get('sort', '').split(','):
        field, reverse = self.get_sort_info(request)
        for field in [field]:
            field = field.strip()
            if field and self._get_sortable_whoosh_field(self.get_field_by_key(field)):
                if field in ret:
                    ret.remove(field)
                ret.insert(0, field)

        if whoosh_fields:
            ret = [self._get_sortable_whoosh_field(
                self.get_field_by_key(field)) for field in ret]

        return ret

    def is_user_agent_banned(self, request):
        # JIRA-673: Baidu doesn't respect the nofollow on the DigiPal search
        # page
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        m = re.search(ur'(?i)baiduspider|AhrefsBot', user_agent)
        return m

    def get_whoosh_index_path(self):
        import os
        return os.path.join(settings.SEARCH_INDEX_PATH, 'faceted', self.key)

    def get_whoosh_index(self):
        from whoosh.index import open_dir
        index = open_dir(self.get_whoosh_index_path())
        return index

    def get_requested_records(self, request):
        if self.is_user_agent_banned(request):
            return []

        self.matched_terms = []
        self.request = request

        # run the query with Whoosh
        index = self.get_whoosh_index()

        # from whoosh.qparser import QueryParser

        search_phrase = request.GET.get('terms', '').strip()

        # make the query
        # get the field=value query from the selected facet options
        field_queries = u''
        for field in self.fields:
            value = request.GET.get(field['key'], '').strip()
            value_diff = request.GET.get(field['key'] + '_diff', '').strip()

            # Reserved field name to fide private content from public users
            if field['key'] == 'PRIVATE':
                value = None
                from digipal.utils import is_staff
                if not is_staff(request):
                    value = u'0'

            if value:
                if field['type'] == 'date':
                    from digipal.utils import get_range_from_date
                    rng = get_range_from_date(value)
                    field_queries += u' %s_min:<=%s %s_max:>=%s ' % (
                        field['key'], rng[1], field['key'], rng[0])
                else:
                    field_queries += u' %s:"%s" ' % (field['key'], value)

            if value_diff:
                value_diff_op = request.GET.get(
                    field['key'] + '_diff_op', '').strip()
                op = {'lte': '<=', 'gte': '>='}.get(value_diff_op, 'gte')
                field_queries += u' %s_diff:%s%s ' % (
                    field['key'], op, value_diff)

        # add the search phrase
        if search_phrase or field_queries:
            qp = self.get_whoosh_parser(index)
            q = qp.parse(u'%s %s' % (search_phrase, field_queries))
        else:
            from whoosh.query.qcore import Every
            q = Every()

        with index.searcher() as searcher:
            # run the query
            facets = self.get_whoosh_facets()

            #
            # result returned by search_page() doesn't support faceting
            # "'ResultsPage' object has no attribute 'groups'"
            #
            # Two possible work-arounds:
            # 1. run two Whoosh searches (one for the groups/facets another for the specific page)
            # 2. run full faceted Whoosh search then paginate the ids
            #
            # TODO: check which one is the most efficient
            #
            # ret = s.search_page(q, 1, pagelen=10, groupedby=facets)

            sortedby = self.get_whoosh_sortedby(request)

            # Will only take top 10/25 results by default
            # ret = s.search(q, groupedby=facets)

            hand_filters.chrono('whoosh:')

            hand_filters.chrono('whoosh.search:')

            view = self.get_selected_view()
            return_snippets = view and view.get(
                'type', '') == 'snippets' and search_phrase

            # ret = s.search(q, groupedby=facets, sortedby=sortedby, limit=1000000)

            ret = self.cached_search(searcher, q, groupedby=facets, sortedby=sortedby,
                                     limit=1000000, get_matched_terms=bool(search_phrase))

            ##ret.fragmenter.charlimit = None

            # ret = s.search(q, groupedby=facets, limit=1000000)
            # ret = s.search(q, sortedby=sortedby, limit=1000000)
            # ret = s.search(q, limit=1000000)
            # #print facets
            # ret = s.search_page(q, 1, pagelen=10, groupedby=facets, sortedby=sortedby)

            hand_filters.chrono(':whoosh.search')

            hand_filters.chrono('whoosh.facets:')
            self.whoosh_groups = ret['facets']
            if 0:
                self.whoosh_groups = {}
                for field in self.fields:
                    if field.get('count', False):
                        #                     if field['key'] == 'hi_has_images':
                        #                         #print ret.groups(field['key'])
                        self.whoosh_groups[field['key']
                                           ] = ret.groups(field['key'])
                    # #self.whoosh_groups[field['key']] = {}
                    # self.whoosh_groups[field['key']] = {}
            hand_filters.chrono(':whoosh.facets')

            # convert the result into a list of model instances
            from django.core.paginator import Paginator

            hand_filters.chrono('whoosh.paginate:')
            # paginate
            self.ids = ret['ids']

            # get highlights from the hits
            if 0:
                for hit in ret:
                    # print repr(hit)
                    # #print '- ' * 20
                    # #print hit['id']

                    if 1 and self.key == 'clauses':
                        #text = self.get_model().objects.get(id=hit['id'])
                        # print repr(hit.highlights('content', top=10))
                        pass

            # Paginate
            page_size = self.get_page_size(request)
            self.paginator = Paginator(
                ret['ids'], page_size if page_size > -1 else 1000000)
            current_page = self.get_page_number(request)
            if current_page < 1:
                current_page = 1
            if current_page > self.paginator.num_pages:
                current_page = self.paginator.num_pages
            self.current_page = self.paginator.page(current_page)
            #ids = [hit['id'] for hit in self.current_page.object_list]
            ids = self.current_page.object_list
            hand_filters.chrono(':whoosh.paginate')

            hand_filters.chrono(':whoosh')

            # #print len(ids)

            # ids = [res['id'] for res in ret]
            hand_filters.chrono('sql:')

            # SQL QUERY to get the records from the current result page
            records = self.get_all_records(True)

            # if overview then instead we get everything and only tag the ids
            if self.get_selected_view()['key'] == 'overview':
                self.overview_all_records = records
#                 for record in records:
#                     ret.append(record)
                # TODO: quick hack to avoid full search to show all bars in red
                # ! filter not implemented in all faceted models
                #ret = records.filter(id__in=self.ids)
                #ret = records.in_bulks(ids)
                # print self.overview_records.count()
                #self.is_full_search = not (search_phrase or field_queries)
#                 if self.is_full_search:
#                     self.ids = []
#                     if str(record.id) in ids and (search_phrase or field_queries):
#                         record.found = True

            if 1:
                # else:
                hand_filters.chrono('bulk:')
                records = records.in_bulk(ids)
                hand_filters.chrono(':bulk')

                if len(records) != len(ids):
                    # raise Exception("DB query didn't retrieve all Whoosh results.")
                    pass

                self.matched_terms = ret.get('matched_terms', [])

                ret = []
                if records:
                    # 'item_part__historical_items'
                    #ret = [records[int(id)] for id in ids if int(id) in records]
                    if len(ids):
                        id_type = type(records.keys()[0])

                    # {1: <rec #1>, 3: <rec #3>} => [<rec #1>, <rec #3>]
                    ret = [records[id_type(id)]
                           for id in ids if id_type(id) in records]

                    # highlight snippets. Only for snippet
                    if return_snippets and hasattr(ret[0], 'content'):
                        terms = self.matched_terms
                        for record in ret:
                            record.snippets = self.get_snippets_from_record(
                                record, terms)

                self.overview_records = ret

            hand_filters.chrono(':sql')

        return ret

    def get_snippets_from_record(self, record, terms):
        from whoosh import highlight
        tools = self.get_snippets_tools()
        content = self.get_plain_text_from_xml(record.content)
        excerpts = highlight.highlight(content, terms=terms, analyzer=tools['analyzer'],
                                       fragmenter=tools['fragmenter'], formatter=tools['formatter'], top=100)
        if excerpts:
            excerpts = tools['template'](excerpts)

        return excerpts

    def get_snippets_tools(self):
        if getattr(self, 'snippets_tools', None) is None:
            # TODO: get that from the existing field type function used for
            # Whoosh schema creation
            from whoosh.analysis import SimpleAnalyzer, StandardAnalyzer, StemmingAnalyzer, CharsetFilter, RegexTokenizer
            from whoosh.support.charset import accent_map
            from whoosh import highlight
            self.snippets_tools = {
                'analyzer': StemmingAnalyzer(minsize=2) | CharsetFilter(accent_map),
                #'analyzer': StandardAnalyzer(minsize=2) | CharsetFilter(accent_map),
                'fragmenter': highlight.ContextFragmenter(maxchars=200, surround=40),
                'formatter': highlight.HtmlFormatter(between=ur'</li><li>'),
                'template': lambda excerpts: ur'<ul><li>%s</li></ul>' % excerpts
            }
        return self.snippets_tools

    def is_full_search(self):
        return self.get_summary(self.request, True).strip().lower() == 'all'

    @classmethod
    def get_cache(cls):
        return utils.get_cache('digipal_faceted_search')

    def cached_search(self, searcher, q, groupedby, sortedby, limit=1000000, get_matched_terms=False):
        # pm dpsearch search --if=images --user=gnoel --qs="terms=seal2"
        search_key = 'query=%s|groups=%s|sorts=%s|terms=%s' % (q,
                                                               ','.join(
                                                                   [f.default_name() for f in groupedby]),
                                                               ','.join(
                                                                   ['%s%s' % ('-' if f.reverse else '', f.default_name()) for f in sortedby]),
                                                               1 if get_matched_terms else 0,
                                                               )
        utils.dplog('Faceted Cache GET: %s' % search_key)

        search_key = utils.get_cache_key_from_string(search_key)

        cache = self.get_cache()

        ret = cache.get(search_key)
        if utils.get_int_from_request_var(self.request, 'nocache'):
            ret = None

        self.cache_hit = False
        if ret is None:
            #utils.dplog('Cache MISS')
            res = searcher.search(
                q, groupedby=groupedby, sortedby=sortedby, limit=limit, terms=get_matched_terms)

            ret = {
                'ids': [hit['id'] for hit in res],
                'facets': {},
                'matched_terms': [],
            }

            if get_matched_terms:
                match_terms = set()
                for hit in res:
                    # list of pairs: (fieldname, term)
                    for term in hit.matched_terms():
                        # Note that these terms are STEMMED!
                        # Whoosh highlighter will resolve them but not our
                        # own tagger.
                        # Private contains binary and cause errors later
                        if term[0] != 'PRIVATE':
                            match_terms.add(term[1])
                ret['matched_terms'] = list(match_terms)

            for field in self.fields:
                if self.settings.areFieldOptionsShown(field):
                    ret['facets'][field['key']] = res.groups(field['key'])

            cache.set(search_key, json.dumps(ret))
        else:
            self.cache_hit = True
            #utils.dplog('Cache HIT')
            ret = json.loads(ret)

        return ret

    def get_total_count(self):
        '''returns the total number of records in the result set'''
        return len(getattr(self, 'ids', []))

    def get_paginator(self):
        return getattr(self, 'paginator', Paginator([], 10))

    def get_current_page(self):
        ret = getattr(self, 'current_page', None)
        return ret

    def get_page_number(self, request):
        return utils.get_int(request.GET.get('page'), 1)

    def get_whoosh_parser(self, index):
        from whoosh.qparser import MultifieldParser, GtLtPlugin

        # TODO: only active columns
        term_fields = [field['key']
                       for field in self.fields if field.get('search', False)]
        parser = MultifieldParser(term_fields, index.schema)
        parser.add_plugin(GtLtPlugin)
        return parser

    def get_selected_view(self):
        ret = None
        if self.views:
            ret = self.views[0]
            for view in self.views:
                if view.get('selected', False):
                    ret = view
                    break
        return ret

    def get_page_size(self, request):
        ret = utils.get_int(request.GET.get('pgs'), 10)
        sizes = self.get_page_sizes(request)
        if ret not in sizes:
            ret = sizes[0]
        return ret

    def get_page_sizes(self, request):
        col_per_row = self.get_col_per_row(request)

        ret = [10, 20, 50, 100]
        selected_view = self.get_selected_view()
        if selected_view:
            pgs = selected_view.get('page_sizes', None)
            if pgs:
                ret = pgs
            else:
                view_type = selected_view.get('type', 'list')
                if view_type == 'grid':
                    ret = [9, 18, 30, 90]
                    ret = [r / 3 * col_per_row for r in ret]
        return ret

    def get_wide_result(self, request):
        return utils.get_int_from_request_var(request, 'wr', 0)

    def get_col_per_row(self, request):
        return 4 if self.get_wide_result(request) else 3

    def get_page_title(self, request):
        ret = 'Search: '
        ret += self.get_label_plural()
        ret += ', '
        ret += self.get_selected_view()['label']
        page = self.get_page_number(request)
        if page > 1:
            ret += ', page %s' % page

        ret += ' ['
        ret += self.get_summary(request, True)
        ret += ']'
        ret += ' | %s' % settings.SITE_TITLE
        return ret


def get_types(request):
    ''' Returns a list of FacetModel instance generated from either
        settings.py::FACETED_SEARCH
        or the local settings.py::FACETED_SEARCH
    '''
    ret = getattr(settings, 'FACETED_SEARCH', None)
    if ret is None:
        import settings as faceted_settings
        ret = faceted_settings.FACETED_SEARCH

    from digipal.utils import is_model_visible
    ret = [
        FacetedModel(ct)
        for ct in ret['types']
        if not ct.get('disabled', False)
        and is_model_visible(ct['model'], request)
    ]

    return ret

# TODO: DIRTY code duplication (see next function!!!)


def simple_search(request, content_type='', objectid='', tabid=''):
    from digipal.views.search import reroute_to_static_search
    ret = reroute_to_static_search(request)
    if ret:
        return ret

    # we just remove jx=1 from the request as we don't want to expose it in the HTML
    # this is an ajax ONLY request parameter.
    request = utils.remove_param_from_request(request, 'jx')

    hand_filters.chrono('VIEW:')

    hand_filters.chrono('SEARCH:')

    context = {'tabid': tabid}

    context['nofollow'] = True
    context['terms'] = request.GET.get('terms', '')

    # select the content type
    cts = get_types(request)
    context['result_type'] = cts[0]
    ct_key = request.GET.get('result_type', context['result_type'].key)
    for ct in cts:
        if ct.key == ct_key:
            context['result_type'] = ct
            break

    ct = context['result_type']

    ct.set_faceted_model_group(cts)

    context['result_type'] = ct

    # run the search
    records = ct.get_requested_records(request)

    return ct


def search_whoosh_view(request, content_type='', objectid='', tabid=''):
    from digipal.views.search import reroute_to_static_search
    ret = reroute_to_static_search(request)
    if ret:
        return ret

    # we just remove jx=1 from the request as we don't want to expose it in the HTML
    # this is an ajax ONLY request parameter.
    request = utils.remove_param_from_request(request, 'jx')

    hand_filters.chrono('VIEW:')

    hand_filters.chrono('SEARCH:')

    context = {'tabid': tabid}

    context['nofollow'] = True
    context['terms'] = request.GET.get('terms', '')

    # select the content type
    cts = get_types(request)
    context['result_type'] = cts[0]
    ct_key = request.GET.get('result_type', context['result_type'].key)
    for ct in cts:
        if ct.key == ct_key:
            context['result_type'] = ct
            break

    ct = context['result_type']

    hand_filters.chrono('set group')
    ct.set_faceted_model_group(cts)

    context['result_type'] = ct

    # run the search
    hand_filters.chrono('get requested records')
    records = ct.get_requested_records(request)

    context['matched_terms'] = ct.matched_terms

    # add the search parameters to the template
    hand_filters.chrono('get facets')
    context['facets'] = ct.get_facets(request)

    hand_filters.chrono('page title')
    context['search_page_title'] = ct.get_page_title(request)

    hand_filters.chrono('columns')
    context['cols'] = ct.get_columns(request)
    context['lines'] = range(
        0, 1 + max([c['line'] for c in context['cols'] if str(c['line']).isdigit()]))

    hand_filters.chrono('sort')
    context['sort_key'], context['sort_reverse'] = ct.get_sort_info(request)
    context['sort_key_valid'] = context['sort_key'] in [f['key']
                                                        for f in context['cols'] if f.get('sortable', False)]

    view = ct.get_selected_view()
    if view:
        context.update(view.get('params', {}))

    # add the results to the template
    context['result'] = list(records)
    previous_record = None
    for record in records:
        record.previous = previous_record
        previous_record = record

    hand_filters.chrono('current page')
    context['current_page'] = ct.get_current_page()

    hand_filters.chrono('summary')
    context['summary'] = ct.get_summary(request)

    context['advanced_search_form'] = True

    hand_filters.chrono('size')
    context['page_sizes'] = ct.get_page_sizes(request)
    context['page_size'] = ct.get_page_size(request)
    context['hit_count'] = ct.get_total_count()
    context['views'] = ct.views
    context['search_help_url'] = utils.get_cms_url_from_slug(
        getattr(settings, 'SEARCH_HELP_PAGE_SLUG', 'search_help'))

    hand_filters.chrono('wide')
    context['wide_result'] = ct.get_wide_result(request)
    # used for the grid.html view
    context['col_per_row'] = ct.get_col_per_row(request)
    context['col_width'] = 12 / context['col_per_row']

    context['wide_page'] = True

    hand_filters.chrono('overview')
    from overview import draw_overview
    draw_overview(ct, context, request)

    hand_filters.chrono(':SEARCH')

    hand_filters.chrono('TEMPLATE:')

    fragment = ''
    if request.is_ajax():
        fragment = '_fragment'

    ret = render_to_response('search/faceted/search_whoosh%s.html' %
                             fragment, context, context_instance=RequestContext(request))

    hand_filters.chrono(':TEMPLATE')

    hand_filters.chrono(':VIEW')

    return ret
