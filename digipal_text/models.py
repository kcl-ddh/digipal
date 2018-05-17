from django.db import models
from mezzanine.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
import os
import re
import string
import unicodedata
import cgi
from django.utils.html import conditional_escape, escape
import logging
import digipal.models
from django.contrib.auth.models import User
from digipal.utils import dplog
from django.utils.text import slugify


class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

# TODO: use QuerySet so more in line with Django design
# TODO: support for QS reuse


class TextUnits(object):
    '''Abstract Class that behaves like a Django Model Manager
       for units of text in a TextContentXML

       Some functions work like Django QS.
       Specifically the use of iterator(), e.g.:

       objs = TextUnit.objects.all()
       a) for r in objs
       b) for r in objs.iterator()

       a) will read everything at once (+MEM) and cache it (-TIME)
       b) will read one record at a time (-MEM), another call will redo it (+TIME)
    '''

    def __init__(self):
        # !!!
        # TODO: this is VERY inefficient if we call in_bulk as we get all the records
        # We need to implement lazy loading instead
        self.options = {'select_related': [], 'prefetch_related': []}
        # this is our result cache, not always used (e.g. .iterator() bypasses
        # it)
        self.filters = {}
        self.recs = None
        self.all()

    def select_related(self, *args, **kwargs):
        self.options['select_related'] = args
        return self

    def prefetch_related(self, *args, **kwargs):
        self.options['prefetch_related'] = args
        return self

    def load_records_iter(self):
        # to be overridden
        return (r for r in [])

    def __iter__(self):
        # NOT RECOMMENDED!
        if self.get_bulk_ids() is None:
            dplog(
                'TextUnit.__iter__() called for ALL UNITS. Use .iterator() instead.', 'WARNING')
        else:
            dplog('TextUnit.__iter__() called', 'INFO')

        ret = []

        if self.recs is None:
            ret = self.recs = list(self.iterator())

        return ret.__iter__()

    def in_bulk(self, *args, **kwargs):
        # TODO: not necessarily reliable to access with args[0]
        # TODO: only get the requested units! Don't load everything.
        aids = self.options['aids'] = args[0]
        ret = {}
        for rec in self.iterator():
            if rec.id in aids:
                ret[rec.id] = rec
        return ret

    def in_bulk_any_type(self, *args, **kwargs):
        '''Works like in_bulk() but the ids passed to the function
            have a prefix with the type of the TextUnit.
            e.g. ['Clause:11:address', 'Title:11:Sheriff']

            We assumed that there are no clashes in IDs among different
            types of units. 11:address will never be another type than Clause.
        '''
        from digipal.views.faceted_search.settings import FacettedType

        aids = self.options['aids'] = args[0]

        # split into types {'Clause': ['11:address']}
        models = {}
        for maid in aids:
            maid = maid.split(':')
            if maid[0] not in models:
                models[maid[0]] = []
            models[maid[0]].append(':'.join(maid[1:]))

        ret = {}
        for name, ids in models.iteritems():
            ct = FacettedType.fromModelName(name)
            if not ct:
                continue
            model = ct.getModelClass()
            if not model:
                continue
            recs = model.objects.in_bulk(ids)
            ret.update(recs)
        return ret

    def iterator(self, *args, **kwargs):
        return self.load_records_iter()

    def get_bulk_ids(self):
        return self.options.get('aids', None)

    def count(self, *args, **kwargs):
        # Note that this may be VERY inefficient
        if self.recs:
            return len(self.recs)
        else:
            return sum((1 for r in self.iterator()))

    def all(self, *args, **kwargs):
        self.options['ais'] = None
        return self

    def get_content_xmls(self):
        # returns content_xml objects the units can be drawn from
        # can apply filters passed to the filter() method
        # e.g. .filter(content_xml__id=4)
        ret = TextContentXML.objects.all()
        filters = {}
        for path, value in self.filters.iteritems():
            if path.startswith('content_xml'):
                filters[re.sub(ur'content_xml_*', '', path)] = value
        if filters:
            ret = ret.filter(**filters)
        return ret

    def filter(self, *args, **kwargs):
        # kwarg = {'content_xml__id': 4}
        if args or kwargs:
            if args:
                raise Exception('filter(args) is not yet supported')
            unrecognised_paths = [path for path in kwargs.keys(
            ) if not path.startswith('content_xml')]
            if unrecognised_paths:
                raise Exception('filter() is not yet supported for following filters: %s' % ', '.join(
                    unrecognised_paths))
            else:
                self.filters.update(kwargs)
        return self

    def order_by(self, *args, **kwargs):
        return self


class TextUnit(object):
    '''Abstract Class that behaves like a Django Model
       for a unit of text in a TextContentXML
    '''

    def __init__(self, units=None):
        self.units = units

    @property
    def id(self):
        return ur'%s:%s' % (self.content_xml.id, self.unitid)

    def get_absolute_url(self, qs=None, metas=None,
                         location_type=None, location=None):
        # TODO: fix it, broken for EXON b/c url now contains more specific info and # fragment
        # return '%s/entry/%s/' % (self.content_xml.get_absolute_url(),
        # self.unitid)
        return '%s' % self.content_xml.get_absolute_url(
            qs=qs, metas=metas, location_type=location_type, location=location)

    def get_thumb(self, request=None):
        '''Returns the Annotation object for this TextUnit.
        If request <> None AND the user has no permission on the image,
            returns None
        '''
        from digipal.models import Annotation
        ret = Annotation.objects.filter(image__item_part=self.content_xml.text_content.item_part,
                                        textannotations__elementid=self.get_elementid()).first()

        # returns None if request user doesn't have permission
        if request and ret and ret.image.is_private_for_user(request):
            ret = None

        return ret

    def get_plain_content(self):
        from digipal import utils as dputils
        return dputils.get_plain_text_from_xmltext(self.content)

    def get_label(self):
        return 'Text unit %s' % self.unitid

    def get_text_annotationid(self):
        ta = TextAnnotation.objects.filter(
            annotation__image__item_part=self.content_xml.text_content.item_part, elementid=self.get_elementid()).first()
        return ta.id if ta else None

    @ClassProperty
    @classmethod
    def objects(cls, *args, **kwargs):
        return TextUnits()


class TextContentType(digipal.models.NameModel):
    class Meta:
        verbose_name = 'Text Type'
        verbose_name_plural = 'Text Types'


class TextContent(models.Model):
    languages = models.ManyToManyField(
        'digipal.Language', blank=True, related_name='text_contents')
    type = models.ForeignKey(
        'TextContentType', blank=False, null=False, related_name='text_contents')
    item_part = models.ForeignKey(
        'digipal.ItemPart', blank=False, null=False, related_name='text_contents')
    text = models.ForeignKey('digipal.Text', blank=True,
                             null=True, related_name='text_contents')
    attribution = models.ForeignKey(
        'digipal.ContentAttribution', blank=True, null=True
    )

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = ('item_part', 'type')
        verbose_name = 'Text (meta)'
        verbose_name_plural = 'Texts (meta)'

    def get_string_from_languages(self):
        return u', '.join([l.name for l in self.languages.all()])

    def __unicode__(self):
        ret = u'New TextContent record'
        if self.pk:
            info = unicode(self.type)
            languages = self.get_string_from_languages()
            if languages:
                info += u', %s' % languages

            ret = u'%s (%s)' % (self.item_part, info)

        return ret

    def get_absolute_url(self, unset=False, qs='', metas=None,
                         location_type=None, location=None, content_types=None):
        '''
            Returns the url to view this text content.
            unset: if True the panels types and content are unspecified
            qs: a partial query string to be added to the url
            metas: additional settings for the main panel (e.g. 'k1=v1;k2=v2')
            content_types: list of content_types (e.g. transcription) to display in the panels
        '''
        types = (content_types or ['transcription', 'translation'])
        ret = u'%stexts/view/' % self.item_part.get_absolute_url()
        if not unset:
            ret += '?' if ('?' not in ret) else '&'
            ret += 'center=%s/sync/location' % self.type.slug
            if 0 and location_type:
                ret += '/%s' % location_type
                if location:
                    ret += '/%s' % location
            #ret += '/'
            if 0 and metas:
                from digipal.utils import urlencode
                ret += (';' + urlencode(metas, True)).replace('=', ':')
            #ret += '&east=%s/sync/%s/' % (set(types).difference(set([self.type.slug])).pop(), self.type.slug)
            #ret += '&north=image/sync/%s/' % self.type.slug
            ret += '&east=%s/sync/location' % set(
                types).difference(set([self.type.slug])).pop()
            ret += '&north=image/sync/location'
        if location_type:
            ret += '?' if ('?' not in ret) else '&'
            ret += 'above=location/%s' % location_type
            if location:
                ret += '/%s' % location
            if metas:
                from digipal.utils import urlencode
                ret += (';' + urlencode(metas, True)).replace('=', ':')
        if qs:
            ret += '?' if ('?' not in ret) else '&'
            if qs[0] in ['&', '?']:
                qs = qs[1:]
            ret += qs
        # ret += '#text-viewer'
        return ret
    # http://localhost/digipal/manuscripts/598/texts/view/?center=transcription;subl:%5B%5B%22%22%2C+%22clause%22%5D%2C+%5B%22type%22%2C+%22witnesses%22%5D%5D&east=translation/sync/transcription/&north=image/sync/transcription/#text-viewer
    # http://localhost/digipal/manuscripts/598/texts/view/?center=transcription;subl:%5B%5B%22%22,%22clause%22%5D,%5B%22type%22,%22witnesses%22%5D%5D;&east=translation/sync/transcription/;subl:%5B%5B%22%22,%22clause%22%5D,%5B%22type%22,%22witnesses%22%5D%5D;&north=image/sync/transcription/;subl:%5B%5B%22%22,%22clause%22%5D,%5B%22type%22,%22witnesses%22%5D%5D;olv:2,1860,-1385,0;#text-viewer


class TextContentXMLStatus(digipal.models.NameModel):
    sort_order = models.IntegerField(
        blank=False, null=False, default=0, help_text='The order of this status in your workflow.')

    class Meta:
        verbose_name = 'Text Status'
        verbose_name_plural = 'Text Statuses'


class TextContentXMLCopy(models.Model):
    source = models.ForeignKey(
        'TextContentXML', blank=True, null=True, related_name='versions')
    ahash = models.CharField(max_length=100, blank=True, null=True)
    content = models.BinaryField(blank=False, null=False)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = ('source', 'ahash',)
        verbose_name = 'Text Copy'
        verbose_name_plural = 'Text Copies'

    @classmethod
    def create_from_content_xml(cls, content_xml):
        '''Save a compressed copy of this content into the Copy table.
            If this is the same as an existing copy, do nothing and return that one.
        '''
        import hashlib
        content = content_xml.content.encode('utf-8')
        ahash = hashlib.sha224(content).hexdigest()

        # do nothing if the last copy is the same as this one
        copy = cls.objects.filter(ahash=ahash, source=content_xml).first()
        if not copy:
            # create a compressed copy
            import zlib
            content = zlib.compress(content, 9)
            copy = TextContentXMLCopy(
                source=content_xml, content=content, ahash=ahash)
            copy.save()

        return copy

    def get_uncompressed_content(self):
        ret = None
        if self.content and len(self.content) > 1:
            import zlib
            ret = zlib.decompress(self.content)
        return ret

    def restore(self):
        # first make a copy of the existing one
        self.source.save_copy()
        self.source.content = self.get_uncompressed_content()
        self.source.save()


class TextContentXML(models.Model):
    status = models.ForeignKey(
        'TextContentXMLStatus', blank=False, null=False, related_name='text_content_xmls')
    text_content = models.ForeignKey(
        'TextContent', blank=False, null=False, related_name='text_content_xmls')
    content = models.TextField(blank=True, null=True)
    last_image = models.ForeignKey(
        'digipal.Image', blank=True, null=True, related_name='text_content_xmls')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = ('text_content',)
        verbose_name = 'Text (XML)'
        verbose_name_plural = 'Texts (XML)'

    def __unicode__(self):
        return '%s (#%s)' % (self.text_content, self.id)

    @classmethod
    def get_public_only(cls, ignore=False):
        '''Return all the publicly accessible records.
           If ignore = True, returns all records, even private ones
        '''
        ret = cls.objects
        if not ignore:
            ret = ret.filter(status__slug__in=[
                             'live', 'published', 'public', 'online'])

        return ret

    def get_length(self):
        if not self.content:
            return 0
        return len(self.content)

    def save(self, *args, **kwargs):
        # initialise the status if undefined
        if not self.status_id:
            self.status = TextContentXMLStatus.objects.order_by(
                'sort_order').first()
        super(TextContentXML, self).save(*args, **kwargs)

    def get_absolute_url(self, unset=False, qs=None, metas=None,
                         location_type=None, location=None, content_types=None):
        return self.text_content.get_absolute_url(
            unset=unset, qs=qs, metas=metas, location_type=location_type, location=location, content_types=content_types)

    def save_copy(self):
        '''Save a compressed copy of this content into the Copy table'''
        TextContentXMLCopy.create_from_content_xml(self)

    def is_private(self):
        return self.status.slug not in [
            'live', 'published', 'public', 'online']

    # TODO: make this function overridable
    def convert(self):
        '''
        This method MUST remain idempotent, that is, converting a second or more
        times produces doesn't change the result from the previous conversion.

        It is called by the auto-convert button on the Text Editor to
        clean and mark-up editorial conventions. E.g. | => <br/>

        For specific projects, inherit this class and override this method.
        Keep generic conversion here.
        '''
        content = self.content

        self.content = content


class TextAnnotation(models.Model):
    annotation = models.ForeignKey(
        'digipal.Annotation', blank=False, null=False, related_name='textannotations')
    elementid = models.CharField(max_length=255, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = ['annotation', 'elementid']

    def __unicode__(self):
        return 'Annotation of "%s" in image "%s"' % (
            self.get_friendly_name(), self.annotation.image)

    def get_friendly_name(self):
        ''' return a friendly name for the element this annotation refers to'''
        import json
        ret = json.loads(self.elementid)
        ret = ' '.join([p[1] for p in ret])
        return ret

###########################################################################
#
#    EntryHand
#
###########################################################################


class EntryHand(models.Model):
    item_part = models.ForeignKey(
        'digipal.ItemPart', blank=False, null=False, related_name='entry_hands')
    entry_number = models.CharField(
        max_length=20, blank=False, null=False, db_index=True)
    hand_label = models.CharField(
        max_length=20, blank=False, null=False, db_index=True)

    order = models.IntegerField(
        blank=False, null=False, default=0, db_index=True)
    correction = models.BooleanField(
        blank=False, null=False, default=False, db_index=True)
    certainty = models.FloatField(blank=False, null=False, default=1.0)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = ['item_part', 'entry_number',
                           'hand_label', 'order', 'correction']

    def __unicode__(self):
        return u'%s %ss %s' % (
            self.hand_label, self.get_intervention_label(), self.entry_number)

    def get_intervention_label(self):
        ret = 'begin'
        if self.order > 0:
            ret = 'continue'
        if self.correction:
            ret = 'correct'
        return ret


class TextPattern(models.Model):
    title = models.CharField(
        max_length=100, unique=True, blank=False, null=False)
    key = models.SlugField(max_length=100, unique=True,
                           blank=False, null=False)
    pattern = models.CharField(max_length=1000, blank=True, null=True)
    order = models.IntegerField(
        blank=False, null=False, default=0, db_index=True)
    description = models.TextField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = ['key']
        ordering = ['order', 'key']

    def __unicode__(self):
        return u'%s' % (self.title)

    def save(self, *args, **kwargs):
        if not self.key.strip():
            self.key = self.title
        self.key = slugify(unicode(self.key))

        if not self.created:
            from datetime import datetime
            self.created = datetime.now()

        super(TextPattern, self).save(*args, **kwargs)

    @classmethod
    def get_empty_pattern(cls, aid=None):
        options = {'title': 'New pattern',
                   'key': 'new-pattern', 'pattern': '', 'order': 10000}
        if aid:
            options['id'] = aid
        ret = cls(**options)
        return ret


from digipal.models import set_additional_models_methods
set_additional_models_methods()

# LEAVE THIS CALL, this is to make sure the customisations are loaded
os.path.basename(settings.PROJECT_ROOT)
module_path = os.path.basename(
    settings.PROJECT_ROOT) + '.customisations.digipal_text.models'
from importlib import import_module
try:
    import_module(module_path)
except ImportError as e:
    # Ingore, customisations are optional
    pass
