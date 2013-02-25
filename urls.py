from django.conf.urls.defaults import patterns, url
from django.views.generic import ListView
from models import Page
from views.facet import facet_search

urlpatterns = patterns('digipal.views.annotation',
                       (r'^page/$', ListView.as_view(
                           model=Page, paginate_by=24,
                           context_object_name='page_list',
                       )),
                       (r'^page/(?P<page_id>\d+)/$', 'page'),
                       (r'^page/(?P<page_id>\d+)/vectors/$', 'page_vectors'),
                       (r'^page/(?P<page_id>\d+)/annotations/$', 'page_annotations'),
                       (r'^page/(?P<page_id>\d+)/allographs/$', 'page_allographs'),
                       (r'^page/(?P<page_id>\d+)/allograph/(?P<allograph_id>\d+)/features/$',
                        'allograph_features'),
                       (r'^page/(?P<page_id>\d+)/save/(?P<vector_id>[a-zA-Z\._0-9]+)/',
                        'save'),
                       (r'^page/(?P<page_id>\d+)/delete/(?P<vector_id>[a-zA-Z\._0-9]+)/',
                        'delete'),
                       )

urlpatterns += patterns('digipal.views.search',
                       (r'^search/graph/$', 'allographHandSearch'),
                       (r'^search/$', 'searchDB'),
                       )

urlpatterns += patterns('digipal.views.image',
                       (r'^image-display/', 'image'),
                       )

urlpatterns += patterns('haystack.views',
                        url(
                            r'^facets/(?P<model>\D+)/$',
                            facet_search,
                            name="haystack_facet"),
                        )
