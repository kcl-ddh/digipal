phantom.page.injectJs('./digipal-test.js');
var x = require('casper').selectXPath;
var dump = require('utils').dump;

AnnotatorTest.prototype = new DigipalTest();

function AnnotatorTest(options) {

    var self = this;
    var tests = self.tests;
    var domain = self.options.page;

    tests.annotator = {
        multiple: false,
        run: function() {
            var page = self.options.page + options.page;
            var tasks = new Tasks(page);
            var AnnotatorTasks = tasks.AnnotatorTasks;

            if (!casper.cli.get('username') || !casper.cli.get('password')) {
                casper.echo('This task needs username and password to the get root access', 'ERROR');
                casper.exit();
            }

            tasks.AnnotatorTasks.get.adminAccess(domain + '/admin', casper.cli.get('username'), casper.cli.get('password'))
                .then(function() {

                    var scenario = new Scenario();

                    casper.then(function() {
                        scenario.Scenario1();
                    });

                    casper.then(function() {
                        scenario.Scenario2();
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
        _self: this,
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
            }
        },


        do :{

            _self: this,

            /*
             ** Draws and describe a new or an existing annotation
             ** Shortcut for the sequence describeForms, drawFeature, describe, save
             */

            annotate: function(feature, describe, callback) {
                var self = this;
                self.describeForms();

                if (feature) {
                    self.select(feature, function() {
                        console.log('Annotating feature: ' + feature);
                        execute();
                    });
                } else {
                    console.log('Drawing new feature...');
                    self.drawFeature();
                    execute();
                }

                var execute = function() {
                    casper.wait(250, function() {
                        self.describeForms();
                        casper.wait(500, function() {
                            if (describe) {
                                console.log('Describing feature...');
                                self.describe();
                            }
                            self.save(callback);
                        });
                    });
                };
            },

            save: function(callback) {
                casper.evaluate(function() {
                    annotator.saveButton.trigger();
                });
                casper.wait(500, function() {
                    if (callback) {

                        if (casper.evaluate(function() {
                            return $('#status').hasClass('alert-success');
                        })) {
                            casper.echo('Annotation succesfully saved', 'INFO');
                        } else {
                            casper.echo('Annotation not saved', 'ERROR');
                        }
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
                    var features_elements = $('.dialog_annotations .features_box');
                    var n = 0;
                    $.each(features_elements, function() {
                        if (n > 5) {
                            return false;
                        }
                        $(this).attr('checked', true);
                        n++;
                    });
                    console.log(n, features_elements.length);
                });
            },

            describeForms: function() {
                casper.evaluate(function() {
                    $('#panelImageBox .allograph_form').val(11).trigger('change');
                    $('#panelImageBox .hand_form').val(332).trigger('change');
                    return $('select').trigger('liszt:updated');
                });
            },

            select: function(feature, callback) {
                casper.evaluate(function(feature) {
                    annotator.selectFeatureById(feature);
                }, feature);

                casper.then(function() {
                    this.wait(300, function() {
                        casper.capture('screen2.png');
                        if (callback) {
                            return callback();
                        }
                    });
                });
            },

            /*
             ** Simulate click on map to deselect features
             */

            unselect: function() {
                casper.click('#OpenLayers_Layer_Zoomify_2');
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

            close: function() {
                casper.click('.ui-dialog-titlebar-close');
            },

            getSelectedFeatures: function() {
                return casper.evaluate(function() {
                    var features_selected = [];
                    var features_elements = $('.features_box');
                    features_elements.each(function() {
                        if ($(this).is(':checked')) {
                            var label = $('.dialog_annotations').find('label[for=' + $(this).attr('id') + ']').text();
                            features_selected.push(label);
                        }
                    });
                    return features_selected;
                });
            }
        },

        filter: {

            getSwitcherValue: function() {
                return casper.evaluate(function() {
                    return $('.toggle-state-switch').bootstrapSwitch('state');
                });
            },

            toggleSwitcher: function() {
                casper.click('.toggle-state-switch');
                return this.getSwitcherValue();
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
                casper.echo(cachedFeatures.length + ' cached features found');
                casper.echo(featuresSelected.length + ' checkboxes checked found');
                casper.test.assert(utils.equals(cachedFeatures, featuresSelected), 'The cached features and the checkboxes checked match');
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


function Scenario() {

    var tasks = new Tasks();
    var AnnotatorTasks = tasks.AnnotatorTasks;

    /*
    - @Scenario1
    - Select any graph. A dialog box should be opened. Make sure that:
    - The features and the components in the dialog correspond to the relative graph and allograph selected
    - The label corresponds to the one selected into the allographs select in the panel above the image
    - Close the box. Reopen it.
    */

    this.Scenario1 = function() {

        casper.echo('Running Annotator Scenario 1', 'PARAMETER');
        var feature = AnnotatorTasks.get.random_vector();
        AnnotatorTasks.do.select(feature.id, function() {
            casper.test.assertExists('.dialog_annotations', 'The dialog is loaded');
            casper.test.assertVisible('.dialog_annotations', 'the dialog is visible on the page');
            var features_selected = tasks.AnnotatorTasks.dialog.getSelectedFeatures();
            AnnotatorTasks.tests.dialogMatchesCache(features_selected);
            var labels = casper.evaluate(function() {
                var dialog_label = $('.allograph_label').text();
                var form_allograph_label = $('#panelImageBox .allograph_form option:selected').text();
                return {
                    'dialog_label': dialog_label,
                    'form_allograph_label': form_allograph_label
                };
            });
            casper.test.assertEquals(labels.dialog_label, labels.form_allograph_label, 'The dialog label and the allograph form label coincide');
            AnnotatorTasks.dialog.close();
            casper.test.assertDoesntExist('.dialog_annotations', 'Dialog closed.');
        });
    };

    /*
    - @Scenario2
    - Select any graph.
    - Check some features checkboxes, save the graph and close the box. Reopen it and make sure the changes are clearly visible. Refresh the page and open it again.
    - Change hand or/and allograph, save the graph. Deselect the graph, then reselect it. Refresh the page and check that everything matches with your changes.
    */

    this.Scenario2 = function() {
        casper.echo('Running Annotator Scenario 2', 'PARAMETER');

        var actions = function(feature) {
            AnnotatorTasks.do.select(feature.id, function() {
                var features_selected = tasks.AnnotatorTasks.dialog.getSelectedFeatures();
                AnnotatorTasks.tests.dialogMatchesCache(features_selected);
            });
        };

        var feature = AnnotatorTasks.get.random_vector();

        casper.wait(200, function() {
            casper.then(function() {
                AnnotatorTasks.do.annotate(feature.id, true, function() {
                    AnnotatorTasks.dialog.close();
                    AnnotatorTasks.do.unselect();
                });
            });

            casper.wait(1000, function() {
                casper.then(function() {
                    actions(feature);
                });
            });

            casper.then(function() {
                casper.echo('Reloading page ...');
                casper.reload(function() {
                    actions(feature);
                });
            });
        });

    };


    /*
    - @ScenarioN
    - Select all graphs in page and check they match with their local cache
    */

    this.ScenarioN = function() {
        var features = AnnotatorTasks.get.features();
        var i = 0;
        casper.eachThen(features, function(response) {
            tasks.AnnotatorTasks.get.select(response.data.id, function() {
                var features_selected = tasks.AnnotatorTasks.dialog.getSelectedFeatures();
                AnnotatorTasks.tests.dialogMatchesCache(features_selected);
            });
        });
    };

}

(function() {
    var page = '/digipal/page/121';
    var annotatorTest = new AnnotatorTest({
        "page": page
    });
    annotatorTest.init();
})();