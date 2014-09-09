# DigiPal

###### Digital Resource for and Database of Paleography, Manuscripts and Diplomatic.
----

## Content

1. About
2. Digipal Technologies Stack
3. How To Set Up Digipal
4. Run Digipal
5. What To Do After
6. Lightbox
7. API
8. Testing


## 1. About

The Digital Resource for Palaeography (DigiPal) is a project funded by the European Research Council that brings digital technology to bear on scholarly discussion of medieval handwriting. At its heart will be hundreds of newly-commissioned photographs of eleventh-century Anglo-Saxon script from the major manuscript collections in the world, with detailed descriptions of the handwriting, the textual content, and the wider manuscript or documentary context.

See further http://digipal.eu/

----

## 2. Digipal Technologies Stack
Digipal is built upon the Django Web Framework. The main technologies used by the project are:
- Django as web framework and Mezzanine as CMS and Blog
- IIPImage for the image server
- OpenLayers as manuscripts viewer and annotator
- Bootstrap and JQuery as front-end frameworks (with the addition of various plugins)
- FontAwesome and Glyphicons icons

## 3. How to set up Digipal

### Download Digipal
Using GIT:

	git clone https://github.com/kcl-ddh/digipal

### Create log folder
In the same folder of that created by the previous command, create a folder and call it "logs", and a file "digipal_django_debug.log" in it.

- digipal-django
	- ...
- logs
	- digipal_django_debug.log

### Installing Requirements
Using PIP:

    pip install -r requirements.txt

To see or manually install all the requirements consult the requirements.txt file provided.

### Database
**In order to run the Digipal's Database we used a PostgresQL database server. Therefore, we recommend you to use PostgresQL as well since we cannot ensure that the database will work on other RDBs.**

Set up the database in your local_settings.py file and fill the DATABASES object with your settings:

	DATABASES = {
	    'default': {
	        'ENGINE': '',
	        'NAME': '',
	        'USER': '',
	        'PASSWORD': '',
	        'HOST': 'localhost',
	        'PORT': '',
	    }
	 }

After that, run in your terminal the following commands:

	python manage.py syncdb
	python manage.py migrate

### Image uploads
	UPLOAD_IMAGES_URL = 'uploads/images/'
	UPLOAD_IMAGES_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.strip('/'),
	        UPLOAD_IMAGES_URL.strip('/'))

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
	IMAGE_SERVER_WEB_ROOT = 'jp2'
	IMAGE_SERVER_HOST = 'digipal.cch.kcl.ac.uk'
	IMAGE_SERVER_PATH = '/iip/iipsrv.fcgi'
	IMAGE_SERVER_ZOOMIFY = 'http://%s%s?zoomify=%s/'
	IMAGE_SERVER_FULL = 'http://%s%s?FIF=%s&amp;RST=*&amp;QLT=100&amp;CVT=JPG'
	IMAGE_SERVER_THUMBNAIL = 'http://%s%s?FIF=%s&amp;RST=*&amp;HEI=35&amp;CVT=JPG'
	IMAGE_SERVER_THUMBNAIL_HEIGHT = 35
	IMAGE_SERVER_RGN = 'http://%s%s?FIF=%s&%s&RGN=%f,%f,%f,%f&CVT=JPG'
	IMAGE_SERVER_EXT = 'jp2'

#### DJANGO-IIPIMAGE
	IMAGE_SERVER_URL  = 'http://%s%s' % (IMAGE_SERVER_HOST, IMAGE_SERVER_PATH)
	IMAGE_SERVER_ROOT = '/vol/digipal2/images'
	IMAGE_SERVER_UPLOAD_ROOT = 'jp2'
	IMAGE_SERVER_ORIGINALS_ROOT = 'originals'
	IMAGE_SERVER_UPLOAD_EXTENSIONS = ('.jp2', '.jpg', '.tif', '.bmp', '.jpeg')
	IMAGE_SERVER_ADMIN_UPLOAD_DIR = os.path.join(IMAGE_SERVER_UPLOAD_ROOT, 'admin-upload')

### Mezzanine
	SITE_TITLE = 'ProjectName'

### Social
	TWITTER = 'TwitterUsername'
	GITHUB = 'GithubUsername/ProjectName'
	COMMENTS_DEFAULT_APPROVED = True
	COMMENTS_DISQUS_SHORTNAME = "yourDisqusName"

### Annotator Settings
	ANNOTATOR_ZOOM_LEVELS = 7	# This setting sets the number of zoom levels of OpenLayers' image map
	REJECT_HTTP_API_REQUESTS = False	# if True, prevents any change to the DB

## 4. Run Digipal
By using the system terminal, go to your Digipal root folder, and then run:

	python manage.py runserver

Run you browser at the address localhost:8000

## 5. What to do after

You should create a superuser to edit the Digipal back-end through the Mezzanine interface.

	python manage.py createsuperuser

After that, you will be able to get to the admin page by using the credentials chosen. To do this, go to the page http://localhost:8000/admin and log in.

## 6. Lightbox

The Lightbox is a separate project, even though it's still tightly linked to Digipal.
It is possible to install it through pip:

	pip install git+https://github.com/Gbuomprisco/Digital-Lightbox.git

By default, it is disabled. You can enable it by setting the variable LIGHTBOX in your settings:

	LIGHTBOX = True

It will be available at the address /lightbox.

For more information about the Digital lightbox, see the [project page](https://github.com/Gbuomprisco/Digital-Lightbox)

## 7. API
It is possible to explore Digipal's content thanks to a RESTFUL API, which can be also used through a Javascript script.

### Documentation
To use the API, read Digipal's API [Documentation](https://github.com/kcl-ddh/digipal/blob/master/api/digipal-api.txt)

### Import Digipal API script
You can find the digipal API script here: [Digipal API](https://github.com/kcl-ddh/digipal/blob/master/static/digipal/scripts/api.digipal.js). Then, you can include it on your web page.

	<script src='api.digipal.js'></script>

### How To Use The API

#### Calling the API class
If you are running the script into a Digipal instance:

	var dapi = new DigipalAPI({
		crossDomain: false,
		root: '/digipal/api
	});

... otherwise just call it without any options:

	var dapi = new DigipalAPI();

#### Making requests
It is possible to use the API in various ways:

1. Specifying the datatype into the URL path through the method **request**
2. By using the datatype as method name

**Note that the first two parameters of the methods are required**

In the first case, we would have:

	var url = 'graph/12453';
	dapi.request(url, function(data){
		console.log(data);
	});

Instead, in the second case, we can have:

	dapi.graph(12453, function(data){
		console.log(data);
	});

	// or

	dapi.image(61, function(data){
		/* ... data ... */
	});

It is possible to use the first parameter in various ways:
1. A single id, like in the examples. Ex. 12453
2. An array of ids. Ex. [134, 553, 356]
3. An object representing the fields and chosen values to match the record. Ex. {id: 10, image:61}

	// an object representing properties and values
	var parameters = {
		name: "Square",
		character__name: "a"
	};

	dapi.allograph(parameters, function(data) {
		console.log(data);
	});

	// a list of ids
	dapi.image([60, 61], function(data) {
		console.log(data);
	});

#### Optional Parameters
There are two further but optional paramaters.

	/* Note the paramters select and limit	*/
	dapi.request(url, callback, select, limit)

The parameter **select** allows to specify the wished fields to be pulled by the request (the field id is always returned).
Ex select = ['image'] will return only two fields: id and image.

The parameter **limit** allows to limit the number of records returned by the request. The default value is 100.

Another example:

	dapi.image({
		id: 18
	}, function(data){
		/* ... your data ... */
	}, ['item_part', 'image'));

	// or
	// note that if select is empty, it will get all the fields to the response
	// here we are limiting the number of record returned down to 1

	dapi.image({
		hands: 35
	}, function(data){
		/* ... your data ... */
	}, [], 1);

#### Results returned by the API functions

Every API call returns an object with the following properties:
	- count: The number of items found
	- errors: An array whose first element represents the HTTP number error (500,400, etc.) and the second element representing the error message (can be an HTML page)
	- results: An array of objects representing the items found
	- success: A boolean that specifies whether the call has been successful or not

## 8. Testing

The documentation for testing Digipal is available at [https://github.com/kcl-ddh/digipal/blob/master/static/digipal/scripts/tests/README.md](https://github.com/kcl-ddh/digipal/blob/master/digipal/static/digipal/scripts/tests/README.md)
