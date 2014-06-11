from digipal.forms import SearchPageForm

def quick_search(request):
    # We need this form for the quick search box
    # on to of every page
    return {'quick_search_form': SearchPageForm()}
