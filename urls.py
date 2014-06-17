from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from mezzanine.core.views import direct_to_template
from patches import mezzanine_patches
from digipal.models import CarouselItem
from index import count
admin.autodiscover()

# apply mezzanine patches at this stage. Before that would be troublesome (importing mezzanine would reimport digipal, etc)
mezzanine_patches()

statistic = count()

urlpatterns = patterns('', 
    url(r'^admin/', include('digipal.urls_admin')),
    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^digipal/', include('digipal.urls_digipal')),
    
    url(r'^account/$', 'django.contrib.auth.views.login'),

    url(r'^robots.txt/?$', 'digipal.views.robots.robots_view'),

    # these allow us to test 404 and 500 pages in DEBUG=True mode
    url('^404/?$', direct_to_template, {'template': 'errors/404.html'}, name = '404'),
    url('^500/?$', direct_to_template, {'template': 'errors/500.html'}, name = '500'),
    
    url('^$', direct_to_template, {
        'template': 'home.html',
        'extra_context': {
                'statistic': statistic,
                'carousel': CarouselItem,
            }
        },
        name = 'home'
    ),
    url(r'^tinymce/', include('tinymce.urls')),

    url(r'^blog/search/$', 'mezzanine.core.views.search'),
)

if settings.LIGHTBOX:
    url(r'^lightbox/', include('lightbox.urls', namespace='lightbox', app_name='lightbox')),

# Server media in debug mode
if settings.DEBUG :
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
