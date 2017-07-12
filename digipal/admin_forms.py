from django.contrib import admin
from django.db.models import Count
from django import forms
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
from mezzanine.conf import settings
import re

# ----------------------------------------------------------------

fieldsets_hand = (
    #(None, {'fields': ('num', )}),
    ('Item Part and Scribe', {'fields': ('item_part', 'scribe')}),
    ('Labels and notes', {'fields': ('label', 'num',
                                     'display_note', 'internal_note', 'comments')}),
    ('Images', {'fields': ('images', 'image_from_desc')}),
    ('Other Catalogues', {
     'fields': ('legacy_id', 'ker', 'scragg', 'em_title')}),
    ('Place and Date', {'fields': ('assigned_place', 'assigned_date')}),
    ('Gloss', {'fields': ('glossed_text',
                          'num_glossing_hands', 'num_glosses', 'gloss_only')}),
    ('Appearance and other properties', {'fields': ('script', 'appearance', 'relevant',
                                                    'latin_only', 'latin_style', 'scribble_only', 'imitative', 'membra_disjecta')}),
    #('Brookes Database', {'fields': ('stewart_record', 'selected_locus', 'locus', 'surrogates')}),
)

# This class is only defined to pass a reference to the current Hand to
# HandsInlineForm


class HandsInlineFormSet(forms.models.BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        kwargs['parent_object'] = self.instance
        return super(HandsInlineFormSet, self)._construct_form(i, **kwargs)

# This class is used to only display the Hand linked to the Item Part
# on an Image form.


class HandsInlineForm(forms.ModelForm):
    class Meta:
        model = Hand.images.through
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        object = kwargs.get('parent_object', None)
        if object:
            kwargs.pop('parent_object')
        super(HandsInlineForm, self).__init__(*args, **kwargs)
        if object:
            self.fields['hand']._set_queryset(
                Hand.objects.filter(item_part=object.item_part))


class HandForm(forms.ModelForm):
    class Meta:
        model = Hand
        fields = '__all__'

    label = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'vTextField'}))
    image_from_desc = forms.BooleanField(
        label='Reset from Stints', help_text='Tick this to reset the above image selection from the stints marked-up in the hand descriptions.', required=False)

    # On the hand form we only show the Images connected to the associated
    # Item Part
    def __init__(self, *args, **kwargs):
        hand = kwargs.get('instance', None)
        super(HandForm, self).__init__(*args, **kwargs)
        if hand:
            self.fields['images']._set_queryset(Image.sort_query_set_by_locus(
                Image.objects.filter(item_part=hand.item_part), True))

# ----------------------------------------------------------------
