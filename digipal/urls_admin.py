from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('digipal.views.admin.general',
    (r'(?P<app_label>digipal)/(?P<model_name>[^/]+)/(?P<object_id>[^/]+)/context/', 'context_view'),
)

urlpatterns += patterns('digipal.views.admin.stewart',
    (r'digipal/stewartrecord/match', 'stewart_match'),
    (r'digipal/stewartrecord/import', 'stewart_import'),
)

urlpatterns = patterns('digipal.views.admin.quickforms',
    (r'digipal/itempart/add/?', 'add_itempart_view'),
)
