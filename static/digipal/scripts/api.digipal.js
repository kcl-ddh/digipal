function DigipalAPI(options) {

    var self = this;
    var domain = 'http://localhost:8000/digipal/api';

    var default_options = {
        crossDomain: true
    };

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
    };

    default_options = utils.extend(default_options, options);

    if (!default_options.crossDomain) {
        domain = '/digipal/api';
    }

    var constants = {
        DOMAIN: domain,
        DATATYPES: ['graph', 'allograph', 'hand', 'scribe', 'allograph', 'idiograph', 'annotation', 'component', 'feature', 'image']
    };

    var init = function() {
        var functions = generateFunctions();
        return functions;
    };

    var generateFunctions = function() {

        var functions = {
            'call': call
        };

        for (var i = 0; i < constants.DATATYPES.length; i++) {
            var datatype = constants.DATATYPES[i];
            (function(datatype) {
                functions[datatype] = function(url, callback) {
                    return functions.call(constants.DOMAIN + '/' + datatype + '/' + url, callback);
                };
            })(datatype);
        }

        return functions;
    };

    var makeRequestScript = function(url) {
        var script = document.createElement('script');
        var head = document.head;
        script.setAttribute("src", url);
        script.setAttribute("async", true);
        head.appendChild(script);
        return script;
    };

    var Ajax = function(url, callback) {
        var xmlhttp;
        var csrftoken = utils.getCookie('csrftoken');

        if (window.XMLHttpRequest) {
            // code for IE7+, Firefox, Chrome, Opera, Safari
            xmlhttp = new XMLHttpRequest();
        } else {
            // code for IE6, IE5
            xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
        }

        xmlhttp.onreadystatechange = function() {
            if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
                callback(xmlhttp.responseText);
            }
        };

        xmlhttp.open("GET", url, true);
        xmlhttp.setRequestHeader("Content-type", "application/json");
        xmlhttp.send('csrftoken=' + csrftoken);

    };

    /*
        Call function
    */

    var call = function(url, callback, options) {
        var cb = '_callback';
        url += '?callback=' + cb;
        if (url instanceof Array) {
            url = url.toString();
        }
        if (default_options.crossDomain) {
            var script = makeRequestScript(url);
            window[cb] = function(data) {
                callback(success, message, data);
                window[cb] = null;
                delete window[cb];
                script.parentNode.removeChild(script);
            };
        } else {
            Ajax(url, callback);
        }

    };

    /*
        Object initialization
    */

    return (function() {
        return init();
    })();
}