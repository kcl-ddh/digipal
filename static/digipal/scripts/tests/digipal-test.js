/*
 * * Digipal Testing using CasperJS and PhantomJS
 **
 **/


function DigipalTest() {

    phantom.page.injectJs('config.js');

    var domain = config.root;
    var http = require('http');
    var system = require('system');
    var casperUtils = require("utils");

    /*
     **Extracting arguments
     */

    if (casper.cli.get('deep')) {
        config.deepScan = true;
    }

    var init = function(page, _options) {

        var errors = [];

        catchEvents(errors);

        /*
         ** Running Tests
         */

        domain = domain + page;

        var _local_options = {
            'deepScan': config.deepScan
        };

        _local_options = utils.extend({}, _local_options, _options);

        casper.start(domain, function() {
            scraper(tests, _local_options);
        }).run(function() {

            if (errors.length > 0) {
                this.echo(errors.length + ' Javascript errors found', "WARNING");
            } else {
                this.echo(errors.length + ' Javascript errors found', "INFO");
            }

            this.echo('All tasks done. Digipal is OK :)', 'GREEN_BAR');
            this.exit();
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

            console.log(JSON.stringify(testsList))
            if (testsList.multiple.length) {
                casper.echo(_links)
                casper.eachThen(_links, function(response) {
                    if (response.data !== null) {

                        var url = domain + response.data;
                        if (utils.isExternalLink(response.data)) {
                            return false;
                        }

                        casper.thenOpen(url, function() {

                            casper.echo('\nOpened ' + url, 'INFO');
                            for (var i = 0; i < testsList.multiple.length; i++) {
                                tests[testsList.multiple[i]].run();
                            }

                            if (_local_options.deepScan) {
                                var links = get_links(linksCache);
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

    var tests = {
        titles: {
            multiple: true,
            run: function() {
                if (casper.getTitle()) {
                    casper.echo('TITLE FOUND', 'GREEN_BAR');
                    casper.echo('Title:' + casper.getTitle(), 'PARAMETER');
                } else {
                    casper.echo('Title is missing', 'WARNING');
                }
            }
        }
    };

    var dom_utils = {
        get_links: function(linksCache) {
            var _links = casper.getElementsAttribute('a', 'href');
            var link;

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
            var regex = /\?(.)*$/;
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

    return {
        'tests': tests,
        'addTest': addTest,
        'init': init
    };
}