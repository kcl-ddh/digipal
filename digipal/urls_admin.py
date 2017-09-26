from django.conf.urls import patterns, url
from mezzanine.conf import settings

urlpatterns = patterns('digipal.views.admin.general',
    (r'(?P<app_label>digipal)/(?P<model_name>[^/]+)/(?P<object_id>[^/]+)/context/', 'context_view'),
    (r'(?P<app_label>digipal)/instances/', 'instances_view'),
    (r'(?P<app_label>digipal)/(?P<model_name>[^/]+)/import/', 'import_view'),
)

urlpatterns += patterns('digipal.views.admin.stewart',
    url(r'digipal/stewartrecord/match', 'stewart_match', name='stewart_match'),
    url(r'digipal/stewartrecord/import', 'stewart_import', name='stewart_import'),
)

urlpatterns += patterns('digipal.views.admin.idiograph',
    (r'digipal/idiograph_editor/$', 'idiograph_editor'),
    (r'digipal/idiograph_editor/get_idiographs', 'get_idiographs'),
    (r'digipal/idiograph_editor/get_allographs', 'get_allographs'),
    (r'digipal/idiograph_editor/get_idiograph', 'get_idiograph'),
    (r'digipal/idiograph_editor/save_idiograph', 'save_idiograph'),
    (r'digipal/idiograph_editor/update_idiograph', 'update_idiograph'),
    (r'digipal/idiograph_editor/delete_idiograph', 'delete_idiograph'),
)

if getattr(settings, 'USE_ITEM_PART_QUICK_ADD_FORM'):
    urlpatterns += patterns('digipal.views.admin.quickforms',
        (r'digipal/itempart/add/?', 'add_itempart_view'),
    )

