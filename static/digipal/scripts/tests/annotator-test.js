phantom.page.injectJs('./digipal-test.js');

AnnotatorTest.prototype = new DigipalTest();

function AnnotatorTest() {

    var tests = this.tests;

    tests.annotator = {
        multiple: false,
        run: function() {
            var tasks = new Tasks();

            tasks.AnnotatorTasks.getAdminAccess('http://localhost:8000/admin', config.username, config.password).
            then(function() {
                var feature = tasks.AnnotatorTasks.getVectorElement();
                var selectedFeature = casper.evaluate(function(feature) {
                    annotator.selectFeatureById(feature.id);
                    return annotator.selectedFeature;
                }, feature);
                casper.test.begin('The two ids are equal', 1, function(test) {
                    test.assert(feature.id === selectedFeature.id);
                    test.done();
                });
            });
        }
    };
}


var Tasks = function() {

    var AnnotatorTasks = {

        getFeatures: function() {
            return casper.evaluate(function() {
                return annotator.vectorLayer.features;
            });
        },

        getAnnotations: function() {
            return casper.evaluate(function() {
                return annotator.annotations;
            });
        },

        getCache: function() {
            return casper.evaluate(function() {
                return annotator.cacheAnnotations.cache;
            });
        },

        getAdminAccess: function(admin_page, username, password) {
            casper.thenOpen(admin_page, function() {
                this.fill('form#login-form', {
                    'username': username,
                    'password': password
                }, true);
            });

            casper.thenOpen(page, function() {
                casper.back().back();
            });

            return casper.then(function() {
                return casper;
            });
        },

        getVectorElement: function() {
            var features = this.getFeatures();
            return features[0];
        }

    };

    var AllographsTasks = function() {

    };

    return {
        'AnnotatorTasks': AnnotatorTasks,
        'AllographsTasks': AllographsTasks
    };

};


var annotatorTest = new AnnotatorTest();
var page = '/digipal/page/81';
annotatorTest.init(page, {
    followLinks: false
});