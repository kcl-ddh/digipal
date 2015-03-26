from digipal.forms import SearchPageForm
import digipal

def quick_search(request):
    from digipal.utils import is_model_visible
    # We need this form for the quick search box
    # on to of every page
    return {
            'quick_search_form': SearchPageForm(),
            'digipal_version': digipal.__version__,
            'can_see': lambda m: is_model_visible(m, request)
            }
