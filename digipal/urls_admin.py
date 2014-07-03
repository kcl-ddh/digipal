from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('digipal.views.admin.general',
    (r'(?P<app_label>digipal)/(?P<model_name>[^/]+)/(?P<object_id>[^/]+)/context/', 'context_view'),
)
