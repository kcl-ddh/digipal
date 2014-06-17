var Actions = function(options) {

    var self = this;

    this.name = 'CollectionsTasks';

    this.actions = {
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
                self.actions.tests.collectionExists(name);
            },

            deleteCollection: function(name) {
                casper.click('#' + name);
                casper.click('#delete_collection');
                casper.test.assertExists('#delete-collection-div', 'The popup to delete a collection has to appear');
                casper.test.assertVisible('#delete-collection-div', 'The popup to delete a collection should be visible');
                console.log('Deleting Collection...');
                casper.click('#delete');
                self.actions.tests.collectionDoesntExist(name);
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
                casper.test.assertTruthy(self.actions.get.collectionByName(name), 'The collection ' + name + ' exists');
            },

            collectionDoesntExist: function(name) {
                casper.test.assertFalsy(self.actions.get.collectionByName(name), 'The collection ' + name + ' does not exist');
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

};

exports.Actions = function(options) {
    return new Actions(options);
};