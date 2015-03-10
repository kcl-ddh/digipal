# Template file for local settings.
# Do NOT change settings.py instead copy this to local_settings.py, change it
# to suite the environment, but do NOT commit it to version control.
DEBUG = True

PROJECT_URL = '/'

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS
STATICFILES_DIRS = (
        # Put strings here, like '/home/html/static' or 'C:/www/django/static'.
        # Always use forward slashes, even on Windows.
        # Don't forget to use absolute paths, not relative paths.
)

SHOW_QUICK_SEARCH_SCOPES = True

"""
Although any DB may be used, we recommend to use PostgresQL, since no other DB has been tested to be working with Digipal except this.
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'digipal',
        'USER': 'app_digipal',
        'PASSWORD': 'dppsqlpass',
        'HOST': '',
        'PORT': '',
    }
}


# Lightbox
"""
The Lightbox is a separate project, even though it's still tightly linked to Digipal. It is possible to install it through pip:
>>> pip install git+https://github.com/Gbuomprisco/Digital-Lightbox.git
By default, it is disabled. You can enable it by setting the variable LIGHTBOX in your settings:
"""
LIGHTBOX = True

# Mezzanine
SITE_TITLE = 'ProjectName'

# Social
"""
The following variables contains the URLs/username to social networking sites.
- The TWITTER variable asks for the Twitter username.
- The GITHUB variable asks for the relative URL to your Github project or account
- The COMMENTS_DISQUS_SHORTNAME asks for the Disqus shortname
"""
TWITTER = 'TwitterUsername'
GITHUB = 'GithubUsername/ProjectName'
COMMENTS_DISQUS_SHORTNAME = "yourDisqusName"

# Annotator Settings

"""
If True, this setting will reject every change to the DB. To be used in production websites.
"""
REJECT_HTTP_API_REQUESTS = False    # if True, prevents any change to the DB

"""
This setting allows to set the number of zoom levels available in the OpenLayers layer.
"""
ANNOTATOR_ZOOM_LEVELS = 7   # This setting sets the number of zoom levels of O

