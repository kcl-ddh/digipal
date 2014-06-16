function Scenario() {

    this.Actions = require('actions.js').Actions;

    var Scenarios = function(options) {
        var tasks = new Actions();

        /*
        - Create a New Collection and make sure it exists
         */
        this.Scenario1 = function() {
            casper.echo('Running Collection Scenario 1', 'PARAMETER');
            tasks.do.newCollection('MyCollection');
        };


        /*
        - Delete a Collection and make sure it does not exist
         */
        this.Scenario2 = function() {
            casper.echo('Running Collection Scenario 2', 'PARAMETER');
            tasks.do.deleteCollection('MyCollection');
        };

        /*
        - Click on a collection, rename it, and make sure it exists (wih the new name)
         */
        this.Scenario3 = function() {
            casper.echo('Running Collection Scenario 3', 'PARAMETER');
            var name = "New Collection name";
            casper.click('.collection img');

            casper.then(function() {
                casper.wait(1000, function() {

                    casper.evaluate(function() {
                        $('.collection-title').text('');
                    });

                    casper.click('.collection-title');

                    this.sendKeys('.collection-title', name);
                    this.sendKeys('.collection-title', casper.page.event.key.Enter, {
                        keepFocus: false
                    });

                    tasks.tests.collectionExists(name);
                });
            });
        };

        /*
        - Create a new Collection, then, delete a collection from its page, wait for redirect and make sure it does not exist
         */
        this.Scenario4 = function() {
            casper.echo('Running Collection Scenario 4', 'PARAMETER');
            casper.thenOpen(options.page + '/digipal/collection', function() {
                var name = 'Just Another Collection';
                tasks.do.newCollection(name);
                casper.click('span[data-href="' + name.replace(/\s/gi, '') + '"] img');
                casper.then(function() {
                    casper.wait(1000, function() {
                        casper.click('#delete-collection');
                        casper.click('#delete');
                        casper.then(function() {
                            casper.wait(1000, function() {
                                tasks.tests.collectionDoesntExist(name);
                            });
                        });
                    });
                });
            });
        };

        this.Scenario5 = function() {
            casper.echo('Running Collection Scenario 5', 'PARAMETER');
            tasks.tests.selectAll();
        };
    };

    this.init = function(options) {
        var page = options.page + '/digipal/collection';
        casper.thenOpen(page, function() {
            var scenarios = new Scenarios(options);
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



exports.CollectionsScenario = new Scenario();