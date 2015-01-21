from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('digipal_text.views',
    url(r'^digipal/manuscripts/(\d+)/texts/$', 'viewer.text_viewer_view'),
    #url(r'^admin/digipal/itempart/(\d+)/edit/([^/]+)/$', 'admin.text_view'),
    
    url(r'^digipal/manuscripts/(\d+)/texts/([^/]+)/([^/]+)/([^/]+)/$', 'viewer.text_api_view'),
)
