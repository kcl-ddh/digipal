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
        'ARCHETYPE_GITHUB', 'ARCHETYPE_TWITTER',
        'DP_BUILD_NUMBER', 'DP_BUILD_TIMESTAMP', 'DP_BUILD_BRANCH',
        'QUICK_SEARCH_TO_FACETS',
        'ARCHETYPE_THUMB_LENGTH_MIN', 'ARCHETYPE_THUMB_LENGTH_MAX',
        'FOOTER_LOGO_LINE', 'DEBUG', 'ARCHETYPE_SEARCH_HELP_URL',
        'KDL_MAINTAINED',
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
    default=u'',
)

register_setting(
    name="DP_BUILD_BRANCH",
    description="DigiPal Build Branch",
    editable=True,
    default=u'',
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

register_setting(
    name="ARCHETYPE_API_READ_ONLY",
    label="API Read Only",
    description="If set, the Web API is read only",
    editable=True,
    default=False,
)

register_setting(
    name="ARCHETYPE_ANNOTATION_TOOLTIP_SHORT",
    label="Annotation tooltip (short)",
    description="Template for the annotation short tooltips",
    editable=True,
    default=u'{allograph} by {hand}\n {locus}',
)

register_setting(
    name="ARCHETYPE_ANNOTATION_TOOLTIP_LONG",
    label="Annotation tooltip (long)",
    description="Template for the annotation long tooltips",
    editable=True,
    default=u'{allograph} by {hand}\n {ip} {locus}\n ({hi_date})',
)

register_setting(
    name="ARCHETYPE_SCRIBE_NAME_PREFIX",
    label="Scribe name prefix",
    description="Prefix added to the scribe names",
    editable=True,
    default=u'DigiPal Scribe',
)

register_setting(
    name="ARCHETYPE_HAND_ID_PREFIX",
    label="Hand ID prefix",
    description="Prefix added to the hand IDs",
    editable=True,
    default=u'DigiPal Hand',
)

register_setting(
    name="ARCHETYPE_HAND_LABEL_DEFAULT",
    label="Hand default label",
    description="Default name used for bulk creation of hands",
    editable=True,
    default=u'Default Hand',
)

register_setting(
    name="ARCHETYPE_TWITTER",
    label="Twitter handler",
    description="Your project twitter handler",
    editable=True,
    default=u'DigiPalProject',
)

register_setting(
    name="ARCHETYPE_GITHUB",
    label="Github handler",
    description="Your project github handler",
    editable=True,
    default=u'kcl-ddh/digipal',
)

register_setting(
    name="ARCHETYPE_GOOGLE_SHORTENER_CLIENTID",
    label="Google Short URL Client ID",
    description="Google Short URL Client ID",
    editable=True,
    default=u'',
)

register_setting(
    name="ARCHETYPE_GOOGLE_SHORTENER_API_KEY",
    label="Google Short URL API Key",
    description="Google Short URL API Key",
    editable=True,
    default=u'',
)

register_setting(
    name="ARCHETYPE_SEARCH_HELP_URL",
    label="Search Help Page",
    description="Use relative URL if page is on this web site",
    editable=True,
    default=u'',
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
