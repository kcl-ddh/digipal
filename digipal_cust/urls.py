from mezzanine.conf import settings
from django.conf.urls import patterns, include, url
from mezzanine.core.views import direct_to_template
from redirects import get_redirect_patterns
from django.contrib import admin
admin.autodiscover()

# redirects
urlpatterns = get_redirect_patterns()

# ADD YOUR OWN URLPATTERNS *ABOVE* THE LINE BELOW.
# DigiPal URLs
urlpatterns += patterns('', ('^', include('digipal.urls')))

# Adds ``STATIC_URL`` to the context.
handler500 = 'mezzanine.core.views.server_error'
handler404 = 'mezzanine.core.views.page_not_found'
