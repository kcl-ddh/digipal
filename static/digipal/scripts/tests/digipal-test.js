/*
 * * Digipal Testing using CasperJS and PhantomJS
 **
 **/


function DigipalTest(_options) {

    phantom.page.injectJs('config.js');

    var self = this;
    var domain = config.root;
    var http = require('http'),
        system = require('system');

    if (casper.cli.get('deep')) {
        config.deepScan = true;
    }

    var options = {
        'deepScan': config.deepScan,
        "page": domain
    };

    var init = function(_options) {

        options = Utils.extend({}, options, _options);

        // errors: 404, 500 and js
        var errors = [];

        // assert errors
        var assert_failures = [];

        Events(errors, assert_failures);

        casper.test.begin('Digipal testing Suite', function() {
            casper.start(options.page, function() {
                Scraper(Tests.tests, options);
            }).run(function() {
                if (assert_failures.length) {
                    this.echo(assert_failures.length + ' failures', 'ERROR');
                }

                if (errors.length > 0) {
                    this.echo(errors.length + ' Javascript errors found', "WARNING");
                } else {
                    this.echo(errors.length + ' Javascript errors found', "INFO");
                }

                this.echo('All tasks done.', 'GREEN_BAR');
                this.exit();
            });
        });

    };

    var Events = function(errors, assert_failures) {

        casper.on('http.status.404', function(resource) {
            this.echo('This url is 404: ' + resource.url, 'ERROR');
            errors.push({
                "Error": 404,
                "url": resource.url
            });
        });

        casper.on('http.status.500', function(resource) {
            this.echo('Woops, 500 error: ' + resource.url, 'ERROR');
            errors.push({
                "Error": 404,
                "url": resource.url
            });
        });

        casper.on("page.error", function(msg, trace) {
            this.echo("Error:    " + msg, "ERROR");
            this.echo("file:     " + trace[0].file, "WARNING");
            this.echo("line:     " + trace[0].line, "WARNING");
            this.echo("function: " + trace[0]["function"], "WARNING");
            errors.push(msg);
        });

        casper.test.on("fail", function(failure) {
            assert_failures.push(failure);
        });

        casper.on('remote.message', function(msg) {
            this.echo('remote message caught: ' + msg);
        });
    };

    var Scraper = function(_tests, options) {

        var linksCache = [];

        (function() {

            var testsList = Tests.methods.sort(_tests);
            if (testsList.multiple.length) {
                var links = Utils.dom.get_links(linksCache);
                casper.eachThen(links, function(response) {
                    if (response.data !== null) {

                        var url = domain + response.data;
                        if (Utils.isExternalLink(response.data)) {
                            return false;
                        }

                        casper.thenOpen(url, function() {
                            casper.echo('\nOpened ' + url, 'PARAMETER');
                            for (var i = 0; i < testsList.multiple.length; i++) {
                                Tests.tests[testsList.multiple[i]].run();
                            }

                            if (options.deepScan) {
                                run();
                            }
                        });
                    }

                });
            }

            if (testsList.single.length) {
                for (var i = 0; i < testsList.single.length; i++) {
                    Tests.tests[testsList.single[i]].run();
                }
            }
        })();

    };

    var Tests = {

        methods: {

            sort: function(tests) {
                var _tests = {
                    'multiple': [],
                    'single': []
                };

                var hasTestsSetting = true;

                if (!config.hasOwnProperty('tests') || !config.tests.length) {
                    casper.echo('Tests not defined in settings file. All tests are being performed', 'INFO');
                    hasTestsSetting = false;
                }

                for (var i in tests) {
                    if (hasTestsSetting && config.tests.indexOf(i) >= 0 || !hasTestsSetting) {
                        if (tests[i].multiple) {
                            _tests.multiple.push(i);
                        } else {
                            _tests.single.push(i);
                        }
                    }
                }
                return _tests;
            },

            add: function(name, Test) {
                tests[name] = Test;
                return tests;
            },

            edit: function(test, attrs) {
                Utils.extend({}, tests[test], attrs);
            },

            list: function() {
                casper.echo('List of available tests\n', 'PARAMETER');
                for (var i in Tests.tests) {
                    casper.echo('\tTest: ' + i, 'INFO');
                    casper.echo('\tDescription:' + Tests.tests[i].message + '\n');
                }
            }
        },

        tests: {
            titles: {
                multiple: true,
                message: 'Checks whether the tag title is present or not',
                run: function() {
                    casper.test.assertTruthy(casper.getTitle());
                }
            }
        }
    };


    var Utils = {

        dom: {
            get_links: function(linksCache) {
                var _links = casper.getElementsAttribute('a', 'href'),
                    link;
                for (var i = 0; i < _links.length; i++) {
                    link = Utils.removeQueryString(_links[i]);
                    if (linksCache.indexOf(link) >= 0) {
                        _links.splice(i, 1);
                        i--;
                    } else {
                        linksCache.push(link);
                    }
                }
                return _links;
            }
        },

        isExternalLink: function(link) {
            var regex = /^http(s)?:\/\/(.)+/;
            if (regex.test(link)) {
                return true;
            }
            return false;
        },

        removeQueryString: function(link) {
            var regex = /[\?#](.)*|javascript:void\(0\)$/;
            return link.replace(regex, '');
        },

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

        equals: function(array1, array2) {

            if (!array1 || !array2) {
                return false;
            }

            if (array1.length != array2.length) {
                return false;
            }

            for (var i = 0, l = array1.length; i < l; i++) {
                if (array1[i] instanceof Array && array2[i] instanceof Array) {
                    if (!array1[i].equals(array2[i]))
                        return false;
                } else if (array1[i] != array2[i]) {
                    return false;
                }
            }
            return true;
        },

        screenshot: function() {
            var viewportSizes = [
                    [320, 480],
                    [320, 568],
                    [600, 1024],
                    [1024, 768],
                    [1280, 800],
                    [1440, 900]
                ],

                url = casper.cli.args[0],
                saveDir = url.replace(/[^a-zA-Z0-9]/gi, '-').replace(/^https?-+/, '');

            casper.each(viewportSizes, function(self, viewportSize, i) {

                // set two vars for the viewport height and width as we loop through each item in the viewport array
                var width = viewportSize[0],
                    height = viewportSize[1];

                this.viewport(width, height);

                //Set up two vars, one for the fullpage save, one for the actual viewport save
                var FPfilename = saveDir + '/fullpage-' + width + ".png";
                var ACfilename = saveDir + '/' + width + '-' + height + ".png";

                //Capture selector captures the whole body
                this.captureSelector(FPfilename, 'body');

                //capture snaps a defined selection of the page
                this.capture(FPfilename + '_selection', {
                    top: 0,
                    left: 0,
                    width: width,
                    height: height
                });

                this.echo('Snapshot taken');

            });
        }
    };

    return {
        'tests': Tests.tests,
        'addTest': Tests.methods.add,
        'editTest': Tests.methods.edit,
        'listTests': Tests.methods.list,
        'init': init,
        'options': options,
        'utils': Utils
    };
}