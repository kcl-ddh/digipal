from django.conf.urls import patterns, url
from mezzanine.conf import settings

urlpatterns = patterns('digipal_text.views')

if settings.DEBUG:
    urlpatterns += patterns(
        'digipal_text.views',
        url(r'^digipal/manuscripts/(\d+)/texts/test/drawing/?',
            'test.drawing_view'),
    )

urlpatterns += patterns(
    'digipal_text.views',
    url(r'^digipal/manuscripts/(\d+)/texts/view/tinymce_generated.css',
        'viewer.tinymce_generated_css_view'),
    url(
        r'^digipal/manuscripts/(\d+)/texts/view/([^/]+)/([^/]+)/?$', 'viewer.text_viewer_view'),
    url(
        r'^digipal/manuscripts/(\d+)/texts/view/([^/]+)/?$', 'viewer.text_viewer_view'),
    url(r'^digipal/manuscripts/(\d+)/texts/view/?$',
        'viewer.text_viewer_view'),

    # Replace the first line with the second as apache doesn't like // (e.g. /texts/translation/whole//)
    # Django web server deals well with it.
    #url(r'^digipal/manuscripts/(\d+)/texts/([^/]+)/([^/]+)/([^/]*)/$', 'viewer.text_api_view'),
    url(r'^digipal/manuscripts/(\d+)/texts/([^/]+)/([^/]+)/([^/]*)/?$',
        'viewer.text_api_view'),
    url(r'^digipal/manuscripts/(\d+)/texts/([^/]+)/([^/]+)/?$',
        'viewer.text_api_view'),
    url(r'^digipal/manuscripts/(\d+)/texts/([^/]+)/?$',
        'viewer.text_api_view'),

    url(r'^digipal/patterns/?$', 'patterns.patterns_view'),
    url(r'^digipal_text/api/(patterns|move_pattern|segunits)/(.*?)/?$',
        'patterns.patterns_api_view'),
)
