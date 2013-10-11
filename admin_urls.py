from django.conf.urls.defaults import patterns, url
from django.conf import settings
from views.facet import facet_search

urlpatterns = patterns('digipal.views.admin.general',
                       (r'(?P<app_label>digipal)/(?P<model_name>[^/]+)/(?P<object_id>[^/]+)/context/', 'context_view'),
                       )
