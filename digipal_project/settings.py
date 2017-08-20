from digipal.settings import *

# Template file for local settings.
# Do NOT change settings.py instead copy this to local_settings.py, change it
# to suite the environment, but do NOT commit it to version control.
DEBUG = True

PROJECT_URL = '/'

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# Remove this line to work with JP2 format
# Note that it requires a kakadu license for commercial applications
IMAGE_SERVER_EXT = 'tif'

IMAGE_SERVER_HOST = 'localhost'
IMAGE_SERVER_ROOT = '/home/digipal/images/'
IMAGE_URLS_RELATIVE = True

IMAGE_SERVER_ZOOMIFY = 'http://%s%s?zoomify=%s/'
IMAGE_SERVER_PATH = '/iip/iipsrv.fcgi'
IMAGE_SERVER_URL = 'http://%s%s' % (IMAGE_SERVER_HOST, IMAGE_SERVER_PATH)

MANAGERS = ADMINS
STATICFILES_DIRS = (
    # Put strings here, like '/home/html/static' or 'C:/www/django/static'.
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

#SHOW_QUICK_SEARCH_SCOPES = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'digipal',
        'USER': 'app_digipal',
        'PASSWORD': 'dppsqlpass',
        'HOST': '',
        'PORT': '',
    },
}
