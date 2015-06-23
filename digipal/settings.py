# -*- coding: utf-8 -*-

#######################################################################
# DO NOT CHANGE SETTINGS IN THIS FILE, ONLY ADD NEW SENSIBLE DEFAULTS #
# FOR MORE INFORMATION SEE local_settings_template.py.                #
#######################################################################

import os
import sys

gettext = lambda s: s

def make_path(path):
    if not os.path.exists(path):
        os.makedirs(path)

########################
# MAIN DJANGO SETTINGS #
########################

# Emails will be sent on server errors if DEBUG=False
# Add admin email addresses in your local_settings.py
ADMINS = ()
#SERVER_EMAIL = 'django@text.com'
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

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
        )

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
            'ENGINE': 'django.db.backends.',
            'NAME': '',
            'USER': '',
            'PASSWORD': '',
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
PROJECT_ROOT = os.path.dirname(os.path.abspath(sys.modules[os.environ['DJANGO_SETTINGS_MODULE']].__file__))
sys.path.append(os.path.join(PROJECT_ROOT, 'apps'))

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

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: 'http://foo.com/media/', '/media/'.
##ADMIN_MEDIA_PREFIX = STATIC_URL + 'grappelli/'

# Package/module name to import the root urlpatterns from for the project.
ROOT_URLCONF = '%s.urls' % PROJECT_DIRNAME

# Put strings here, like '/home/html/django_templates'
# or 'C:/www/django/templates'.
# Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
TEMPLATE_DIRS = [os.path.join(PROJECT_ROOT, 'templates'), os.path.join(PROJECT_ROOT, '../digipal/templates'),]

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

# SOUTH_MIGRATION_MODULES = {
#     'taggit': 'taggit.south_migrations',
# }

###############
# MIDDLEWARES #
###############

# List of processors used by RequestContext to populate the context.
# Each one should be a callable that takes the request object as its
# only parameter and returns a dictionary to add to the context.
TEMPLATE_CONTEXT_PROCESSORS = (
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        # Only add this if you want the sql queries and debug variables in your template
        # Only activated in debug mode
        'django.core.context_processors.debug',
        'django.core.context_processors.i18n',
        'django.core.context_processors.static',
        'django.core.context_processors.media',
        'django.core.context_processors.request',
        "django.core.context_processors.tz",
        'mezzanine.conf.context_processors.settings',
        'digipal.processor.quick_search',
        'mezzanine.pages.context_processors.page',
        )

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
        #'django.contrib.auth.middleware.RemoteUserMiddleware',

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
        )

###################
# ADMIN DASHBOARD #
###################

ADMIN_MENU_ORDER = (
    ('Web Content', ('blog.BlogPost', 'pages.Page', 'digipal.CarouselItem', 'generic.Keyword', 'generic.ThreadedComment', ('Media Library', 'fb_browse'))),
    ('Item', ('digipal.HistoricalItem', 'digipal.CurrentItem', 'digipal.ItemPart', 'digipal.HistoricalItemType', 'digipal.Format', 'digipal.Category', 'digipal.ItemPartType', )),
    ('Image', ('digipal.Image', 'digipal.MediaPermission')),
    ('Hand', ('digipal.Hand', 'digipal.Scribe', 'digipal.Script')),
    ('Annotation', ('digipal.Annotation', 'digipal.Graph', 'digipal.ImageAnnotationStatus')),
    ('Symbol', ('digipal.Ontograph', 'digipal.OntographType', 'digipal.Character', 'digipal.Allograph', 'digipal.Idiograph', 'digipal.Language', 'digipal.LatinStyle', 'digipal.Alphabet', 'digipal.CharacterForm')),
    ('Descriptor', ('digipal.Component', 'digipal.Feature', 'digipal.ComponentFeature', 'digipal.Aspect', 'digipal.Appearance')),
    ('Actor', ('digipal.Person', 'digipal.Owner', 'digipal.OwnerType', 'digipal.Repository', 'digipal.Institution', 'digipal.InstitutionType')),
    ('Location', ('digipal.Place', 'digipal.PlaceType', 'digipal.Region', 'digipal.County')),
    ('Admin', ('auth.User', 'auth.Group', 'conf.Setting', 'sites.Site', 'redirects.Redirect', 'digipal.RequestLog', 'admin.LogEntry')),
    ('Text Content', ('digipal.Text', 'digipal_text.TextContent', 'digipal_text.TextContentType', 'digipal_text.TextContentXML', 'digipal_text.TextContentXMLStatus')),
)

ADMIN_MENU_COLLAPSED = True

DASHBOARD_TAGS = (
    ("mezzanine_tags.app_list", "blog_tags.quick_blog"),
    ("comment_tags.recent_comments",),
    ("mezzanine_tags.recent_actions",),
)

# SITEMAP GENERATION (see python manage.py sitemap)
# List of DigiPal models to list in the sitemap
SITEMAP_MODELS = ['ItemPart', 'Hand', 'Scribe', 'Image']
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
        'south',
        )

# Grappelli
GRAPPELLI_ADMIN_TITLE = 'DigiPal'

# Hand/Legacy
HISTORICAL_ITEM_TYPES = ['charter', 'manuscript']
INSTITUTION_TYPES = ['medieval institution', 'modern repository']
UNKOWN_PLACE_NAME = '000000'

LEGACY_CATEGORY_REGEX = r'^(\w+).*'
LEGACY_INSTITUTION_DICT = {0: INSTITUTION_TYPES[0], 2: INSTITUTION_TYPES[1]}
LEGACY_LIBRARY_REGEX = r'\[?([^,]*),\s+([^],]*),?\s*([^\]]*)'
LEGACY_MODERN_PERSON = 1
LEGACY_NULL_BOOLEAN_DICT = {-1: True, 0: False, 1: None}
LEGACY_REFERENCE_REGEX = r'[\[\{]([^#]*)#[^#]*[\]\}]?'
LEGACY_REFERENCE_PAGE_REGEX = r'([\[])([^#]*)(#\d*)[^\]]*([\]])'

SOURCE_CLA = 'cla'
SOURCE_GNEUSS = 'gneuss'
SOURCE_KER = 'ker'
SOURCE_SCRAGG = 'scragg'
SOURCE_SAWYER = 'sawyer'
SOURCE_SAWYER_KW = 'electronic'
SOURCE_PELTERET = 'pelteret'
# To be removed, no longer used
#SOURCES = [SOURCE_CLA, SOURCE_GNEUSS, SOURCE_KER, SOURCE_SCRAGG, SOURCE_SAWYER, SOURCE_PELTERET]
# the id of the source record for this project
SOURCE_PROJECT_ID = 8
SOURCE_PROJECT_NAME = 'DigiPal Project'

# To be removed, no longer used
# CATALOGUE_NUMBERS = {'cla_number': SOURCE_CLA,
#         'index': SOURCE_GNEUSS,
#         'ker_index': SOURCE_KER,
#         'scragg': SOURCE_SCRAGG,
#         'sawyer_number': SOURCE_SAWYER,
#         'pelteret_number': SOURCE_PELTERET}

CHARACTER_ABBREV_STROKE = 'abbrev.stroke'

CHOPPER_EXPORTS = os.path.join(MEDIA_ROOT, 'chopper')
CHOPPER_NAMESPACE = {'c': 'http://idp.bl.uk/chopper/standalone'}
CHOPPER_SOURCES = {'G': SOURCE_GNEUSS, 'S': SOURCE_SAWYER}
CHOPPER_CHARACTER_MAPPING = {u'Ã°': 'eth', u'Ã¾': 'thorn', '(punctus)': '.',
        '(punctus elevatus)': './', '(punctus versus)': ';',
        '(punctus uersus)': ';', '(abbrev)': CHARACTER_ABBREV_STROKE,
        '(accent)': 'accent', '(ligature)': 'ligature', '(wynn)': 'wynn',
        'w': 'wynn', 'asc': u'Ã¦', 'll': 'l', 'rr': 'r', 'v': 'u',
        'nasal': CHARACTER_ABBREV_STROKE, ':-': ';'}
CHOPPER_ABBREV_STROKE_MARKER = '['

ITEM_PART_DEFAULT_LOCUS = 'face'

SCRIBE_NAME_PREFIX = 'DigiPal Scribe '

# This appears in the advanced search page
HAND_ID_PREFIX = 'DigiPal Hand '

# Default name used for bulk creation of hands
HAND_DEFAULT_LABEL = 'Default Hand'

STATUS_CHOPPER = 'chopper'
STATUS_DEFAULT = 'draft'
STATUS = [STATUS_DEFAULT, STATUS_CHOPPER]

MAX_THUMB_LENGTH = 50
#MIN_THUMB_LENGTH = 50

# Image Server

# IMAGE_SERVER_WEB_ROOT is now only used for the migration script
IMAGE_SERVER_WEB_ROOT = 'jp2'
IMAGE_SERVER_HOST = 'digipal.cch.kcl.ac.uk'
IMAGE_SERVER_PATH = '/iip/iipsrv.fcgi'
#IMAGE_SERVER_METADATA = '%s?FIF=%s&amp;OBJ=Max-size'
#IMAGE_SERVER_METADATA_REGEX = r'^.*?Max-size:(\d+)\s+(\d+).*?$'
IMAGE_SERVER_ZOOMIFY = 'http://%s%s?zoomify=%s/'
IMAGE_SERVER_FULL = 'http://%s%s?FIF=%s&amp;RST=*&amp;QLT=100&amp;CVT=JPG'
IMAGE_SERVER_THUMBNAIL = 'http://%s%s?FIF=%s&amp;RST=*&amp;HEI=35&amp;CVT=JPG'
# TODO: move that to the view!
IMAGE_SERVER_THUMBNAIL_HEIGHT = 35
IMAGE_SERVER_RGN = 'http://%s%s?FIF=%s&%s&RGN=%0.6f,%0.6f,%0.6f,%0.6f&CVT=JPEG'
IMAGE_SERVER_EXT = 'jp2'
# Set this to 1.0 if you are using IIPSrv >= 1.0
IMAGE_SERVER_VERSION = 0.9

# DJANGO-IIPIMAGE

# The URL of the IIP image server (e.g. http://www.mydomain.com/iip/iipsrv.fcgi)
IMAGE_SERVER_URL  = 'http://%s%s' % (IMAGE_SERVER_HOST, IMAGE_SERVER_PATH)
# The absolute filesystem path of the images served by the image server (e.g. /home/myimages)
# It should match iipserver FILESYSTEM_PREFIX parameter
IMAGE_SERVER_ROOT = '/vol/digipal2/images'
# python manage.py dpim will look under IMAGE_SERVER_ROOT + IMAGE_SERVER_UPLOAD_ROOT for new images to upload
IMAGE_SERVER_UPLOAD_ROOT = 'jp2'
# python manage.py dpim will look under IMAGE_SERVER_ROOT + IMAGE_SERVER_ORIGINALS_ROOT for original images
IMAGE_SERVER_ORIGINALS_ROOT = 'originals'
# file extensions eligible for upload
IMAGE_SERVER_UPLOAD_EXTENSIONS = ('.jp2', '.jpg', '.tif', '.bmp', '.jpeg')
# The path relative to IMAGE_SERVER_ROOT where the images uploaded via the
# admin interface will be created
IMAGE_SERVER_ADMIN_UPLOAD_DIR = os.path.join(IMAGE_SERVER_UPLOAD_ROOT, 'admin-upload')

# Mezzanine
SITE_TITLE = 'DigiPal'

TWITTER = 'DigiPalProject'
GITHUB = 'kcl-ddh/digipal'

# South
SOUTH_TESTS_MIGRATE = False

# DISQUS

COMMENTS_DEFAULT_APPROVED = True

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

# Haystack
# HAYSTACK_CONNECTIONS = {
#     'default': {
#         'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
#     },
#     'whoosh': {
#         'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
#         'PATH': os.path.join(SEARCH_INDEX_PATH, 'haystack'),
#     },
#}

#########################
# OPTIONAL APPLICATIONS #
#########################

# These will be added to ``INSTALLED_APPS``, only if available.
OPTIONAL_APPS = (
        #'debug_toolbar',
        'django_extensions',
        PACKAGE_NAME_FILEBROWSER,
        PACKAGE_NAME_GRAPPELLI,
        'lightbox',
        )

DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS': False}

########
# LOGS #
########

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'digipal_debug': {
                'format': '[%(asctime)s] %(levelname)s %(message)s (%(module)s)',
                'datefmt' : "%d/%b/%Y %H:%M:%S"
            },
        },
        'handlers': {
            'digipal_debug': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'digipal_debug',
                'filename': os.path.join(PROJECT_ROOT, 'logs/debug.log'),
                'backupCount': 10,
                'maxBytes': 10*1024*1024,
            },
            'digipal_error': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'digipal_debug',
                'filename': os.path.join(PROJECT_ROOT, 'logs/error.log'),
                'backupCount': 10,
                'maxBytes': 10*1024*1024,
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
            'digipal_debugger': {
                'handlers': ['digipal_debug'],
                'level': 'DEBUG',
                'propagate': False,
            },
        }
    }

# BACKUPS #

DB_BACKUP_PATH = os.path.join(PROJECT_ROOT, 'backups')
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

# DJANGO COMPRESSOR
# True => Combine all resources into a single file
COMPRESS_ENABLED = True

INSTALLED_APPS = INSTALLED_APPS + ('compressor',)
STATICFILES_FINDERS = STATICFILES_FINDERS + ('compressor.finders.CompressorFinder',)

# CACHING (make sure it is persistent otherwise files are recompiled each time
# the app restarts)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'django-compressor': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(PROJECT_ROOT, 'django_cache/django_compressor/'),
    }
}

# Uncomment this to force less to ALWAYS be compiled, even when not changed
# Slow but useful when making changes to css
#CACHES['django-compressor'] = CACHES['default']

# Mezzanine settings var reuire as soon as we use django cache
NEVERCACHE_KEY = 'NOCACHE'

COMPRESS_CACHE_BACKEND = 'django-compressor'

# Preprocessing of the CSS
# ONLY if COMPRESS_ENABLED == True
COMPRESS_CSS_FILTERS = [
    #'compressor.filters.css_default.CssAbsoluteFilter',
    #'compressor.filters.cssmin.CSSMinFilter',
]

# Compiling LESS to CSS
# ALWAYS (even when COMPRESS_ENABLED == False)
COMPRESS_PRECOMPILERS = (
    #('text/coffeescript', 'coffee --compile --stdio'),
    ('text/less', 'digipal.compressor_filters.LessAndCssAbsoluteFilter'),
    #('text/less', 'lessc {infile}'),
)
# ----------------------------------------------------------------------------

# TINY MCE
TINYMCE_DEFAULT_CONFIG = {
        'language': "en",

        'width': '700',
        'height': '200',
        'fix_list_elements': True,
        'forced_root_block': "p",
        'remove_trailing_nbsp': True,
        'relative_urls' : False,

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
        'paste_auto_cleanup_on_paste' : True,
        'paste_remove_styles': True,
        'paste_remove_styles_if_webkit': True,
        'paste_strip_class_attributes': True
}

# Annotator Settings
ANNOTATOR_ZOOM_LEVELS = 7

# Web API
REJECT_HTTP_API_REQUESTS = False
# See /digipal/doc/http-api.md for instructions
API_PERMISSIONS = [['crud', 'ALL']]

# Models Exposure
# List of models we want to show to everyone and to staff respectively
MODELS_PUBLIC = ['itempart', 'image', 'graph', 'hand', 'scribe'] # 'textcontentxml'
MODELS_PRIVATE = ['itempart', 'image', 'graph', 'hand', 'scribe'] # 'textcontentxml'

# Lightbox Settings
LIGHTBOX = False

##################
# LOCAL SETTINGS #
##################

# from PROJECT_PACKAGE.local_settings import *'
# Where PROJECT_PACKAGE is the Django package for your project
import importlib
try:
    local_settings = importlib.import_module('..local_settings', os.environ['DJANGO_SETTINGS_MODULE'])
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

#
