/**
 * Add elements to Lightbox function, updates the collection counter in the main menu
   -- Digipal Project --> digipal.eu
 */

var collection_types = {
    'annotation': {'group': 'annotations', 'label': 'Graph'},
    'textunit': {'group': 'textunits', 'label': 'Text Annotation'},
    'image': {'group': 'images', 'label': 'Page'},
    'editorial': {'group': 'editorial', 'label': 'Editorial Annotation'},
}

function update_collection_counter() {
    var basket_elements;
    var collections;
    if (localStorage.getItem('collections') && !$.isEmptyObject(JSON.parse(localStorage.getItem('collections')))) {
        collections = localStorage.getItem('collections');
        basket_elements = JSON.parse(collections);
    } else {
        collections = {
            'Collection': {
                'id': "1"
            }
        };
        basket_elements = collections;
        localStorage.setItem('collections', JSON.stringify(collections));
        localStorage.setItem('selectedCollection', '1');
    }

    var menu_links = $('.navLink');
    var basket_element;
    var current_collection = {
        "id": localStorage.getItem('selectedCollection')
    };

    if (!current_collection.id) {
        $.each(basket_elements, function(index, value) {
            current_collection.id = value.id;
        });
        localStorage.setItem('selectedCollection', current_collection.id);
    }

    var current_collection_id = current_collection.id;
    var children = 0;
    for (var col in basket_elements) {
        children++;
        if (basket_elements[col].id == current_collection_id) {
            current_collection['name'] = col;
            break;
        } else {
            current_collection['name'] = col;
            current_collection['id'] = basket_elements[col].id;
        }
    }


    for (var ind = 0; ind < menu_links.length; ind++) {
        if ($.trim(menu_links[ind].innerHTML) == 'Collection') {
            basket_element = $(menu_links[ind]);
            basket_element.attr('id', 'collection_link');
        }
    }

    if (!basket_element) {
        basket_element = $('#collection_link');
    }

    var i = 0;

    if (basket_elements[current_collection['name']]['images']) {
        i += basket_elements[current_collection['name']]['images'].length;
    }

    if (basket_elements[current_collection['name']]['annotations']) {
        i += basket_elements[current_collection['name']]['annotations'].length;
    }

    if (basket_elements[current_collection['name']]['editorial']) {
        i += basket_elements[current_collection['name']]['editorial'].length;
    }

    var link_label = current_collection['name'];

    if (link_label.length > 20) {
        link_label = link_label.substr(0, 17) + '...';
    }

    basket_element.html(link_label + " (" + i + " <i class = 'fa fa-picture-o'></i> )");
    basket_element.attr('href', '/digipal/collection/' + current_collection['name'].replace(/\s+/gi, ''));
    basket_element.attr('title', current_collection['name']);
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
        
        type_info = collection_types[type];
        if (!type_info) {
            notify('Invalid item type (' + type + ') for collection.', 'danger');
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
