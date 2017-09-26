from django.conf.urls import patterns, url, include
from mezzanine.conf import settings
from mezzanine.core.views import direct_to_template
#from views.facet import facet_search

urlpatterns = patterns('digipal.views.annotation',
    (r'^page/(?P<image_id>\d+)/$', 'image'),
    (r'^page/(?P<image_id>\d+)/(allographs|metadata|copyright|pages|hands|texts)/$', 'image'),
    # GN: dec 14, commented out as it is seems to be no longer used
    #(r'^page/(?P<image_id>\d+)/vectors/$', 'image_vectors'),
    (r'^page/(?P<image_id>\d+)/annotations/$', 'image_annotations'),
    (r'^page/(?P<image_id>\d+)/image_allographs/$', 'image_allographs'),
    (r'^page/(?P<image_id>\d+)/graph/(?P<graph_id>\d+)/allographs_by_graph/$', 'get_allographs_by_graph'),
    (r'^page/(?P<image_id>\d+)/allographs/(?P<allograph_id>\d+)/(?P<character_id>\d+)/allographs_by_allograph/$', 'get_allographs_by_allograph'),
    (r'^page/(?P<image_id>\d+)/graph/(?P<graph_id>\d+)/$', 'get_allograph'),
    (r'^page/(?P<image_id>\d+)/hands_list/$', 'hands_list'),

    (r'^api/old/(?P<content_type>[a-zA-Z]+)/(?P<ids>([0-9])+((,)*([0-9])*)*)/(?P<only_features>(features)*)$', 'get_old_api_request'),
    (r'^api/(?P<content_type>[0-9a-zA-Z_]+)/(?P<ids>[^/]*)/?(?P<only_features>(features)*)/?$', 'get_content_type_data'),

    (r'^api/graph/save/(?P<graphs>.+)/', 'save'),
    (r'^api/graph/save_editorial/(?P<graphs>.+)/', 'save_editorial'),

    (r'^page/(?P<image_id>\d+)/delete/(?P<graph_id>[a-zA-Z\._0-9]+)/', 'delete'),
    (r'^page/dialog/(?P<image_id>[a-zA-Z\._0-9]+)/$', 'form_dialog'),
    (r'^page/(?P<image_id>\d+)/(?P<graph>[a-zA-Z\._0-9]+)/graph_vector/$', 'get_vector'),

    (r'^collection/(?P<collection_name>.+)/images/$', 'images_lightbox'),
    (r'^collection/(?P<collection_name>.+)/$', direct_to_template, {
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
)

urlpatterns += patterns('digipal.views.search',
    # search pages
    (r'^page/$', 'search_ms_image_view'),
    (r'^search/$', 'search_record_view'),
    (r'^quicksearch/$', 'search_record_view'),
    (r'^search/index/?$', 'search_index_view'),
    (r'^search/graph/$', 'search_graph_view'),
    (r'^search/suggestions.json/?$', 'search_suggestions'),
    # Record views
    (r'^(?P<content_type>hands|manuscripts|scribes|graphs|pages)/(?P<objectid>[^/]+)(/(?P<tabid>[^/]+))?(?:/|$)', 'record_view'),
    (r'^(?P<content_type>hands|manuscripts|scribes|pages)(?:/|$)', 'index_view'),
    (r'^catalogue/(?P<source>[^/]+)(/(?P<number>[^/]+))?(?:/|$)', 'catalogue_number_view'),
)

urlpatterns += patterns('',
    url(r'^search/facets/$', 'digipal.views.faceted_search.faceted_search.search_whoosh_view', name='facets'),
    (r'^400/?$', 'digipal.views.errors.view_400'),
    (r'^500/?$', 'digipal.views.errors.view_500'),
    #(r'^search/facets/$', 'digipal.views.faceted_search.faceted_search.search_haystack_view'),
    #(r'^search/facets/$', include('haystack.urls')),
    #url(r'^search/facets/$', FacetedSearchView(form_class=FacetedSearchForm, searchqueryset=sqs), name='haystack_search'),
)

# TODO: move this to urls_admin.py
urlpatterns += patterns('digipal.views.admin.image',
    (r'admin/image/bulk_edit', 'image_bulk_edit'),
)

if settings.DEBUG:
    urlpatterns += patterns('digipal.views.test',
       (r'test/cookied_inputs/$', 'cookied_inputs'),
       (r'test/iipimage/$', 'iipimage'),
       (r'test/similar_graph/$', 'similar_graph_view'),
       (r'test/map/$', 'map_view'),
       (r'test/autocomplete/$', 'autocomplete_view'),
       (r'test/api/$', 'api_view'),
       # jquery notebook
       (r'test/jqnotebook/$', 'jqnotebook_view'),
   )

urlpatterns += patterns('digipal.views.test', (r'test/error/?$', 'server_error_view'),)
urlpatterns += patterns('digipal.views.email', (r'test/email/$', 'send_email'),)



# urlpatterns += patterns('haystack.views',
#     url(r'^facets/(?P<model>\D+)/$', facet_search, name="haystack_facet"),
# )
