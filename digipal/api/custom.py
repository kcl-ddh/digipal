from django.http import QueryDict
from django.db.models.base import Model
from django.core.exceptions import ObjectDoesNotExist

'''
    Base class for the custom content-type API request processor
'''


class APICustom(object):
    JSON_DATA_TYPES = ['NoneType', 'unicode', 'str',
                       'int', 'float', 'dict', 'list', 'tuple']

    @classmethod
    def get_data_from_record(cls, record, request, fieldsets=[], method='GET'):
        # basic output, only the small literals
        ret = {}

        # set values from the query string
        meta = record.__class__._meta
        for field_name in meta.get_all_field_names():
            field = meta.get_field_by_name(field_name)[0]

            # field_name may not be a property of the record
            # if it is a related object manager
            if not hasattr(record, field_name):
                get_accessor_name = getattr(field, 'get_accessor_name', None)
                if get_accessor_name:
                    field_name = get_accessor_name()

            value = get_param_value_from_request(request, field_name)
            value_set = False

            # set the field value from the request or get it from the record
            if value is not None:
                setattr(record, field_name, value)
                value_set = True
            else:
                try:
                    value = getattr(record, field_name)
                except ObjectDoesNotExist, e:
                    # E.g. a graph without an annotation
                    value = None

            # Add the basic values to the results (or the value of the fields
            # in @select=)
            field_type_name = type(field).__name__

            expanded = u'*' + field_name in fieldsets

            return_field = (field_name in ['id']) or \
                len(fieldsets) == 0 or\
                (field_name in fieldsets) or \
                expanded or value_set

            if (return_field or method in ['PUT', 'POST']):

                # print u'%20s\t%20s\t%s' % (field_name, field_type_name,
                # unicode(value).encode('ascii', 'ignore'))

                # related object for a FK to another model (e.g.
                # graph.annotation)
                field_name_id = field_name + u'__id'
                if isinstance(value, Model):

                    # TODO: support for setting a Null value
                    value_id = get_param_value_from_request(
                        request, field_name_id)
                    if value_id is not None:
                        setattr(record, field_name + '_id', value_id)

                    ret[field_name_id] = value.id if value is not None else None
                    # optional expansion of the related object (e.g.
                    # @select=*image)
                    if expanded:
                        # TODO: call the custom processor
                        value = APICustom.get_data_from_record(
                            value, request, fieldsets, method='GET')
                else:
                    # RelatedObject for another model with a FK to this model (e.g. graph.graph_components)
                    # RelatedObject for another model with a FK to this model (e.g. graph.aspects)
                    # GenericRelatedObjectManager (e.g. image.keywords; GN:
                    # doesn't work anymore! KeywordField)
                    if field_type_name in ['RelatedObject', 'ManyToManyField', 'GenericRelatedObjectManager']:
                        if value is None:
                            # case where a graph has no annotation
                            ret[field_name_id] = None
                    if value and hasattr(value, 'all'):
                        sub_result = []
                        for related_record in value.all():
                            if expanded:
                                sub_result.append(APICustom.get_data_from_record(
                                    related_record, request, fieldsets, method='GET'))
                            else:
                                sub_result.append(related_record.id)
                        value = sub_result

                # force conversion to string as this type is not JSON
                # serialisable
                value_type_name = type(value).__name__
                if value_type_name not in cls.JSON_DATA_TYPES:
                    value = u'%s' % value

                if return_field:
                    ret[field_name] = value

        if method == 'PUT':
            record.save()

        label_field_name = 'str'
        if label_field_name in fieldsets or not fieldsets:
            ret[label_field_name] = u'%s' % record

        return ret


def get_param_value_from_request(request, param_name):
    from generic import get_request_params
    params = get_request_params(request)
    return params.get(param_name, None)

################################################################
#
# Write your content type specific API processors here
#
################################################################


from digipal.templatetags.html_escape import annotation_img


class APIAnnotation(APICustom):
    @classmethod
    def get_data_from_record(cls, record, request, fieldsets=[], method='GET'):
        # write
        path = record.get_shape_path()
        shape_x_diff = get_param_value_from_request(request, 'shape_x_diff')
        shape_y_diff = get_param_value_from_request(request, 'shape_y_diff')
        for p in path:
            if shape_x_diff:
                p[0] += int(shape_x_diff)
            if shape_y_diff:
                p[1] -= int(shape_y_diff)

        centre = None
        import math
        for d in [0, 1]:
            increase_length = get_param_value_from_request(
                request, 'shape_%s_diff' % ('width' if d == 0 else 'height'))
            if increase_length is not None:
                if centre is None:
                    centre = [sum([p[0] for p in path]) / len(path),
                              sum([p[1] for p in path]) / len(path)]
                sample = 2
                increase_length = int(increase_length)
                # find the two most extreme points in dimension d
                path_sorted = sorted(
                    path, key=lambda p: p[d], reverse=(d == 0))
                # get the point in the middle of those two
                avg = [sum([p[0] for p in path_sorted[:sample]]) / sample,
                       sum([p[1] for p in path_sorted[:sample]]) / sample]
                # get the vector from the centre to that point and normalise it
                v = [avg[d2] - centre[d2] for d2 in [0, 1]]
                l = math.sqrt(v[0] * v[0] + v[1] * v[1])
                v = [v[0] * 1.0 / l, v[1] * 1.0 / l]
                # now extend those points
                s = 1
                for i in range(0, sample):
                    #if i >= sample: s = -1
                    path_sorted[i][0] += int(increase_length * v[0] * s)
                    path_sorted[i][1] += int(increase_length * v[1] * s)

        record.set_shape_path(path)

        # generic processing
        ret = super(APIAnnotation, cls).get_data_from_record(
            record, request, fieldsets, method)

        # read
        if 'html' in fieldsets:
            ret['html'] = annotation_img(record)
        if 'htmlr' in fieldsets:
            # This forces the inclusion of the css transform in the output even if rotation = 0.
            # This is useful for the quick preview mode in the edit annotation
            # tab.
            ret['htmlr'] = annotation_img(record, force_rotation=True)

        return ret
