var AnnotatorScenario = require('../annotator/scenario.js');

function Scenario() {

    var Scenarios = function(AnnotatorTasks) {

        var tasks = require('actions.js').Actions;

        /*
        - @Scenario6
        - Select any graph
        - Make sure a popup comes out, displaying correct component and features
        - Make sure the checked feature appears into the summary popup on the left side of the popup
        - Check any feature, make sure it appears in the summary popup. Then uncheck it again, and make sure it disappears from the summary popup.
        */

        this.Scenario6 = function() {
            casper.echo('Running Allographs Scenario 6', 'PARAMETER');
            if (tasks.tab.current() !== '#allographs') {
                tasks.tab.switch('allographs');
            }
            casper.wait(300);

            // waiting for 300 ms as the animation makes the page still invisible for
            // a brief fraction of time
            //

            var feature = tasks.get.random_vector();
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