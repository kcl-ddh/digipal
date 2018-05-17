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
        if value is None:
            value = ''
        from django.utils.safestring import mark_safe
        return mark_safe(value)


class MessageField(forms.Field):
    widget = MessageWidget

    def __init__(self, message='', required=False, *args, **kwargs):
        self.message = message
        self.parent_form = None
        ret = super(MessageField, self).__init__(
            *args, required=required, **kwargs)
        return ret

    def set_form(self, form):
        self.parent_form = form

    def prepare_value(self, value):
        ret = self.message
        if callable(ret):
            obj = getattr(self.parent_form, 'instance', None)
            if obj:
                ret = ret(obj)
            else:
                ret = 'WARNING: no object'
        return ret


class ModelFormWithMessageFields(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModelFormWithMessageFields, self).__init__(*args, **kwargs)
        for f in self.fields.values():
            if isinstance(f, MessageField):
                f.set_form(self)

# -----------------------------------------------------------


def text_content_form_action_edit_message(text_content):
    ret = u''

    if text_content and text_content.pk and text_content.item_part:
        ret = u'<a href="%s">Edit the Text</a>' % text_content.get_absolute_url()

    return ret


class TextContentForm(ModelFormWithMessageFields):
    action_edit = MessageField(
        message=text_content_form_action_edit_message,
        label='Action'
    )

    class Meta:
        fields = '__all__'
        model = TextContent


class FilterTCDuplicate(SimpleListFilter):
    title = 'Duplicates'

    parameter_name = ('dup')

    def lookups(self, request, model_admin):
        return (
            ('0', ('Unique')),
            ('1', ('Duplicate')),
        )

    def queryset(self, request, queryset):
        if self.value() in ['0', '1']:
            duplicates = [r.id for r in TextContent.objects.raw(
                'select tc.* from digipal_text_textcontent tc, digipal_text_textcontent tc2 where tc.id <> tc2.id and tc.item_part_id = tc2.item_part_id AND tc.type_id = tc2.type_id')]
            if self.value() == '1':
                qs = queryset.filter(id__in=duplicates)
            else:
                qs = queryset.exclude(id__in=duplicates)
            return qs


class TextContentAdmin(reversion.VersionAdmin):
    model = TextContent
    form = TextContentForm

    list_display = ['item_part', 'text',
                    'get_string_from_languages', 'type', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['item_part__display_label',
                     'text__name', 'languages__name', 'type__name']
    list_filter = ['languages', 'type', FilterTCDuplicate]

    fieldsets = (
        (None, {'fields': ('item_part', 'text', 'type', 'languages')}),
        ('Attribution', {'fields': ('attribution', )}),
        ('Actions', {'fields': ('action_edit', )}),
    )


class TextContentTypeAdmin(reversion.VersionAdmin):
    model = TextContentType


class FilterCTXDuplicate(SimpleListFilter):
    title = 'Duplicates'

    parameter_name = ('dup')

    def lookups(self, request, model_admin):
        return (
            ('0', ('Unique')),
            ('1', ('Duplicate')),
        )

    def queryset(self, request, queryset):
        if self.value() in ['0', '1']:
            duplicates = [r.id for r in TextContentXML.objects.raw(
                'select tcx.* from digipal_text_textcontentxml tcx, digipal_text_textcontentxml tcx2 where tcx.id <> tcx2.id and tcx.text_content_id = tcx2.text_content_id')]
            if self.value() == '1':
                qs = queryset.filter(id__in=duplicates)
            else:
                qs = queryset.exclude(id__in=duplicates)
            return qs


class FilterCTXEmpty(SimpleListFilter):
    title = 'Empty'

    parameter_name = ('empty')

    def lookups(self, request, model_admin):
        return (
            ('0', ('Not empty')),
            ('1', ('Empty')),
        )

    def queryset(self, request, queryset):
        if self.value() in ['0', '1']:
            #qs = queryset.extra(select={'content_length': 'length(content)'})
            cdt = ' > 2 '
            if self.value() == '1':
                cdt = ' < 3 OR content is null '
            return queryset.extra(where=['length(content) ' + cdt])


class TextContentXMLAdmin(reversion.VersionAdmin):
    model = TextContentXML

    list_display = ['id', 'text_content', 'get_type_name',
                    'status', 'get_length', 'modified', 'created']
    list_display_links = ['id', 'text_content', 'modified', 'created']
    search_fields = ['id', 'text_content__item_part__display_label']
    list_filter = ['status', 'text_content__languages',
                   'text_content__type', FilterCTXEmpty, FilterCTXDuplicate]
    list_editable = ['status']

    def get_queryset(self, request):
        qs = super(TextContentXMLAdmin, self).get_queryset(request)
        qs = qs.extra(select={'content_length': 'length(content)'})
        return qs

    def get_type_name(self, ctx):
        return ctx.text_content.type.name
    get_type_name.short_description = 'Type'
    get_type_name.admin_order_field = 'text_content__type__name'

    def get_length(self, tcx):
        return tcx.content_length
    get_length.short_description = 'Size'
    get_length.admin_order_field = 'content_length'

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
