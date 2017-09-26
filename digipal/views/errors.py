from django.shortcuts import render_to_response
from django.template import RequestContext

from mezzanine.conf import settings
from digipal import utils
from digipal.utils import raise_404


def view_400(request):
    raise_404('TEST 400')


def view_500(request):
    raise Exception('TEST 500')
