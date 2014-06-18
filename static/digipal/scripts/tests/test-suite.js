/*
 * * Testing Suite using CasperJS and PhantomJS
 **
 **/


function TestSuite(_options) {

    var self = this;
    var config = require('./config.js').config;
    var domain = config.root;
    var http = require('http'),
        system = require('system'),
        fs = require('fs');

    var options = {
        'deepScan': config.deepScan,
        "page": domain
    };

    var parentDirectory = fs.workingDirectory;

    if (casper.cli.get('deep')) {
        config.deepScan = true;
        options.deepScan = config.deepScan;
    }

    if (casper.cli.get('root')) {
        options.page = casper.cli.get('root');
    }

    var init = function(_options) {

        // errors: 404, 500 and js
        var errors = [];

        // assert errors
        var assert_failures = [];

        Events(errors, assert_failures);

        casper.test.begin('Initializing Tests', function() {
            casper.start().then(function() {
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

        casper.on('url.changed', function(url) {
            console.log('URL has changed to ' + url);
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

        if (casper.cli.get('debug-remote')) {
            casper.on('remote.message', function(msg) {
                this.echo('remote message caught: ' + msg);
            });
        }
    };

    var Scraper = function(_tests, options) {

        var linksCache = [];
        var run = function() {

            var testsList = Tests.methods.sort(_tests);
            if (testsList.multiple.length) {
                var links = Utils.dom.get_links(linksCache);
                casper.eachThen(links, function(response) {
                    if (response.data !== null) {

                        var url = options.page + response.data;
                        if (Utils.isExternalLink(response.data)) {
                            return false;
                        }

                        casper.thenOpen(url, function() {
                            casper.echo('\nOpened ' + url, 'PARAMETER');
                            for (var i = 0; i < testsList.multiple.length; i++) {
                                Tests.tests[testsList.multiple[i]].run(loadScenarios);
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
                    Tests.tests[testsList.single[i]].run(loadScenarios);
                }
            }
        };

        run();

    };

    var Tests = {

        methods: {

            sort: function(tests) {
                var _tests = {
                    'multiple': [],
                    'single': []
                };

                var hasTestsSetting = true;
                var excludes = [];

                if (casper.cli.get('exclude-test')) {
                    excludes = casper.cli.get('exclude-test').split(',');
                }

                if (!config.hasOwnProperty('tests') || !config.tests.length) {
                    casper.echo('Tests not defined in settings file. All tests are being performed', 'INFO');
                    hasTestsSetting = false;
                }

                for (var i in tests) {
                    if (hasTestsSetting && excludes.indexOf(i) < 0 && config.tests.indexOf(i) >= 0 || !hasTestsSetting) {
                        if (tests[i].multiple) {
                            _tests.multiple.push(i);
                        } else {
                            _tests.single.push(i);
                        }
                    }
                }
                return _tests;
            },

            add: function() {

                var tests = Tests.tests;

                if (!arguments.length) {
                    throw new Error('At least one test must be provided');
                }

                for (var i = 0; i < arguments.length; i++) {
                    var test = arguments[i];
                    tests[test.name] = test;
                }

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
                name: 'titles',
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
                var exclude_paths = ['/media/', '/feeds/'];
                for (var i = 0; i < _links.length; i++) {
                    link = Utils.removeQueryString(_links[i]);
                    if (linksCache.indexOf(link.replace(/\/(\d)+\//)) >= 0 || link.indexOf()) {
                        _links.splice(i, 1);
                        i--;
                    } else {
                        linksCache.push(link.replace(/\/(\d)+\//), '//');
                    }
                }
                return _links;
            }
        },

        isExternalLink: function(link) {
            var regex = /^http|https:\/\/(.)+|mailto/;
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

        exclude_folders: function(folders, excludes) {
            folders = JSON.parse(JSON.stringify(folders));
            excludes = JSON.parse(JSON.stringify(excludes));
            for (var i = 0; i < excludes.length; i++) {
                for (var j = 0; j < folders.length; j++) {
                    if (excludes[i] == folders[j]) {
                        folders.splice(j, 1);
                    }
                }
            }
            return folders;
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

    var loadScenarios = function(scenarios) {

        var scenariosPath = parentDirectory + '/' + config.scenarios.path;
        var excludes = config.scenarios.excludes;
        if (!fs.exists(scenariosPath)) {
            throw new Error('The folder scenarios does not exist');
        }

        fs.changeWorkingDirectory(scenariosPath);
        var absolute_path = scenariosPath;
        var scanned = [];

        var lookup = function(directory) {
            var _directory = fs.list(directory);
            _directory = Utils.exclude_folders(_directory, ['.', '..']);

            for (var i = 0; i < _directory.length; i++) {
                var path = _directory[i];

                if (fs.isDirectory(path) && excludes.indexOf(path) < 0 && scenarios.indexOf(path) >= 0 && scanned.indexOf(path) < 0) {

                    fs.changeWorkingDirectory(path);

                    var path_children = fs.list(fs.workingDirectory);
                    path_children = Utils.exclude_folders(path_children, ['.', '..']);

                    for (var j = 0; j < path_children.length; j++) {
                        if (fs.isDirectory(path_children[j]) && excludes.indexOf(path_children[j]) < 0) {
                            scenarios.push(path_children[j]);
                        }
                    }

                    lookup(fs.workingDirectory);

                } else if (fs.isFile(path) && path.indexOf('.js') != -1 && path.indexOf('actions.js') == -1) {

                    var scenario_module = require(path);
                    var scenariosSelected = [];

                    for (var c in scenario_module) {
                        scenariosSelected.push(scenario_module[c]);
                    }

                    casper.eachThen(scenariosSelected, function(response) {
                        var Scenario = response.data;
                        var Scenarios = Scenario.Scenarios;
                        var dependencies = [];
                        casper.eachThen(Scenario.dependencies, function(dependency) {
                            var module_dependency = require(lastWorkingDirectory + '/' + dependency.data).Actions(options);
                            dependencies[module_dependency.name] = module_dependency.actions;
                        });

                        casper.then(function() {
                            var scenarios = new Scenarios(dependencies, options);
                            var scenariosList = [];
                            for (var i in scenarios) {
                                scenariosList.push(scenarios[i]);
                            }
                            if (Scenario.hasOwnProperty('middleware')) {
                                var middleware = Scenario.middleware;
                                casper.eachThen(middleware, function(middleware) {
                                    var mdl = require('./middleware/' + middleware.data).Middleware();
                                    mdl.done(options, function() {
                                        casper.eachThen(scenariosList, function(scenario) {
                                            scenario.data.call();
                                        });
                                    });
                                });
                            } else {
                                casper.eachThen(scenariosList, function(scenario) {
                                    scenario.data.call();
                                });
                            }
                        });
                    });
                }

                if (i == _directory.length - 1) {
                    scanned.push(directory);
                    var lastWorkingDirectory = fs.workingDirectory;
                    fs.changeWorkingDirectory('../');
                }

            }
        };

        return lookup(fs.workingDirectory);

    };

    options = Utils.extend({}, options, _options);

    return {
        'tests': Tests.tests,
        'addTest': Tests.methods.add,
        'editTest': Tests.methods.edit,
        'listTests': Tests.methods.list,
        'init': init,
        'options': options,
        'utils': Utils,
        'loadScenarios': loadScenarios
    };
}