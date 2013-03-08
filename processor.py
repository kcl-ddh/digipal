from digipal.forms import SearchForm

def quick_search(request):
	quicksearchform = SearchForm()
	context = {'quicksearchform': quicksearchform}
	return context
