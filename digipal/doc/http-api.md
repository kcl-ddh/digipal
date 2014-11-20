# Web API Syntax  

Expose the DigiPal Django Models as a Restful web API.

It handles CRUD requests from HTTP and returns JSON responses.

## Request

Here is the general form for the requests

```
(HTTP-METHOD) http://.../digipal/api/:content_type/[:selector/]?[_:filter=:value1][&@select=[*]:fieldset1,[*]:fieldset2,...][&:field=:value2][&@limit=:limit][&@format=:format]
```

* : is used to denote a variable. All variables are described in the section below.
* optional parameters are surrounded by []
    
## Request parameters

### HTTP-METHOD
* GET     : to retrieve records
* PUT     : to update records
* POST    : to create a record [NO YET IMPLEMENTED]
* DELETE  : to remove records  [NO YET IMPLEMENTED]

### :content_type
The name of DigiPal model in lower case (e.g. annotation, image, itempart, graph)

### :selector
A comma separated list of record ids. If not supplied no filter is applied (all records are returned). 
This is functionally equivalent to `?_id__in=[:selector]`

e.g. `GET /digipal/api/annotation/1000,1001/`

=> retrieves annotation records with id = 1000 or 1001 

### :filter
Any Django valid QuerySet filter that can be applied to the model specified in :content_type. 
Note that filters must start with an underscore. You can use more than one filter.

String values shouldn't be surrounded by quotes and booleans can be expressed 
with 0 (False) or 1 (True). Arrays should be surrounded by [] (e.g. `?_id__in=[1,3,5]`).

e.g. `GET /digipal/api/annotation/?_graph__id__gt=2000&_rotation=0`

=> retrieves annotation where annotation.graph.id > 2000 AND annotation.rotation = 0

e.g. `GET /digipal/api/itempart/?_pagination=1&_display_label__icontains=badminton`

=> retrieves itemparts where itempart.pagination = True and itempart.display_label contains 'badminton'

### :fieldset
A field name from the requested content_type or a custom-defined fieldset.
If @select is not provided all fields are returned.
Note that the field 'id' is always returned.
'str' is a special field that corresponds to the string representation of the record.
For related records only the id is returned.
Use * to expand the information about related records (see example below).
 
e.g. `GET /digipal/api/annotation/1000/`

=> returns all the fields of annotation 1000

e.g. `GET /digipal/api/annotation/?@select=rotation,modified`

=> returns only annotation.id, annotation.rotation and annotation.modified
e.g. `GET /digipal/api/annotation/?@select=myset`

=> returns a custom-defined set of fields named 'myset'. This fieldset is defined
in custom.py:APIAnnotation()

e.g. `GET /digipal/api/annotation/1000/?@select=graph`

=> returns only 'id' and 'graph__id' and 'graph' (string repr of the associated graph record)

e.g. `GET /digipal/api/annotation/1000/?@select=*graph`

=> returns only 'id' and 'graph', with graph being a dictionary with id

### :field
A field to be changed in the retrieved records. You can provide multiple fields. 

e.g. `PUT /digipal/api/annotation/1000/?rotation=20&image_id=500`

=> change the rotation and the image of the annotation record with id = 1000
        
### :limit
Maximum number of records the operation works on. If unspecified the limit is DEFAULT_RESULT_SIZE. 
This is to avoid accidental requests retrieving too many records by mistake.
	
### :format
The desired output format for the response. Supported formats are: json, jsonp and xml. 
If not provided the output format is json. 
If @callback is specified, the output format is always jsonp (@format is ignored).  

e.g. `GET /digipal/api/annotation/?@format=xml`

=> returns annotation records in a XML format

## Response

```
    {
        'success': boolean,
        'errors': [],
        'count': the size of the result set BEFORE applying @limit
        'results': [
            {'id': ,
            'field1': 
            'field2':
            ... 
            },
            ...
        ]
    }
```

## Permissions
	
Each DigiPal instance can set its own permission for each operation on each content type. If you try an operation that is not permitted you will received an error.

To set the permissions in your own DigiPal instance you can change API_PERMISSIONS in your local_settings.py.

API_PERMISSIONS is a list of permission instructions. Each instruction is a list made of two elements: the crud operation to (dis)allow and a comma separated list of content types affected by this instruction.

To determine the permission on a content type, the API will execute the instructions one by one following their order of definition in API_PERMISSIONS.

Examples:

```

# No permission at all
API_PERMISSIONS = []

# All content types can be created and read
API_PERMISSIONS = [['cr', 'ALL']]

# All content types can be created and read
# graph and annotation can also be updated
API_PERMISSIONS = [['cr', 'ALL'], ['+u', 'graph,annotation']]

# All content types can be created and read
# annotation can only be deleted
# graph can only be created
API_PERMISSIONS = [['cr', 'ALL'], ['+u', 'annotation'], ['d', 'annotation'], ['-r', 'graph']]
```

