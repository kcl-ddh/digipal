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
                    tasks.tests.collectionDoesntEsist(name);
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

                collectionDoesntEsist: function(name) {
                    casper.test.assertFalsy(tasks.get.collectionByName(name), 'The collection ' + name + ' does not exist');
                }
            }

        };
        return tasks;
    };

    this.Tasks = Tasks;

    var Scenarios = function() {
        var tasks = new Tasks();

        this.Scenario1 = function() {
            tasks.do.newCollection('MyCollection');
        };

        this.Scenario2 = function() {
            tasks.do.deleteCollection('MyCollection');
        };
    };

    this.init = function(options) {
        var page = options.page + '/digipal/collection';
        casper.thenOpen(page, function() {
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


exports.CollectionsScenario = new Scenario();