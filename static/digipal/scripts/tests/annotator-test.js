phantom.page.injectJs('./digipal-test.js');

AnnotatorTest.prototype = new DigipalTest();

function AnnotatorTest(options) {

    var tests = this.tests;
    var domain = config.root;

    tests.annotator = {
        multiple: false,
        run: function() {
            var tasks = new Tasks(options.page);

            if (!casper.cli.get('username') || !casper.cli.get('password')) {
                casper.echo('This task needs username and password to the get root access', 'ERROR');
                casper.exit();
            }

            tasks.AnnotatorTasks.getAdminAccess('http://localhost:8000/admin', casper.cli.get('username'), casper.cli.get('password'))
                .then(function() {
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


var Tasks = function(page) {

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
            casper.open(admin_page, function() {
                this.fill('form#login-form', {
                    'username': username,
                    'password': password
                }, true);
            }).then(function() {
                casper.back();
            });

            return casper.thenOpen(page, function() {
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

(function() {
    var page = config.root + '/digipal/page/81';
    var annotatorTest = new AnnotatorTest({
        page: page
    });
    annotatorTest.init();
})();