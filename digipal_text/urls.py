from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('digipal_text.views',
    url(r'^admin/digipal/itempart/(\d+)/edit/$', 'admin.text_edit_view'),
    url(r'^admin/digipal/itempart/(\d+)/edit/([^/]+)/$', 'admin.text_edit_view'),
)
