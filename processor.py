from digipal.forms import SearchPageForm
from digipal.models import Scribe, ItemPart
from itertools import chain
from django.utils import simplejson
from django.db.models import Q

def quick_search(request):
    # We need this form for the quick search box
    # on to of every page
	return {'quick_search_form': SearchPageForm().as_ul()}
