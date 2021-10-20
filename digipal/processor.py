from digipal.forms import SearchPageForm
import digipal
from mezzanine.conf import settings


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
    ret = api.get_all_content_types('content_type')
    return ret


def get_contextable_digipal_settings():
    ret = {}
    # space separated list of django settings variable names
    # to expose in the templates as global javascript var.
    #
    template_settings = 'ANNOTATOR_ZOOM_LEVELS ANNOTATOR_ZOOM_FACTOR ARCHETYPE_GOOGLE_SHORTENER_CLIENTID ARCHETYPE_GOOGLE_SHORTENER_API_KEY'
    for k in template_settings.split(' '):
        k = k.strip()
        ret[k] = getattr(settings, k, '')
    return ret


def digipal_site_context(request):
    # Supply additional variables to the response context
    # See also TEMPLATE_ACCESSIBLE_SETTINGS
    import json
    return {
        'quick_search_form': SearchPageForm(),
        'digipal_version': digipal.__version__,
        # Usage in template:
        # {% if cansee.Hand %}
        'cansee': CanUserSeeModel(request),
        'dapi_content_type_response': get_dapi_content_type_response,
        'DIGIPAL_SETTINGS': json.dumps(get_contextable_digipal_settings()),
        'DEBUG': settings.DEBUG,
        'ARCHETYPE_CITE': settings.ARCHETYPE_CITE
    }
