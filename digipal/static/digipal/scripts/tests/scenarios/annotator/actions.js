var Actions = function(options) {

    var self = this;

    this.name = 'AnnotatorTasks';

    this.actions = {
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

            adminAccess: function(admin_page, username, password, page_id) {
                var page = options.root + '/digipal/page/' + page_id;

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
                /*
                    Look for a feature that HAS a graph and is NOT undefined
                 */
                var feature = features[Math.round(Math.random() * features.length)];
                while (typeof feature == 'undefined' || feature && !feature.hasOwnProperty('graph')) {
                    feature = features[Math.round(Math.random() * features.length)];
                }
                return feature;
            },

            get_components: function(feature) {
                return casper.evaluate(function(feature) {
                    var _components = [];
                    var cachedAllograph = annotator.cacheAnnotations.cache.allographs[feature.allograph_id].components;
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
                    if (annotator.cacheAnnotations.cache.graphs.hasOwnProperty(feature.graph)) {
                        var cachedGraph = annotator.cacheAnnotations.cache.graphs[feature.graph];
                        for (var i = 0; i < cachedGraph.features.length; i++) {
                            _feature = {
                                'id': cachedGraph.features[i].feature[0],
                                'component_id': cachedGraph.features[i].component_id
                            };
                            _features.push(_feature);
                        }
                    } else {
                        casper.echo("The graph" + feature.graph + " has not been found in cache", "ERROR");
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

            annotate: function(feature, describe, callback, save) {
                var self = this;

                var execute = function() {
                    if (describe) {
                        self.describeForms();
                    }
                    casper.then(function() {
                        casper.wait(1000, function() {
                            if (describe) {
                                console.log('Describing feature...');
                                self.describe(null, true);
                            }
                            if (save || typeof save === 'undefined') {
                                self.save(callback);
                            } else {
                                if (typeof callback !== 'undefined' && callback instanceof Function) {
                                    callback();
                                }
                            }
                        });
                    });
                };

                casper.then(function() {
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
                });
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
                            var error = casper.evaluate(function() {
                                return $('#status').text();
                            });
                            casper.echo('Error:' + error, 'ERROR');
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
                        fillOpacity: 0.5,
                        stored: false,
                        features: [],
                        linked_to: []
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
                - @reusable for AllographsActions
                - specify "allographs" as value of page, or leave empty if for Actions
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
                            condition = !$(this).attr('checked');
                        } else {
                            condition = $(this).attr('checked');
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
                } else if (!page || page == 'annotator') {
                    dialog = '#panelImageBox';
                }

                casper.evaluate(function(dialog) {
                    dialog = $(dialog);
                    if (!dialog.find('.allograph_form').val()) {
                        dialog.find('.allograph_form').val(13).trigger('change');
                    }
                    if (!dialog.find('.hand_form').val()) {
                        dialog.find('.hand_form').val(345).trigger('change');
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
                var features = self.actions.get.features();
                var i = 0;
                casper.echo('Caching all graphs', 'INFO');
                casper.eachThen(features, function(response) {
                    if (response && typeof response.hasOwnProperty('data') && response.data && response.data.hasOwnProperty('id')) {
                        var id = response.data.id;
                        if (id) {
                            self.actions.do.select(id, function() {
                                if (casper.evaluate(function(id) {
                                    return annotator.cacheAnnotations.cache.graphs.hasOwnProperty(id);
                                }), id) {
                                    console.log(id + ' loaded in cache');
                                }
                            });
                        }
                    } else {
                        casper.echo('It was not possible to cache a graph', 'ERROR');
                        casper.echo(JSON.stringify(response.data), 'WARNING');
                    }
                });
            },
            generateUrl: function(callback) {
                casper.click('.url_allograph');
                casper.wait(1000, function() {
                    casper.test.assertExists('.allograph_url_div', 'The URL has been generated');
                    casper.click('#long_url');
                    var url = casper.evaluate(function() {
                        return $('.allograph_url_div input').val();
                    });
                    url = url.replace(/(.)*\/digipal/, options.root + '/digipal');
                    casper.thenOpen(url, function() {
                        casper.test.assertExists('.dialog_annotations', 'The dialog has been correctly loaded');
                        if (typeof callback !== 'undefined' && callback instanceof Function) {
                            callback();
                        }
                    });
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
                        @ reusable for AllographActions
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
                        @ reusable for AllographsActions
                        - specify page = 'allographs' and a graph as third parameter
                         */
            dialogMatchesCache: function(featuresSelected, page, graph) {
                var cachedFeatures = casper.evaluate(function(page, graph) {
                    var graphCache;
                    if (page == 'annotator' || !page) {
                        graphCache = annotator.cacheAnnotations.cache.graphs[annotator.selectedFeature.graph];
                    } else {
                        if (!graph) {
                            throw new Error('A graph must be provided if using the function in AllographsActions Scenarios');
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
        },

        tabs: {

            switch: function(target) {
                casper.click(x('//a[@data-target="#' + target + '"]'));
                console.log('Switched to tab ' + target);
            },

            current: function() {
                return casper.evaluate(function() {
                    return $('.nav li.active.in').find('a').data('target');
                });
            }

        }
    };
};

exports.Actions = function(options) {
    return new Actions(options);
};