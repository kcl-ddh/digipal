function add_to_lightbox(button, type, annotations, multiple) {
	var current_basket = JSON.parse(localStorage.getItem('lightbox_basket'));
	var flag, i, j, elements;
	if (multiple) {
		if (current_basket) {
			flag = true;
			for (i = 0; i < annotations.length; i++) {
				for (j = 0; j < current_basket.annotations.length; j++) {
					if (current_basket.annotations[j].graph == annotations[i]) {
						flag = false;
					}
				}
				if (flag) {
					current_basket.annotations.push(annotations[i]);
				}
			}
			current_basket.annotations = current_basket.annotations.filter(function(elem, pos, self) {
				return self.indexOf(elem) == pos;
			});
			console.log(current_basket)

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
			elements = basket_elements.annotations;
		} else {
			graph = annotations;
			elements = basket_elements.images;
		}

		if (basket_elements && elements && elements.length) {
			flag = true;
			for (j = 0; j < elements.length; j++) {
				if (type == 'annotation') {
					if (elements[j] == graph) {
						flag = false;
					}
				} else {
					if (elements[j].id == graph) {
						flag = false;
					}
				}
			}
			if (flag) {
				if (type == 'annotation') {
					elements.push(annotations);
				} else {
					elements.push({
						'id': annotator.image_id
					});
				}
				localStorage.setItem('lightbox_basket', JSON.stringify(basket_elements));
			}

		} else {
			if (type == 'annotation') {
				if (basket_elements.hasOwnProperty('images')) {
					basket_elements.annotations = [];
					basket_elements.annotations.push(selectedFeature);
				} else {
					basket_elements = {};
					basket_elements.annotations = [];
					basket_elements.annotations.push(selectedFeature);
				}

			} else {
				if (basket_elements.hasOwnProperty('annotations')) {
					basket_elements.images = [];
					basket_elements.images.push({
						id: annotator.image_id
					});
				} else {
					basket_elements = {};
					basket_elements.images = [];
					basket_elements.images.push({
						id: annotator.image_id
					});
				}
			}

			localStorage.setItem('lightbox_basket', JSON.stringify(basket_elements));
		}

	}
	var length_basket_elements = function() {
		var n = 0;
		var current_basket = JSON.parse(localStorage.getItem('lightbox_basket'));
		if (current_basket) {
			$.each(current_basket, function() {
				n += this.length;
			});
		}
		return n;
	};

	$('#lightbox_button a').html("Lightbox (" + length_basket_elements() + " images)");

}

function PublicAllograhs() {
	_self = this;

	this.selectedAnnotations = [];

	this.clean_annotations = function(annotation) {
		var annotations = _self.selectedAnnotations;
		var length_annotations = annotations.length;
		for (i = 0; i < length_annotations; i++) {
			if (annotations[i] == annotation) {
				_self.selectedAnnotations.splice(i, 1);
				break;
			}
		}
	};


	this.init = function() {
		var _self = this;
		$('.annotation_li').click(function(event) {
			var annotation_li = $(this);
			var annotation = annotation_li.data('graph');

			if (annotation_li.data('selected')) {
				_self.clean_annotations(annotation);
				annotation_li.data('selected', false);
				annotation_li.removeClass('selected');
			} else {
				annotation_li.data('selected', false).removeClass('selected');
				annotation_li.data('selected', true);
				annotation_li.addClass('selected');
				_self.selectedAnnotations.push(annotation);
			}

		});

		$('.annotation_li a').click(function(event) {
			event.stopPropagation();
		});

		$('.deselect_all').click(function() {
			var key = $(this).data('key');
			var ul = $('ul[data-key="' + key + '"]');
			var checkboxes = ul.find('li');
			_self.selectedAnnotations = [];
			temporary_vectors = [];
			checkboxes.data('selected', false);
			checkboxes.removeClass('selected');
		});

		$('.select_all').click(function() {
			var key = $(this).data('key');
			var ul = $('ul[data-key="' + key + '"]');
			var checkboxes = ul.find('li');
			var annotation;
			for (var i = 0; i < checkboxes.length; i++) {
				_self.selectedAnnotations.push(annotation);
			}
			checkboxes.data('selected', true);
			checkboxes.addClass('selected');
		});

		var to_lightbox = $('.to_lightbox');
		to_lightbox.click(function() {
			add_to_lightbox($(this), 'annotation', _self.selectedAnnotations, true);
		});

	};
}

$(document).ready(function() {
	var publicAllograhs = new PublicAllograhs();
	publicAllograhs.init();
});