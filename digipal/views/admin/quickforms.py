# -*- coding: utf-8 -*-
import re
from django import http, template
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.http import HttpResponse, Http404, HttpResponseBadRequest

import logging
dplog = logging.getLogger( 'digipal_debugger')


@staff_member_required
def add_itempart_view(request):
    context = {}
    
    return render(request, 'admin/digipal/add_itempart.html', context)

