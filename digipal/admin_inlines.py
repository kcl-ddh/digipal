from django.contrib import admin
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
    CarouselItem, ApiTransform, ItemPartAuthenticity
from mezzanine.conf import settings
from mezzanine.core.admin import StackedDynamicInlineAdmin
import re
import admin_forms

#########################
#                       #
#   Generic Inlines     #
#                       #
#########################

'''
    The Inlines below are optimisations.
    This is to avoid running one database query per FK dropdown
    per form in an inline formset. This saves a a lot of time on
    change forms that have a lot of related records or inlines
    with many foreign key drop downs. 
'''


class DigiPalInline(admin.StackedInline):
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(DigiPalInline, self).formfield_for_dbfield(
            db_field, **kwargs)
        if hasattr(formfield, 'choices'):
            # dirty trick so queryset is evaluated and cached in .choices
            formfield.choices = formfield.choices
        return formfield


class DigiPalInlineDynamic(StackedDynamicInlineAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(DigiPalInlineDynamic, self).formfield_for_dbfield(
            db_field, **kwargs)
        if hasattr(formfield, 'choices'):
            # dirty trick so queryset is evaluated and cached in .choices
            formfield.choices = formfield.choices
        return formfield

#########################
#                       #
#   Custom Inlines      #
#                       #
#########################


class OwnerInline(DigiPalInline):
    model = Owner


class PlaceInline(DigiPalInline):
    model = Place


class CurrentItemInline(DigiPalInline):
    model = CurrentItem


class HistoricalItemInline(DigiPalInline):
    model = HistoricalItem


class HistoricalItemOwnerInline(DigiPalInline):
    model = HistoricalItem.owners.through
    verbose_name = "Ownership"
    verbose_name_plural = "Ownerships"


class ItemPartOwnerInline(DigiPalInline):
    model = ItemPart.owners.through
    verbose_name = "Ownership"
    verbose_name_plural = "Ownerships"


class CurrentItemOwnerInline(DigiPalInline):
    model = CurrentItem.owners.through
    verbose_name = "Ownership"
    verbose_name_plural = "Ownerships"


class OwnerHistoricalItemInline(DigiPalInline):
    model = HistoricalItem.owners.through
    verbose_name = "Historical Item"
    verbose_name_plural = "Historical Items"


class OwnerCurrentItemInline(DigiPalInline):
    model = CurrentItem.owners.through
    verbose_name = "Current Item"
    verbose_name_plural = "Current Items"


class OwnerItemPartInline(DigiPalInline):
    model = ItemPart.owners.through
    verbose_name = "Item Part"
    verbose_name_plural = "Item Parts"


class AllographComponentInline(DigiPalInline):
    model = AllographComponent

    filter_horizontal = ['features']


class IdiographInline(DigiPalInline):
    model = Idiograph

    filter_horizontal = ['aspects']


class TextItemPartInline(DigiPalInline):
    model = TextItemPart


class AllographInline(DigiPalInline):
    model = Allograph

    filter_horizontal = ['aspects']


class ItemPartInline(DigiPalInline):
    model = ItemPart


class ItemPartItemInline(DigiPalInlineDynamic):
    extra = 3
    model = ItemPartItem


class ItemPartItemInlineFromHistoricalItem(ItemPartItemInline):
    verbose_name = 'Item Part'
    verbose_name_plural = 'Item Parts'


class ItemPartItemInlineFromItemPart(ItemPartItemInline):
    verbose_name = 'Historical Item'
    verbose_name_plural = 'Historical Items'


class DateEvidenceInline(DigiPalInline):
    model = DateEvidence


class DateEvidenceInlineFromDate(DigiPalInline):
    model = DateEvidence
    fk_name = 'date'


class GraphComponentInline(DigiPalInline):
    model = GraphComponent

    filter_horizontal = ['features']


class PlaceEvidenceInline(DigiPalInline):
    model = PlaceEvidence


class ProportionInline(DigiPalInline):
    model = Proportion


class HandDescriptionInline(DigiPalInline):
    model = HandDescription


class CatalogueNumberInline(DigiPalInline):
    model = CatalogueNumber


class CategoryInline(DigiPalInline):
    model = Category


class CollationInline(DigiPalInline):
    model = Collation


class DecorationInline(DigiPalInline):
    model = Decoration


class DescriptionInline(DigiPalInline):
    model = Description


class ItemDateInline(DigiPalInline):
    model = HistoricalItemDate


class ItemOriginInline(DigiPalInline):
    model = ItemOrigin


class PartLayoutInline(DigiPalInline):
    model = Layout
    exclude = ('historical_item', )


class ItemLayoutInline(DigiPalInline):
    model = Layout
    exclude = ('item_part', )


class GraphInline(DigiPalInline):
    model = Graph

    filter_horizontal = ['aspects']


class IdiographComponentInline(DigiPalInline):
    model = IdiographComponent

    filter_horizontal = ['features']


class ScribeInline(DigiPalInline):
    model = Scribe


class ImageInline(DigiPalInline):
    model = Image

#     def formfield_for_dbfield(self, db_field, **kwargs):
#         formfield = super(ImageInline, self).formfield_for_dbfield(db_field, **kwargs)
#         #print db_field.name, repr(formfield), repr(db_field)
#         #if db_field.name in ['annotation_status']:
#         if hasattr(formfield, 'choices'):
#             #print 'HERE'
#             # dirty trick so queryset is evaluated and cached in .choices
#             formfield.choices = formfield.choices
#         return formfield

    # removed keywords as it generates too many queries (one per form in the
    # formset)
    exclude = ['image', 'caption', 'display_label', 'folio_side',
               'folio_number', 'width', 'height', 'size', 'keywords']


class ItemPartAuthenticityInline(DigiPalInlineDynamic):
    model = ItemPartAuthenticity
    extra = 3

    verbose_name = 'Authenticity note'
    verbose_name_plural = 'Authenticity notes'

#    readonly_fields = ['display_label']
#     fieldsets = (
#                 (None, {'fields': ('name', 'type',)}),
#                 ('Locus of this part in the group', {'fields': ('group_locus', )}),
#                 ('This part is currently found in ...', {'fields': ('current_item', 'locus')}),
#                 )


class ItemSubPartInline(DigiPalInlineDynamic):
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


class CharacterInline(DigiPalInline):
    model = Character

    filter_horizontal = ['components']

# MOA-116: we don't use DigiPalInline as it overwrites the hand selection
# done by admin_forms.HandsInlineForm and shows all hands instead.


class HandsInline(admin.StackedInline):
    model = Hand.images.through
    form = admin_forms.HandsInlineForm
    formset = admin_forms.HandsInlineFormSet


class InstitutionInline(DigiPalInline):
    model = Institution


class ScriptComponentInline(DigiPalInline):
    model = ScriptComponent

    filter_horizontal = ['features']


class HandInline(DigiPalInlineDynamic):
    model = Hand
    extra = 5
    form = admin_forms.HandForm

    filter_horizontal = ['images']

    fieldsets = admin_forms.fieldsets_hand
