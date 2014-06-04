phantom.page.injectJs('./digipal-test.js');
var x = require('casper').selectXPath;
var dump = require('utils').dump;

AnnotatorTest.prototype = new DigipalTest();

function AnnotatorTest(options) {

    var self = this;
    var tests = self.tests;
    var domain = config.root;

    tests.annotator = {
        multiple: false,
        run: function() {
            var tasks = new Tasks(options.page);
            var AnnotatorTasks = tasks.AnnotatorTasks;
            if (!casper.cli.get('username') || !casper.cli.get('password')) {
                casper.echo('This task needs username and password to the get root access', 'ERROR');
                casper.exit();
            }

            tasks.AnnotatorTasks.get.adminAccess(config.root + '/admin', casper.cli.get('username'), casper.cli.get('password'))
                .then(function() {
                    var features = tasks.AnnotatorTasks.get.features();
                    var i = 0;
                    casper.eachThen(features, function(response) {
                        tasks.AnnotatorTasks.get.select(response.data.id, function() {
                            var features_selected = tasks.AnnotatorTasks.dialog.getSelectedFeatures();
                            AnnotatorTasks.tests.dialogMatchesCache(features_selected);
                        });
                    });

                    /*tasks.AnnotatorTasks.do.annotate(function() {
                        console.log('I finished saving!');
                    });*/
                });
        }
    };
}


var Tasks = function(page) {

    var AnnotatorTasks = {

        get: {

            features: function() {
                return casper.evaluate(function() {
                    return annotator.vectorLayer.features;
                });
            },

            annotations: function() {
                return casper.evaluate(function() {
                    return annotator.annotations;
                });
            },

            cache: function() {
                return casper.evaluate(function() {
                    return annotator.cacheAnnotations.cache;
                });
            },

            adminAccess: function(admin_page, username, password) {

                casper.thenOpen(admin_page, function() {
                    this.fill('form#login-form', {
                        'username': username,
                        'password': password
                    }, true);
                });

                return casper.thenOpen(page, function() {
                    return casper;
                });
            },

            random_vector: function() {
                var features = this.features();
                return features[Math.round(Math.random() * features.length)];
            },

            select: function(feature, callback) {
                casper.evaluate(function(feature) {
                    annotator.selectFeatureById(feature);
                }, feature);

                casper.then(function() {
                    this.wait(300, function() {
                        if (callback) {
                            return callback();
                        }
                    });
                });
            }
        },

        do :{

            /*
             ** Draws and describe a new annotation
             ** Shortcut for the sequence describeForms, drawFeature, describe, save
             */

            annotate: function(describe, callback) {
                var self = this;
                self.describeForms();
                self.drawFeature();
                casper.wait(250, function() {
                    self.describeForms();
                    casper.wait(250, function() {
                        if (describe) {
                            self.describe();
                        }
                        self.save(callback);
                    });
                });
            },

            save: function(callback) {
                casper.evaluate(function() {
                    annotator.saveButton.trigger();
                });
                casper.wait(500, function() {
                    if (callback) {
                        return callback();
                    }
                });
            },

            delete: function() {
                return casper.evaluate(function() {
                    return annotator.deleteFeature.clickFeature();
                });
            },

            refreshLayer: function() {
                return casper.evaluate(function() {
                    return annotator.refresh_layer();
                });
            },

            drawFeature: function() {
                return casper.waitFor(function() {
                    return this.evaluate(function() {
                        var random_number = function(m) {
                            return Math.random() * m;
                        };

                        var points = [
                            new OpenLayers.Geometry.Point(random_number(2000), random_number(2000)),
                            new OpenLayers.Geometry.Point(random_number(2000), random_number(2000)),
                            new OpenLayers.Geometry.Point(random_number(2000), random_number(2000)),
                            new OpenLayers.Geometry.Point(random_number(2000), random_number(2000))
                        ];

                        var ring = new OpenLayers.Geometry.LinearRing(points);
                        var rectangle = new OpenLayers.Geometry.Polygon([ring]);

                        var attributes = {
                            strokeColor: "#11CDD4",
                            strokeOpacity: 0.5,
                            strokeWidth: 2,
                            fillColor: "#11CDD4",
                            fillOpacity: 0.5
                        };

                        var feature = new OpenLayers.Feature.Vector(rectangle, attributes);
                        annotator.vectorLayer.addFeatures([feature]);
                        annotator.selectFeatureById(feature.id);
                        return annotator.selectedFeature;
                    });

                }, function then() {
                    return this.evaluate(function() {
                        return annotator.selectedFeature;
                    });
                });

            },

            describe: function() {
                casper.evaluate(function() {
                    var features_elements = $('.features_box');
                    $.each(features_elements, function() {
                        $(this).attr('checked', true);
                    });
                });
            },

            describeForms: function() {
                casper.evaluate(function() {
                    $('#panelImageBox .allograph_form').val(11);
                    $('#panelImageBox .hand_form').val(287);
                });
            }
        },


        options: {

            openWindow: function() {

                var modal = casper.evaluate(function() {
                    $('#settings_annotator').toggle('click');
                    return $('#modal_settings');
                });

                casper.then(function() {
                    casper.test.assertExists('#modal_settings', 'Checking the settings window has been opened');
                });
                return modal;
            },

            isAdmin: function() {
                return casper.evaluate(function() {
                    return annotator.isAdmin();
                });
            },

            boxes_on_click: function(value) {
                return casper.evaluate(function(value) {
                    if (value) {
                        annotator.boxes_on_click = value;
                    }
                    return annotator.boxes_on_click;
                }, value);
            },

            annotating: function(value) {
                return casper.evaluate(function(value) {
                    if (value) {
                        annotator.annotating = value;
                    }
                    return annotator.annotating;
                }, value);
            },

            clickOption: function(option) {
                var self = this;
                var OptionsWindow = self.openWindow();
                casper.click('#' + option);
            }
        },

        dialog: {

            getDialog: function() {
                return casper.evaluate(function() {
                    return $('.dialog_annotations');
                });
            },

            getSelectedFeatures: function() {
                return casper.evaluate(function() {
                    var features_selected = [];
                    var features_elements = $('.features_box');

                    features_elements.each(function() {
                        if ($(this).is(':checked')) {
                            var label = $('label[for=' + $(this).attr('id') + ']').text();
                            features_selected.push(label);
                        }
                    });

                    return features_selected;
                });
            }
        },

        filter: {
            toggleSwitcher: function() {
                return casper.evaluate(function() {
                    $('.toggle-state-switch').bootstrapSwitch('toggleState');
                    return $('.toggle-state-switch').bootstrapSwitch('state');
                });
            },

            openWindow: function() {
                return casper.evaluate(function() {
                    $('#filterAllographs').toggle('click');
                    return $('#allographs_filtersBox');
                });
            }
        },

        tests: {
            dialogMatchesCache: function(featuresSelected) {
                var cachedFeatures = casper.evaluate(function() {
                    var graphCache = annotator.cacheAnnotations.cache.graphs[annotator.selectedFeature.graph];
                    var _cachedFeatures = [];
                    for (var i = 0; i < graphCache.features.length; i++) {
                        _cachedFeatures.push(graphCache.features[i].feature[0]);
                    }
                    return _cachedFeatures;
                });
                console.log(dump(cachedFeatures), dump(featuresSelected))
                casper.test.assert(utils.equals(cachedFeatures, featuresSelected), 'The cached features and the checkboxes checked must match');

            },
        }
    };

    var AllographsTasks = function() {

    };

    var Tabs = {

        switch: function(target) {
            casper.click(x('//a[@data-target="#' + target + '"]'));
        },

        current: function() {
            return casper.evaluate(function() {
                return $('.nav li.active.in').find('a').data('target');
            });
        }

    };

    return {
        'AnnotatorTasks': AnnotatorTasks,
        'AllographsTasks': AllographsTasks,
        'Tabs': Tabs
    };

};

(function() {
    var page = config.root + '/digipal/page/80';
    var annotatorTest = new AnnotatorTest({
        "page": page
    });
    annotatorTest.init();
})();