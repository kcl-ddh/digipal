# Configuring DigiPal

Update (18/03/15): Docker is now the recommended way to install the DigiPal framework on your machine. The documentation below is therefore superceded by those found on the [DigiPal Docker page](https://registry.hub.docker.com/u/gnoelddh/digipal/).

 These below are the basic requirements to configure DigiPal and make it work correctly. All the optional configurations are available in the local_settings.py file you can find in the DigiPal project folder.

### Database
**In order to run the DigiPal Database we used a PostgresQL database server. Therefore, we recommend you to use PostgresQL as well since we cannot ensure that the database will work on other RDBs.**

Set up the database in your local_settings.py file and fill the DATABASES object with your settings:


```
DATABASES = {
    'default': {
        'ENGINE': '',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    }
 }

```
After that, run in your terminal the following commands:


```
python manage.py syncdb
python manage.py migrate
```

### Image uploads

```
UPLOAD_IMAGES_URL = 'uploads/images/'
UPLOAD_IMAGES_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.strip('/'),
        UPLOAD_IMAGES_URL.strip('/'))

ARCHETYPE_THUMB_LENGTH_MAX = 50
```

### Haystack

```
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'haystack',
    },
}

ITEM_PART_DEFAULT_LOCUS = 'face'

```

### IIP   Image Server

```
IMAGE_SERVER_WEB_ROOT = 'jp2'
IMAGE_SERVER_HOST = 'digipal.cch.kcl.ac.uk'
IMAGE_SERVER_PATH = '/iip/iipsrv.fcgi'
IMAGE_SERVER_ZOOMIFY = 'http://%s%s?zoomify=%s/'
IMAGE_SERVER_FULL = 'http://%s%s?FIF=%s&amp;amp;RST=*&amp;amp;QLT=100&amp;amp;CVT=JPG'
IMAGE_SERVER_THUMBNAIL = 'http://%s%s?FIF=%s&amp;amp;RST=*&amp;amp;HEI=35&amp;amp;CVT=JPG'
IMAGE_SERVER_THUMBNAIL_HEIGHT = 35
IMAGE_SERVER_RGN = 'http://%s%s?FIF=%s&amp;%s&amp;RGN=%f,%f,%f,%f&amp;CVT=JPG'
IMAGE_SERVER_EXT = 'jp2'
```

#### DJANGO-IIPIMAGE

```
IMAGE_SERVER_URL  = 'http://%s%s' % (IMAGE_SERVER_HOST, IMAGE_SERVER_PATH)
IMAGE_SERVER_ROOT = '/vol/digipal2/images'
IMAGE_SERVER_UPLOAD_ROOT = 'jp2'
IMAGE_SERVER_ORIGINALS_ROOT = 'originals'
IMAGE_SERVER_UPLOAD_EXTENSIONS = ('.jp2', '.jpg', '.tif', '.bmp', '.jpeg')
IMAGE_SERVER_ADMIN_UPLOAD_DIR = os.path.join(IMAGE_SERVER_UPLOAD_ROOT, 'admin-upload')
```
 

_Giancarlo Buomprisco _

