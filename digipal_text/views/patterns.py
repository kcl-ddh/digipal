# -*- coding: utf-8 -*-
# from digipal_text.models import *
from digipal_text.models import TextContentXMLStatus, TextContent, TextContentXML
import re
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.db import transaction
from digipal import utils
from django.utils.datastructures import SortedDict
from django.conf import settings
from digipal import utils as dputils
import json

import logging
from digipal.utils import sorted_natural
from digipal.templatetags.hand_filters import chrono
dplog = logging.getLogger('digipal_debugger')

def patterns_view(request):

    from digipal_text.models import TextPattern

    context = {}
    context['wide_page'] = True
    context['patterns'] = list(TextPattern.objects.all())

    new_pattern = TextPattern(title='New pattern', key='new-pattern', pattern='')
    print new_pattern.key

    context['patterns'].append(new_pattern)

    return render(request, 'digipal_text/patterns.html', context)
