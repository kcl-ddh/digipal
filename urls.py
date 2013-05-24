from django.conf.urls.defaults import patterns, url
from views.facet import facet_search

urlpatterns = patterns('digipal.views.annotation',
                       #(r'^page/$', ListView.as_view(
                           #model=Page, paginate_by=24,
                           #context_object_name='page_list',
                       #)),
                       (r'^page/$', 'page_list'),
                       (r'^page/(?P<page_id>\d+)/$', 'page'),
                       (r'^page/(?P<page_id>\d+)/vectors/$', 'page_vectors'),
                       (r'^page/(?P<page_id>\d+)/annotations/$', 'page_annotations'),
                       (r'^page/(?P<page_id>\d+)/allographs/$', 'page_allographs'),
                       (r'^page/(?P<page_id>\d+)/metadata/$', 'page_metadata'),
                       (r'^page/(?P<page_id>\d+)/copyright/$', 'page_copyright'),
                       (r'^page/(?P<page_id>\d+)/allograph/(?P<allograph_id>\d+)/features/$',
                        'allograph_features'),
                       (r'^page/(?P<page_id>\d+)/graph/(?P<graph_id>\d+)/features/$', 'get_features'),

                       (r'^page/(?P<page_id>\d+)/save/(?P<vector_id>[a-zA-Z\._0-9]+)/',
                        'save'),
                       (r'^page/(?P<page_id>\d+)/delete/(?P<vector_id>[a-zA-Z\._0-9]+)/',
                        'delete'),

                       )

urlpatterns += patterns('digipal.views.search',
                       (r'^search/graph/$', 'allographHandSearch'),
                       (r'^graphs/graph/$', 'allographHandSearchGraphs'),
                       (r'^search/$', 'searchDB'),
                       (r'^graphs/$', 'graphsSearch'),
                       (r'^quicksearch/$', 'quickSearch'),
                       )

urlpatterns += patterns('digipal.views.image',
                       (r'^image-display/', 'image'),
                       )

urlpatterns += patterns('digipal.views.admin.page',
                       (r'admin/page/bulk_edit', 'page_bulk_edit'),
                       )

urlpatterns += patterns('digipal.views.admin.stewart',
                       (r'admin/stewartrecord/import', 'stewart_import'),
                       )

urlpatterns += patterns('haystack.views',
                        url(
                            r'^facets/(?P<model>\D+)/$',
                            facet_search,
                            name="haystack_facet"),
                        )
