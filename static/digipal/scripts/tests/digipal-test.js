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

    var _local_options = {
        'deepScan': config.deepScan,
        "page": domain
    };

    var init = function() {

        // errors: 404, 500 and js
        var errors = [];
        catchEvents(errors);

        // assert errors
        var assert_failures = [];

        casper.test.on("fail", function(failure) {
            assert_failures.push(failure);
        });

        casper.test.begin('Digipal testing Suite', function() {
            casper.start(_local_options.page, function() {
                scraper(tests, _local_options);
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

    var catchEvents = function(errors) {

        casper.on('http.status.404', function(resource) {
            this.echo('This url is 404: ' + resource.url, 'ERROR');
        });

        casper.on('http.status.500', function(resource) {
            this.echo('Woops, 500 error: ' + resource.url, 'ERROR');
        });

        casper.on("page.error", function(msg, trace) {
            this.echo("Error:    " + msg, "ERROR");
            this.echo("file:     " + trace[0].file, "WARNING");
            this.echo("line:     " + trace[0].line, "WARNING");
            this.echo("function: " + trace[0]["function"], "WARNING");
            errors.push(msg);
        });

    };

    var scraper = function(_tests, _local_options) {

        var linksCache = [];

        var run = function(_links) {

            var testsList = SortTests(_tests);
            if (testsList.multiple.length) {
                casper.eachThen(_links, function(response) {
                    if (response.data !== null) {

                        var url = domain + response.data;
                        if (utils.isExternalLink(response.data)) {
                            return false;
                        }

                        casper.thenOpen(url, function() {

                            casper.echo('\nOpened ' + url, 'PARAMETER');
                            for (var i = 0; i < testsList.multiple.length; i++) {
                                tests[testsList.multiple[i]].run();
                            }

                            if (_local_options.deepScan) {
                                var links = dom_utils.get_links(linksCache);
                                run(links);
                            }
                        });
                    }

                });
            }

            if (testsList.single.length) {
                for (var i = 0; i < testsList.single.length; i++) {
                    tests[testsList.single[i]].run();
                }
            }
        };

        var links = dom_utils.get_links(linksCache);
        run(links);

    };

    var SortTests = function(tests) {

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

    };

    var addTest = function(name, Test) {
        tests[name] = Test;
        return tests;
    };

    var editTest = function(test, attrs) {
        utils.extend({}, tests[test], attrs);
    };

    var tests = {
        titles: {
            multiple: true,
            message: 'Testing titles',
            run: function() {
                casper.test.assertTruthy(casper.getTitle());
            }
        }
    };

    var dom_utils = {
        get_links: function(linksCache) {
            var _links = casper.getElementsAttribute('a', 'href'),
                link;
            for (var i = 0; i < _links.length; i++) {
                link = utils.removeQueryString(_links[i]);
                if (linksCache.indexOf(link) >= 0) {
                    _links.splice(i, 1);
                    i--;
                } else {
                    linksCache.push(link);
                }
            }
            return _links;
        }
    };

    var utils = {

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
        }

    };

    _local_options = utils.extend({}, _local_options, _options);

    return {
        'tests': tests,
        'addTest': addTest,
        'editTest': editTest,
        'init': init,
        'options': _local_options
    };
}