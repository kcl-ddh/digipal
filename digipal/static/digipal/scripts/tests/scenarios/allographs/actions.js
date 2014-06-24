var Actions = function(options) {

    this.name = 'AllographsTasks';

    this.actions = {
        _self: this,

        get: {
            random_vector: function() {
                return casper.evaluate(function() {
                    var annotations = $('.annotation_li');
                    var random = Math.round(Math.random() * annotations.length);
                    return $(annotations[random]).data('graph');
                });
            }
        },

        do :{

            select: function(feature_id, callback) {

                casper.click('.annotation_li[data-graph="' + feature_id + '"]');

                casper.then(function() {
                    casper.waitForSelector('.selected', function() {
                        casper.test.assertExists('.selected', 'Element is correctly selected. Class .selected exists.');
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
                        var error = casper.evaluate(function() {
                            return $('#status').text();
                        });
                        casper.echo('Error:' + error, 'ERROR');
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