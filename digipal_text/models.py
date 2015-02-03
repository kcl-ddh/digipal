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
dplog = logging.getLogger('digipal_debugger')

class TextContentType(digipal.models.NameModel):
    pass

class TextContent(models.Model):
    languages = models.ManyToManyField('digipal.Language', blank=True, null=True, related_name='text_contents')
    type = models.ForeignKey('TextContentType', blank=True, null=True, related_name='text_contents')
    item_part = models.ForeignKey('digipal.ItemPart', blank=True, null=True, related_name='text_contents')
    text = models.ForeignKey('digipal.Text', blank=True, null=True, related_name='text_contents')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)
    
    def get_string_from_languages(self):
        return ', '.join([l.name for l in self.languages.all()])
        
    def __unicode__(self):
        info = self.type
        languages = self.get_string_from_languages()
        if languages:
            info +=  ', %s' % languages
        
        ret = '%s (%s)' % (self.item_part, info)
        return ret
    
    def get_absolute_url(self):
        return '%stexts/view/' % self.item_part.get_absolute_url()

class TextContentXMLStatus(digipal.models.NameModel):
    pass

class TextContentXML(models.Model):
    status = models.ForeignKey('TextContentXMLStatus', blank=True, null=True, related_name='text_content_xmls')
    text_content = models.ForeignKey('TextContent', blank=True, null=True, related_name='text_content_xmls')
    content = models.TextField(blank=True, null=True)
    last_image = models.ForeignKey('digipal.Image', blank=True, null=True, related_name='text_content_xmls')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True, editable=False)

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
        if self._meta.module_name in ['currentitem']: 
            return None            
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
            if (not hasattr(attribute, 'get_absolute_url')) and getattr(attribute, 'has_absolute_url', False):
                attribute.get_absolute_url = model_get_absolute_url
            attribute.get_admin_url = model_get_admin_url


set_additional_models_methods()

