# -*- coding: utf-8 -*-
from digipal.models import *
from digipal_text.models import *
import re
from django import http, template
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy, ugettext as _
from django.utils.safestring import mark_safe
import htmlentitydefs
from django.core import urlresolvers
from digipal.forms import ScribeAdminForm, OnlyScribe
from django.forms.formsets import formset_factory
import json
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.db import transaction
from django.utils.datastructures import SortedDict
from django.http import Http404

import logging
dplog = logging.getLogger( 'digipal_debugger')


def text_viewer_view(request, item_partid=0):
    
    context = {}    
    
    return render(request, 'digipal_text/text_viewer.html', context)

