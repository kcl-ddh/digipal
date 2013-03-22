from digipal.forms import QuickSearch
from digipal.models import Scribe, ItemPart
from itertools import chain
from django.utils import simplejson
from django.db.models import Q


def quick_search(request):
	quicksearchform = QuickSearch()
	context = {'quicksearchform': quicksearchform}
	return context

def suggestions(request):
	hands = ItemPart.objects.filter(
                    Q(locus__isnull=False) | \
                    Q(current_item__shelfmark__isnull=False) | \
                    Q(current_item__repository__name__isnull=False) | \
                    Q(historical_item__catalogue_number__isnull=False) | \
                    Q(historical_item__description__description__isnull=False)).values_list('locus', flat=True).distinct()

	scribes = Scribe.objects.filter(
                name__isnull=False).values_list('name', flat=True).order_by('name')
	itemParts = ItemPart.objects.filter(
                    Q(locus__isnull=False) | \
                    Q(current_item__shelfmark__isnull=False) | \
                    Q(current_item__repository__name__isnull=False) | \
                    Q(historical_item__catalogue_number__isnull=False) | \
                    Q(historical_item__description__description__isnull=False)).values_list('current_item__repository__place__name',flat=True).distinct()
	result = list(set(chain(hands, scribes, itemParts)))
	context = {'suggestions': simplejson.dumps(result)}

	return context

