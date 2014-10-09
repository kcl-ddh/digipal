function Scenario() {

    this.dependencies = ['actions.js'];
    this.middleware = ['login.js'];

    this.Scenarios = function(dependencies, options) {

        var self = this;
        var AnnotatorTasks = dependencies.AnnotatorTasks;

        /*
        - @Scenario1
        - Select any graph. A dialog box should be opened. Make sure that:
        - The features and the components in the dialog correspond to the relative graph and allograph selected
        - The label corresponds to the one selected into the allographs select in the panel above the image
        - Close the box. Reopen it.
        */

        this.Scenario1 = function() {

            var isAnnotatorLoaded = casper.evaluate(function() {
                return typeof annotator !== 'undefined' && annotator.annotations && annotator.vectorLayer.features;
            });

            if (isAnnotatorLoaded) {
                casper.echo('The annotator is loaded', 'INFO');
            }

            var features = AnnotatorTasks.get.features();
            casper.echo(features.length + ' features found', 'INFO');

            if (!features.length) {
                casper.echo('Hey, wait, this scenario needs an image with at least one feature', 'WARNING');
                casper.echo('Please provide another image to continue');
                return casper.exit();
            }
            self.features = features;
            casper.echo('Running Annotator Scenario 1', 'PARAMETER');

            if (AnnotatorTasks.tabs.current() !== '#annotator') {
                AnnotatorTasks.tabs.
                switch ('annotator');
            }

            casper.evaluate(function() {
                if (annotator.editorial.active) {
                    annotator.editorial.deactivate();
                }
            });

            var isMultipleSelected = casper.evaluate(function() {
                return annotator.multiple_annotations;
            });

            var isAnnotatingSelected = casper.evaluate(function() {
                return annotator.annotating;
            });

            if (isMultipleSelected) {
                AnnotatorTasks.options.clickOption('multiple_annotations');
            }

            if (!isAnnotatingSelected) {
                AnnotatorTasks.options.clickOption('development_annotation');
            }

            var feature = AnnotatorTasks.get.random_vector(features);
            console.log('Graph selected:' + feature.graph);
            casper.then(function() {
                AnnotatorTasks.do .
                select(feature.graph, function() {
                    casper.test.assertExists('.dialog_annotations', 'The dialog is loaded');
                    casper.test.assertVisible('.dialog_annotations', 'the dialog is visible on the page');
                    casper.wait(1000, function() {
                        var features_selected = AnnotatorTasks.dialog.getSelectedFeatures();
                        AnnotatorTasks.tests.dialogMatchesCache(features_selected);
                        var labels = casper.evaluate(function() {
                            var dialog_label = $('.allograph_label').text();
                            var form_allograph_label = $('#annotator .allograph_form option:selected').text();
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
                AnnotatorTasks.do .
                select(feature.id, function() {
                    casper.wait(1000, function() {
                        var features_selected = AnnotatorTasks.dialog.getSelectedFeatures();
                        AnnotatorTasks.tests.dialogMatchesCache(features_selected);
                    });
                });
            };

            var feature = AnnotatorTasks.get.random_vector(self.features);

            casper.then(function() {
                AnnotatorTasks.do .
                annotate(feature.id, true, function() {
                    AnnotatorTasks.dialog.close();
                    AnnotatorTasks.do .
                    unselect();
                });
            });

            casper.then(function() {
                casper.wait(1000, function() {
                    actions(feature);
                });
            });

            casper.then(function() {
                casper.echo('Reloading page...');
                casper.reload(function() {
                    actions(feature);
                });
            });

            casper.then(function() {
                casper.echo('Reloading page...');
                casper.reload(function() {
                    AnnotatorTasks.do .
                    annotate(null, true, function() {
                        AnnotatorTasks.dialog.close();
                        AnnotatorTasks.do .
                        unselect();
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
            var feature = AnnotatorTasks.get.random_vector(self.features);
            var allograph_id = feature.allograph_id;
            AnnotatorTasks.do .
            select(feature.id, function() {

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
                        console.log(found, vectors_ids.length);
                        casper.test.assert(found === vectors_ids.length, 'All images have been loaded');
                        casper.click('.close_top_div_annotated_allographs');
                        casper.test.assertDoesntExist('.close_top_div_annotated_allographs', 'The windows has been closed');
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

            AnnotatorTasks.do .
            unselect();

            var isMultipleSelected = casper.evaluate(function() {
                return annotator.multiple_annotations;
            });

            var isAnnotatingSelected = casper.evaluate(function() {
                return annotator.annotating;
            });

            casper.then(function() {
                console.log('Enabling multiple annotations option');

                if (!isMultipleSelected) {
                    AnnotatorTasks.options.clickOption('multiple_annotations');
                }

                if (!isAnnotatingSelected) {
                    AnnotatorTasks.options.clickOption('development_annotation');
                }
            });

            var feature = AnnotatorTasks.get.random_vector(self.features);
            var feature2 = AnnotatorTasks.get.random_vector(self.features);

            casper.then(function() {
                while (feature.allograph_id !== feature2.allograph_id) {
                    feature2 = AnnotatorTasks.get.random_vector(self.features);
                    AnnotatorTasks.do .
                    select(feature2.id);
                }
            });

            casper.then(function() {
                AnnotatorTasks.do .
                unselect();
                AnnotatorTasks.do .
                select(feature.id);
            });

            casper.then(function() {
                AnnotatorTasks.do .
                select(feature2.id);
            });

            casper.then(function() {
                casper.wait(1200, function() {
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
            AnnotatorTasks.do .
            loadCache();

            casper.then(function() {
                console.log('Enabling multiple annotations option');
                AnnotatorTasks.options.clickOption('multiple_annotations');
                var isEnabled = casper.evaluate(function() {
                    return annotator.selectFeature.multiple;
                });
                console.log("Enalbled: " + isEnabled);
            });

            casper.then(function() {
                AnnotatorTasks.do .
                unselect();
                casper.then(function() {
                    feature = AnnotatorTasks.get.random_vector(self.features);
                    feature2 = AnnotatorTasks.get.random_vector(self.features);

                    AnnotatorTasks.do .
                    select(feature.id);
                    AnnotatorTasks.do .
                    select(feature2.id);

                    casper.echo('Looking for different allographs with common components...');
                    while (feature.allograph_id !== feature2.allograph_id && !AnnotatorTasks.get.common_components(feature, feature2).length) {
                        (function() {
                            feature2 = AnnotatorTasks.get.random_vector(self.features);
                            AnnotatorTasks.do .
                            unselect();

                            casper.then(function() {
                                AnnotatorTasks.do .
                                select(feature.id);
                            });

                            casper.then(function() {
                                AnnotatorTasks.do .
                                select(feature2.id);
                            });
                        })();
                    }
                });

                casper.then(function() {
                    casper.echo(AnnotatorTasks.get.common_components(feature, feature2));
                    casper.wait(1500);
                });

                casper.then(function() {
                    var common_features = AnnotatorTasks.get.common_features(feature, feature2);
                    var areFeaturesChecked = casper.evaluate(function(common_features) {
                        console.log(annotator.selectedAnnotations.length);
                        console.log(common_features.length, $('.features_box:checked').length || "null");
                        return common_features.length === $('.features_box:checked').length;
                    }, common_features);

                    casper.test.assert(areFeaturesChecked, 'The number of common features coincides with the number of checkboxes checked');

                    AnnotatorTasks.do .
                    unselect();

                    casper.wait(500, function() {
                        AnnotatorTasks.do .
                        annotate(feature.id, true);
                    });

                    casper.wait(500, function() {
                        AnnotatorTasks.do .
                        annotate(feature2.id, true);
                    });

                    casper.wait(500, function() {
                        var features_selected = AnnotatorTasks.dialog.getSelectedFeatures();
                        AnnotatorTasks.tests.dialogMatchesCache(features_selected);
                    });
                });
            });

        };

        this.Scenario6 = function() {
            casper.echo('Running Annotator Scenario 6', 'PARAMETER');
            casper.echo('Unselecting all annotations...');
            AnnotatorTasks.do .
            unselect();
            feature = AnnotatorTasks.get.random_vector(self.features);
            AnnotatorTasks.do .
            select(feature.id, function() {
                casper.echo('Generating url for graph ' + feature.id + '...');
                AnnotatorTasks.do .
                generateUrl(function() {
                    AnnotatorTasks.do .
                    unselect();
                    AnnotatorTasks.options.clickOption('development_annotation');
                    AnnotatorTasks.do .
                    annotate(null, false, function() {
                        casper.test.assertExists('.dialog_annotations', 'The dialog has been loaded');
                        casper.test.assertExists('.name_temporary_annotation', 'Input temporary annotation loaded');
                        casper.test.assertExists('.public_text_dialog_div', 'Textarea temporary annotation loaded');
                        casper.fillSelectors('.ui-dialog', {
                            ".name_temporary_annotation": 'Name',
                            ".public_text_dialog_div": "<b>Content</b>"
                        }, false);
                        AnnotatorTasks.do .
                        generateUrl();
                    }, false);
                });
            });
        };

        this.Scenario7 = function() {
            console.log('Activating editorial annotations');
            AnnotatorTasks.do .
            unselect();
            AnnotatorTasks.options.clickOption('multiple_annotations');
            AnnotatorTasks.options.clickOption('development_annotation');
            casper.evaluate(function() {
                annotator.editorial.activate();
            });
            AnnotatorTasks.do .
            annotate(null, false, function() {
                casper.then(function() {
                    casper.wait(800, function() {
                        casper.test.assertExists('#internal_note', 'The internal note textarea exists');
                        casper.test.assertExists('#display_note', 'The public note textarea exists');
                        casper.evaluate(function() {
                            $('#internal_note').html('Internal Note');
                            $('#display_note').html('Display Note');
                        });

                        AnnotatorTasks.do .
                        save(function() {
                            AnnotatorTasks.do .
                            unselect();
                            /*
                            AnnotatorTasks.do.select(vector_id, function() {
                                var values = casper.evaluate(function() {
                                    return {
                                        'internal_note': $('#internal_note').html(),
                                        'display_note': $('#display_note').html()
                                    };
                                });
                                casper.test.assertEquals(values.internal_note, 'Internal Note', 'Internal note text matches');
                                casper.test.assertEquals(values.display_note, 'Display Note', 'Display note text matches');
                            });
                        */
                        });
                    });
                });
            }, false);
        };
    };
}

exports.AnnotatorTest = new Scenario();