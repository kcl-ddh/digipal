phantom.page.injectJs('./test-suite.js');
var x = require('casper').selectXPath;
var Tester = new TestSuite();

var AnnotatorTest = {
    multiple: false,
    message: 'Test on annotator and allographs pages',
    name: 'annotator',
    run: function(loadScenarios) {

        phantom.clearCookies();
        var scenarios = ['annotator'];
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