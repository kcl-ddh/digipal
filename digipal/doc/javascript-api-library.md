# Javascript API library
 The Javascript API library allows developers to programmatically fetch data from the DigiPal database, as alternative to the API by HTTP queries. To use it, you must include the script in your web page, and then use one of the methods provided by the library to start querying DigiPal.

**It works both in local DigiPal instances and in your websites.**

You can download the script at [https://github.com/kcl-ddh/digipal/blob/master/digipal/static/digipal/scripts/api.digipal.js](https://github.com/kcl-ddh/digipal/blob/master/digipal/static/digipal/scripts/api.digipal.js)

Include it in your page:


```
&lt;script src='api.digipal.js'&gt;&lt;/script&gt;

```
 

Alternatively, you can load it from Github:&lt;script src='[https://raw.githubusercontent.com/kclddh/digipal/master/digipal/static/digipal/scripts/api.digipal.js](https://raw.githubusercontent.com/kclddh/digipal/master/digipal/static/digipal/scripts/api.digipal.js)'&gt;&lt;/script&gt;


### Calling the API class
If you are running the script into a DigiPal instance:


```
var dapi = new DigipalAPI({
    crossDomain: false,
    root: '/digipal/api'
});

```
... otherwise just call it without any options:


```
var dapi = new DigipalAPI();

```

### Making requests
It is possible to use the API in various ways:


1.  Specifying the datatype into the URL path through the method request
2. By using the datatype as method name**Note that the first two parameters of the methods are required**

In the first case, we would have:

 


```
var url = 'graph/12453';
dapi.request(url, function(data) {
    console.log(data);
});

```

```

```
Instead, in the second case, we can have:

 


```
dapi.graph(12453, function(data) {
    console.log(data);
});

// or

dapi.image(61, function(data) {
    /* ... data ... */
});

```

```

```
It is possible to use the first parameter in various ways: 1. A single id, like in the examples. Ex. 12453 2. An array of ids. Ex. [134, 553, 356] 3. An object representing the fields and chosen values to match the record. Ex. {id: 10, image:61}

 


```
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

```

### There are two further but optional paramaters.

```
/* Note the paramters select and limit  */
dapi.request(url, callback, select, limit)

```

```

```
The parameter **select** allows to specify the wished fields to be pulled by the request (the field id is always returned). Ex select = ['image'] will return only two fields: id and image.

The parameter **limit** allows to limit the number of records returned by the request. The default value is 100.

Another example:

 


```
dapi.image({
    id: 18
}, function(data) {
    /* ... your data ... */
}, ['item_part', 'image']);

// or
// note that if select is empty, it will get all the fields to the response
// here we are limiting the number of record returned down to 1

dapi.image({
    hands: 35
}, function(data) {
    /* ... your data ... */
}, [], 1);

```

### Every API call returns an object with the following properties:

```
- count: The number of items found
- errors: An array whose first element represents the HTTP 
  number error (500,400, etc.) and the second element representing 
  the error message (can be an HTML page)
- results: An array of objects representing the items found
- success: A boolean that specifies whether the call has been successful or not
```
 

### Example of a request:
JS API call:


```
dapi.graph(234, function(data) {
    console.log(data);
});
```
 

The result printed will be:

{   **"count"**: 1,   **"errors"**: [],   **"results"**: [      {         **"aspects"**: [],         **"created"**: "2012-05-22 13:08:37.072243+00:00",         **"idiograph__id"**: 51,         **"modified"**: "2013-05-02 10:19:22.364557+00:00",         **"group"**: null,         **"idiograph"**: "e. DigiPal Scribe 3. Saec. xi1/4",         **"parts"**: [],         **"display_label"**: "e. DigiPal Scribe 3. Saec. xi1/4. Hand 1 (fols. 70\u201396)",         **"str"**: "e. DigiPal Scribe 3. Saec. xi1/4. Hand 1 (fols. 70\u201396)",         **"id"**: 234,         **"annotation__id"**: null,         **"hand"**: "Hand 1 (fols. 70\u201396)",         **"annotation"**: null,         **"hand__id"**: 636,         **"graph_components"**: []      }   ],   **"success"**: true} 

_Giancarlo Buomprisco_

__

 

