function notify(msg, status) {
    var status_element = $('#status');
    if (!status_element.length) {
        status_element = $('<div id="status">');
        $('body').append(status_element.hide());
    }
    status_class = status ? ' alert-' + status : '';
    status_element.attr('class', 'alert' + status_class);
    status_element.html(msg).fadeIn();

    setTimeout(function() {
        status_element.fadeOut();
    }, 5000);
}

function increment_last(v) {
    return v.replace(/[0-9]+(?!.*[0-9])/, parseInt(v.match(/[0-9]+(?!.*[0-9])/), 10) + 1);
}


function uniqueid() {
    var text = "";
    var possible = "0123456789";

    for (var i = 0; i < 4; i++)
        text += possible.charAt(Math.floor(Math.random() * possible.length));

    return text;
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function length_basket_elements(elements) {
    var n = 0;
    if (elements) {
        $.each(elements, function() {
            n += this.length;
        });
    }
    return n;
}

function getParameter(paramName) {
    var searchString = window.location.search.substring(1),
        i, val, params = searchString.split("&");
    var parameters = [];
    for (i = 0; i < params.length; i++) {
        val = params[i].split("=");
        if (val[0] == paramName) {
            parameters.push(unescape(val[1]));
        }
    }
    return parameters;
}

function save_collection(collection) {
    var id = uniqueid();
    var collections = JSON.parse(localStorage.getItem('collections'));
    var collection_name = collection['name'];
    var collection_name_trimmed = collection_name.replace(' ', '');
    if (collection_name) {
        if (collections) {
            if (collections[collection_name]) {
                var new_re = /^[.]*([0-9])$/;
                if (!new_re.test(collection_name)) {
                    collection_name += '0';
                }
                while (collections[collection_name]) {
                    collection_name = increment_last(collection_name);
                }
            }
            collections[collection_name] = collection;
        } else {
            collections = {};
            collections[collection_name] = collection;
        }
        collections[collection_name]['id'] = id;
        localStorage.setItem("collections", JSON.stringify(collections));
    }
    return id;
}

function delete_collections(selectedCollections, delete_function, collection_page) {
    var collections = JSON.parse(localStorage.getItem('collections'));
    var current_collection = localStorage.getItem('selectedCollection');
    var selectedCollection;

    $.each(collections, function(index, value) {
        if (this.id == current_collection) {
            selectedCollection = index;
            return false;
        }
    });

    var background_div = $('<div class="dialog-background">');
    var window_save_collection = $('<div>');
    var s = '';

    window_save_collection.attr('class', 'loading-div').attr('id', 'delete-collection-div');

    if (!collection_page) {

        if (selectedCollections.length == 1) {
            s += '<h3>Delete Collection?</h3>';
            s += '<p>You are about to delete 1 collection</p>';
        } else {
            s += '<h3>Delete Collections?</h3>';
            s += '<p>You are about to delete ' + selectedCollections.length + ' collections</p>';
        }
    } else {
        s += '<h3>Delete ' + selectedCollection + '?</h3>';
        s += '<p>You are about to delete the collection <i>' + selectedCollection + '</i></p>';
    }

    s += '<div style="margin-top:2em"><input type = "button" class="btn btn-sm btn-success" id="delete" type="button" value="Delete" /> ';
    s += '<input type = "button" class="btn btn-sm btn-danger" id="close_window_collections" value="Cancel" /></div></div>';

    window_save_collection.html(s);

    if (!$('#delete-collection-div').length) {
        background_div.html(window_save_collection);
        $('body').append(background_div);
    }

    $('#close_window_collections').unbind().click(function(event) {
        background_div.fadeOut().remove();
        event.stopPropagation();
    });

    $('#delete').unbind().click(function(event) {
        if (collection_page) {
            _delete(selectedCollections);
        } else {
            delete_function();
        }
        update_collection_counter();
        event.stopPropagation();
        event.preventDefault();
        if (collection_page) {
            location.href = '../';
        }
    });


}

function _delete(selectedCollections) {
    var collections = JSON.parse(localStorage.getItem('collections'));
    var container_basket = $("#container_basket");
    for (var i = 0; i < selectedCollections.length; i++) {
        $.each(collections, function(index, value) {
            if (value.id == selectedCollections[i]) {
                delete collections[index];
                $('#' + value.id).fadeOut().remove();
            }
        });
    }

    localStorage.setItem('collections', JSON.stringify(collections));
    localStorage.removeItem('selectedCollection');
    $('#delete-collection-div').parent().fadeOut().remove();

    if ($.isEmptyObject(collections)) {
        var s = '<div class="container alert alert-warning">No collections</div>';
        container_basket.append(s);
    }

}

function share(selectedCollections) {
    var b = {},
        i = 0;

    var selectedCollection = selectedCollections[0];
    var collections = JSON.parse(localStorage.getItem('collections'));
    var basket;

    $.each(collections, function(index, value) {
        if (value.id == selectedCollection) {
            basket = this;
            basket['name'] = index;
        }
    });
    var url = window.location.hostname + '/digipal/collection/shared/1/' +
        '?collection=' + encodeURIComponent(JSON.stringify(basket));

    var scriptTwitter = '<script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0];if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src="https://platform.twitter.com/widgets.js";fjs.parentNode.insertBefore(js,fjs);}}(document,"script","twitter-wjs");</script>';
    var div = $('#share_basket_div');
    if (!div.length) {
        div = $('<div class="loading-div" id="share_basket_div">');
        div.html('<h3>Share Collection URL</h3>');
        div.append('<div style="margin-top:2em"><p><a id="basket_url" ><img src="/static/digipal/images/ajax-loader.gif" /></a></p>');
        div.append('<p><button class="btn btn-danger btn-sm">Close Window</button></p></div>');
        $('body').append(div);

        div.find('button').click(function() {
            div.fadeOut();
        });
    } else {
        div.fadeIn();
    }

    dputils.gapi_shorten_url(url, function(short_url) {
        $("#basket_url").replaceWith('<input type="text" value="' + short_url + '" />');
        var linkTwitter = ' <a href="https://twitter.com/share" data-hashtags="digipal" class="twitter-hashtag-button" data-lang="en" data-count="none" data-size="large" data-related="digipal" data-text="' + short_url + '">Tweet</a>';
        if (!$('.twitter-hashtag-button').length) {
            div.find('input').after(linkTwitter + scriptTwitter);
        } else {
            twttr.widgets.load();
        }
    });

}

