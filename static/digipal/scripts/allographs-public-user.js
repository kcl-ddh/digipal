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

		var to_lightbox = $('.to_lightbox');

		to_lightbox.click(function() {

			var array = [];
			var annotations = _self.selectedAnnotations;

			for (var j = 0; j < annotations.length; j++) {
				array.push(annotations[j]);
			}

			location.href = 'http://lightbox-dev.dighum.kcl.ac.uk/?annotations=[' +
				array.toString() + ']';
		});

	};
}

$(document).ready(function() {
	var publicAllograhs = new PublicAllograhs();
	publicAllograhs.init();
});