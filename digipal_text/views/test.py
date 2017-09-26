# -*- coding: utf-8 -*-
#from digipal_text.models import *
from digipal_text.models import TextContentXMLStatus, TextContent, TextContentXML
import re
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.db import transaction
from digipal import utils

import logging
dplog = logging.getLogger('digipal_debugger')

MAX_FRAGMENT_SIZE = 60000


def drawing_view(request, item_partid=0):

    context = {}

    return render(request, 'digipal_text/test/drawing.html', context)
