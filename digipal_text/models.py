from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.safestring import mark_safe
from django.db.models import Q
import os, re, string, unicodedata, cgi
from django.utils.html import conditional_escape, escape
from tinymce.models import HTMLField
from django.db import transaction
from mezzanine.generic.fields import KeywordsField
import logging
import digipal.models
from django.contrib.auth.models import User
dplog = logging.getLogger('digipal_debugger')

class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

class TextUnits(object):
    '''Abstract Class that behaves like a Django Model Manager
       for units of text in a TextContentXML
    '''

    def __init__(self):
        # !!!
        # TODO: this is VERY inefficient if we call in_bulk as we get all the records
        # We need to implement lazy loading instead
        self.options = {'select_related': [], 'prefetch_related': []}
        self.load_records()

    def select_related(self, *args, **kwargs):
        self.options['select_related'] = args
        self.load_records()
        return self

    def prefetch_related(self, *args, **kwargs):
        self.options['prefetch_related'] = args
        self.load_records()
        return self

    def load_records(self):
        # actually find and load the requested records
        self.recs = list()

    def __iter__(self):
        return self.recs.__iter__()

    def in_bulk(self, *args, **kwargs):
        # TODO: not necessarily reliable to access with args[0]
        ids = args[0]
        ret = {}
        for rec in self.recs:
            if rec.id in ids:
                ret[rec.id] = rec
        return ret

    def iterator(self, *args, **kwargs):
        return self.recs

    def count(self, *args, **kwargs):
        return len(self.recs)

    def all(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

class TextUnit(object):
    '''Abstract Class that behaves like a Django Model
       for a unit of text in a TextContentXML
    '''

    @property
    def id(self):
        return ur'%s:%s' % (self.content_xml.id, self.unitid)

    def get_absolute_url(self, qs=None, metas=None):
        # TODO: fix it, broken for EXON b/c url now contains more specific info and # fragment
        #return '%s/entry/%s/' % (self.content_xml.get_absolute_url(), self.unitid)
        return '%s' % self.content_xml.get_absolute_url(qs=qs, metas=metas)

    def get_thumb(self):
        from digipal.models import Annotation
        ret = Annotation.objects.filter(image__item_part=self.content_xml.text_content.item_part, textannotations__elementid=self.get_elementid()).first()

        return ret

    @ClassProperty
    @classmethod
    def objects(cls, *args, **kwargs):
        return TextUnits()

class TextContentType(digipal.models.NameModel):
    class Meta:
        verbose_name = 'Text Type'
        verbose_name_plural = 'Text Types'

class TextContent(models.Model):
    languages = models.ManyToManyField('digipal.Language', blank=True, null=True, related_name='text_contents')
    type = models.ForeignKey('TextContentType', blank=False, null=False, related_name='text_contents')
    item_part = models.ForeignKey('digipal.ItemPart', blank=False, null=False, related_name='text_contents')
    text = models.ForeignKey('digipal.Text', blank=True, null=True, related_name='text_contents')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)

    class Meta:
        unique_together = ('item_part', 'type')
        verbose_name = 'Text (meta)'
        verbose_name_plural = 'Texts (meta)'

    def get_string_from_languages(self):
        return u', '.join([l.name for l in self.languages.all()])

    def __unicode__(self):
        info = self.type
        languages = self.get_string_from_languages()
        if languages:
            info +=  u', %s' % languages

        ret = u'%s (%s)' % (self.item_part, info)
        return ret

    def get_absolute_url(self, unset=False, qs='', metas=None, location_type=None, location=None):
        '''
            Returns the url to view this text content.
            unset: if True the panels types and content are unspecified
            qs: a partial query string to be added to the url
            metas: additional settings for the main panel (e.g. 'k1=v1;k2=v2')
        '''
        types = ['transcription', 'translation']
        ret = u'%stexts/view/' % self.item_part.get_absolute_url()
        if not unset:
            ret += '?center=%s' % self.type.slug
            if location_type:
                ret += '/%s' % location_type
                if location:
                    ret += '/%s' % location
            ret += '/'
            if metas:
                from digipal.utils import urlencode
                ret += (';' + urlencode(metas, True)).replace('=', ':')
            ret += '&east=%s/sync/%s/' % (set(types).difference(set([self.type.slug])).pop(), self.type.slug)
            ret += '&north=image/sync/%s/' % self.type.slug
        if qs:
            if '?' not in ret:
                ret += '?'
            else:
                ret += '&'
            if qs[0] in ['&', '?']:
                qs = qs[1:]
            ret += qs
        ret += '#text-viewer'
        return ret
    # http://localhost/digipal/manuscripts/598/texts/view/?center=transcription;subl:%5B%5B%22%22%2C+%22clause%22%5D%2C+%5B%22type%22%2C+%22witnesses%22%5D%5D&east=translation/sync/transcription/&north=image/sync/transcription/#text-viewer
    # http://localhost/digipal/manuscripts/598/texts/view/?center=transcription;subl:%5B%5B%22%22,%22clause%22%5D,%5B%22type%22,%22witnesses%22%5D%5D;&east=translation/sync/transcription/;subl:%5B%5B%22%22,%22clause%22%5D,%5B%22type%22,%22witnesses%22%5D%5D;&north=image/sync/transcription/;subl:%5B%5B%22%22,%22clause%22%5D,%5B%22type%22,%22witnesses%22%5D%5D;olv:2,1860,-1385,0;#text-viewer

class TextContentXMLStatus(digipal.models.NameModel):
    sort_order = models.IntegerField(blank=False, null=False, default=0, help_text='The order of this status in your workflow.')

    class Meta:
        verbose_name = 'Text Status'
        verbose_name_plural = 'Text Statuses'

class TextContentXMLCopy(models.Model):
    source = models.ForeignKey('TextContentXML', blank=True, null=True, related_name='versions')
    ahash = models.CharField(max_length=100, blank=True, null=True)
    content = models.BinaryField(blank=False, null=False)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)

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
            copy = TextContentXMLCopy(source=content_xml, content=content, ahash=ahash)
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
    status = models.ForeignKey('TextContentXMLStatus', blank=False, null=False, related_name='text_content_xmls')
    text_content = models.ForeignKey('TextContent', blank=False, null=False, related_name='text_content_xmls')
    content = models.TextField(blank=True, null=True)
    last_image = models.ForeignKey('digipal.Image', blank=True, null=True, related_name='text_content_xmls')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)

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
        if not ignore: ret = ret.filter(status__slug__in=['live', 'published', 'public', 'online'])

        return ret

    def get_length(self):
        if not self.content:
            return 0
        return len(self.content)

    def save(self, *args, **kwargs):
        # initialise the status if undefined
        if not self.status_id:
            self.status = TextContentXMLStatus.objects.order_by('sort_order').first()
        super(TextContentXML, self).save(*args, **kwargs)

    def get_absolute_url(self, unset=False, qs=None, metas=None, location_type=None, location=None):
        return self.text_content.get_absolute_url(unset=unset, qs=qs, metas=metas, location_type=location_type, location=location)

    def save_copy(self):
        '''Save a compressed copy of this content into the Copy table'''
        TextContentXMLCopy.create_from_content_xml(self)

    def is_private(self):
        return self.status.slug not in ['live', 'published', 'public', 'online']

    # TODO: make this function overridable
    def convert(self):
        content = self.content

        # convert () into expansions
        content = re.sub(ur'\(([^)<>]{1,50})\)', ur'<span data-dpt="ex" data-dpt-cat="chars">\1</span>', content)

        # convert <> into supplied
        content = re.sub(ur'&lt;(.*?)&gt;', ur'<span data-dpt="supplied" data-dpt-cat="chars">\1</span>', content)

        # convert 7 into tironian sign
        content = re.sub(ur'\b7\b', u'\u204a', content)

        # convert | into spans
        content = re.sub(ur'\|+', u'<span data-dpt="lb" data-dpt-cat="sep">|</span>', content)
        #content = re.sub(ur'(<br\s*/?>\s*)+', u'<br/>', content)

        self.content = content

class TextAnnotation(models.Model):
    annotation = models.ForeignKey('digipal.Annotation', blank=False, null=False, related_name='textannotations')
    elementid = models.CharField(max_length=255, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)

    class Meta:
        unique_together = ['annotation', 'elementid']

    def __unicode__(self):
        return 'Annotation of "%s" in image "%s"' % (self.get_friendly_name(), self.annotation.image)

    def get_friendly_name(self):
        ''' return a friendly name for the element this annotation refers to'''
        import json
        ret = json.loads(self.elementid)
        ret = ' '.join([p[1] for p in ret])
        return ret

from digipal.models import set_additional_models_methods

set_additional_models_methods()
