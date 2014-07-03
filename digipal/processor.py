from digipal.forms import SearchPageForm
import digipal

def quick_search(request):
    # We need this form for the quick search box
    # on to of every page
    return {
            'quick_search_form': SearchPageForm(),
            'digipal_version': digipal.__version__
            }
