# -*- coding: utf-8 -*-

#######################################################################
# DO NOT CHANGE SETTINGS IN THIS FILE, ONLY ADD NEW SENSIBLE DEFAULTS #
# FOR MORE INFORMATION SEE local_settings_template.py.                #
#######################################################################

import os
import sys
import logging
import importlib


def gettext(s): return s


def make_path(path):
    if not os.path.exists(path):
        os.makedirs(path)

########################
# MAIN DJANGO SETTINGS #
########################


# Emails will be sent on server errors if DEBUG=False
# Add admin email addresses in your local_settings.py
ADMINS = ()
# SERVER_EMAIL = 'django@text.com'
MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
USE_TZ = True
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

# A boolean that turns on/off debug mode. When set to ``True``, stack traces
# are displayed for error pages. Should always be set to ``False`` in
# production. Best set to ``True`` in local_settings.py
DEBUG = False

# Whether a user's session cookie expires when the Web browser is closed.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'change-me'

# Tuple of IP addresses, as strings, that:
#   * See debug comments, when DEBUG is true
#   * Receive x-headers
INTERNAL_IPS = ('127.0.0.1',)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    # Authentication using REMOTE_USER
    'django.contrib.auth.backends.RemoteUserBackend',
)

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

#############
# DATABASES #
#############

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

#########
# PATHS #
#########

PROJECT_URL = '/'

# URLs used for login/logout when ACCOUNTS_ENABLED is set to True.
LOGIN_URL = PROJECT_URL + 'account/'
LOGOUT_URL = PROJECT_URL + 'account/logout/'

# Full filesystem path to the project.
PROJECT_ROOT = os.path.dirname(os.path.abspath(
    sys.modules[os.environ['DJANGO_SETTINGS_MODULE']].__file__))
# sys.path.append(os.path.join(PROJECT_ROOT, 'apps'))

# Name of the directory for the project.
PROJECT_DIRNAME = PROJECT_ROOT.split(os.sep)[-1]

# Every cache key will get prefixed with this value - here we set it to
# the name of the directory the project is in to try and use something
# project specific.
CACHE_MIDDLEWARE_KEY_PREFIX = PROJECT_DIRNAME

# URL prefix for static files.
# Example: 'http://media.lawrence.com/static/'
STATIC_URL = '/static/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' 'static/' subdirectories and in STATICFILES_DIRS.
# Example: '/home/media/media.lawrence.com/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, STATIC_URL.strip('/'))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: 'http://media.lawrence.com/media/', 'http://example.com/media/'
MEDIA_URL = '/media/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: '/home/media/media.lawrence.com/media/'
MEDIA_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.strip('/'))

# Annotations
ANNOTATIONS_URL = 'uploads/annotations/'
ANNOTATIONS_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.strip('/'),
                                ANNOTATIONS_URL.strip('/'))

make_path(ANNOTATIONS_ROOT)

# Images uploads
UPLOAD_IMAGES_URL = 'uploads/images/'
UPLOAD_IMAGES_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.strip('/'),
                                  UPLOAD_IMAGES_URL.strip('/'))

make_path(UPLOAD_IMAGES_ROOT)

# Image cache
IMAGE_CACHE_URL = 'uploads/images/tmp/'
IMAGE_CACHE_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.strip('/'),
                                IMAGE_CACHE_URL.strip('/'))

make_path(IMAGE_CACHE_ROOT)

# Package/module name to import the root urlpatterns from for the project.
ROOT_URLCONF = '%s.urls' % PROJECT_DIRNAME

CUSTOM_STATIC_PATH = os.path.join(PROJECT_ROOT, 'customisations', 'static')

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like '/home/html/static' or 'C:/www/django/static'.
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # use this for your project customisations of digipal
    os.path.join(CUSTOM_STATIC_PATH).replace('\\', '/'),
)

make_path(os.path.join(PROJECT_ROOT, 'customisations'))
make_path(CUSTOM_STATIC_PATH)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #        'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

################
# APPLICATIONS #
################

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.redirects',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'mezzanine.boot',
    'mezzanine.conf',
    'mezzanine.core',
    'mezzanine.generic',
    'mezzanine.blog',
    'mezzanine.forms',
    'mezzanine.pages',
    'mezzanine.galleries',
    'mezzanine.twitter',
    'pagination',
    'tinymce',
)

###############
# MIDDLEWARES #
###############

# List of processors used by RequestContext to populate the context.
# Each one should be a callable that takes the request object as its
# only parameter and returns a dictionary to add to the context.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # You can override app templates in the project/templates folder
            os.path.join(PROJECT_ROOT, 'templates'),
            # DigiPal app can also override other app templates
            os.path.join(PROJECT_ROOT, '../digipal/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                # Only add this if you want the sql queries and debug variables in your template
                # Only activated in debug mode
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
                "django.template.context_processors.tz",
                'django.contrib.messages.context_processors.messages',

                'django.template.context_processors.request',

                # Mezzzanine
                'mezzanine.conf.context_processors.settings',
                'mezzanine.pages.context_processors.page',

                # DigiPal
                'digipal.processor.digipal_site_context',
            ]
        },
    }
]


# List of middleware classes to use. Order is important; in the request phase,
# this middleware classes will be applied in the order given, and in the
# response phase the middleware will be applied in reverse order.
MIDDLEWARE_CLASSES = (
    'digipal.middleware.HttpsAdminMiddleware',

    'mezzanine.core.middleware.UpdateCacheMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Authentication using REMOTE_USER
    # GN 09/05/13: Commented out, see Mantis #5585
    # This was preventing us from testing the site as a non-staff user
    # or log in as a different staff user.
    # 'django.contrib.auth.middleware.RemoteUserMiddleware',

    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'mezzanine.core.request.CurrentRequestMiddleware',
    'mezzanine.core.middleware.RedirectFallbackMiddleware',
    'mezzanine.core.middleware.TemplateForDeviceMiddleware',
    'mezzanine.core.middleware.TemplateForHostMiddleware',
    'mezzanine.core.middleware.AdminLoginInterfaceSelectorMiddleware',
    'mezzanine.core.middleware.SitePermissionMiddleware',
    'mezzanine.pages.middleware.PageMiddleware',
    'mezzanine.core.middleware.FetchFromCacheMiddleware',

    'pagination.middleware.PaginationMiddleware',

    # Uncomment the following if using any of the SSL settings:
    # 'mezzanine.core.middleware.SSLRedirectMiddleware',
    "django.middleware.gzip.GZipMiddleware",
    'digipal.middleware.ErrorMiddleware',
)

###################
# ADMIN DASHBOARD #
###################

ADMIN_MENU_ORDER = (
    ('Web Content', ('blog.BlogPost', 'pages.Page', 'digipal.CarouselItem',
                     'generic.Keyword', 'generic.ThreadedComment',
                     ('Media Library', 'fb_browse'))),
    ('Image', ('digipal.Image', 'digipal.MediaPermission')),
    ('Text', ('digipal_text.TextContentXML', 'digipal_text.TextContent',
              'digipal_text.TextContentType', 'digipal_text.TextContentXMLStatus',
              'digipal.Text')),
    ('Item', ('digipal.HistoricalItem', 'digipal.CurrentItem', 'digipal.ItemPart',
              'digipal.HistoricalItemType', 'digipal.Format', 'digipal.Category',
              'digipal.ItemPartType', )),
    ('Hand', ('digipal.Hand', 'digipal.Scribe', 'digipal.Script')),
    ('Annotation', ('digipal.Annotation',
                    'digipal.Graph', 'digipal.ImageAnnotationStatus')),
    ('Symbol', ('digipal.Ontograph', 'digipal.OntographType', 'digipal.Character',
                'digipal.Allograph', 'digipal.Idiograph', 'digipal.Language',
                'digipal.LatinStyle', 'digipal.Alphabet',
                'digipal.CharacterForm')),
    ('Descriptor', ('digipal.Component', 'digipal.Feature',
                    'digipal.ComponentFeature', 'digipal.Aspect',
                    'digipal.Appearance')),
    ('Actor', ('digipal.Person', 'digipal.Owner', 'digipal.OwnerType',
               'digipal.Repository', 'digipal.Institution',
               'digipal.InstitutionType')),
    ('Location', ('digipal.Place', 'digipal.PlaceType',
                  'digipal.Region', 'digipal.County')),
    ('Admin', ('auth.User', 'auth.Group', 'conf.Setting', 'sites.Site',
               'redirects.Redirect', 'digipal.RequestLog', 'admin.LogEntry')),
)

ADMIN_MENU_COLLAPSED = True

DASHBOARD_TAGS = (
    ("mezzanine_tags.app_list", "blog_tags.quick_blog"),
    ("comment_tags.recent_comments",),
    ("mezzanine_tags.recent_actions",),
)

# SITEMAP GENERATION (see python manage.py sitemap)
# List of DigiPal models to list in the sitemap
# DEPRECATED, use MODELS_PUBLIC instead
# SITEMAP_MODELS = ['ItemPart', 'Hand', 'Scribe', 'Image']
# The website root URL (with trailing slash)
SITEMAP_PATH_TO_RESOURCE = 'http://www.digipal.eu/'

# Store these package names here as they may change in the future since
# at the moment we are using custom forks of them.
PACKAGE_NAME_FILEBROWSER = 'filebrowser_safe'
PACKAGE_NAME_GRAPPELLI = 'grappelli_safe'

#########################
# APPLICATIONS SETTINGS #
#########################

# DigiPal Applications
INSTALLED_APPS = INSTALLED_APPS + (
    'digipal',
    'digipal_text',
    'reversion',
)

# Grappelli
GRAPPELLI_ADMIN_TITLE = 'DigiPal'

##################
# IMAGE SERVER   #
##################

# IMAGE_SERVER_WEB_ROOT is now only used for the migration script
IMAGE_SERVER_WEB_ROOT = 'jp2'
IMAGE_SERVER_HOST = 'digipal.cch.kcl.ac.uk'
IMAGE_SERVER_PATH = '/iip/iipsrv.fcgi'
# IMAGE_SERVER_METADATA = '%s?FIF=%s&amp;OBJ=Max-size'
# IMAGE_SERVER_METADATA_REGEX = r'^.*?Max-size:(\d+)\s+(\d+).*?$'
IMAGE_SERVER_ZOOMIFY = 'http://%s%s?zoomify=%s/'
IMAGE_SERVER_FULL = 'http://%s%s?FIF=%s&amp;RST=*&amp;QLT=100&amp;CVT=JPG'
IMAGE_SERVER_THUMBNAIL = 'http://%s%s?FIF=%s&amp;RST=*&amp;HEI=35&amp;CVT=JPG'
# TODO: move that to the view!
IMAGE_SERVER_THUMBNAIL_HEIGHT = 35
IMAGE_SERVER_RGN = 'http://%s%s?FIF=%s&%s&RGN=%0.6f,%0.6f,%0.6f,%0.6f&CVT=JPEG'
IMAGE_SERVER_EXT = 'jp2'
# Set this to 1.0 if you are using IIPSrv >= 1.0
IMAGE_SERVER_VERSION = 1.0
# When True, all images on the website will have a relative URL
# IMAGE_SERVER_HOST is therfore ignored.
# Added this for the Docker instance where all requests (images and others)
# go through the same web server.
IMAGE_URLS_RELATIVE = False

# DJANGO-IIPIMAGE

# The URL of the IIP image server (e.g.
# http://www.mydomain.com/iip/iipsrv.fcgi)
IMAGE_SERVER_URL = 'http://%s%s' % (IMAGE_SERVER_HOST, IMAGE_SERVER_PATH)
# The absolute filesystem path of the images served by the image server (e.g. /home/myimages)
# It should match iipserver FILESYSTEM_PREFIX parameter
IMAGE_SERVER_ROOT = '/vol/digipal2/images'
# python manage.py dpim will look under IMAGE_SERVER_ROOT +
# IMAGE_SERVER_UPLOAD_ROOT for new images to upload
IMAGE_SERVER_UPLOAD_ROOT = 'jp2'
# python manage.py dpim will look under IMAGE_SERVER_ROOT +
# IMAGE_SERVER_ORIGINALS_ROOT for original images
IMAGE_SERVER_ORIGINALS_ROOT = 'originals'
# file extensions eligible for upload
IMAGE_SERVER_UPLOAD_EXTENSIONS = ('.jp2', '.jpg', '.tif', '.bmp', '.jpeg')
# The path relative to IMAGE_SERVER_ROOT where the images uploaded via the
# admin interface will be created
IMAGE_SERVER_ADMIN_UPLOAD_DIR = os.path.join(
    IMAGE_SERVER_UPLOAD_ROOT, 'admin-upload')

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

#########################
#         SEARCH        #
#########################

# Search page
# The slug of the CMS Page that contains the help about the search interface
SEARCH_HELP_PAGE_SLUG = 'how-to-use-digipal'
SEARCH_INDEX_PATH = os.path.join(PROJECT_ROOT, 'search')

# Set this to True to let the quick search box go to the faceted search page
# If False, goes to the advanced search page
QUICK_SEARCH_TO_FACETS = True

# If True the auto complete is enabled on the search page
AUTOCOMPLETE_PUBLIC_USER = True

#########################
# OPTIONAL APPLICATIONS #
#########################

# These will be added to ``INSTALLED_APPS``, only if available.
OPTIONAL_APPS = (
    'django_extensions',
    PACKAGE_NAME_FILEBROWSER,
    PACKAGE_NAME_GRAPPELLI,
    'lightbox',
)

# Allowed file extensions in Filebrowser app (used by Mezzanine Gallery)
# It is a copy of filebrowser_safe/settings.py:EXTENSIONS
# without svg and tif (not all tif formats are supported by Chrome).
# See AC #20 / PHDPAL-7
FILEBROWSER_EXTENSIONS = {
    'Folder': [''],
    'Image': ['.jpg', '.jpeg', '.gif', '.png'],
    'Video': ['.mov', '.wmv', '.mpeg', '.mpg', '.avi', '.rm', '.mp4'],
    'Document': ['.pdf', '.doc', '.rtf', '.txt', '.xls', '.csv', '.docx'],
    'Audio': ['.mp3', '.wav', '.aiff', '.midi', '.m4p'],
    'Code': ['.html', '.py', '.js', '.css']
}

########
# LOGS #
########

# Send an email to the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

# Log DigiPal framework messages into digipal.log
# One of DEBUG, INFO, WARNING, ERROR, CRITICAL
# see digipal.utils.dplog()
# USE 'ERROR' ON PRODUCTION SITE
DIGIPAL_LOG_LEVEL = 'ERROR'

# Log SQL statements into digipal.log
# INDEPENDENT FROM DIGIPAL_LOG_LEVEL
# USE False ON PRODUCTION SITE
DJANGO_LOG_SQL = False

# Log the duration of each http response from django into digipal.log
# also internal operations (search, indexing)
# See middleware,py
# Only if DIGIPAL_LOG_LEVEL >= DEBUG
# USE False ON PRODUCTION SITE
DEBUG_PERFORMANCE = False

PROJECT_LOG_PATH = os.path.join(PROJECT_ROOT, 'logs')
make_path(PROJECT_LOG_PATH)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'digipal_debug': {
            'format': '[%(asctime)s] %(levelname)s %(message)s (%(module)s)',
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        # see digipal.utils.dplog()
        'digipal_debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'digipal_debug',
            'filename': os.path.join(PROJECT_LOG_PATH, 'digipal.log'),
            'backupCount': 10,
            'maxBytes': 10 * 1024 * 1024,
        },
        'digipal_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'digipal_debug',
            'filename': os.path.join(PROJECT_LOG_PATH, 'error.log'),
            'backupCount': 10,
            'maxBytes': 10 * 1024 * 1024,
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['digipal_error', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        # see digipal.utils.dplog()
        'digipal_debugger': {
            'handlers': ['digipal_debug'],
            'level': DIGIPAL_LOG_LEVEL,
            'propagate': False,
        },
    },
}

# Let's ignore some of the warnings for future django version

WARNINGS_IGNORED = [
    'RemovedInDjango18Warning2',
]


class filter_django_warnings(logging.Filter):
    def filter(self, record):
        for ignored in WARNINGS_IGNORED:
            if ignored in record.args[0]:
                return False
        return True


warn_logger = logging.getLogger('py.warnings')
warn_logger.addFilter(filter_django_warnings())

##################
#     BACKUPS    #
##################

DB_BACKUP_PATH = os.path.join(PROJECT_ROOT, 'backups')
make_path(DB_BACKUP_PATH)

# Front-end message for images which are inheriting unspecified media
# permission from their repository
# TODO: don't ahrdcode the url
UNSPECIFIED_MEDIA_PERMISSION_MESSAGE = '''<p>A full image of this page is not yet
    available. For further details see <a href="/about/acknowledgements-image-rights/">Acknowledgements and Image
    Rights</a>.</p>'''

# ADMIN CUSTOMISATIONS
# If True a custom and simplified form to add a new Item Part record will be used
# Typically found at /admin/digipal/itempart/add/
USE_ITEM_PART_QUICK_ADD_FORM = True

ADMIN_FORCE_HTTPS = False

# We add blogpost to OWNABLE_MODELS_ALL_EDITABLE
# That way all the posts are visible to everyone
# Otherwise only visible to owner or superuser.
try:
    OWNABLE_MODELS_ALL_EDITABLE
except NameError:
    OWNABLE_MODELS_ALL_EDITABLE = []

OWNABLE_MODELS_ALL_EDITABLE.append('blog.blogpost')

# ----------------------------------------------------------------------------

##################
#     CACHE      #
##################

# DJANGO COMPRESSOR
# True => Combine all resources into a single file
COMPRESS_ENABLED = True

INSTALLED_APPS = INSTALLED_APPS + ('compressor',)
STATICFILES_FINDERS = STATICFILES_FINDERS + \
    ('compressor.finders.CompressorFinder',)

DJANGO_CACHE_PATH = os.path.join(PROJECT_ROOT, 'django_cache')
make_path(DJANGO_CACHE_PATH)


# CACHING (make sure it is persistent otherwise files are recompiled each time
# the app restarts)
# FILE_BASED_CACHE_BACKEND = 'django.core.cache.backends.filebased.FileBasedCache'
FILE_BASED_CACHE_BACKEND = 'digipal.middleware.FileBasedCacheArchetype'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'django-compressor': {
        'BACKEND': FILE_BASED_CACHE_BACKEND,
        'LOCATION': os.path.join(DJANGO_CACHE_PATH, 'django_compressor'),
        'TIMEOUT': 60 * 60 * 24,
        'MAX_ENTRIES': 300,
    },
    'digipal_faceted_search': {
        'BACKEND': FILE_BASED_CACHE_BACKEND,
        'LOCATION': os.path.join(DJANGO_CACHE_PATH, 'faceted_search'),
        'TIMEOUT': 60 * 60 * 24,
        # 'TIMEOUT': 1,
        'MAX_ENTRIES': 300,
    },
    'digipal_compute': {
        'BACKEND': FILE_BASED_CACHE_BACKEND,
        'LOCATION': os.path.join(DJANGO_CACHE_PATH, 'compute'),
        'TIMEOUT': 60 * 60 * 24,
        # 'TIMEOUT': 1,
        'MAX_ENTRIES': 300,
    },
    'digipal_text_patterns': {
        'BACKEND': FILE_BASED_CACHE_BACKEND,
        'LOCATION': os.path.join(DJANGO_CACHE_PATH, 'text_patterns'),
        'TIMEOUT': 60 * 60 * 24,
        # 'TIMEOUT': 1,
        'MAX_ENTRIES': 300,
    }
}

# Uncomment this to force less to ALWAYS be compiled, even when not changed
# Slow but useful when making changes to css
# CACHES['django-compressor'] = CACHES['default']

# Mezzanine settings var reuire as soon as we use django cache
NEVERCACHE_KEY = 'NOCACHE'

COMPRESS_CACHE_BACKEND = 'django-compressor'

# Preprocessing of the CSS
# ONLY if COMPRESS_ENABLED == True
COMPRESS_CSS_FILTERS = [
    # NECESSARY on production site to avoid rel refs to non existent images
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]

# Compiling LESS to CSS
# ALWAYS (even when COMPRESS_ENABLED == False)
COMPRESS_PRECOMPILERS = (
    ('text/less', 'digipal.compressor_filters.LessAndCssAbsoluteFilter'),
    ('text/typescript', 'tsc {infile} --out {outfile}'),
)
# ----------------------------------------------------------------------------

##################
#     TINY MCE   #
##################

TINYMCE_DEFAULT_CONFIG = {
    'language': "en",

    'width': '700',
    'height': '200',
    'fix_list_elements': True,
    'forced_root_block': "p",
    'remove_trailing_nbsp': True,
    'relative_urls': False,

    # theme_advanced
    'theme_advanced_toolbar_location': "top",
    'theme_advanced_toolbar_align': "left",
    'theme_advanced_statusbar_location': "",
    'theme_advanced_buttons1': "bold,italic,|,link,unlink,|,image,|,charmap,|,code,|,table,|,bullist,numlist,blockquote,|,undo,redo,|,formatselect",
    'theme_advanced_buttons2': "",
    'theme_advanced_buttons3': "",
    'theme_advanced_blockformats': "p,h1,h2,h3,h4,h5,h6,pre",

    'plugins': "paste,table",

    # remove MS Word's inline styles when copying and pasting.
    'paste_remove_spans': True,
    'paste_auto_cleanup_on_paste': True,
    'paste_remove_styles': True,
    'paste_remove_styles_if_webkit': True,
    'paste_strip_class_attributes': True
}

##################
#     DIGIPAL    #
##################

# Annotator Settings
ANNOTATOR_ZOOM_LEVELS = 7
# Zoom Increment for the OpenLayers/Zoomify viewer
# Lower value for smaller increments (OL default = 2)
ANNOTATOR_ZOOM_FACTOR = 1.4

# Show ms date on annotator?
PAGE_IMAGE_SHOW_MSDATE = False
# Show MS summary on annotator?
PAGE_IMAGE_SHOW_MSSUMMARY = False

# See /digipal/doc/http-api.md for instructions
API_PERMISSIONS = [['crud', 'ALL']]

# Models Exposure
# List of models we want to show to everyone and to staff respectively
MODELS_PUBLIC = ['itempart', 'image', 'graph',
                 'hand', 'scribe', 'textcontentxml']
MODELS_PRIVATE = ['itempart', 'image', 'graph',
                  'hand', 'scribe', 'textcontentxml']

# which text type is used as primary a reference for markup-up - image links
TEXT_IMAGE_MASTER_CONTENT_TYPE = 'transcription'

# Lightbox Settings
LIGHTBOX = True

# Hand/Legacy
HISTORICAL_ITEM_TYPES = ['charter', 'manuscript']
INSTITUTION_TYPES = ['medieval institution', 'modern repository']
UNKOWN_PLACE_NAME = '000000'

SOURCE_CLA = 'cla'
SOURCE_GNEUSS = 'gneuss'
SOURCE_KER = 'ker'
SOURCE_SCRAGG = 'scragg'
SOURCE_SAWYER = 'sawyer'
SOURCE_SAWYER_KW = 'electronic'
SOURCE_PELTERET = 'pelteret'
# the id of the source record for this project
SOURCE_PROJECT_ID = 8
SOURCE_PROJECT_NAME = 'DigiPal Project'
CHARACTER_ABBREV_STROKE = 'abbrev.stroke'

ITEM_PART_DEFAULT_LOCUS = 'face'

# ##

# set this to True in your local_settings if the site is maintained
# by King's Digital Lab. LEAVE IT False here.
# This will show the KDL cookie/privacy policy at the bottom of the page
# ONLY is this is True AND DEBUG = False
KDL_MAINTAINED = False

####

TEXT_EDITOR_OPTIONS = {
    'buttons': {
        'psclause': 'Address,Disposition,Witnesses',
        'psClauseSecondary': 'Arenga,Boundaries,Holding,Injunction,Malediction,Narration,Notification,Prohibition,Salutation,Sealing,Subscription,Intitulatio,Warrandice'
    },
    'toolbars': {
        'default': 'psclear undo redo pssave | psconvert | psclause | psClauseSecondary | psperson | pslocation | psex pssupplied psdel | code ',
    },
    'panels': {
        'north': {
            'ratio': 0.6
        },
        'east': {
            'ratio': 0.5
        },
    }
}

##################
# LOCAL SETTINGS #
##################

CUSTOM_APPS = []

# from PROJECT_PACKAGE.local_settings import *'
# Where PROJECT_PACKAGE is the Django package for your project
try:
    local_settings = importlib.import_module(
        '..local_settings', os.environ['DJANGO_SETTINGS_MODULE'])
    module_dict = local_settings.__dict__
    try:
        to_import = local_settings.__all__
    except AttributeError:
        to_import = [name for name in module_dict if not name.startswith('_')]
    for name in to_import:
        globals().update({name: module_dict[name]})
except ImportError:
    # no local_settings.py
    print 'WARNING: local_settings.py not found'
    pass

# DJANGO DEBUG INFO get logged into our debug log file
# This includes the SQL statements
if DJANGO_LOG_SQL and LOGGING:
    LOGGING['loggers']['django.db.backends'] = {
        'handlers': ['digipal_debug'],
        'level': 'DEBUG',
        'propagate': False,
    }

LOGGING['loggers']['digipal_debugger']['level'] = DIGIPAL_LOG_LEVEL

# See http://stackoverflow.com/questions/26682413/django-rotating-file-handler-stuck-when-file-is-equal-to-maxbytes/32011192#32011192
# Deactivate log for the parent process of runserver, children will have the log
# This is to avoid errors when the log rotates and the parent process
# still has a handle of the file
RUNNING_DEVSERVER = (len(sys.argv) > 1 and sys.argv[1] == 'runserver')
if RUNNING_DEVSERVER and DEBUG and os.environ.get('RUN_MAIN', None) != 'true':
    LOGGING = {}


import collections


def merge_dic(d, u):
    # like d.update(u) but it will only enrich d rather than remove missing
    # entries
    # see https://stackoverflow.com/a/3233356/3748764
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            d[k] = merge_dic(d.get(k, {}), v)
        else:
            d[k] = v
    return d


if 'TEXT_EDITOR_OPTIONS_CUSTOM' in locals():
    # TEXT_EDITOR_OPTIONS.update(locals()['TEXT_EDITOR_OPTIONS_CUSTOM'])
    merge_dic(TEXT_EDITOR_OPTIONS, locals()['TEXT_EDITOR_OPTIONS_CUSTOM'])

#
if not COMPRESS_ENABLED:
    CACHES['django-compressor'] = CACHES['default']


INSTALLED_APPS = INSTALLED_APPS + tuple(CUSTOM_APPS)

####################
# DYNAMIC SETTINGS #
####################

# set_dynamic_settings() will rewrite globals based on what has been
# defined so far, in order to provide some better defaults where
# applicable. We also allow this settings module to be imported
# without Mezzanine installed, as the case may be when using the
# fabfile, where setting the dynamic settings below isn't strictly
# required.
try:
    from mezzanine.utils.conf import set_dynamic_settings
except ImportError:
    pass
else:
    set_dynamic_settings(globals())
