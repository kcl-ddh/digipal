from iipimage.fields import *

# Patch 3:
# The order of the query string arguments do matter,
# if CVT appears before HEI, the resizing will fail on some iip image
# server implementations


def thumbnail_url(self, height=None, width=None):
    try:
        height = '&HEI=%s' % str(int(height))
    except (TypeError, ValueError):
        height = ''
    try:
        width = '&WID=%s' % str(int(width))
    except (TypeError, ValueError):
        width = ''
    return '%s%s%s&CVT=JPEG' % (self.full_base_url, height, width)


ImageFieldFile.thumbnail_url = thumbnail_url
