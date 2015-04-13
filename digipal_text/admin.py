from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.models import LogEntry
from django.db.models import Count
from django import forms
from django.core.urlresolvers import reverse
from models import TextContent, TextContentXML, TextContentXMLStatus, TextContentType
import reversion
from mezzanine.core.admin import StackedDynamicInlineAdmin
import re

import logging
from operator import isCallable
dplog = logging.getLogger( 'digipal_debugger')

#-----------------------------------------------------------
# TODO: move this to digipal lib
'''
MessageField(message=''|lambda obj)

a new field that can be added to a form.
it will display the message on the form.
The message is either a string or a function of the model instance that returns a string.
'''

class MessageWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        if value is None: value = ''
        from django.utils.safestring import mark_safe
        return mark_safe(value)
    
class MessageField(forms.Field):
    widget = MessageWidget

    def __init__(self, message='', *args, **kwargs):
        self.message = message
        self.parent_form = None
        return super(MessageField, self).__init__(*args, **kwargs)

    def set_form(self, form):
        self.parent_form = form
        
    def prepare_value(self, value):
        ret = self.message
        if isCallable(ret):
            obj = getattr(self.parent_form, 'instance', None)
            if obj:
                ret = ret(obj)
            else:
                ret = ''
        return ret

class ModelFormWithMessageFields(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModelFormWithMessageFields, self).__init__(*args, **kwargs)
        for f in self.fields.values():
            if isinstance(f, MessageField):
                f.set_form(self)

#-----------------------------------------------------------

class TextContentForm(ModelFormWithMessageFields):
    action_edit = MessageField(message=lambda o: '<a href="/admin/digipal/itempart/%s/edit/">Edit the Text</a>' % o.item_part.id, label='Action')

    class Meta:
        model = TextContent

class TextContentAdmin(reversion.VersionAdmin):
    model = TextContent
    form = TextContentForm

    list_display = ['item_part', 'text', 'get_string_from_languages', 'type', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['item_part__display_label', 'text__name', 'languages__name', 'type__name']
    list_filter = ['languages', 'type']
    
    fieldsets = (
            (None, {'fields': ('item_part', 'text', 'type', 'languages')}),
            ('Actions', {'fields': ('action_edit', )}),
            )
    
class TextContentTypeAdmin(reversion.VersionAdmin):
    model = TextContentType

class TextContentXMLAdmin(reversion.VersionAdmin):
    model = TextContentXML

    list_display = ['id', 'text_content', 'status', 'get_length', 'modified', 'created']
    list_display_links = ['id', 'text_content', 'status', 'modified', 'created']
    search_fields = ['id', 'text_content__item_part__display_label']
    list_filter = ['status', 'text_content__languages', 'text_content__type']
    
#     fieldsets = (
#             (None, {'fields': ('item_part', 'text', 'type', 'languages')}),
#             ('Actions', {'fields': ('action_edit', )}),
#             )

class TextContentXMLStatusAdmin(reversion.VersionAdmin):
    model = TextContentXMLStatus

    list_display = ['id', 'name', 'sort_order']
    list_display_links = ['id', 'name']
    list_editable = ['sort_order']

admin.site.register(TextContent, TextContentAdmin)
admin.site.register(TextContentType, TextContentTypeAdmin)
admin.site.register(TextContentXML, TextContentXMLAdmin)
admin.site.register(TextContentXMLStatus, TextContentXMLStatusAdmin)
