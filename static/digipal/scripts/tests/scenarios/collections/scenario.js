phantom.page.injectJs('./digipal-test.js');
var x = require('casper').selectXPath;

CollectionTest.prototype = new DigipalTest();

function CollectionTest(options) {

    tests.collections = {
        multiple: false,
        run: function() {

        }
    };

}

function Tasks() {

}

(function() {
    var test = new CollectionTest();
    var page = '/digipal/collections';
    test.init({
        page: page
    });
})();