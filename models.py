from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.safestring import mark_safe
from PIL import Image as pil
import httplib
import os
import re
import string
import unicodedata
import cgi
import iipimage.fields
import iipimage.storage

import logging
dplog = logging.getLogger( 'digipal_debugger')

# Aspect on legacy db
class Appearance(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    text = models.CharField(max_length=128)
    sort_order = models.IntegerField()
    description = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['sort_order', 'text']
        verbose_name_plural = 'Appearance'

    def __unicode__(self):
        return u'%s' % (self.text)


# Does this need more fields?
class Feature(models.Model):
    name = models.CharField(max_length=32, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class Component(models.Model):
    name = models.CharField(max_length=128, unique=True)
    features = models.ManyToManyField(Feature, related_name='components')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class Aspect(models.Model):
    name = models.CharField(max_length=128, unique=True)
    features = models.ManyToManyField(Feature)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class OntographType(models.Model):
    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class Ontograph(models.Model):
    name = name = models.CharField(max_length=128)
    ontograph_type = models.ForeignKey(OntographType, verbose_name='type')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['ontograph_type', 'name']
        unique_together = ['name', 'ontograph_type']

    def __unicode__(self):
        return u'%s: %s' % (self.name, self.ontograph_type)


class Character(models.Model):
    name =  models.CharField(max_length=128, unique=True)
    unicode_point = models.CharField(max_length=32, unique=True)
    form = models.CharField(max_length=128)
    ontograph = models.ForeignKey(Ontograph)
    components = models.ManyToManyField(Component, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class Allograph(models.Model):
    name = models.CharField(max_length=128)
    character = models.ForeignKey(Character)
    default = models.BooleanField()
    aspects = models.ManyToManyField(Aspect, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['character__name', 'name']
        unique_together = ['name', 'character']

    def __unicode__(self):
        return u'%s, %s' % (self.character.name, self.name)

    def human_readable(self):
        if unicode(self.character) != unicode(self.name):
            return u'%s, %s' % (self.character, self.name)
        else:
            return u'%s' % (self.name)


class AllographComponent(models.Model):
    allograph = models.ForeignKey(Allograph)
    component = models.ForeignKey(Component)
    features = models.ManyToManyField(Feature, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['allograph', 'component']

    def __unicode__(self):
        return u'%s. %s' % (self.allograph, self.component)


class Script(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=128)
    allographs = models.ManyToManyField(Allograph)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class ScriptComponent(models.Model):
    script = models.ForeignKey(Script)
    component = models.ForeignKey(Component)
    features = models.ManyToManyField(Feature)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['script', 'component']

    def __unicode__(self):
        return u'%s. %s' % (self.script, self.component)


# References in legacy db
class Reference(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=128)
    name_index = models.CharField(max_length=1, blank=True, null=True)
    legacy_reference = models.CharField(max_length=128, blank=True, null=True)
    full_reference = models.TextField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'name_index']

    def __unicode__(self):
        return u'%s%s' % (self.name, self.name_index or '')


# MsOwners in legacy db
class Owner(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    date = models.CharField(max_length=128)
    evidence = models.TextField()
    rebound = models.NullBooleanField()
    annotated = models.NullBooleanField()
    dubitable = models.NullBooleanField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['date']

    def __unicode__(self):
        return u'%s: %s. %s' % (self.content_type, self.content_object,
                self.date)


# DateText in legacy db
class Date(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    date = models.CharField(max_length=128)
    sort_order = models.IntegerField(blank=True, null=True)
    weight = models.FloatField()
    band = models.IntegerField(blank=True, null=True)
    additional_band = models.IntegerField(blank=True, null=True)
    post_conquest = models.NullBooleanField()
    s_xi = models.NullBooleanField()
    min_weight = models.FloatField(blank=True, null=True)
    max_weight = models.FloatField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['sort_order']

    def __unicode__(self):
        return u'%s' % (self.date)


# CategoryText, KerCategoryText in legacy db
class Category(models.Model):
    name = models.CharField(max_length=128, unique=True)
    sort_order = models.PositiveIntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __unicode__(self):
        return u'%s' % (self.name)


# CharterTypeText in legacy db
class Format(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


# HairText in legacy db
class Hair(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    label = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['label']
        verbose_name_plural = 'Hair'

    def __unicode__(self):
        return u'%s' % (self.label)


class HistoricalItemType(models.Model):
    name = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


# CharterLanguageText in legacy db
class Language(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


# Manuscripts, Charters in legacy db
class HistoricalItem(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    historical_item_type = models.ForeignKey(HistoricalItemType)
    historical_item_format = models.ForeignKey(Format, blank=True, null=True)
    date = models.CharField(max_length=128, blank=True, null=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    categories = models.ManyToManyField(Category, blank=True, null=True)
    hair = models.ForeignKey(Hair, blank=True, null=True)
    language = models.ForeignKey(Language, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    vernacular = models.NullBooleanField()
    neumed = models.NullBooleanField()
    owners = models.ManyToManyField(Owner, blank=True, null=True)
    catalogue_number = models.CharField(max_length=128, editable=False)
    display_label = models.CharField(max_length=128, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['display_label', 'date', 'name']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def set_catalogue_number(self):
        if self.catalogue_numbers:
            self.catalogue_number = u''.join([u'%s %s ' % (cn.source,
                cn.number) for cn in self.catalogue_numbers.all()]).strip()
        else:
            self.catalogue_number = u'NOCATNO'

    def save(self, *args, **kwargs):
        self.set_catalogue_number()
        self.display_label = u'%s %s %s' % (self.historical_item_type,
                self.catalogue_number, self.name or '')
        super(HistoricalItem, self).save(*args, **kwargs)


class Source(models.Model):
    name = models.CharField(max_length=128, unique=True)
    label = models.CharField(max_length=12, unique=True, blank=True,
            null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.label or self.name)


# Manuscripts, Charters in legacy db
class CatalogueNumber(models.Model):
    historical_item = models.ForeignKey(HistoricalItem,
            related_name='catalogue_numbers')
    source = models.ForeignKey(Source)
    number = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['source', 'number']
        unique_together = ['source', 'number']

    def __unicode__(self):
        return u'%s %s' % (self.source, self.number)


# Manuscripts in legacy db
class Collation(models.Model):
    historical_item = models.ForeignKey(HistoricalItem)
    fragment = models.NullBooleanField()
    leaves = models.IntegerField(blank=True, null=True)
    front_flyleaves = models.IntegerField(blank=True, null=True)
    back_flyleaves = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['historical_item']

    def __unicode__(self):
        return u'%s' % (self.historical_item)


# Manuscripts in legacy db
class Decoration(models.Model):
    historical_item = models.ForeignKey(HistoricalItem)
    illustrated = models.NullBooleanField()
    decorated = models.NullBooleanField()
    illuminated = models.NullBooleanField()
    num_colours = models.IntegerField(blank=True, null=True)
    colours = models.CharField(max_length=256, blank=True, null=True)
    num_inks = models.IntegerField(blank=True, null=True)
    inks = models.CharField(max_length=256, blank=True, null=True)
    style = models.CharField(max_length=256, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    catalogue_references = models.CharField(max_length=256, blank=True,
            null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['historical_item']

    def __unicode__(self):
        return '%s' % (self.historical_item)


class Description(models.Model):
    historical_item = models.ForeignKey(HistoricalItem)
    source = models.ForeignKey(Source)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['historical_item']

    def __unicode__(self):
        return u'%s %s' % (self.historical_item, self.source)


# Manuscripts in legacy db
class Layout(models.Model):
    historical_item = models.ForeignKey(HistoricalItem)
    page_height = models.IntegerField(blank=True, null=True)
    page_width = models.IntegerField(blank=True, null=True)
    frame_height = models.IntegerField(blank=True, null=True)
    frame_width = models.IntegerField(blank=True, null=True)
    tramline_width = models.IntegerField(blank=True, null=True)
    lines = models.IntegerField(blank=True, null=True)
    columns = models.IntegerField(blank=True, null=True)
    on_top_line = models.NullBooleanField()
    multiple_sheet_rulling = models.NullBooleanField()
    bilinear_ruling = models.NullBooleanField()
    comments = models.TextField(blank=True, null=True)
    hair_arrangement = models.ForeignKey(Hair, blank=True, null=True)
    insular_pricking = models.NullBooleanField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['historical_item']

    def __unicode__(self):
        return u'%s' % (self.historical_item)


# MsOrigin in legacy db
class ItemOrigin(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    historical_item = models.ForeignKey(HistoricalItem)
    evidence = models.TextField(blank=True, null=True)
    dubitable = models.NullBooleanField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['historical_item']

    def __unicode__(self):
        return u'%s: %s %s' % (self.content_type, self.content_object,
                self.historical_item)


# MsOrigin in legacy db
class Archive(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    historical_item = models.ForeignKey(HistoricalItem)
    dubitable = models.NullBooleanField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['historical_item']

    def __unicode__(self):
        return u'%s: %s. %s' % (self.content_type, self.content_object,
                self.historical_item)


class Region(models.Model):
    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


# CountiesText in legacy db
class County(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Counties'

    def __unicode__(self):
        return u'%s' % (self.name)


# PlaceText in legacy db
class Place(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=256)
    eastings = models.FloatField(blank=True, null=True)
    northings = models.FloatField(blank=True, null=True)
    region = models.ForeignKey(Region, blank=True, null=True)
    current_county = models.ForeignKey(County,
            related_name='county_current',
            blank=True, null=True)
    historical_county = models.ForeignKey(County,
            related_name='county_historical',
            blank=True, null=True)
    origins = generic.GenericRelation(ItemOrigin)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)





# Libraries in legacy db
class Repository(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=256)
    short_name = models.CharField(max_length=64, blank=True, null=True)
    place = models.ForeignKey(Place)
    url = models.URLField(blank=True, null=True)
    comma = models.NullBooleanField(null=True)
    british_isles = models.NullBooleanField(null=True)
    digital_project = models.NullBooleanField(null=True)
    copyright_notice = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Repositories'

    def __unicode__(self):
        return u'%s' % (self.short_name or self.name)

    def human_readable(self):
        return u'%s, %s' % (self.place, self.name)




class CurrentItem(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    repository = models.ForeignKey(Repository)
    shelfmark = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    display_label = models.CharField(max_length=128, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['repository', 'shelfmark']
        unique_together = ['repository', 'shelfmark']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def save(self, *args, **kwargs):
        self.display_label = u'%s; %s' % (self.repository, self.shelfmark)
        super(CurrentItem, self).save(*args, **kwargs)


# OwnerText in legacy db
class Person(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=256, unique=True)
    owners = generic.GenericRelation(Owner)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class InstitutionType(models.Model):
    name = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


# PlaceText in legacy db
class Institution(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    institution_type = models.ForeignKey(InstitutionType)
    name = models.CharField(max_length=256)
    founder = models.ForeignKey(Person, related_name='person_founder',
            blank=True, null=True)
    reformer = models.ForeignKey(Person, related_name='person_reformer',
            blank=True, null=True)
    patron = models.ForeignKey(Person, related_name='person_patron',
            blank=True, null=True)
    place = models.ForeignKey(Place)
    foundation = models.CharField(max_length=128, blank=True, null=True)
    refoundation = models.CharField(max_length=128, blank=True, null=True)
    owners = generic.GenericRelation(Owner)
    origins = generic.GenericRelation(ItemOrigin)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


# Scribes on legacy db
class Scribe(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=128, unique=True)
    date = models.CharField(max_length=128, blank=True, null=True)
    scriptorium = models.ForeignKey(Institution, blank=True, null=True)
    reference = models.ManyToManyField(Reference, blank=True, null=True)    
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s. %s' % (self.name, self.date or '')


class Idiograph(models.Model):
    allograph = models.ForeignKey(Allograph)
    scribe = models.ForeignKey(Scribe, related_name="idiographs", blank=True, null=True)
    aspects = models.ManyToManyField(Aspect, blank=True, null=True)
    display_label = models.CharField(max_length=128, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['allograph']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def save(self, *args, **kwargs):
        self.display_label = u'%s. %s' % (self.allograph, self.scribe)
        super(Idiograph, self).save(*args, **kwargs)


class IdiographComponent(models.Model):
    idiograph = models.ForeignKey(Idiograph)
    component = models.ForeignKey(Component)
    features = models.ManyToManyField(Feature)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['idiograph', 'component']

    def __unicode__(self):
        return u'%s. %s' % (self.idiograph, self.component)


# MsDate in legacy db
class HistoricalItemDate(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    historical_item = models.ForeignKey(HistoricalItem)
    date = models.ForeignKey(Date)
    evidence = models.TextField()
    vernacular = models.NullBooleanField()
    addition = models.NullBooleanField()
    dubitable = models.NullBooleanField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['date']

    def __unicode__(self):
        return u'%s. %s' % (self.historical_item, self.date)


# Manuscripts and Charters in legacy db
class ItemPart(models.Model):
    historical_item = models.ForeignKey(HistoricalItem)
    current_item = models.ForeignKey(CurrentItem)
    locus = models.CharField(max_length=64, blank=True, null=True,
            default=settings.ITEM_PART_DEFAULT_LOCUS)
    display_label = models.CharField(max_length=128, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)
    pagination = models.BooleanField(blank=False, null=False, default=False)

    class Meta:
        ordering = ['display_label']
        unique_together = ['historical_item', 'current_item', 'locus']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def save(self, *args, **kwargs):
        self.display_label = u'%s, %s' % (self.current_item, self.locus or '')
        super(ItemPart, self).save(*args, **kwargs)


# LatinStyleText in legacy db
class LatinStyle(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    style = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['style']

    def __unicode__(self):
        return u'%s' % (self.style)


class Page(models.Model):
    item_part = models.ForeignKey(ItemPart, related_name='pages', null=True)
    locus = models.CharField(max_length=64)
    # r|v|vr|n=none|NULL=unspecified
    folio_side = models.CharField(max_length=4, blank=True, null=True)
    folio_number = models.CharField(max_length=8, blank=True, null=True)
    caption = models.CharField(max_length=256)
    image = models.ImageField(upload_to=settings.UPLOAD_IMAGES_URL, blank=True,
            null=True)
    iipimage = iipimage.fields.ImageField(upload_to=iipimage.storage.get_image_path, 
            blank=True, null=True, storage=iipimage.storage.image_storage)
    display_label = models.CharField(max_length=128, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['display_label']

    def __unicode__(self):
        return u'%s' % (self.display_label)
    
    def get_locus_label(self):
        ret = ''
        if self.folio_number:
            ret = ret + self.folio_number
        if self.folio_side:
            ret = ret + self.folio_side
        
        if ret == '0r':
            ret = 'face'
        if ret == '0v':
            ret = 'dorse'
        
        if ret and self.folio_number and self.folio_number != '0':
            unit = 'f.'
            if self.item_part and self.item_part.pagination:
                unit = 'p.'
            ret = unit + ret
            
        return ret

    def save(self, *args, **kwargs):
        # TODO: shouldn't this be turned into a method instead of resetting each time? 
        if (self.item_part):
            self.display_label = u'%s: %s' % (self.item_part, self.locus)
        else:
            self.display_label = u''
        super(Page, self).save(*args, **kwargs)

    def path(self):
        """Returns the path of the image on the image server. The server path
        is composed by combining repository/shelfmark/locus."""
        #raise RuntimeError('deprecated, partial URL is encapsulated by the iipimage field.')
        #dplog.debug(self.iipimage.storage.base_url)
        #print dir(self.iipimage.storage)
        return self.iipimage.name

#        repository = self.item_part.current_item.repository.short_name
#        shelfmark = self.item_part.current_item.shelfmark
#
#        if repository and shelfmark:
#            repository = normalize_string(repository)
#            shelfmark = normalize_string(shelfmark)
#            locus = normalize_string(self.locus)
#
#            path = u'%s/%s/%s/%s.%s' % (settings.IMAGE_SERVER_WEB_ROOT,
#                    repository, shelfmark, locus, settings.IMAGE_SERVER_EXT)
#
#        return path

    def dimensions(self):
        """Returns a tuple with the image width and height."""
        # TODO: review the performances of this: 
        # a http request for each image seems prohibitive.
        width = 0
        height = 0
        
        if self.iipimage:
            width, height = self.iipimage._get_image_dimensions()
        
        return int(width), int(height)
#        if self.path():
#            h = httplib.HTTPConnection(settings.IMAGE_SERVER_HOST)
#            h.request('GET', settings.IMAGE_SERVER_METADATA % \
#                    (settings.IMAGE_SERVER_PATH, self.path()))
#            response = h.getresponse()
#
#            if response:
#                message = response.read().strip()
#                matches = re.match(settings.IMAGE_SERVER_METADATA_REGEX,
#                        message)
#
#                if matches:
#                    width = matches.group(1)
#                    height = matches.group(2)
#        elif self.image:
#            width = self.image.width
#            height = self.image.height
#
#        return int(width), int(height)

    def full(self):
        """Returns the URL for the full size image."""
        ret = ''
        path = ''
        if self.iipimage:
            #path = self.iipimage.full_base_url
            path = settings.IMAGE_SERVER_FULL % \
                    (settings.IMAGE_SERVER_HOST, settings.IMAGE_SERVER_PATH,
                            self.path())
            
        return path
    
#        if self.path():
#            src = settings.IMAGE_SERVER_FULL % \
#                    (settings.IMAGE_SERVER_HOST, settings.IMAGE_SERVER_PATH,
#                            self.path())
#        elif self.image:
#            src = self.image.url
#
#        return src

    def thumbnail(self):
        """Returns HTML to display the page image as a thumbnail."""
        ret = ''
        if self.iipimage:
            src = self.iipimage.thumbnail_url(settings.IMAGE_SERVER_THUMBNAIL_HEIGHT)
            ret = mark_safe(u'<img src="%s" />' % (cgi.escape(src)))
        return ret
                
#        dplog.debug('thmb')
#        if self.path():
#            src = settings.IMAGE_SERVER_THUMBNAIL % \
#                    (settings.IMAGE_SERVER_HOST, settings.IMAGE_SERVER_PATH,
#                            self.path())
#            return mark_safe(u'<img src="%s" />' % (src))
#        elif self.image:
#            return thumbnail(self.image)

    thumbnail.short_description = 'Thumbnail'
    thumbnail.allow_tags = True

    def thumbnail_with_link(self):
        """Returns HTML to display the page image as a thumbnail with a link to
        view the image."""
        ret = ''
        ret = mark_safe(u'<a href="%s">%s</a>' % \
                (self.full(), self.thumbnail()))
        return ret
        
#        if self.path():
#            return mark_safe(u'<a href="%s">%s</a>' % \
#                    (self.full(), self.thumbnail()))
#        elif self.image:
#            return mark_safe(u'<a href="%s">%s</a>' % (self.image.url,
#                thumbnail(self.image)))

    thumbnail_with_link.short_description = 'Thumbnail'
    thumbnail_with_link.allow_tags = True

    def zoomify(self):
        """Returns the URL to view the image from the image server as zoomify
        tiles."""
        zoomify = None

        if self.path():
            zoomify = settings.IMAGE_SERVER_ZOOMIFY % \
                    (settings.IMAGE_SERVER_HOST, settings.IMAGE_SERVER_PATH,
                            self.path())
        

        return zoomify


def normalize_string(s):
    """Converts non-ascii characters into ascii, removes punctuation,
    substitutes spaces with _, and converts to lowercase."""
    s = s.strip()
    s = unicodedata.normalize('NFKD', u'%s' % s).encode('ascii', 'ignore')
    s = s.translate(string.maketrans('', ''), string.punctuation)
    s = re.sub(r'\s+', '_', s)
    s = s.lower()

    return s


# Adapted from http://djangosnippets.org/snippets/162/
# Useful for image package download http://djangosnippets.org/snippets/20/
def thumbnail(image, length=settings.MAX_THUMB_LENGTH):
    """Display thumbnail-size image of ImageField named image. Assumes images
    are not very large (i.e. no manipulation of the image is done on backend).
    Requires constant named max_thumb_length to limit longest axis"""
    max_thumb_length = length
    max_img_length = max(image.width, image.height)
    ratio = max_img_length > max_thumb_length \
            and float(max_img_length) / max_thumb_length \
            or 1
    thumb_width = image.width / ratio
    thumb_width = int(thumb_width)
    thumb_height = image.height / ratio
    thumb_height = int(thumb_height)
    url = image.url

    return mark_safe(u'<img src="%s" width="%s" height="%s"/>' % \
            (url, thumb_width, thumb_height))


# Hands in legacy db
class Hand(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    num = models.IntegerField()
    item_part = models.ForeignKey(ItemPart)
    script = models.ForeignKey(Script, blank=True, null=True)
    scribe = models.ForeignKey(Scribe, blank=True, null=True)
    assigned_date = models.ForeignKey(Date, blank=True, null=True)
    assigned_place = models.ForeignKey(Place, blank=True, null=True)
    scragg = models.CharField(max_length=6, blank=True, null=True)
    scragg_description = models.TextField(blank=True, null=True)
    em_title = models.CharField(max_length=256, blank=True, null=True)
    em_description = models.TextField(blank=True, null=True)
    mancass_description = models.TextField(blank=True, null=True)
    label = models.TextField(blank=True, null=True)
    display_note = models.TextField(blank=True, null=True)
    internal_note = models.TextField(blank=True, null=True)
    appearance = models.ForeignKey(Appearance, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    relevant = models.NullBooleanField()
    latin_only = models.NullBooleanField()
    gloss_only = models.NullBooleanField()
    membra_disjecta = models.NullBooleanField()
    num_glosses = models.IntegerField(blank=True, null=True)
    num_glossing_hands = models.IntegerField(blank=True, null=True)
    glossed_text = models.ForeignKey(Category, blank=True, null=True)
    scribble_only = models.NullBooleanField()
    imitative = models.NullBooleanField()
    latin_style = models.ForeignKey(LatinStyle, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    pages = models.ManyToManyField(Page, blank=True, null=True)
    display_label = models.CharField(max_length=128, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    def idiographs(self):
        if self.scribe:
            results = [idio.display_label for idio in self.scribe.idiographs.all()]
            return list(set(results))
        else:
            return None

    class Meta:
        ordering = ['display_label']

    # def get_idiographs(self):
        # return [idiograph for idiograph in self.scribe.idiograph_set.all()]

    def __unicode__(self):
        return u'%s' % (self.description)


class Alphabet(models.Model):
    name = models.CharField(max_length=128, unique=True)
    ontographs = models.ManyToManyField(Ontograph, blank=True, null=True)
    hands = models.ManyToManyField(Hand, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


# DateEvidence in legacy db
class DateEvidence(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    hand = models.ForeignKey(Hand)
    date = models.ForeignKey(Date, blank=True, null=True)
    date_description = models.CharField(max_length=128, blank=True, null=True)
    reference = models.ForeignKey(Reference, blank=True, null=True)
    evidence = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['date']

    def __unicode__(self):
        return u'%s. %s. %s' % (self.hand, self.date, self.date_description)


class Graph(models.Model):
    idiograph = models.ForeignKey(Idiograph)
    hand = models.ForeignKey(Hand)
    aspects = models.ManyToManyField(Aspect)
    display_label = models.CharField(max_length=256, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['idiograph']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def save(self, *args, **kwargs):
        self.display_label = u'%s. %s' % (self.idiograph, self.hand)
        super(Graph, self).save(*args, **kwargs)


class GraphComponent(models.Model):
    graph = models.ForeignKey(Graph, related_name='graph_components')
    component = models.ForeignKey(Component)
    features = models.ManyToManyField(Feature)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['graph', 'component']

    def __unicode__(self):
        return u'%s. %s' % (self.graph, self.component)


class Status(models.Model):
    name = models.CharField(max_length=32, unique=True)
    default = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Status'

    def __unicode__(self):
        return u'%s' % (self.name)


class Annotation(models.Model):
    page = models.ForeignKey(Page)
    cutout = models.CharField(max_length=256)
    status = models.ForeignKey(Status, blank=True, null=True)
    before = models.ForeignKey(Allograph, blank=True, null=True,
            related_name='allograph_before')
    graph = models.OneToOneField(Graph, blank=True, null=True)
    after = models.ForeignKey(Allograph, blank=True, null=True,
            related_name='allograph_after')
    vector_id = models.TextField()
    geo_json = models.TextField()
    display_note = models.TextField(blank=True, null=True)
    internal_note = models.TextField(blank=True, null=True)
    author = models.ForeignKey(User, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['graph', 'modified']
        unique_together = ('page', 'vector_id')

    def save(self, *args, **kwargs):
        super(Annotation, self).save(*args, **kwargs)

        json = eval(self.geo_json)
        coordinates = json['geometry']['coordinates']

        xx = list()
        yy = list()

        for c in coordinates[0]:
            xx.append(c[0])
            yy.append(c[1])

        min_x = float(min(xx))
        max_x = float(max(xx))
        min_y = float(min(yy))
        max_y = float(max(yy))

        if self.page.path():
            img_width, img_height = self.page.dimensions()
            if img_width > 0 and img_height > 0:
                img_width = float(img_width)
                img_height = float(img_height)

                left = min_x / img_width
                top = (img_height - max_y) / img_height
                width = max_x - min_x
                height = max_y - min_y
                length = settings.MAX_THUMB_LENGTH

                if width > height:
                    if width > length:
                        length = length / 1.75

                    f = length * img_width / width
                    size = 'WID=%d' % (f)
                else:
                    if height > length:
                        length = length / 1.75

                    f = length * img_height / height
                    size = 'HEI=%d' % (f)

                width = width / img_width
                height = height / img_height

                self.cutout = settings.IMAGE_SERVER_RGN % \
                        (settings.IMAGE_SERVER_HOST,
                                settings.IMAGE_SERVER_PATH, self.page.path(),
                                size, left, top, width, height)
        elif self.page.image:
            img = pil.open(self.page.image.path)
            cropped = img.crop((int(min_x),
                self.page.image.height - int(max_y), int(max_x),
                self.page.image.height - min_y))

            cropped_name = '%d.jpg' % (self.id)
            cropped_path = os.path.join(settings.ANNOTATIONS_ROOT,
                    cropped_name)

            cropped.save(cropped_path)

            self.cutout = '%s%s/%s' % (settings.MEDIA_URL,
                    settings.ANNOTATIONS_URL, cropped_name)

        super(Annotation, self).save(*args, **kwargs)

    def thumbnail(self):
        return mark_safe(u'<img alt="%s" src="%s" />' % (self.page, cgi.escape(self.cutout)))

    def thumbnail_with_link(self):
        return mark_safe(u'<a href="%s">%s</a>' % (cgi.escape(self.cutout),
            self.thumbnail()))

    thumbnail.short_description = 'Thumbnail'
    thumbnail.allow_tags = True


# PlaceEvidence in legacy db
class PlaceEvidence(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    hand = models.ForeignKey(Hand)
    place = models.ForeignKey(Place)
    place_description = models.CharField(max_length=128, blank=True, null=True)
    reference = models.ForeignKey(Reference)
    evidence = models.TextField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['place']

    def __unicode__(self):
        return u'%s. %s. %s' % (self.hand, self.place, self.reference)



# MeasurementText in legacy db
class Measurement(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    label = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['label']

    def __unicode__(self):
        return u'%s' % (self.label)


# Proportions in legacy db
class Proportion(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    hand = models.ForeignKey(Hand)
    measurement = models.ForeignKey(Measurement)
    description = models.TextField(blank=True, null=True)
    cue_height = models.FloatField()
    value = models.FloatField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['hand', 'measurement']

    def __unicode__(self):
        return u'%s. %s' % (self.hand, self.measurement)
