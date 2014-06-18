phantom.page.injectJs('./test-suite.js');
var x = require('casper').selectXPath;
var Tester = new TestSuite();

var AnnotatorTest = {
    multiple: false,
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
    name: 'collections',
    run: function(loadScenarios) {
        var scenarios = ['collections'];
        loadScenarios(scenarios);
    }
};

Tester.addTest(AnnotatorTest, CollectionTest);
Tester.init();