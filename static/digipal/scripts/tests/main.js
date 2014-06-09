phantom.page.injectJs('./test-suite.js');
var x = require('casper').selectXPath;

AnnotatorTest.prototype = new TestSuite();

function AnnotatorTest(options) {

    var self = this;
    var tests = self.tests;
    var domain = self.options.page;

    tests.annotator = {
        multiple: false,
        run: function() {

            if (!casper.cli.get('username') || !casper.cli.get('password')) {
                casper.echo('This task needs username and password to the get root access', 'ERROR');
                casper.exit();
            }

            var scenarios = ['annotator', 'allographs'];
            self.loadScenarios(scenarios);
        }
    };

    tests.collection = {
        multiple: false,
        run: function() {
            var scenarios = ['collections'];
            self.loadScenarios(scenarios);
        }
    };
}


(function() {
    var annotatorTest = new AnnotatorTest();
    annotatorTest.init();
})();