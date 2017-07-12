import json
from digipal import utils

#
# See /digipal/doc/http-api.md for the documentation about the request and response.
#
# Keep this code generic!
#
# Anything specific to a content type goes into custom.py:API<ContentTypeName>
#


class API(object):

    # We put a limit by default as accidental queries for all records can easily happen
    # and that's too long to process.
    # TODO: possibility to override it using a special query string param
    # (@limit=).
    DEFAULT_LIMIT = 100

    @classmethod
    def has_permission(cls, content_type, operation='r', user=None):
        '''
            Return True if a user has permission for a CRUD operation on a content_type
            operation = c|r|u|d OR post|get|put|delete
            content_type = one DigiPal model name (lower case), e.g. 'annotation'
            user = Currently unused
        '''
        ret = False

        # convert HTTP method to CRUD operation
        crud_from_http_method = {'post': 'c',
                                 'get': 'r', 'put': 'u', 'delete': 'd'}
        operation = operation.lower()
        operation = crud_from_http_method.get(operation, operation)

        # TODO: think about caching this
        from mezzanine.conf import settings
        permissions = getattr(settings, 'API_PERMISSIONS', [['crud', 'ALL']])
        for perm, cts in permissions:
            cts = [ct.lower() for ct in cts.split(',')]
            if 'all' in cts or content_type.lower() in cts:
                op_found = operation in perm
                if perm.startswith('-'):
                    if op_found:
                        ret = False
                elif perm.startswith('+'):
                    if op_found:
                        ret = True
                else:
                    ret = op_found

        return ret

    @classmethod
    def convert_response(cls, data, format=None, jsonpcallback=None, xslt=None):
        '''Convert a json response (data) into another format
           Allowed formats:
            * json
            * jsonp (jsonpcallback must also be provided)
            * xml
        '''
        mimetype = 'application/json'
        is_webpage = False

        if format == 'jsonp':
            data = u';%s(%s);' % (jsonpcallback, data)
            mimetype = 'text/javascript'

        if xslt:
            format = 'xml'

        if format == 'xml':
            from django.utils.html import escape

            def get_xml_from_entry(entry=None):
                ret = u''
                if isinstance(entry, dict):
                    for k, v in entry.iteritems():
                        ret += u'<%s>%s</%s>' % (k, get_xml_from_entry(v), k)
                elif isinstance(entry, list) or isinstance(entry, tuple):
                    ret = u''
                    for v in entry:
                        ret += u'<item>%s</item>' % get_xml_from_entry(v)
                elif isinstance(entry, bool):
                    ret += '1' if entry else '0'
                elif entry is None:
                    ret += ''
                else:
                    ret += u'%s' % escape(entry)
                return ret
            prolog = u'<?xml version="1.0" encoding="UTF-8"?>'
            data = u'%s<response>%s</response>' % (
                prolog, get_xml_from_entry(json.loads(data)))
            mimetype = 'text/xml'

        if xslt:
            from digipal.models import ApiTransform
            transforms = ApiTransform.objects.filter(slug=xslt.lower().strip())
            if transforms.count():
                transform = transforms[0]
                template = transform.template
                # apply the transform
                data = utils.get_xslt_transform(data, template)
                mimetype = transform.mimetype
                is_webpage = transform.webpage

        return data, mimetype, is_webpage

    @classmethod
    def get_all_content_types(cls, content_type):
        ret = {'success': True, 'errors': [], 'results': []}
        from digipal import models

        # problem with this format... [[ct1, ct2]]. Should be a simple list,
        # not a nested one.
        ret['results'].append([member.lower() for member in dir(
            models) if hasattr(getattr(models, member), '_meta')])
        ret['count'] = len(ret['results'][0])

        # new version, same output format as other responses
        if content_type == 'content_type2':
            for ct in ret['results'][0]:
                ret['results'].append({'str': ct, 'permissions': ''.join(
                    [op for op in 'crud' if cls.has_permission(ct, op)])})
            del ret['results'][0]

        ret = json.dumps(ret)
        return ret

    @classmethod
    def process_request(cls, request, content_type, selector):
        '''
            Process ALL requests on the API.
            request = a Django request object
            content_type = lower case version of a DigiPal model
            selector = a string that specify which records to work on
        '''
        ret = {'success': True, 'errors': [], 'results': []}

        method = request.GET.get('@method', request.META['REQUEST_METHOD'])
        is_get = method in ['GET']

        # special case for content_type='content_type'
        if content_type in ['content_type', 'content_type2']:
            return cls.get_all_content_types(content_type)

        # refusal if there is no permission for that operation
        if not cls.has_permission(content_type, method):
            ret = {'success': False, 'errors': ['%s method not permitted on %s' % (
                method.upper(), content_type)], 'results': []}
            return json.dumps(ret)

        # find the model
        model = None
        from digipal import models as models1
        # TODO: find a more generic way to include other apps than hard-coding
        # the name here
        from digipal_text import models as models2
        for models in [models1, models2]:
            for member in dir(models):
                if member.lower() == content_type:
                    model = getattr(models, member)
                    if hasattr(model, '_meta'):
                        break

        if not model:
            ret['success'] = False
            ret['errors'] = u'Content type not found (%s).' % content_type
        else:
            # filter the selection
            # filter from the selector passed in the web path
            filters = {}
            ids = cls.get_list_from_csv(selector)
            if ids:
                filters['id__in'] = ids

            # filters in the query string
            # for filter, value in request.REQUEST.iteritems():
            request_params = get_request_params(request)
            for filter, value in request_params.iteritems():
                if filter.startswith('_'):
                    # a conditional filter _FIELD__OP=VALUE
                    filter = filter[1:]
                    if value.startswith('['):
                        value = value[1:-1].split(',')
                    if filter.endswith('__isnull'):
                        # That's necessary otherwise '1' will be only partly
                        # understood by django: it will do an inner join
                        # depiste also doing a IS NULL!
                        value = utils.get_bool_from_string(value)
                    filters[filter] = value

            # get the records
            records = model.objects.filter(**filters).distinct().order_by('id')

            ret['count'] = records.count()

            # limit the result set
            limit = int(request.GET.get('@limit', cls.DEFAULT_LIMIT))
            records = records[0:limit]

            # we refuse changes over the whole data set!
            if records.count() and not filters and not is_get:
                ret['success'] = False
                ret['errors'] = u'Modification of a all records is not supported.'
            else:
                fieldsets = [f for f in request_params.get(
                    '@select', '').split(',') if f]

                # generate the results
                for record in records:
                    ret['results'].append(cls.get_data_from_record(
                        record, request, fieldsets, method))

        ret = json.dumps(ret)

        return ret

    @classmethod
    def get_data_from_record(cls, *args, **kwargs):
        import custom
        custom_processor = custom.APICustom
        custom_cls_name = 'api%s' % type(args[0]).__name__.lower()
        for member in dir(custom):
            if member.lower() == custom_cls_name:
                custom_processor = getattr(custom, member)

        ret = custom_processor.get_data_from_record(*args, **kwargs)

        return ret

    @classmethod
    def get_list_from_csv(cls, csv):
        '''Returns a list of numbers from a comma separated string.
            Empty values are ignored.
            E.g. get_list_from_csv('1,2') => [1, 2]
                get_list_from_csv('') => []
        '''
        ret = []

        if csv:
            ret = [int(v) for v in csv.split(',') if v]

        return ret


def get_request_params(request):
    '''Returns all parameters and values found in the request: GET, POST, PUT, etc
        request.REQUEST only contains GET and POST
    '''
    from django.http import QueryDict

    ret = QueryDict(request.body).copy()
    ret.update(request.GET)
    ret.update(request.POST)

    return ret
