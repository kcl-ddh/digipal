function DigipalAPI(options) {

    var self = this;
    var domain = 'http://localhost:8000/digipal/api';

    var default_options = {};

    var constants = {
        DOMAIN: domain,
        DATATYPES: ['graph', 'allograph', 'hand', 'scribe', 'allograph', 'idiograph', 'annotation', 'component', 'feature', 'image']
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
        }
    };

    // extend
    utils.extend({}, default_options, options);

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

    /*
        Call function
    */

    var call = function(url, callback, options) {
        var cb = '_callback';
        url += '?callback=' + cb;
        if (url instanceof Array) {
            url = url.toString();
        }
        var script = makeRequestScript(url);
        window[cb] = function(data) {
            callback(success, message, data);
            window[cb] = null;
            delete window[cb];
            script.parentNode.removeChild(script);
        };
    };

    /*
        Object initialization
    */

    return (function() {
        return init();
    })();
}