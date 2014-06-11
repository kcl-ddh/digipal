function Scenario() {

    var Tasks = function() {
        var tasks = {
            _self: this,
            do :{
                newCollection: function(name) {
                    casper.click('#new_collection');
                    casper.test.assertExists('#new-collection-div', 'The popup to create a collection has to appear');
                    casper.test.assertVisible('#new-collection-div', 'The popup to create a collection should be visible');
                    casper.fillSelectors('#new-collection-div', {
                        "#name_collection": name
                    }, false);
                    console.log('Saving Collection...');
                    casper.click('#save_collection');
                    tasks.tests.collectionExists(name);
                },

                deleteCollection: function(name) {
                    casper.click('#' + name);
                    casper.click('#delete_collection');
                    casper.test.assertExists('#delete-collection-div', 'The popup to delete a collection has to appear');
                    casper.test.assertVisible('#delete-collection-div', 'The popup to delete a collection should be visible');
                    console.log('Deleting Collection...');
                    casper.click('#delete');
                    tasks.tests.collectionDoesntExist(name);
                }
            },

            get: {
                collections: function() {
                    return casper.evaluate(function() {
                        var collections = localStorage.getItem('collections');
                        return JSON.parse(collections);
                    });
                },

                collectionByName: function(name) {
                    var collections = this.collections();
                    var collection;
                    for (var i in collections) {
                        if (i == name) {
                            collection = collections[i];
                        }
                    }

                    return collection;
                }
            },

            tests: {
                collectionExists: function(name) {
                    casper.test.assertTruthy(tasks.get.collectionByName(name), 'The collection ' + name + ' exists');
                },

                collectionDoesntExist: function(name) {
                    casper.test.assertFalsy(tasks.get.collectionByName(name), 'The collection ' + name + ' does not exist');
                },

                selectAll: function() {
                    console.log('Selecting all collections...');
                    var isChecked = casper.evaluate(function() {
                        return $('#check_collections').attr('checked');
                    });
                    if (!isChecked) {
                        casper.click('#check_collections');
                        casper.test.assertExists('.selected-collection', 'All Collections are selected');
                    }
                }
            }

        };
        return tasks;
    };

    this.Tasks = Tasks;

    var Scenarios = function(options) {
        var tasks = new Tasks();

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