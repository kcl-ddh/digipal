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

    for (var i = 0; i < 3; i++)
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
    var re = /^\w*$/;
    var collections = JSON.parse(localStorage.getItem('collections'));
    var collection_name = collection['name'];
    var collection_name_trimmed = collection_name.replace(' ', '');
    if (collection_name && re.test(collection_name_trimmed)) {
        if (collections) {
            if (collections[collection_name]) {
                var new_re = /^[\w]*([0-9])$/;
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
}