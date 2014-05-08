from django.http import QueryDict
from django.db.models.base import Model

'''
    Base class for the custom content-type API request processor
'''
class APICustom(object):
    JSON_DATA_TYPES = ['NoneType', 'unicode', 'str', 'int', 'float', 'dict', 'list', 'tuple']

    @classmethod
    def get_data_from_record(cls, record, request, fieldsets=[], method='GET'):
        # basic output, only the small literals
        ret = {}
        
        # set values from the query string
        meta = record.__class__._meta
        for field_name in meta.get_all_field_names():
            field = meta.get_field_by_name(field_name)[0]
            get_accessor_name = getattr(field, 'get_accessor_name', None)
            if get_accessor_name:
                field_name = get_accessor_name()
                
            value = request.REQUEST.get(field_name, QueryDict(request.body).get(field_name, None))
            
            # set the field value from the request or get it from the record
            if value is not None:
                setattr(record, field_name, value)
            else:
                value = getattr(record, field_name)
            
            # Add the basic values to the results (or the value of the fields in @select=)
            field_type_name = type(field).__name__
            
            expanded = u'*'+field_name in fieldsets

            #print field, repr(value), type(value)
            if (field_name in ['id']) or \
                len(fieldsets) == 0 or\
                (field_name in fieldsets) or \
                expanded:
                
                #if field_type_name in ['ForeignKey']:
                if isinstance(value, Model):
                    ret[field_name+u'__id'] = value.id if value is not None else None
                    # optional expansion of the related object (e.g. @select=*image)
                    if expanded:
                        # TODO: call the custom processor
                        value = APICustom.get_data_from_record(value, request, fieldsets, method='GET')
                
                if field_type_name in ['RelatedObject']:
                    sub_result = []
                    for related_record in value.all():
                        if expanded:
                            sub_result.append(APICustom.get_data_from_record(related_record, request, fieldsets, method='GET'))
                        else:
                            sub_result.append(related_record.id)
                    value = sub_result
                    
                # force conversion to string as this type is not JSON serialisable
                value_type_name = type(value).__name__
                if value_type_name not in cls.JSON_DATA_TYPES:
                    value = u'%s' % value

                ret[field_name] = value
                
        if method == 'PUT':
            record.save()
            
        label_field_name = 'str'
        if label_field_name in fieldsets or not fieldsets:
            ret[label_field_name] = u'%s' % record

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
