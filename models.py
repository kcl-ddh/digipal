from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.safestring import mark_safe
from django.db.models import Q
from PIL import Image as pil
import os
import re
import string
import unicodedata
import cgi
import iipimage.fields
import iipimage.storage

import logging
dplog = logging.getLogger( 'digipal_debugger')

def has_edit_permission(request, model):
    '''Returns True if the user of the current HTTP request
        can edit a model. False otherwise.

        model is a model class
        request is a django request
    '''
    ret = False
    if model and request and request.user:
        perm = model._meta.app_label + '.' + model._meta.get_change_permission()
        ret = request.user.has_perm(perm)

    return ret

def get_list_as_string(*parts):
    '''
        Takes a list of items and separators and returns this list as a string.
        If an item is None or converts to an empty string it won't be included in the output.

        >> get_list_as_string('1', ': ', '2', ', ', '3')
        u'1: 2, 3'

        >> get_list_as_string('1', ': ', '', ', ', '3')
        u'1: 3'
    '''
    ret = u''
    if parts:
        parts = list(parts)
        waiting_sep = u''
        while parts:
            item = parts.pop(0)
            sep = ''
            if parts: sep = parts.pop(0)
            if item is None:
                continue
            item_str = (u'%s' % item).strip()
            if not item_str:
                continue

            if len(waiting_sep) and ret.endswith(waiting_sep[0]):
                ret = ret[:-1]
            ret += waiting_sep + item_str
            waiting_sep = sep
    return ret

class MediaPermission(models.Model):
    label = models.CharField(max_length=64, blank=False, null=False,
        help_text='''An short label describing the type of permission. For internal use only.''')
    is_private = models.BooleanField(null=False, default=False,
        help_text='''If ticked the image the following message will be displayed instead of the image.''')
    display_message = models.TextField(blank=True, null=False, default='',
        help_text='''If Private is ticked the image the message will be displayed instead of the image.''')

    class Meta:
        ordering = ['label']

    def __unicode__(self):
        status = 'Public'
        if self.is_private:
            status = 'Private'
        return ur'%s [%s]' % (self.label, status)

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
    nesting_level = models.IntegerField(blank=False, null=False, default=0,
            help_text='''An ontograph can contain another ontograph of a higher level. E.g. level 3 con be made of ontographs of level 4 and above. Set 0 to prevent any nesting.''')
    sort_order = models.IntegerField(blank=False, null=False, default=0)

    class Meta:
        #ordering = ['ontograph_type', 'name']
        ordering = ['sort_order', 'ontograph_type__name', 'name']
        unique_together = ['name', 'ontograph_type']

    def __unicode__(self):
        #return u'%s: %s' % (self.name, self.ontograph_type)
        return get_list_as_string(self.name, ': ', self.ontograph_type)

class Character(models.Model):
    name =  models.CharField(max_length=128, unique=True)
    unicode_point = models.CharField(max_length=32, unique=False, blank=True, null=True)
    form = models.CharField(max_length=128)
    ontograph = models.ForeignKey(Ontograph)
    components = models.ManyToManyField(Component, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        #ordering = ['name']
        ordering = ['ontograph__sort_order', 'ontograph__ontograph_type__name', 'name']

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
        #ordering = ['character__name', 'name']
        ordering = ['character__ontograph__sort_order', 'character__ontograph__ontograph_type__name', 'name']
        unique_together = ['name', 'character']

    def __unicode__(self):
        #return u'%s, %s' % (self.character.name, self.name)
        return self.human_readable()

    def human_readable(self):
        if unicode(self.character) != unicode(self.name):
            return get_list_as_string(self.character, ', ', self.name)
        else:
            return u'%s' % (self.name)


class AllographComponent(models.Model):
    allograph = models.ForeignKey(Allograph, related_name="allograph_components")
    component = models.ForeignKey(Component)
    features = models.ManyToManyField(Feature, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['allograph', 'component']

    def __unicode__(self):
        #return u'%s. %s' % (self.allograph, self.component)
        return get_list_as_string(self.allograph, '. ', self.component)

class Text(models.Model):
    name = models.CharField(max_length=200)
    item_parts = models.ManyToManyField('ItemPart', through='TextItemPart', related_name='texts')
    legacy_id = models.IntegerField(blank=True, null=True)

    date = models.CharField(max_length=128, blank=True, null=True)
    categories = models.ManyToManyField('Category', blank=True, null=True, related_name='texts')
    languages = models.ManyToManyField('Language', blank=True, null=True, related_name='texts')
    url = models.URLField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        unique_together = ['name']
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)

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
        #return u'%s. %s' % (self.script, self.component)
        return get_list_as_string(self.script, '. ', self.component)


# References in legacy db
class Reference(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=128)
    name_index = models.CharField(max_length=1, blank=True, null=True)
    legacy_reference = models.CharField(max_length=128, blank=True, null=True, default='')
    full_reference = models.TextField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'name_index']

    def __unicode__(self):
        #return u'%s%s' % (self.name, self.name_index or '')
        return get_list_as_string(self.name, '', self.name_index)


# MsOwners in legacy db
class Owner(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)

    # GN: replaced generic relations with particular FKs.
    # because generic relations are not easy to edit in the admin.
    #
    #content_type = models.ForeignKey(ContentType)
    #object_id = models.PositiveIntegerField()
    #content_object = generic.GenericForeignKey()
    #
    institution = models.ForeignKey('Institution', blank=True, null=True
        , default=None, related_name='owners',
        help_text='Please select either an institution or a person')
    person = models.ForeignKey('Person', blank=True, null=True, default=None,
        related_name='owners',
        help_text='Please select either an institution or a person')

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

    @property
    def content_object(self):
        return self.institution or self.person

    @property
    def content_type(self):
        ret = self.content_object
        if ret:
            ret = ContentType.objects.get_for_model(ret)
        return ret

    def __unicode__(self):
        #return u'%s: %s. %s' % (self.content_type, self.content_object,
        #        self.date)
        #return get_list_as_string(self.content_type, ': ', self.content_object,
        #        '. ', self.date)
        return u'%s in %s (%s)' % (self.content_object, self.date, self.content_type)


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
    legacy_reference = models.CharField(max_length=128, blank=True, null=True, default='')
    evidence = models.CharField(max_length=255, blank=True, null=True, default='')

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
    display_label = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)
    legacy_reference = models.CharField(max_length=128, blank=True, null=True, default='')

    class Meta:
        ordering = ['display_label', 'date', 'name']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def get_descriptions(self):
        #ret = Description.objects.filter(historical_item=self).distinct()
        ret = self.description_set.all()
        return ret

    def set_catalogue_number(self):
        if self.catalogue_numbers:
            self.catalogue_number = u''.join([u'%s %s ' % (cn.source,
                cn.number) for cn in self.catalogue_numbers.all()]).strip()
        else:
            self.catalogue_number = u'NOCATNO'

    def get_part_count(self):
        return self.item_parts.all().count()
    get_part_count.short_description = 'Parts'
    get_part_count.allow_tags = False

    def save(self, *args, **kwargs):
        self.set_catalogue_number()
        #self.display_label = u'%s %s %s' % (self.historical_item_type,
        #        self.catalogue_number, self.name or '')
        self.display_label = get_list_as_string(self.historical_item_type,
                ' ', self.catalogue_number, ' ', self.name)
        super(HistoricalItem, self).save(*args, **kwargs)

    def get_display_description(self):
        ret = None
        ret_priority = 10
        is_charter = (self.historical_item_type and self.historical_item_type.name == 'charter')
        # See JIRA 95
        for desc in  self.get_descriptions():
            if desc.source.name == 'digipal':
                ret = desc
                break
            if is_charter and desc.source.name in ['sawyer'] and ret_priority > 1:
                ret = desc
                ret_priority = 1
            if is_charter and desc.source.name in ['pelteret'] and ret_priority > 2:
                ret = desc
                ret_priority = 2
            if not is_charter and desc.source.name in ['gneuss'] and ret_priority > 3:
                ret = desc
                ret_priority = 3
            if ret_priority == 10:
                ret = desc
        return ret

class Source(models.Model):
    name = models.CharField(max_length=128, unique=True)
    label = models.CharField(max_length=12, unique=True, blank=True,
            null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def get_authors_short(self):
        ''' Used by the front-end to display the source as a shorthand '''
        return self.label

    def get_authors_long(self):
        ''' Used by the front-end to display the authors of the source '''
        return self.name.title()

    def get_display_reference(self):
        ''' Used by the front-end to display the source as a reference '''
        return self.get_authors_long()

    def __unicode__(self):
        return u'%s' % (self.label or self.name)

# Manuscripts, Charters in legacy db
class CatalogueNumber(models.Model):
    historical_item = models.ForeignKey(HistoricalItem,
            related_name='catalogue_numbers', blank=True, null=True)
    text = models.ForeignKey('Text', related_name='catalogue_numbers', blank=True, null=True)
    source = models.ForeignKey(Source)
    number = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    def clean(self):
        if self.historical_item is None and self.text is None:
            from django.core.exceptions import ValidationError
            raise ValidationError('A catalogue number must refer to a Text or a Historical Item.')

    class Meta:
        ordering = ['source', 'number']
        unique_together = ['source', 'number', 'historical_item', 'text']

    def __unicode__(self):
        return get_list_as_string(self.source, ' ', self.number)


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
    historical_item = models.ForeignKey(HistoricalItem, blank=True, null=True)
    text = models.ForeignKey('Text', related_name='descriptions', blank=True, null=True)

    source = models.ForeignKey(Source)

    description = models.TextField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    summary = models.CharField(max_length=256, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['historical_item', 'text']
        unique_together = ['source', 'historical_item', 'text']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.historical_item is None and self.text is None:
            raise ValidationError('A description must refer to a Text or a Historical Item.')
        if not(self.description or self.comments or self.summary):
            raise ValidationError('A description record must have a summary, a description or comments.')

    def __unicode__(self):
        #return u'%s %s' % (self.historical_item, self.source)
        return get_list_as_string(self.historical_item, ' ', self.source)

# Manuscripts in legacy db
class Layout(models.Model):
    historical_item = models.ForeignKey(HistoricalItem, blank=True, null=True)
    item_part = models.ForeignKey('ItemPart', blank=True, null=True, related_name='layouts')
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
        ordering = ['item_part', 'historical_item']

    def __unicode__(self):
        return u'%s' % (self.item_part or self.historical_item)


# MsOrigin in legacy db
class ItemOrigin(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    historical_item = models.ForeignKey(HistoricalItem)
    evidence = models.TextField(blank=True, null=True, default='')
    dubitable = models.NullBooleanField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['historical_item']

    def __unicode__(self):
        #return u'%s: %s %s' % (self.content_type, self.content_object,
        #        self.historical_item)
        return get_list_as_string(self.content_type, ': ',
                self.content_object, ' ', self.historical_item)

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
        #return u'%s: %s. %s' % (self.content_type, self.content_object,
        #        self.historical_item)
        return get_list_as_string(self.content_type, ': ',
                self.content_object, '. ', self.historical_item)


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

class PlaceType(models.Model):
    name = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

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
    type = models.ForeignKey(PlaceType, blank=True, null=True)
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
    media_permission = models.ForeignKey(MediaPermission, null=True,
            blank=True, default=None,
            help_text='''The default permission scheme for images originating
            from this repository.<br/> The Pages can override the
            repository default permission.
            ''')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Repositories'

    def __unicode__(self):
        return u'%s' % (self.short_name or self.name)

    def human_readable(self):
        #return u'%s, %s' % (self.place, self.name)
        return get_list_as_string(self.place, ', ', self.name)

    @staticmethod
    def get_default_media_permission():
        return MediaPermission(label='Unspecified',
                               display_message=settings.UNSPECIFIED_MEDIA_PERMISSION_MESSAGE,
                               is_private=True)

    def get_media_permission(self):
        # this function will always return a mdia_permission object
        return self.media_permission or Repository.get_default_media_permission()

    def is_media_private(self):
        return self.get_media_permission().is_private


class CurrentItem(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    repository = models.ForeignKey(Repository)
    shelfmark = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    display_label = models.CharField(max_length=128)
    owners = models.ManyToManyField(Owner, blank=True, null=True, default=None, related_name='current_items')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['repository', 'shelfmark']
        unique_together = ['repository', 'shelfmark']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def save(self, *args, **kwargs):
        self.display_label = get_list_as_string(self.repository, ' ', self.shelfmark)
        super(CurrentItem, self).save(*args, **kwargs)

    def get_part_count(self):
        return self.itempart_set.all().count()
    get_part_count.short_description = 'Parts'
    get_part_count.allow_tags = False


# OwnerText in legacy db
class Person(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=256, unique=True)
    #owners = generic.GenericRelation(Owner)
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
    #owners = generic.GenericRelation(Owner)
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
    legacy_reference = models.CharField(max_length=128, blank=True, null=True, default='')

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        #return u'%s. %s' % (self.name, self.date or '')
        return get_list_as_string(self.name, '. ', self.date)


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
        #self.display_label = u'%s. %s' % (self.allograph, self.scribe)
        self.display_label = get_list_as_string(self.allograph, '. ', self.scribe)
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
        #return u'%s. %s' % (self.historical_item, self.date)
        return get_list_as_string(self.historical_item, '. ', self.date)

class ItemPartType(models.Model):
    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)

# Manuscripts and Charters in legacy db
class ItemPart(models.Model):
    historical_items = models.ManyToManyField(HistoricalItem, through='ItemPartItem', related_name='item_parts')
    current_item = models.ForeignKey(CurrentItem, blank=True, null=True, default=None)
    
    # the reference to a grouping part and the locus of this part in the group 
    group = models.ForeignKey('self', related_name='subdivisions', null=True, blank=True, help_text='the item part which contains this one')
    group_locus = models.CharField(max_length=64, blank=True, null=True, help_text='the locus of this part in the group')
    
    # This is the locus in the current item
    locus = models.CharField(max_length=64, blank=True, null=True,
            default=settings.ITEM_PART_DEFAULT_LOCUS, help_text='the location of this part in the Current Item')
    display_label = models.CharField(max_length=128)
    pagination = models.BooleanField(blank=False, null=False, default=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)
    type = models.ForeignKey(ItemPartType, null=True, blank=True)
    owners = models.ManyToManyField(Owner, blank=True, null=True)

    class Meta:
        ordering = ['display_label']
        #unique_together = ['historical_item', 'current_item', 'locus']

    def __unicode__(self):
        return u'%s' % (self.display_label)
    
    def clean(self):
        if self.group_id and self.group_id == self.id:
            from django.core.exceptions import ValidationError
            raise ValidationError('An Item Part cannot be its own group.')

    def get_image_count(self):
        return self.images.all().count()
    get_image_count.short_description = 'Images'
    get_image_count.allow_tags = False
    
    def get_part_count(self):
        return self.subdivisions.all().count()
    get_part_count.short_description = 'Parts'
    get_part_count.allow_tags = False

    def save(self, *args, **kwargs):
        #self.display_label = u'%s, %s' % (self.current_item, self.locus or '')
        if self.current_item:
            self.display_label = get_list_as_string(self.current_item, ', ', self.locus)
        else:
            label = self.historical_label
            if label:
                self.display_label = label
        super(ItemPart, self).save(*args, **kwargs)

    @property
    def historical_label(self):
        ret= ''
        # label is 'HI, locus'
        iphis = self.constitutionalities.all()
        if iphis.count():
            ret = get_list_as_string(iphis[0].historical_item, ', ', iphis[0].locus)
        else:
            # label is 'group.historical_label, group_locus'
            if self.group:
                ret = get_list_as_string(self.group.historical_label, ', ', self.group_locus)
        return ret

    @property
    def historical_item(self):
        ret= None
        try:
            ret = self.historical_items.order_by('id')[0]
        except IndexError:
            pass
        return ret

''' This is used to build the front-end URL of the item part objects
    See set_models_absolute_urls()
'''
ItemPart.webpath_key = 'Manuscripts'

# Represents the physical belonging to a whole (Item) during a period of time in history.
# A constitutionality.
class ItemPartItem(models.Model):
    historical_item = models.ForeignKey(HistoricalItem, related_name='partitions')
    item_part = models.ForeignKey(ItemPart, related_name='constitutionalities')
    locus = models.CharField(max_length=64, blank=True, null=False, default='')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['historical_item__id']
        verbose_name = 'Item Partition'

    def __unicode__(self):
        ret = u''
        
        # Type, [Shelfmark, locus], [HI.name, locus]
        if self.item_part.type:
            ret += u'%s: ' % self.item_part.type

        ret += u'%s, %s' % (self.historical_item.name, self.locus)

        if self.item_part.current_item:
            ret += u' ('
            ret += u'%s' % self.item_part.current_item.shelfmark
            if self.item_part.locus:
                ret += ', '
                ret += u'%s' % self.item_part.locus
            ret += u')'

        if self.item_part.group:
            group_label = ''
            if self.item_part.group.locus:
                group_label = '%s, %s' % (self.item_part.group.current_item.shelfmark, self.item_part.group.locus)
            else:
                ipi = ItemPartItem.objects.filter(item_part=self.item_part.group)
                if ipi.count():
                    ipi = ipi[0]
                    group_label = '%s, %s' % (ipi.historical_item.name, ipi.locus)
            if group_label:
                ret += ur' [part of %s: %s]' % (self.item_part.group.type, group_label)

        return ret

class TextItemPart(models.Model):
    item_part = models.ForeignKey('ItemPart', related_name="text_instances", blank=False, null=False)
    text = models.ForeignKey('Text', related_name="text_instances", blank=False, null=False)
    locus = models.CharField(max_length=20, blank=True, null=True)
    date = models.CharField(max_length=128, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        unique_together = ['item_part', 'text']

    def __unicode__(self):
        locus = ''
        if self.locus:
            locus = u' (%s)' % self.locus
        return u'%s in %s%s' % (self.text.name, self.item_part.display_label, locus)

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

class Image(models.Model):
    item_part = models.ForeignKey(ItemPart, related_name='images', null=True)

    locus = models.CharField(max_length=64)
    # r|v|vr|n=none|NULL=unspecified
    folio_side = models.CharField(max_length=4, blank=True, null=True)
    folio_number = models.CharField(max_length=8, blank=True, null=True)
    # no longer used, to be removed.
    caption = models.CharField(max_length=256, blank=True, null=True)

    # Legacy field, deprecated.
    # PLEASE USE IIPIMAGE INSTEAD.
    # eg. self.image.url => self.iipimage.name
    image = models.ImageField(upload_to=settings.UPLOAD_IMAGES_URL, blank=True,
            null=True)
    iipimage = iipimage.fields.ImageField(upload_to=iipimage.storage.get_image_path,
            blank=True, null=True, storage=iipimage.storage.image_storage)

    display_label = models.CharField(max_length=128)
    # optional the display label provided by the user
    custom_label = models.CharField(max_length=128, blank=True, null=True, help_text='Leave blank unless you want to customise the value of the display label field')
    
    media_permission = models.ForeignKey(MediaPermission, null=True, blank=True, default=None,
            help_text='''This field determines if the image is publicly visible and the reason if not.''')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)
    
    transcription = models.TextField(blank=True, null=True)
    internal_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['item_part__display_label', 'folio_number', 'folio_side']

    def __unicode__(self):
        ret = u''
        if self.display_label:
            ret = u'%s' % self.display_label
        else:
            ret = u'Untitled Image #%s' % self.id
            if self.iipimage:
                ret += u' (%s)' % re.sub(ur'^.*?([^/]+)/([^/.]+)[^/]+$', ur'\1, \2', self.iipimage.name)
        return ret

    def get_repository(self):
        ret = None
        if self.item_part and self.item_part.current_item and self.item_part.current_item:
            ret = self.item_part.current_item.repository
        return ret

    def get_media_permission(self):
        '''Returns the media permission of the page or inherited from repo'''
        ret = self.media_permission
        if not ret:
            repo = self.get_repository()
            if repo:
                ret = repo.get_media_permission()
        if not ret:
            ret = Repository.get_default_media_permission()
        return ret

    def is_media_private(self):
        return self.get_media_permission().is_private

    def get_media_unavailability_reason(self, user=None):
        '''Returns an empty string if the media can be viewed by the user.
           Returns a message explaining the reason otherwise.
        '''
        ret = ''

        if not self.iipimage:
            # image is missing, default message
            ret = 'The image was not found'
        else:
            if (user is None) or (not user.is_superuser):
                permission = self.get_media_permission()
                if permission.is_private:
                    ret = permission.display_message
                    if not ret:
                        ret = settings.UNSPECIFIED_MEDIA_PERMISSION_MESSAGE

        return ret
    
    @classmethod
    def filter_public_permissions(cls, image_queryset):
        '''Filter an Image queryset to keep only the images with public permissions.
            Returns the modified query set.
        '''
        ret = image_queryset.filter(Q(media_permission__is_private=False) | (Q(media_permission__is_private__isnull=True) & Q(item_part__current_item__repository__media_permission__is_private=False)))
        return ret

    def get_locus_label(self, hide_type=False):
        ''' Returns a label for the locus from the side and number fields.
            If hide_type is False, don't include p. or f. in the output.
        '''
        ret = ''
        if self.folio_number:
            ret = ret + self.folio_number
        if self.folio_side:
            ret = ret + self.folio_side

        if ret == '0r':
            ret = 'face'
        if ret == '0v':
            ret = 'dorse'

        if ret and self.folio_number and self.folio_number != '0' and not hide_type:
            unit = 'f.'
            if self.item_part and self.item_part.pagination:
                unit = 'p.'
            ret = unit + ret

        return ret

    def save(self, *args, **kwargs):
        # TODO: shouldn't this be turned into a method instead of resetting each time?
        if self.custom_label is None: self.custom_label = ''
        self.custom_label = self.custom_label.strip()
        if self.custom_label:
            self.display_label = self.custom_label
        else:
            if (self.item_part):
                self.display_label = get_list_as_string(self.item_part, ': ', self.locus)
            else:
                self.display_label = u''
        self.update_number_and_side_from_locus()
        super(Image, self).save(*args, **kwargs)

    def update_number_and_side_from_locus(self):
        ''' sets self.folio_number and self.folio_side from self.locus
            e.g. self.locus = '10r' => self.folio_number = 10, self.folio_side = 'r'
        '''
        self.folio_number = None
        self.folio_side = None
        if self.locus:
            m = re.search(ur'(\d+)', self.locus[::-1])
            if m:
                self.folio_number = m.group(1)[::-1]

            m = re.search(ur'(?:[^a-z]|^)([rv])(?:[^a-z]|$)', self.locus[::-1])
            if m:
                self.folio_side = m.group(1)[::-1]

    def path(self):
        """Returns the path of the image on the image server. The server path
        is composed by combining repository/shelfmark/locus."""
        return self.iipimage.name

    def dimensions(self):
        """Returns a tuple with the image width and height."""
        # TODO: review the performances of this:
        # a http request for each image seems prohibitive.
        width = 0
        height = 0

        if self.iipimage:
            width, height = self.iipimage._get_image_dimensions()

        return int(width), int(height)

    def full(self):
        """Returns the URL for the full size image.
           Something like http://iip-lcl:3080/iip/iipsrv.fcgi?FIF=jp2/cccc/391/602.jp2&RST=*&QLT=100&CVT=JPG
        """
        path = ''
        if self.iipimage:
            #path = self.iipimage.full_base_url
            path = settings.IMAGE_SERVER_FULL % \
                    (settings.IMAGE_SERVER_HOST, settings.IMAGE_SERVER_PATH,
                            self.path())

        return path

    def thumbnail_url(self, height=None, width=None):
        """Returns HTML to display the page image as a thumbnail."""
        ret = ''
        if width is None and height is None:
            height = settings.IMAGE_SERVER_THUMBNAIL_HEIGHT
        if self.iipimage:
            ret = self.iipimage.thumbnail_url(height, width)
        return ret

    def thumbnail(self, height=None, width=None):
        """Returns HTML to display the page image as a thumbnail."""
        ret = ''
        if self.iipimage:
            ret = mark_safe(u'<img src="%s" />' % (cgi.escape(self.thumbnail_url(height, width))))
        return ret

    thumbnail.short_description = 'Thumbnail'
    thumbnail.allow_tags = True

    def thumbnail_with_link(self, height=None, width=None):
        """Returns HTML to display the page image as a thumbnail with a link to
        view the image."""
        ret = mark_safe(u'<a href="%s">%s</a>' % \
                (self.full(), self.thumbnail(height, width)))
        return ret

    thumbnail_with_link.short_description = 'Thumbnail'
    thumbnail_with_link.allow_tags = True

    @classmethod
    def sort_query_set_by_locus(self, query_set):
        ''' Returns a query set based on the given one but with
            results sorted by item part then locus.
        '''
        # TODO: fall back for non-postgresql RDBMS
        # TODO: optimise this by caching the result in a field
        return query_set.extra(select={'fn': ur'''CASE WHEN digipal_image.folio_number~E'^\\d+$' THEN digipal_image.folio_number::integer ELSE 0 END'''}, ).order_by('item_part__display_label',  'fn', 'folio_side')

    def zoomify(self):
        """Returns the URL to view the image from the image server as zoomify
        tiles."""
        zoomify = None

        if self.path():
            zoomify = settings.IMAGE_SERVER_ZOOMIFY % \
                    (settings.IMAGE_SERVER_HOST, settings.IMAGE_SERVER_PATH,
                            self.path())


        return zoomify
''' This is used to build the front-end URL of the item part objects
    See set_models_absolute_urls()
'''
Image.webpath_key = 'Page'


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
    num = models.IntegerField(help_text='''The order of display of the Hand label. e.g. 1 for Main Hand, 2 for Gloss.''')
    item_part = models.ForeignKey(ItemPart, related_name='hands')
    script = models.ForeignKey(Script, blank=True, null=True)
    scribe = models.ForeignKey(Scribe, blank=True, null=True, related_name='hands')
    assigned_date = models.ForeignKey(Date, blank=True, null=True)
    assigned_place = models.ForeignKey(Place, blank=True, null=True)
    # This is an absolute hand (or scribe) number, so we can
    # have multiple Hand records with the same scragg.
    scragg = models.CharField(max_length=6, blank=True, null=True)
    # This is a hand (or scribe) number, relative to the ker
    # cat number for the historical item (added 04/06/2011)
    ker = models.CharField(max_length=10, blank=True, null=True)
    em_title = models.CharField(max_length=256, blank=True, null=True)
    label = models.TextField(blank=True, null=True)
    display_note = models.TextField(blank=True, null=True, help_text='An optional note that will be publicly visible on the website.')
    internal_note = models.TextField(blank=True, null=True, help_text='An optional note for internal or editorial purpose only. Will not be visible on the website.')
    appearance = models.ForeignKey(Appearance, blank=True, null=True)
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
    images = models.ManyToManyField(Image, blank=True, null=True, related_name='hands', help_text='''Select the images this hand appears in. The list of available images comes from images connected to the Item Part associated to this Hand.''')
    
    # GN: we might want to ignore display_label, it is not used on the admin 
    # form or the search or record views on the front end.
    # Use label instead. 
    display_label = models.CharField(max_length=128, editable=False)
    
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)
    
    # Imported from Brookes DB
    locus = models.CharField(max_length=300, null=True, blank=True, default='')
    # TODO: migrate to Cat Num (From Brookes DB)
    surrogates = models.CharField(max_length=50, null=True, blank=True, default='')
    # From Brookes DB
    selected_locus = models.CharField(max_length=100, null=True, blank=True, default='')
    stewart_record = models.ForeignKey('StewartRecord', null=True, blank=True, related_name='hands')

    def idiographs(self):
        if self.scribe:
            results = [idio.display_label for idio in self.scribe.idiographs.all()]
            return list(set(results))
        else:
            return None

    class Meta:
        ordering = ['item_part', 'num']

    # def get_idiographs(self):
        # return [idiograph for idiograph in self.scribe.idiograph_set.all()]

    def __unicode__(self):
        #return u'%s' % (self.description or '')
        # GN: See Jira ticket DIGIPAL-76,
        # hand.reference has moved to hand.label
        return u'%s' % (self.label or self.description or '')[0:80]

    # self.description is an alias for hd.description
    # with hd = self.HandDescription.description such that
    # hd.source.name = 'digipal'.
    def __getattr__(self, name):
        if name == 'description':
            ret = ''
            for description in self.descriptions.filter(source__name='digipal'):
                ret = description.description
        else:
            ret = super(Hand, self).__getattr__(name)
        return ret

    def __setattr__(self, name, value):
        if name == 'description':
            self.set_description('digipal', value, True)
        else:
            super(Hand, self).__setattr__(name, value)
            
    def validate_unique(self, exclude=None):
        # Unique constraint for new records only: (item_part, label)
        # Not as unique_together because we already have records violating this  
        super(Hand, self).validate_unique(exclude)
        if Hand.objects.filter(label=self.label, item_part=self.item_part).exclude(id=self.id).exists():
            from django.core.exceptions import ValidationError
            errors = {}
            errors.setdefault('label', []).append(ur'Insertion failed, another record with the same label and item part already exists')
            raise ValidationError(errors)

    def set_description(self, source_name, description=None, remove_if_empty=False):
        ''' Set the description of a hand according to a source (e.g. ker, sawyer).
            Create the source if it doesn't exist yet.
            Update description if it exists, add it otherwise.
            Null or blank description field are ignored. Unless remove_if_empty = True
        '''
        empty_value = description is None or not description.strip()
        if empty_value and not remove_if_empty: return

        # TODO: opt: cache the sources
        sources = Source.objects.filter(name=source_name)
        source = None
        if sources:
            source = sources[0]
        else:
            source = Source(name=source_name, label=source_name.upper())
            source.save()

        if empty_value:
            # remove a desc
            self.descriptions.filter(source=source).delete()
        else:
            # add or change the desc
            hand_description = None
            for hand_description in self.descriptions.all():
                if hand_description.source == source:
                    break
                hand_description = None
            if hand_description is None:
                hand_description = HandDescription(hand=self, source=source)

            hand_description.description = description
            hand_description.save()

            self.descriptions.add(hand_description)

Hand.images.through.__unicode__ = lambda self: u'%s in %s' % (self.hand.label, self.image.display_label)

class HandDescription(models.Model):
    hand = models.ForeignKey(Hand, related_name="descriptions", blank=True, null=True)
    source = models.ForeignKey(Source, related_name="hand_descriptions", blank=True, null=True)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['hand']

    def __unicode__(self):
        #return u'%s %s' % (self.historical_item, self.source)
        return get_list_as_string(self.hand, ' ', self.source)

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
    evidence = models.CharField(max_length=255, blank=True, null=True, default='')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['date']

    def __unicode__(self):
        #return u'%s. %s. %s' % (self.hand, self.date, self.date_description)
        return get_list_as_string(self.hand, '. ', self.date, '. ', self.date_description)


class Graph(models.Model):
    idiograph = models.ForeignKey(Idiograph)
    hand = models.ForeignKey(Hand, related_name='graphs')
    aspects = models.ManyToManyField(Aspect, null=True, blank=True)
    display_label = models.CharField(max_length=256, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)
    group = models.ForeignKey('Graph', related_name='parts', blank=True,
                              null=True, help_text=u'Select a graph that contains this one')

    class Meta:
        ordering = ['idiograph']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def save(self, *args, **kwargs):
        #self.display_label = u'%s. %s' % (self.idiograph, self.hand)
        self.display_label = get_list_as_string(self.idiograph, '. ', self.hand)
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
    # TODO: to remove
    #page = models.ForeignKey(Image, related_name='to_be_removed')
    image = models.ForeignKey(Image, null=True, blank=False)
    cutout = models.CharField(max_length=256)
    status = models.ForeignKey(Status, blank=True, null=True)
    before = models.ForeignKey(Allograph, blank=True, null=True,
            related_name='allograph_before')
    graph = models.OneToOneField(Graph, blank=True, null=True)
    after = models.ForeignKey(Allograph, blank=True, null=True,
            related_name='allograph_after')
    vector_id = models.TextField()
    geo_json = models.TextField()
    display_note = models.TextField(blank=True, null=True, help_text='An optional note that will be publicly visible on the website.')
    internal_note = models.TextField(blank=True, null=True, help_text='An optional note for internal or editorial purpose only. Will not be visible on the website.')
    author = models.ForeignKey(User, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True,
            editable=False)

    class Meta:
        ordering = ['graph', 'modified']
        unique_together = ('image', 'vector_id')

    def get_coordinates(self, geo_json=None):
        ''' Returns the coordinates of the graph rectangle
            E.g. ((602, 56), (998, 184))
        '''
        import json
        if geo_json is None: geo_json = self.geo_json

        # See JIRA-229, some old geo_json format are not standard JSON
        # and cause trouble with the deserialiser (json.loads()).
        # The property names are surrounded by single quotes
        # instead of double quotes.
        # simplistic conversion but in our case it works well
        # e.g. {'geometry': {'type': 'Polygon', 'coordinates':
        #     Returns {"geometry": {"type": "Polygon", "coordinates":
        geo_json = geo_json.replace('\'', '"')

        ret = json.loads(geo_json)
        # TODO: test if this exists!
        ret = ret['geometry']['coordinates'][0]
        ret = (
                (min([c[0] for c in ret]),
                min([c[1] for c in ret])),
                (max([c[0] for c in ret]),
                max([c[1] for c in ret]))
            )
        return ret

    def set_graph_group(self):
        # if the graph is contained within another
        # this function will set self.group to that other graph.
        group_id = None
        min_dist = 1e6

        coord = self.get_coordinates()

        # Assumptions made:
        #    1. all regions are rectangles, no more complex shapes.
        #    2. nested graphs are saved after their parent graph.
        if self.graph:
            level = self.graph.idiograph.allograph.character.ontograph.nesting_level
            if level > 1:
                lvl_field = 'graph__idiograph__allograph__character__ontograph__nesting_level';
                for a in Annotation.objects.filter(image=self.image, graph__idiograph__allograph__character__ontograph__nesting_level__range=(1, level - 1)).values('graph_id', 'geo_json', lvl_field):
                    a_coord = self.get_coordinates(a['geo_json'])
                    if coord[0][0] >= a_coord[0][0] and \
                        coord[0][1] >= a_coord[0][1] and \
                        coord[1][0] <= a_coord[1][0] and \
                        coord[1][1] <= a_coord[1][1]:
                        dist = abs(coord[0][0] - a_coord[0][0])
                        if dist < min_dist:
                            group_id = a['graph_id']
                            min_dist = dist

            self.graph.group_id = group_id
            self.graph.save()

    def save(self, *args, **kwargs):
        super(Annotation, self).save(*args, **kwargs)

        # TODO: suspicious call to eval. Should call json.loads() instead - GN
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

        if self.image.path():
            img_width, img_height = self.image.dimensions()
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
                                settings.IMAGE_SERVER_PATH, self.image.path(),
                                size, left, top, width, height)
        elif self.image.image:
            img = pil.open(self.image.image.path)
            cropped = img.crop((int(min_x),
                self.image.image.height - int(max_y), int(max_x),
                self.image.image.height - min_y))

            cropped_name = '%d.jpg' % (self.id)
            cropped_path = os.path.join(settings.ANNOTATIONS_ROOT,
                    cropped_name)

            cropped.save(cropped_path)

            self.cutout = '%s%s/%s' % (settings.MEDIA_URL,
                    settings.ANNOTATIONS_URL, cropped_name)

        super(Annotation, self).save(*args, **kwargs)

    def get_cutout_url(self):
        ''' Returns the URL of the cutout.
            Call this function instead of self.cutout, see JIRA 149.
        '''
        # graft the query string of self.cutout to self.image.thumbnail_url
        # See JIRA 149: Annotation cutouts should be stored as coordinates only not as a full URL
        #return mark_safe(u'<img alt="%s" src="%s" />' % (self.image, cgi.escape(self.cutout)))
        #from utils import update_query_string
        cutout_qs = re.sub(ur'^(.*)\?(.*)$', ur'\2', self.cutout)
        # This technique doesn't work because of the encoding:
        # cutout_url = update_query_string(self.image.thumbnail_url(), cutout_qs)
        # Just concatenate things together instead
        image_url = re.sub(ur'^(.*)\?(.*)$', ur'\1', self.image.thumbnail_url())
        return u'%s?%s' % (image_url, cutout_qs)

    def thumbnail(self):
        return mark_safe(u'<img alt="%s" src="%s" />' % (self.graph, self.get_cutout_url()))

    def thumbnail_with_link(self):
        return mark_safe(u'<a href="%s">%s</a>' % (cgi.escape(self.get_cutout_url()),
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
        #return u'%s. %s. %s' % (self.hand, self.place, self.reference)
        return get_list_as_string(self.hand, '. ', self.place, '. ', self.reference)


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
        #return u'%s. %s' % (self.hand, self.measurement)
        return get_list_as_string(self.hand, '. ', self.measurement)

# Import of Stewart's database
class StewartRecord(models.Model):
    scragg = models.CharField(max_length=300, null=True, blank=True, default='')
    repository = models.CharField(max_length=300, null=True, blank=True, default='')
    shelf_mark = models.CharField(max_length=300, null=True, blank=True, default='')
    stokes_db = models.CharField(max_length=300, null=True, blank=True, default='')
    fols = models.CharField(max_length=300, null=True, blank=True, default='')
    gneuss = models.CharField(max_length=300, null=True, blank=True, default='')
    ker = models.CharField(max_length=300, null=True, blank=True, default='')
    sp = models.CharField(max_length=300, null=True, blank=True, default='')
    ker_hand = models.CharField(max_length=300, null=True, blank=True, default='')
    locus = models.CharField(max_length=300, null=True, blank=True, default='')
    selected = models.CharField(max_length=300, null=True, blank=True, default='')
    adate = models.CharField(max_length=300, null=True, blank=True, default='')
    location = models.CharField(max_length=300, null=True, blank=True, default='')
    surrogates = models.CharField(max_length=300, null=True, blank=True, default='')
    contents = models.CharField(max_length=500, null=True, blank=True, default='')
    notes = models.CharField(max_length=600, null=True, blank=True, default='')
    em = models.CharField(max_length=800, null=True, blank=True, default='')
    glosses = models.CharField(max_length=300, null=True, blank=True, default='')
    minor = models.CharField(max_length=300, null=True, blank=True, default='')
    charter = models.CharField(max_length=300, null=True, blank=True, default='')
    cartulary = models.CharField(max_length=300, null=True, blank=True, default='')
    eel = models.CharField(max_length=1000, null=True, blank=True, default='')
    import_messages = models.TextField(null=True, blank=True, default='')

    class Meta:
        ordering = ['scragg']

    def __unicode__(self):
        return ur'Scr%s K%s G%s D%s SP %s' % (self.scragg, self.ker, self.gneuss, self.stokes_db, self.sp)

    def get_ids(self):
        ret = []
        if self.scragg: ret.append(u'Scr. %s' % self.scragg)
        if self.gneuss: ret.append(u'G. %s' % self.gneuss)
        if self.ker:
            ker = u'K. %s' % self.ker
            if self.ker_hand:
                ker += '.%s' % self.ker_hand
            ret.append(ker)
        if self.sp: ret.append(u'SP. %s' % self.sp)
        if self.stokes_db: ret.append(u'L. %s' % self.stokes_db)
        return ', '.join(ret)

    def import_field(self, src_field, dst_obj, dst_field, append=False):
        ret = ''
        def normalise_value(value):
            if value is None: value = ''
            return (u'%s' % value).strip()

        src_value = normalise_value(getattr(self, src_field, ''))
        dst_value = normalise_value(getattr(dst_obj, dst_field, ''))

        if src_value:
            if (not append) or (dst_value.find(src_value) == -1):
                if (not append) and (dst_value and src_value != dst_value):
                    ret = u'Different values: #%s.%s = "%s" <> %s.#%s.%s = "%s"' % (self.id, src_field, src_value, dst_obj.__class__.__name__, dst_obj.id, dst_field, dst_value)

                if not ret:
                    if append:
                        src_value = dst_value + '\n' + src_value
                    setattr(dst_obj, dst_field, src_value)
                    dst_obj.save()

        if ret: ret += '\n'

        return ret

    @classmethod
    def get_sources(self):
        sources = getattr(self.__class__, 'sources', {})
        if not sources:
            sources = {}
            for source in Source.objects.all():
                sources[source.name] = source

            self.__class__.sources = sources

        return self.sources

    def import_related_object(self, hand, related_name, related_model, related_label_field, value):
        ret = ''
        related_object = getattr(hand, related_name, None)
        if related_object:
            existing_value = getattr(related_object, related_label_field)
            if existing_value != value:
                ret = u'Different values for %s: already set to "%s", cannot overwrite it with "%s" (Brookes DB)' % (related_name, existing_value, value)
            #else:
                #ret = u'Already set'
        else:
            # does it exists?
            query = {related_label_field+'__iexact': value.lower().strip()}
            related_objects = related_model.objects.filter(**query)
            if related_objects.count():
                # yes, just find it
                related_object = related_objects[0]
                #ret = u'Found %s' % related_object.id
            else:
                # no, then create it
                # but only if it does not have a ? at the end
                if value.strip()[-1] == '?':
                    ret = 'Did not set uncertain value for %s field: "%s" (Brookes DB)' % (related_name, value)
                    if hand.internal_note:
                        hand.internal_note += '\n' + ret
                    else:
                        hand.internal_note = ret
                else:
                    query = {related_label_field: value.strip()}
                    related_object = related_model(**query)
                    if related_model == Date:
                        related_object.weight = 0.0
                    related_object.save()
                    #ret = u'Created %s' % related_object.id
            # create link
            setattr(hand, related_name, related_object)
            hand.save()

        if ret:
            if hand.internal_note:
                hand.internal_note += '\n' + ret
            else:
                hand.internal_note = ret
            hand.save()

        return ret

    def import_steward_record(self, single_hand=None):
        '''
            TODO: transfer (Scragg_Description, EM_Description)

            [DONE] ker -> ItemPart_HistoricalItem_CatalogueNumbers(Source.name='ker')
            [DONE] sp ->

            # hand number
            [DONE] scragg -> hand.scragg
            [DONE] Locus -> hand.+locus
            [DONE] Selected -> Page (Use this to generate a new Page record)
            [DONE] Notes      Hand.InternalNote

            [DONE] * ker_hand -> Missing. Use description + Source model. [this is only a hand number, why saving this as a desc?]
            [DONE] Contents      Scragg_Description
            [DONE] EM      Hand.EM_Description (Use description + Source model.)
            [DONE] EEL      MISSING. Use Description + Source model
            # Format is too messy to be imported into the catalogue num
            # we import it into the surrogates field and add a filter

            [DONE~] Surrogates      Use Source Model

            Date      Hand.AssignedDate
            Location      Hand.AssignedPlace

            [DONE] Glosses      Hand.GlossOnly
            [DONE] Minor      Hand.ScribbleOnly
        '''
        if single_hand:
            hands = [single_hand]
        else:
            hands = self.hands.all()
        if not hands:
            return

        from datetime import datetime
        now = datetime.now()

        for hand in hands:
            messages = u'[%s] IMPORT record #%s into hand #%s.\n' % (now.strftime('%d-%m-%Y %H:%M:%S') , self.id, hand.id)

            # 1. Simple TEXT fields

            # hand number
            messages += self.import_field('scragg', hand, 'scragg')
            messages += self.import_field('ker_hand', hand, 'ker')

            messages += self.import_field('locus', hand, 'locus')
            messages += self.import_field('selected', hand, 'selected_locus')
            messages += self.import_field('notes', hand, 'internal_note', True)

            if hand.gloss_only is None and self.glosses == 'Yes':
                hand.gloss_only = True
            if hand.scribble_only is None and self.minor == 'Yes':
                hand.scribble_only = True

            # This should be imported as a cat num but format is too inconsistent
            # EEMF, ASMMF, BL Fiche
            messages += self.import_field('surrogates', hand, 'surrogates')

            # 2. Description fields

            hand.set_description('scragg', self.contents)
            hand.set_description('eel', self.eel)
            hand.set_description('em1060-1220', self.em)

            # 3. Related objects

            # 3470
            # TODO: import by creating a new date?
            ##messages += self.import_field('adate', hand, 'assigned_date')
            # TODO: import by creating a new place?
            if self.location:
                messages += self.import_related_object(hand, 'assigned_place', Place, 'name', self.location)
            if self.adate:
                messages += self.import_related_object(hand, 'assigned_date', Date, 'date', re.sub(ur'\s*(?:' + u'\xd7' + ur'|x)\s*', u'\xd7', self.adate))

            # 4. Catalogue numbers
            # Ker, S/P (NOT Scragg, b/c its a hand number)
            if self.ker or self.sp:
                def add_catalogue_number(historical_item, source, number):
                    if CatalogueNumber.objects.filter(source=source, number=number).count() == 0:
                        historical_item.catalogue_numbers.add(CatalogueNumber(source=source, number=number))

                sources = self.get_sources()

                cat_nums = {}

                historical_item = hand.item_part.historical_item
                for cat_num in historical_item.catalogue_numbers.all():
                    cat_nums[cat_num.source.name] = cat_num.number

                if self.ker and 'ker' not in cat_nums:
                    add_catalogue_number(historical_item, sources['ker'], self.ker)

                if self.sp:
                    source_dp = 'sawyer'
                    document_id = self.sp
                    document_id_p = re.sub('(?i)^\s*p\s*(\d+)', r'\1', document_id)
                    if document_id_p != document_id:
                        document_id = document_id_p
                        source_dp = 'pelteret'

                    if source_dp not in cat_nums:
                        add_catalogue_number(historical_item, sources[source_dp], document_id)

            self.import_messages += messages
            self.save()

class RequestLog(models.Model):
    request = models.CharField(max_length=300, null=True, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    result_count = models.IntegerField(blank=False, null=False, default=0)

    @classmethod
    def save_request(cls, request, count=0):
        last = None
        # Don't log two consecutive queries if they have the same count
        # TODO: improve this algorithm, it is to naive
        if count > 0:
            try:
                last = cls.objects.latest('id')
            except cls.DoesNotExist:
                pass
        if not last or last.result_count != count:
            path = request.build_absolute_uri()
            rl = cls(result_count=count, request=path)
            rl.save()

# Assign get_absolute_url() and get_admin_url() for all models 
# get_absolute_url() returns /digipal/MODEL_PLURAL/ID
# E.g. /digipal/scribes/101
def set_additional_models_methods():
    
    def model_get_absolute_url(self):
        from utils import plural
        # get custom label if defined in _meta, otehrwise stick to module name
        webpath_key = getattr(self, 'webpath_key', plural(self._meta.module_name, 2))
        ret = '/%s/%s/%s/' % (self._meta.app_label, webpath_key.lower(), self.id)
        return ret

    def model_get_admin_url(self):
        # get_admin_url
        from django.core.urlresolvers import reverse
        info = (self._meta.app_label, self._meta.module_name)
        ret = reverse('admin:%s_%s_change' % info, args=(self.pk,))
        return ret
            
    for attribute in globals().values():
        # Among all the symbols accessible here, filter the Model defined in this module
        if isinstance(attribute, type) and issubclass(attribute, models.Model) and attribute.__module__ == __name__:
            attribute.get_absolute_url = model_get_absolute_url
            attribute.get_admin_url = model_get_admin_url


set_additional_models_methods()
