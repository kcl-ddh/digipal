from django.db import models
from mezzanine.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
#from django.contrib.contenttypes import generic
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.safestring import mark_safe
from django.db.models import Q
from PIL import Image as pil
import os
import re
import string
import unicodedata
import cgi
import iipfield.fields
import iipfield.storage
from django.utils.html import conditional_escape, escape
from tinymce.models import HTMLField
from django.db import transaction
from mezzanine.generic.fields import KeywordsField
import logging
from django.utils.text import slugify
import utils as dputils
from digipal.utils import sorted_natural
from collections import OrderedDict

from patches import admin_patches, whoosh_patches
# need to call it here because get_image_path() is called in the model


def has_edit_permission(request, model):
    '''Returns True if the user of the current HTTP request can edit a model.
        False otherwise.

        model is a model class
        request is a django request or None (assumed public user)
    '''
    ret = False
    if request and request.user:
        ret = has_user_edit_permission(request.user, model)

    return ret


def has_user_edit_permission(user, model):
    '''Returns True if the user can edit a model. False otherwise.

        model is a model class
        user is a django User instance or None (assumed public user)
    '''
    ret = False
    if model and user:
        from django.contrib.auth import get_permission_codename
        perm = model._meta.app_label + '.' + \
            get_permission_codename('change', model._meta)
        ret = user.has_perm(perm)

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
            if parts:
                sep = parts.pop(0)
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


class NameModel(models.Model):
    '''
        An abstract model that contains just a name, a created and modified field.
    '''
    name = models.CharField(max_length=100, unique=True,
                            blank=False, null=False)
    slug = models.SlugField(max_length=100, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(
        auto_now=True, editable=False)

    class Meta:
        abstract = True
        ordering = ['name']

    def save(self, *args, **kwargs):
        self.slug = (self.slug or '').strip()
        if not self.slug:
            self.slug = slugify(unicode(self.name))
        super(NameModel, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % (self.name)


class MediaPermission(models.Model):

    PERM_PRIVATE = 100
    PERM_THUMB_ONLY = 200
    PERM_PUBLIC = 300
    PERM_CHOICES = (
        (PERM_PRIVATE, 'Private'),
        (PERM_THUMB_ONLY, 'Thumbnail Only'),
        (PERM_PUBLIC, 'Full Resolution'),
    )

    label = models.CharField(max_length=64, blank=False, null=False,
                             help_text='''A short label describing the type of permission. For internal use only.''')

    permission = models.IntegerField(
        null=False, default=PERM_PRIVATE, choices=PERM_CHOICES)

    display_message = HTMLField(blank=True, null=False, default='',
                                help_text='''This message will be displayed when the image is not available to the user.''')

    class Meta:
        ordering = ['label']

    @classmethod
    def get_new_default(cls):
        ret = cls(display_message=settings.UNSPECIFIED_MEDIA_PERMISSION_MESSAGE,
                  label='Unspecified',
                  permission=cls.PERM_PRIVATE)
        return ret

    def get_permission_label(self):
        ret = u''
        for choice in self.PERM_CHOICES:
            if choice[0] == self.permission:
                ret = choice[1]
                break
        return ret

    def __unicode__(self):
        return ur'%s [%s]' % (self.label, self.get_permission_label())

# Aspect on legacy db


class Appearance(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    text = models.CharField(max_length=128)
    sort_order = models.IntegerField()
    description = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
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
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class Component(models.Model):
    name = models.CharField(max_length=128, unique=True)
    features = models.ManyToManyField(
        Feature, related_name='components', through='ComponentFeature')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class ComponentFeature(models.Model):
    component = models.ForeignKey('Component', blank=False, null=False)
    feature = models.ForeignKey('Feature', blank=False, null=False)
    set_by_default = models.BooleanField(null=False, default=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(
        auto_now=True, editable=False)

    class Meta:
        unique_together = ['component', 'feature']
        db_table = 'digipal_component_features'
        ordering = ['component__name', 'feature__name']

    def __unicode__(self):
        ret = u''
        if self.component:
            ret += self.component.name
        ret += u' - '
        if self.feature:
            ret += self.feature.name
        return ret


class Aspect(models.Model):
    name = models.CharField(max_length=128, unique=True)
    features = models.ManyToManyField(Feature)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class OntographType(models.Model):
    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class Ontograph(models.Model):
    name = name = models.CharField(max_length=128)
    ontograph_type = models.ForeignKey(OntographType, verbose_name='type')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)
    nesting_level = models.IntegerField(blank=False, null=False, default=0,
                                        help_text='''An ontograph can contain another ontograph of a higher level. E.g. level 3 con be made of ontographs of level 4 and above. Set 0 to prevent any nesting.''')
    sort_order = models.IntegerField(blank=False, null=False, default=0)

    @staticmethod
    def get_definition():
        return u'''?Graphical abstraction of a character. It is formless and shapeless.'''

    class Meta:
        #ordering = ['ontograph_type', 'name']
        ordering = ['sort_order', 'ontograph_type__name', 'name']
        unique_together = ['name', 'ontograph_type']

    def __unicode__(self):
        # return u'%s: %s' % (self.name, self.ontograph_type)
        return get_list_as_string(self.name, ': ', self.ontograph_type)


class CharacterForm(models.Model):
    name = models.CharField(max_length=128, unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Character(models.Model):
    name = models.CharField(max_length=128, unique=True)
    unicode_point = models.CharField(
        max_length=32, unique=False, blank=True, null=True)
    form = models.ForeignKey(CharacterForm, blank=False, null=False)
    ontograph = models.ForeignKey(Ontograph)
    components = models.ManyToManyField(Component, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    @staticmethod
    def get_definition():
        return u'''Similar to sign; more or less a set of letters in the abstract sense but also including punctuation and abbreviations'''

    class Meta:
        #ordering = ['name']
        ordering = ['ontograph__sort_order',
                    'ontograph__ontograph_type__name', 'name']

    def __unicode__(self):
        return u'%s' % (self.name)


class Allograph(models.Model):
    name = models.CharField(max_length=128)
    character = models.ForeignKey(Character)
    default = models.BooleanField(default=False)
    aspects = models.ManyToManyField(Aspect, blank=True)
    hidden = models.BooleanField(
        default=False, help_text=u'''If ticked the public users won't see this allograph on the web site.''')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    @staticmethod
    def get_definition():
        return u'''A recognised variant form of the same character (e.g. a and a, or Caroline and Insular)'''

    class Meta:
        #ordering = ['character__name', 'name']
        ordering = ['character__ontograph__sort_order',
                    'character__ontograph__ontograph_type__name', 'name']
        unique_together = ['name', 'character']

    def __unicode__(self):
        # return u'%s, %s' % (self.character.name, self.name)
        return self.human_readable()

    def human_readable(self):
        if unicode(self.character) != unicode(self.name):
            return get_list_as_string(self.character, ', ', self.name)
        else:
            return u'%s' % (self.name)


class AllographComponent(models.Model):
    allograph = models.ForeignKey(
        Allograph, related_name="allograph_components")
    component = models.ForeignKey(Component)
    features = models.ManyToManyField(Feature, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['allograph', 'component']

    def __unicode__(self):
        # return u'%s. %s' % (self.allograph, self.component)
        return get_list_as_string(self.allograph, '. ', self.component)


class ModelWithDate(models.Model):
    date = models.CharField(max_length=128, blank=True,
                            null=True, help_text='Date of the Historical Item')
    date_sort = models.CharField(max_length=128, blank=True, null=True,
                                 help_text='Optional date used for sorting HI or visualising HI on timeline. It is interpretable and bounded: e.g. 1200 x 1229.')

    class Meta:
        abstract = True

    def is_date_precise(self):
        ret = False
        date = self.get_date_sort()
        # if re.search(ur'\d{3,4}$', date) and not re.search(ur'(?i)circa',
        # date) and not re.search(ur'(?i)\bx\b', date) and not
        # re.search(ur'(?i)\bc\b', date):
        if re.match(ur'\d{1,2}\s+\w+\s+\d{4}$', date) and not re.search(ur'(?i)circa',
                                                                        date) and not re.search(ur'(?i)\bx\b', date) and not re.search(ur'(?i)\bc\b', date):
            ret = True
        return ret

    def get_date_sort_range_diff(self):
        ret = 1000
        date = self.get_date_sort()
        if date:
            rng = dputils.get_range_from_date(date)
            diff = abs(rng[0] - rng[1])
            ret = diff

        return ret

    def get_date_sort(self):
        return self.date_sort or self.date


class Text(ModelWithDate):
    name = models.CharField(max_length=200)
    item_parts = models.ManyToManyField(
        'ItemPart', through='TextItemPart', related_name='texts')
    legacy_id = models.IntegerField(blank=True, null=True)

    categories = models.ManyToManyField(
        'Category', blank=True, related_name='texts')
    languages = models.ManyToManyField(
        'Language', blank=True, related_name='texts')
    url = models.URLField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        verbose_name = 'Text Info'
        verbose_name_plural = 'Text Info'
        unique_together = ['name']
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class Script(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=128)
    allographs = models.ManyToManyField(Allograph)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
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
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['script', 'component']

    def __unicode__(self):
        # return u'%s. %s' % (self.script, self.component)
        return get_list_as_string(self.script, '. ', self.component)


# References in legacy db
class Reference(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=128)
    name_index = models.CharField(max_length=1, blank=True, null=True)
    legacy_reference = models.CharField(
        max_length=128, blank=True, null=True, default='')
    full_reference = HTMLField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'name_index']

    def __unicode__(self):
        # return u'%s%s' % (self.name, self.name_index or '')
        return get_list_as_string(self.name, '', self.name_index)


# MsOwners in legacy db
# GN: this is actually an Ownership table
class Owner(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)

    # deprecated, use repository
    institution = models.ForeignKey('Institution', blank=True, null=True, default=None, related_name='owners',
                                    help_text='Please select either an institution or a person. Deprecated, please use `Repository` instead.')
    # deprecated, use repository
    person = models.ForeignKey('Person', blank=True, null=True, default=None,
                               related_name='owners',
                               help_text='Please select either an institution or a person. Deprecated, please use `Repository` instead.')

    repository = models.ForeignKey('Repository', blank=True, null=True, default=None, related_name='owners',
                                   help_text='`Repository` actually represents the institution, person or library owning the item.')

    date = models.CharField(max_length=128)
    display_label = models.CharField(
        max_length=250, blank=True, null=False, default='')
    evidence = models.TextField()
    rebound = models.NullBooleanField()
    annotated = models.NullBooleanField()
    dubitable = models.NullBooleanField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(
        auto_now=True, editable=False)

    class Meta:
        ordering = ['date']

    #objects = OwnerManager()

    @property
    def content_object(self):
        return self.institution or self.person or self.repository

    @property
    def content_type(self):
        ret = self.content_object
        if ret:
            ret = ContentType.objects.get_for_model(ret)
        return ret

    def get_owned_item(self):
        ret = None
        if self.pk:
            ret = self.itempart_set.first() or self.historicalitem_set.first(
            ) or self.current_items.first()
        return ret

    def save(self, *args, **kwargs):
        self.display_label = self.compute_display_label()
        super(Owner, self).save(*args, **kwargs)

    def compute_display_label(self):
        ret = u''

        item = self.get_owned_item()
        if item:
            ret += u'\'%s\'' % item
        else:
            ret += u'?'

        ret += u' owned by '

        ret += u' \'%s\' ' % self.content_object

        if self.date:
            ret += u' in \'%s\'' % self.date

        return ret

    def __unicode__(self):
        return self.display_label

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
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)
    legacy_reference = models.CharField(
        max_length=128, blank=True, null=True, default='')
    evidence = models.CharField(
        max_length=255, blank=True, null=True, default='')

    class Meta:
        ordering = ['sort_order']

    def __unicode__(self):
        return u'%s' % (self.date)


# CategoryText, KerCategoryText in legacy db
class Category(models.Model):
    name = models.CharField(max_length=128, unique=True)
    sort_order = models.PositiveIntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
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
    modified = models.DateTimeField(auto_now=True,
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
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['label']
        verbose_name_plural = 'Hair'

    def __unicode__(self):
        return u'%s' % (self.label)


class HistoricalItemType(models.Model):
    name = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
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
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


# Manuscripts, Charters in legacy db


class HistoricalItem(ModelWithDate):
    legacy_id = models.IntegerField(blank=True, null=True)
    historical_item_type = models.ForeignKey(HistoricalItemType)
    historical_item_format = models.ForeignKey(Format, blank=True, null=True)

    name = models.CharField(max_length=256, blank=True, null=True)
    categories = models.ManyToManyField(Category, blank=True)
    hair = models.ForeignKey(Hair, blank=True, null=True)
    language = models.ForeignKey(Language, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    vernacular = models.NullBooleanField()
    neumed = models.NullBooleanField()
    owners = models.ManyToManyField(Owner, blank=True)
    catalogue_number = models.CharField(max_length=128, editable=False)
    display_label = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)
    legacy_reference = models.CharField(
        max_length=128, blank=True, null=True, default='')

    class Meta:
        ordering = ['display_label', 'date', 'name']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def get_first_text(self):
        ret = None
        ip = self.item_parts.first()
        if ip:
            ret = ip.texts.first()
        return ret

    def get_descriptions(self):
        ret = self.description_set.all().order_by('source__priority')
        return ret

    def set_catalogue_number(self):
        cn = u''
        if self.pk:
            cns = self.catalogue_numbers.all()
            if cns:
                cn = u''.join([u'%s %s ' % (cn.source, cn.number)
                               for cn in cns]).strip()
        self.catalogue_number = cn

    def get_part_count(self):
        return self.item_parts.all().count()
    get_part_count.short_description = 'Parts'
    get_part_count.allow_tags = False

    def save(self, *args, **kwargs):
        self.set_catalogue_number()
        # self.display_label = u'%s %s %s' % (self.historical_item_type,
        #        self.catalogue_number, self.name or '')
        self.display_label = get_list_as_string(self.historical_item_type,
                                                ' ', self.catalogue_number, ' ', self.name)
        super(HistoricalItem, self).save(*args, **kwargs)

    def get_display_description(self):
        ret = None
        descs = self.get_descriptions()
        if descs.count():
            ret = descs[0]

        return ret

    @classmethod
    def get_or_create(cls, name, cat_num):
        ret = None
        name = name.strip()
        cat_num = CatalogueNumber.get_or_create(cat_num.strip())

        if name or cat_num:
            his = HistoricalItem.objects.all()
            if name:
                his = his.filter(name__iexact=name)
            if cat_num:
                his = his.filter(catalogue_number=cat_num)
            if his.count() == 1:
                ret = his[0]
            if his.count() == 0:
                ret = HistoricalItem(
                    name=name, historical_item_type=HistoricalItemType.objects.first())
                ret.save()
                if cat_num:
                    ret.catalogue_numbers.add(cat_num)

        return ret


class Source(models.Model):
    name = models.CharField(max_length=128, unique=True,
                            help_text='Full reference of this source (e.g. British Library)')
    label = models.CharField(max_length=30, unique=True, blank=True,
                             null=True, help_text='A shorthand for the reference (e.g. BL)')
    label_slug = models.SlugField(max_length=30, blank=True, null=True)
    label_styled = models.CharField(max_length=30, blank=True, null=True,
                                    help_text='Styled version of the label, text between _underscores_ will be italicised')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)
    priority = models.IntegerField(blank=False, null=False, default=0,
                                   help_text=u'''Lower number has a higher display priority on the web site. 0 is top, 1 second, then 2, etc.''')

    class Meta:
        ordering = ['name']

    def get_authors_short(self):
        ''' Used by the front-end to display the source as a shorthand '''
        return self.label

    def get_authors_long(self):
        ''' Used by the front-end to display the authors of the source '''
        return self.name

    def get_display_reference(self):
        ''' Used by the front-end to display the source as a reference '''
        return self.get_authors_long()

    def __unicode__(self):
        return u'%s' % (self.label or self.name)

    @classmethod
    def get_all_sources(cls):
        '''Return all sources (load them the first time then cache them)'''
        ret = getattr(cls, '_sources', None)
        if ret is None:
            ret = cls.objects.all().order_by('id')
            cls._sources = ret

        return ret

    @classmethod
    def get_source_from_keyword(cls, keyword, none_if_not_found=False):
        '''Returns a source from a keyword matching part of the name or the label.
           e.g. Source.get_source_from_keyword('digipal') => <Source: DigiPal>
           If more than one match, the one with the lowest ID is returned.
        '''
        ret = None
        sources = cls.get_all_sources()

        if sources:
            for source in sources:
                if keyword.lower() in source.name.lower() or keyword.lower() in source.label.lower():
                    ret = source
                    break

        if not none_if_not_found and not ret:
            raise Exception('Source not found "%s".' % keyword)

        return ret

    @classmethod
    def get_or_create(cls, name):
        ret = None

        name = name or ''
        name = name.strip()
        if name:
            ret = cls.get_source_from_keyword(name, none_if_not_found=True)
            if ret is None:
                # not found create it
                ret = Source(name=name, label=name)
                ret.save()

        return ret

    def save(self, *args, **kwargs):
        self.label_slug = slugify(unicode(self.label))
        super(Source, self).save(*args, **kwargs)
        self.__class__._sources = None

# Manuscripts, Charters in legacy db


class CatalogueNumber(models.Model):
    historical_item = models.ForeignKey(HistoricalItem,
                                        related_name='catalogue_numbers', blank=True, null=True)
    text = models.ForeignKey(
        'Text', related_name='catalogue_numbers', blank=True, null=True)
    source = models.ForeignKey(Source)
    number = models.CharField(max_length=100)
    number_slug = models.SlugField(max_length=100, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    def clean(self):
        if self.historical_item is None and self.text is None:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                'A catalogue number must refer to a Text or a Historical Item.')

    class Meta:
        ordering = ['source', 'number']
        unique_together = ['source', 'number', 'historical_item', 'text']

    def __unicode__(self):
        return get_list_as_string(self.source, ' ', self.number)

    def save(self, *args, **kwargs):
        self.number_slug = slugify(unicode(self.number).replace('/', '-'))

        super(CatalogueNumber, self).save(*args, **kwargs)

        # save the associated HI (to recalculate HI.catalogue_number and
        # HI.display_label)
        if self.historical_item:
            self.historical_item.save()

    def on_post_delete(self):
        # save the associated HI (to recalculate HI.catalogue_number and
        # HI.display_label)
        if self.historical_item:
            self.historical_item.save()

    @classmethod
    def get_or_create(cls, cat_num):
        # cat_num is either a string 'SOURCE NUM' or a list/tuple ('SOURCE',
        # 'NUM')
        ret = None

        if isinstance(cat_num, list) or isinstance(
                cat_num, tuple) and len(cat_num) == 2:
            source, number = cat_num
        else:
            parts = [p.strip() for p in cat_num.strip().split(' ', 1)]
            if len(parts) == 2:
                source, number = parts
            else:
                source = None
                number = parts[0]

        source = Source.get_or_create(source)

        cns = CatalogueNumber.objects.filter(
            number__iexact=number, historical_item__isnull=False)
        if source:
            cns = cns.filter(source=source)

        if cns.count() == 0:
            if source:
                ret = CatalogueNumber(number=number, source=source)
                ret.save()
        if cns.count() == 1:
            ret = cns[0]

        return ret


from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=CatalogueNumber,
          dispatch_uid='cataloguenumber_delete_signal')
def cataloguenumber_delete_signal(sender, instance, using, **kwargs):
    instance.on_post_delete()

# Manuscripts in legacy db


class Collation(models.Model):
    historical_item = models.ForeignKey(HistoricalItem)
    fragment = models.NullBooleanField()
    leaves = models.IntegerField(blank=True, null=True)
    front_flyleaves = models.IntegerField(blank=True, null=True)
    back_flyleaves = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
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
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['historical_item']

    def __unicode__(self):
        return '%s' % (self.historical_item)


class Description(models.Model):
    '''A HI description'''
    historical_item = models.ForeignKey(HistoricalItem, blank=True, null=True)
    text = models.ForeignKey(
        'Text', related_name='descriptions', blank=True, null=True)

    source = models.ForeignKey(Source)

    description = HTMLField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    summary = models.CharField(max_length=256, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['historical_item', 'text']
        unique_together = ['source', 'historical_item', 'text']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.historical_item is None and self.text is None:
            raise ValidationError(
                'A description must refer to a Text or a Historical Item.')
        if not(self.description or self.comments or self.summary):
            raise ValidationError(
                'A description record must have a summary, a description or comments.')

    def __unicode__(self):
        # return u'%s %s' % (self.historical_item, self.source)
        return get_list_as_string(self.historical_item, ' ', self.source)

    def get_absolute_url(self):
        ret = u''
        hi = self.historical_item
        if hi:
            ip = hi.item_parts.first()
            if ip:
                ret = u'%sdescriptions/' % ip.get_absolute_url()
        return ret

    def get_description_or_summary(self):
        ret = (self.description or '').strip() or self.summary
        return ret

    def get_description_plain_text(self):
        '''Returns the description in plain text, no html tag or any encoding, just utf-8'''
        from utils import get_plain_text_from_html
        return get_plain_text_from_html(self.description)

# Manuscripts in legacy db


class Layout(models.Model):
    historical_item = models.ForeignKey(HistoricalItem, blank=True, null=True)
    item_part = models.ForeignKey(
        'ItemPart', blank=True, null=True, related_name='layouts')
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
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['item_part', 'historical_item']

    def __unicode__(self):
        return u'%s' % (self.item_part or self.historical_item)


# MsOrigin in legacy db
class ItemOrigin(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    historical_item = models.ForeignKey(HistoricalItem)
    evidence = models.TextField(blank=True, null=True, default='')
    dubitable = models.NullBooleanField()

    place = models.ForeignKey(
        'Place', null=True, blank=True, related_name='item_origins')
    institution = models.ForeignKey(
        'Institution', null=True, blank=True, related_name='item_origins')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['historical_item']

    def __unicode__(self):
        return get_list_as_string(
            self.content_type, ': ', self.content_object, ' ', self.historical_item)

    @property
    def content_object(self):
        '''Returns a Place or an Institution or None'''
        return self.place or self.institution or None

    @property
    def content_type(self):
        '''Returns a Place or an Institution id or None'''
        ret = None
        obj = self.content_object
        if obj:
            ret = ContentType.objects.get_for_model(obj)
        return ret

    @property
    def object_id(self):
        '''Returns a Place or an Institution id or None'''
        ret = None
        obj = self.content_object
        if obj:
            ret = obj.id
        return ret

# MsOrigin in legacy db


class Archive(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    historical_item = models.ForeignKey(HistoricalItem)
    dubitable = models.NullBooleanField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['historical_item']

    def __unicode__(self):
        # return u'%s: %s. %s' % (self.content_type, self.content_object,
        #        self.historical_item)
        return get_list_as_string(self.content_type, ': ',
                                  self.content_object, '. ', self.historical_item)


class Region(models.Model):
    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
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
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Counties'

    def __unicode__(self):
        return u'%s' % (self.name)


class PlaceType(models.Model):
    name = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)

# PlaceText in legacy db


class Place(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    # modern name
    name = models.CharField(max_length=256)
    # other name
    other_names = models.CharField(max_length=256, blank=True, null=True)
    eastings = models.FloatField(blank=True, null=True)
    northings = models.FloatField(blank=True, null=True)
    region = models.ForeignKey(Region, blank=True, null=True)
    current_county = models.ForeignKey(County,
                                       related_name='county_current',
                                       blank=True, null=True)
    historical_county = models.ForeignKey(County,
                                          related_name='county_historical',
                                          blank=True, null=True)
    type = models.ForeignKey(PlaceType, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)

    @classmethod
    def get_or_create(cls, name):
        ret = None

        name = name.strip()
        places = Place.objects.filter(name__iexact=name)
        if places.count():
            ret = places[0]
        else:
            ret = Place(name=name)
            ret.save()

        return ret


class OwnerType(models.Model):
    name = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class LibraryManager(models.Manager):
    def get_queryset(self):
        return super(LibraryManager, self).get_queryset().filter(type__id=3)

# Libraries in legacy db
# GN: this is now a general Owner table (Person, Institution, Repo)


class Repository(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=256)
    short_name = models.CharField(max_length=64, blank=True, null=True)
    place = models.ForeignKey(Place)
    url = models.URLField(blank=True, null=True)
    comma = models.NullBooleanField(null=True)
    # legacy.`Overseas?`
    british_isles = models.NullBooleanField(null=True)

    type = models.ForeignKey('OwnerType', null=True,
                             blank=True, default=None, related_name='repositories')

    part_of = models.ForeignKey('self', null=True,
                                blank=True, default=None, related_name='parts')

    digital_project = models.NullBooleanField(null=True)
    copyright_notice = HTMLField(blank=True, null=True)
    media_permission = models.ForeignKey(MediaPermission, null=True,
                                         blank=True, default=None,
                                         help_text='''The default permission scheme for images originating
            from this repository.<br/> The Pages can override the
            repository default permission.
            ''')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    #objects = LibraryManager()
    #all_objects = models.Manager()

    class Meta:
        ordering = ['short_name', 'name']
        verbose_name_plural = 'Repositories'

    def __unicode__(self):
        return u'%s' % (self.short_name or self.name)

    def human_readable(self):
        # return u'%s, %s' % (self.place, self.name)
        return get_list_as_string(self.place, ', ', self.name)

    @staticmethod
    def get_default_media_permission():
        return MediaPermission.get_new_default()

    def get_media_permission(self):
        # this function will always return a media_permission object
        return self.media_permission or Repository.get_default_media_permission()

    @classmethod
    def get_or_create(cls, city_comma_name):
        ret = None
        parts = [p.strip() for p in city_comma_name.split(',', 1)]
        if len(parts) == 2:
            city, name = parts
            place = Place.get_or_create(city)
            repos = Repository.objects.filter(name__iexact=name, place=place)
            if repos.count():
                ret = repos[0]
            else:
                ret = Repository(name=name, place=place)
                ret.save()
        return ret


class CurrentItem(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    repository = models.ForeignKey(Repository)
    shelfmark = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    display_label = models.CharField(max_length=128)
    owners = models.ManyToManyField(
        Owner, blank=True, default=None, related_name='current_items')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['repository', 'shelfmark']
        unique_together = ['repository', 'shelfmark']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def save(self, *args, **kwargs):
        self.display_label = get_list_as_string(
            self.repository, ' ', self.shelfmark)
        super(CurrentItem, self).save(*args, **kwargs)

    def get_part_count(self):
        return self.itempart_set.all().count()
    get_part_count.short_description = 'Parts'
    get_part_count.allow_tags = False

    @classmethod
    def get_or_create(cls, shelfmark, repository):
        ret = None
        shelfmark = shelfmark.strip()
        repository = repository.strip()
        repository = Repository.get_or_create(repository)
        if repository:
            items = CurrentItem.objects.filter(
                shelfmark__iexact=shelfmark, repository=repository)
            if items.count():
                ret = items[0]
            else:
                ret = CurrentItem(shelfmark=shelfmark, repository=repository)
                ret.save()
        return ret

# OwnerText in legacy db


class Person(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=256, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


class InstitutionType(models.Model):
    name = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
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
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
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
    reference = models.ManyToManyField(Reference, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)
    legacy_reference = models.CharField(
        max_length=128, blank=True, null=True, default='')

    class Meta:
        ordering = ['name']

    has_absolute_url = True

    def __unicode__(self):
        # return u'%s. %s' % (self.name, self.date or '')
        return get_list_as_string(self.name, '. ', self.date)

    def get_images(self):
        return Image.objects.filter(hands__scribe=self)


class Idiograph(models.Model):
    allograph = models.ForeignKey(Allograph)
    scribe = models.ForeignKey(
        Scribe, related_name="idiographs", blank=True, null=True)
    aspects = models.ManyToManyField(Aspect, blank=True)
    display_label = models.CharField(max_length=128, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    @staticmethod
    def get_definition():
        return u'''The way (or one of the ways) in which an individual writes a given allograph'''

    class Meta:
        ordering = ['allograph']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def save(self, *args, **kwargs):
        #self.display_label = u'%s. %s' % (self.allograph, self.scribe)
        self.display_label = get_list_as_string(
            self.allograph, '. ', self.scribe)
        super(Idiograph, self).save(*args, **kwargs)


class IdiographComponent(models.Model):
    idiograph = models.ForeignKey(Idiograph)
    component = models.ForeignKey(Component)
    features = models.ManyToManyField(Feature)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
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
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['date']

    def __unicode__(self):
        # return u'%s. %s' % (self.historical_item, self.date)
        return get_list_as_string(self.historical_item, '. ', self.date)


class ItemPartType(models.Model):
    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)

# Manuscripts and Charters in legacy db


class ItemPart(models.Model):
    historical_items = models.ManyToManyField(
        HistoricalItem, through='ItemPartItem', related_name='item_parts')
    current_item = models.ForeignKey(
        CurrentItem, blank=True, null=True, default=None)

    # the reference to a grouping part and the locus of this part in the group
    group = models.ForeignKey('self', related_name='subdivisions', null=True,
                              blank=True, help_text='the item part which contains this one')
    group_locus = models.CharField(
        max_length=64, blank=True, null=True, help_text='the locus of this part in the group')

    # This is the locus in the current item
    locus = models.CharField(max_length=64, blank=True, null=True,
                             default=settings.ITEM_PART_DEFAULT_LOCUS, help_text='the location of this part in the Current Item')
    display_label = models.CharField(max_length=300)
    custom_label = models.CharField(
        max_length=300,
        blank=True, null=True,
        help_text='A custom label for this part. If blank the shelfmark will be used as a label.',
    )
    pagination = models.BooleanField(blank=False, null=False, default=False)
    type = models.ForeignKey(ItemPartType, null=True, blank=True)
    owners = models.ManyToManyField(Owner, blank=True)
    notes = models.TextField(blank=True, null=True)

    keywords = KeywordsField(
        help_text='<br/>Comma separated list of keywords. Keywords are case sensitive and can contain spaces. Keywords can also be added or removed using the list above.')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['display_label']
        #unique_together = ['historical_item', 'current_item', 'locus']

    has_absolute_url = True

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def clean(self):
        if self.group_id and self.group_id == self.id:
            from django.core.exceptions import ValidationError
            raise ValidationError('An Item Part cannot be its own group.')

    def get_has_public_image_label(self):
        # a label for the faceted search
        ret = 'Without image'
        if self.get_non_private_image_count():
            ret = 'With image'
        return ret

    def get_non_private_image_count(self):
        return Image.filter_permissions(self.images.all(
        ), [MediaPermission.PERM_PUBLIC, MediaPermission.PERM_THUMB_ONLY]).count()

    def get_shelfmark_with_auth(self):
        ret = self.current_item.shelfmark
        if self.is_suspect():
            ret += ' <b>(anachronistic)</b>'
        return ret

    def is_suspect(self, authenticities=None):
        authenticities = authenticities or self.authenticities.all()
        return any([auth.is_suspect() for auth in authenticities])

    def get_authenticity_labels(self):
        ret = []
        authenticities = self.authenticities.all()
        for auth in authenticities:
            cat = auth.category
            ret.append(cat.name)
        if self.is_suspect(authenticities):
            ret.append('Anachronistic')

        if not ret:
            ret = ['Unspecified']

        return ret

    def get_image_count(self):
        return self.images.all().count()
    get_image_count.short_description = 'Images'
    get_image_count.allow_tags = False

    def get_part_count(self):
        return self.subdivisions.all().count()
    get_part_count.short_description = 'Parts'
    get_part_count.allow_tags = False

    def _update_display_label_and_save(self):
        ''' only save if the display label has changed '''
        if self._update_display_label():
            self.save()

    def _update_display_label(self):
        '''Automatically update the display_label.
        Use .custom_label if defined.
        Otherwise use the CurrentItem.display_label + locus
        Otherwise use the HistoricalItem.display_label
        '''
        old_label = self.display_label
        if self.custom_label and self.custom_label.strip():
            self.display_label = self.custom_label.strip()
        else:
            if self.current_item:
                self.display_label = get_list_as_string(
                    self.current_item, ', ', self.locus)
            else:
                label = self.historical_label
                if label:
                    self.display_label = label
        return old_label != self.display_label

    def save(self, *args, **kwargs):
        self._update_display_label()
        super(ItemPart, self).save(*args, **kwargs)

    @property
    def historical_label(self):
        ret = ''
        # label is 'HI, locus'
        iphis = self.constitutionalities.all()
        if iphis.count():
            ret = get_list_as_string(
                iphis[0].historical_item, ', ', iphis[0].locus)
        else:
            # label is 'group.historical_label, group_locus'
            if self.group:
                ret = get_list_as_string(
                    self.group.historical_label, ', ', self.group_locus)
        return ret

    @property
    def historical_item(self):
        # Commented out as it is not cached by Django due to the sorting
        # If sorting is important then it is best to do it manually on all().
        # return self.historical_items.order_by('id').first()
        return self.historical_items.first()

    def get_current_items(self):
        # this function will return all related current items.
        # by looking at this CI and also the subdivisions CI.
        ret = {}
        if self.current_item:
            ret[self.current_item.id] = self.current_item
        for subdivision in self.subdivisions.all().order_by('id'):
            if subdivision.current_item:
                ret[subdivision.current_item.id] = subdivision.current_item
        return ret.values()

    def get_quires(self):
        return self.get_quires_from_id(self.id)

    def get_first_image(self):
        '''Returns the first non private image for this IP
            If in DEBUG mode we ignore permissions.
        '''
        ret = Image.sort_query_set_by_locus(self.images.all())
        if not settings.DEBUG:
            ret = Image.filter_permissions(ret, [
                MediaPermission.PERM_PUBLIC, MediaPermission.PERM_THUMB_ONLY])
        return ret.first()

    @classmethod
    def get_quires_from_id(cls, item_partid):
        '''Returns a dict of quire information
            {QUIRE_NUMBER: {'start': LOCUS}}
           In no particular order.
        '''
        locus_quire = {}
        for info in Image.objects.filter(item_part_id=item_partid).values_list(
                'locus', 'quire').order_by('id'):
            locus_quire[info[0]] = info[1]

        # only keep the first locus for each quire
        ret = {}
        for locus in sorted_natural(
                locus_quire.keys(), roman_numbers=True, is_locus=True)[::-1]:
            ret[locus_quire[locus]] = {'start': locus}

        return ret


''' This is used to build the front-end URL of the item part objects
    See set_models_absolute_urls()
'''
ItemPart.webpath_key = 'Manuscripts'

# Represents the physical belonging to a whole (Item) during a period of time in history.
# A constitutionality.


class ItemPartItem(models.Model):
    historical_item = models.ForeignKey(
        HistoricalItem, related_name='partitions')
    item_part = models.ForeignKey(ItemPart, related_name='constitutionalities')
    locus = models.CharField(max_length=64, blank=True, null=False, default='')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
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
                group_label = '%s, %s' % (
                    self.item_part.group.current_item.shelfmark, self.item_part.group.locus)
            else:
                ipi = ItemPartItem.objects.filter(
                    item_part=self.item_part.group)
                if ipi.count():
                    ipi = ipi[0]
                    group_label = '%s, %s' % (
                        ipi.historical_item.name, ipi.locus)
            if group_label:
                ret += ur' [part of %s: %s]' % (
                    self.item_part.group.type, group_label)

        return ret


class ItemPartAuthenticity(models.Model):
    item_part = models.ForeignKey(
        'ItemPart', related_name="authenticities", blank=False, null=False)
    category = models.ForeignKey(
        'AuthenticityCategory', related_name="itempart_authenticity", blank=False, null=False)
    source = models.ForeignKey(
        'Source', related_name="itempart_authenticity", blank=True, null=True)
    note = models.TextField(blank=True, null=True, default=None)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(
        auto_now=True, editable=False)

    class Meta:
        unique_together = ['item_part', 'category', 'source']

    def __unicode__(self):
        return '%s (%s)' % (self.category, self.source.label)

    def is_suspect(self):
        return 'anachronistic' in self.category.slug


class AuthenticityCategory(NameModel):
    pass


class TextItemPart(models.Model):
    item_part = models.ForeignKey(
        'ItemPart', related_name="text_instances", blank=False, null=False)
    text = models.ForeignKey(
        'Text', related_name="text_instances", blank=False, null=False)
    locus = models.CharField(max_length=20, blank=True, null=True)
    date = models.CharField(max_length=128, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(
        auto_now=True, editable=False)

    class Meta:
        unique_together = ['item_part', 'text']

    def __unicode__(self):
        locus = ''
        if self.locus:
            locus = u' (%s)' % self.locus
        return u'%s in %s%s' % (
            self.text.name, self.item_part.display_label, locus)

# LatinStyleText in legacy db


class LatinStyle(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    style = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['style']

    def __unicode__(self):
        return u'%s' % (self.style)


class ImageAnnotationStatus(models.Model):
    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Image annotation statuses'

    def __unicode__(self):
        return u'%s' % (self.name)

# This is an image of a part of an item-part


class Image(models.Model):
    item_part = models.ForeignKey(
        ItemPart, related_name='images', null=True, blank=True, default=None)

    locus = models.CharField(max_length=64, blank=True, null=False, default='')
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
    iipimage = iipfield.fields.ImageField(upload_to=iipfield.storage.get_image_path,
                                          blank=True, null=True, storage=iipfield.storage.image_storage, max_length=200)

    display_label = models.CharField(max_length=128)
    # optional the display label provided by the user
    custom_label = models.CharField(max_length=128, blank=True, null=True,
                                    help_text='Leave blank unless you want to customise the value of the display label field')

    media_permission = models.ForeignKey(MediaPermission, null=True, blank=True, default=None,
                                         help_text='''This field determines if the image is publicly visible and the reason if not.''')

    transcription = models.TextField(blank=True, null=True)
    internal_notes = models.TextField(blank=True, null=True)

    annotation_status = models.ForeignKey(
        ImageAnnotationStatus, related_name='images', null=True, blank=True, default=None)

    # THESE FIELDS SHOULD NOT BE READ DIRECTLY,
    # please call self.dimension instead.
    # They are used internally as a cache for the dimensions.
    width = models.IntegerField(blank=False, null=False, default=0)
    height = models.IntegerField(blank=False, null=False, default=0)

    # Size of the image file in bytes.
    # This field may contain 0 even if the record points to a valid image.
    # This is because, unlike the height/width, the size cannot be obtained from the image server.
    # It can only be populated by code having access to the file on
    # disk/network.
    size = models.IntegerField(blank=False, null=False, default=0)

    keywords = KeywordsField(
        help_text='<br/>Comma separated list of keywords. Keywords are case sensitive and can contain spaces. Keywords can also be added or removed using the list above.')

    quire = models.CharField(max_length=10, blank=True, null=True,
                             default=None, help_text='A quire number, e.g. 3')

    page_boundaries = models.CharField(max_length=100, blank=True, null=True, default=None,
                                       help_text='relative coordinates of the page boundaries in json. e.g. [[0.3, 0.1], [0.7, 0.9]]')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(
        auto_now=True, editable=False)

    __original_iipimage = None

    class Meta:
        ordering = ['item_part__display_label', 'folio_number', 'folio_side']

    has_absolute_url = True

    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
        self.__original_iipimage = self.iipimage

    def __unicode__(self):
        ret = u''
        if self.display_label:
            ret = u'%s' % self.display_label
        else:
            ret = u'Untitled Image #%s' % self.id
            if self.iipimage:
                ret += u' (%s)' % re.sub(
                    ur'^.*?([^/]+)/([^/.]+)[^/]+$', ur'\1, \2', self.iipimage.name)
        return ret

    def get_annotation_count(self):
        '''returns only annotations which have either a graph or a display note'''
        return len([1 for an in self.annotation_set.all()
                    if an.is_publicly_visible])

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

    def set_page_boundaries(self, boundaries):
        ''' e.g. [[0.3, 0.1], [0.7, 0.9]] '''
        import json
        self.page_boundaries = json.dumps(boundaries)

    def get_page_boundaries(self, margin=0.02):
        ''' Returns the boundaries of the page in the image.
        [[x0, y0], [x1, y1]], all proportional to size of the image
        e.g. [[0.3, 0.1], [0.7, 0.9]]
        margin: to enlarge the boundaries, to compensate for boundaries
            approximation and to be visually more pleasant
        '''
        import json
        ret = self.page_boundaries
        if ret:
            ret = json.loads(ret)
        else:
            ret = [[0.0, 0.0], [1.0, 1.0]]

        dims = self.dimensions()
        for i in [0, 1]:
            for d in [0, 1]:
                diff = (1.0 * margin)
                ret[i][d] += ((i * 2) - 1) * diff
                if ret[i][d] < 0:
                    ret[i][d] = 0.0
                if ret[i][d] > 1:
                    ret[i][d] = 1.0

        return ret

    def is_media_public(self):
        return not self.is_media_private()

    def is_media_private(self):
        return self.get_media_permission().permission == MediaPermission.PERM_PRIVATE

    def is_thumb_only(self):
        return self.get_media_permission().permission == MediaPermission.PERM_THUMB_ONLY

    def is_full_res_for_user(self, request):
        #ret = not self.is_private_for_user(request) and self.get_media_permission().permission == MediaPermission.PERM_PUBLIC
        from digipal.utils import is_staff
        ret = is_staff(request) or self.get_media_permission(
        ).permission == MediaPermission.PERM_PUBLIC
        return ret

    def is_private_for_user(self, request):
        from digipal.utils import is_staff
        return (not is_staff(request)) and (
            self.get_media_permission().permission <= MediaPermission.PERM_PRIVATE)

    def get_media_right_label(self):
        ret = 'Full size image'
        if self.is_media_private():
            ret = 'Thumbnail only'
        return ret

    def get_media_unavailability_reason(self, user=None):
        '''Returns an empty string if the media can be viewed in full res. by the user.
           Returns a message explaining the reason otherwise.
           If User is not given, we assume public user.
        '''
        ret = ''

        if not self.iipimage:
            # image is missing, default message
            ret = 'This record has no Image'
        else:
            if not has_user_edit_permission(user, Image):
                permission = self.get_media_permission()
                if permission.permission < MediaPermission.PERM_PUBLIC:
                    ret = permission.display_message
                    if not ret:
                        ret = settings.UNSPECIFIED_MEDIA_PERMISSION_MESSAGE

        return ret

    def get_document_summary(self):
        ret = u''
        if self.item_part and self.item_part.historical_item:
            ret = self.item_part.historical_item.get_display_description()
            if ret:
                ret = ret.get_description_or_summary()
        return ret

    @classmethod
    def filter_public_permissions(cls, image_queryset):
        '''Filter an Image queryset to keep only the images with FULL public permissions.
            Returns the modified query set.
        '''
        return cls.filter_permissions(image_queryset)

    @classmethod
    def filter_permissions(cls, image_queryset, permissions=[
                           MediaPermission.PERM_PUBLIC]):
        '''Filter an Image queryset to keep only the images with FULL public permissions.
            Returns the modified query set.
        '''
        ret = image_queryset
        if permissions:

            conditions = Q(media_permission__permission__in=permissions) |\
                (
                    Q(media_permission__permission__isnull=True) &
                    Q(item_part__current_item__repository__media_permission__permission__in=permissions)
            )

            if MediaPermission.PERM_PRIVATE in permissions:
                conditions = conditions |\
                    (
                        Q(media_permission__permission__isnull=True) &
                        Q(item_part__current_item__repository__media_permission__permission__isnull=True)
                    )

            ret = ret.filter(conditions)
        return ret

    @classmethod
    def get_public_only(cls):
        '''Return all the publicly accessible records.'''
        return cls.filter_public_permissions(cls.objects.all())

    @classmethod
    def filter_permissions_from_request(
            cls, image_queryset, request, show_full=False):
        from digipal.utils import is_staff
        ret = image_queryset
        if not is_staff(request):
            permissions = [MediaPermission.PERM_PUBLIC]
            if not show_full:
                permissions.append(MediaPermission.PERM_THUMB_ONLY)
            ret = cls.filter_permissions(ret, permissions)
        return ret

    @classmethod
    def get_all_public_images(cls):
        if not hasattr(cls, 'public_images'):
            cls.public_images = Image.filter_public_permissions(
                Image.objects.all())
        return cls.public_images

    def get_locus_label_without_type(self, hide_type=False):
        return self.get_locus_label(True)

    def get_locus_label(self, hide_type=False):
        ''' Returns a label for the locus from the side and number fields.
            If hide_type is False, don't include p. or f. in the output.
        '''
        ret = u''
        if self.folio_number:
            ret = ret + unicode(self.folio_number)
        if self.folio_side:
            ret = ret + unicode(self.folio_side)

        if ret == u'0r':
            ret = u'face'
        if ret == u'0v':
            ret = u'dorse'

        if ret and self.folio_number and self.folio_number != u'0' and not hide_type:
            unit = u'f.'
            if self.item_part and self.item_part.pagination:
                unit = u'p.'
            ret = unit + ret

        return ret

    def save(self, *args, **kwargs):
        # TODO: shouldn't this be turned into a method instead of resetting
        # each time?
        if self.custom_label is None:
            self.custom_label = ''
        self.custom_label = self.custom_label.strip()
        if self.custom_label:
            self.display_label = self.custom_label
        else:
            if (self.item_part):
                self.display_label = get_list_as_string(
                    self.item_part, ': ', self.locus)
            else:
                self.display_label = u''
        self.update_number_and_side_from_locus()

        # update the height amd width if the image path has changed
        if self.iipimage != self.__original_iipimage:
            self.height = 0
            self.width = 0
            self.size = 0

        if self.iipimage and self.iipimage.name:
            self.iipimage.name = self.iipimage.name.replace('\\', '/')

        super(Image, self).save(*args, **kwargs)
        self.__original_iipimage = self.iipimage

    def update_number_and_side_from_locus(self):
        ''' sets self.folio_number and self.folio_side from self.locus
            e.g. self.locus = '10r' => self.folio_number = 10, self.folio_side = 'r'
            Front => (None, None)
            327(2) => (327, v)

            See dptest.py test_locus() for test cases
        '''
        self.folio_number = None
        self.folio_side = None
        self.locus = (self.locus or '').strip()
        if self.locus:
            matches = re.findall(ur'(\d+)', self.locus)
            if matches:
                self.folio_number = matches[0]
            else:
                if 'seal' in self.locus.lower():
                    # appear after all other folios
                    self.folio_number = 'x'
                if 'front' in self.locus.lower():
                    # appear before anything else
                    self.folio_number = '0'

            locus = u'%s' % self.locus
            locus = re.sub(ur'(?i)face', 'recto', locus)
            locus = re.sub(ur'(?i)dorse', 'verso', locus)
            locus = re.sub(ur'(?i)recto', 'r', locus)
            locus = re.sub(ur'(?i)verso', 'v', locus)

            matches = re.findall(ur'(?:[^a-z]|^)([rv])(?:[^a-z]|$)', locus)
            if matches:
                self.folio_side = matches[0]
        else:
            # that way unset locus are displayed below set locus
            self.folio_number = 'y'

        return self.folio_number, self.folio_side

    def path(self):
        """Returns the path of the image on the image server. The server path
        is composed by combining repository/shelfmark/locus."""
        return self.iipimage.name.replace('\\', '/')

    def dimensions(self, cropped=False):
        """Returns a tuple with the image width and height.
            This function can SAVE the current model if the
            cache dimensions were 0 (or the image has changed).
            If cropped = True, returns the dimensions of the page boundaries
        """
        ret = (self.width, self.height)

        # image has changed, we reset the dims
        if (self.iipimage != self.__original_iipimage):
            ret = (0, 0)

        if ret == (0, 0):
            if self.iipimage:
                # obtain the new dims from the image server
                ret = self.iipimage._get_image_dimensions()

        if ret != (self.width, self.height):
            (self.width, self.height) = ret
            if self.pk:
                # need to do this otherwise the dims will be reset in save
                self.__original_iipimage = self.iipimage
                self.save()

        if cropped:
            boundaries = self.get_page_boundaries()
            if boundaries:
                ret = [int((boundaries[1][d] - boundaries[0][d]) * ret[d])
                       for d in [0, 1]]

        return ret

    def zoomify(self):
        """Returns the URL to view the image from the image server as zoomify
        tiles."""
        zoomify = None

        if self.path():
            zoomify = settings.IMAGE_SERVER_ZOOMIFY % \
                (settings.IMAGE_SERVER_HOST, settings.IMAGE_SERVER_PATH,
                 self.path())
            zoomify = self.get_relative_or_absolute_url(zoomify)

        return zoomify

    def full(self):
        """Returns the URL for the full size image.
           Something like http://iip-lcl:3080/iip/iipsrv.fcgi?FIF=jp2/cccc/391/602.jp2&amp;RST=*&amp;QLT=100&amp;CVT=JPG
           The query string in the returned URL is already encoded with ampersand.
        """
        path = ''
        if self.iipimage:
            #path = self.iipimage.full_base_url
            path = settings.IMAGE_SERVER_FULL % \
                (settings.IMAGE_SERVER_HOST, settings.IMAGE_SERVER_PATH,
                 self.path())

            path = self.get_relative_or_absolute_url(path)

        return path

    @classmethod
    def get_relative_or_absolute_url(cls, url):
        ret = url
        if settings.IMAGE_URLS_RELATIVE:
            ret = re.sub(ur'(?i)(^https?://[^/]+)', '', ret)
        return ret

    def thumbnail_with_link(self, height=None, width=None):
        """Returns HTML to display the page image as a thumbnail with a link to
        view the image."""
        ret = mark_safe(u'<a href="%s">%s</a>' %
                        (self.full(), self.thumbnail(height, width)))
        return ret
    thumbnail_with_link.short_description = 'Thumbnail'
    thumbnail_with_link.allow_tags = True

    def thumbnail(self, height=None, width=None, uncropped=False):
        """Returns HTML to display the page image as a thumbnail."""
        ret = ''
        if self.iipimage:
            ret = mark_safe(u'<img src="%s" />' %
                            (cgi.escape(self.thumbnail_url(height, width, uncropped))))
        return ret

    thumbnail.short_description = 'Thumbnail'
    thumbnail.allow_tags = True

    def thumbnail_url(self, height=None, width=None, uncropped=False):
        """Returns URL of the image thumbnail.
           By default the image is cropped to include only the page.
        """
        ret = ''
        if width is None and height is None:
            height = settings.IMAGE_SERVER_THUMBNAIL_HEIGHT
        if self.iipimage:
            ret = self.iipimage.thumbnail_url(height, width)

        if 1 and ret and not uncropped:
            region = self.get_page_boundaries()
            if region:
                # convert region from ((x0rel, y0rel), (x1rel, y1rel))
                # to RGN=x,y,w,h (all ratios)
                region = [
                    region[0][0], region[0][1],
                    region[1][0] - region[0][0], region[1][1] - region[0][1]
                ]
                ret = ret.replace('&CVT=', '&RGN=%s&CVT=' %
                                  (','.join(['%0.5f' % p for p in region]),))

        ret = self.get_relative_or_absolute_url(ret)

        return ret

    def get_region_dimensions(self, region_url):
        ''' returns the dimension (width, height) of an IIPImage server
            region (e.g. ...WID=500&RGN=0.1,0.1,0.2,0.2&CVT=JPG) of this image
            returns -1 for unknown dimensions'''
        ret = [-1, -1]
        dims = [float(v) for v in self.dimensions()]
        if max(dims) == 0:
            return (0, 0)
        matches = re.search(ur'(WID|HEI)=(\d*)', region_url)
        if matches:
            d = 0
            if matches.group(1) == 'HEI':
                d = 1
            requested_dim = float(matches.group(2))
            dims[1 - d] = dims[1 - d] / dims[d] * requested_dim
            dims[d] = requested_dim
        matches = re.search(ur'RGN=([^&]*)', region_url)
        if matches:
            parts = [float(part) for part in matches.group(1).split(',')]
            parts[2]
            # don't ask... it sees like iip image server returns the double of
            # the requested size!!
            factor = 2
            ret = [int(parts[2] * dims[0]) * factor,
                   int(parts[3] * dims[1]) * factor]
        return ret

    @classmethod
    def sort_query_set_by_locus(self, query_set, ignore_item_part=False):
        ''' Returns a query set based on the given one but with
            results sorted by item part then locus.
        '''
        # TODO: fall back for non-postgresql RDBMS
        # TODO: optimise this by caching the result in a field
        sort_fields = ['fn', 'folio_side']
        if not ignore_item_part:
            sort_fields.insert(0, 'item_part__display_label')
        return query_set.extra(select={
                               'fn': ur'''CASE WHEN digipal_image.folio_number~E'^\\d+$' THEN digipal_image.folio_number::integer ELSE 0 END'''}, ).order_by(*sort_fields)

    def get_duplicates(self):
        '''Returns a list of Images with the same locus and shelfmark.'''
        return Image.objects.filter(
            id__in=Image.get_duplicates_from_ids([self.id]).get(self.id, []))

    def get_img_size(self):
        '''Returns (w, h), the width and height of the image
            WARNING: this function is SLOW because it makes a HTTP request to the image server.
            Only call if absolutely necessary.
        '''
        return self.iipimage._get_image_dimensions()

    @classmethod
    def get_duplicates_from_ids(cls, ids=None):
        ''' Returns a dictionary of duplicate images
            e.g. {1: (3,), 2: (8,), 3: (1,), 8: (2,)}
            Images are considered as duplicates if they have the same CI.id and the same locus.
            Means that 1 and 3 are duplicates and 2 and 8 are duplicates
            If ids is none, all possible duplicates are returned.
            Otherwise only duplicates for the given list of ids are returned.
        '''
        ret = {}
        from django.db import connection
        cursor = connection.cursor()
        selection_condition = u''
        if ids is not None:
            selection_condition = 'and i1.id in (%s)' % ', '.join(
                [unicode(item) for item in ids])
        select = u'''
            select distinct i1.id, i2.id
            from digipal_image i1 join digipal_itempart ip1 on i1.item_part_id = ip1.id,
            digipal_image i2 join digipal_itempart ip2 on i2.item_part_id = ip2.id
            where i1.id <> i2.id
            and regexp_replace(replace(replace(lower(i1.locus), 'recto', 'r'), 'verso', 'v'), '^(p|f|pp)(\.|\s)|\s+', '', 'g') =
                regexp_replace(replace(replace(lower(i2.locus), 'recto', 'r'), 'verso', 'v'), '^(p|f|pp)(\.|\s)|\s+', '', 'g')
            and ip1.current_item_id = ip2.current_item_id
            %s
            order by i1.id, i2.id''' % selection_condition
        cursor.execute(select)

        for (id1, id2) in list(cursor.fetchall()):
            ret[id1] = ret.get(id1, [])
            ret[id1].append(id2)
        cursor.close()

        return ret


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


# Hands in legacy db
class Hand(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    num = models.IntegerField(
        help_text='''The order of display of the Hand label. e.g. 1 for Main Hand, 2 for Gloss.''')
    item_part = models.ForeignKey(ItemPart, related_name='hands')
    script = models.ForeignKey(Script, blank=True, null=True)
    scribe = models.ForeignKey(
        Scribe, blank=True, null=True, related_name='hands')
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
    display_note = models.TextField(
        blank=True, null=True, help_text='An optional note that will be publicly visible on the website.')
    internal_note = models.TextField(
        blank=True, null=True, help_text='An optional note for internal or editorial purpose only. Will not be visible on the website.')
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
    images = models.ManyToManyField(Image, blank=True, related_name='hands',
                                    help_text='''Select the images this hand appears in. The list of available images comes from images connected to the Item Part associated to this Hand.''')

    # GN: we might want to ignore display_label, it is not used on the admin
    # form or the search or record views on the front end.
    # Use label instead.
    display_label = models.CharField(max_length=128, editable=False)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    # Imported from Brookes DB
    locus = models.CharField(max_length=300, null=True, blank=True, default='')
    # TODO: migrate to Cat Num (From Brookes DB)
    surrogates = models.CharField(
        max_length=50, null=True, blank=True, default='')
    # From Brookes DB
    selected_locus = models.CharField(
        max_length=100, null=True, blank=True, default='')
    stewart_record = models.ForeignKey(
        'StewartRecord', null=True, blank=True, related_name='hands')

    def idiographs(self):
        if self.scribe:
            results = [
                idio.display_label for idio in self.scribe.idiographs.all()]
            return list(set(results))
        else:
            return None

    class Meta:
        ordering = ['item_part', 'num']

    has_absolute_url = True

    # def get_idiographs(self):
    # return [idiograph for idiograph in self.scribe.idiograph_set.all()]

    @classmethod
    def get_default_label(cls):
        return getattr(
            settings, 'ARCHETYPE_HAND_LABEL_DEFAULT', 'Default Hand')

    def get_search_label(self):
        return '%s%s' % (settings.ARCHETYPE_HAND_ID_PREFIX, self.id)

    def get_short_label(self):
        ret = unicode(self)
        ret = re.sub(ur'\([^)]*\)', ur'', ret)
        return ret

    def __unicode__(self):
        # return u'%s' % (self.description or '')
        # GN: See Jira ticket DIGIPAL-76,
        # hand.reference has moved to hand.label
        return u'%s' % (self.label or self.description or '')[0:80]

    # self.description is an alias for hd.description
    # with hd = self.HandDescription.description such that
    # hd.source.name = 'digipal'.
    def __getattr__(self, name):
        if name == 'description':
            ret = ''
            for description in self.descriptions.filter(
                    source__id=settings.SOURCE_PROJECT_ID):
                ret = description.description
        else:
            ret = super(Hand, self).__getattr__(name)
        return ret

    def __setattr__(self, name, value):
        if name == 'description':
            self.set_description(settings.SOURCE_PROJECT_NAME, value, True)
        else:
            super(Hand, self).__setattr__(name, value)

    def validate_unique(self, exclude=None):
        # Unique constraint for new records only: (item_part, label)
        # Not as unique_together because we already have records violating this
        super(Hand, self).validate_unique(exclude)
        if Hand.objects.filter(label=self.label, item_part=self.item_part).exclude(
                id=self.id).exists():
            from django.core.exceptions import ValidationError
            errors = {}
            errors.setdefault('label', []).append(
                ur'Insertion failed, another record with the same label and item part already exists')
            raise ValidationError(errors)

    def set_description(self, source_name, description=None,
                        remove_if_empty=False):
        ''' Set the description of a hand according to a source (e.g. ker, sawyer).
            Create the source if it doesn't exist yet.
            Update description if it exists, add it otherwise.
            Null or blank description field are ignored. Unless remove_if_empty = True
        '''
        empty_value = description is None or not description.strip()
        if empty_value and not remove_if_empty:
            return

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

    def _update_images_from_stints(self, errors=None):
        # get the hand descriptions
        loci = []
        for desc in self.descriptions.all().order_by('source__priority'):
            for stint_range in desc.get_stints_ranges():
                # expand the stint range (e.g. 363v14-4r18) into loci (->
                # 363v...364r)
                from digipal.utils import expand_folio_range
                stint_loci = expand_folio_range(stint_range, errors)
                loci.extend(stint_loci)
            if loci:
                break
        #
        images = Image.objects.filter(locus__in=loci)
        # reset the images
        self.images.clear()
        #
        self.images.add(*images)


Hand.images.through.__unicode__ = lambda self: u'%s in %s' % (
    self.hand.label, self.image.display_label)


class HandDescription(models.Model):
    hand = models.ForeignKey(
        Hand, related_name="descriptions", blank=True, null=True)
    source = models.ForeignKey(
        Source, related_name="hand_descriptions", blank=True, null=True)

    description = models.TextField(
        help_text='''This field accepts TEI elements.''')

    label = models.CharField(max_length=64, blank=True, null=True,
                             help_text='''A label assigned to this hand by a source. E.g. 'Alpha' (for source 'Flight').''')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['hand', 'source__priority']

    def get_stints_ranges(self):
        return re.findall(
            ur'<span[^>]+data-dpt="stint"[^>]+>([^<]+)</span>', self.description or '')

    def get_description_html(self, editorial_view=False):
        '''Returns the description field with additional XML mark-up based on the format
            If editorial_view is True, additional info is provided such as unfound loci.
        '''
        ret = self.description

        loci = {}
        for im in self.hand.item_part.images.all():
            loci[im.locus.lower()] = im.get_absolute_url()

        hands = {}
        for hand in self.hand.item_part.hands.all().prefetch_related('descriptions'):
            for desc in hand.descriptions.all().order_by('-source__priority'):
                if desc.label:
                    hands[desc.label.lower()] = hand.get_absolute_url()
            if hand.label:
                hands[hand.label.lower()] = hand.get_absolute_url()

        # print hands

        def replace_references(content, apattern, labels, content_type):
            pattern = re.compile(apattern)
            pos = 0
            while True:
                match = pattern.search(content, pos)
                if not match:
                    break

                label = match.group(1).lower()

                replacement = ''

                if 'model="graph"' in apattern:
                    # The user grabs the id of graph on the front end
                    # Click the 'Annotation' button. This marks up as 'graph'.
                    #
                    # <span data-dpt-model="graph" data-dpt="record">#10</span>
                    #
                    # We find the annotation with that graph ID
                    #
                    matchid = re.match(ur'#(\d+)', label)
                    if matchid:
                        from digipal.templatetags.html_escape import annotation_img
                        # replacement = annotation_img(annotation,  [width=W]
                        # [height=H] [cls=HTML_CLASS] [lazy=0|1] [padding=0])
                        annotation = Annotation.objects.filter(
                            graph__id=matchid.group(1)).first()
                        if annotation:
                            replacement = '<a href="%s">%s</a>' % (
                                annotation.get_absolute_url(), annotation_img(annotation))
                        elif editorial_view:
                            replacement = '<span class="locus-not-found" title="%s not found" data-toggle="tooltip">%s</span>' % (
                                content_type, label)

                if not replacement:
                    replacement = match.group(0)
                    link = labels.get(label, '')
                    if link:
                        replacement = '<a href="%s">%s</a>' % (
                            link, match.group(0))
                    elif editorial_view:
                        replacement = '<span class="locus-not-found" title="%s not found" data-toggle="tooltip">%s</span>' % (
                            content_type, replacement)
                        # print replacement

                content = content[0:match.start(
                    0)] + replacement + content[match.end(0):]
                pos = match.start(0) + len(replacement)
            return content

        # locus -> reference to an image
        # e.g. 452r7 -> <a href="/digipal/image/<ID>">452r7</a>
        ret = replace_references(
            ret, ur'(?<!OF\s)\b(\d{1,4}(r|v))[^\s;,\]<]*', loci, 'Image')

        ret = re.sub(
            ur'<span data-dpt="ref" data-dpt-target="([^"]+)">([^<]+)</span>', ur'<a href="\1">\2</a>', ret)

        # <span data-dpt-model="hand" data-dpt="record">theta</span>
        ret = replace_references(
            ret, ur'(?:<span[^>]*data-dpt-model="hand"[^>]*>)([^<]+)(?:</span>)', hands, 'Hand')

        # <span data-dpt-model="graph" data-dpt="record">#10</span>
        ret = replace_references(
            ret, ur'(?:<span[^>]*data-dpt-model="graph"[^>]*>)([^<]+)(?:</span>)', {}, 'Annotation')

        ip = self.hand.item_part
        if ip:
            {'key': 'repo_city', 'label': 'Repository City', 'path': 'annotation.image.item_part.current_item.repository.place.name',
                'count': True, 'search': True, 'viewable': True, 'type': 'title'},
            {'key': 'repo_place', 'label': 'Repository Place', 'path': 'annotation.image.item_part.current_item.repository.human_readable',
                'path_result': 'annotation.image.item_part.current_item.repository.name', 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
            {'key': 'shelfmark', 'label': 'Shelfmark', 'path': 'annotation.image.item_part.current_item.shelfmark',
                'search': True, 'viewable': True, 'type': 'code'},

            # char
            link = ur'/digipal/search/facets/?sort=locus&hand_label=%s&repo_city=%s&repo_place=%s&shelfmark=%s&character=\2&img_is_public=1&page=1&result_type=graphs&view=list' % (
                self.hand.label, ip.current_item.repository.place.name, ip.current_item.repository.human_readable(), ip.current_item.shelfmark)
            ret = re.sub(ur'(<span[^>]*data-dpt-model="character"[^>]*>)([^<]+)(</span>)',
                         ur'<a href="' + link + ur'">\1\2\3</a>', ret)
            #/digipal/search/facets/?sort=locus&hand_label=iota&character=s&img_is_public=1&page=1&%40xp_result_type=1&result_type=graphs&view=list

        return ret

    def save(self, *args, **kwargs):
        self.description = re.sub('<p>&nbsp;</p>', '', self.description)
        return super(HandDescription, self).save(*args, **kwargs)

    def __unicode__(self):
        # return u'%s %s' % (self.historical_item, self.source)
        return get_list_as_string(self.hand, ' ', self.source)


class Alphabet(models.Model):
    name = models.CharField(max_length=128, unique=True)
    ontographs = models.ManyToManyField(Ontograph, blank=True)
    hands = models.ManyToManyField(Hand, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % (self.name)


# DateEvidence in legacy db
class DateEvidence(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    hand = models.ForeignKey(Hand, blank=True, null=True, default=None)
    historical_item = models.ForeignKey(
        'HistoricalItem', related_name='date_evidences', blank=True, null=True, default=None)
    date = models.ForeignKey(Date, blank=True, null=True)

    # is this a firm date (i.e. undisputed)
    is_firm_date = models.BooleanField(null=False, default=False)
    # transcription of the date from a reference
    date_description = models.CharField(max_length=128, blank=True, null=True)
    # the bibliographical reference of the date
    reference = models.ForeignKey(Reference, blank=True, null=True)
    # explanation for the date
    evidence = models.TextField(
        max_length=255, blank=True, null=True, default='')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['date']

    def __unicode__(self):
        # return u'%s. %s. %s' % (self.hand, self.date, self.date_description)
        return get_list_as_string(
            self.hand, '. ', self.date, '. ', self.date_description)


class Graph(models.Model):
    idiograph = models.ForeignKey(Idiograph)
    hand = models.ForeignKey(Hand, related_name='graphs')
    aspects = models.ManyToManyField(Aspect, blank=True)
    display_label = models.CharField(max_length=256, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)
    group = models.ForeignKey('Graph', related_name='parts', blank=True,
                              null=True, help_text=u'Select a graph that contains this one')

    @staticmethod
    def get_definition():
        return u'''A single instance of a given sign written on the page'''

    class Meta:
        ordering = ['idiograph']

    def __unicode__(self):
        return u'%s' % (self.display_label)

    def get_aspect_positions(self):
        ret = []
        for a in self.aspects.all():
            name = re.sub(ur'(?i)Position\s*:\s*', ur'', a.name)
            if name != a.name:
                ret.append(name)
        return ret or ['unspecified']

    def get_short_label(self):
        return self.get_label(
            pattern=settings.ARCHETYPE_ANNOTATION_TOOLTIP_SHORT)

    def get_long_label(self):
        return self.get_label(
            pattern=settings.ARCHETYPE_ANNOTATION_TOOLTIP_LONG)

    def get_label(
            self, pattern=ur'{allograph} by {hand}\n {ip}, {locus}\n ({hi_date})'):
        '''Return a label by sustituting the fields in the given pattern.
           Error during susbtitution goes to std out and generate UPPERcase field in label.
           Unkown field names are left untouched.
           See setting.ARCHETYPE_ANNOTATION_TOOLTIP_*
        '''

        ret = unicode(pattern).decode('unicode_escape')

        def get_field(match):
            r = match.group(0)
            key = match.group(1)
            try:
                if key == 'allograph':
                    r = self.idiograph.allograph
                if key == 'hand':
                    r = self.hand
                if key == 'locus':
                    r = self.annotation.image.locus
                if key == 'public_note':
                    r = dputils.get_plain_text_from_html(
                        self.annotation.display_note or '')
                if key == 'ip':
                    r = self.annotation.image.item_part
                if key == 'hi_date':
                    r = self.annotation.image.item_part.historical_item.date
                if key == 'text_date':
                    r = ur''
                    text = self.annotation.image.item_part.historical_item.get_first_text()
                    if text:
                        r = text.date
                if key == 'desc':
                    r = (self.get_description_as_str() or u'')
            except Exception as e:
                print 'EXCEPTION: graph.get_label() => "%s"' % e
                r = r.upper()
            return ur'%s' % r

        ret = re.sub(ur'\{([^}]+)\}', get_field, ret)

        return ret

    def save(self, *args, **kwargs):
        #self.display_label = u'%s. %s' % (self.idiograph, self.hand)
        self.display_label = get_list_as_string(
            self.idiograph, '. ', self.hand)
        super(Graph, self).save(*args, **kwargs)

    def get_absolute_url(self):
        ret = '/'
        # TODO: try/catch for missing annotation

        if hasattr(self, 'annotation'):
            ret = self.annotation.get_absolute_url()
        return ret

    def get_description_as_array_str(self):
        ret = OrderedDict()
        for c in self.graph_components.all().order_by('component__name'):
            for f in c.features.all().order_by('name'):
                ret[u'%s: %s' % (c.component.name, f.name)] = 1
        return ret.keys()

    def get_description_as_str(self):
        return u', '.join(self.get_description_as_array_str())

    def get_serialised_description(self):
        ret = []
        for c in self.graph_components.all():
            for f in c.features.all():
                ret.append(u'%s_%s' % (c.component.id, f.id))
        return u' '.join(ret)

    def get_component_feature_labels(self):
        return self.get_description_as_array_str()
#         ret = []
#
#         for c in self.graph_components.all():
#             for f in c.features.all():
#                 ret.append(u'%s: %s' % (c.component.name, f.name))
#
#         return ret


class GraphComponent(models.Model):
    graph = models.ForeignKey(Graph, related_name='graph_components')
    component = models.ForeignKey(Component)
    features = models.ManyToManyField(Feature)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['graph', 'component']

    def __unicode__(self):
        return u'%s. %s' % (self.graph, self.component)


class Status(models.Model):
    name = models.CharField(max_length=32, unique=True)
    default = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Status'

    def __unicode__(self):
        return u'%s' % (self.name)


class AnnotationQuerySet(models.query.QuerySet):
    def editorial(self):
        '''returns only annotations which don't have a graph'''
        return self.filter(type='editorial')

    def with_graph(self):
        '''returns only annotations which have a graph'''
        return self.filter(graph_id__gt=0)

    def publicly_visible(self):
        '''returns only annotations which have either a graph or a display note'''
        return self.filter(Q(graph__isnull=False) | ~(
            Q(display_note__exact='') | Q(display_note__isnull=True)))

    def exclude_hidden(self, include_hidden=False):
        '''Don't return the annotations where allograph.hidden=True.
            Unless include_hidden=True.
        '''
        ret = self
        if not include_hidden:
            ret = self.exclude(graph__idiograph__allograph__hidden=True)
        return ret


class AnnotationManager(models.Manager):
    def get_queryset(self):
        return AnnotationQuerySet(self.model, using=self._db)


class Annotation(models.Model):
    # TODO: to remove
    #page = models.ForeignKey(Image, related_name='to_be_removed')
    image = models.ForeignKey(Image, null=True, blank=False)
    # WARNING: this value is derived from geo_json on save()
    # No need to change it directly
    # GN: 23/9/16: shouldn't use it at all anymore
    cutout = models.CharField(
        max_length=256, null=True, blank=True, default=None)
    # This is the rotation in degree applied to the cut-out to show it in the right orientation.
    # Note that it does not affect the shape of the annotation box, only the
    # rendering of the cut out.
    rotation = models.FloatField(blank=False, null=False, default=0.0)
    status = models.ForeignKey(Status, blank=True, null=True)
    before = models.ForeignKey(Allograph, blank=True, null=True,
                               related_name='allograph_before')
    graph = models.OneToOneField(Graph, blank=True, null=True)
    after = models.ForeignKey(Allograph, blank=True, null=True,
                              related_name='allograph_after')
    # GN: try avoid using this field as it may not be useful anymore
    # Use the record id instead
    vector_id = models.TextField(blank=True, null=False, default=u'')
    geo_json = models.TextField()
    display_note = HTMLField(
        blank=True, null=True, help_text='An optional note that will be publicly visible on the website.')
    internal_note = HTMLField(
        blank=True, null=True, help_text='An optional note for internal or editorial purpose only. Will not be visible on the website.')
    author = models.ForeignKey(User, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(
        auto_now=True, editable=False)
    holes = models.CharField(max_length=1000, null=True, blank=True)
    # GN: A temporary id set on the client side.
    # Used ONLY until the id of the new record has been returned to the client.
    clientid = models.CharField(
        max_length=24, blank=True, null=True, db_index=True)
    # 'text' for text annotation; ('editorial' for editorial annotation, not used yet)
    type = models.CharField(max_length=15, blank=True,
                            null=True, db_index=True, default=None)

    objects = AnnotationManager()

    class Meta:
        ordering = ['graph', 'modified']
        #unique_together = ('image', 'vector_id')

    def __unicode__(self):
        return get_list_as_string(self.graph, ' in ', self.image)

    @property
    def is_editorial(self):
        '''Returns True only if the annotation has no graph attached to it'''
        return bool(self.graph)

    @property
    def is_publicly_visible(self):
        return self.display_note or self.graph_id

    def get_absolute_url(self):
        ret = '/'
        # TODO: change to ID instead of vector id!
#         if self.image and self.vector_id:
#             ret = u'/digipal/page/%s/?vector_id=%s' % (self.image.id, self.vector_id)
        if self.image and self.graph:
            ret = u'/digipal/page/%s/?graph=%s' % (
                self.image.id, self.graph.id)
        return ret

    def get_geo_json_as_dict(self, geo_json_str=None):
        import json
        # See JIRA-229, some old geo_json format are not standard JSON
        # and cause trouble with the deserialiser (json.loads()).
        # The property names are surrounded by single quotes
        # instead of double quotes.
        # simplistic conversion but in our case it works well
        # e.g. {'geometry': {'type': 'Polygon', 'coordinates':
        #     Returns {"geometry": {"type": "Polygon", "coordinates":
        ret = {}
        if not geo_json_str:
            geo_json_str = self.geo_json
        if geo_json_str:
            geo_json_str = geo_json_str.replace('\'', '"')
            ret = json.loads(geo_json_str)
        return ret

    def correct_geometry(self, geo_json):
        if 'geometry' in geo_json:
            dims = self.image.dimensions()
            for point in geo_json['geometry']['coordinates'][0]:
                if point[1] < 0:
                    point[1] += dims[1]

    def set_geo_json_from_dict(self, geo_json):
        import json
        self.geo_json = json.dumps(geo_json)

    def get_shape_path(self, geo_json_str=None):
        ret = [[0, 0]]
        geo_json = self.get_geo_json_as_dict(geo_json_str)
        if 'geometry' in geo_json:
            ret = geo_json['geometry']['coordinates'][0][:]
        return ret

    def set_shape_path(self, path=[]):
        geo_json = self.get_geo_json_as_dict()
        # TODO: test if this exists!
        geo_json['geometry']['coordinates'][0] = path
        self.set_geo_json_from_dict(geo_json)

    def get_coordinates(self, geo_json_str=None,
                        y_from_top=False, rotated=False):
        ''' Returns the coordinates of the smallest rectangle
            that contain the path around the annotation shape.
            E.g. ((602, 56), (998, 184))

            WARNING: the y coordinates are relative to the BOTTOM of the image!
        '''

        def get_surrounding_rectangle(cs):
            ret = [
                [min([c[0] for c in cs]),
                 min([c[1] for c in cs])],
                [max([c[0] for c in cs]),
                 max([c[1] for c in cs])]
            ]
            return ret

        cs = self.get_shape_path(geo_json_str)

        # TODO: need to get to the bottom of this
        # seem like OL3 returns negative Y coordinates (real one is positive
        # and top base)
        if cs[0][1] < 0:
            width, height = self.image.dimensions()
            for i in range(0, len(cs)):
                cs[i][1] = height + cs[i][1]

        # change the y coordinates (from the top rather than the bottom)
        if y_from_top:
            width, height = self.image.dimensions()
            # print width, height
            # print cs
            for i in range(0, len(cs)):
                cs[i][1] = height - cs[i][1]

        # rotate the shape
        if rotated:
            import math
            angle = math.radians(float(self.rotation))
            rect = get_surrounding_rectangle(cs)
            centre = [((rect[0][d] + rect[1][d]) / 2) for d in [0, 1]]
            for i in range(0, len(cs)):
                c = cs[i]
                c = [c[0] - centre[0], c[1] - centre[1]]
                c = (c[0] * math.cos(angle) - c[1] * math.sin(angle),
                     c[0] * math.sin(angle) + c[1] * math.cos(angle))
                c = [c[0] + centre[0], c[1] + centre[1]]
                cs[i] = c

        # get the surrounding rectangle
        ret = get_surrounding_rectangle(cs)

        return ret

    def set_graph_group(self):
        '''
            If the graph is contained within another
            This function will set self.group to that other graph.
            It also set self.holes: the holes to draw on the image thumbnail on the frontend.
            Modifications are directly saved to the DB, no need to call save().
        '''

        group = None
        min_dist = 1e6

        # Assumptions made:
        #    1. all regions are rectangles, no more complex shapes.
        #    2. nested graphs are saved after their parent graph.
        if self.graph:
            level = self.graph.idiograph.allograph.character.ontograph.nesting_level
            #
            # we search for another annotations with
            #     * nesting_level > self.graph....nesting_level
            #     * containing this annotation
            #
            # we keep only the annotation with the nearest top left corner
            #
            if level >= 1:
                coord = self.get_coordinates(y_from_top=True)
                lvl_field = 'graph__idiograph__allograph__character__ontograph__nesting_level'
                # for a in Annotation.objects.filter(image=self.image,
                # graph__idiograph__allograph__character__ontograph__nesting_level__range=(1,
                # level - 1)).values('graph_id', 'geo_json', lvl_field):
                for a in Annotation.objects.exclude(id=self.id).filter(
                        image=self.image, graph__idiograph__allograph__character__ontograph__nesting_level__gt=0).values('graph_id', 'geo_json', lvl_field):
                    a_coord = self.get_coordinates(
                        a['geo_json'], y_from_top=True)

                    # containment test
                    if coord[0][0] >= a_coord[0][0] and \
                            coord[0][1] >= a_coord[0][1] and \
                            coord[1][0] <= a_coord[1][0] and \
                            coord[1][1] <= a_coord[1][1]:

                        # top left corner distance
                        dist = abs(coord[0][0] - a_coord[0][0])
                        if dist < min_dist:
                            group = a
                            min_dist = dist

            if group:
                # now 'group' is the closest containing annotation
                if group[lvl_field] < level:
                    # nesting
                    # print '%s nested in %s' % (self.graph.id,
                    # group['graph_id'])
                    if group['graph_id'] != self.graph.group_id:
                        self.graph.group_id = group['graph_id']
                        self.graph.save()
                else:
                    # print '%s is a hole in %s' % (self.graph.id,
                    # group['graph_id'])
                    a_group = Annotation.objects.get(
                        graph_id=group['graph_id'])
                    a_group.set_hole(self.id, coord)
                    # print a_group.holes
                    a_group.save()

    def get_holes(self):
        import json
        return json.loads(self.holes or '{}')

    def set_hole(self, annotation_id, a_coord):
        import json
        holes = self.get_holes()
        coord = self.get_coordinates(y_from_top=True)
        #
        # convert the coordinates into relative offsets and lengths
        # [[781.818359375, 1889.2272949218996], [1805.818359375, 2929.2272949218996]]
        # =>
        # [offx, offy, lengthx, lengthy]
        #
        r_coord = [0, 0, 0, 0]
        r_coord[2] = coord[1][0] - coord[0][0]
        r_coord[3] = coord[1][1] - coord[0][1]
        r_coord[0] = (a_coord[0][0] - coord[0][0]) / r_coord[2]
        r_coord[1] = (a_coord[0][1] - coord[0][1]) / r_coord[3]
        r_coord[2] = (a_coord[1][0] - a_coord[0][0]) / r_coord[2]
        r_coord[3] = (a_coord[1][1] - a_coord[0][1]) / r_coord[3]
        holes[annotation_id] = r_coord
        self.holes = json.dumps(holes)

    def save(self, *args, **kwargs):
        if not self.geo_json:
            raise Exception(
                'Trying to save an annotation with an empty geo_json.')
            return

        return super(Annotation, self).save(*args, **kwargs)

    def get_cutout_url_info(self, esc=False, rotated=False, fixlen=None):
        # Returns cutout info about this annotation
        # as a dictionary.
        # If fixlen is None, the length is
        #  !!! between settings.ARCHETYPE_THUMB_LENGTH_MIN and settings.ARCHETYPE_THUMB_LENGTH_MAX
        # if fixlen is between 0 and 1, the length is fixlen * orginal size
        #
        ret = {'url': '', 'dims': [0, 0], 'frame_dims': [0, 0]}

        # get the rectangle surrounding the shape
        psr = ps = self.get_coordinates(y_from_top=True, rotated=False)

        rotation = float(self.rotation)
        if rotation > 0.0:
            psr = self.get_coordinates(y_from_top=True, rotated=True)
        # dims: full image dimensions
        dims = [float(v) for v in self.image.dimensions()]

        for d in [0, 1]:
            ret['frame_dims'][d] = psr[1][d] - psr[0][d]

        longest_dim = 0
        if ret['frame_dims'][1] > ret['frame_dims'][0]:
            longest_dim = 1

        if min(dims) <= 0 or min(ret['frame_dims']) <= 0:
            return ret

        if rotation > 0.0:
            # get the dimension of the region to retrieve
            # extend it by 50%
            extension = 0.5
            centre = [0, 0]
            for d in [0, 1]:
                ret['dims'][d] = (ps[1][d] - ps[0][d]) * (1 + extension * 2)
                centre[d] = (ps[0][d] + ps[1][d]) / 2

            # make it square
            ret['dims'] = [max(ret['dims']), max(ret['dims'])]
            ps[0] = [(centre[d] - ret['dims'][d] / 2) for d in [0, 1]]
        else:
            ret['dims'] = ret['frame_dims'][:]

        # turn it into a thumbnail (max len is settings.ARCHETYPE_THUMB_LENGTH_MAX)
        #factor = min(1.0, float(settings.ARCHETYPE_THUMB_LENGTH_MAX) / float(max(ret['frame_dims'])))
        if fixlen:
            if fixlen > 0 and fixlen <= 1:
                max_len = fixlen * max(ret['frame_dims'])
            else:
                max_len = fixlen
        else:
            max_len = float(settings.ARCHETYPE_THUMB_LENGTH_MAX)
            if getattr(settings, 'ARCHETYPE_THUMB_LENGTH_MIN',
                       settings.ARCHETYPE_THUMB_LENGTH_MAX) < settings.ARCHETYPE_THUMB_LENGTH_MAX:
                max_lens = [settings.ARCHETYPE_THUMB_LENGTH_MIN, max_len]
                max_len = min(max_lens[1], max_lens[0] + float(max_lens[1] - max_lens[0]) / float(
                    dims[longest_dim]) * ret['frame_dims'][longest_dim] * 1.25)
        factor = min(1.0, max_len / float(max(ret['frame_dims'])))

        # Diff btw IIPSrv 0.9 and 1.0. In 1.0, the WID is always the output WID.
        # Previosuly it was applied before RGN!
        wid = int(factor * dims[0])
        if settings.IMAGE_SERVER_VERSION >= 1.0:
            wid = ret['dims'][0] * factor

        ret['url'] = settings.IMAGE_SERVER_RGN % \
            (settings.IMAGE_SERVER_HOST, settings.IMAGE_SERVER_PATH, self.image.path(),
             'WID=%d' % wid,
             ps[0][0] / dims[0],
             ps[0][1] / dims[1],
             ret['dims'][0] / dims[0],
             ret['dims'][1] / dims[1])

        ret['url'] = Image.get_relative_or_absolute_url(ret['url'])

        for d in [0, 1]:
            ret['dims'][d] *= factor
            ret['frame_dims'][d] *= factor

        if esc:
            ret['url'] = escape(ret['url'])

        return ret

    def get_cutout_url(self, esc=False, full_size=False, fixlen=None):
        ''' Returns the URL of the cutout.
            Call this function instead of self.cutout, see JIRA 149.
            If esc is True, special chars are turned into entities (e.g. & -> &amp;)
            full_size: deprecated
        '''
        return self.get_cutout_url_info(
            esc=esc, rotated=False, fixlen=fixlen)['url']

    def thumbnail(self):
        ''' returns HTML of an image inside a span'''
        from templatetags.html_escape import annotation_img
        return annotation_img(self, lazy=1)

    thumbnail.short_description = 'Thumbnail'
    thumbnail.allow_tags = True

    def thumbnail_with_link(self):
        return mark_safe(u'<a href="%s">%s</a>' %
                         (self.get_absolute_url(), self.thumbnail()))

    thumbnail_with_link.short_description = 'Thumbnail'
    thumbnail_with_link.allow_tags = True

#     def __unicode__(self):
#         return u'%s' % (self.name)

# PlaceEvidence in legacy db


class PlaceEvidence(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    hand = models.ForeignKey(Hand, blank=True, null=True, default=None)
    historical_item = models.ForeignKey(
        HistoricalItem, blank=True, null=True, default=None)
    place = models.ForeignKey(Place)
    written_as = models.CharField(max_length=128, blank=True, null=True)
    place_description = models.CharField(max_length=128, blank=True, null=True)
    reference = models.ForeignKey(Reference)
    evidence = models.TextField()
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['place']

    def __unicode__(self):
        # return u'%s. %s. %s' % (self.hand, self.place, self.reference)
        return get_list_as_string(
            self.hand, '. ', self.place, '. ', self.reference)


# MeasurementText in legacy db
class Measurement(models.Model):
    legacy_id = models.IntegerField(blank=True, null=True)
    label = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
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
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    class Meta:
        ordering = ['hand', 'measurement']

    def __unicode__(self):
        # return u'%s. %s' % (self.hand, self.measurement)
        return get_list_as_string(self.hand, '. ', self.measurement)


class CarouselItem(models.Model):
    link = models.CharField(max_length=200, blank=True, null=True,
                            help_text='The URL of the page this item links to. E.g. /digipal/page/80/')
    image_file = models.ImageField(upload_to=settings.UPLOAD_IMAGES_URL, blank=True, null=True, default=None,
                                   help_text='The image for this item. Not needed if you have provided a the URL of the image in the image field.')
    image = models.CharField(max_length=200, blank=True, null=True,
                             help_text='The URL of the image of this item. E.g. /static/digipal/images/Catholic_Homilies.jpg. Not needed if you have uploaded a file in the image_file field.')
    image_alt = models.CharField(max_length=300, blank=True, null=True,
                                 help_text='a few words describing the image content.')
    image_title = models.CharField(max_length=300, blank=True, null=True,
                                   help_text='the piece of text that appears when the user moved the mouse over the image (optional).')
    sort_order = models.IntegerField(
        help_text='The order of this item in the carousel. 1 appears first, 2 second, etc. 0 is hidden.')
    title = models.CharField(
        max_length=300, help_text='The caption under the image of this item. This can contain some inline HTML. You can surround some text with just <a>...</a>.')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    @staticmethod
    def get_visible_items():
        '''Returns the visible carousel slides/items in the correct display order'''
        ret = CarouselItem.objects.filter(
            sort_order__gt=0).order_by('sort_order')
        return ret

    def title_with_link(self):
        '''Returns the item title with a correct hyperlink
            The HTML is marked safe and the links are properly escaped (e.g. &amp;)
            so no further trasnform is needed in the template.
        '''
        ret = self.title
        if ret.find('<a>') == -1:
            ret = '<a href="%s">%s</a>' % (escape(self.link), ret)
        else:
            ret = ret.replace('<a>', '<a href="%s">' % escape(self.link))
        return mark_safe(ret)


class ContentAttribution(models.Model):
    title = models.CharField(
        max_length=128,
        help_text='A unique shorthand/label for this attribution',
        unique=True,
    )
    message = HTMLField(
        blank=True, null=True,
        help_text="Shown under the text in the Text Viewer. Please don't exceed six words."
    )
    short_message = HTMLField(
        blank=True,
        null=True,
        help_text="Shown under the text in the Text Viewer. Please don't exceed six words."
    )

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True,
                                    editable=False)

    def __unicode__(self):
        return self.title

    def get_short_message(self):
        ret = self.short_message or ''

        ret = re.sub(ur'</?(p|div)\b[^>]*>', ur'', ret)
        ret = re.sub(ur'(<a)\b', ur'\1 target="_blank" ', ret)

        return ret


# Import of Stewart's database
class StewartRecord(models.Model):
    scragg = models.CharField(
        max_length=300, null=True, blank=True, default='')
    repository = models.CharField(
        max_length=300, null=True, blank=True, default='')
    shelf_mark = models.CharField(
        max_length=300, null=True, blank=True, default='')
    stokes_db = models.CharField(
        max_length=300, null=True, blank=True, default='')
    fols = models.CharField(max_length=300, null=True, blank=True, default='')
    gneuss = models.CharField(
        max_length=300, null=True, blank=True, default='')
    ker = models.CharField(max_length=300, null=True, blank=True, default='')
    sp = models.CharField(max_length=300, null=True, blank=True, default='')
    ker_hand = models.CharField(
        max_length=300, null=True, blank=True, default='')
    locus = models.CharField(max_length=300, null=True, blank=True, default='')
    selected = models.CharField(
        max_length=300, null=True, blank=True, default='')
    adate = models.CharField(max_length=300, null=True, blank=True, default='')
    location = models.CharField(
        max_length=300, null=True, blank=True, default='')
    surrogates = models.CharField(
        max_length=300, null=True, blank=True, default='')
    contents = models.CharField(
        max_length=500, null=True, blank=True, default='')
    notes = models.CharField(max_length=600, null=True, blank=True, default='')
    em = models.CharField(max_length=800, null=True, blank=True, default='')
    glosses = models.CharField(
        max_length=300, null=True, blank=True, default='')
    minor = models.CharField(max_length=300, null=True, blank=True, default='')
    charter = models.CharField(
        max_length=300, null=True, blank=True, default='')
    cartulary = models.CharField(
        max_length=300, null=True, blank=True, default='')
    eel = models.CharField(max_length=1000, null=True, blank=True, default='')
    import_messages = models.TextField(null=True, blank=True, default='')
    matched_hands = models.CharField(
        max_length=1000, null=True, blank=True, default='')

    class Meta:
        ordering = ['scragg']

    def __unicode__(self):
        ret = u'#%s' % self.id
        ids = self.get_ids()
        if ids:
            ret += u', %s' % ids
        return ret

    def set_matched_hands(self, matched_hands=[]):
        # format:
        #     ['h:HAND_ID','ip:IP_ID']
        if matched_hands:
            matched_hands = [hand for hand in matched_hands if re.match(
                ur'^(ip|h):\d+$', hand)]
        if matched_hands:
            import json
            self.matched_hands = json.dumps(matched_hands)
        else:
            self.matched_hands = u''
        return matched_hands

    def get_matched_hands(self):
        ret = []
        if self.matched_hands:
            import json
            ret = json.loads(self.matched_hands)
        return ret

    def get_matched_hands_objects(self):
        ret = []
        for match in self.get_matched_hands():
            rtype, rid = match.split(':')
            if rtype == 'h':
                ret.append(rid)

        ret = list(Hand.objects.filter(id__in=ret).order_by('id'))

        return ret

    def get_ids(self):
        ret = []
        if self.scragg:
            ret.append(u'Scr. %s' % self.scragg)
        if self.gneuss:
            ret.append(u'G. %s' % self.gneuss)
        if self.ker:
            ker = u'K. %s' % self.ker
            if self.ker_hand:
                ker += '.%s' % self.ker_hand
            ret.append(ker)
        if self.sp:
            aid = u''
            if not ('p' in self.sp.lower()):
                aid = u'S. '
            aid += self.sp
            ret.append(aid)
        if self.stokes_db:
            ret.append(u'L. %s' % self.stokes_db)
        return ', '.join(ret)

    def import_field(self, src_field, dst_obj, dst_field, append=False):
        ret = ''

        def normalise_value(value):
            if value is None:
                value = ''
            return (u'%s' % value).strip()

        src_value = normalise_value(getattr(self, src_field, ''))
        dst_value = normalise_value(getattr(dst_obj, dst_field, ''))

        if src_value:
            if (not append) or (dst_value.find(src_value) == -1):
                if (not append) and (dst_value and src_value != dst_value):
                    ret = u'Different values: #%s.%s = "%s" <> %s.#%s.%s = "%s"' % (
                        self.id, src_field, src_value, dst_obj.__class__.__name__, dst_obj.id, dst_field, dst_value)

                if not ret:
                    if append:
                        src_value = dst_value + '\n' + src_value
                    setattr(dst_obj, dst_field, src_value)
                    dst_obj.save()

        if ret:
            ret += '\n'

        return ret

    def import_related_object(self, hand, related_name,
                              related_model, related_label_field, value):
        ret = ''
        related_object = getattr(hand, related_name, None)
        if related_object:
            existing_value = getattr(related_object, related_label_field)
            if existing_value != value:
                ret = u'Different values for %s: already set to "%s", cannot overwrite it with "%s" (Brookes DB)\n' % (
                    related_name, existing_value, value)
            # else:
                #ret = u'Already set'
        else:
            # does it exists?
            query = {related_label_field + '__iexact': value.lower().strip()}
            related_objects = related_model.objects.filter(**query)
            if related_objects.count():
                # yes, just find it
                related_object = related_objects[0]
                #ret = u'Found %s' % related_object.id
            else:
                # no, then create it
                # but only if it does not have a ? at the end
                if value.strip()[-1] == '?':
                    ret = 'Did not set uncertain value for %s field: "%s" (Brookes DB)\n' % (
                        related_name, value)
                    if hand.internal_note:
                        hand.internal_note += '\n' + ret
                    else:
                        hand.internal_note = ret
                else:
                    query = {related_label_field: value.strip()}
                    related_object = related_model(**query)

                    if related_model == Date:
                        from utils import get_range_from_date
                        rng = get_range_from_date(value.strip())
                        related_object.min_weight = rng[0]
                        related_object.max_weight = rng[1]
                        related_object.weight = (
                            related_object.min_weight + related_object.max_weight) / 2
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

    @transaction.atomic
    def import_steward_record(self, single_hand=None):
        '''
            [DONE] ker -> ItemPart_HistoricalItem_CatalogueNumbers(Source.name='ker')
            [DONE] sp ->

            # hand number
            [DONE] scragg -> hand.scragg
            [DONE] Locus -> hand.+locus
            [DONE] Selected -> Page
                * (Use this to generate a new Page record)
            [DONE] Notes      Hand.InternalNote

            [DONE] ker_hand -> Missing. Use description + Source model. [this is only a hand number, why saving this as a desc?]
            [DONE] Contents      Scragg_Description
            [DONE] EM      Hand.EM_Description (Use description + Source model.)
            [DONE] EEL      MISSING. Use Description + Source model

            # Format is too messy to be imported into the catalogue num
            # we import it into the surrogates field and add a filter
            [DONE~] Surrogates      Use Source Model

            [DONE] Glosses      Hand.GlossOnly
            [DONE] Minor      Hand.ScribbleOnly

            TODO:
            [TEST] Date                  Hand.AssignedDate
            [TEST] Location              Hand.AssignedPlace

            Charter: empty
            Image URL: not in the import file
            UCLA online: not in the import file
            cartulary: empty

        '''
#         if single_hand:
#             hands = [single_hand]
#         else:
#             matches = self.get_matched_hands()
#         if not hands:
#             return

        from datetime import datetime
        now = datetime.now()

        matched_hands = []

        for match in self.get_matched_hands():

            rtype, rid = match.split(':')

            hand = None
            if rtype == 'h':
                hand = Hand.objects.get(id=rid)
            if rtype == 'ip':
                hand = Hand(item_part=ItemPart.objects.get(
                    id=rid), num='10000', label="Hand")
                hand.internal_note = (
                    hand.internal_note or '') + '\nNew Hand created from Brookes record #%s' % self.id
                hand.save()

            matched_hands.append(u'h:%s' % hand.id)

            new_label = ''
            if rtype == 'ip':
                new_label = 'NEW '
            messages = u'[%s] IMPORT record #%s into %shand #%s.\n' % (
                now.strftime('%d-%m-%Y %H:%M:%S'), self.id, new_label, hand.id)

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

            # scragg
            hand.set_description(Source.get_source_from_keyword(
                'scragg').name, self.contents)
            # eel
            hand.set_description(
                Source.get_source_from_keyword('eel').name, self.eel)
            # em1060-1220
            hand.set_description(Source.get_source_from_keyword(
                'english manuscripts').name, self.em)

            # 3. Related objects

            # 3470
            # TODO: import by creating a new date?
            ##messages += self.import_field('adate', hand, 'assigned_date')
            # TODO: import by creating a new place?
            if self.location:
                messages += self.import_related_object(
                    hand, 'assigned_place', Place, 'name', self.location)
            if self.adate:
                messages += self.import_related_object(hand, 'assigned_date', Date, 'date', re.sub(
                    ur'\s*(?:' + u'\xd7' + ur'|x)\s*', u'\xd7', self.adate))

            # 4. Catalogue numbers
            # Ker, S/P (NOT Scragg, b/c its a hand number)
            if self.ker or self.sp:
                def add_catalogue_number(
                        historical_item, source_keyword, number):
                    if number and number.strip():
                        number = number.strip()
                        source = Source.get_source_from_keyword(source_keyword)
                        if not CatalogueNumber.objects.filter(
                                source=source, number__iexact=number, historical_item=historical_item):
                            CatalogueNumber(
                                source=source, number=number, historical_item=historical_item).save()

                historical_item = hand.item_part.historical_item

                add_catalogue_number(historical_item, 'ker', self.ker)

                if self.sp:
                    source_dp = settings.SOURCE_SAWYER_KW
                    document_id = self.sp
                    document_id_p = re.sub(
                        '(?i)^\s*p\s*(\d+)', r'\1', document_id)
                    if document_id_p != document_id:
                        document_id = document_id_p
                        source_dp = 'pelteret'

                    add_catalogue_number(
                        historical_item, source_dp, document_id)

            if self.import_messages is None:
                self.import_messages = u''
            if self.import_messages:
                self.import_messages += u'\n'
            self.import_messages += messages

        self.set_matched_hands(matched_hands)
        self.save()


class RequestLog(models.Model):
    request = models.CharField(
        max_length=300, null=True, blank=True, default='')
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


import json


class KeyVal(models.Model):
    #
    # A simple key-value table for ad hoc data that don't need their own dedicated table
    # use get() and set() class methods to access entries
    #
    key = models.CharField(max_length=300, null=False,
                           blank=False, unique=True)
    val = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(
        auto_now=True, editable=False)

    class Meta:
        ordering = ['key', ]

    def __unicode__(self):
        return u'%s' % (self.key)

    @classmethod
    def getjs(cls, key, default=None):
        notfound = '##NOTFOUND##'
        ret = cls.get(key, notfound)
        if ret == notfound:
            ret = default
        else:
            ret = dputils.json_loads(ret)

        return ret

    @classmethod
    def setjs(cls, key, val):
        cls.set(key, dputils.json_dumps(val))

    @classmethod
    def get(cls, key, default=None):
        ret = default
        keyval = cls.objects.filter(key=key).first()
        if keyval:
            ret = keyval.val
        return ret

    @classmethod
    def set(cls, key, val):
        keyval, created = cls.objects.get_or_create(key=key)
        if val != keyval.val:
            keyval.val = val
            keyval.save()


class ApiTransform(models.Model):
    title = models.CharField(max_length=30, blank=False, null=False,
                             help_text='A unique title for this XSLT template.', unique=True)
    slug = models.SlugField(max_length=30, blank=False, null=False,
                            help_text='A unique code to refer to this template when using the web API. @xslt=slug', editable=False, unique=True)
    template = models.TextField(
        blank=True, null=True, help_text='Your XSLT template')
    description = models.TextField(
        blank=True, null=True, help_text='A description of the transform')
    mimetype = models.CharField(max_length=30, blank=False, null=False,
                                help_text='The mime type of the output from the transform.', default='text/xml')
    sample_request = models.CharField(max_length=200, blank=True, null=True,
                                      help_text='A sample API request this transform can be tested on. It is a API request URL without this part: http://.../digipal/api/. E.g. graph/100,101,102?@select=id,str', default='graph')
    webpage = models.BooleanField(
        default=False, null=False, blank=False, verbose_name='Show as a webpage?')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(
        auto_now=True, editable=False)

    class Meta:
        ordering = ['title']

    def clean(self):
        from django.utils.text import slugify
        self.slug = slugify(self.title)

    def get_absolute_url(self):
        ret = '/digipal/api/' + self.sample_request
        if '?' not in ret:
            ret += '?'
        ret += '&@xslt=' + self.slug
        return ret

    def __unicode__(self):
        return u'%s' % (self.title)


# Generate a meaningful object label for the m2m models
HistoricalItem.owners.through.__unicode__ = lambda self: unicode(
    self.historicalitem)

ItemPart.owners.through.__unicode__ = lambda self: unicode(self.itempart)

CurrentItem.owners.through.__unicode__ = lambda self: unicode(self.currentitem)

# Assign get_absolute_url() and get_admin_url() for all models
# get_absolute_url() returns /digipal/MODEL_PLURAL/ID
# E.g. /digipal/scribes/101
#
# model.get_absolute_url() is created only if model.has_absolute_url = True
#


def set_additional_models_methods():

    def model_get_absolute_url(self):
        from utils import plural
        # get custom label if defined in _meta, otehrwise stick to module name
        if self._meta.model_name in ['currentitem']:
            return None
        webpath_key = getattr(self, 'webpath_key',
                              plural(self._meta.model_name, 2))
        ret = '/%s/%s/%s/' % (self._meta.app_label,
                              webpath_key.lower(), self.id)
        return ret

    def model_get_admin_url(self):
        # get_admin_url
        from django.core.urlresolvers import reverse
        info = (self._meta.app_label, self._meta.model_name)
        ret = reverse('admin:%s_%s_change' % info, args=(self.pk,))
        return ret

    for attribute in globals().values():
        # Among all the symbols accessible here, filter the Model defined in
        # this module
        if isinstance(attribute, type) and issubclass(attribute,
                                                      models.Model) and attribute.__module__ == __name__:
            if (not hasattr(attribute, 'get_absolute_url')) and getattr(
                    attribute, 'has_absolute_url', False):
                attribute.get_absolute_url = model_get_absolute_url
            attribute.get_admin_url = model_get_admin_url


set_additional_models_methods()

admin_patches()
whoosh_patches()
