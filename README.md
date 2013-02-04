DigiPal
=======

Digital Resource for and Database of Paleography, Manuscripts and Diplomatic.

Required settings
=================

# Image uploads
UPLOAD_IMAGES_URL = 'uploads/images/'
UPLOAD_IMAGES_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.strip('/'),
        UPLOAD_IMAGES_URL.strip('/'))

MAX_THUMB_LENGTH = 50

# Haystack
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'haystack',
    },
}

ITEM_PART_DEFAULT_LOCUS = 'face'

# IIP Image Server
IMAGE_SERVER_ROOT = 'jp2'
IMAGE_SERVER_HOST = 'digipal.cch.kcl.ac.uk'
IMAGE_SERVER_PATH = '/iip/iipsrv.fcgi'
IMAGE_SERVER_METADATA = '%s?FIF=%s&OBJ=Max-size'
IMAGE_SERVER_METADATA_REGEX = r'^.*?Max-size:(\d+)\s+(\d+).*?$'
IMAGE_SERVER_ZOOMIFY = 'http://%s%s?zoomify=%s/'
IMAGE_SERVER_FULL = 'http://%s%s?FIF=%s&RST=*&QLT=100&CVT=JPG'
IMAGE_SERVER_THUMBNAIL = 'http://%s%s?FIF=%s&RST=*&HEI=35&CVT=JPG'
IMAGE_SERVER_RGN = 'http://%s%s?FIF=%s&RST=*&%s&RGN=%f,%f,%f,%f&CVT=JPG'
IMAGE_SERVER_EXT = 'jp2'
