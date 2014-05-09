from django.conf.urls.defaults import patterns, url
from django.conf import settings
from mezzanine.core.views import direct_to_template
from views.facet import facet_search
from patches import mezzanine_patches
# apply mezzanine patches at this stage. Before that would be troublesome (importing mezzanine would reimport digipal, etc)
mezzanine_patches()

urlpatterns = patterns('digipal.views.annotation',
                       #(r'^page/$', ListView.as_view(
                           #model=Page, paginate_by=24,
                           #context_object_name='page_list',
                       #)),
                       (r'^page/(?P<image_id>\d+)/$', 'image'),
                       (r'^page/(?P<image_id>\d+)/(allographs|metadata|copyright|pages|hands)/$', 'image'),
                       (r'^page/(?P<image_id>\d+)/vectors/$', 'image_vectors'),
                       (r'^page/(?P<image_id>\d+)/annotations/$', 'image_annotations'),
                       (r'^page/(?P<image_id>\d+)/image_allographs/$', 'image_allographs'),
                       (r'^page/(?P<image_id>\d+)/graph/(?P<graph_id>\d+)/allographs_by_graph/$', 'get_allographs_by_graph'),
                       (r'^page/(?P<image_id>\d+)/allographs/(?P<allograph_id>\d+)/(?P<character_id>\d+)/allographs_by_allograph/$', 'get_allographs_by_allograph'),
                       (r'^page/(?P<image_id>\d+)/graph/(?P<graph_id>\d+)/$', 'get_allograph'),
                       (r'^page/(?P<image_id>\d+)/hands_list/$', 'hands_list'),

                       #(r'^api/(?P<content_type>[a-zA-Z]+)/(?P<id>([0-9])+((,)*([0-9])*)*)/(?P<only_features>(features)*)$', 'get_content_type_data'),
                       (r'^api/(?P<content_type>[a-zA-Z]+)/(?P<ids>[^/]*)/?(?P<only_features>(features)*)/?$', 'get_content_type_data'),
                        
                       (r'^api/graph/save/(?P<graphs>.+)/', 'save'),
                       #(r'^api/annotation/(?P<selector>.*)', 'api_get_annotation'),
                       (r'^page/(?P<image_id>\d+)/delete/(?P<vector_id>[a-zA-Z\._0-9]+)/',
                        'delete'),
                       (r'^page/dialog/(?P<image_id>[a-zA-Z\._0-9]+)/$',
                        'form_dialog'),
                       (r'^page/(?P<image_id>\d+)/(?P<graph>[a-zA-Z\._0-9]+)/graph_vector/$',
                        'get_vector'),
                        (r'^collection/(?P<collection_name>[a-zA-Z-_0-9]+)/$', direct_to_template, {
                          'template': 'digipal/collection.html',
                          'extra_context': {
                                'LIGHTBOX': settings.LIGHTBOX,
                          }
                        }),
                       (r'^collection/shared/1/$', direct_to_template, {
                          'template': 'digipal/collection.html',
                          'extra_context': {
                                'LIGHTBOX': settings.LIGHTBOX,
                          }
                        }),
                       (r'^collection/$', direct_to_template, {
                          'template': 'digipal/lightbox_basket.html',
                           'extra_context': {
                                'LIGHTBOX': settings.LIGHTBOX,
                            }
                        }),
                       (r'^collection/(?P<collection_name>[a-zA-Z-_0-9]+)/images/$',
                        'images_lightbox'),
                       )

urlpatterns += patterns('digipal.views.search',
                       # search pages
                       (r'^page/$', 'search_ms_image_view'),
                       (r'^search/$', 'search_record_view'),
                       (r'^quicksearch/$', 'search_record_view'),
                       (r'^search/graph/$', 'search_graph_view'),
                       (r'^search/suggestions.json/?$', 'search_suggestions'),
                       # Record views
                       (r'^(?P<content_type>hands|manuscripts|scribes|graphs|pages)/(?P<objectid>[^/]+)(/(?P<tabid>[^/]+))?(?:/|$)', 'record_view'),
                       (r'^(?P<content_type>hands|manuscripts|scribes|graphs|pages)(?:/|$)', 'index_view'),
                       )

urlpatterns += patterns('digipal.views.admin.image',
                       (r'admin/image/bulk_edit', 'image_bulk_edit'),
                       (r'admin/newscriptentry/$', 'newScriptEntry'),
                       (r'admin/newscriptentry/get_idiographs', 'get_idiographs'),
                       (r'admin/newscriptentry/get_allographs', 'get_allographs'),
                       (r'admin/newscriptentry/get_ideograph', 'get_ideograph'),
                       (r'admin/newscriptentry/save_idiograph', 'save_idiograph'),
                       (r'admin/newscriptentry/update_idiograph', 'update_idiograph'),
                       (r'admin/newscriptentry/delete_idiograph', 'delete_idiograph'),
                       )

urlpatterns += patterns('digipal.views.admin.stewart',
                       (r'admin/digipal/stewartrecord/match', 'stewart_match'),
                       (r'admin/digipal/stewartrecord/import', 'stewart_import'),
                       )

if settings.DEBUG:
    urlpatterns += patterns('digipal.views.test',
                           (r'test/cookied_inputs/$', 'cookied_inputs'),
                           (r'test/iipimage/$', 'iipimage'),
                           (r'test/similar_graph/$', 'similar_graph_view'),
                           (r'test/map/$', 'map_view'),
                           (r'test/autocomplete/$', 'autocomplete_view'),
                           (r'test/api/$', 'api_view'),
                           )

urlpatterns += patterns('haystack.views',
                        url(
                            r'^facets/(?P<model>\D+)/$',
                            facet_search,
                            name="haystack_facet"),
                        )
