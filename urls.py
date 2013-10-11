from django.conf.urls.defaults import patterns, url
from django.conf import settings
from views.facet import facet_search

urlpatterns = patterns('digipal.views.annotation',
                       #(r'^page/$', ListView.as_view(
                           #model=Page, paginate_by=24,
                           #context_object_name='page_list',
                       #)),
                       (r'^page/$', 'image_list'),
                       (r'^page/(?P<image_id>\d+)/$', 'image'),
                       (r'^page/(?P<image_id>\d+)/vectors/$', 'image_vectors'),
                       (r'^page/(?P<image_id>\d+)/annotations/$', 'image_annotations'),
                       (r'^page/(?P<image_id>\d+)/allographs/$', 'image_allographs'),
                       (r'^page/(?P<image_id>\d+)/graph/(?P<graph_id>\d+)/(?P<character_id>\d+)/allographs_by_graph/$', 'get_allographs_by_graph'),
                       (r'^page/(?P<image_id>\d+)/allographs/(?P<allograph_id>\d+)/(?P<character_id>\d+)/allographs_by_allograph/$', 'get_allographs_by_allograph'),
                       (r'^page/(?P<image_id>\d+)/graph/(?P<graph_id>\d+)/$', 'get_allograph'),
                       (r'^page/(?P<image_id>\d+)/hands_list/$', 'hands_list'),
                       (r'^page/(?P<image_id>\d+)/metadata/$', 'image_metadata'),
                       (r'^page/(?P<image_id>\d+)/copyright/$', 'image_copyright'),
                       (r'^page/(?P<image_id>\d+)/allograph/(?P<allograph_id>\d+)/features/$',
                        'allograph_features'),
                       (r'^page/(?P<image_id>\d+)/graph/(?P<graph_id>\d+)/features/$', 'get_features'),

                       (r'^page/(?P<image_id>\d+)/save/(?P<vector_id>[a-zA-Z\._0-9]+)/',
                        'save'),
                       (r'^page/(?P<image_id>\d+)/delete/(?P<vector_id>[a-zA-Z\._0-9]+)/',
                        'delete'),
                       )

urlpatterns += patterns('digipal.views.search',
                       (r'^search/graph/$', 'allographHandSearch'),
                       (r'^graphs/graph/$', 'allographHandSearchGraphs'),
                       (r'^search/$', 'search_page_view'),
                       (r'^graphs/$', 'graphsSearch'),
                       (r'^quicksearch/$', 'search_page_view'),
                       (r'^search/suggestions.json/?$', 'search_suggestions'),
                       # Record views
                       (r'^(?P<content_type>hands|manuscripts|scribes|graphs|pages)/(?P<objectid>[^/]+)(?:/|$)', 'record_view'),
                       )

urlpatterns += patterns('digipal.views.image',
                       (r'^image-display/', 'image'),
                       )

urlpatterns += patterns('digipal.views.admin.image',
                       (r'admin/image/bulk_edit', 'image_bulk_edit'),
                       (r'admin/newscriptentry/$', 'newScriptEntry'),
                       (r'admin/Scribeinserted/$', 'inserting'),
                       (r'admin/newscriptentry/get_idiographs', 'get_idiographs'),
                       (r'admin/newscriptentry/get_allographs', 'get_allographs'),
                       (r'admin/newscriptentry/get_ideograph', 'get_ideograph'),

                       )

urlpatterns += patterns('digipal.views.admin.stewart',
                       (r'admin/digipal/stewartrecord/match', 'stewart_match'),
                       (r'admin/digipal/stewartrecord/import', 'stewart_import'),
                       )

if settings.DEBUG:
    urlpatterns += patterns('digipal.views.test',
                           (r'test/cookied_inputs/$', 'cookied_inputs'),
                           )

urlpatterns += patterns('haystack.views',
                        url(
                            r'^facets/(?P<model>\D+)/$',
                            facet_search,
                            name="haystack_facet"),
                        )
