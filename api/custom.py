from django.http import QueryDict

class APICustom(object):
    BASIC_DATA_MAX_LEN = 200
    BASIC_DATA_TYPES = ['NoneType', 'datetime', 'unicode', 'int', 'float']

    @classmethod
    def get_data_from_record(cls, record, request, fieldsets=[], method='GET'):
        # basic output, only the small literals
        ret = {}
        
        # set values from the query string
        meta = record.__class__._meta
        for field in meta.get_all_field_names():
            value = request.REQUEST.get(field, QueryDict(request.body).get(field, None))
            if value is not None:
                setattr(record, field, value)
            else:
                value = getattr(record, field)
            
            # Add the basic values to the results (or the value of the fields in @select=)
            #print field, repr(value), type(value)
            if field in ['id'] or (field in fieldsets) or ('basic' in fieldsets and type(value).__name__ in cls.BASIC_DATA_TYPES and len('%s' % value) <= cls.BASIC_DATA_MAX_LEN):
                if type(value).__name__ in ['datetime']:
                    # force conversion to string as this type is not JSON serialisable
                    value = '%s' % value
                ret[field] = value
                
        if method == 'PUT':
            record.save()

        return ret
    
################################################################
#
# Write your content type specific API processors here
#
################################################################

from digipal.templatetags.html_escape import annotation_img

class APIAnnotation(APICustom):
    @classmethod
    def get_data_from_record(cls, record, request, fieldsets=[], method='GET'):
        ret = super(APIAnnotation, cls).get_data_from_record(record, request, fieldsets, method)
        if 'html' in fieldsets:
            ret['html'] = annotation_img(record)
        return ret
