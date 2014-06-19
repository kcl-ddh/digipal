phantom.page.injectJs('./test-suite.js');
var x = require('casper').selectXPath;
var Tester = new TestSuite();

var AnnotatorTest = {
    multiple: false,
    message: 'Test on annotator and allographs pages',
    name: 'annotator',
    run: function(loadScenarios) {

        if (!casper.cli.get('username') || !casper.cli.get('password')) {
            casper.echo('This task needs username and password to the get root access', 'ERROR');
            casper.exit();
        }

        var scenarios = ['annotator', 'allographs'];
        loadScenarios(scenarios);
    }
};

var CollectionTest = {
    multiple: false,
    message: 'Test on collections pages',
    name: 'collections',
    run: function(loadScenarios) {
        var scenarios = ['collections'];
        loadScenarios(scenarios);
    }
};

Tester.addTest(AnnotatorTest, CollectionTest);
Tester.listTests();
Tester.init();