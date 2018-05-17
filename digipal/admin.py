from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.db.models import Count
from django import forms
from django.core.urlresolvers import reverse
from digipal.models import Allograph, AllographComponent, Alphabet, Annotation, \
    Appearance, Aspect, \
    CatalogueNumber, Category, Character, CharacterForm, Collation, Component, County, \
    ComponentFeature, CurrentItem, \
    Date, DateEvidence, Decoration, Description, \
    Feature, Format, \
    Graph, GraphComponent, \
    Hair, Hand, HistoricalItem, HistoricalItemType, \
    Idiograph, IdiographComponent, Institution, InstitutionType, \
    HistoricalItemDate, \
    ItemOrigin, ItemPart, ItemPartType, ItemPartItem, \
    Language, LatinStyle, Layout, \
    Measurement, \
    Ontograph, OntographType, Owner, OwnerType, ImageAnnotationStatus, \
    Image, Person, Place, PlaceType, PlaceEvidence, Proportion, \
    Reference, Region, Repository, \
    Scribe, Script, ScriptComponent, Source, Status, MediaPermission, \
    StewartRecord, HandDescription, RequestLog, Text, TextItemPart, \
    CarouselItem, ApiTransform, AuthenticityCategory, KeyVal, ContentAttribution
from mezzanine.conf import settings
import reversion
import django_admin_customisations
from mezzanine.core.admin import StackedDynamicInlineAdmin
import re
import admin_filters
import admin_inlines
import admin_forms


class DigiPalModelAdmin(reversion.VersionAdmin):
    '''
        An extension of DigiPalModelAdmin (itself an extension of ModelAdmin)
        which:
            * hides inlines from the change form when they get too large (i.e too slow to display in a reasonable time).
                threshold can be defined in local_settings.py::ADMIN_INLINE_HIDE_SIZE
                default threshold is 100
    '''

    @classmethod
    def get_related_records_count(cls, record, related_model):
        '''Return a query set with all the instances of related_model linking to record'''
        ret = 0
        if not record:
            return ret

        model = record.__class__

        for field_name in model._meta.get_all_field_names():
            field = model._meta.get_field_by_name(field_name)[0]
            get_accessor_name = getattr(field, 'get_accessor_name', None)
            if get_accessor_name:
                field_name = get_accessor_name()

            field = getattr(record, field_name, None)

            if field and related_model in [
                    getattr(field, 'through', ''), getattr(field, 'model', '')]:
                ret = field.count()
                break

        return ret

    def get_inline_instances(self, request, *args, **kwargs):
        ret = super(DigiPalModelAdmin, self).get_inline_instances(
            request, *args, **kwargs)
        threshold = getattr(settings, 'ADMIN_INLINE_HIDE_SIZE', 100)

        instance = args[0] if len(args) else None

        ret = [inline for inline in ret if self.get_related_records_count(
            instance, inline.model) < threshold]

        return ret


#########################
#                       #
#        Forms          #
#                       #
#########################

class GraphForm(forms.ModelForm):

    class Meta:
        model = Graph
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        # Don't look into other pages for possible grouping graphs.
        # We know that both the containing (group) graph and the child graphs
        # belong to the same page.
        super(GraphForm, self).__init__(*args, **kwargs)
        obj = getattr(self, 'instance', None)
        try:
            if obj and obj.annotation:
                group_field = self.fields['group']
                group_field._set_queryset(Graph.objects.filter(
                    annotation__image=obj.annotation.image).exclude(id=obj.id))
        except Annotation.DoesNotExist:
            print 'ERROR'


class ImageForm(forms.ModelForm):

    class Meta:
        model = Image
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        # we change the label of the default value for the media_permission
        # field so it displays the actual permission on the repository object.
        #
        # We also add a link to the repository in the help message under the
        # field
        super(ImageForm, self).__init__(*args, **kwargs)
        image = getattr(self, 'instance', None)
        permission_field = self.fields['media_permission']
        if image:
            # TODO: remove code duplication in the functions
            repository = image.get_repository()
            if repository:
                permission = repository.get_media_permission()
                repository_url = reverse("admin:digipal_repository_change",
                                         args=[repository.id])
                permission_field.empty_label = 'Inherited: %s' % permission
                permission_field.help_text += ur'''<br/>To inherit from the
                    default permission set in the
                    <a target="_blank" href="%s">repository</a>, please
                    select the first option.<br/>''' % repository_url


class RepositoryForm(forms.ModelForm):

    class Meta:
        model = Repository
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        # we change the label of the default value for the media_permission
        # field so it displays the actual permission (public/private)
        super(RepositoryForm, self).__init__(*args, **kwargs)
        self.fields['media_permission'].empty_label = '%s' % Repository.get_default_media_permission()

#########################
#                       #
#     Model Admins      #
#                       #
#########################


class AllographAdmin(DigiPalModelAdmin):
    model = Allograph

    search_fields = ['name', 'character__name']

    list_display = ['name', 'character', 'hidden', 'created', 'modified']
    list_display_links = ['name', 'character', 'created', 'modified']
    list_editable = ['hidden']

    filter_horizontal = ['aspects']
    inlines = [admin_inlines.AllographComponentInline,
               admin_inlines.IdiographInline]


class AlphabetAdmin(DigiPalModelAdmin):
    model = Alphabet

    filter_horizontal = ['ontographs', 'hands']
    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class AnnotationAdmin(DigiPalModelAdmin):
    change_list_template = 'admin/digipal/change_list.html'
    model = Annotation

    fieldsets = (
                (None, {'fields': ('graph', 'image')}),
        #('Preview', {'fields': ('thumbnail', )}),
                ('Metadata', {'fields': ('before',
                                         'after', 'rotation', 'status')}),
                ('Notes', {'fields': ('internal_note', 'display_note')}),
                ('Internal data', {
                 'fields': ('geo_json', 'holes', 'vector_id', 'cutout')}),
    )

    list_display = ['id', 'get_graph_desc', 'thumbnail_with_link',
                    'image', 'author', 'created', 'modified', 'status', 'clientid']
    list_display_links = ['id', 'get_graph_desc',
                          'image', 'author', 'created', 'modified', 'status']
    search_fields = ['id', 'graph__id', 'vector_id', 'image__display_label',
                     'graph__idiograph__allograph__character__name']
    list_filter = ['author__username', 'graph__idiograph__allograph__character__name', 'status', 'type',
                   admin_filters.AnnotationFilterDuplicateClientid, admin_filters.AnnotationFilterLinkedToText]

    def get_graph_desc(self, obj):
        ret = u''
        if obj and obj.graph:
            ret = u'%s (#%s)' % (obj.graph, obj.graph.id)
        return ret
    get_graph_desc.short_description = 'Graph'

    readonly_fields = ('graph',)


class AppearanceAdmin(DigiPalModelAdmin):
    model = Appearance

    list_display = ['text', 'sort_order', 'created', 'modified']
    list_display_links = ['text', 'sort_order', 'created', 'modified']
    search_fields = ['text', 'description']


class AspectAdmin(DigiPalModelAdmin):
    model = Aspect

    filter_horizontal = ['features']
    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class CatalogueNumberAdmin(DigiPalModelAdmin):
    model = CatalogueNumber

    list_display = ['historical_item', 'source', 'number', 'created',
                    'modified']
    list_display_links = ['historical_item', 'source', 'number', 'created',
                          'modified']
    search_fields = ['source__name', 'number']


class CategoryAdmin(DigiPalModelAdmin):
    model = Category

    list_display = ['name', 'sort_order', 'created', 'modified']
    list_display_links = ['name', 'sort_order', 'created', 'modified']
    search_fields = ['name']


class CharacterFormAdmin(DigiPalModelAdmin):
    model = CharacterForm

    list_display = ['id', 'name']
    list_display_links = list_display

    search_fields = ['name', 'id']


class CharacterAdmin(DigiPalModelAdmin):
    model = Character

    filter_horizontal = ['components']
    inlines = [admin_inlines.AllographInline]
    list_display = ['name', 'unicode_point', 'form', 'created', 'modified']
    list_display_links = ['name', 'unicode_point', 'form', 'created',
                          'modified']
    search_fields = ['name', 'form__name']


class CollationAdmin(DigiPalModelAdmin):
    model = Collation

    list_display = ['historical_item', 'fragment', 'leaves', 'front_flyleaves',
                    'back_flyleaves', 'created', 'modified']
    list_display_links = ['historical_item', 'fragment', 'leaves',
                          'front_flyleaves', 'back_flyleaves',
                          'created', 'modified']


class ComponentAdmin(DigiPalModelAdmin):
    model = Component

    filter_horizontal = ['features']
    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class ComponentFeatureAdmin(DigiPalModelAdmin):
    model = ComponentFeature

    list_display = ['id', 'component', 'feature',
                    'set_by_default', 'created', 'modified']
    list_display_links = ['id', 'component', 'feature', 'created', 'modified']
    list_editable = ['set_by_default']
    search_fields = ['component__name', 'feature__name']


class CountyAdmin(DigiPalModelAdmin):
    model = County

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class ItemPartItemInline(StackedDynamicInlineAdmin):
    extra = 3
    model = ItemPartItem


class CurrentItemAdmin(DigiPalModelAdmin):
    model = CurrentItem

    list_display = ['id', 'display_label', 'repository',
                    'shelfmark', 'get_part_count', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['repository__name',
                     'shelfmark', 'description', 'display_label']
    list_filter = ['repository', admin_filters.CurrentItemPartNumberFilter]

    readonly_fields = ('display_label',)

    fieldsets = (
                (None, {'fields': ('display_label',
                                   'repository', 'shelfmark', 'description')}),
                ('Legacy', {'fields': ('legacy_id',)}),
    )

    inlines = [admin_inlines.ItemPartInline,
               admin_inlines.CurrentItemOwnerInline]
    filter_horizontal = ['owners']


class DateAdmin(DigiPalModelAdmin):
    model = Date

    inlines = [admin_inlines.DateEvidenceInlineFromDate]
    list_display = ['sort_order', 'date', 'created', 'modified']
    list_display_links = ['sort_order', 'date', 'created', 'modified']
    search_fields = ['date']


class DateEvidenceAdmin(DigiPalModelAdmin):
    model = DateEvidence

    list_display = ['hand', 'date', 'reference', 'created', 'modified']
    list_display_links = ['hand', 'date', 'reference', 'created', 'modified']
    search_fields = ['date_description']


class DecorationAdmin(DigiPalModelAdmin):
    model = Decoration

    list_display = ['historical_item', 'illustrated', 'decorated',
                    'illuminated', 'created', 'modified']
    list_display_links = ['historical_item', 'illustrated', 'decorated',
                          'illuminated', 'created', 'modified']
    search_fields = ['description']


class DescriptionAdmin(DigiPalModelAdmin):
    model = Description

    list_display = ['historical_item', 'source',
                    'created', 'modified', 'description']
    list_display_links = ['historical_item', 'source', 'created', 'modified']

    search_fields = ['historical_item__display_label',
                     'source__name', 'description']

    list_filter = ['source', admin_filters.DescriptionFilter]


class FeatureAdmin(DigiPalModelAdmin):
    model = Feature

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class FormatAdmin(DigiPalModelAdmin):
    model = Format

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class GraphAdmin(DigiPalModelAdmin):
    form = GraphForm
    model = Graph

    filter_horizontal = ['aspects']
    inlines = [admin_inlines.GraphComponentInline]
    list_display = ['id', 'hand', 'idiograph', 'created', 'modified']
    list_display_links = list_display

    list_filter = [admin_filters.GraphFilterNoAnnotation]

    actions = ['action_update_group']

    def action_update_group(self, request, queryset):
        #from django.http import HttpResponseRedirect
        #graphs = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        graphs = Graph.objects.filter(
            annotation__isnull=False).select_related('annotation')
        for graph in graphs:
            graph.annotation.set_graph_group()

    action_update_group.short_description = 'Update nestings'


class HairAdmin(DigiPalModelAdmin):
    model = Hair

    list_display = ['label', 'created', 'modified']
    list_display_links = ['label', 'created', 'modified']
    search_fields = ['label']


class HandAdmin(DigiPalModelAdmin):
    model = Hand
    form = admin_forms.HandForm

    filter_horizontal = ['images']
    list_display = ['id', 'item_part', 'label', 'num', 'scragg', 'script', 'scribe',
                    'assigned_date', 'assigned_place', 'legacy_id', 'created',
                    'modified']
    list_display_links = ['id', 'item_part', 'label', 'scragg', 'script', 'scribe',
                          'assigned_date', 'assigned_place', 'legacy_id', 'created',
                          'modified']
    search_fields = ['id', 'legacy_id', 'scragg', 'label', 'num',
                     'em_title', 'label', 'item_part__display_label',
                     'display_note', 'internal_note']
    list_filter = ['latin_only', admin_filters.HandItempPartFilter,
                   admin_filters.HandFilterSurrogates, admin_filters.HandGlossNumFilter,
                   admin_filters.HandGlossTextFilter, admin_filters.HandImageNumberFilter]
    list_editable = ['num']

    fieldsets = admin_forms.fieldsets_hand

    inlines = [admin_inlines.HandDescriptionInline, admin_inlines.DateEvidenceInline,
               admin_inlines.PlaceEvidenceInline, admin_inlines.ProportionInline]

    def response_change(self, request, obj, *args, **kwargs):
        image_from_desc = request.POST.get('image_from_desc', False)
        if image_from_desc:
            errors = []
            obj._update_images_from_stints(errors)
            from django.contrib import messages
            for error in errors:
                messages.warning(request, error)
#         obj._update_display_label_and_save()
        return super(HandAdmin, self).response_change(
            request, obj, *args, **kwargs)


class HistoricalItemAdmin(DigiPalModelAdmin):
    model = HistoricalItem

    search_fields = ['id', 'catalogue_number', 'date', 'name']
    list_display = ['id', 'catalogue_number', 'name', 'date', 'historical_item_type', 'get_part_count',
                    'historical_item_format', 'created', 'modified']
    list_display_links = list_display
    list_filter = ['historical_item_type', 'historical_item_format',
                   admin_filters.HistoricalItemDescriptionFilter, admin_filters.HistoricalItemKerFilter,
                   admin_filters.HistoricalItemGneussFilter, admin_filters.HistoricalItemItemPartNumberFilter,
                   admin_filters.HistoricalCatalogueNumberFilter]

    fieldsets = (
                (None, {'fields': ('display_label',
                                   'name', 'date', 'catalogue_number')}),
                ('Classifications', {
                 'fields': ('historical_item_type', 'historical_item_format', 'categories')}),
                ('Properties', {'fields': ('language',
                                           'vernacular', 'neumed', 'hair', 'url')}),
        #('Owners', {'fields': ('owners',)}),
                ('Legacy', {'fields': ('legacy_id', 'legacy_reference',)}),
    )

    readonly_fields = ['catalogue_number', 'display_label']

    filter_horizontal = ['categories', 'owners']

    inlines = [admin_inlines.ItemPartItemInlineFromHistoricalItem, admin_inlines.CatalogueNumberInline,
               admin_inlines.ItemDateInline, admin_inlines.ItemOriginInline, admin_inlines.HistoricalItemOwnerInline,
               admin_inlines.CollationInline, admin_inlines.DecorationInline, admin_inlines.DescriptionInline, admin_inlines.ItemLayoutInline]


class HistoricalItemTypeAdmin(DigiPalModelAdmin):
    model = HistoricalItemType

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class IdiographAdmin(DigiPalModelAdmin):
    model = Idiograph

    filter_horizontal = ['aspects']
    inlines = [admin_inlines.IdiographComponentInline,
               admin_inlines.GraphInline]
    list_display = ['allograph', 'scribe', 'created', 'modified']
    list_display_links = ['allograph', 'scribe', 'created', 'modified']
    search_fields = ['allograph__name']


class InstitutionAdmin(DigiPalModelAdmin):
    model = Institution

    inlines = [admin_inlines.OwnerInline, admin_inlines.ScribeInline]
    list_display = ['institution_type', 'name', 'founder', 'place', 'created',
                    'modified']
    list_display_links = ['institution_type', 'name', 'founder', 'place',
                          'created', 'modified']
    search_fields = ['name', 'place__name']


class InstitutionTypeAdmin(DigiPalModelAdmin):
    model = InstitutionType

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class ItemDateAdmin(DigiPalModelAdmin):
    model = HistoricalItemDate

    list_display = ['historical_item', 'date', 'created', 'modified']
    list_display_links = ['historical_item', 'date', 'created', 'modified']
    search_fields = ['evidence']


class ItemOriginAdmin(DigiPalModelAdmin):
    model = ItemOrigin

    list_display = ['content_type', 'content_object', 'historical_item',
                    'created', 'modified']
    list_display_links = ['content_type', 'content_object', 'historical_item',
                          'created', 'modified']
    search_fields = ['evidence']


class ItemSubPartInline(StackedDynamicInlineAdmin):
    model = ItemPart
    extra = 3

    verbose_name = 'Item Part'
    verbose_name_plural = 'Sub-parts In This Group'

    readonly_fields = ['display_label']
    fieldsets = (
                (None, {'fields': ('display_label', 'type',)}),
                ('Locus of this part in the group',
                 {'fields': ('group_locus', )}),
                ('This part is currently found in ...',
                 {'fields': ('current_item', 'locus')}),
    )


class ItemPartAdmin(DigiPalModelAdmin):
    model = ItemPart

    # 'current_item', 'locus',
    list_display = ['id', 'display_label', 'historical_label', 'type',
                    'get_image_count', 'get_part_count', 'keywords_string',
                    'created', 'modified']
    list_display_links = list_display
    search_fields = ['id', 'locus', 'display_label',
                     'historical_items__display_label', 'current_item__display_label',
                     'subdivisions__display_label', 'group__display_label',
                     'type__name', 'keywords_string', 'notes']
    list_filter = ('type', 'authenticities__category', admin_filters.ItemPartHIFilter, admin_filters.ItemPartImageNumberFilter,
                   admin_filters.ItemPartMembersNumberFilter, admin_filters.ItemPartHasGroupGroupFilter)

    readonly_fields = ('display_label', 'historical_label')
    fieldsets = (
                (None, {'fields': ('display_label',
                                   'historical_label', 'custom_label', 'type',)}),
                ('This part is currently found in ...', {
                 'fields': ('current_item', 'locus', 'pagination')}),
                ('It belongs (or belonged) to another part...',
                 {'fields': ('group', 'group_locus')}),
                ('Notes', {'fields': ('notes', )}),
                ('Keywords', {'fields': ('keywords',)}),
        #('Owners', {'fields': ('owners',)}),
    )
    filter_horizontal = ['owners']
    inlines = [
        admin_inlines.ItemPartItemInlineFromItemPart,
        admin_inlines.ItemSubPartInline,
        admin_inlines.ItemPartAuthenticityInline,
        admin_inlines.HandInline,
        admin_inlines.ImageInline,
        admin_inlines.ItemPartOwnerInline,
        admin_inlines.PartLayoutInline,
        admin_inlines.TextItemPartInline
    ]

#     def get_inline_instances(self, request, *args, **kwargs):
#         ret = super(ItemPartAdmin, self).get_inline_instances(request, *args, **kwargs)
#         ret = [inline for inline in ret if inline.get_queryset(request).count() < 20]
#         return ret

    # Due to denormalisation of display_label and its dependency on IPHI.locus, we have
    # to update this field and resave the IP *after* the related models have been saved!
    # See https://code.djangoproject.com/ticket/13950
    def response_add(self, request, obj, *args, **kwargs):
        obj._update_display_label_and_save()
        return super(ItemPartAdmin, self).response_add(
            request, obj, *args, **kwargs)

    def response_change(self, request, obj, *args, **kwargs):
        obj._update_display_label_and_save()
        return super(ItemPartAdmin, self).response_change(
            request, obj, *args, **kwargs)


class ItemPartTypeAdmin(DigiPalModelAdmin):
    model = ItemPartType

    list_display = ['name', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['name']


class LanguageAdmin(DigiPalModelAdmin):
    model = Language

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class LatinStyleAdmin(DigiPalModelAdmin):
    model = LatinStyle

    list_display = ['style', 'created', 'modified']
    list_display_links = ['style', 'created', 'modified']
    search_fields = ['style']


class LayoutAdmin(DigiPalModelAdmin):
    model = Layout

    list_display = ['historical_item', 'created', 'modified']
    list_display_links = ['historical_item', 'created', 'modified']
    search_fields = ['comments']


class MeasurementAdmin(DigiPalModelAdmin):
    model = Measurement

    inlines = [admin_inlines.ProportionInline]
    list_display = ['label', 'created', 'modified']
    list_display_links = ['label', 'created', 'modified']
    search_fields = ['label']


class OwnerAdmin(DigiPalModelAdmin):
    model = Owner

    list_display = ['id', 'legacy_id', 'get_owned_item', 'get_content_object', 'get_content_type', 'date',
                    'rebound', 'annotated', 'dubitable', 'created', 'modified']
    list_display_links = list_display

    list_filter = ('repository__type__name', )

    search_fields = ['evidence', 'institution__name', 'person__name', 'repository__name', 'itempart__display_label',
                     'current_items__display_label', 'historicalitem__display_label', 'id', 'legacy_id', 'date']

    fieldsets = (
                ('Owner', {'fields': ('repository', 'person', 'institution',)}),
                ('Misc.', {'fields': ('date', 'rebound',
                                      'annotated', 'dubitable', 'evidence')}),
                ('legacy', {'fields': ('legacy_id',)}),
    )

    inlines = [admin_inlines.OwnerHistoricalItemInline,
               admin_inlines.OwnerItemPartInline, admin_inlines.OwnerCurrentItemInline]

    def get_content_type(self, obj):
        ret = unicode(obj.content_type)
        if ret == u'repository':
            ret += u'/' + obj.repository.type.name
        return ret

    def get_owned_item(self, obj):
        return obj.get_owned_item()
    get_owned_item.short_description = 'Owned Item'

    def get_content_object(self, obj):
        return obj.content_object
    get_content_object.short_description = 'Owner'


class OwnerTypeAdmin(DigiPalModelAdmin):
    model = OwnerType

    list_display = ['id', 'name']
    list_display_links = list_display
    search_fields = ['name']


class OntographAdmin(DigiPalModelAdmin):
    model = Ontograph

    list_display = ['name', 'ontograph_type', 'sort_order',
                    'nesting_level', 'created', 'modified']
    list_display_links = ['name', 'ontograph_type', 'created', 'modified']
    list_editable = ['nesting_level', 'sort_order']
    list_filter = ['ontograph_type', 'nesting_level']
    search_fields = ['name', 'ontograph_type']

    inlines = [admin_inlines.CharacterInline]


class OntographTypeAdmin(DigiPalModelAdmin):
    model = OntographType

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']

# This class is only defined to pass a reference to the current Hand to
# HandsInlineForm


class HandsInlineFormSet(forms.models.BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        kwargs['parent_object'] = self.instance
        return super(HandsInlineFormSet, self)._construct_form(i, **kwargs)


class ImageAnnotationStatusAdmin(DigiPalModelAdmin):
    model = ImageAnnotationStatus

    list_display = ['name', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['name']


class ImageAdmin(DigiPalModelAdmin):
    form = ImageForm
    change_list_template = 'admin/digipal/change_list.html'

    # temporary
    #list_per_page = 500

    exclude = ['image', 'caption']
    list_display = ['id', 'display_label', 'locus', 'get_thumbnail',
                    'get_status_label', 'get_annotations_count', 'get_dims', 'get_annotation_status_field', 'get_media_permission_field', 'created', 'modified',
                    'keywords_string', 'get_iipimage_field']
    list_display_links = ['id', 'display_label',
                          'get_annotation_status_field', 'get_media_permission_field', 'created', 'modified',
                          'keywords_string', 'get_iipimage_field']
    list_editable = ['locus']

    search_fields = ['id', 'display_label', 'locus',
                     'item_part__display_label', 'iipimage', 'annotation_status__name',
                     'keywords_string', 'internal_notes', 'transcription']

    actions = ['bulk_editing', 'action_regen_display_label',
               'bulk_natural_sorting', 'action_find_nested_annotations']

    list_filter = ['annotation_status', 'media_permission__label', admin_filters.ImageLocus, admin_filters.ImageAnnotationNumber, admin_filters.ImageWithFeature, admin_filters.ImageWithHand,
                   admin_filters.ImageFilterNoItemPart, admin_filters.ImageFilterDuplicateShelfmark, admin_filters.ImageFilterDuplicateFilename]

    readonly_fields = ('display_label', 'folio_number',
                       'folio_side', 'width', 'height', 'size')

    fieldsets = (
                (None, {'fields': ('display_label', 'custom_label')}),
                ('Source', {'fields': ('item_part',
                                       'locus', 'folio_side', 'folio_number',)}),
                ('Image file', {
                 'fields': ('iipimage', 'media_permission', 'width', 'height', 'size')}),
                ('Internal and editorial information', {
                 'fields': ('annotation_status', 'internal_notes', 'transcription')}),
                ('Keywords', {'fields': ('keywords',)}),
    )
    inlines = [admin_inlines.HandsInline]

    def get_iipimage_field(self, obj):
        from django.template.defaultfilters import truncatechars
        return u'<span title="%s">%s</span>' % (
            obj.iipimage, truncatechars(obj.iipimage, 15))
    get_iipimage_field.short_description = 'file'
    get_iipimage_field.allow_tags = True

    def get_changelist(self, request, **kwargs):
        ''' Override this function in order to enforce a sort order on the folio
         number and side'''
        from django.contrib.admin.views.main import ChangeList

        class SortedChangeList(ChangeList):
            def get_queryset(self, *args, **kwargs):
                qs = super(SortedChangeList, self).get_queryset(
                    *args, **kwargs)
                return Image.sort_query_set_by_locus(qs).prefetch_related(
                    'annotation_set', 'hands').select_related('item_part')

        if request.GET.get('o'):
            return ChangeList

        return SortedChangeList

    def get_dims(self, image):
        return ur'%s x %s' % (image.width, image.height)
    get_dims.short_description = 'Dims'
    get_dims.admin_order_field = 'width'

    def get_annotations_count(self, image):
        return image.annotation_set.count()
        # return ''
    get_annotations_count.short_description = '#A'

    def get_thumbnail(self, image):
        from templatetags.html_escape import iip_img_a
        return iip_img_a(image, width=70, cls='img-expand', lazy=True)
    get_thumbnail.short_description = 'Thumbnail'
    get_thumbnail.allow_tags = True

    def action_regen_display_label(self, request, queryset):
        for image in queryset.all():
            image.save()
    action_regen_display_label.short_description = 'Regenerate display labels'

    def action_find_nested_annotations(self, request, queryset):
        for annotation in Annotation.objects.filter(
                image__in=queryset).order_by('image__id'):
            annotation.set_graph_group()
    action_find_nested_annotations.short_description = 'Find nested annotations'

    def bulk_editing(self, request, queryset):
        from django.http import HttpResponseRedirect
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(reverse(
            'digipal.views.admin.image.image_bulk_edit') + '?ids=' + ','.join(selected))
    bulk_editing.short_description = 'Bulk edit'

    def get_status_label(self, obj):
        hand_count = obj.hands.count()
        ret = '%d' % hand_count
        if not hand_count:
            ret = '<span style="color:red">%s</span>' % ret
        if obj.item_part is None:
            ret = '<span style="color:red">No IP</span></br>%s' % ret
        return ret
    get_status_label.short_description = '#H'
    get_status_label.allow_tags = True

    def get_media_permission_field(self, obj):
        return obj.media_permission
    get_media_permission_field.short_description = 'Perms'

    def get_annotation_status_field(self, obj):
        return obj.annotation_status
    get_annotation_status_field.short_description = 'Status'

    def get_locus_label(self, obj):
        return obj.get_locus_label()
    get_locus_label.short_description = 'Locus'


class PersonAdmin(DigiPalModelAdmin):
    model = Person

    inlines = [admin_inlines.OwnerInline]
    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class PlaceTypeAdmin(DigiPalModelAdmin):
    model = PlaceType

    list_display = ['name', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['name']


class PlaceAdmin(DigiPalModelAdmin):
    model = Place

    list_display = ['name', 'type', 'region', 'current_county',
                    'historical_county', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['name', 'type__name']
    list_filter = ['type__name']

    fieldsets = (
                (None, {'fields': ('name', 'type')}),
                ('Regions', {'fields': ('region',
                                        'current_county', 'historical_county')}),
                ('Coordinates', {'fields': ('eastings', 'northings')}),
                ('Legacy', {'fields': ('legacy_id',)}),
    )
    inlines = [admin_inlines.InstitutionInline,
               admin_inlines.PlaceEvidenceInline]


class PlaceEvidenceAdmin(DigiPalModelAdmin):
    model = PlaceEvidence

    list_display = ['hand', 'place', 'reference', 'created', 'modified']
    list_display_links = ['hand', 'place', 'reference', 'created', 'modified']
    search_fields = ['place_description', 'evidence']


class ProportionAdmin(DigiPalModelAdmin):
    model = Proportion

    list_display = ['hand', 'measurement', 'created', 'modified']
    list_display_links = ['hand', 'measurement', 'created', 'modified']
    search_fields = ['description']


class ReferenceAdmin(DigiPalModelAdmin):
    model = Reference

    list_display = ['name', 'name_index', 'legacy_reference', 'created',
                    'modified']
    list_display_links = ['name', 'name_index', 'legacy_reference', 'created',
                          'modified']
    search_fields = ['name']


class RegionAdmin(DigiPalModelAdmin):
    model = Region

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class RepositoryAdmin(DigiPalModelAdmin):
    form = RepositoryForm

    # disabled as too slow, see JIRA https://jira.dighum.kcl.ac.uk/browse/DIGIPAL-643
    #inlines = [CurrentItemInline]
    list_display = ['name', 'short_name', 'place', 'created', 'modified']
    list_display_links = ['name', 'short_name', 'place', 'created', 'modified']
    search_fields = ['legacy_id', 'name', 'short_name', 'place__name']
    list_filter = ['media_permission__label']


class ScribeAdmin(DigiPalModelAdmin):
    model = Scribe

    filter_horizontal = ['reference']
    inlines = [admin_inlines.HandInline, admin_inlines.IdiographInline]
    list_display = ['name', 'date', 'scriptorium', 'created', 'modified']
    list_display_links = ['name', 'date', 'scriptorium', 'created', 'modified']
    search_fields = ['legacy_id', 'name', 'date']


class ScriptAdmin(DigiPalModelAdmin):
    model = Script

    filter_horizontal = ['allographs']
    inlines = [admin_inlines.ScriptComponentInline]
    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class SourceAdmin(DigiPalModelAdmin):
    model = Source

    list_display = ['label', 'priority', 'name', 'created', 'modified']
    list_display_links = ['label', 'name', 'created', 'modified']
    list_editable = ['priority']
    list_filter = ['priority']

    search_fields = ['name', 'label', 'priority']


class StatusAdmin(DigiPalModelAdmin):
    model = Status

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']


class LogEntryAdmin(DigiPalModelAdmin):
    list_display = ['action_time', 'user', 'content_type', 'change_message',
                    'is_addition', 'is_change', 'is_deletion']
    list_filter = ['action_time', 'user', 'content_type']
    ordering = ['-action_time']
    readonly_fields = ['user', 'content_type', 'object_id', 'object_repr',
                       'action_flag', 'change_message']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Returning False causes table to not show up in admin image
        return True

    def has_delete_permission(self, request, obj=None):
        return False


class MediaPermissionAdmin(DigiPalModelAdmin):
    list_display = ['id', 'label', 'display_message', 'get_permission_label']
    ordering = ['label']


class TextAdmin(DigiPalModelAdmin):
    model = Text

    list_display = ['name', 'date', 'created', 'modified']
    list_display_link = list_display
    search_fields = ['name']
    ordering = ['name']

    inlines = [admin_inlines.TextItemPartInline,
               admin_inlines.CatalogueNumberInline, admin_inlines.DescriptionInline]


class CarouselItemAdmin(DigiPalModelAdmin):
    model = CarouselItem

    list_display = ['title', 'sort_order', 'created', 'modified']
    list_display_link = ['title', 'created', 'modified']
    list_editable = ['sort_order']
    search_fields = ['title']
    ordering = ['sort_order']


class StewartRecordFilterMatched(admin.SimpleListFilter):
    title = 'Match'
    parameter_name = 'matched'

    def lookups(self, request, model_admin):
        return (
            ('1', 'matched'),
            ('0', 'not matched'),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.exclude(matched_hands__isnull=True).exclude(
                matched_hands__exact='').distinct()
        if self.value() == '0':
            from django.db.models import Q
            return queryset.filter(Q(matched_hands__isnull=True) | Q(
                matched_hands__exact='')).distinct()


class StewartRecordAdmin(DigiPalModelAdmin):
    model = StewartRecord

    list_display = ['id', 'field_hands', 'scragg', 'sp', 'ker',
                    'gneuss', 'stokes_db', 'repository', 'shelf_mark']
    list_display_links = ['id', 'scragg', 'sp', 'ker',
                          'gneuss', 'stokes_db', 'repository', 'shelf_mark']
    list_filter = [StewartRecordFilterMatched,
                   admin_filters.StewartRecordFilterLegacy, admin_filters.StewartRecordFilterMerged]
    search_fields = ['id', 'scragg', 'sp', 'ker',
                     'gneuss', 'stokes_db', 'repository', 'shelf_mark']

    actions = ['match_hands', 'merge_matched_simulation', 'merge_matched']

    def field_hands(self, record):
        ret = u''
#         for hand in record.hands.all():
#             if ret: ret += ' ; '
#             ret += u'Hand #%s' % hand.id
#             ret += u', %s' % hand.scribe
#             ret += u', %s' % hand.item_part
        for match_id in record.get_matched_hands():
            rttype, rid = match_id.split(':')
            if ret:
                ret += '<br/>'
            content_type = 'hand'
            if rttype == 'ip':
                content_type = 'itempart'
            ret += u'<a href="/admin/digipal/%s/%s/">%s #%s</a>' % (
                content_type, rid, {'h': u'Hand', 'ip': u'New Hand on Item Part'}[rttype], rid)
        return ret
    field_hands.short_description = 'Matched hand'
    field_hands.allow_tags = True

    def match_hands(self, request, queryset):
        from django.http import HttpResponseRedirect
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(
            reverse('stewart_match') + '?ids=' + ','.join(selected))
    match_hands.short_description = 'Match with DigiPal hand records'

    def merge_matched(self, request, queryset):
        from django.http import HttpResponseRedirect
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(
            reverse('stewart_import') + '?ids=' + ','.join(selected))
    merge_matched.short_description = 'Merge records into their matched hand records'

    def merge_matched_simulation(self, request, queryset):
        from django.http import HttpResponseRedirect
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(
            reverse('stewart_import') + '?dry_run=1&ids=' + ','.join(selected))
    merge_matched_simulation.short_description = 'Simulate merge records into their matched hand records'


class RequestLogAdmin(admin.ModelAdmin):
    model = RequestLog
    list_display = ['id', 'request_hyperlink',
                    'field_terms', 'result_count', 'created']
    list_display_links = ['id', 'field_terms', 'result_count', 'created']
    search_fields = ['id', 'request', 'result_count', 'created']
    ordering = ['-id']

    list_filter = [admin_filters.RequestLogFilterEmpty]

    def field_terms(self, record):
        return re.sub('^.*terms=([^&#?]*).*$', r'\1', record.request)
    field_terms.short_description = 'Terms'

    def request_hyperlink(self, record):
        ret = '<a href="%s">%s</a>' % (record.request, record.request)
        return ret
    request_hyperlink.short_description = 'Request'
    request_hyperlink.allow_tags = True


class ApiTransformAdmin(DigiPalModelAdmin):
    model = ApiTransform

    list_display = ['id', 'title', 'slug', 'modified', 'created']
    list_display_links = list_display
    search_fields = ['id', 'title', 'slug']
    ordering = ['id']

    fieldsets = (
                (None, {'fields': ('title', 'template', 'description',
                                   'sample_request', 'mimetype', 'webpage')}),
    )


class AuthenticityCategoryAdmin(DigiPalModelAdmin):
    model = AuthenticityCategory

    list_display = ['id', 'name', 'slug', 'modified', 'created']
    list_display_links = list_display
    search_fields = ['id', 'name', 'slug']
    ordering = ['name']


class ContentAttributionAdmin(DigiPalModelAdmin):
    model = ContentAttribution

    list_display = ['id', 'title', 'modified', 'created']
    list_display_links = list_display
    search_fields = ['id', 'title', 'message']
    ordering = ['title']


class KeyValAdmin(DigiPalModelAdmin):
    model = KeyVal

    list_display = ['id', 'key', 'modified', 'created']
    list_display_links = list_display
    search_fields = ['id', 'key']
    ordering = ['key']

#     fieldsets = (
#                 (None, {'fields': ('title', 'template', 'description', 'sample_request', 'mimetype', 'webpage')}),
#                 )


admin.site.register(Allograph, AllographAdmin)
admin.site.register(Alphabet, AlphabetAdmin)
admin.site.register(Annotation, AnnotationAdmin)
admin.site.register(Appearance, AppearanceAdmin)
admin.site.register(Aspect, AspectAdmin)
admin.site.register(CatalogueNumber, CatalogueNumberAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Character, CharacterAdmin)
admin.site.register(CharacterForm, CharacterFormAdmin)
admin.site.register(Collation, CollationAdmin)
admin.site.register(Component, ComponentAdmin)
admin.site.register(ComponentFeature, ComponentFeatureAdmin)
admin.site.register(County, CountyAdmin)
admin.site.register(CurrentItem, CurrentItemAdmin)
admin.site.register(Date, DateAdmin)
admin.site.register(DateEvidence, DateEvidenceAdmin)
admin.site.register(Decoration, DecorationAdmin)
admin.site.register(Description, DescriptionAdmin)
admin.site.register(Feature, FeatureAdmin)
admin.site.register(Format, FormatAdmin)
admin.site.register(Graph, GraphAdmin)
admin.site.register(Hair, HairAdmin)
admin.site.register(Hand, HandAdmin)
admin.site.register(HistoricalItem, HistoricalItemAdmin)
admin.site.register(HistoricalItemType, HistoricalItemTypeAdmin)
admin.site.register(Idiograph, IdiographAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(InstitutionType, InstitutionTypeAdmin)
admin.site.register(HistoricalItemDate, ItemDateAdmin)
admin.site.register(ItemOrigin, ItemOriginAdmin)
admin.site.register(ItemPart, ItemPartAdmin)
admin.site.register(ItemPartType, ItemPartTypeAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(LatinStyle, LatinStyleAdmin)
admin.site.register(Layout, LayoutAdmin)
admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(Measurement, MeasurementAdmin)
admin.site.register(Owner, OwnerAdmin)
admin.site.register(OwnerType, OwnerTypeAdmin)
admin.site.register(Ontograph, OntographAdmin)
admin.site.register(OntographType, OntographTypeAdmin)
admin.site.register(ImageAnnotationStatus, ImageAnnotationStatusAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(PlaceType, PlaceTypeAdmin)
admin.site.register(Place, PlaceAdmin)
admin.site.register(PlaceEvidence, PlaceEvidenceAdmin)
admin.site.register(Proportion, ProportionAdmin)
admin.site.register(Reference, ReferenceAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(Repository, RepositoryAdmin)
admin.site.register(Scribe, ScribeAdmin)
admin.site.register(Script, ScriptAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(MediaPermission, MediaPermissionAdmin)
admin.site.register(CarouselItem, CarouselItemAdmin)
admin.site.register(StewartRecord, StewartRecordAdmin)
admin.site.register(RequestLog, RequestLogAdmin)
admin.site.register(ApiTransform, ApiTransformAdmin)
admin.site.register(Text, TextAdmin)
admin.site.register(AuthenticityCategory, AuthenticityCategoryAdmin)
admin.site.register(ContentAttribution, ContentAttributionAdmin)
admin.site.register(KeyVal, KeyValAdmin)

# Let's add the Keywords to the admin interface
try:
    from mezzanine.generic.models import Keyword
    admin.site.register(Keyword)
except ImportError as e:
    pass
