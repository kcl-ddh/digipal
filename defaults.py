from mezzanine.conf import register_setting

register_setting(
    name="TEMPLATE_ACCESSIBLE_SETTINGS",
    description="Sequence of setting names available within templates.",
    editable=False,
    default=(
        'ADMIN_STYLES',
    ),
    append=True,
)
