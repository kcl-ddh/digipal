from mezzanine.conf import register_setting

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
        'MIN_THUMB_LENGTH', 'MAX_THUMB_LENGTH',
        'FOOTER_LOGO_LINE',
        # A way to silence Mezzanine warning when django calls
        # dir(context['settings'])
        # where context['settings'] is a TemplateSettings()
        '__methods__', '__members__'
    ),
    append=True,
)

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
    name="MIN_THUMB_LENGTH",
    description="Minimum size of annotation thumbnails",
    editable=True,
    default=50,
)

register_setting(
    name="MAX_THUMB_LENGTH",
    description="Maximum size of annotation thumbnails",
    editable=True,
    default=300,
)

register_setting(
    name='QUICK_SEARCH_TO_FACETS',
    description="Search box goes to facet search page?",
    editable=True,
    default=False,
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
