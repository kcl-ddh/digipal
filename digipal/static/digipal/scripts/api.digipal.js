/**
 ** Digipal API
 ** @options {Object}
 **/

function DigipalAPI(options) {

    var self = this;
    var PATH = '/digipal/api';
    var DIGIPAL_URL = 'http://www.digipal.eu';

    var default_options = {
        crossDomain: true,
        timeout: 5000,
        root: "http://" + location.host + PATH
    };

    /*
     ** Utils
     */

    var utils = {

        extend: function() {
            var out = out || {};
            for (var i = 1; i < arguments.length; i++) {
                if (!arguments[i]) {
                    continue;
                }
                for (var key in arguments[i]) {
                    if (arguments[i].hasOwnProperty(key))
                        out[key] = arguments[i][key];
                }
            }
            return out;
        },

        getCookie: function(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        serializeObject: function(_object) {
            var s = '';
            var n = 0;
            for (var i in _object) {
                if (n >= 1) {
                    s += '&';
                }
                s += '_' + i + '=' + _object[i];
                n++;
            }
            return s;
        }
    };

    /*
     ** AJAX call if calls get done on the same domain
     ** for parameters see @request
     */

    var Ajax = function(url, callback, async) {
        var xmlhttp;
        var csrftoken = utils.getCookie('csrftoken');

        if (typeof async == 'undefined') {
            async = true;
        }

        if (window.XMLHttpRequest) {
            // code for IE7+, Firefox, Chrome, Opera, Safari
            xmlhttp = new XMLHttpRequest();
        } else {
            // code for IE6, IE5
            xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
        }

        xmlhttp.onreadystatechange = function() {
            if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
                callback(JSON.parse(xmlhttp.responseText), true);
            } else if (xmlhttp.readyState == 4 && xmlhttp.status !== 200) {
                var error = {
                    errors: [xmlhttp.status, xmlhttp.responseText],
                    success: false
                };
                callback(error, false);
            }
        };

        xmlhttp.open("GET", url, async);
        xmlhttp.setRequestHeader("Content-type", "application/json");
        xmlhttp.send('csrftoken=' + csrftoken);

    };

    /*
     ** Function to inject JSONP script
     ** for @url parameter see @request
     */

    var makeRequestScript = function(url, async) {
        var script = document.createElement('script');
        var head = document.head;
        script.setAttribute("src", url);
        script.setAttribute("async", async);
        head.appendChild(script);
        return script;
    };

    /*
     ** the default options get extended with those selected at initialization
     */

    default_options = utils.extend({}, default_options, options);

    /*
     ** If crossDomain is true, the Digipal URL will be set. Can be changed in the
     ** options though.
     */

    default_options.root = default_options.crossDomain === true ?
        DIGIPAL_URL + PATH : default_options.root;

    var crossDomain = function(isCrossDomain) {
        if (typeof isCrossDomain !== 'undefined') {
            if (isCrossDomain.toLowerCase() == "false") {
                isCrossDomain = false;
            } else {
                isCrossDomain = true;
            }
            default_options.crossDomain = isCrossDomain;
        }
        return default_options.crossDomain;
    };

    var constants = {
        ROOT: default_options.root
    };

    var get_datatypes = function(callback) {
        
        // API optimisation, we preload the API content types to avoid BLOCKING requests by the JS API
        if (window.DAPI_CONTENT_TYPE_RESPONSE) {
            callback(window.DAPI_CONTENT_TYPE_RESPONSE);
        } else {
            
            var url = constants.ROOT + '/content_type/';

            if (default_options.crossDomain) {
                var cb = '_datatypes';
                url += '?@callback=' + cb;
                var script = makeRequestScript(url, false);
                window[cb] = function(data) {
                    callback(data);
                    window[cb] = null;
                    script.parentNode.removeChild(script);
                };

            } else {
                Ajax(url, function(data) {
                    callback(data);
                }, false);
            }
        }
    };

    /*
     ** Function to dynamically create methods based on constants.DATATYPES
     */

    var generateFunctions = function() {
        var functions = {};
        for (var i = 0; i < constants.DATATYPES.length; i++) {
            var datatype = constants.DATATYPES[i];
            (function(datatype) {
                functions[datatype] = function(url, callback, select, limit) {
                    url = process_url(url, select, limit);
                    return request(constants.ROOT + '/' + datatype + '/' + url, callback, select);
                };
            })(datatype);
        }
        (function() {
            functions['request'] = function(_url, _callback, _select, _limit) {
                return request(constants.ROOT + '/' + _url, _callback, _select);
            };
        })();
        functions['crossDomain'] = crossDomain;
        return functions;
    };

    var process_url = function(url, select, limit) {

        var isObject = false;

        if (url instanceof Array) {
            url = url.toString();
        } else if (url && url instanceof Object) {
            url = '?' + utils.serializeObject(url);
            isObject = true;
        }

        if (!isObject && ((select && select.length))) {
            url += '?';
        }

        if (typeof select !== 'undefined' && select.length) {
            if (isObject) {
                url += '&';
            }
            url += '@select=' + select.toString();
        }

        if (typeof limit !== 'undefined' && limit) {
            if ((url instanceof Object && url) || (select && select.length)) {
                url += '&';
            }
            url += '@limit=' + limit;
        }

        return url;
    };

    /*
     ** Request function
     ** @url = {Number} : id of the resource,
     ** @url = {Array} : array of ids of the resource,
     ** @url = {Object} : list of fields {field: value, field2 : value2} (see @constants.DATATYPES)
     ** @callback = {Function} : function to be executed when the call finishes
     ** @select: {Array} : array of fields (see @constants.DATATYPES) to be pulled. If undefined, all fields get called
     */

    var request = function(url, callback) {

        /*
         ** JSONP request, made if crossDomain is true
         */

        if (default_options.crossDomain) {
            var cb = '_callback';
            url += '?@callback=' + cb;
            var script = makeRequestScript(url, true);
            window[cb] = function(data) {
                window.clearInterval(window[cb].timer);
                callback(data, true);
                window[cb] = null;
                delete window[cb];
                script.parentNode.removeChild(script);
            };
            window[cb].timer = window.setTimeout(function() {
                window[cb] = undefined;
                var error = {
                    errors: ["Timeout", '<div id="summary">Error: Request failed</div>'],
                    success: false
                };
                callback(error, false);
                delete window[cb];
            }, default_options.timeout);
        } else {

            /*
             ** AJAX request, made if crossDomain is false
             */

            Ajax(url, callback);
        }
    };


    /*
     ** Return public methods generated by @generateFunctions to the object
     */

    var init = function(callback) {
        get_datatypes(function(datatypes) {
            constants.DATATYPES = datatypes.results[0];
            return callback();
        });
    };

    init(function() {
        var functions = generateFunctions();
        for (var func in functions) {
            self[func] = functions[func];
        }
    });

}