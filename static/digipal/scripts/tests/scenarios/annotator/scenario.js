function Scenario() {

    var Tasks = function(options) {

        var tasks = {
            _self: this,
            get: {

                features: function() {
                    return casper.evaluate(function() {
                        return annotator.vectorLayer.features;
                    });
                },

                featuresByAllograph: function(allograph_id, attribute) {
                    return casper.evaluate(function(allograph_id, attribute) {
                        var features = annotator.vectorLayer.features;
                        var featuresByAllograph = [];
                        for (var i = 0; i < features.length; i++) {
                            if (features[i].allograph_id == allograph_id) {
                                if (attribute) {
                                    featuresByAllograph.push(features[i][attribute]);
                                } else {
                                    featuresByAllograph.push(features[i]);
                                }
                            }
                        }
                        return JSON.parse(JSON.stringify(featuresByAllograph));
                    }, allograph_id, attribute);
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
                    var page = options.page + '/digipal/page/80';

                    var isAdmin = casper.evaluate(function() {
                        if (typeof annotator === 'undefined') {
                            return false;
                        } else {
                            return annotator.isAdmin;
                        }
                    });

                    if (isAdmin === 'True') {
                        return casper;
                    } else {
                        casper.thenOpen(admin_page, function() {
                            this.fill('form#login-form', {
                                'username': username,
                                'password': password
                            }, true);
                        });

                        return casper.thenOpen(page, function() {
                            return casper;
                        });
                    }
                },

                random_vector: function(features) {
                    return features[Math.round(Math.random() * features.length)];
                },

                get_components: function(feature) {
                    return casper.evaluate(function(feature) {
                        var _components = [];
                        var cachedAllograph = annotator.cacheAnnotations.cache.allographs[feature.allograph_id];
                        for (var i in cachedAllograph) {
                            _components.push(cachedAllograph[i].id);
                        }
                        return _components;
                    }, feature);
                },

                get_graphs_features: function(feature) {
                    return casper.evaluate(function(feature) {
                        var _features = [];
                        var _feature;
                        var cachedGraph = annotator.cacheAnnotations.cache.graphs[feature.graph];
                        for (var i = 0; i < cachedGraph.features.length; i++) {
                            _feature = {
                                'id': cachedGraph.features[i].feature[0],
                                'component_id': cachedGraph.features[i].component_id
                            };
                            _features.push(_feature);
                        }
                        return _features;
                    }, feature);
                },

                common_components: function(feature, feature2) {

                    var components = this.get_components(feature);
                    var components2 = this.get_components(feature2);
                    var common_components = [];

                    console.log('Components for graph ' + feature.id + ': ' + components);
                    console.log('Components for graph ' + feature2.id + ': ' + components2);

                    for (var i = 0; i < components.length; i++) {
                        if (components2.indexOf(components[i]) >= 0) {
                            common_components.push(components[i]);
                        }
                    }
                    return common_components;
                },

                common_features: function(feature, feature2) {
                    var features = this.get_graphs_features(feature);
                    var features2 = this.get_graphs_features(feature2);

                    var common_features = [];

                    for (var i = 0; i < features.length; i++) {
                        for (var j = 0; j < features2.length; j++) {
                            if (features2[j].id == features[i].id && features2[j].component_id == features[i].component_id) {
                                common_features.push(features[i]);
                            }
                        }
                    }

                    return common_features;
                },

                getGraphByVectorId: function(vector_id) {
                    return casper.evaluate(function(vector_id) {
                        var graph, features = annotator.vectorLayer.features;
                        for (var i = 0; i < features.length; i++) {
                            if (features[i].vector_id == vector_id) {
                                graph = features[i].graph;
                            }
                        }
                        return graph;
                    }, vector_id);
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
                    var execute = function() {
                        casper.then(function() {
                            self.describeForms();
                            casper.wait(1000, function() {
                                if (describe) {
                                    console.log('Describing feature...');
                                    self.describe();
                                }
                                casper.capture('screen.png');
                                self.save(callback);
                            });
                        });
                    };

                    if (feature) {
                        self.select(feature, function() {
                            console.log('Annotating feature: ' + feature);
                            execute();
                        });
                    } else {
                        console.log('Drawing new feature...');
                        self.drawFeature(function() {
                            execute();
                        });
                    }
                },

                save: function(callback) {
                    casper.echo('Saving Annotations...');
                    casper.evaluate(function() {
                        annotator.saveButton.trigger();
                    });
                    casper.wait(1500, function() {
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
                    casper.echo('Deleting Annotations...');
                    return casper.evaluate(function() {
                        return annotator.deleteFeature.clickFeature();
                    });
                },

                refreshLayer: function() {
                    return casper.evaluate(function() {
                        return annotator.refresh_layer();
                    });
                },

                drawFeature: function(callback) {
                    casper.evaluate(function() {
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
                    });
                    if (callback) {
                        return callback();
                    }

                },

                /*
                - @reusable for AllographsTasks
                - specify "allographs" as value of page, or leave empty if for Tasks
                - specify check = false if you want to undescribe checkboxes
                */

                describe: function(page, check) {
                    var checkboxes = casper.evaluate(function(page, check) {
                        var features_elements;
                        var _checkboxes = [];
                        if (page == 'annotator' || !page) {
                            features_elements = $('.dialog_annotations .features_box');
                        } else if (page == 'allographs') {
                            features_elements = $('.myModal .features_box');
                        }

                        var n = 0;
                        $.each(features_elements, function() {
                            var condition;

                            if (check === true || typeof check === 'undefined') {
                                condition = $(this).attr('checked');
                            } else {
                                condition = !$(this).attr('checked');
                            }

                            if (condition) {
                                if (n > 5) {
                                    return false;
                                }
                                _checkboxes.push($(this).attr('id').split('_')[1]);
                                n++;
                            }
                        });
                        return _checkboxes;
                    }, page, check);

                    for (var i = 0; i < checkboxes.length; i++) {
                        casper.click(x('//input[@data-feature="' + checkboxes[i] + '"]'));
                    }
                },

                describeForms: function(page) {
                    var dialog;

                    if (page == 'allographs') {
                        dialog = '#modal_features';
                    } else {
                        dialog = '#panelImageBox';
                    }
                    casper.evaluate(function(dialog) {
                        dialog = $(dialog);
                        if (!dialog.find('allograph_form').val()) {
                            dialog.find('allograph_form').val(13).trigger('change');
                        }
                        if (!dialog.find('hand_form').val()) {
                            dialog.find('.hand_form').val(312).trigger('change');
                        }
                        return $('select').trigger('liszt:updated');
                    }, dialog);
                },

                select: function(feature, callback) {

                    casper.then(function() {
                        casper.evaluate(function(feature) {
                            annotator.selectFeatureById(feature);
                        }, feature);
                    });

                    casper.then(function() {
                        casper.wait(500, function() {
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
                },

                loadCache: function() {
                    var self = this;
                    var features = tasks.get.features();
                    var i = 0;
                    casper.echo('Caching all graphs', 'INFO');
                    casper.eachThen(features, function(response) {
                        if (response && typeof response.hasOwnProperty('data') && response.data && response.data.hasOwnProperty('id')) {
                            var id = response.data.id;
                            tasks.do.select(id, function() {
                                if (casper.evaluate(function(id) {
                                    return annotator.cacheAnnotations.cache.graphs.hasOwnProperty(id);
                                }), id) {
                                    console.log(id + ' loaded in cache');
                                }
                            });
                        } else {
                            casper.echo('It was not possible to cache a graph', 'ERROR');
                        }
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
                        if (typeof value !== 'undefined') {
                            annotator.boxes_on_click = value;
                        }
                        return annotator.boxes_on_click;
                    }, value);
                },

                annotating: function(value) {
                    return casper.evaluate(function(value) {
                        if (typeof value !== 'undefined') {
                            annotator.annotating = value;
                        }
                        return annotator.annotating;
                    }, value);
                },

                multiple_annotations: function(value) {
                    return casper.evaluate(function(value) {
                        if (typeof value !== 'undefined') {
                            $("#multiple_annotations").prop('checked', value);
                        }
                        return $("#multiple_annotations").prop('checked');
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

                /*
                        @ reusable for AllographTasks
                        - specify page = 'allographs'
                         */
                getSelectedFeatures: function(page) {
                    return casper.evaluate(function(page) {
                        var features_selected = [];
                        var dialog;

                        if (page == 'annotator' || !page) {
                            dialog = $('.dialog_annotations');
                        } else if (page == 'allographs') {
                            dialog = $('#modal_features');
                        }

                        features_elements = dialog.find('.features_box');
                        features_elements.each(function() {
                            if ($(this).is(':checked')) {
                                var label = dialog.find('label[for=' + $(this).attr('id') + ']').text();
                                features_selected.push(label);
                            }
                        });
                        return features_selected;
                    }, page);
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
                /*
                        @ reusable for AllographsTasks
                        - specify page = 'allographs' and a graph as third parameter
                         */
                dialogMatchesCache: function(featuresSelected, page, graph) {
                    var cachedFeatures = casper.evaluate(function(page, graph) {
                        var graphCache;
                        if (page == 'annotator' || !page) {
                            graphCache = annotator.cacheAnnotations.cache.graphs[annotator.selectedFeature.graph];
                        } else {
                            if (!graph) {
                                throw new Error('A graph must be provided if using the function in AllographsTasks Scenarios');
                            }
                            graphCache = allographsPage.cache.cache.graphs[graph];
                        }
                        var _cachedFeatures = [];
                        for (var i = 0; i < graphCache.features.length; i++) {
                            _cachedFeatures.push(graphCache.features[i].feature[0]);
                        }
                        return _cachedFeatures;
                    }, page, graph);
                    casper.echo(cachedFeatures.length + ' cached features found');
                    casper.echo(featuresSelected.length + ' checkboxes checked found');
                    casper.test.assert(utils.equals(cachedFeatures, featuresSelected), 'The cached features and the checkboxes checked match');
                },
            }
        };

        return tasks;
    };

    this.Tasks = Tasks;

    var Tabs = {

        switch: function(target) {
            casper.click(x('//a[@data-target="#' + target + '"]'));
            console.log('Switched to tab ' + target);
        },

        current: function() {
            return casper.evaluate(function() {
                return $('.nav li.active.in').find('a').data('target');
            });
        }

    };

    var Scenarios = function() {
        var AnnotatorTasks = new Tasks();

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

            if (Tabs.current() !== '#annotator') {
                Tabs.switch('annotator');
            }

            AnnotatorTasks.options.multiple_annotations(false);

            var feature = AnnotatorTasks.get.random_vector(features);

            casper.then(function() {
                AnnotatorTasks.do.select(feature.id, function() {
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
        var tasks = new this.Tasks(options);

        tasks.get.adminAccess(options.page + '/admin', casper.cli.get('username'), casper.cli.get('password'))
            .then(function() {
                var scenarios = new Scenarios();
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