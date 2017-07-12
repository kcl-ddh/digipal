from mezzanine.conf import register_setting

# http://mezzanine.jupo.org/docs/configuration.html#reading-settings
'''
Mezzanine rules:
    * registered settings can also be in settings.py but only if value = default
    * IF VARIABLE ALSO IN SETTINGS THEN IT WON'T SHOW UP IN THE ADMIN INTERFACE
    * if different, the value from settings.py is used
    * if absent or =default, the value from database is used

    * in the admin form, mezzanine uses the first token of the name to group
      variables. e.g. THUMB_MAX_LENGTH => THUMB


'''

# Make some settings.py variables accessible in the django template context
# They'll be accessed in the template using {{ settings.X }}
register_setting(
    name="TEMPLATE_ACCESSIBLE_SETTINGS",
    description="Sequence of setting names available within templates.",
    editable=False,
    default=(
        'ADMIN_STYLES', 'BANNER_LOGO_HTML', 'SHOW_QUICK_SEARCH_SCOPES',
        'GITHUB', 'TWITTER',
        'DP_BUILD_NUMBER', 'DP_BUILD_TIMESTAMP', 'DP_BUILD_BRANCH',
        'QUICK_SEARCH_TO_FACETS',
        'ARCHETYPE_THUMB_LENGTH_MIN', 'ARCHETYPE_THUMB_LENGTH_MAX',
        'FOOTER_LOGO_LINE', 'DEBUG',
        # A way to silence Mezzanine warning when django calls
        # dir(context['settings'])
        # where context['settings'] is a TemplateSettings()
        '__methods__', '__members__'
    ),
    append=True,
)

'''
The following settings will be saved in the Database and override the settings.py
ones IF and ONLY IF the variable not in settings.py OR value = default.
'''
# Build information, see repo.py and dpdb.py
register_setting(
    name="DP_BUILD_NUMBER",
    description="DigiPal Build Number",
    editable=True,
    default=0,
)

register_setting(
    name="DP_BUILD_TIMESTAMP",
    description="DigiPal Build Date Time",
    editable=True,
    default='',
)

register_setting(
    name="DP_BUILD_BRANCH",
    description="DigiPal Build Branch",
    editable=True,
    default='',
)

# Build information, see repo.py and dpdb.py
register_setting(
    name="ARCHETYPE_THUMB_LENGTH_MIN",
    label="Thumb Min Size",
    description="Minimum size of annotation thumbnails (in pixel)",
    editable=True,
    default=50,
)

register_setting(
    name="ARCHETYPE_THUMB_LENGTH_MAX",
    label="Thumb Max Size",
    description="Maximum size of annotation thumbnails (in pixel)",
    editable=True,
    default=300,
)

# Prevent TinyMCE from stripping the tags and attributes necessary to
# embed video in the blog posts.

register_setting(
    name="RICHTEXT_ALLOWED_TAGS",
    append=True,
    default=("object", "embed", "iframe"),  # etc
)

register_setting(
    name="RICHTEXT_ALLOWED_ATTRIBUTES",
    append=True,
    default=("frameborder", "webkitAllowFullScreen",
             "mozallowfullscreen", "allowFullScreen"),  # etc
)

register_setting(
    name="SITE_TITLE",
    editable=True,
    default='My Archetype Site'
)
