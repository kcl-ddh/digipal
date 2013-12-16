/**
 * Add elements to Lightbox function
   -- Digipal Project --> digipal.eu
 */

function add_to_lightbox(button, type, annotations, multiple) {
	var current_basket = JSON.parse(localStorage.getItem('lightbox_basket'));
	if (!current_basket) {
		current_basket = {};
	}
	var flag, i, j, elements;
	if (multiple) {
		if (current_basket) {
			for (i = 0; i < annotations.length; i++) {
				flag = true;
				for (j = 0; j < current_basket.annotations.length; j++) {
					//console.log(current_basket.annotations[j].graph + " == " + annotations[i].graph)
					if (current_basket.annotations[j].graph == annotations[i].graph) {
						flag = false;
					}
				}
				console.log(flag)
				if (flag) {
					console.log(annotations[i]);
					current_basket.annotations.push(annotations[i]);
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
					if (elements[j].graph == graph) {
						flag = false;
					}
				} else {
					if (elements[j].id == graph) {
						flag = false;
					}
				}
			}
			if (flag) {
				var image_id
				if (type == 'annotation') {
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
			}

			localStorage.setItem('lightbox_basket', JSON.stringify(current_basket));

		} else {
			console.log(annotations);
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

				var image_id;

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
			console.log(current_basket);
			localStorage.setItem('lightbox_basket', JSON.stringify(current_basket));
		}

	}

	var length_basket = length_basket_elements(JSON.parse(localStorage.getItem('lightbox_basket')));
	var basket_element = $('#lightbox_button a');
	if (length_basket == 1) {
		basket_element.html("Lightbox (" + length_basket + " image)");
	} else {
		basket_element.html("Lightbox (" + length_basket + " images)");
	}

}