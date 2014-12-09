from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('digipal.views.admin.general',
    (r'(?P<app_label>digipal)/(?P<model_name>[^/]+)/(?P<object_id>[^/]+)/context/', 'context_view'),
)

urlpatterns += patterns('digipal.views.admin.stewart',
    url(r'digipal/stewartrecord/match', 'stewart_match', name='stewart_match'),
    url(r'digipal/stewartrecord/import', 'stewart_import', name='stewart_import'),
)

if getattr(settings, 'USE_ITEM_PART_QUICK_ADD_FORM'):
    urlpatterns += patterns('digipal.views.admin.quickforms',
        (r'digipal/itempart/add/?', 'add_itempart_view'),
    )
