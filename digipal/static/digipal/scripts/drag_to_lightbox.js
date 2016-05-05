/**
 * Every element that match the css selector 'a.droppable_image'
 * will be detected by the script to be "starrable". The element must have an data-id attribute
 * which contains the ID of the digipal image record to add to the basket, or
 * data graph if this is an annotation
 *
 * Dependency: add_to_lightbox.js

        <span id="dialog-star" data-toggle="tooltip" data-container="body"
            title="Add image to collection" class="glyphicon
            glyphicon-star unstarred|starred" />
 */
/*

 from add_to_lightbox.js:
 add_to_lightbox(element, type, id, multiple)

 */

var Star = function(options) {

    var self = this;

    var defaults = {
        className: '.droppable_image',
        parentName: '.folio-image-wrapper'
    };

    if (options && !$.isEmptyObject(options)) {
        defaults = $.extend(defaults, options);
    }

    var init = function() {
        events();
    };

    var events = function() {
        var elements = $(defaults.className);
        findStarredInPage();
        elements.closest(defaults.parentName).on('mouseenter', function(event) {
            dialog.init($(this).find(defaults.className));
        }).on('mouseleave', function(event) {
            dialog.hide();
        });

        events_image_to_lightbox();
    };

    /*
     * Add add/remove behaviour to the Page star button on the annotator and
     * Image Zoom search results 
    */
    var events_image_to_lightbox = function() {
        var selectedCollection = getCurrentCollection();
        var image_to_lightbox = $("#image_to_lightbox");
        var imageid = image_to_lightbox.data('id');
        
        if (isInCollection(selectedCollection, imageid, 'image')) {
            image_to_lightbox.children().addClass('starred').removeClass('unstarred');
            image_to_lightbox.attr('data-original-title', 'Remove page from collection');
        }

        image_to_lightbox.click(function() {
            if ($(this).children().hasClass('starred')) {
                removeFromCollection(image_to_lightbox, 'image');
                $(this).children().removeClass('starred').addClass('unstarred');
                image_to_lightbox.attr('data-original-title', 'Add page to collection');
            } else {
                add_to_lightbox($(this), 'image', imageid, false);
                $(this).children().removeClass('unstarred').addClass('starred');
                image_to_lightbox.attr('data-original-title', 'Remove page from collection');
            }
            return false;
        }).tooltip();
    }

    var dialog = {

        init: function(image) {
            var _self = this;
            if (!$("#dialog-star").length) {
                _self.element = _self.create(image);
                _self.show(image);
            }
        },

        create: function(image) {
            //var element = $('<span id="dialog-star"></span>');
            var element = null;
            return this.fill(image, element);
        },

        fill: function(image, element) {
            var data = getData(image);
            var star = $('<span id="dialog-star" data-toggle="tooltip" data-container="body" title="Add image to collection" class="glyphicon glyphicon-star star-icon unstarred"></span>');
            var selectedCollection = getCurrentCollection();
            if (isInCollection(selectedCollection, data.id, data.type)) {
                star.addClass('starred').removeClass("unstarred");
                star.attr('title', 'Image added to collection');
            }
            star.tooltip();
            //element.append(star);
            return star;
        },

        show: function(image) {
            var element = this.element;
            image.append(element);
            this.events(element, image);
        },

        hide: function() {
            var element = $("#dialog-star");
            element.fadeOut().remove();
        },

        events: function(element, image) {

            element.on('click', function() {
                if ($(this).hasClass('starred')) {
                    removeFromCollection(image);
                } else {
                    addToCollection(image);
                }
                return false;
            });
        }

    };

    var getDataAttrName = function(image) {
        // returns the name of the data attribute which contains the id
        // of the object to add to the collection.
        return collection_types[image.data('type')].idattr || 'id';
    }

    var getData = function(image) {
        return {
            'type': image.data('type'),
            'id': image.data(getDataAttrName(image))
        };
    };

    var addToCollection = function(image) {
        var data = getData(image);
        if (add_to_lightbox(image, data.type, data.id, false)) {
            dialog.element.addClass('starred').removeClass('unstarred');
            var _type = getDataAttrName(image);
            var element = $("[data-" + _type + "='" + data.id + "']");
            if (typeof element.data('add-star') !== 'undefined' && !element.data('add-star')) {
                return false;
            }
            var star = "<span class='glyphicon glyphicon-star star-icon starred-image'></span>";
            if (element.find('.starred-image').length) return false;
            element.append(star);
        }
    };

    var removeFromCollection = function(image, type) {
        var _self = this;
        var collections = JSON.parse(localStorage.getItem('collections'));
        var collection_id = getCurrentCollection();
        var collection = getCollection(collection_id);
        var data = getData(image);
        data.type += 's';
        for (var i = 0; i < collection[data.type].length; i++) {
            if (collection[data.type][i] == data.id) {
                collection[data.type].splice(i, 1);
                i--;
                notify('Image removed from Collection', 'success');
                break;
            }
        }
        if (dialog.element) {
            dialog.element.addClass('unstarred').removeClass('starred');
        }
        var _type = getDataAttrName(image);
        var element = $("[data-" + _type + "='" + data.id + "']");
        element.find('.starred-image').remove();
        collections[collection.name] = collection;
        localStorage.setItem('collections', JSON.stringify(collections));
        update_collection_counter();
    };

    var getElementsFromCollections = function() {
        var collections = JSON.parse(localStorage.getItem('collections'));
        var collection;
        var arrays = ['images', 'annotations'];
        var allElements = {};
        $.each(collections, function(index, value) {
            for (var i = 0; i < arrays.length; i++) {
                if (value.hasOwnProperty(values[i])) {
                    for (var j = 0; j < value[arrays[i]].length; j++) {
                        allElements[value[arrays[i]][j]] = value.id;
                    }
                }
            }
        });
        return allElements;
    };

    var getCollection = function(collection_id) {
        var collections = JSON.parse(localStorage.getItem('collections'));
        var collection;
        $.each(collections, function(index, value) {
            if (value.id == collection_id) {
                collection = value;
                collection['name'] = index;
                return false;
            }
        });
        return collection;
    };

    var isInCollection = function(collection_id, id, type) {
        var collection = getCollection(collection_id);
        var found = false;
        type += 's';
        if (collection && collection.hasOwnProperty(type)) {
            for (var i = 0; i < collection[type].length; i++) {
                if (collection[type][i] == id) {
                    found = true;
                    break;
                }
            }
        }
        return found;
    };

    var getCurrentCollection = function() {
        return localStorage.getItem('selectedCollection');
    };

    var findStarredInPage = function() {
        var collection_id = getCurrentCollection();
        var graphs = $('.droppable_image[data-graph], .droppable_image[data-id]');
        var star = "<span class='glyphicon glyphicon-star starred-image star-icon'></span>";
        $.each(graphs, function(index, value) {
            value = $(value);
            var id = value.data('id');
            var type = value.data('type') || 'annotation';
            var graphid = value.data('graph');

            if (graphid) {
                // Yeah... I know... type = annotation BUT id of a graph!
                // That's a major cause of confusion everywhere in the code
                // Can't be changed easily because it is now saved in
                // bookmarks and localstorage.
                id = graphid;
            }

            if (isInCollection(collection_id, id, type)) {
                if (typeof value.data('add-star') === 'undefined' || value.data('add-star')) {
                    value.append(star);
                }
            }
        });
    };

    return {
        'init': init,
        "removeFromCollection": removeFromCollection,
        "getCurrentCollection": getCurrentCollection,
        "isInCollection": isInCollection
    };
};

$(document).ready(function() {
    var star = new Star();
    window.collection_star = star;
    star.init();
});
