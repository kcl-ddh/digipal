/**
 * Add elements to Lightbox function, updates the collection counter in the main menu
   -- Digipal Project --> digipal.eu
 */

function length_basket_elements(elements) {
	var n = 0;
	if (elements) {
		$.each(elements, function() {
			n += this.length;
		});
	}
	return n;
}

function update_collection_counter() {

	var basket;
	if (localStorage.getItem('lightbox_basket')) {
		basket = localStorage.getItem('lightbox_basket');
	} else {
		return false;
	}

	var basket_elements = JSON.parse(basket);
	var menu_links = $('.navLink');
	var basket_element;

	for (var ind = 0; ind < menu_links.length; ind++) {
		if ($.trim(menu_links[ind].innerHTML) == 'Collection') {
			basket_element = $(menu_links[ind]);
			basket_element.attr('id', 'collection_link');
		}
	}

	if (!basket_element) {
		basket_element = $('#collection_link');
	}

	var length_basket = length_basket_elements(basket_elements);
	basket_element.html("Collection (" + length_basket + ")");

}

function add_to_lightbox(button, type, annotations, multiple) {
	console.log(annotations);
	var current_basket = JSON.parse(localStorage.getItem('lightbox_basket'));
	if (!current_basket) {
		current_basket = {};
	}
	var flag, i, j, elements, image_id;
	if (multiple) {
		if (current_basket && current_basket.annotations) {
			for (i = 0; i < annotations.length; i++) {
				flag = true;
				for (j = 0; j < current_basket.annotations.length; j++) {
					//console.log(current_basket.annotations[j].graph + " == " + annotations[i].graph)
					if (!annotations[i]) {
						notify('Annotation not saved yet, otherwise refresh the layer', 'danger');
						return false;
					}
					if (current_basket.annotations[j].graph == annotations[i].graph) {
						flag = false;
					}
				}
				if (flag) {
					current_basket.annotations.push(annotations[i]);
				} else {
					//notify('Image already in the basket', 'danger');
					continue;
				}
			}

		} else {
			current_basket = {};
			current_basket.annotations = [];
			for (i = 0; i < annotations.length; i++) {
				current_basket.annotations.push(annotations[i]);
			}
		}
		localStorage.setItem('lightbox_basket', JSON.stringify(current_basket));
	} else {
		var graph;
		if (type == 'annotation') {
			graph = button.data('graph');
			if (typeof graph == 'undefined' || !graph) {
				notify('Annotation not saved yet', 'danger');
				return false;
			}
			if (current_basket.annotations === undefined) {
				current_basket.annotations = [];
			}
			elements = current_basket.annotations;
		} else {
			graph = annotations;
			if (current_basket.images === undefined) {
				current_basket.images = [];
			}
			elements = current_basket.images;
		}

		if (current_basket && elements && elements.length) {
			for (j = 0; j < elements.length; j++) {
				flag = true;

				if (type == 'annotation') {
					var el;

					if (elements[j].hasOwnProperty('graph')) {
						el = elements[j].graph;
					} else {
						el = elements[j];
					}

					if (el == graph) {
						flag = false;
					}

				} else {
					if (elements[j].id == graph) {
						flag = false;
						break;
					}
				}
			}
			if (flag) {
				if (type == 'annotation') {
					if (annotations == 'undefined' || !annotations) {
						notify('Annotation not saved yet', 'danger');
						return false;
					}
					elements.push(annotations);
				} else {
					if (typeof annotator != 'undefined') {
						image_id = annotator.image_id;
					} else {
						image_id = graph;
					}
					elements.push({
						'id': image_id
					});
				}
			} else {
				notify('Image already collected', 'danger');
				return false;
			}

			localStorage.setItem('lightbox_basket', JSON.stringify(current_basket));

		} else {
			if (type == 'annotation') {
				if (current_basket.hasOwnProperty('images')) {
					current_basket.annotations = [];
					current_basket.annotations.push(annotations);
				} else {
					current_basket = {};
					current_basket.annotations = [];
					current_basket.annotations.push(annotations);
				}

			} else {

				if (typeof annotator != 'undefined') {
					image_id = annotator.image_id;
				} else {
					image_id = graph;
				}

				if (current_basket.hasOwnProperty('annotations')) {
					current_basket.images = [];
					current_basket.images.push({
						id: image_id
					});
				} else {
					current_basket = {};
					current_basket.images = [];
					current_basket.images.push({
						id: image_id
					});
				}
			}
			localStorage.setItem('lightbox_basket', JSON.stringify(current_basket));
		}
	}

	update_collection_counter();
	notify('Image added to collection!', 'success');
	return true;
}

function notify(msg, status) {

	var running = running || true;

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
		status_element.html("<a style='color:#468847;' href='/digipal/collection'>" + msg + "</a>").fadeIn();
	} else {
		status_element.html(msg).fadeIn();
	}

	var timeout =
		setTimeout(function() {
			status_element.fadeOut();
			running = false;
		}, 5000);
}

(function() {
	update_collection_counter();
})();