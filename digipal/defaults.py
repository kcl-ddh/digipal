from mezzanine.conf import register_setting

register_setting(
    name="TEMPLATE_ACCESSIBLE_SETTINGS",
    description="Sequence of setting names available within templates.",
    editable=False,
    default=(
        'ADMIN_STYLES', 'BANNER_LOGO_HTML', 'SHOW_QUICK_SEARCH_SCOPES',  
        'GITHUB', 'TWITTER', 
        'DP_BUILD_NUMBER', 'DP_BUILD_TIMESTAMP', 'DP_BUILD_BRANCH'
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

# Prevent TinyMCE from stripping the tags and attributes necessary to
# embed video in the blog posts.

register_setting(
    name="RICHTEXT_ALLOWED_TAGS",
    append=True,
    default=("object", "embed", "iframe"), #etc
)

register_setting(
    name="RICHTEXT_ALLOWED_ATTRIBUTES",
    append=True,
    default=("frameborder", "webkitAllowFullScreen", "mozallowfullscreen", "allowFullScreen"), #etc
)
