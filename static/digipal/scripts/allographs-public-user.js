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