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

	this.to_annotator = function(annotation_id) {
		if (typeof annotator !== 'undefined') {
			var tab = $('a[data-target="#annotator"]');
			tab.tab('show');
			annotator.selectFeatureByIdAndZoom(annotation_id);
			var select_allograph = $('#panelImageBox');
			var annotation_graph;
			select_allograph.find('.hand_form').val(annotator.selectedFeature.hand);
			for (var i in annotator.annotations) {
				if (annotator.annotations[i].graph == annotator.selectedFeature.graph) {
					annotation_graph = annotator.annotations[i];
					break;
				}
			}
			select_allograph.find('.allograph_form').val(getKeyFromObjField(annotation_graph, 'hidden_allograph'));
			$('select').trigger('liszt:updated');
		}
	};


	this.init = function() {
		var _self = this;
		var annotation_li = $('.annotation_li');

		annotation_li.on('click', function(event) {
			var annotation_li = $(this);
			var panel = annotation_li.closest('.allograph-item');
			var annotation = $(annotation_li).data('graph');

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

			if (_self.selectedAnnotations.length) {
				panel.find('.to_lightbox').attr('disabled', false);
			} else {
				panel.find('.to_lightbox').attr('disabled', true);
			}

		});

		annotation_li.find('a').click(function(event) {
			var id = $(this).parent('.annotation_li').data('annotation');
			_self.to_annotator(id);

			/*
			var panel = $('#panelImageBox');
			$('body').animate({
				scrollLeft: panel.position().left,
				scrollTop: panel.position().top
			});
			*/

			event.stopPropagation();
			event.preventDefault();
		});

		var deselect_all = $('.deselect_all');
		deselect_all.click(function() {
			var key = $(this).data('key');
			var ul = $('.list-allographs[data-key="' + key + '"]');
			var checkboxes = ul.find('.annotation_li');
			var panel = $(this).parent().parent();
			_self.selectedAnnotations = [];
			temporary_vectors = [];
			checkboxes.data('selected', false);
			checkboxes.removeClass('selected');
			panel.find('.to_lightbox').attr('disabled', true);
		});

		var select_all = $('.select_all');
		select_all.click(function() {
			var key = $(this).data('key');
			var ul = $('.list-allographs[data-key="' + key + '"]');
			var checkboxes = ul.find('.annotation_li');
			var panel = $(this).parent().parent();
			var annotation;
			for (var i = 0; i < checkboxes.length; i++) {
				annotation = $(checkboxes[i]).data('graph');
				_self.selectedAnnotations.push(annotation);
			}
			checkboxes.data('selected', true);
			checkboxes.addClass('selected');
			panel.find('.to_lightbox').attr('disabled', false);
		});

		var to_lightbox = $('.to_lightbox');

		to_lightbox.click(function() {
			var graphs = [];
			for (var i = 0; i < _self.selectedAnnotations.length; i++) {
				graphs.push(_self.selectedAnnotations[i]);
			}
			add_to_lightbox($(this), 'annotation', graphs, true);

		});

	};
}

$(document).ready(function() {
	var publicAllograhs = new PublicAllograhs();
	publicAllograhs.init();
});