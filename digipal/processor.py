from digipal.forms import SearchPageForm
import digipal

class CanUserSeeModel(object):
    ''' Usage:
            cs = CanUserSeeModel(request)
            v = cs['Hand']
            
            => v is True is request.user can see Hand model
            See settings.py:MODELS_PUBLIC & MODELS_PRIVATE
    ''' 
    
    def __init__(self, request=None):
        self.request = request
    
    def __getitem__(self, index):
        from digipal.utils import is_model_visible
        return is_model_visible(index, self.request)

def get_dapi_content_type_response():
    '''Returns a string with all the content types supported by the API.
        Optimisation to avoid blocking call by the JS API.
    '''
    from digipal.api.generic import API
    api = API()
    ret = api.get_all_content_types('content_type');
    return ret

def quick_search(request):
    # We need this form for the quick search box
    # on to of every page
    return {
            'quick_search_form': SearchPageForm(),
            'digipal_version': digipal.__version__,
            # Usage in template: 
            # {% if cansee.Hand %}
            'cansee': CanUserSeeModel(request),
            'dapi_content_type_response': get_dapi_content_type_response
            }
