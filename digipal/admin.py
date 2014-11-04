from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.models import LogEntry
from django.db.models import Count
from django import forms
from django.core.urlresolvers import reverse
from models import Allograph, AllographComponent, Alphabet, Annotation, \
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
        CarouselItem, ApiTransform
import reversion
import django_admin_customisations
from mezzanine.core.admin import StackedDynamicInlineAdmin
import re

import logging
dplog = logging.getLogger( 'digipal_debugger')

#########################
#                       #
#   Advanced Filters    #
#                       #
#########################

class ImageAnnotationNumber(SimpleListFilter):
    title = ('Annotations')

    parameter_name = ('Annot')

    def lookups(self, request, model_admin):
        return (
            ('1', ('At least five annotations')),
            ('2', ('Fewer than five annotations')),
            ('3', ('At least one annotation')),
            ('0', ('No annotation')),
        )        

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.exclude(annotation__id__gt=0)
        if self.value() == '3':
            return queryset.filter(annotation__id__gt=0).distinct()
        if self.value() == '1':
            return queryset.annotate(num_annot = Count('annotation__image__item_part')).exclude(num_annot__lt = 5)
        if self.value() == '2':
            return queryset.annotate(num_annot = Count('annotation__image__item_part')).filter(num_annot__lt = 5)
            

class ImageFilterNoItemPart(SimpleListFilter):
    title = 'Item Part'

    parameter_name = ('item_part')

    def lookups(self, request, model_admin):
        return (
            ('with', ('With Item Part')),
            ('without', ('Without Item Part')),
        )        

    def queryset(self, request, queryset):
        if self.value() == 'with':
            return queryset.filter(item_part_id__gt = 0).distinct()
        if self.value() == 'without':
            return queryset.exclude(item_part_id__gt = 0).distinct()

class GraphFilterNoAnnotation(SimpleListFilter):
    title = 'Annotation'

    parameter_name = ('annotation')

    def lookups(self, request, model_admin):
        return (
            ('with', ('With annotation')),
            ('without', ('Annotation is missing')),
        )        

    def queryset(self, request, queryset):
        if self.value() == 'with':
            return queryset.filter(annotation__isnull = False).distinct()
        if self.value() == 'without':
            return queryset.filter(annotation__isnull = True).distinct()

class ImageFilterDuplicateShelfmark(SimpleListFilter):
    title = 'Duplicate Shelfmark'

    parameter_name = ('dup')

    def lookups(self, request, model_admin):
        return (
            ('1', ('has duplicate shelfmark')),
            ('-1', ('has unique shelfmark')),
        )        

    def queryset(self, request, queryset):
        if self.value() in ['1', '-1']:
            all_duplicates_ids = Image.get_duplicates_from_ids().keys()
        
        if self.value() == '1':
            return queryset.filter(id__in = all_duplicates_ids).distinct()
        if self.value() == '-1':
            return queryset.exclude(id__in = all_duplicates_ids).distinct()

class ImageFilterDuplicateFilename(SimpleListFilter):
    title = 'Duplicate Image File'

    parameter_name = ('dupfn')

    def lookups(self, request, model_admin):
        return (
            ('1', ('has duplicate filename')),
            ('-1', ('has unique filename')),
        )        

    def queryset(self, request, queryset):
        if self.value() in ['-1', '1']:
            duplicate_iipimages = Image.objects.all().values_list('iipimage').annotate(dcount=Count('iipimage')).filter(dcount__gt=1).values_list('iipimage', flat=True)
        
        if self.value() == '1':
            return queryset.filter(iipimage__in = duplicate_iipimages).distinct()
        if self.value() == '-1':
            return queryset.exclude(iipimage__in = duplicate_iipimages).distinct()

class ImageWithFeature(SimpleListFilter):
    title = ('Associated Features')

    parameter_name = ('WithFeat')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Has feature(s)')),
            ('no', ('No features')),
        )        

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(annotation__graph__graph_components__features__id__gt = 0).distinct()
        if self.value() == 'no':
            return queryset.exclude(annotation__graph__graph_components__features__id__gt = 0)
           
class ImageWithHand(SimpleListFilter):
    title = ('Associated Hand')

    parameter_name = ('WithHand')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Has Hand(s)')),
            ('no', ('No Hand')),
        )        

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(hands__id__gt=0).distinct()
        if self.value() == 'no':
            return queryset.exclude(hands__id__gt=0).distinct()
           

class DescriptionFilter(SimpleListFilter):
    title = ('To Fix or Check')

    parameter_name = ('toFixOrCheck')

    def lookups(self, request, model_admin):
        return (
            ('toFix', ('Needs to be fixed')),
            ('toCheck', ('Needs to be checked')),
            ('goodlikethis', ('No needs to be checked or fixed')),
        )   

    def queryset(self, request, queryset):
        if self.value() == 'toFix':
            return queryset.filter(description__contains = "FIX")
        if self.value() == 'toCheck':
            return queryset.filter(description__contains = "CHECK")
        if self.value() == 'goodlikethis':
            q = queryset.exclude(description__contains = "CHECK")
            k = q.exclude(description__contains = "FIX")
            return k


class HistoricalItemDescriptionFilter(SimpleListFilter):
    title = ('To Fix or Check')

    parameter_name = ('toFixOrCheck')

    def lookups(self, request, model_admin):
        return (
            ('toFix', ('Needs to be fixed')),
            ('toCheck', ('Needs to be checked')),
            ('goodlikethis', ('No needs to be checked or fixed')),
        )   

    def queryset(self, request, queryset):
        if self.value() == 'toFix':
            return queryset.filter(description__description__contains = "FIX")
        if self.value() == 'toCheck':
            return queryset.filter(description__description__contains = "CHECK")
        if self.value() == 'goodlikethis':
            q = queryset.exclude(description__description__contains = "CHECK")
            k = q.exclude(description__description__contains = "FIX")
            return k

class RelatedObjectNumberFilter(SimpleListFilter):
    title = ('Number of Related Objects')
    parameter_name = ('n')
    
    related_table = 'digipal_image'
    foreign_key = 'item_part_id'
    this_table = 'digipal_itempart'
    this_key = 'id'

    def lookups(self, request, model_admin):
        return (
            ('0', ('None')),
            ('1', ('One')),
            ('1p', ('One or more')),
            ('2p', ('More than one')),
        )   

    def queryset(self, request, queryset):
        select = (ur'''((SELECT COUNT(*) FROM %s fcta WHERE fcta.%s = %s.%s) ''' % (self.related_table, self.foreign_key, self.this_table, self.this_key)) 
        select += ur'%s )'
        if self.value() == '0':
            return queryset.extra(where=[select % ' = 0'])
        if self.value() == '1':
            return queryset.extra(where=[select % ' = 1'])
        if self.value() == '1p':
            return queryset.extra(where=[select % ' >= 1'])
        if self.value() == '2p':
            return queryset.extra(where=[select % ' > 1'])

class ItemPartHasGroupGroupFilter(SimpleListFilter):
    title = ('Membership')

    parameter_name = ('hg')

    def lookups(self, request, model_admin):
        return (
            ('0', ('not part of a group')),
            ('1', ('part of a group')),
        )   

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(group__isnull = False)
        if self.value() == '0':
            return queryset.filter(group__isnull = True)

class ItemPartMembersNumberFilter(RelatedObjectNumberFilter):
    title = ('Number of parts')

    parameter_name = ('np')

    related_table = 'digipal_itempart'
    foreign_key = 'group_id'
    this_table = 'digipal_itempart'
    
class ItemPartImageNumberFilter(RelatedObjectNumberFilter):
    title = ('Number of Images')

    parameter_name = ('ni')

    related_table = 'digipal_image'
    foreign_key = 'item_part_id'
    this_table = 'digipal_itempart'
    
class CurrentItemPartNumberFilter(RelatedObjectNumberFilter):
    title = ('Number of Parts')

    parameter_name = ('ci_nip')

    related_table = 'digipal_itempart'
    foreign_key = 'current_item_id'
    this_table = 'digipal_currentitem'

class HistoricalItemItemPartNumberFilter(RelatedObjectNumberFilter):
    title = ('Number of Parts')

    parameter_name = ('hi_nip')

    related_table = 'digipal_itempartitem'
    foreign_key = 'historical_item_id'
    this_table = 'digipal_historicalitem'

class HistoricalItemKerFilter(SimpleListFilter):
    title = ('Ker')

    parameter_name = ('ker')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Contains Ker')),
            ('no', ('Not contains Ker')),
        )   

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(description__description__contains = "Ker")
        if self.value() == 'no':
            return queryset.exclude(description__description__contains = "Ker")

class HistoricalItemGneussFilter(SimpleListFilter):
    title = ('Gneuss')

    parameter_name = ('gneuss')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Contains Gneuss Number')),
            ('no', ('Not contains Gneuss Number')),
        )   

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(catalogue_numbers__source__label='G.')
        if self.value() == 'no':
            return queryset.exclude(catalogue_numbers__source__label='G.')

# class HandMatchedFilter(SimpleListFilter):
#     title = ('matched with Stewart Hand')
# 
#     parameter_name = ('mwsh')
# 
#     def lookups(self, request, model_admin):
#         return (
#             ('yes', ('Matched')),
#             ('no', ('Not matched')),
#         )   
# 
#     def queryset(self, request, queryset):
#         if self.value() == 'yes':
#             return Hand.objects.filter(item_part__historical_items__in = HistoricalItem.objects.annotate(num_itemparts= Count('itempart')).filter(num_itemparts__gt='1'))
#         if self.value() == 'no':
#             return Hand.objects.filter(item_part__historical_items__in = HistoricalItem.objects.annotate(num_itemparts= Count('itempart')).exclude(num_itemparts__gt='1'))

class HandItempPartFilter(SimpleListFilter):
    title = ('numbers of ItemParts')

    parameter_name = ('morethanoneItemPart')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Has more than one Item Part')),
            ('no', ('Has not more than one Item Part')),
        )   

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return Hand.objects.filter(item_part__historical_items__in = HistoricalItem.objects.annotate(num_itemparts= Count('itempart')).filter(num_itemparts__gt='1'))
        if self.value() == 'no':
            return Hand.objects.filter(item_part__historical_items__in = HistoricalItem.objects.annotate(num_itemparts= Count('itempart')).exclude(num_itemparts__gt='1'))

class HandGlossNumFilter(SimpleListFilter):
    title = ('number of Glossing Hands')

    parameter_name = ('glosshandwithnum')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Has Num. Glossing hands')),
            ('no', ('Not has Num. Glossing hands')),
        )   

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return Hand.objects.filter(gloss_only=True).filter(num_glosses__isnull=False)
        if self.value() == 'no':
            return Hand.objects.filter(gloss_only=True).filter(num_glosses__isnull=True)

class HandGlossTextFilter(SimpleListFilter):
    title = ('has Glossing Text')

    parameter_name = ('glosshandwithtext')

    def lookups(self, request, model_admin):
        return (
            ('yes', ('Has Glossed Text')),
            ('no', ('Not has Glossed text')),
        )   

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return Hand.objects.filter(gloss_only=True).filter(glossed_text__isnull=False)
        if self.value() == 'no':
            return Hand.objects.filter(gloss_only=True).filter(glossed_text__isnull=True) 

class HandImageNumberFilter(RelatedObjectNumberFilter):
    title = ('Number of images')

    parameter_name = ('ni')

    related_table = 'digipal_hand_images'
    foreign_key = 'hand_id'
    this_table = 'digipal_hand'
    

#########################
#                       #
#        Forms          #
#                       #
#########################

fieldsets_hand = (
            #(None, {'fields': ('num', )}),
            ('Item Part and Scribe', {'fields': ('item_part', 'scribe')}),
            ('Labels and notes', {'fields': ('label', 'num', 'display_note', 'internal_note', 'comments')}),
            ('Images', {'fields': ('images',)}),
            ('Other Catalogues', {'fields': ('legacy_id', 'ker', 'scragg', 'em_title')}),
            ('Place and Date', {'fields': ('assigned_place', 'assigned_date')}),
            ('Gloss', {'fields': ('glossed_text', 'num_glossing_hands', 'num_glosses', 'gloss_only')}),
            ('Appearance and other properties', {'fields': ('script', 'appearance', 'relevant', 'latin_only', 'latin_style', 'scribble_only', 'imitative', 'membra_disjecta')}),
            ('Brookes Database', {'fields': ('stewart_record', 'selected_locus', 'locus', 'surrogates')}),
            ) 

class GraphForm(forms.ModelForm):

    class Meta:
        model = Graph    

    def __init__(self, *args, **kwargs):
        # Don't look into other pages for possible grouping graphs.
        # We know that both the containing (group) graph and the child graphs
        # belong to the same page.
        super(GraphForm, self).__init__(*args, **kwargs)
        obj = getattr(self, 'instance', None)
        try:
            if obj and obj.annotation:
                group_field = self.fields['group']
                group_field._set_queryset(Graph.objects.filter(annotation__image=obj.annotation.image).exclude(id=obj.id))
        except Annotation.DoesNotExist:
            print 'ERROR'

class ImageForm(forms.ModelForm):

    class Meta:
        model = Image    

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

    def __init__(self, *args, **kwargs):
        # we change the label of the default value for the media_permission 
        # field so it displays the actual permission (public/private)
        super(RepositoryForm, self).__init__(*args, **kwargs)
        self.fields['media_permission'].empty_label = '%s' % Repository.get_default_media_permission()


#########################
#                       #
#        Inlines        #
#                       #
#########################


class OwnerInline(admin.StackedInline):
    model = Owner

class PlaceInline(admin.StackedInline):
    model = Place

class CurrentItemInline(admin.StackedInline):
    model = CurrentItem

class HistoricalItemInline(admin.StackedInline):
    model = HistoricalItem

class HistoricalItemOwnerInline(admin.StackedInline):
    model = HistoricalItem.owners.through
    verbose_name = "Historical Item"
    verbose_name_plural = "Historical Items"    

class CurrentItemOwnerInline(admin.StackedInline):
    model = CurrentItem.owners.through
    verbose_name = "Current Item"
    verbose_name_plural = "Current Items"    

class ItemPartOwnerInline(admin.StackedInline):
    model = ItemPart.owners.through
    verbose_name = "Item Part"
    verbose_name_plural = "Item Parts"    

class AllographComponentInline(admin.StackedInline):
    model = AllographComponent

    filter_horizontal = ['features']

class IdiographInline(admin.StackedInline):
    model = Idiograph

    filter_horizontal = ['aspects']

class TextItemPartInline(admin.StackedInline):
    model = TextItemPart

#########################
#                       #
#     Model Admins      #
#                       #
#########################

class AllographAdmin(reversion.VersionAdmin):
    model = Allograph

    search_fields = ['name', 'character__name']

    list_display = ['name', 'character', 'hidden', 'created', 'modified']
    list_display_links = ['name', 'character', 'created', 'modified']
    list_editable = ['hidden']

    filter_horizontal = ['aspects']
    inlines = [AllographComponentInline, IdiographInline]

class AlphabetAdmin(reversion.VersionAdmin):
    model = Alphabet

    filter_horizontal = ['ontographs', 'hands']
    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class AnnotationAdmin(reversion.VersionAdmin):
    model = Annotation

    list_display = ['author', 'image', 'status', 'before', 'graph', 'after',
            'thumbnail', 'created', 'modified']
    list_display_links = ['author', 'image', 'status', 'before', 'graph',
            'after', 'created', 'modified']
    search_fields = ['vector_id', 'image__display_label',
            'graph__idiograph__allograph__character__name']
    list_filter = ['author__username', 'graph__idiograph__allograph__character__name']

    readonly_fields = ('graph',)

class AppearanceAdmin(reversion.VersionAdmin):
    model = Appearance

    list_display = ['text', 'sort_order', 'created', 'modified']
    list_display_links = ['text', 'sort_order', 'created', 'modified']
    search_fields = ['text', 'description']


class AspectAdmin(reversion.VersionAdmin):
    model = Aspect

    filter_horizontal = ['features']
    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class CatalogueNumberAdmin(reversion.VersionAdmin):
    model = CatalogueNumber

    list_display = ['historical_item', 'source', 'number', 'created',
            'modified']
    list_display_links = ['historical_item', 'source', 'number', 'created',
            'modified']
    search_fields = ['source__name', 'number']


class CategoryAdmin(reversion.VersionAdmin):
    model = Category

    list_display = ['name', 'sort_order', 'created', 'modified']
    list_display_links = ['name', 'sort_order', 'created', 'modified']
    search_fields = ['name']


class AllographInline(admin.StackedInline):
    model = Allograph

    filter_horizontal = ['aspects']


class CharacterFormAdmin(reversion.VersionAdmin):
    model = CharacterForm

    list_display = ['id', 'name']
    list_display_links = list_display

    search_fields = ['name', 'id']

class CharacterAdmin(reversion.VersionAdmin):
    model = Character

    filter_horizontal = ['components']
    inlines = [AllographInline]
    list_display = ['name', 'unicode_point', 'form', 'created', 'modified']
    list_display_links = ['name', 'unicode_point', 'form', 'created',
            'modified']
    search_fields = ['name', 'form__name']


class CollationAdmin(reversion.VersionAdmin):
    model = Collation

    list_display = ['historical_item', 'fragment', 'leaves', 'front_flyleaves',
            'back_flyleaves', 'created', 'modified']
    list_display_links = ['historical_item', 'fragment', 'leaves',
            'front_flyleaves', 'back_flyleaves',
            'created', 'modified']


class ComponentAdmin(reversion.VersionAdmin):
    model = Component

    filter_horizontal = ['features']
    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']

class ComponentFeatureAdmin(reversion.VersionAdmin):
    model = ComponentFeature
    
    list_display = ['id', 'component', 'feature', 'set_by_default', 'created', 'modified']
    list_display_links = ['id', 'component', 'feature', 'created', 'modified']
    list_editable = ['set_by_default']
    search_fields = ['component__name', 'feature__name']

class CountyAdmin(reversion.VersionAdmin):
    model = County

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class ItemPartInline(admin.StackedInline):
    model = ItemPart

class ItemPartItemInline(StackedDynamicInlineAdmin):
    model = ItemPartItem

class ItemPartItemInlineFromHistoricalItem(ItemPartItemInline):
    verbose_name = 'Item Part'
    verbose_name_plural = 'Item Parts'

class ItemPartItemInlineFromItemPart(ItemPartItemInline):
    verbose_name = 'Historical Item'
    verbose_name_plural = 'Historical Items'

class CurrentItemAdmin(reversion.VersionAdmin):
    model = CurrentItem

    list_display = ['id', 'display_label', 'repository', 'shelfmark', 'get_part_count', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['repository__name', 'shelfmark', 'description', 'display_label']
    list_filter = ['repository', CurrentItemPartNumberFilter]
    
    readonly_fields = ('display_label',)
    
    fieldsets = (
                (None, {'fields': ('display_label', 'repository', 'shelfmark', 'description')}),
                ('Owners', {'fields': ('owners', )}),
                ('Legacy', {'fields': ('legacy_id',)}),
                ) 

    inlines = [ItemPartInline]
    filter_horizontal = ['owners']

class DateEvidenceInline(admin.StackedInline):
    model = DateEvidence


class DateAdmin(reversion.VersionAdmin):
    model = Date

    inlines = [DateEvidenceInline]
    list_display = ['sort_order', 'date', 'created', 'modified']
    list_display_links = ['sort_order', 'date', 'created', 'modified']
    search_fields = ['date']


class DateEvidenceAdmin(reversion.VersionAdmin):
    model = DateEvidence

    list_display = ['hand', 'date', 'reference', 'created', 'modified']
    list_display_links = ['hand', 'date', 'reference', 'created', 'modified']
    search_fields = ['date_description']


class DecorationAdmin(reversion.VersionAdmin):
    model = Decoration

    list_display = ['historical_item', 'illustrated', 'decorated',
            'illuminated', 'created', 'modified']
    list_display_links = ['historical_item', 'illustrated', 'decorated',
            'illuminated', 'created', 'modified']
    search_fields = ['description']


class DescriptionAdmin(reversion.VersionAdmin):
    model = Description

    list_display = ['historical_item', 'source', 'created', 'modified', 'description']
    list_display_links = ['historical_item', 'source', 'created', 'modified']
    search_fields = ['description']
    list_filter = [DescriptionFilter]

class FeatureAdmin(reversion.VersionAdmin):
    model = Feature

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class FormatAdmin(reversion.VersionAdmin):
    model = Format

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class GraphComponentInline(admin.StackedInline):
    model = GraphComponent

    filter_horizontal = ['features']


class GraphAdmin(reversion.VersionAdmin):
    form = GraphForm
    model = Graph

    filter_horizontal = ['aspects']
    inlines = [GraphComponentInline]
    list_display = ['id', 'hand', 'idiograph', 'created', 'modified']
    list_display_links = list_display

    list_filter = [GraphFilterNoAnnotation]

    actions = ['action_update_group']

    def action_update_group(self, request, queryset):
        #from django.http import HttpResponseRedirect
        #graphs = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        from digipal.models import Graph
        graphs = Graph.objects.filter(annotation__isnull=False).select_related('annotation')
        for graph in graphs:
            graph.annotation.set_graph_group()

    action_update_group.short_description = 'Update nestings'


class HairAdmin(reversion.VersionAdmin):
    model = Hair

    list_display = ['label', 'created', 'modified']
    list_display_links = ['label', 'created', 'modified']
    search_fields = ['label']


class PlaceEvidenceInline(admin.StackedInline):
    model = PlaceEvidence


class ProportionInline(admin.StackedInline):
    model = Proportion

class HandDescriptionInline(admin.StackedInline):
    model = HandDescription

class HandFilterSurrogates(admin.SimpleListFilter):
    title = 'Surrogates'
    parameter_name = 'surrogates'
    
    def lookups(self, request, model_admin):
        return (
                    ('1', 'with surrogates'),
                    ('0', 'without surrogates'),
                )
    
    def queryset(self, request, queryset):
        from django.db.models import Q
        q = Q(surrogates__isnull=True) | Q(surrogates__exact='')
        if self.value() == '0':
            return queryset.filter(q)
        if self.value() == '1':
            return queryset.exclude(q)

class HandForm(forms.ModelForm):
    class Meta:
        model = Hand
    label = forms.CharField(widget=forms.TextInput(attrs={'class': 'vTextField'}))

    # On the hand form we only show the Images connected to the associated Item Part 
    def __init__(self, *args, **kwargs):
        hand = kwargs.get('instance', None)
        super(HandForm, self).__init__(*args, **kwargs)
        if hand:
            self.fields['images']._set_queryset(Image.objects.filter(item_part=hand.item_part))

class HandAdmin(reversion.VersionAdmin):
    model = Hand
    form = HandForm

    filter_horizontal = ['images']
    list_display = ['id', 'legacy_id', 'scragg', 'item_part', 'num', 'label', 'script', 'scribe',
            'assigned_date', 'assigned_place', 'created',
            'modified']
    list_display_links = list_display
    search_fields = ['id', 'legacy_id', 'scragg', 'label', 'num', 
            'em_title', 'label', 'item_part__display_label', 
            'display_note', 'internal_note']
    list_filter = ['latin_only', HandItempPartFilter, HandFilterSurrogates, HandGlossNumFilter, HandGlossTextFilter, HandImageNumberFilter]
    
    fieldsets = fieldsets_hand

    inlines = [HandDescriptionInline, DateEvidenceInline, PlaceEvidenceInline, ProportionInline]
    
class CatalogueNumberInline(admin.StackedInline):
    model = CatalogueNumber


class CategoryInline(admin.StackedInline):
    model = Category


class CollationInline(admin.StackedInline):
    model = Collation


class DecorationInline(admin.StackedInline):
    model = Decoration


class DescriptionInline(admin.StackedInline):
    model = Description


class ItemDateInline(admin.StackedInline):
    model = HistoricalItemDate


class ItemOriginInline(admin.StackedInline):
    model = ItemOrigin


class PartLayoutInline(admin.StackedInline):
    model = Layout
    exclude = ('historical_item', )

class ItemLayoutInline(admin.StackedInline):
    model = Layout
    exclude = ('item_part', )

class HistoricalItemAdmin(reversion.VersionAdmin):
    model = HistoricalItem

    search_fields = ['id', 'catalogue_number', 'date', 'name']
    list_display = ['id', 'catalogue_number', 'name', 'date', 'historical_item_type', 'get_part_count', 
                    'historical_item_format', 'created', 'modified']
    list_display_links = list_display
    list_filter = ['historical_item_type', 'historical_item_format', 
                   HistoricalItemDescriptionFilter, HistoricalItemKerFilter, 
                   HistoricalItemGneussFilter, HistoricalItemItemPartNumberFilter]
    
    fieldsets = (
                (None, {'fields': ('display_label', 'name', 'date', 'catalogue_number')}),
                ('Classifications', {'fields': ('historical_item_type', 'historical_item_format', 'categories')}),
                ('Properties', {'fields': ('language', 'vernacular', 'neumed', 'hair', 'url')}),
                ('Owners', {'fields': ('owners',)}),
                ('Legacy', {'fields': ('legacy_id', 'legacy_reference',)}),
                ) 
    
    readonly_fields = ['catalogue_number', 'display_label']
    
    filter_horizontal = ['categories', 'owners']
    inlines = [ItemPartItemInlineFromHistoricalItem, CatalogueNumberInline, CollationInline,
            DecorationInline, DescriptionInline, ItemDateInline,
            ItemOriginInline, ItemLayoutInline]

class HistoricalItemTypeAdmin(reversion.VersionAdmin):
    model = HistoricalItemType

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class GraphInline(admin.StackedInline):
    model = Graph

    filter_horizontal = ['aspects']


class IdiographComponentInline(admin.StackedInline):
    model = IdiographComponent

    filter_horizontal = ['features']


class IdiographAdmin(reversion.VersionAdmin):
    model = Idiograph

    filter_horizontal = ['aspects']
    inlines = [IdiographComponentInline, GraphInline]
    list_display = ['allograph', 'scribe', 'created', 'modified']
    list_display_links = ['allograph', 'scribe', 'created', 'modified']
    search_fields = ['allograph__name']


class ScribeInline(admin.StackedInline):
    model = Scribe


class InstitutionAdmin(reversion.VersionAdmin):
    model = Institution

    inlines = [OwnerInline, ScribeInline]
    list_display = ['institution_type', 'name', 'founder', 'place', 'created',
            'modified']
    list_display_links = ['institution_type', 'name', 'founder', 'place',
            'created', 'modified']
    search_fields = ['name', 'place__name']


class InstitutionTypeAdmin(reversion.VersionAdmin):
    model = InstitutionType

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']

class ItemDateAdmin(reversion.VersionAdmin):
    model = HistoricalItemDate

    list_display = ['historical_item', 'date', 'created', 'modified']
    list_display_links = ['historical_item', 'date', 'created', 'modified']
    search_fields = ['evidence']


class ItemOriginAdmin(reversion.VersionAdmin):
    model = ItemOrigin

    list_display = ['content_type', 'content_object', 'historical_item',
            'created', 'modified']
    list_display_links = ['content_type', 'content_object', 'historical_item',
            'created', 'modified']
    search_fields = ['evidence']


class HandInline(StackedDynamicInlineAdmin):
    model = Hand
    form = HandForm

    filter_horizontal = ['images']
    
    fieldsets = fieldsets_hand


class ImageInline(admin.StackedInline):
    model = Image

    exclude = ['image', 'caption', 'display_label', 'folio_side', 'folio_number']

class ItemSubPartInline(StackedDynamicInlineAdmin):
    model = ItemPart
    
    verbose_name = 'Item Part'
    verbose_name_plural = 'Sub-parts In This Group'
    
    readonly_fields = ['display_label']
    fieldsets = (
                (None, {'fields': ('display_label', 'type',)}),
                ('Locus of this part in the group', {'fields': ('group_locus', )}),
                ('This part is currently found in ...', {'fields': ('current_item', 'locus')}),
                ) 

class ItemPartAdmin(reversion.VersionAdmin):
    model = ItemPart

    # 'current_item', 'locus', 
    list_display = ['id', 'display_label', 'historical_label', 'type', 
                    'get_image_count', 'get_part_count', 
                    'created', 'modified']
    list_display_links = list_display
    search_fields = ['locus', 'display_label',
            'historical_items__display_label', 'current_item__display_label',
            'subdivisions__display_label', 'group__display_label', 
            'type__name']
    list_filter = ('type', ItemPartImageNumberFilter, ItemPartMembersNumberFilter, ItemPartHasGroupGroupFilter)
    
    readonly_fields = ('display_label', 'historical_label')
    fieldsets = (
                (None, {'fields': ('display_label', 'historical_label', 'type',)}),
                ('This part is currently found in ...', {'fields': ('current_item', 'locus', 'pagination')}),
                ('It belongs (or belonged) to another part...', {'fields': ('group', 'group_locus')}),
                ('Owners', {'fields': ('owners',)}),
                ) 
    filter_horizontal = ['owners']
    inlines = [ItemPartItemInlineFromItemPart, ItemSubPartInline, HandInline, ImageInline, PartLayoutInline, TextItemPartInline]
    
    # Due to denormalisation of display_label and its dependency on IPHI.locus, we have
    # to update this field and resave the IP *after* the related models have been saved!
    # See https://code.djangoproject.com/ticket/13950 
    def response_add(self, request, obj, *args, **kwargs):
        obj._update_display_label_and_save()
        return super(ItemPartAdmin, self).response_add(request, obj, *args, **kwargs)
    
    def response_change(self, request, obj, *args, **kwargs):
        obj._update_display_label_and_save()
        return super(ItemPartAdmin, self).response_change(request, obj, *args, **kwargs)

class ItemPartTypeAdmin(reversion.VersionAdmin):
    model = ItemPartType

    list_display = ['name', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['name']

class LanguageAdmin(reversion.VersionAdmin):
    model = Language

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class LatinStyleAdmin(reversion.VersionAdmin):
    model = LatinStyle

    list_display = ['style', 'created', 'modified']
    list_display_links = ['style', 'created', 'modified']
    search_fields = ['style']


class LayoutAdmin(reversion.VersionAdmin):
    model = Layout

    list_display = ['historical_item', 'created', 'modified']
    list_display_links = ['historical_item', 'created', 'modified']
    search_fields = ['comments']


class MeasurementAdmin(reversion.VersionAdmin):
    model = Measurement

    inlines = [ProportionInline]
    list_display = ['label', 'created', 'modified']
    list_display_links = ['label', 'created', 'modified']
    search_fields = ['label']


class OwnerAdmin(reversion.VersionAdmin):
    model = Owner

    list_display = ['id', 'legacy_id', 'get_owned_item', 'get_content_object', 'get_content_type', 'date', 
                    'rebound', 'annotated', 'dubitable', 'created', 'modified']
    list_display_links = list_display
    
    list_filter = ('repository__type__name', ) 

    search_fields = ['evidence', 'institution__name', 'person__name', 'repository__name', 'itempart__display_label', 
                     'current_items__display_label', 'historicalitem__display_label', 'id', 'legacy_id', 'date']

    fieldsets = (
                ('Owner', {'fields': ('repository', 'person', 'institution',)}),
                ('Misc.', {'fields': ('date', 'rebound', 'annotated', 'dubitable', 'evidence')}),
                ('legacy', {'fields': ('legacy_id',)}),
                )
    
    inlines = [HistoricalItemOwnerInline, ItemPartOwnerInline, CurrentItemOwnerInline]
    
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
        
    
class OwnerTypeAdmin(reversion.VersionAdmin):
    model = OwnerType

    list_display = ['id', 'name']
    list_display_links = list_display
    search_fields = ['name']

class CharacterInline(admin.StackedInline):
    model = Character

    filter_horizontal = ['components']

class OntographAdmin(reversion.VersionAdmin):
    model = Ontograph

    list_display = ['name', 'ontograph_type', 'sort_order', 'nesting_level', 'created', 'modified']
    list_display_links = ['name', 'ontograph_type', 'created', 'modified']
    list_editable = ['nesting_level', 'sort_order']
    list_filter = ['ontograph_type', 'nesting_level']
    search_fields = ['name', 'ontograph_type']

    inlines = [CharacterInline]

class OntographTypeAdmin(reversion.VersionAdmin):
    model = OntographType

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']

# This class is used to only display the Hand linked to the Item Part
# on an Image form.
class HandsInlineForm(forms.ModelForm):
    class Meta:
        model = Hand.images.through
 
    def __init__(self, *args, **kwargs):
        object = kwargs.get('parent_object', None)
        if object:
            kwargs.pop('parent_object')
        super(HandsInlineForm, self).__init__(*args, **kwargs)
        if object:
            self.fields['hand']._set_queryset(Hand.objects.filter(item_part=object.item_part))

# This class is only defined to pass a reference to the current Hand to HandsInlineForm
class HandsInlineFormSet(forms.models.BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        kwargs['parent_object'] = self.instance
        return super(HandsInlineFormSet, self)._construct_form(i, **kwargs)

class HandsInline(admin.StackedInline):
    model = Hand.images.through
    form = HandsInlineForm
    formset = HandsInlineFormSet

class ImageAnnotationStatusAdmin(reversion.VersionAdmin):
    model = ImageAnnotationStatus

    list_display = ['name', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['name']

class ImageAdmin(reversion.VersionAdmin):
    form = ImageForm
    change_list_template = 'admin/digipal/change_list.html'

    exclude = ['image', 'caption']
    list_display = ['id', 'display_label', 'get_thumbnail', 
            'get_status_label', 'get_annotation_status_field', 'get_annotations_count', 'get_media_permission_field', 'created', 'modified',
            'get_iipimage_field']
    list_display_links = ['id', 'display_label', 
            'get_annotation_status_field', 'get_media_permission_field', 'created', 'modified',
            'get_iipimage_field']
    search_fields = ['id', 'display_label', 'locus', 
            'item_part__display_label', 'iipimage', 'annotation_status__name']

    actions = ['bulk_editing', 'action_regen_display_label', 'bulk_natural_sorting', 'action_find_nested_annotations']
    
    list_filter = ['annotation_status', 'media_permission__label', ImageAnnotationNumber, ImageWithFeature, ImageWithHand, ImageFilterNoItemPart, ImageFilterDuplicateShelfmark, ImageFilterDuplicateFilename]
    
    readonly_fields = ('display_label', 'folio_number', 'folio_side', 'width', 'height')
    
    fieldsets = (
                (None, {'fields': ('display_label', 'custom_label')}),
                ('Source', {'fields': ('item_part', 'locus', 'folio_side', 'folio_number',)}),
                ('Image file', {'fields': ('iipimage', 'media_permission', 'width', 'height')}),
                ('Internal and editorial information', {'fields': ('annotation_status', 'internal_notes', 'transcription')})
                ) 
    inlines = [HandsInline]
    
    def get_iipimage_field(self, obj):
        from django.template.defaultfilters import truncatechars
        return u'<span title="%s">%s</span>' % (obj.iipimage, truncatechars(obj.iipimage, 15))
    get_iipimage_field.short_description = 'file'
    get_iipimage_field.allow_tags = True
    
    def get_changelist(self, request, **kwargs):
        ''' Override this function in order to enforce a sort order on the folio number and side'''
        from django.contrib.admin.views.main import ChangeList
         
        class SortedChangeList(ChangeList):
            def get_query_set(self, *args, **kwargs):
                qs = super(SortedChangeList, self).get_query_set(*args, **kwargs)
                return Image.sort_query_set_by_locus(qs).prefetch_related('annotation_set', 'hands')
                 
        if request.GET.get('o'):
            return ChangeList
             
        return SortedChangeList        
    
    def get_annotations_count(self, image):
        return image.annotation_set.count()
        #return ''
    get_annotations_count.short_description = '#ann.'
    
    def get_thumbnail(self, image):
        from digipal.templatetags.html_escape import iip_img_a
        return iip_img_a(image, width=70, cls='img-expand', lazy=True)
    get_thumbnail.short_description = 'Thumbnail'
    get_thumbnail.allow_tags = True 

    def action_regen_display_label(self, request, queryset):
        for image in queryset.all():
            image.save()
    action_regen_display_label.short_description = 'Regenerate display labels'

    def action_find_nested_annotations(self, request, queryset):
        from digipal.models import Annotation
        for annotation in Annotation.objects.filter(image__in=queryset).order_by('image__id'):
            annotation.set_graph_group()
    action_find_nested_annotations.short_description = 'Find nested annotations'

    def bulk_editing(self, request, queryset):
        from django.http import HttpResponseRedirect
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(reverse('digipal.views.admin.image.image_bulk_edit') + '?ids=' + ','.join(selected) )
    bulk_editing.short_description = 'Bulk edit'
    
    def get_status_label(self, obj):
        hand_count = obj.hands.count()
        ret = '%d hands' % hand_count
        if not hand_count:
            ret = '<span style="color:red">%s</span>' % ret
        if obj.item_part is None:
            ret = '<span style="color:red">Item Part Missing</span></br>%s' % ret
        return ret
    get_status_label.short_description = 'Hands'
    get_status_label.allow_tags = True 
    
    def get_media_permission_field(self, obj):
        return obj.media_permission
    get_media_permission_field.short_description = 'Permission' 

    def get_annotation_status_field(self, obj):
        return obj.annotation_status
    get_annotation_status_field.short_description = 'Status' 

    def get_locus_label(self, obj):
        return obj.get_locus_label()
    get_locus_label.short_description = 'Locus' 

class PersonAdmin(reversion.VersionAdmin):
    model = Person

    inlines = [OwnerInline]
    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class InstitutionInline(admin.StackedInline):
    model = Institution

class PlaceTypeAdmin(reversion.VersionAdmin):
    model = PlaceType

    list_display = ['name', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['name']


class PlaceAdmin(reversion.VersionAdmin):
    model = Place

    list_display = ['name', 'type', 'region', 'current_county', 'historical_county', 'created', 'modified']
    list_display_links = list_display
    search_fields = ['name', 'type__name']
    list_filter = ['type__name']

    fieldsets = (
                (None, {'fields': ('name', 'type')}),
                ('Regions', {'fields': ('region', 'current_county', 'historical_county')}),
                ('Coordinates', {'fields': ('eastings', 'northings')}),
                ('Legacy', {'fields': ('legacy_id',)}),
                ) 
    inlines = [InstitutionInline, PlaceEvidenceInline]

class PlaceEvidenceAdmin(reversion.VersionAdmin):
    model = PlaceEvidence

    list_display = ['hand', 'place', 'reference', 'created', 'modified']
    list_display_links = ['hand', 'place', 'reference', 'created', 'modified']
    search_fields = ['place_description', 'evidence']


class ProportionAdmin(reversion.VersionAdmin):
    model = Proportion

    list_display = ['hand', 'measurement', 'created', 'modified']
    list_display_links = ['hand', 'measurement', 'created', 'modified']
    search_fields = ['description']


class ReferenceAdmin(reversion.VersionAdmin):
    model = Reference

    list_display = ['name', 'name_index', 'legacy_reference', 'created',
            'modified']
    list_display_links = ['name', 'name_index', 'legacy_reference', 'created',
            'modified']
    search_fields = ['name']


class RegionAdmin(reversion.VersionAdmin):
    model = Region

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']

class RepositoryAdmin(reversion.VersionAdmin):
    form = RepositoryForm

    # disabled as too slow, see JIRA https://jira.dighum.kcl.ac.uk/browse/DIGIPAL-643
    #inlines = [CurrentItemInline]
    list_display = ['name', 'short_name', 'place', 'created', 'modified']
    list_display_links = ['name', 'short_name', 'place', 'created', 'modified']
    search_fields = ['legacy_id', 'name', 'short_name', 'place__name']
    list_filter = ['media_permission__label']


class ScribeAdmin(reversion.VersionAdmin):
    model = Scribe

    filter_horizontal = ['reference']
    inlines = [HandInline, IdiographInline]
    list_display = ['name', 'date', 'scriptorium', 'created', 'modified']
    list_display_links = ['name', 'date', 'scriptorium', 'created', 'modified']
    search_fields = ['legacy_id', 'name', 'date']


class ScriptComponentInline(admin.StackedInline):
    model = ScriptComponent

    filter_horizontal = ['features']


class ScriptAdmin(reversion.VersionAdmin):
    model = Script

    filter_horizontal = ['allographs']
    inlines = [ScriptComponentInline]
    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']
    search_fields = ['name']


class SourceAdmin(reversion.VersionAdmin):
    model = Source

    list_display = ['label', 'priority', 'name', 'created', 'modified']
    list_display_links = ['label', 'name', 'created', 'modified']
    list_editable = ['priority']
    list_filter = ['priority']

    search_fields = ['name', 'label', 'priority']

class StatusAdmin(reversion.VersionAdmin):
    model = Status

    list_display = ['name', 'created', 'modified']
    list_display_links = ['name', 'created', 'modified']


class LogEntryAdmin(reversion.VersionAdmin):
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

class MediaPermissionAdmin(reversion.VersionAdmin):
    list_display = ['label', 'display_message', 'is_private']
    ordering = ['label']

class TextAdmin(reversion.VersionAdmin):
    model = Text
    
    list_display = ['name', 'date', 'created', 'modified']
    list_display_link = list_display
    search_fields = ['name']
    ordering = ['name']
    
    inlines = [TextItemPartInline, CatalogueNumberInline, DescriptionInline]

class CarouselItemAdmin(reversion.VersionAdmin):
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
            return queryset.exclude(matched_hands__isnull=True).exclude(matched_hands__exact='').distinct()
        if self.value() == '0':
            from django.db.models import Q
            return queryset.filter(Q(matched_hands__isnull=True) | Q(matched_hands__exact='')).distinct()

class StewartRecordFilterLegacy(admin.SimpleListFilter):
    title = 'Legacy'
    parameter_name = 'legacy'
    
    def lookups(self, request, model_admin):
        return (
                    ('1', 'has legacy id'),
                    ('0', 'no legacy id'),
                )
    
    def queryset(self, request, queryset):
        from django.db.models import Q
        q = Q(stokes_db__isnull=True) | Q(stokes_db__exact='')
        if self.value() == '0':
            return queryset.filter(q)
        if self.value() == '1':
            return queryset.exclude(q)

class StewartRecordFilterMerged(admin.SimpleListFilter):
    title = 'Already Merged'
    parameter_name = 'merged'
    
    def lookups(self, request, model_admin):
        return (
                    ('1', 'yes'),
                    ('0', 'no'),
                )
    
    def queryset(self, request, queryset):
        from django.db.models import Q
        q = Q(import_messages__isnull=True) | Q(import_messages__exact='')
        if self.value() == '0':
            return queryset.filter(q)
        if self.value() == '1':
            return queryset.exclude(q)

class StewartRecordAdmin(reversion.VersionAdmin):
    model = StewartRecord
    
    list_display = ['id', 'field_hands', 'scragg', 'sp', 'ker', 'gneuss', 'stokes_db', 'repository', 'shelf_mark']
    list_display_links = ['id', 'scragg', 'sp', 'ker', 'gneuss', 'stokes_db', 'repository', 'shelf_mark']
    list_filter = [StewartRecordFilterMatched, StewartRecordFilterLegacy, StewartRecordFilterMerged]
    search_fields = ['id', 'scragg', 'sp', 'ker', 'gneuss', 'stokes_db', 'repository', 'shelf_mark']
    
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
            ret += u'<a href="/admin/digipal/%s/%s/">%s #%s</a>' % (content_type, rid, {'h': u'Hand', 'ip': u'New Hand on Item Part'}[rttype], rid)
        return ret
    field_hands.short_description = 'Matched hand'
    field_hands.allow_tags = True 

    def match_hands(self, request, queryset):
        from django.http import HttpResponseRedirect
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(reverse('stewart_match') + '?ids=' + ','.join(selected) )
    match_hands.short_description = 'Match with DigiPal hand records'
    
    def merge_matched(self, request, queryset):
        from django.http import HttpResponseRedirect
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(reverse('stewart_import') + '?ids=' + ','.join(selected) )
    merge_matched.short_description = 'Merge records into their matched hand records'
    
    def merge_matched_simulation(self, request, queryset):
        from django.http import HttpResponseRedirect
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(reverse('stewart_import') + '?dry_run=1&ids=' + ','.join(selected) )
    merge_matched_simulation.short_description = 'Simulate merge records into their matched hand records'
    
class RequestLogFilterEmpty(admin.SimpleListFilter):
    title = 'Result size'
    parameter_name = 'result_size'
    
    def lookups(self, request, model_admin):
        return (
                    ('0', 'empty'),
                    ('1', 'not empty'),
                )
    
    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(result_count__gt=0).distinct()
        if self.value() == '0':
            return queryset.filter(result_count=0).distinct()

class RequestLogAdmin(admin.ModelAdmin):
    model = RequestLog
    list_display = ['id', 'request_hyperlink', 'field_terms', 'result_count', 'created']
    list_display_links = ['id', 'field_terms', 'result_count', 'created']
    search_fields = ['id', 'request', 'result_count', 'created']
    ordering = ['-id']

    list_filter = [RequestLogFilterEmpty]

    def field_terms(self, record):
        return re.sub('^.*terms=([^&#?]*).*$', r'\1', record.request)
    field_terms.short_description = 'Terms'

    def request_hyperlink(self, record):
        ret = '<a href="%s">%s</a>' % (record.request, record.request)
        return ret
    request_hyperlink.short_description = 'Request'
    request_hyperlink.allow_tags = True

class ApiTransformAdmin(reversion.VersionAdmin):
    model = ApiTransform

    list_display = ['id', 'title', 'slug', 'modified', 'created']
    list_display_links = list_display
    search_fields = ['id', 'title', 'slug']
    ordering = ['id']
    
    fieldsets = (
                (None, {'fields': ('title', 'template', 'description', 'sample_request', 'mimetype', 'webpage')}),
                ) 
    
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

# Let's add the Keywords to the admin interface
try:
    from mezzanine.generic.models import Keyword
    admin.site.register(Keyword)
except ImportError, e:
    pass
