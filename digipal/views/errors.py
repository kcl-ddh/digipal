from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
import json
from digipal.forms import SearchPageForm
from django.utils.safestring import mark_safe

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from digipal.templatetags import hand_filters, html_escape
from digipal import utils
from django.utils.datastructures import SortedDict
from digipal.templatetags.hand_filters import chrono
import digipal.models
import re
from digipal.utils import raise_404

def view_400(request):
    raise_404('TEST 400')

def view_500(request):
    raise Exception('TEST 500')
