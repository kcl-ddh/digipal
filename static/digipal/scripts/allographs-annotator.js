annotator.url_allographs = true;
annotator.url_annotations = '../annotations';

if (annotator.hands_page == "True") {
	annotator.url_annotations = '/digipal/page/61/annotations/';
}
var request = $.getJSON(annotator.url_annotations, function(data) {
	annotator.annotations = data;
});

var chained = request.then(function(data) {

	$('#id_allograph').change(function() {
		updateFeatureSelect();
	});

	var format = annotator.format;
	var layer = annotator.vectorLayer;
	var url_vectors = '../vectors/';
	if (annotator.hands_page == "True") {
		url_vectors = '/digipal/page/61/vectors/';
	}
	var features_request = $.getJSON(url_vectors);

	features_request.then(function(data) {
		var features = [];
		var annotations = annotator.annotations;
		for (var j in data) {
			var f = format.read(data[j])[0];
			f.id = j;
			for (var i in annotations) {
				var allograph = annotations[i]['feature'];
				var graph = annotations[i]['graph'];
				if (f.id == annotations[i]['vector_id']) {
					f.feature = allograph;
					f.graph = graph;
				}
			}
			features.push(f);
		}
		// adds all the vectors to the vector layer
		layer.addFeatures(features); // zooms to the max extent of the map area
		var vectors = annotator.vectorLayer.features;

		var summary_shown = true;
		$('#show_summary').click(function() {
			if (summary_shown) {
				$("#summary").animate({
					'right': 0,
					'opacity': 0
				}, 350);
				summary_shown = false;
				$(this).addClass('active');
			} else {
				$("#summary").animate({
					'right': "34%",
					'opacity': 1
				}, 350);
				summary_shown = true;
				$(this).removeClass('active');
			}
		});

		modal = false;
		current_feature = false;
		$("#modal_features").draggable();
		selectedAnnotations = {
			'allograph': null,
			'annotations': []
		};

		function clean_annotations(annotation) {
			var annotations = selectedAnnotations.annotations;
			for (i = 0; i < annotations.length; i++) {
				if (annotations[i].id == annotation.id) {
					annotations.splice(i, 1);
					i--;
					break;
				}
			}
		}

		$('.annotation_li').click(function(event) {
			var annotation = getFeatureById($(this).data('annotation'));
			if (event.target.type != 'checkbox') {
				if (selectedAnnotations.allograph !== null && selectedAnnotations.allograph != annotation.feature) {
					selectedAnnotations.allograph = null;
					selectedAnnotations.annotations = [];
					$('.annotation_li').removeClass('selected');
					$('.annotation_li').data('selected', false);
				}
				if ($(this).data('selected')) {
					clean_annotations(annotation);
					$(this).data('selected', false);
					$(this).removeClass('selected');
					$(this).find('input').attr('checked', false);
				} else {
					selectedAnnotations.annotations = [];
					$('.annotation_li').data('selected', false).removeClass('selected');
					$('.annotation_li').find('input').attr('checked', false);
					selectedAnnotations.allograph = annotation.feature;
					selectedAnnotations.annotations.push(annotation);
					$(this).data('selected', true);
					$(this).addClass('selected');
					$(this).find('input').attr('checked', true);
					modal = true;
				}
			} else {
				if (selectedAnnotations.allograph !== null && selectedAnnotations.allograph != annotation.feature) {
					selectedAnnotations.allograph = null;
					selectedAnnotations.annotations = [];
					$('.annotation_li').removeClass('selected');
					$('.annotation_li').data('selected', false);
				}
				if ($(this).is(':checked')) {
					clean_annotations(annotation);
					$(this).data('selected', false);
					$(this).removeClass('selected');
				} else {
					selectedAnnotations.allograph = annotation.feature;
					selectedAnnotations.annotations.push(annotation);
					$(this).data('selected', true);
					$(this).addClass('selected');
					modal = true;
				}
			}
			main();
		});


		function main() {
			if (modal) {
				if (selectedAnnotations.annotations.length > 1) {
					$('.myModalLabel .label-modal-value').html(annotation.feature + " (" + selectedAnnotations.annotations.length + " selected)");
				} else {
					$('.myModalLabel .label-modal-value').html(annotation.feature);
				}
			}

			modal = true;
			$('#save').click(function() {
				var features = annotator.vectorLayer.features;
				selected_features = [];
				for (var i = 0; i < features.length; i++) {
					for (var j = 0; j < selectedAnnotations.annotations.length; j++) {
						if (features[i].graph == selectedAnnotations.annotations[j].graph) {
							selected_features.push(features[i]);
						}
					}
				}
				for (i = 0; i < selected_features.length; i++) {
					annotator.selectedFeature = selected_features[i];
					annotator.saveAnnotation();
				}
			});

			$('#delete').click(function() {
				var features = annotator.vectorLayer.features;
				selected_features = [];
				for (var i = 0; i < features.length; i++) {
					for (var j = 0; j < selectedAnnotations.annotations.length; j++) {
						if (features[i].graph == selectedAnnotations.annotations[j].graph) {
							selected_features.push(features[i]);
						}
					}
				}
				var j = 0;
				for (var i = 0; i < selected_features.length; i++) {
					annotator.deleteAnnotation(annotator.vectorLayer, selected_features[i]);
				}
			});


			if (!selectedAnnotations.annotations.length) {
				$("#modal_features").fadeOut();
				return false;
			} else {
				$("#modal_features").fadeIn();
			}
			if (annotation) {
				if (selectedAnnotations.annotations.length > 1) {
					$('.myModalLabel .label-modal-value').html(annotation.feature + " (" + selectedAnnotations.annotations.length + " selected)");
				} else {
					$('.myModalLabel .label-modal-value').html(annotation.feature);
				}
				$('#hidden_hand').val(annotation.hidden_hand);
				$('#id_hand').val(annotation.hidden_hand);
				$('#id_allograph').val(getKeyFromObjField(annotation, 'hidden_allograph'));
				$('#hidden_allograph').val(getKeyFromObjField(annotation, 'hidden_allograph'));
				$('#id_display_note').val(annotation.display_note);
				$('#id_internal_note').val(annotation.internal_note);
				$('select').trigger('liszt:updated');
				if (annotator.hands_page == "True") {
					url = '/digipal/graph/' + annotation.graph + '/features/';
				}
				var url = '../graph/' + annotation.graph + '/features/';
				var features_owned = $.ajax({
					url: url,
					dataType: 'json',
					cache: false,
					type: 'GET',
					async: false
				});


				features_owned.done(function(f) {
					array_features_owned = [];
					for (var i = 0; i < f.length; i++) {
						for (var j = 0; j < f[i].feature.length; j++) {
							s = f[i].name;
							s += ':' + f[i].feature[j];
							array_features_owned.push(s);
						}
						s = '';
					}
				});

				$('#id_display_note').parent('p').hide();
				$('#id_internal_note').parent('p').hide();
				var url_features = "../graph/" + annotation.graph;
				if (annotator.hands_page == "True") {
					var url_features = "/digipal/page/61/graph/" + annotation.graph;
				}

				var request = $.getJSON(url_features);

				var features = annotator.vectorLayer.features;
				request.done(function(data) {
					var url = '../allograph/' + data.id + '/features/';
					if (annotator.hands_page == "True") {
						var url = "/digipal/page/61/allograph/" + data.id + '/features/';
					}
					var allographs = $.getJSON(url);
					var s = "<div id='box_features_container'>";
					var string_summary = '';
					allographs.done(function(data) {
						$.each(data, function(idx) {
							component = data[idx].name;
							component_id = data[idx].id;
							string_summary += "<span style='display:block;font-weight:bold;border-bottom:1px solid #ccc;'>" + data[idx].name + "</span>";
							var features = data[idx].features;
							s += "<p class='component_labels' data-id='component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component icon-arrow-down'></span></span></b>";
							s += "<div class='checkboxes_div pull-right' style='margin: 1%;'><button class='check_all btn btn-small'>All</button> <button class='btn btn-small uncheck_all'>Clear</button></div><div>";

							s += "<div id='component_" + component_id + "' data-hidden='true' class='feature_containers'>";
							$.each(features, function(idx) {
								var value = component_id + '::' + features[idx].id;
								var names = component + ':' + features[idx].name;

								if (array_features_owned.indexOf(names) >= 0) {
									string_summary += "<span style='display:block;'>" + features[idx].name; + "</span>";
									s += "<p><input checked = 'checked' type='checkbox' value='" + value + "' class='features_box' id='" + features[idx].id + "' data-feature = '" + features[idx].id + "' /> <label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + features[idx].id + "'>" + features[idx].name + "</label>";
								} else {
									s += "<p><input id='" + features[idx].id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "'/> <label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + features[idx].id + "'>" + features[idx].name + "</label>";
								}
							});
							s += "</p></div>";
						});
						s += "</div>";
						$("#summary").html(string_summary);
						$('#features_container').html(s);
						$('.check_all').click(function() {
							var checkboxes = $(this).parent().next().children().find('input[type=checkbox]');
							checkboxes.attr('checked', true);
						});
						$('.uncheck_all').click(function() {
							var checkboxes = $(this).parent().next().children().find('input[type=checkbox]');
							checkboxes.attr('checked', false);
						});
						$('.myModal select').chosen();

						$('.component_labels').click(function() {
							var div = $("#" + $(this).data('id'));
							if (div.data('hidden') === false) {
								$(this).next('.checkboxes_div').hide();
								div.slideUp().data('hidden', true);
								$(this).find('.arrow_component').removeClass('icon-arrow-up').addClass('icon-arrow-down');

							} else {
								div.slideDown().data('hidden', false);
								$(this).next('.checkboxes_div').show();
								$(this).find('.arrow_component').removeClass('icon-arrow-down').addClass('icon-arrow-up');
							}
						});

						//updateFeatureSelect(annotation.features, feature);
						$('#modal_features .close').click(function() {
							$("#modal_features").fadeOut();
							$('#status').html('-');
							modal = false;
							selectedAnnotations.allograph = null;
							selectedAnnotations.annotations = [];
							$('.annotation_li').removeClass('selected');
						});

					});
					$('select[id!=id_feature]').chosen();

				});

			}

		}
	});
});