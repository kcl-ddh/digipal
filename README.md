# DigiPal
###### Digital Resource for and Database of Paleography, Manuscripts and Diplomatic.
----

## About

The Digital Resource for Palaeography (DigiPal) is a project funded by the European Research Council that brings digital technology to bear on scholarly discussion of medieval handwriting. At its heart will be hundreds of newly-commissioned photographs of eleventh-century Anglo-Saxon script from the major manuscript collections in the world, with detailed descriptions of the handwriting, the textual content, and the wider manuscript or documentary context.

See further http://digipal.eu/

----
## How to set up Digipal

### Installing Requirements
Using PIP:

	pip install -r requirements.txt

To see or manually install all the requirements consult the requirements.txt file provided.    

### Image uploads
	UPLOAD_IMAGES_URL = 'uploads/images/'
	UPLOAD_IMAGES_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.strip('/'), UPLOAD_IMAGES_URL.strip('/'))
	MAX_THUMB_LENGTH = 50

### Haystack
	HAYSTACK_CONNECTIONS = {
		'default': {
	        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
	        'URL': 'http://localhost:9200/',
	        'INDEX_NAME': 'haystack',
	    },
	}

	ITEM_PART_DEFAULT_LOCUS = 'face'

### IIP Image Server
	IMAGE_SERVER_ROOT = 'jp2'
	IMAGE_SERVER_HOST = 'digipal.cch.kcl.ac.uk'
	IMAGE_SERVER_PATH = '/iip/iipsrv.fcgi'
	IMAGE_SERVER_METADATA = '%s?FIF=%s&OBJ=Max-size'
	IMAGE_SERVER_METADATA_REGEX = r'^.*?Max-size:(\d+)\s+(\d+).*?$'
	IMAGE_SERVER_ZOOMIFY = 'http://%s%s?zoomify=%s/'
	IMAGE_SERVER_FULL = 'http://%s%s?FIF=%s&RST=*&QLT=100&CVT=JPG'
	IMAGE_SERVER_THUMBNAIL = 'http://%s%s?FIF=%s&RST=*&HEI=35&CVT=JPG'
	IMAGE_SERVER_RGN = 'http://%s%s?FIF=%s&RST=*&%s&RGN=%f,%f,%f,%f&CVT=JPG'
	IMAGE_SERVER_EXT = 'jp2'