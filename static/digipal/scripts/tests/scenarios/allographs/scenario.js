var AnnotatorScenario = require('../annotator/scenario.js');

function Scenario() {

    var Tasks = function(options) {

        var tasks = {
            _self: this,

            get: {
                random_vector: function() {
                    return casper.evaluate(function() {
                        var annotations = $('.annotation_li');
                        var random = Math.round(Math.random() * annotations.length);
                        return $(annotations[random]).data('annotation');
                    });
                }
            },

            do :{

                select: function(feature_id, callback) {

                    casper.click('.annotation_li[data-annotation="' + feature_id + '"]');
                    casper.test.assertExists('.selected', 'Element is correctly selected. Class .selected exists.');
                    casper.then(function() {
                        casper.wait(500, function() {
                            if (callback) {
                                return callback();
                            }
                        });
                    });
                },

                save: function(callback) {
                    casper.echo('Saving Annotations...');
                    casper.click('#save');
                    casper.wait(1500, function() {
                        if (casper.evaluate(function() {
                            return $('#status').hasClass('alert-success');
                        })) {
                            casper.echo('Annotation succesfully saved', 'INFO');
                        } else {
                            casper.echo('Annotation not saved', 'ERROR');
                        }
                        if (callback) {
                            return callback();
                        }
                    });
                },

                delete: function(callback) {
                    casper.echo('Deleting Annotations...');
                    casper.click('#delete');
                    casper.wait(500, function() {
                        if (casper.evaluate(function() {
                            return $('#status').hasClass('alert-success');
                        })) {
                            casper.echo('Annotation succesfully deleted', 'INFO');
                        } else {
                            casper.echo('Annotation not deleted', 'ERROR');
                        }
                        if (callback) {
                            return callback();
                        }
                    });
                },

                selectAllGraphsInRow: function() {

                    casper.echo('Selecting all selected graphs in first row...');
                    casper.click(x('[@class="select_all"][1]'));

                    return casper.evaluate(function() {
                        var selected_elements = $($('.allograph-item panel')[0]).find('.annotation_li');
                        var n = 0;
                        return selected_elements.each(function() {
                            if ($(this).hasClass("selected")) {
                                n++;
                            }
                            return n === selected_elements.length;
                        });
                    });
                },

                deselect_all_graphs: function() {
                    casper.echo('Deselecting all selected graphs...');
                    casper.click('.deselect_all_graphs');
                    casper.test.assertDoesntExist('.selected', 'No elements with class .selected should exist');
                }
            },

            dialog: {

                getDialog: function(attribute) {
                    return casper.evaluate(function(attribute) {
                        if (attribute) {
                            return $('#modal_features').attr(attribute);
                        }
                        return $('#modal_features');
                    }, attribute);
                },

                doesDialogExist: function() {
                    casper.test.assertExists('#modal_features', 'The dialog is correctly loaded in page');
                    casper.test.assertVisible('#modal_features', 'The dialog is correctly visible in page');
                },

                doesSummaryExist: function() {
                    casper.test.assertExists('#summary', 'The summary element is correctly loaded in page');
                    casper.test.assertVisible('#summary', 'The summary element is correctly visible in page');
                },

                labelMatchesForm: function() {
                    casper.test.assert(casper.evaluate(function() {
                        var label = $('.label-modal-value').text();
                        var form = $('.myModal .allograph_form option:selected').text();
                        return label === form;
                    }), 'The window label and the allograph form value should match');
                }
            },

            tests: {
                summaryMatchesCheckboxes: function() {
                    casper.test.assert(casper.evaluate(function() {
                        var checkboxes = $('#modal_features').find('.features_box:checked');
                        var n = 0;
                        var labels = (function() {
                            var _labels = [];
                            checkboxes.each(function() {
                                _labels.push($('label[for="' + $(this).attr('id') + '"]').text());
                            });
                            return _labels;
                        })();
                        var summary_elements = $('#summary').find('.feature_summary');
                        $.each(summary_elements, function() {
                            var value = $.trim($(this).contents().filter(function() {
                                return this.nodeType == 3;
                            })[0].nodeValue);
                            if (labels.indexOf(value) >= 0 && $(this).has('a').length) {
                                n++;
                            }
                        });
                        console.log('Number of checkboxes selected: ' + checkboxes.length);
                        console.log('Number of elements in summary popup: ' + n);
                        return n === checkboxes.length;
                    }), 'Summary labels should match with selected checkboxes');
                }
            }
        };

        return tasks;
    };

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

    var Scenarios = function(AnnotatorTasks) {

        var tasks = new Tasks();
        var tabs = Tabs;

        /*
        - @Scenario6
        - Select any graph
        - Make sure a popup comes out, displaying correct component and features
        - Make sure the checked feature appears into the summary popup on the left side of the popup
        - Check any feature, make sure it appears in the summary popup. Then uncheck it again, and make sure it disappears from the summary popup.
        */

        this.Scenario6 = function() {
            casper.echo('Running Allographs Scenario 6', 'PARAMETER');
            if (Tabs.current() !== '#allographs') {
                Tabs.switch('allographs');
            }
            casper.wait(300);

            // waiting for 300 ms as the animation makes the page still invisible for
            // a brief fraction of time
            //

            var feature = tasks.get.random_vector();
            console.log(feature)
            tasks.do.select(feature, function() {
                tasks.dialog.doesDialogExist();
                tasks.dialog.doesSummaryExist();
                tasks.dialog.labelMatchesForm();
                var graph = AnnotatorTasks.get.getGraphByVectorId(feature);
                var features = AnnotatorTasks.dialog.getSelectedFeatures('allographs');
                AnnotatorTasks.tests.dialogMatchesCache(features, 'allographs', graph);
                AnnotatorTasks.do.describe('allographs');
                tasks.tests.summaryMatchesCheckboxes();
                console.log('Deselecting some checkboxes and repeating test ...');
                AnnotatorTasks.do.describe('allographs', false);
                tasks.tests.summaryMatchesCheckboxes();
            });
        };

        /*
        - Replicate the same actions of the annotator tab
        - Selecting and saving annotations
        - Deselecting all annotations
        - Selecting and removing annotations
     */

        this.Scenario7 = function() {
            casper.echo('Running Allographs Scenario 7', 'PARAMETER');

            var feature = tasks.get.random_vector();
            AnnotatorTasks.do.describeForms('allographs');
            casper.wait(600);
            tasks.do.select(feature, function() {

                casper.then(function() {
                    tasks.do.save(function() {
                        tasks.do.deselect_all_graphs();
                        casper.evaluate(function() {
                            return $('#status').remove();
                        });
                        feature = tasks.get.random_vector();
                        tasks.do.select(feature, function() {
                            tasks.do.delete();
                        });
                    });
                });
            });
        };

        /*
        - Select multiple graphs
        - Try to delete them and make sure they actually disappear form the page
         */

        this.Scenario8 = function() {
            casper.echo('Running Allographs Scenario 8', 'PARAMETER');

            var feature = tasks.get.random_vector();
            var feature2 = tasks.get.random_vector();

            casper.then(function() {
                tasks.do.select(feature);
            });

            casper.then(function() {
                tasks.do.select(feature2);
            });

            casper.then(function() {
                tasks.do.delete(function() {
                    casper.test.assertDoesntExist(x('.annotation_li[@data-annotation="' + feature + '"]'), 'Feature has been deleted');
                    casper.test.assertDoesntExist(x('.annotation_li[@data-annotation="' + feature + '"]'), 'Feature 2 has been deleted');
                });
            });
        };

    };

    this.init = function(options) {
        var tasks = new Tasks(options);
        var AnnotatorTasks = new AnnotatorScenario.AnnotatorTest.Tasks(options);

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


exports.AllographsTest = new Scenario();