function Scenario() {

    var Scenarios = function(AnnotatorTasks) {

        var features = AnnotatorTasks.get.features();

        /*
        - @Scenario1
        - Select any graph. A dialog box should be opened. Make sure that:
        - The features and the components in the dialog correspond to the relative graph and allograph selected
        - The label corresponds to the one selected into the allographs select in the panel above the image
        - Close the box. Reopen it.
        */

        this.Scenario1 = function() {

            casper.echo('Running Annotator Scenario 1', 'PARAMETER');

            if (AnnotatorTasks.tabs.current() !== '#annotator') {
                AnnotatorTasks.tabs.switch('annotator');
            }

            AnnotatorTasks.options.multiple_annotations(false);

            var feature = AnnotatorTasks.get.random_vector(features);

            casper.then(function() {
                AnnotatorTasks.do.select(feature.vector_id, function() {
                    casper.test.assertExists('.dialog_annotations', 'The dialog is loaded');
                    casper.test.assertVisible('.dialog_annotations', 'the dialog is visible on the page');
                    casper.wait(500, function() {
                        var features_selected = AnnotatorTasks.dialog.getSelectedFeatures();
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
                });
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
                    casper.wait(1000, function() {
                        var features_selected = AnnotatorTasks.dialog.getSelectedFeatures();
                        AnnotatorTasks.tests.dialogMatchesCache(features_selected);
                    });
                });
            };

            var feature = AnnotatorTasks.get.random_vector(features);

            casper.then(function() {
                AnnotatorTasks.do.annotate(feature.id, true, function() {
                    AnnotatorTasks.dialog.close();
                    AnnotatorTasks.do.unselect();
                });
            });

            casper.wait(1000, function() {
                actions(feature);
            });

            casper.then(function() {
                casper.echo('Reloading page ...');
                casper.reload(function() {
                    actions(feature);
                });
            });

            casper.then(function() {
                casper.echo('Reloading page ...');
                casper.reload(function() {
                    AnnotatorTasks.do.annotate(null, true, function() {
                        casper.capture('screen.png');
                        AnnotatorTasks.dialog.close();
                        AnnotatorTasks.do.unselect();
                    });
                });
            });
        };

        /*
        - @Scenario3
        - Select any graph.
        - Click the button to open the graphs of the same allograph you selected. Check they are all correct. Furthermore, they should be grouped for hand, check they are correct.
        - Deselect the graph, now change allograph in the dropdown and re-click the button to see a popup containing all the graphs common to the selected allograph. Now the popup should show the graphs related to the selected allograph according to the dropdown.
         */


        this.Scenario3 = function() {
            casper.echo('Running Annotator Scenario 3', 'PARAMETER');
            var feature = AnnotatorTasks.get.random_vector(features);
            var allograph_id = feature.allograph_id;
            AnnotatorTasks.do.select(feature.id, function() {

                casper.then(function() {
                    casper.click('.number-allographs');
                    casper.test.assertExists('.letters-allograph-container', 'The Popup window exists');
                    casper.test.assertVisible('.letters-allograph-container', 'The Popup window is visible');
                });

                casper.then(function() {
                    casper.wait(1000, function() {
                        var featuresByAllograph = AnnotatorTasks.get.featuresByAllograph(allograph_id, 'graph');
                        var vectors_ids = (function() {
                            return casper.evaluate(function() {
                                var ids = [];
                                var vectors = $('.vector_image_link');
                                $.each(vectors, function() {
                                    ids.push($(this).data('graph'));
                                });
                                return JSON.parse(JSON.stringify(ids));
                            });
                        })();

                        var found = 0;
                        for (var i = 0; i < vectors_ids.length; i++) {
                            for (var j = 0; j < featuresByAllograph.length; j++) {
                                if (featuresByAllograph[j] == vectors_ids[i]) {
                                    found++;
                                }
                            }
                        }
                        casper.test.assert(found === vectors_ids.length, 'All images have been loaded');
                    });
                });

            });
        };

        /*
        - @Scenario4
        - Select two graphs, with different allograph, which have no common components
        - The popup should clearly state there are no common components
         */

        this.Scenario4 = function() {
            casper.echo('Running Annotator Scenario 4', 'PARAMETER');

            casper.then(function() {
                console.log('Enabling multiple annotations option');
                AnnotatorTasks.options.clickOption('multiple_annotations');
            });

            var feature = AnnotatorTasks.get.random_vector(features);
            var feature2 = AnnotatorTasks.get.random_vector(features);

            casper.then(function() {
                while (feature.allograph_id !== feature2.allograph_id) {
                    feature2 = AnnotatorTasks.get.random_vector(features);
                }
            });

            casper.then(function() {
                AnnotatorTasks.do.select(feature.id);
            });

            casper.then(function() {
                AnnotatorTasks.do.select(feature2.id);
            });

            casper.then(function() {
                casper.wait(800, function() {
                    casper.test.assertExists('.dialog_annotations', 'The dialog has been created');
                    if (!AnnotatorTasks.get.common_components(feature, feature2).length) {
                        casper.echo('The two features have no common components');
                        casper.test.assertSelectorHasText('.dialog_annotations', 'No common components', 'The window clearly states that the two graph have no common components');
                    } else {
                        casper.echo('The two features have common components');
                        casper.test.assertExists('.features_box', 'The window clearly states that the two graph have common components and their features are visible');
                    }
                });
            });

        };

        /*
        - Select two graphs, with different allograph, which have common components
        - Only the common components should be shown
        - Make sure that:
            - Common features are ticked or unticked
            - Uncommon features are indeterminate
            - Try various combinations saving the graphs, like:
            - Tick a feature and save the graphs.
            - Select the graphs and make sure both have the selected feature.
            - Now try to save a feature only on one graph. Then re-select both of them and make sure that the uncommon feature is indeterminate
         */

        this.Scenario5 = function() {
            casper.echo('Running Annotator Scenario 5', 'PARAMETER');
            var feature, feature2;
            AnnotatorTasks.options.multiple_annotations(false);
            AnnotatorTasks.do.loadCache();

            casper.then(function() {
                console.log('Enabling multiple annotations option');
                AnnotatorTasks.options.clickOption('multiple_annotations');
            });

            casper.then(function() {

                feature = AnnotatorTasks.get.random_vector(features);
                feature2 = AnnotatorTasks.get.random_vector(features);

                AnnotatorTasks.do.select(feature.id);
                AnnotatorTasks.do.select(feature2.id);

                casper.echo('Looking for different allographs with common components...');

                while (feature.allograph_id !== feature2.allograph_id && !AnnotatorTasks.get.common_components(feature, feature2).length) {
                    feature2 = AnnotatorTasks.get.random_vector(features);
                    AnnotatorTasks.do.unselect();
                    AnnotatorTasks.do.select(feature.id);
                    AnnotatorTasks.do.select(feature2.id);
                }

                casper.then(function() {
                    var common_features = AnnotatorTasks.get.common_features(feature, feature2);
                    var areFeaturesChecked = casper.evaluate(function(common_features) {
                        return common_features.length === $('.features_box:checked').length;
                    }, common_features);

                    casper.test.assert(areFeaturesChecked, 'The number of common features coincides with the number of checkboxes checked');

                    casper.wait(500, function() {
                        AnnotatorTasks.do.annotate(feature.id, true);
                    });

                    casper.wait(500, function() {
                        AnnotatorTasks.do.annotate(feature2.id, true);
                    });

                    casper.wait(500, function() {
                        var features_selected = AnnotatorTasks.dialog.getSelectedFeatures();
                        AnnotatorTasks.tests.dialogMatchesCache(features_selected);
                    });
                });
            });

        };
    };

    this.init = function(options) {
        var AnnotatorTasks = require('./actions.js').Actions(options);

        AnnotatorTasks.get.adminAccess(options.page + '/admin', casper.cli.get('username'), casper.cli.get('password'))
            .then(function() {
                var scenarios = new Scenarios(AnnotatorTasks);
                var scenariosList = [];
                for (var i in scenarios) {
                    scenariosList.push(scenarios[i]);
                }
                casper.eachThen(scenariosList, function(response) {
                    response.data.call();
                });

            });
    };

}

exports.AnnotatorTest = new Scenario();