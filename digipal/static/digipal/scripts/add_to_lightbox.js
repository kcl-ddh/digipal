/**
 * Add elements to Lightbox function, updates the collection counter in the main menu
   -- Digipal Project --> digipal.eu
 */

// annotation type => group: key in the Collection dictionnary, label: Human readable label
// idattr: name of the data attribute which contains the id of the object to add to the collection.
// idindex: index of the value identifying uniquely the item in the array returned by annotation.py.images_lightbox()
var collection_types = {
    'annotation':       {'group': 'annotations', 'label': 'Graph', 'idattr': 'graph', 'idindex': 1},
    'editorial':        {'group': 'editorial', 'label': 'Editorial Annotation', 'idattr': 'graph', 'idindex': 2},
    'textunit':         {'group': 'textunits', 'label': 'Text Annotation', 'idindex': 1},
    'image':            {'group': 'images', 'label': 'Page', 'idindex': 1},
};
var collection_default_name = 'My Collection';

function update_collection_counter() {
    // basket_elements = collections in the localStorage
    // Create it if not there yet
    var collections = localStorage.getItem('collections');
    if (collections && !$.isEmptyObject(JSON.parse(collections))) {
    } else {
        collections = {};
        collections[collection_default_name] = {id: '1'};
        collections = JSON.stringify(collections);
        localStorage.setItem('collections', collections);
        localStorage.setItem('selectedCollection', '1');
    }
    var basket_elements = JSON.parse(collections);

    // current_collection_id = current_collection.id = ID of selected collection
    var current_collection = {
        "id": localStorage.getItem('selectedCollection')
    };

    // take the ID of any collection if not found (and set it in LS)
    if (!current_collection.id) {
        $.each(basket_elements, function(index, value) {
            current_collection.id = value.id;
        });
        localStorage.setItem('selectedCollection', current_collection.id);
    }

    var current_collection_id = current_collection.id;

    // Find a collection in the LS with ID = current_collection_id
    // then set current_collection.name & .id
    var children = 0;
    for (var col in basket_elements) {
        children++;
        current_collection.name = col;
        if (basket_elements[col].id == current_collection_id) {
            break;
        }
        current_collection.id = basket_elements[col].id;
    }

    // basket_element = primary nav element for the link to the collection page
    // Sets basket_ement.id = 'collection_link'
    // CONDITION: the hyperlink has 'collection' in its href
    var basket_element = $('#collection_link');
    var menu_links = $('.navLink[href]');
    for (var ind = 0; ind < menu_links.length; ind++) {
        //if ($.trim(menu_links[ind].innerHTML) == 'Collection') {
        if (menu_links[ind].href.search(/\bcollection\b/) > -1) {
            basket_element = $(menu_links[ind]);
            basket_element.attr('id', 'collection_link');
            break;
        }
    }

    // Update the label and link of the collection link in the primary nav
    var items_count = 0;

    $.each(collection_types, function(k, v) {
        items_count += (basket_elements[current_collection.name][v.group] || []).length;
    });

    var link_label = current_collection.name;

    if (link_label.length > 20) {
        link_label = link_label.substr(0, 17) + '...';
    }

    basket_element.html(link_label + " (" + items_count + " <i class = 'fa fa-picture-o'></i> )");
    basket_element.attr('href', '/digipal/collection/' + current_collection.name.replace(/\s+/gi, ''));
    basket_element.attr('title', current_collection.name);
}

function add_to_lightbox(button, type, annotations, multiple) {
    var selectedCollection = localStorage.getItem('selectedCollection');
    var collections = JSON.parse(localStorage.getItem('collections'));
    var collection_name;
    var collection_id;

    // find the collection by its id
    $.each(collections, function(index, value) {
        if (value.id == selectedCollection) {
            current_basket = value;
            collection_name = index;
            collection_id = value.id;
        }
    });

    // no collectionid sellected, select the last one
    if (!selectedCollection) {
        selectedCollection = {};
        $.each(collections, function(index, value) {
            current_basket = value;
            collection_name = index;
            selectedCollection.id = value.id;
        });
        localStorage.setItem('selectedCollection', selectedCollection.id);
    }

    if (annotations === null) {
        notify('Error (no annotations). Try again', 'danger');
        return false;
    }

    var flag, i, j, elements, image_id;
    if (multiple) {
        if (current_basket && current_basket.annotations) {
            for (i = 0; i < annotations.length; i++) {
                flag = true;
                for (j = 0; j < current_basket.annotations.length; j++) {
                    if (!annotations[i]) {
                        notify('Annotation has not been saved yet. Otherwise, refresh the layer', 'danger');
                        return false;
                    }
                    if (current_basket.annotations[j] == annotations[i]) {
                        flag = false;
                    }
                }
                if (flag) {
                    current_basket.annotations.push(parseInt(annotations[i], 10));
                    notify('Graph added to Collection', 'success');
                } else {
                    notify('Annotation has already been added to Collection', 'danger');
                }
            }

        } else {
            current_basket = {};
            current_basket.annotations = [];
            for (i = 0; i < annotations.length; i++) {
                current_basket.annotations.push(parseInt(annotations[i], 10));
            }
        }
        collections[collection_name].annotations = current_basket.annotations;
        localStorage.setItem('collections', JSON.stringify(collections));
        if (annotations.length > 1) {
            notify('Annotations added to Collection', 'success');
        } else {
            notify('Graph added to Collection', 'success');
        }
    } else {
        var graph = annotations;

        var type_info = collection_types[type];
        if (!type_info) {
            notify('Invalid collection item type (' + type + ')', 'danger');
            return false;
        }

        var group_name = type_info.group;

        if (type == 'annotation') {
            if (typeof graph == 'undefined' || !graph) {
                notify('Annotation has not been saved yet', 'danger');
                return false;
            }
        }

        if (current_basket[group_name] === undefined) {
            current_basket[group_name] = [];
        }
        elements = current_basket[group_name];

        if (1 || (current_basket && elements && elements.length)) {

            if (elements.indexOf(graph) < 0) {
                if (type == 'image') {
                    image_id = graph;
                    elements.push(parseInt(image_id, 10));
                } else {
                    if (annotations == 'undefined' || !annotations) {
                        notify('Annotation has not been saved yet', 'danger');
                        return false;
                    }
                    elements.push(annotations);
                }
                notify(type_info.label+' added to Collection', 'success');
            } else {
                notify(type_info.label+' has already been added to Collection', 'danger');
            }

        } else {
            // GN: 28/04/2016: Don't see why we need this branch at all???

            if (type == 'annotation' || type == 'editorial') {
                if (type == 'annotation') {
                    type = 'annotations';
                }
                if (current_basket.hasOwnProperty(type)) {
                    current_basket[type].push(annotations);
                } else {
                    current_basket = {};
                    current_basket[type] = [];
                    current_basket[type].push(annotations);
                    current_basket.id = collection_id;
                    collections[collection_name] = current_basket;
                }
                notify('Graph added to Collection', 'success');
            } else if (type == 'image') {
                image_id = graph;
                if (current_basket.hasOwnProperty('annotations')) {
                    current_basket.images = [];
                    current_basket.images.push(parseInt(image_id, 10));
                } else {
                    current_basket = {};
                    current_basket.images = [];
                    current_basket.images.push(parseInt(image_id, 10));
                    current_basket.id = collection_id;
                    collections[collection_name] = current_basket;
                }
                notify('Image added to Collection', 'success');
            }
        }
        localStorage.setItem('collections', JSON.stringify(collections));
    }

    update_collection_counter();
    return true;
}

function notify(msg, status) {

    var running = running || true;
    var current_collection_name = (function() {
        var current_collection_id = localStorage.getItem('selectedCollection');
        var collections = JSON.parse(localStorage.getItem('collections'));
        var collection_name;
        for (var i in collections) {
            if (collections[i].id == current_collection_id) {
                collection_name = i;
                break;
            }
        }
        return collection_name;
    })();

    if (running) {
        clearInterval(timeout);
        $('#status').remove();
    }

    var status_element = $('#status');

    if (!status_element.length) {
        status_element = $('<div id="status">');
        $('body').append(status_element.hide());
    }

    status_element.css('z-index', 5000);
    status_class = status ? ' alert-' + status : '';
    status_element.attr('class', 'alert' + status_class);

    if (status == 'success') {
        status_element.html("<a style='color:#468847;' href='/digipal/collection/" + current_collection_name + "'>" + msg + "</a>").fadeIn();
    } else {
        status_element.html(msg).fadeIn();
    }

    var timeout =
        setTimeout(function() {
            status_element.fadeOut();
            running = false;
        }, 5000);
}

$(document).ready(function() {
    update_collection_counter();
    $(window).bind('storage', function(e) {
        update_collection_counter();
    });
});
