// inherits from Annotator
DigipalAnnotator.prototype = new Annotator();

// corrects the contructor pointer because it points to Annotator
DigipalAnnotator.prototype.constructor = DigipalAnnotator;

/**
 * Annotator implementation for DigiPal.
 *
 * @param imageUrl
 *              URL of the image to annotate.
 * @param imageWidth
 *              Width of the image to annotate.
 * @param imageHeight
 *              Height of the image to annotate.
 * @param imageServerUrl
 *              URL of the image on an image server.
 */

function DigipalAnnotator(mediaUrl, imageUrl, imageWidth, imageHeight,
	imageServerUrl, isAdmin) {
	if (imageServerUrl && imageServerUrl != 'None' && imageServerUrl.length) {
		Annotator.call(this, imageServerUrl, imageWidth, imageHeight, true);
	} else {
		Annotator.call(this, imageUrl, imageWidth, imageHeight, false);
	}
	this.annotations = null;
	this.annotating = true;
	this.has_changed = false;
	this.events = false;
	this.url_allographs = false;
	this.unsaved_annotations = [];
	this.isAdmin = isAdmin;
	this.mediaUrl = mediaUrl;
	this.allow_multiple_dialogs = false;
	this.boxes_on_click = false;
	this.deleteFeature.panel_div.title = 'Delete (shift + Backspace)';
	this.transformFeature.panel_div.title = 'Modify (shift + m)';
	this.rectangleFeature.panel_div.title = 'Draw Annotation (shift + d)';
	if (isAdmin !== 'True') {
		this.rectangleFeature.panel_div.title = 'Create Annotation (shift + d)';
	}
	this.selectFeature.panel_div.title = 'Select (shift + g)';
	this.zoomBoxFeature.panel_div.title = 'Zoom (shift + z)';
	this.saveButton.panel_div.title = 'Save (shift + s)';
	this.selectedAnnotations = [];
	this.cacheAnnotations = new AnnotationsCache();
}

/**
 * Function that is called after a feature is selected.
 *
 * @param event
 *              The select event.
 */

DigipalAnnotator.prototype.onFeatureSelect = function(event) {
	var self = this;
	this.selectedFeature = event.feature;

	var group_button = $('.link_graphs');
	if (self.selectedFeature.linked_to && !$.isEmptyObject(self.selectedFeature.linked_to[0]) && allow_multiple()) {
		$.each(self.selectedFeature.linked_to[0], function(index, value) {
			if (value) {
				self.showAnnotation(value);
				self.selectedAnnotations.push(value);
				var msg;

				if (self.selectedAnnotations.length > 1 || !self.selectedAnnotations.length) {
					msg = self.selectedAnnotations.length + ' annotations selected';
				} else {
					msg = self.selectedAnnotations.length + ' annotation selected';
				}

				updateStatus(msg, 'success');

				if (group_button.length && self.selectedAnnotations.length > 1) {
					group_button.removeClass('disabled').attr('disabled', false);
				} else {
					group_button.addClass('disabled').attr('disabled', true);
				}
			}
		});

		if (group_button.length && self.selectedAnnotations.length > 1) {
			group_button.removeClass('disabled').attr('disabled', false);
		} else {
			group_button.addClass('disabled').attr('disabled', true);
		}

	} else if (typeof self.selectedFeature.linked_to != 'undefined' && $.isEmptyObject(self.selectedFeature.linked_to[0]) && allow_multiple()) {

		self.selectedAnnotations.push(self.selectedFeature);
		var msg;

		if (self.selectedAnnotations.length > 1 || !self.selectedAnnotations.length) {
			msg = self.selectedAnnotations.length + ' annotations selected';
		} else {
			msg = self.selectedAnnotations.length + ' annotation selected';
		}

		updateStatus(msg, 'success');
		self.showAnnotation(self.selectedFeature);
		if (self.selectedAnnotations.length < 2) {
			if (group_button.length) {
				group_button.addClass('disabled').attr('disabled', true);
			}
		} else {
			if (group_button.length) {
				group_button.removeClass('disabled').attr('disabled', false);
			}
		}

	} else {
		self.showAnnotation(event.feature);
	}

	restoreFullscreenPositions();
	highlight_vectors();
};

/**
 * Function that is called after a feature is unselected.
 *
 * @param event
 *              The unselect event.
 */
DigipalAnnotator.prototype.onFeatureUnSelect = function(event, is_event) {
	var _self = this;
	var feature;

	if (is_event) {
		feature = event.feature;
	} else {
		feature = event;
	}

	var boxes = $('.dialog_annotations');
	if (allow_multiple()) {
		var max = this.selectedAnnotations.length;
		for (var i = 0; i < max; i++) {
			if (feature.graph == this.selectedAnnotations[i].graph) {
				this.selectedAnnotations.splice(i, 1);
				i--;
				break;
			}
		}

		if (this.selectedAnnotations.length && boxes.length && !annotator.allow_multiple_dialogs) {
			if (!$.isEmptyObject(feature.linked_to[0])) {
				boxes.remove();
			}
		}

		if (!this.selectedAnnotations.length) {
			boxes.remove();
		}

		if (this.selectedAnnotations.length < 2) {
			var group_button = $('.link_graphs');
			group_button.addClass('disabled');
		}

		var msg;

		if (this.selectedAnnotations.length > 1 || !this.selectedAnnotations.length) {
			msg = this.selectedAnnotations.length + ' annotations selected';
		} else {
			msg = this.selectedAnnotations.length + ' annotation selected';
		}

		updateStatus(msg, 'success');
	} else {
		if (!annotator.allow_multiple_dialogs) {
			boxes.remove();
		}
	}

	if (feature.described) {
		feature.style.fillColor = 'green';
		feature.style.strokeColor = 'green';
	} else {
		var color;
		if (feature.state == 'Insert' && $('.number_unsaved_allographs').hasClass('active') && !feature.stored) {
			color = "#fe2deb";
		} else {
			color = '#ee9900';
		}

		feature.style.strokeColor = color;
		feature.style.fillColor = color;

	}

	this.vectorLayer.redraw();

	if (this.selectedAnnotations.length) {
		this.selectedFeature = this.selectedAnnotations[0];
	} else {
		this.selectedFeature = null;
	}

	$(".number_annotated_allographs .number-allographs").html(0);

	restoreFullscreenPositions();

};

DigipalAnnotator.prototype.linkAnnotations = function() {
	var self = this;
	var features = self.selectedAnnotations;
	if (features.length) {
		for (var i = 0; i < features.length; i++) {
			if (!$.isEmptyObject(features[i].linked_to[0]) || typeof features[i].linked_to == 'undefined') {
				features[i].linked_to = [];
			}
			var feature = {};
			for (var j = 0; j < features.length; j++) {
				feature[features[j].id] = features[j];
			}
			features[i].linked_to.push(feature);
		}
	}
	if (annotator.selectedFeature.linked_to.length && !$.isEmptyObject(annotator.selectedFeature.linked_to[0])) {
		var num_linked = 0;
		var elements_linked = [];

		for (var g in annotator.selectedFeature.linked_to[0]) {
			num_linked++;
			elements_linked.push(annotator.selectedFeature.linked_to[0][g]);
		}

		var allograph_label = $('.allograph_label');
		allograph_label.html("Group (<span class='num_linked'>" + num_linked + '</span>) <i title="Show group elements" class="glyphicon glyphicon-list show_group" data-placement="bottom" data-container="body" data-toggle="tooltip" data-hidden="true" />').css('cursor', 'pointer').data('hidden', true);

		allograph_label.unbind().on('click', function() {
			var element = "<div class='elements_linked'>";
			$.each(elements_linked, function() {
				this.feature = this.feature || 'Undefined annotation';
				element += "<p data-id='" + this.id + "'>" + this.feature + "<i title='ungroup' class='pull-right glyphicon glyphicon-remove ungroup' data-id='" + this.id + "' /></p>";
			});

			element += '</div>';

			if ($('.elements_linked').length) {
				$('.elements_linked').replaceWith(element);
			} else {
				$('#box_features_container').prepend(element);
			}

			var el_link = $('.elements_linked');
			if ($(this).data('hidden')) {
				el_link.slideDown();
				$(this).data('hidden', false);
			} else {
				el_link.slideUp(500);
				$(this).data('hidden', true);
			}
			var annotations_layer = $('#OpenLayers_Layer_Vector_27_svgRoot');

			el_link.find('p').on('mouseover', function(event) {
				var id = $(this).data('id');
				for (var i = 0; i < annotator.vectorLayer.features.length; i++) {
					var f = annotator.vectorLayer.features[i];
					if (f.id == id) {
						f.style.strokeColor = 'red';
						f.style.strokeWidth = 6;
					}
				}
				annotator.vectorLayer.redraw();

				if (annotator.fullScreen.active) {
					annotations_layer[0].setAttribute('viewBox', "0 0 " + $(window).width() + " " + $(window).height());
				}

			}).on('mouseout', function(event) {
				var id = $(this).data('id');
				for (var i = 0; i < annotator.vectorLayer.features.length; i++) {
					var f = annotator.vectorLayer.features[i];
					if (f.id == id) {
						f.style.strokeColor = 'blue';
						f.style.strokeWidth = 2;
					}
				}
				annotator.vectorLayer.redraw();

				if (annotator.fullScreen.active) {
					annotations_layer[0].setAttribute('viewBox', "0 0 " + $(window).width() + " " + $(window).height());
				}

			}).on('click', function() {
				var id = $(this).data('id');
				//annotator.selectFeatureByIdAndZoom(id);
				var feature;
				for (var i = 0; i < annotator.vectorLayer.features.length; i++) {
					if (annotator.vectorLayer.features[i].id == id) {
						feature = annotator.vectorLayer.features[i];
					}
				}
				annotator.map.zoomToExtent(feature.geometry.getBounds());
				/*
				for (var i = 0; i < features_length; i++) {
					if (features[i].id == id) {
						selectedFeature = features[i];
						break;
					}
				}

				annotator.selectedFeature = selectedFeature;
				var annotation = annotator.annotations[selectedFeature.graph];
				$('#panelImageBox .allograph_form').val(getKeyFromObjField(annotation, 'hidden_allograph'));
				$('#panelImageBox .hand_form').val(annotation.hand);
				$('select').trigger('liszt:updated');

				var n = 0;

				for (var g = 0; g < features_length; g++) {
					if (features[g].feature == feature.feature && features[g].stored) {
						n++;
					}
				}

				$(".number_annotated_allographs .number-allographs").html(n);
				*/
			});

			restoreFullscreenPositions();

			var ungroup_elements = $('.ungroup');

			ungroup_elements.click(function() {
				var id = $(this).data('id');
				$(this).parent('p').fadeOut().remove();
				ungroup(id);
				$.each(elements_linked, function(index, value) {
					if (value && value.id == id) {
						elements_linked.splice(index, 1);
					}
				});
			});

		});
	}
};


function ungroup(element_id) {
	var a;

	for (var i = 0; i < annotator.selectedAnnotations.length; i++) {
		var annotation = annotator.selectedAnnotations[i];
		if (!$.isEmptyObject(annotation.linked_to[0]) && typeof annotation.linked_to[0][element_id] !== "undefined") {
			delete annotation.linked_to[0][element_id];
		}

		if (annotation.id == element_id) {
			var group_items = 0;

			for (var j in annotation.linked_to[0]) {
				group_items++;
			}

			if (group_items <= 1) {
				$('.allograph_label').html(annotation.feature);
				$('.elements_linked').remove();
			}

			annotation.linked_to = [];
			a = annotation;
		}

	}

	annotator.selectFeature.unselect(a);

	for (i = 0; i < annotator.vectorLayer.features.length; i++) {
		var f = annotator.vectorLayer.features[i];

		if (f.id == element_id) {
			f.style.strokeWidth = 2;
		}
	}
	annotator.vectorLayer.redraw();
	var element_num_linked = $('.num_linked');
	var num_linked = parseInt(element_num_linked.text(), 10) - 1;
	if (num_linked === 0) {
		var boxes = $('.dialog_annotations');
		boxes.remove();
	} else {
		element_num_linked.html(num_linked);
	}

}

DigipalAnnotator.prototype.filterAnnotation = function(checkboxes, formal_attribute, formal_attribute2) {
	var _self = this;
	var features = _self.vectorLayer.features;
	var feature;
	var attribute, attribute2;
	var hand;
	var allograph;
	for (var i in features) {
		if (formal_attribute == 'hand') {
			attribute = features[i].hand;
			attribute2 = features[i].feature.replace(/\., |;\. | /, '');
			hand = $('#hand_input_' + attribute);
			allograph = $('#allograph_' + attribute2);
			var allographs = $('.checkVectors');
			if (!($(checkboxes).is(':checked'))) {
				if ($(checkboxes).val() == attribute && features[i].hand == hand.val()) {
					features[i].style.fillOpacity = 0;
					features[i].style.strokeOpacity = 0;
				}
			} else {
				var max = allographs.length;
				for (var h = 0; h < max; h++) {
					var a = $(allographs[h]);
					if (a.is(':checked') && a.val().replace(/\., |;\. | /, '') == attribute2) {
						if ($(checkboxes).val() == attribute) {
							features[i].style.fillOpacity = 0.4;
							features[i].style.strokeOpacity = 1;
						}
					}
				}
			}
		} else {
			attribute = features[i].feature.replace(/\., |;\. | /, '_');
			attribute2 = features[i].hand;
			hand = $('#hand_input_' + attribute2);
			allograph = $('#hand_input_' + attribute2);
			if (!($(checkboxes).is(':checked'))) {
				if ($(checkboxes).val().replace(/\., |;\. | /, '_') == attribute && features[i].hand == hand.val()) {
					features[i].style.fillOpacity = 0;
					features[i].style.strokeOpacity = 0;
				}
			} else {
				if ($(checkboxes).val().replace(/\., |;\. | /, '_') == attribute && features[i].hand == hand.val() && hand.is(':checked')) {
					features[i].style.fillOpacity = 0.4;
					features[i].style.strokeOpacity = 1;
				}

			}
		}

	}
	_self.vectorLayer.redraw();
};

DigipalAnnotator.prototype.filterCheckboxes = function(checkboxes, check) {
	var _self = this;
	var features = _self.vectorLayer.features;

	function stylize(color, feature) {
		feature.style.fillColor = color;
		feature.style.strokeColor = color;
		if (feature.display_note) {
			feature.style.strokeColor = 'yellow';
		} else {
			feature.style.strokeColor = color;
		}
	}

	var allographs = $('.checkVectors');
	var hands = $('.checkVectors_hands');
	var hand, i;
	if (check == 'check') {
		$(checkboxes).attr('checked', true);
		var features_length = features.length;
		var hands_length = hands.length;
		for (i = 0; i < features_length; i++) {
			for (var h = 0; h < hands_length; h++) {
				hand = $(hands[h]);
				if (features[i].hand == hand.val() && hand.is(':checked') && features[i].stored) {
					if (!features[i].style) {
						features[i].style = {
							'fillOpacity': 0.4,
							'strokeOpacity': 1
						};
						if (features[i].described) {
							stylize('green', features[i]);

						} else {
							stylize('#ee9900', features[i]);
						}

					} else {
						features[i].style.fillOpacity = 0.4;
						features[i].style.strokeOpacity = 1;
						if (features[i].described) {
							stylize('green', features[i]);
						} else {
							stylize('#ee9900', features[i]);
						}
					}
				}
			}
		}

	} else if (check == 'uncheck') {
		$(checkboxes).attr('checked', false);
		var max = features.length;
		for (i = 0; i < max; i++) {
			if (features[i].stored) {
				if (!features[i].style) {
					features[i].style = {
						'fillOpacity': 0,
						'strokeOpacity': 0
					};
					if (features[i].described) {
						stylize('green', features[i]);
					} else {
						stylize('#ee9900', features[i]);
					}
				} else {
					features[i].style.fillOpacity = 0;
					features[i].style.strokeOpacity = 0;
					if (features[i].described) {
						stylize('green', features[i]);
					} else {
						stylize('#ee9900', features[i]);
					}
				}
			}
		}
	}
	_self.vectorLayer.redraw();
};

/**
 * Shows the annotation details for the given feature.
 *
 * @param feature
 *              The feature to display the annotation.
 */
DigipalAnnotator.prototype.showAnnotation = function(feature) {
	var select_allograph;

	if ($('.tab-pane.active').attr('id') == 'annotator') {
		select_allograph = $('#panelImageBox .allograph_form');
	} else {
		select_allograph = $('.modal-body .allograph_form');
	}

	if (feature.state == 'Insert') {
		var allograph;
		var allograph_list = select_allograph.find('option');
		$.each(allograph_list, function() {
			if ($(this).text() == feature.feature) {
				allograph = $(this).val();
			}
		});
		if (allograph) {
			select_allograph.val(allograph);
		}
		$('select').trigger('liszt:updated');
	}

	if (feature) {
		if (feature.style) {
			feature.style.fillColor = 'blue';
			feature.style.strokeColor = 'blue';
		} else {
			feature.style = {
				'fillColor': 'blue',
				'strokeColor': 'blue',
				'fillOpacity': 0.4
			};
		}
		this.vectorLayer.redraw();
	}

	var features = annotator.vectorLayer.features;
	var features_length = features.length;
	var n = 0;
	for (var i = 0; i < features_length; i++) {
		if (features[i].feature == feature.feature && features[i].stored) {
			n++;
		}
	}
	$(".number_annotated_allographs .number-allographs").html(n);

	if (this.annotations) {
		var annotation = null;
		for (var idx in this.annotations) {
			annotation = this.annotations[idx];
			if (annotation.vector_id == feature.id) {
				break;
			} else {
				annotation = null;
			}
		}
		showBox(annotation, function() {
			if (annotation) {
				if ($('.letters-allograph-container').length) {

					var allograph_id = $('#panelImageBox .allograph_form').val();
					var al = select_allograph.find('option:selected').text();

					if (typeof current_allograph === "undefined") {
						refresh_letters_container(al, allograph_id, true);
					}

					if (typeof current_allograph !== "undefined" && annotation.feature !== current_allograph) {
						refresh_letters_container(al, allograph_id, true);
					}
				}
			}

			if (annotator.selectedAnnotations.length > 1) {
				var checkboxes = $('.dialog_annotations').find('.features_box');
				var graphs = [];

				for (var g = 0; g < annotator.selectedAnnotations.length; g++) {
					graphs.push(annotator.selectedAnnotations[g].graph);
				}

				var cache = $.extend({}, annotator.cacheAnnotations.cache);
				detect_common_features(graphs, checkboxes, cache);

				/*
				for (g = 0; g < annotator.selectedAnnotations.length; g++) {
					var graph = annotator.selectedAnnotations[g].graph;
					var allograph_id2 = annotator.cacheAnnotations.cache.graphs[graph].allograph_id;

					delete annotator.cacheAnnotations.cache.allographs[allograph_id2];
					delete annotator.cacheAnnotations.cache.graphs[graph];
				}
				*/
			}
		});
	}
};

/*
    Function to get a feature by the vector id
    @param vector_id in annotator.annotations
    annotation returned
*/

function getFeatureById(id) {
	var selectedFeature = id;
	var features = annotator.vectorLayer.features;
	var features_length = features.length;
	var feature;
	for (i = 0; i < features_length; i++) {
		feature = features[i];
		if (selectedFeature == feature.id) {
			annotator.selectedFeature = feature;
			break;
		} else {
			feature = null;
		}
	}

	for (var idx in annotator.annotations) {
		annotation = annotator.annotations[idx];
		if (annotation.vector_id == feature.id) {
			break;
		} else {
			annotation = null;
		}
	}
	return annotation;
}

/* Applies style to a vector */
var stylize = function(feature, fill, stroke, opacity) {
	feature.style = {
		'strokeColor': stroke,
		'fillColor': fill,
		"fillOpacity": opacity
	};
};

/* Checks whether it is possible to select multiple annotations or not */
function allow_multiple() {
	var multiple_checkbox = $("#multiple_annotations");
	if (multiple_checkbox.is(':checked')) {
		return true;
	}
	return false;
}

/* Function to refresh the layer when saved an annotation */
DigipalAnnotator.prototype.refresh_layer = function() {
	annotator.vectorLayer.removeAllFeatures();
	annotator.vectorLayer.destroyFeatures();
	annotator.vectorLayer.addFeatures([]);
	$('circle').remove();
	$('polyline').remove();
	annotator.annotations = [];
	annotator.selectedFeature = null;
	annotator.selectedAnnotations = [];
	annotator.cacheAnnotations.clear();
	$('.dialog_annotations').parent().remove();
	var request = $.getJSON(annotator.absolute_image_url + 'annotations/', function(data) {
		annotator.annotations = data;
	});
	var div = $('<div>');
	div.attr('class', 'loading-div');
	div.html('<p>Reloading annotations. Please wait...</p></p><img src="/static/digipal/images/ajax-loader3.gif" />');
	$('#annotator').append(div.fadeIn());
	var chained = request.done(function(data) {
		if ($.isEmptyObject(data)) {
			div.fadeOut().remove();
			return false;
		}
		var layer = annotator.vectorLayer;
		var format = annotator.format;
		var annotations = data;
		var features_request = $.getJSON(annotator.absolute_image_url + 'vectors/');
		features_request.done(function(data) {
			var features = [];
			for (var j in data) {
				var f = format.read(data[j])[0];
				f.id = j;
				for (var i in annotations) {
					var allograph = annotations[i]['feature'];
					var character_id = annotations[i]['character_id'];
					var graph = annotations[i]['graph'];
					var character = annotations[i]['character'];
					var hand = annotations[i]['hand'];
					var image_id = annotations[i]['image_id'];
					var num_features = annotations[i]['num_features'];
					var display_note = annotations[i]['display_note'];
					if (f.id == annotations[i]['vector_id']) {
						f.feature = allograph;
						f.character_id = character_id;
						f.graph = graph;
						f.character = character;
						f.hand = hand;
						f.image_id = image_id;
						f.num_features = num_features;
						f.display_note = display_note;
						f.stored = true;
						f.linked_to = [];
					}
				}
				features.push(f);
			}
			layer.addFeatures(features);
			var vectors = annotator.vectorLayer.features;
			if (vectors) {
				reload_described_annotations(div);
				annotator.unsaved_annotations = [];
				$('.number_unsaved_allographs').html(0);
			}
			registerEvents();
			restoreFullscreenPositions();
			var activeControls = annotator.map.getControlsBy('active', true);
			toggleAll(activeControls, false);
		});
	});
};

/**
 
 * Updates the feature select according to the currently selected allograph.
 
 */
function updateFeatureSelect(currentFeatures, id) {
	var features = annotator.vectorLayer.features;
	var allograph_selected, select_allograph;
	var can_edit = $('#development_annotation').is(':checked');
	if ($('.tab-pane.active').attr('id') == 'annotator') {
		select_allograph = $('#panelImageBox .allograph_form');
	} else {
		select_allograph = $('.modal-body .allograph_form');
	}
	var annotations = annotator.annotations;
	if ($.isNumeric(currentFeatures)) {
		allograph_selected = currentFeatures;
	} else {
		if (select_allograph.val()) {
			allograph_selected = select_allograph.val();
		}
	}

	if (annotator.isAdmin === "True" && can_edit) {
		var allograph = select_allograph.val();
		var content_type = 'allograph';
		var url = '/digipal/api/' + content_type + '/' + allograph_selected;

		var dialog;
		var prefix;

		if ($('.tab-pane.active').attr('id') == 'annotator') {
			dialog = $('#dialog' + id);
			if (dialog.parent().find(".number_annotated_allographs").length) {
				dialog.parent().find(".number_annotated_allographs .number-allographs").html(n);
			}
			prefix = 'annotator_';
		} else {
			dialog = $('.modal-body');
			prefix = 'allographs_';
		}

		if (typeof allograph_selected !== 'undefined' && allograph_selected) {
			var request = $.getJSON(url);
			request.done(function(data) {
				var allographs = data[0];
				update_dialog(prefix, allographs, annotator.selectedAnnotations, function(s) {

					if (!annotator.editorial.active && annotator.selectedFeature) {
						if (annotator.selectedFeature.linked_to && !$.isEmptyObject(annotator.selectedFeature.linked_to[0])) {
							var num_linked = 0;
							elements_linked = [];
							for (var g in annotator.selectedFeature.linked_to[0]) {
								num_linked++;
								elements_linked.push(annotator.selectedFeature.linked_to[0][g]);
							}

							var allograph_label = $('.allograph_label');
							allograph_label.html("Group (<span class='num_linked'>" + num_linked + '</span>) <i title="Show group elements" data-placement="bottom" data-container="body" data-toggle="tooltip" class="glyphicon glyphicon-list show_group" data-hidden="true" />')
								.css('cursor', 'pointer')
								.data('hidden', true);

							allograph_label.unbind().click(function() {

								var element = "<div class='elements_linked'>";

								$.each(elements_linked, function() {
									element += "<p data-id='" + this.id + "'>" + this.feature + "<i title='ungroup' class='pull-right glyphicon glyphicon-remove ungroup' data-id='" + this.id + "' /></p>";
								});

								element += '</div>';

								if ($('.elements_linked').length) {
									$('.elements_linked').replaceWith(element);
								} else {
									$('#box_features_container').prepend(element);
								}

								var el_link = $('.elements_linked');
								if ($(this).data('hidden')) {
									el_link.slideDown();
									$(this).data('hidden', false);
								} else {
									el_link.slideUp(500);
									$(this).data('hidden', true);
								}

								var annotations_layer = $('#OpenLayers_Layer_Vector_27_svgRoot');

								el_link.find('p').on('mouseover', function(event) {
									var id = $(this).data('id');
									for (var i = 0; i < annotator.vectorLayer.features.length; i++) {
										var f = annotator.vectorLayer.features[i];
										if (f.id == id) {
											f.style.strokeColor = 'red';
											f.style.strokeWidth = 6;
										}
									}
									annotator.vectorLayer.redraw();
									if (annotator.fullScreen.active) {
										annotations_layer[0].setAttribute('viewBox', "0 0 " + $(window).width() + " " + $(window).height());
									}
								}).on('mouseout', function(event) {
									var id = $(this).data('id');
									for (var i = 0; i < annotator.vectorLayer.features.length; i++) {
										var f = annotator.vectorLayer.features[i];
										if (f.id == id) {
											f.style.strokeColor = 'blue';
											f.style.strokeWidth = 2;
										}
									}
									annotator.vectorLayer.redraw();
									if (annotator.fullScreen.active) {
										annotations_layer[0].setAttribute('viewBox', "0 0 " + $(window).width() + " " + $(window).height());
									}
								}).on('click', function() {
									var id = $(this).data('id');
									//annotator.selectFeatureByIdAndZoom(id);
									var feature;
									for (var i = 0; i < annotator.vectorLayer.features.length; i++) {
										if (annotator.vectorLayer.features[i].id == id) {
											feature = annotator.vectorLayer.features[i];
										}
									}
									annotator.map.zoomToExtent(feature.geometry.getBounds());
								});

								var ungroup_elements = $('.ungroup');

								ungroup_elements.click(function() {
									var id = $(this).data('id');
									$(this).parent('p').fadeOut().remove();
									ungroup(id);
									$.each(elements_linked, function(index, value) {
										if (value.id == id) {
											elements_linked.splice(index, 1);
											index--;
										}
									});
								});

							});
						} else {
							dialog.parent().find('.allograph_label').html($('#panelImageBox .allograph_form option:selected').text());
						}
					}
					dialog.find('#box_features_container').html(s);
					dialog.find('.check_all').click(function(event) {
						var checkboxes = $(this).parent().parent().next().find('input[type=checkbox]');
						checkboxes.attr('checked', true);
						event.stopPropagation();
					});

					dialog.find('.uncheck_all').click(function(event) {
						var checkboxes = $(this).parent().parent().next().find('input[type=checkbox]');
						checkboxes.attr('checked', false);
						event.stopPropagation();
					});

					var set_by_default = dialog.find('.set_by_default');
					set_by_default.on('click', function(event) {
						var component_id = $(this).data('component');
						check_features_by_default(component_id, allograph, annotator.cacheAnnotations.cache);
						event.stopPropagation();
					});

					dialog.find('.component_labels').click(function() {
						var div = $("#" + $(this).data('id'));
						if (div.data('hidden') === false) {
							div.slideUp().data('hidden', true);
							$(this).next('.checkboxes_div').hide();
							$(this).find('.arrow_component').removeClass('fa-angle-double-up').addClass('fa-angle-double-down');
						} else {
							div.slideDown().data('hidden', false);
							$(this).next('.checkboxes_div').show();
							$(this).find('.arrow_component').removeClass('fa-angle-double-down').addClass('fa-angle-double-up');
						}
					});

					if (annotator.selectedFeature && annotator.selectedFeature.state == 'Insert') {
						$('.features_box').on('change', function() {
							var checkbox = $(this);
							var val = checkbox.val();
							if (checkbox.is(':checked')) {
								if (annotator.selectedFeature.features.indexOf(val) !== 0) {
									annotator.selectedFeature.features.push(val);
								}
							} else {
								if (annotator.selectedFeature.features.indexOf(val) !== 0) {
									annotator.selectedFeature.features.splice(annotator.selectedFeature.features.indexOf(val), 1);
								}
							}

						});
					}

					// Showing all the allographs of a given allograph
					dialog.parent().find('.number_annotated_allographs').click(function() {
						open_allographs($(this), true);
					});
				});
			});
		}
	}
}


function createPopup(feature) {
	var map = annotator.map;
	feature.popup = new OpenLayers.Popup.FramedCloud("pop",
		feature.geometry.getBounds().getCenterLonLat(),
		null,
		'<div class="markerContent">' + feature.display_note + '</div>',
		null,
		null,
		function() {
			controls['selector'].unselectAll();
		}
	);

	//feature.popup.closeOnMove = true;
	map.addPopup(feature.popup);
	$('.olPopupCloseBox').click(function() {
		feature.popup.destroy();
		feature.popup = null;
	});
}

function deletePopup(feature) {
	feature.popup.destroy();
	feature.popup = null;
}


/*

Feature to discover the already described allographs and
render the layer according to each allograph

*/

function reload_described_annotations(div) {
	var check_described = null;
	var annotations = annotator.annotations;
	$.each(annotations, function(index, annotation) {
		var feature = annotator.vectorLayer.features;
		var selectedFeature;
		if (typeof annotator.selectedFeature !== "undefined" && typeof annotator.selectedFeature != "null") {
			selectedFeature = annotator.selectedFeature;
		}
		var num_features = annotation.num_features;
		var h = 0;
		var path;
		check_described = $.each(feature, function(index, data) {
			while (h < feature.length) {
				if (annotation.graph == feature[h].graph) {
					if (num_features) {
						stylize(feature[h], 'green', 'green', 0.4);
						feature[h].described = true;

						if (typeof selectedFeature != "undefined" && typeof selectedFeature != "null" && selectedFeature && feature[h].graph == selectedFeature.graph) {
							//stylize(feature[h], 'blue', 'blue', 0.4);
							feature[h].described = true;
							annotator.selectFeatureById(feature[h].id);
						}
						/*
						if (feature[h].display_note) {
							feature[h].style.strokeColor = 'yellow';
						}
						*/
					} else {
						stylize(feature[h], '#ee9900', '#ee9900', 0.4);
						feature[h].described = false;

						if (typeof selectedFeature != "undefined" && typeof selectedFeature != "null" && selectedFeature) {
							if (feature[h].graph == selectedFeature.graph) {
								//stylize(feature[h], 'blue', 'blue', 0.4);
								feature[h].described = false;
								annotator.selectFeatureById(feature[h].id);
							}
						}

						/*
						if (feature[h].display_note) {
							feature[h].style.strokeColor = 'yellow';
						}
						*/
					}
				}
				h++;
			}
		});

	});

	if (check_described) {
		annotator.vectorLayer.redraw();
		if (typeof div != "undefined") {
			div.fadeOut().remove();
		}
	}
}

/*

Function to create a new dialog for each allograph clicked

*/

function create_dialog(selectedFeature, id) {

	if (typeof annotator.allow_multiple_dialogs == "undefined") {
		annotator.allow_multiple_dialogs = false;
	}

	if (!annotator.allow_multiple_dialogs) {
		var dialog_annotations = $('.dialog_annotations');
		dialog_annotations.parent('.ui-dialog').remove();
		dialog_annotations.remove();
	}

	var dialog = $("<div>");

	dialog.attr('id', 'dialog' + id);
	$('#annotations').append(dialog);
	var path = $("#OpenLayers_Layer_Vector_27_svgRoot");

	if (selectedFeature && selectedFeature.hasOwnProperty('graph')) {
		var vector_id;
		var features_length = annotator.vectorLayer.features.length;
		for (var i = 0; i < features_length; i++) {
			var feature = annotator.vectorLayer.features[i];
			if (feature.graph == selectedFeature.graph) {
				vector_id = feature.geometry.id;
				break;
			}
		}
		//path = $('#' + vector_id);
		path = document.getElementById(vector_id);
	}
	dialog.data('feature', selectedFeature);
	var absolute_position = false;
	var position = function() {
		var p;
		if (annotator.allow_multiple_dialogs) {
			p = {
				my: 'right top',
				at: 'right bottom',
				of: $(path)
			};
		} else {
			absolute_position = true;
			p = ['60%', '30%'];
		}
		return p;
	};

	$('#boxes_on_click').attr('checked', true);
	dialog.dialog({
		draggable: true,
		height: 340,
		minHeight: 340,
		minWidth: 335,
		resizable: false,
		close: function(event, ui) {
			$(this).dialog('destroy').empty().remove();
			if (!$('.dialog_annotations').length) {
				annotator.pinned = undefined;
			}
		},
		title: function() {
			var title;
			if (annotator.isAdmin == "True") {
				/*

				var button = <span class='btn btn-sm btn-primary number_annotated_allographs' data-feature = '" + selectedFeature.feature + "' title='Show all the images of this allograph'><i class= 'icon-eye-open'></i> <span class='number-allographs'></span></span>

				*/
				if (selectedFeature && !annotator.editorial.active) {
					title = "<span class='allograph_label'>" + selectedFeature.feature +
						"</span> <button title='Share URL' data-toggle='tooltip' data-container='body' data-hidden='true' class='url_allograph btn-default btn btn-xs'><i  class='fa fa-link' ></i></button> <button title='Add graph to collection' data-toggle='tooltip' data-container='body' class='to_lightbox btn btn-default btn-xs' data-graph = '" + selectedFeature.graph + "'><i class='fa fa-folder-open'></i></button> <button data-toggle='tooltip' data-placement='bottom' data-container='body' type='button' title='Check by default' class='btn btn-xs btn-default set_all_by_default'><i class='fa fa-plus-square'></i></button>";
					if (allow_multiple() && annotator.selectedAnnotations.length > 1) {
						title += " <button class='btn btn-default btn-xs link_graphs'>Group</button>";
					} else {
						title += " <button class='btn btn-default btn-xs link_graphs disabled' disabled>Group</button>";
					}
				} else if (!annotator.annotating) {
					title = "<input type='text' placeholder = 'Type name' class='name_temporary_annotation' /> <span style='margin-left: 8%;'><button data-toggle='tooltip' data-container='body' title='Share URL' style='margin-right: 3%;' data-hidden='true' class='url_allograph btn btn-xs btn-default pull-right'><i class='fa fa-link'></i></button> ";

				} else {
					if (annotator.editorial.active) {
						title = "<span class='allograph_label'>Annotation</span>" +
							" <button data-hidden='true' data-toggle='tooltip' data-container='body' title='Share URL' class='url_allograph btn btn-default btn-xs'><i class='fa fa-link'></i></button> ";
						if (allow_multiple() && annotator.selectedAnnotations.length > 1) {
							title += " <button data-toggle='tooltip' data-container='body' title='Group Annotations' class='btn btn-default btn-xs link_graphs'>Group</button>";
						} else {
							title += " <button data-toggle='tooltip' data-container='body' title='Group Annotations' class='btn btn-default btn-xs link_graphs disabled' disabled>Group</button>";
						}
					} else {
						title = "<span class='allograph_label'>Annotation</span> <button data-hidden='true' class='url_allograph btn btn-default btn-xs' data-toggle='tooltip' data-container='body' title='Share URL'><i class='fa fa-link'></i></button> ";
						if (annotator.selectedFeature) {
							title += "<button class='to_lightbox btn btn-default btn-xs' data-graph = '" + annotator.selectedFeature.graph + "' data-toggle='tooltip' data-container='body' title='Add graph to collection'><i class='fa fa-folder-open'></i></button>";
						}
						if (allow_multiple() && annotator.selectedAnnotations.length > 1) {
							title += " <button data-toggle='tooltip' data-container='body' title='Group Annotations' class='btn btn-default btn-xs link_graphs'>Group</button>";
						} else {
							title += " <button data-toggle='tooltip' data-container='body' title='Group Annotations' class='btn btn-default btn-xs link_graphs disabled' disabled>Group</button>";
						}
					}
				}
			} else {
				if (selectedFeature) {
					title = "<span class='allograph_label'>" + selectedFeature.feature + "</span> <button data-toggle='tooltip' title='Share URL' data-hidden='true' class='url_allograph btn btn-default btn-xs'><i class='fa fa-link'></i></button> <button data-toggle='tooltip' title='Add graph to collection' class='to_lightbox btn btn-default btn-xs' data-graph = '" + selectedFeature.graph + "'><i class='fa fa-folder-open'></i></button>";
				} else {
					title = "<input type='text' placeholder = 'Type name' class='name_temporary_annotation' /> <span class='pull-right' style='margin-right: 0.5em;''><button data-hidden='true' class='url_allograph btn btn-default btn-xs ' data-toggle='tooltip' title='Share URL'><i class='fa fa-link'></i></button>";
				}
				if (annotator.selectedAnnotations.length > 1) {
					title += " <button data-toggle='tooltip' data-container='body' title='Group Annotations' class='btn btn-default btn-xs link_graphs'>Group</button></span>";
				} else {
					title += " <button data-toggle='tooltip' data-container='body' title='Group Annotations' class='btn btn-default btn-xs link_graphs disabled' disabled>Group</button></span>";
				}
			}
			return title;
		},
		position: position()
	}).addClass('dialog_annotations');

	if (absolute_position) {
		var top_page_position = $(window).scrollTop();
		var window_height = ($(window).height() / 100) * 25;
		dialog.parent().css({
			'position': 'absolute',
			'top': top_page_position + window_height,
			'left': '68%'
		});
	}

	if (annotator.isAdmin == "False" || !annotator.annotating) {
		$('.name_temporary_annotation').focus();
		$('.ui-dialog-title').on('click', function() {
			$('.name_temporary_annotation').focus();
		});
		annotator.selectedFeature.isTemporary = true;
	}

	/*
	if (typeof selectedFeature === "null" || typeof selectedFeature === "undefined") {
		updateFeatureSelect(null, id);
	} else {
		updateFeatureSelect(selectedFeature, id);
	}
	*/

	// Showing all the allographs of a given allograph
	dialog.parent().find('.number_annotated_allographs').click(function() {
		open_allographs($(this), true);
	});

	if (annotator.selectedFeature && !selectedFeature) {
		selectedFeature = annotator.selectedFeature;
	}

	$('.to_lightbox').click(function() {
		if (!annotator.selectedFeature) {
			annotator.selectedFeature = annotator.selectedAnnotations[annotator.selectedAnnotations.length];
		}
		if (annotator.selectedAnnotations.length > 1) {
			var links = [];
			for (var l in annotator.selectedAnnotations) {
				links.push(annotator.selectedAnnotations[l].graph);
			}
			add_to_lightbox($(this), 'annotation', links, true);
		} else {
			add_to_lightbox($(this), 'annotation', selectedFeature.graph, false);
		}

	});

	$('.link_graphs').click(function() {
		annotator.linkAnnotations();
	});

	$('*[data-toggle="tooltip"]').tooltip({
		container: 'body',
		placement: 'bottom'
	});
}

function load_allographs_container(allograph_value, url, show, allograph_id) {
	var features = $.getJSON(url);
	if (show === undefined) {
		show = true;
	}
	var div = $("<div>");

	div.attr('class', 'letters-allograph-container');
	div.css({
		'position': 'fixed',
		'top': '20%',
		'left': '33%',
		'width': '30%',
		'height': 'auto',
		'min-height': '25%',
		'z-index': 1020
	});
	div.draggable({
		handle: '#top_div_annotated_allographs',
		cursor: "move"
	});

	var top_div = $("<div id='top_div_annotated_allographs'>");

	var number_allographs = $('.number-allographs');
	top_div.append("<span>" + allograph_value + "</span> <i title='Close box' class='icon pull-right glyphicon glyphicon-remove close_top_div_annotated_allographs'></i>");

	div.append(top_div);

	var container_div = $("<div id='container-letters-popup'>");
	div.append(container_div);
	if (show) {
		$('#annotator').append(div);
	}

	var img = $("<img>");

	img.attr('class', 'img-loading');
	img.attr('src', '/static/digipal/images/ajax-loader3.gif');
	$('#top_div_annotated_allographs').find('span').after(img);

	features.done(function(data) {
		number_allographs.html(data.length);
		var s = '';

		if (data != "False") {
			data = data.sort();
			var j = 0;
			var data_hand;
			if (data.length === 1) {
				j = 1;
				s += "<label class='hands_labels' data-hand = '" + data[0].hand + "' id='hand_" + data[0].hand + "'>Hand: " + data[0].hand_name + "</label>\n";
				data_hand = data[0].hand;
				s += "<span data-hand = '" + data_hand + "' class='vector_image_link' data-vector-id='" + data[0].vector_id + "' title='Click on the image to center the map; Double click to select letter'>" + data[0].image + '</span>\n';
			} else {
				for (var i = 0; i < data.length; i++) {
					j++;
					if (i === 0) {
						s += "<label class='hands_labels' data-hand = '" + data[i].hand + "' id='hand_" + data[i].hand + "'>Hand: " + data[i].hand_name + "</label>\n";
						data_hand = data[i].hand;
					}
					if (typeof data[i - 1] != "undefined" && typeof data[i + 1] != "undefined" && data[i].hand != data[i - 1].hand) {
						j = 1;
						data_hand = data[i].hand;
						s += "<label class='hands_labels' data-hand = '" + data[i].hand + "'  id='hand_" + data_hand + "'>Hand: " + data[i + 1].hand_name + "</label>\n";
					}
					if (typeof data[i + 1] == "undefined" && data[i].hand != data[i - 1].hand) {
						j = 1;
						data_hand = data[i].hand;
						s += "<label class='hands_labels' data-hand = '" + data[i].hand + "'  id='hand_" + data_hand + "'>Hand: " + data[i].hand_name + "</label>\n";
					}
					s += "<span data-hand = '" + data_hand + "' class='vector_image_link' data-vector-id='" + data[i].vector_id + "' title='Click on the image to center the map; Double click to select letter'>" + data[i].image + '</span>\n';
				}
			}

			$(s).find('img').each(function() {
				$(this).on('load', function() {

					img.remove();
					container_div.html(s);

					var button = $('.close_top_div_annotated_allographs');
					var container = $('.letters-allograph-container');
					var container_number = $('.number_annotated_allographs');
					var images_link = $('.vector_image_link');
					var annotations_layer = $('#OpenLayers_Layer_Vector_27_svgRoot');
					var features = annotator.vectorLayer.features;

					images_link.fadeIn();

					button.click(function() {
						container.fadeOut().remove();
						container_number.removeClass('active');
					});


					images_link.click(function() {
						var vector = $(this);
						annotator.centreById(vector.data('vector-id'));
					});


					// waiting for all images to be loaded
					images_link.on("mouseover", function() {
						var vector = $(this);
						for (var i = 0; i < features.length; i++) {
							if (features[i].id == vector.data('vector-id')) {
								features[i].originalColor = features[i].style.fillColor;
								features[i].style.strokeColor = 'red';
								features[i].style.strokeWidth = 6;
								break;
							}
						}
						annotator.vectorLayer.redraw();
						restoreFullscreenPositions();
					});


					images_link.mouseout(function() {
						var vector = $(this);
						for (var i = 0; i < features.length; i++) {
							if (features[i].id == vector.data('vector-id')) {
								features[i].style.strokeColor = features[i].originalColor;
								features[i].style.strokeWidth = 2;
								break;
							}
						}
						annotator.vectorLayer.redraw();
						restoreFullscreenPositions();
					});

					images_link.dblclick(function() {
						var vector = $(this);
						annotator.selectFeatureByIdAndCentre(vector.data('vector-id'));
					});


					var hands = $('.hands_labels');
					$.each(hands, function(index_hands, hand) {
						var c = 0;
						$.each(images_link, function(index_images, image) {
							if ($(image).data('hand') == $(hand).data('hand')) {
								c++;
							}
						});
						$(hand).append(" <span class='num_all_hands badge'>" + c + "</span>");
					});
				});
			});

			/*
			var ul = $('ul[data-allograph="' + allograph_value + '"]');
			if (!ul.length) {
				ul = $('<ul data-allograph="' + allograph_value + '" class="list-allographs" data-key="' + allograph_id + '_' + allograph_value.replace('', '-') + '">');
				ul.html('<h5 class="header5">' + allograph_value + '</h5>');
			}
			var el = '';
			for (var h = 0; h < data.length; h++) {
				el += '<li class="annotation_li" data-graph="' + data[h].graph + '" data-annotation="' + data[h].vector_id + '" data-image="' + data[h].image_id + '">';
				el += '<p><span class="label label-info">' + (h + 1) + '</span></p>' + data[h].image + '</li>';
			}
			ul.html(el);
			*/
		} else {
			s = "<p><label>No Annotations</label></p>";
			container_div.html(s);
		}
	});
}

function open_allographs(allograph, show) {
	current_allograph = allograph;
	var container = $('.letters-allograph-container');
	if (container.length) {
		container.remove();
	}
	$(this).addClass('active');
	var allograph_value, allograph_id;
	if (annotator.isAdmin == 'True') {
		if (typeof allograph != "undefined") {
			allograph_value = allograph.parent().prev().text();
		} else {
			allograph_value = $('#panelImageBox .allograph_form option:selected').text();
			allograph_id = $('#panelImageBox .allograph_form').val();
		}
	} else {
		allograph_value = annotator.selectedFeature.feature;
	}
	if (allograph_value) {
		var features = annotator.vectorLayer.features;
		var feature, character;
		for (var i = 0; i < features.length; i++) {
			if (features[i].feature == allograph_value) {
				feature = features[i].graph;
				character = features[i].character_id;
				break;
			}
		}
		if (!feature && !character) {
			return false;
		}
		var url = annotator.absolute_image_url + "graph/" + feature + "/" + character + "/allographs_by_graph/";
		load_allographs_container(allograph_value, url, show, allograph_id);
	}
}

function refresh_letters_container(allograph, allograph_id, show) {
	current_allograph = allograph;
	var container = $('.letters-allograph-container');
	if (container.length) {
		container.remove();
		show = true;
	} else {
		show = false;
	}
	var features = annotator.vectorLayer.features;
	var character_id;
	for (i = 0; i < features.length; i++) {
		if (features[i].feature == allograph) {
			character_id = features[i].character_id;
			break;
		}
	}
	if (typeof character_id == "undefined") {
		return false;
	}
	var url = annotator.absolute_image_url + "allographs/" + allograph_id + "/" + character_id + "/allographs_by_allograph/";
	load_allographs_container(allograph, url, show);
}

/*

Function to fill the content of a dialog

*/

function fill_dialog(id, annotation) {
	var can_edit = $('#development_annotation').is(':checked');
	var dialog = $('#dialog' + id);
	var s = '';
	var panel = $('#panelImageBox');
	if (typeof annotation != 'null') {
		if (can_edit) {
			s += "<input type='hidden' name='allograph' id='hidden_allograph' /> <input type='hidden' id='hidden_hand' name='hand' />";
			s += "<div id='box_features_container'></div>";

			panel.find('.allograph_form').on('change', function() {
				var n = 0;
				var features = annotator.vectorLayer.features;
				var allograph = $('#panelImageBox .allograph_form option:selected').text();
				var allograph_id = $(this).val();

				for (var i = 0; i < features.length; i++) {
					if (features[i].feature == allograph && features[i].stored) {
						n++;
					}
				}

				$(".number_annotated_allographs .number-allographs").html(n);
				updateFeatureSelect(annotation, id);
			});
		}
	} else {
		s += "<textarea style='height:95%;' class='textarea_temporary_annotation form-control' placeholder='Type description here...'></textarea>";
	}

	dialog.html(s);

	var url_allograph_button = dialog.parent().find('.url_allograph');

	url_allograph_button.click(function() {
		show_url_allograph(dialog, annotation, $(this));
	});

	var name_temporary_annotation = $('.name_temporary_annotation');
	var content_temporary_annotation = $('.textarea_temporary_annotation');

	if (annotator.selectedFeature.contentAnnotation) {
		content_temporary_annotation.val(annotator.selectedFeature.contentAnnotation);
	}

	if (annotator.selectedFeature.contentTitle) {
		name_temporary_annotation.val(annotator.selectedFeature.contentTitle);
	}

	name_temporary_annotation.on('keyup', function() {
		annotator.selectedFeature.contentTitle = $(this).val();
	});

	name_temporary_annotation.on('change', function() {
		annotator.selectedFeature.contentTitle = $(this).val();
	});

	content_temporary_annotation.on('keyup', function() {
		annotator.selectedFeature.contentAnnotation = $(this).val();
	});

	content_temporary_annotation.on('change', function() {
		annotator.selectedFeature.contentAnnotation = $(this).val();
	});

	var hidden_hand = panel.find('.hand_form').val();
	var hidden_allograph = panel.find('.allograph_form').val();

	$('#hidden_hand').val(hidden_hand);
	$('#hidden_allograph').val(hidden_allograph);

	if ($('.letters-allograph-container').length && annotation) {
		var allograph_id = get_allograph(annotation.feature);
		refresh_letters_container(annotation.feature, allograph_id, true);
	}

}

function get_allograph(allograph) {
	var annotations = annotator.annotations;
	var allograph_id;
	$.each(annotations, function() {
		if (this.feature == allograph) {
			allograph_id = this.hidden_allograph.split('::')[0];
		}
	});
	return allograph_id;
}

function show_url_allograph(dialog, annotation, button) {
	var features = annotator.vectorLayer.features;
	if (button.data('hidden')) {
		button.data('hidden', false);
		$('.link_graphs').after(' <img src="/static/digipal/images/ajax-loader3.gif" id="url_allograph_gif" />');
		var url = $("<div class='allograph_url_div' data-url-type='short'>");
		var allograph_url, stored = false;
		var a = $('<a>');
		a.attr('target', '_tab');
		var title = $('.name_temporary_annotation').val();
		var desc = $('.textarea_temporary_annotation').val();

		// get annotations visibility status
		var getAnnotationsVisibility = $('.toggle-state-switch').bootstrapSwitch('state');
		var layerExtent = annotator.map.getExtent();
		var dialogPosition = $('.dialog_annotations').offset();
		var checkboxesOff = [];
		var checkboxes = $('.checkVectors');
		var i;
		checkboxes.each(function() {
			if (!$(this).is(':checked')) {
				checkboxesOff.push($(this).parent('p').data('annotation'));
			}
		});

		if (annotation !== null && annotation) {
			for (i = 0; i < features.length; i++) {
				if (annotation.graph == features[i].graph && features[i].stored) {
					stored = true;
				}
			}
		}

		if (annotator.selectedFeature.stored) {
			annotation = annotator.selectedFeature;
			stored = true;
		}

		var multiple = false,
			url_temp;
		if (annotation !== null && typeof annotation !== "undefined" && stored) {

			if (annotator.selectedAnnotations.length &&
				annotator.selectedFeature.linked_to != 'undefined' &&
				annotator.selectedFeature.linked_to.length && allow_multiple()) {

				multiple = true;
				allograph_url = [];

				for (i = 0; i < annotator.selectedAnnotations.length; i++) {

					url_temp = 'vector_id=' + annotator.selectedAnnotations[i].id;

					allograph_url.push(url_temp);

				}

				allograph_url = window.location.hostname + document.location.pathname + '?' + allograph_url.join('&') + '&map_extent=' + JSON.stringify(layerExtent);

			} else {

				allograph_url = window.location.hostname + document.location.pathname + '?vector_id=' + annotator.selectedFeature.id;

			}

		} else {
			var geometryObject, geoJSONText;
			if (annotator.selectedAnnotations.length &&
				annotator.selectedFeature.linked_to != 'undefined' &&
				annotator.selectedFeature.linked_to.length && allow_multiple()) {

				allograph_url = [];

				for (i = 0; i < annotator.selectedAnnotations.length; i++) {

					geometryObject = annotator.selectedAnnotations[i];
					geoJSONText = JSON.parse(annotator.format.write(geometryObject));

					geoJSONText.title = title;
					geoJSONText.desc = desc;
					geoJSONText.dialogPosition = dialogPosition;
					geoJSONText.extent = layerExtent;
					geoJSONText.visibility = getAnnotationsVisibility;

					if (checkboxesOff.length) {
						geoJSONText.checkboxes = checkboxesOff;
					}

					url_temp = 'temporary_vector=' + JSON.stringify(geoJSONText);

					allograph_url.push(url_temp);

				}
				allograph_url = window.location.hostname +
					document.location.pathname + '?' + allograph_url.join('&');
			} else {

				geometryObject = annotator.selectedFeature;
				geoJSONText = JSON.parse(annotator.format.write(geometryObject));

				geoJSONText.title = title;
				geoJSONText.desc = desc;
				geoJSONText.dialogPosition = dialogPosition;
				geoJSONText.extent = layerExtent;
				geoJSONText.visibility = getAnnotationsVisibility;

				if (checkboxesOff.length) {
					geoJSONText.checkboxes = checkboxesOff;
				}
				allograph_url = window.location.hostname +
					document.location.pathname + '?temporary_vector=' + JSON.stringify(geoJSONText);
			}
		}

		gapi.client.load('urlshortener', 'v1', function() {

			var request = gapi.client.urlshortener.url.insert({
				'resource': {
					'longUrl': allograph_url
				}
			});

			var resp = request.execute(function(resp) {
				if (resp.error) {
					throw new Error('Got error in requesting short url');
				} else {
					$('#url_allograph_gif').fadeOut().remove();
					a.attr('href', resp.id);
					a.attr('title', 'Copy link to annotation and share it');
					a.text(resp.id);
					button.data('url', resp.id);
					url.append(a);
					url.append("<button style='font-size: 12px;' class='btn btn-default btn-xs pull-right' id='long_url'>Long URL?</button>");
					dialog.prepend(url);

					var long_url_button = $('#long_url');
					long_url_button.on('click', function() {
						if (url.data('url-type') == 'short') {
							a.text(allograph_url);
							button.data('url', allograph_url);
							url.html("<a title='Copy link to annotation and share it' href='http://" + allograph_url + "'>" + allograph_url.substring(0, 60) + "...</a>");
							url.data('url-type', 'long');
						}
					});
				}
			});

		});

	} else {
		button.data('hidden', true);
		var url_allograph_element = dialog.parent().find('.allograph_url_div');
		url_allograph_element.fadeOut().remove();
	}
}

function showBox(selectedFeature, callback) {

	var features = annotator.vectorLayer.features;
	var id = Math.random().toString(36).substring(7);
	var can_edit = $('#development_annotation').is(':checked');
	var select_allograph;
	if ($('.tab-pane.active').attr('id') == 'annotator') {
		select_allograph = $('#panelImageBox');
	} else {
		select_allograph = $('.modal-body');
	}

	if (annotator.isAdmin == "True") {
		highlight_vectors();
	}

	if (selectedFeature === null || typeof selectedFeature == "undefined") {
		create_dialog(null, id);
		fill_dialog(id, null);
		dialog = $('#dialog' + id);
		if (annotator.editorial.active && can_edit) {
			var s = '<label>Editorial Note</label>';
			s += '<textarea class="form-control" id="editorial_note" name="editorial_note" style="width:90%;height:40%;"></textarea>';
			s += '<label>Public Note</label>';
			s += '<textarea class="form-control" id="public_note" name="public_note" style="width:90%;height:40%;"></textarea>';
			dialog.css('margin', '3%');
			dialog.html(s);
		}

		if (annotator.selectedFeature) {
			select_allograph.find('.hand_form').val(annotator.selectedFeature.hand);
			$('select').trigger('liszt:updated');
		}
		updateFeatureSelect(false, id);
		return false;
	}

	if (annotator.boxes_on_click) {
		create_dialog(selectedFeature, id);
		fill_dialog(id, selectedFeature);
	}

	var n = 0;
	var annotations = annotator.annotations;


	for (var i = 0; i < features.length; i++) {
		if (features[i].feature == annotator.selectedFeature.feature && features[i].hand == annotator.selectedFeature.hand && features[i].stored) {
			n++;
		}
	}

	if ($(".number_annotated_allographs").length) {
		$(".number_annotated_allographs .number-allographs").html(n);
	}


	select_allograph.find('.hand_form').val(selectedFeature.hidden_hand);
	select_allograph.find('.allograph_form').val(getKeyFromObjField(selectedFeature, 'hidden_allograph'));
	$('select').trigger('liszt:updated');

	var url, request;
	var cache = annotator.cacheAnnotations;

	var allograph = selectedFeature.hidden_allograph.split(':')[0];
	var graph = selectedFeature.graph;

	var content_type = 'graph';
	var prefix = 'annotator_';

	// if there's no allograph cached, I make a full AJAX call
	if (!cache.search("allograph", allograph)) {

		url = '/digipal/api/' + content_type + '/' + selectedFeature.graph + '/';
		request = $.getJSON(url);
		request.done(function(data) {
			cache.update('allograph', data[0]['allograph_id'], data[0]);
			cache.update('graph', graph, data[0]);
			if (annotator.boxes_on_click) {
				refresh_dialog(id, data[0], selectedFeature, callback);
			}
		});

		// else if allograph is cached, I only need the features, therefore I change the URL to omit allographs
	} else if (cache.search("allograph", allograph) && (!cache.search('graph', graph))) {

		url = '/digipal/api/' + content_type + '/' + selectedFeature.graph + '/features';
		request = $.getJSON(url);
		request.done(function(data) {
			data[0]['allographs'] = cache.cache.allographs[allograph];
			cache.update('graph', graph, data[0]);
			if (annotator.boxes_on_click) {
				refresh_dialog(id, data[0], selectedFeature, callback);
			}
		});

		// otherwise I have both cached, I can get them from the cache object
	} else {
		var data = {};
		data['allographs'] = cache.cache.allographs[allograph];
		data['features'] = cache.cache.graphs[graph]['features'];
		data['allograph_id'] = cache.cache.graphs[graph]['allograph_id'];
		data['hand_id'] = cache.cache.graphs[graph]['hand_id'];
		data['hands'] = cache.cache.graphs[graph]['hands'];
		if (annotator.boxes_on_click) {
			refresh_dialog(id, data, selectedFeature, callback);
		}
	}
}


function refresh_features_dialog(features, dialog) {
	var s = '<ul>';
	if (!$.isEmptyObject(features)) {
		for (i = 0; i < features.length; i++) {
			var component = features[i]['name'];
			s += "<li class='component'><b>" + component + "</b></li>";
			for (j = 0; j < features[i]['feature'].length; j++) {
				s += "<li class='feature'>" + (features[i]['feature'][j]) + "</li>";
			}
		}
	} else {
		s += "<li class='component'>This graph has not yet been described.</li>";
	}
	s += "</ul>";
	dialog.html(s);
}

function refresh_dialog(dialog_id, data, selectedFeature, callback) {

	var can_edit = $('#development_annotation').is(':checked');
	var dialog = $('#dialog' + dialog_id);

	if (can_edit) {

		if (annotator.selectedAnnotations.length > 1) {
			var selected = [];

			for (var g = 0; g < annotator.selectedAnnotations.length; g++) {
				selected.push(annotator.selectedAnnotations[g].graph);
			}

			data['allographs'] = common_components(selected, annotator.cacheAnnotations.cache, data['allographs']);
		}

		update_dialog('annotator_', data, annotator.selectedAnnotations, function(s) {

			$('#id_internal_note').remove();
			$('#id_display_note').remove();

			var display_note = $('<textarea>');
			display_note.attr('id', 'id_display_note').attr('name', 'display_note').addClass('feature_containers form-control').data('hidden', true).val(selectedFeature.display_note);

			var internal_note = $('<textarea>');
			internal_note.attr('id', 'id_internal_note').attr('name', 'internal_note').addClass('feature_containers form-control').data('hidden', true).val(selectedFeature.internal_note);

			s += "<p id='label_display_note' class='component_labels' data-id='id_display_note'><b>Display Note</b></p>";
			s += "<p id='label_internal_note' class='component_labels' data-id='id_internal_note'><b>Internal Note</b></p>";

			dialog.html(s);

			$('#label_display_note').after(display_note);
			$('#label_internal_note').after(internal_note);

			var check_all = $('.check_all');
			check_all.click(function(event) {
				var checkboxes = $(this).parent().parent().next().find('input[type=checkbox]');
				checkboxes.attr('checked', true);
				event.stopPropagation();
			});

			var uncheck_all = $('.uncheck_all');
			uncheck_all.click(function(event) {
				var checkboxes = $(this).parent().parent().next().find('input[type=checkbox]');
				checkboxes.attr('checked', false);
				event.stopPropagation();
			});

			var set_by_default = dialog.find('.set_by_default');
			set_by_default.on('click', function(event) {
				var component_id = $(this).data('component');
				var allograph = $('#panelImageBox .allograph_form').val();
				check_features_by_default(component_id, allograph, annotator.cacheAnnotations.cache);
				event.stopPropagation();
			});

			var set_all_by_default = $('.set_all_by_default');
			set_all_by_default.on('click', function(event) {
				var components = [];
				var allograph = $('#panelImageBox .allograph_form').val();

				for (var i in annotator.cacheAnnotations.cache.allographs) {
					for (var j = 0; j < annotator.cacheAnnotations.cache.allographs[i].length; j++) {
						var component = annotator.cacheAnnotations.cache.allographs[i][j].id;
						components.push(component);
					}
				}

				for (var c in components) {
					check_features_by_default(components[c], allograph, annotator.cacheAnnotations.cache);
				}

				event.stopPropagation();
			});

			var component_labels = dialog.find('.component_labels');
			component_labels.click(function() {
				var component = $(this);
				var div = $("#" + $(this).data('id'));
				if (!div.data('hidden')) {
					div.slideUp().data('hidden', true);
					component.next('.checkboxes_div').hide();
					component.find('.arrow_component').removeClass('fa-angle-double-up').addClass('fa-angle-double-down');
				} else {
					div.slideDown().data('hidden', false);
					component.next('.checkboxes_div').show();
					component.find('.arrow_component').removeClass('fa-angle-double-down').addClass('fa-angle-double-up');
				}
			});

			var annotation;
			var features = annotator.vectorLayer.features;
			for (var i = 0; i < features.length; i++) {
				for (var j in annotator.annotations) {
					if (annotator.annotations[j].graph == features[i].graph) {
						annotation = annotator.annotations[j];
					}
				}
			}
			var feature_checkboxes = $(".features_box");
			feature_checkboxes.on('change', function() {
				var value = $(this).val();
				if (annotation.state == 'Insert') {
					var index = annotation.features.indexOf(value);
					if (index < 0) {
						annotation.features.push(value);
					} else {
						annotation.features.splice(index, 1);
					}
				}
			});
		});

		if (callback) {
			callback();
		}

	} else {

		var features = data['features'];
		refresh_features_dialog(features, dialog);

	}
}


/**
 * Some fields are stored in the database as key:value. This function returns
 * the key.
 */

function getKeyFromObjField(obj, field) {
	var key = null;

	if (obj[field]) {
		key = obj[field];
		key = key.substring(0, key.indexOf('::'));
	}
	return key;
}

/**
 * This function returns the value.
 */

function getValueFromObjField(obj, field) {
	var value = null;
	if (obj[field]) {
		value = obj[field];
		value = value.substring(value.indexOf('::') + 1);
	}
	return value;
}



function highlight_vectors() {

	var allograph_form_id = $('#panelImageBox .allograph_form').attr('id');
	$('#' + allograph_form_id + '_chzn').find('.active-result').on('mouseover', function() {
		var text = $(this).text();
		var features = annotator.vectorLayer.features;
		for (i = 0; i < features.length; i++) {
			if (features[i].feature == text) {
				features[i].originalColor = features[i].style.fillColor;
				features[i].originalWidth = 2;
				features[i].style.strokeColor = 'red';
				features[i].style.strokeWidth = 6;
			}
		}
		annotator.vectorLayer.redraw();
		restoreFullscreenPositions();
	});

	$('#' + allograph_form_id + '_chzn').find('.active-result').on('mouseout', function() {
		var text = $(this).text();
		var features = annotator.vectorLayer.features;
		for (i = 0; i < features.length; i++) {
			if (features[i].feature == text) {
				features[i].style.strokeColor = features[i].originalColor;
				features[i].style.strokeWidth = features[i].originalWidth;
			}
		}
		annotator.vectorLayer.redraw();
		restoreFullscreenPositions();
	});

}

function highlight_unsaved_vectors(button) {
	var features = annotator.unsaved_annotations;
	var color = "#fe2deb";
	for (i = 0; i < features.length; i++) {
		features[i].feature.originalColor = '#ee9900';
		if (features[i].feature.style) {
			features[i].featureoriginalWidth = 2;
			features[i].feature.style.strokeColor = color;
			features[i].feature.style.fillColor = color;
		} else {
			features[i].feature.style = {};
			features[i].feature.fillopacity = 0.3;
			features[i].featureoriginalWidth = 2;
			features[i].feature.style.strokeColor = color;
			features[i].feature.style.fillColor = color;
		}
	}
	annotator.vectorLayer.redraw();
	button.addClass('active');
}


function unhighlight_unsaved_vectors(button) {
	var features = annotator.unsaved_annotations;
	for (i = 0; i < features.length; i++) {
		features[i].feature.style.strokeColor = features[i].feature.originalColor;
		features[i].feature.style.fillColor = features[i].feature.originalColor;
		features[i].feature.style.strokeWidth = features[i].feature.originalWidth;
	}
	annotator.vectorLayer.redraw();
	button.removeClass('active');
}

function trigger_highlight_unsaved_vectors() {
	$('.number_unsaved_allographs').on('click', function() {
		if (!$(this).hasClass('active')) {
			highlight_unsaved_vectors($(this));
		} else {
			unhighlight_unsaved_vectors($(this));
		}
	});

	/*
	$('.number_unsaved_allographs').on('mouseover', function() {
		highlight_unsaved_vectors($(this));
	});

	$('.number_unsaved_allographs').on('mouseout', function() {
		unhighlight_unsaved_vectors($(this));
	});
	*/

}



/**
 * Displays an alert for each error in the Ajax response (json).
 * Returns true only if data is invalid (contains error or empty).
 *
 * @param data
 *              JSON response from the server
 *              E.g. {'errors': ['allograph: This field is required.',
 *              'hand: This field is required.'], 'success': False}
 */

function handleErrors(data) {
	if (data && 'success' in data && data.success) return false;
	// something is not right
	var message = 'Internal error: the AJAX response is empty';
	if (data) {
		message = 'Internal error: no "success" in AJAX response';
		if ('success' in data) {
			message = '';
			if (!data.success) {
				message = 'Unknown error.';
				if ('errors' in data) {
					message = '';
					for (var i in data.errors) {
						message += '<p>' + data.errors[i] + '</p>';
					}
				}
			}
		}
	}
	console.warn(message);
	if (message) {
		updateStatus(message, 'danger');
	}

	return (message.length > 0);
}

/**
 * Updates the status message and style of the last operation.
 *
 * @param msg
 *              Status message to display.
 * @param status
 *              Either 'error', 'success' or ''
 */

DigipalAnnotator.prototype.removeDuplicate = function(element, attribute, text) {
	var seen = {};
	var txt;
	$(element).each(function() {
		if (text) {
			txt = $(this).text();
			attribute = null;
		} else {
			txt = $(this).attr(attribute);
		}
		if (seen[txt])
			$(this).remove();
		else
			seen[txt] = true;
	});
};


/**
 * Saves an annotation for the currently selected feature.
 */
DigipalAnnotator.prototype.saveAnnotation = function(ann, allographs_page) {

	if (!ann) {
		ann = null;
	}

	if (typeof allographs_page == 'undefined') {
		allographs_page = false;
	}

	if (this.selectedAnnotations.length) {
		this.selectedAnnotations.reverse();
	}

	updateStatus('Saving Annotation...', 'warning');

	var image_id = annotator.image_id;
	var graphs = [],
		vector = {}, geoJson;
	var feature;
	var data = make_form();
	var url = annotator.absolute_image_url + 'save';
	var cache = this.cacheAnnotations.cache;
	if (allow_multiple() && this.selectedAnnotations.length > 1 && !allographs_page) {

		var msg = 'You are about to save ' + this.selectedAnnotations.length + ' annotations. Do you want to continue?';

		if (confirm(msg)) {
			for (var i = 0; i < this.selectedAnnotations.length; i++) {

				feature = this.selectedAnnotations[i];
				geoJson = annotator.format.write(feature);

				vector = {};
				vector['id'] = feature.graph;
				vector['image'] = image_id;
				vector['geoJson'] = geoJson;
				vector['vector_id'] = feature.id;
				graphs.push(vector);

			}

			url = '/digipal/api/graph/save/' + JSON.stringify(graphs) + '/';
			save(url, graphs, data, ann, data.features);

		}

	} else {

		if (allographs_page) {

			for (ind2 = 0; ind2 < ann.length; ind2++) {
				geoJson = annotator.format.write(ann[ind2]);
				graphs.push({
					'id': ann[ind2].graph,
					'image': image_id,
					'geoJson': geoJson,
					'vector_id': ann[ind2].id
				});
			}

			url = '/digipal/api/graph/save/' + JSON.stringify(graphs) + '/';
			save(url, graphs, data, ann, data.features);

		} else {
			if (this.selectedFeature) {
				feature = this.selectedFeature;
				geoJson = annotator.format.write(feature);

				vector = {};
				vector['id'] = feature.graph;
				vector['image'] = image_id;
				vector['geoJson'] = geoJson;
				vector['vector_id'] = feature.id;

				graphs.push(vector);

				url = '/digipal/api/graph/save/' + JSON.stringify(graphs) + '/';
				save(url, graphs, data, ann, data.features);

			}

		}
	}

	var tab_link = $('a[data-target="#allographs"]');
	var f = annotator.vectorLayer.features;
	var y = 0;
	while (y < f.length && f[y].attributes.saved === 1) {
		y++;
	}

	tab_link.html('Annotations (' + y + ')');

};


/**
 * Deletes the annotation for the selected feature.
 *
 * @param layer
 *              The feature's layer.
 * @param feature
 *              The feature to delete the annotation for.
 */
DigipalAnnotator.prototype.deleteAnnotation = function(layer, feature, number_annotations) {
	var _self = this;
	var msg;
	if (typeof number_annotations == 'undefined' || !number_annotations) {
		msg = 'You are about to delete this annotation. It cannot be restored at a later time! Continue?';
	} else {
		var plural = number_annotations > 1;
		if (!plural) {
			msg = 'You are about to delete ' + number_annotations + ' annotation. It cannot be restored at a later time! Continue?';
		} else {
			msg = 'You are about to delete ' + number_annotations + ' annotations. They cannot be restored at a later time! Continue?';
		}
	}

	var doDelete = confirm(msg);
	if (doDelete) {
		if (feature !== null && feature !== undefined) {
			delete_annotation(layer, feature, number_annotations);
		}
	}

};


/**
 * Deletes the annotation for the feature with the given id.
 *
 * @param id
 *              The feature id.
 */

function deleteAnnotationByFeatureId(id) {
	annotator.selectFeatureByIdAndCentre(id);
	annotator.deleteAnnotation(annotator.vectorLayer, annotator.vectorLayer.getFeatureById(id));
}

function delete_annotation(layer, feature, number_annotations) {
	var featureId = feature.id;
	var temp = feature;
	updateStatus('Deleting annotations');
	layer.destroyFeatures([feature]);
	var url = annotator.absolute_image_url + 'delete/' + featureId + '/';
	$.ajax({
		url: url,
		data: '',
		error: function(xhr, textStatus, errorThrown) {
			alert('Error: ' + textStatus);
			throw new Error(textStatus);
		},
		success: function(data) {
			if (!handleErrors(data)) {
				if (number_annotations > 1) {
					updateStatus('Annotations deleted.', 'success');
				} else {
					updateStatus('Annotation deleted.', 'success');
				}

				var allograph = $('#panelImageBox .allograph_form option:selected').text();
				var allograph_id = $('#panelImageBox .allograph_form').val();
				if ($('.tab-pane.active').attr('id') == 'annotator') {
					refresh_letters_container(allograph, allograph_id, true);
				}
				if (temp['state'] == 'Insert') {
					var element = $('.number_unsaved_allographs');
					var number_unsaved = element.html();
					var annotations = annotator.unsaved_annotations;
					for (var i = 0; i < annotations.length; i++) {
						if (annotations[i].feature.id == feature.id) {
							annotations.splice(i, 1);
							break;
						}
					}
					element.html(annotations.length);
					temp = null;
				}

				var boxes = $(".dialog_annotations");
				if (boxes.length) {
					boxes.remove();
				}

				var tab_link = $('a[data-target="#allographs"]');
				var f = annotator.vectorLayer.features;
				var y = 0;
				while (y < f.length && f[y].attributes.saved === 1) {
					y++;
				}

				tab_link.html('Annotations (' + y + ')');

				annotator.has_changed = true;
			}
		}
	});
}

function serializeObject(obj) {
	var o = {};
	var a = obj.serializeArray();
	$.each(a, function() {
		if (o[obj.name]) {
			if (!o[obj.name].push) {
				o[obj.name] = [o[obj.name]];
			}
			o[obj.name].push(obj.value || '');
		} else {
			o[obj.name] = obj.value || '';
		}
	});
	return o;
}



function make_form() {

	var modal;

	if ($('.tab-pane.active').attr('id') == 'annotator') {
		select_allograph = $('#panelImageBox');
		modal = $('.dialog_annotations');
	} else {
		select_allograph = $('.myModal');
		modal = select_allograph;
	}

	var form = select_allograph.find('.frmAnnotation');
	var obj = {};
	var array_values_checked = [],
		array_values_unchecked = [];
	var features = {};
	var has_features = false;

	if (modal.find('.features_box').length) {
		modal.find('.features_box').each(function() {
			if ($(this).is(':checked') && !$(this).prop('indeterminate')) {
				array_values_checked.push($(this).val());
				has_features = true;
			} else if (!$(this).is(':checked') && !$(this).prop('indeterminate')) {
				array_values_unchecked.push($(this).val());
			}
		});
	}

	var features_labels = [];
	var components = modal.find('.feature_containers');
	$.each(components, function() {
		if ($(this).find('.features_box:checked').length) {
			var component_id = $(this).attr('id');
			var component_name = $('[data-id="' + component_id + '"]');
			var component = $.trim(component_name.children('b').text());
			var features_labels_array = [];
			var features_input = $(this).find('.features_box:checked');

			var f_id, f_value, label_element;
			$.each(features_input, function() {
				f_id = $(this).attr('id');
				f_value = $(this).val();
				label_element = $('label[for="' + f_id + '"');
				features_labels_array.push(label_element.text());
			});

			features_labels.push({
				'feature': features_labels_array,
				'name': component,
				'component_id': parseInt(f_value.split(':')[0], 10)
			});
		}
	});


	obj['feature'] = array_values_checked;

	var form_serialized = form.serialize();
	var s = '';

	for (i = 0; i < array_values_checked.length; i++) {
		s += '&feature=' + array_values_checked[i];
	}

	for (i = 0; i < array_values_unchecked.length; i++) {
		s += '&-feature=' + array_values_unchecked[i];
	}

	form_serialized += s;

	if ($('#id_display_note').val()) {
		form_serialized += "&display_note=" + $('#id_display_note').val();
	}

	if ($('#id_internal_note').val()) {
		form_serialized += "&internal_note=" + $('#id_internal_note').val();
	}

	return {
		'form_serialized': form_serialized,
		'features_labels': features_labels
	};
}


/**
 * Executes an Ajax call to save a feature/annotation.
 *
 * @param url
 *              The save url.
 * @param feature
 *              The feature.
 * @param data
 *              Additional data for the annotation.
 */

function save(url, graphs, data, ann, features) {
	console.log(graphs)
	var save_annotations = $.ajax({
		url: url,
		data: data['form_serialized'],
		beforeSend: function() {
			updateStatus('Saving annotation ...');
		},
		error: function(xhr, textStatus, errorThrown) {
			updateStatus(textStatus, 'error');
			// annotator.setSavedAttribute(feature, Annotator.UNSAVED, false);
		},
		success: function(data) {
			console.log(data);
			if (!handleErrors(data)) {
				updateStatus('Saved annotation.', 'success');

				if ($('.tab-pane.active').attr('id') == 'annotator') {
					select_allograph = $('#panelImageBox');
				} else {
					select_allograph = $('.modal-body');
				}

				var allograph = select_allograph.find('.allograph_form option:selected').text();
				var allograph_id = select_allograph.find('.allograph_form').val();

				if ($('.tab-pane.active').attr('id') == 'annotator') {
					refresh_letters_container(allograph, allograph_id, true);
				}

				var f = annotator.vectorLayer.features;
				var f_length = annotator.vectorLayer.features.length;
				var feature, id, temp;
				var form_serialized = data;

				var new_graphs = data['graphs'];

				for (var i = 0; i < new_graphs.length; i++) {

					/*	Updating cache	*/
					var new_graph = new_graphs[i].graph,
						new_allograph = new_graphs[i].allograph_id;
					annotator.cacheAnnotations.update('graph', new_graph, new_graphs[i]);
					annotator.cacheAnnotations.update('allograph', new_allograph, new_graphs[i]);
					allographsPage.cache.update('graph', new_graph, new_graphs[i]);
					allographsPage.cache.update('allograph', new_allograph, new_graphs[i]);

					/*	Updating annotator features	*/
					for (var feature_ind = 0; feature_ind < f_length; feature_ind++) {
						if (f[feature_ind].graph == new_graphs[i].graph) {
							feature = f[feature_ind];
							id = feature.id;
							feature.feature = allograph;
							annotator.setSavedAttribute(feature, Annotator.SAVED, false);

							var color;

							feature.features = new_graphs[i].features;
							var num_features = new_graphs[i].features.length;
							var element = $('.number_unsaved_allographs');
							var number_unsaved = element.html();
							var unsaved_annotations = annotator.unsaved_annotations;

							for (var ind = 0; ind < unsaved_annotations.length; ind++) {
								if (unsaved_annotations[ind].feature.id == feature.id) {
									unsaved_annotations.splice(ind, 1);
									ind--;
									break;
								}
							}

							for (var ann in annotator.annotations) {
								if (annotator.annotations[ann].graph == feature.graph) {
									annotator.annotations[ann].hidden_allograph = new_allograph + '::' + $.trim(allograph.split(',')[1]);
									annotator.annotations[ann].feature = allograph;
								}
							}

							if (num_features > 0) {
								color = 'green';
								feature.described = true;
								feature.num_features = feature.features.length + 1;
							} else {
								color = '#ee9900';
								feature.described = false;
								feature.num_features = 0;
							}

							stylize(feature, color, color, 0.4);
							feature.style.originalColor = color;
							feature.style.strokeWidth = 2;
							feature.stored = true;
							feature.last_feature_selected = null;
							element.html(annotations.length);

							var n = 0,
								d = 0;
							for (g = 0; g < f_length; g++) {
								if (f[g].feature == feature.feature && f[g].stored) {
									n++;
								}

								if (f[g].stored) {
									d++;
								}
							}

							$(".number_annotated_allographs .number-allographs").html(n);

							$('[data-target="#allographs"]').html('Annotations (' + d + ')');
						}
					}
				}



				annotator.selectedAnnotations = [];

			}

		},
		complete: function() {

			annotator.has_changed = true;
		}
	});
}

function registerEvents() {
	if (annotator.isAdmin == 'True') {
		annotator.events = true;
		var paths = $('#OpenLayers_Layer_Vector_27_vroot').find("path");
		/*

			Uncomment to activate mouseover and mouseout events
			for displaying popups when a graphs has a display note field

		*/

		/*
		paths.unbind().mouseenter(function() {
			var features = annotator.vectorLayer.features;
			for (var i = 0; i < features.length; i++) {
				if ($(this).attr('id') == features[i].geometry.id) {
					if (features[i].display_note) {
						createPopup(features[i]);
					}
				}
			}
		}).mouseleave(function() {
			var features = annotator.vectorLayer.features;
			for (var i = 0; i < features.length; i++) {
				if (features[i].popup) {
					deletePopup(features[i]);
				}
			}
		});
		*/

		paths.unbind().dblclick(function(event) {

			if (annotator.boxes_on_click) {
				boxes_on_click = true;
			}

			if (annotator.selectFeature.active && !annotator.boxes_on_click) {

				annotator.boxes_on_click = true;
				var boxes_on_click_element = $("#boxes_on_click");
				boxes_on_click_element.prop('checked', true);
				var boxes_on_click = false;
				var annotation;

				for (var a in annotator.annotations) {
					if (annotator.annotations[a].graph == annotator.selectedFeature.graph) {
						annotation = annotator.annotations[a];
					}
				}
				showBox(annotation, function() {
					if (!boxes_on_click) {
						annotator.boxes_on_click = false;
						boxes_on_click_element.prop('checked', false);
						restoreFullscreenPositions();
					}
				});

			}
			showBox(annotation, function() {
				if (!boxes_on_click) {
					annotator.boxes_on_click = false;
					boxes_on_click_element.prop('checked', false);
				}
			});

		});
	}

}

function disable_annotation_tools() {
	var editorial, delete_icon, edit;

	if ($('.olControlEditorialFeature').length) {
		editorial = $('.olControlEditorialFeature');
	} else {
		$('.olControlEditorialFeatureItemActive');
	}

	var save_icon = $('.olControlSaveFeaturesItemInactive');

	if ($('.olControlDeleteFeature').length) {
		delete_icon = $('.olControlDeleteFeature');
	} else {
		delete_icon = $('.olControlDeleteFeatureItemActive');
	}

	if ($('.olControlTransformFeature').length) {
		edit = $('.olControlTransformFeature');
	} else {
		edit = $('.olControlTransformFeatureItemActive');
	}

	editorial.fadeOut();
	delete_icon.fadeOut();
	save_icon.fadeOut();
	edit.fadeOut();
}

function enable_annotation_tools() {

	var editorial, delete_icon, edit;

	if ($('.olControlEditorialFeature').length) {
		editorial = $('.olControlEditorialFeature');
	} else {
		$('.olControlEditorialFeatureItemActive');
	}

	var save_icon = $('.olControlSaveFeatures');

	if ($('.olControlDeleteFeature').length) {
		delete_icon = $('.olControlDeleteFeature');
	} else {
		delete_icon = $('.olControlDeleteFeatureItemActive');
	}

	if ($('.olControlTransformFeatureItemInactive').length) {
		edit = $('.olControlTransformFeatureItem');
	} else {
		edit = $('.olControlTransformFeatureItemActive');
	}

	editorial.fadeIn();
	delete_icon.fadeIn();
	save_icon.fadeIn();
	edit.fadeIn();
}

/**
 * Loads existing vectors into the vectors layer.
 *
 * @param layer
 *              The layer where the vectors will be rendered.
 */

/**
 * Loads existing annotations.
 */
DigipalAnnotator.prototype.loadAnnotations = function() {
	var _self = this;
	//var selectedFeature = this.selectedFeature;
	var url = this.url_annotations;
	var json = $.getJSON(url, function(data) {
		_self.annotations = data;
		//showAnnotationsOverview(data);
	});

};

/* FullScreen Mode */

DigipalAnnotator.prototype.full_Screen = function() {
	var map = $('#map');
	var panel = $('#panelImageBox');
	var toolbar = $('#toolbar');
	var map_size;
	if (!(this.fullScreen.active)) {

		$('html, body').animate({
			scrollTop: map.position().top
		}, 0);

		this.fullScreen.activate();
		map.addClass("fullScreenMap");

		$(document).keyup(function(e) {
			if (e.keyCode == 27) {
				map.removeClass('fullScreenMap');
				panel.removeClass('fullScreenPanel');
				toolbar.removeClass('mapHorizontalFullscreen');
				toolbar.removeClass('fullScreenToolbarVertical');
				annotator.fullScreen.deactivate();
			}
		});

		$('.olControlFullScreenFeatureItemInactive').attr('title', 'Deactivate Full Screen');
		panel.addClass('fullScreenPanel');


		var input_toolbar_position = $("input[name='toolbar_position']:checked");
		if (input_toolbar_position.val() != 'Vertical') {
			toolbar.addClass('mapHorizontalFullscreen');
			toolbar.removeClass('fullScreenToolbarVertical');
		} else {
			toolbar.removeClass('mapHorizontalFullscreen');
			toolbar.addClass('fullScreenToolbarVertical');
		}


	} else {
		this.fullScreen.deactivate();
		map.removeClass('fullScreenMap');

		$('.olControlFullScreenFeatureItemInactive').attr('title', 'Activate Full Screen');
		panel.removeClass('fullScreenPanel');
		toolbar.removeClass('mapHorizontalFullscreen');
		toolbar.removeClass('fullScreenToolbarVertical');

		$('html, body').animate({
			scrollTop: map.position().top
		}, 0);

	}

	restoreFullscreenPositions();
};


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

/**
 * Turns on keyboard shortcuts for the controls.
 */

var toggleAll = function(activeControls, active) {
	for (i = 0; i < activeControls.length; i++) {
		if (activeControls[i].title) {
			if (activeControls[i].displayClass != 'olControlFullScreenFeature' && activeControls[i].displayClass != "olControlEditorialFeature") {
				if (active) {
					activeControls[i].activate();
				} else {
					activeControls[i].deactivate();
				}
			}
		}
	}
};

DigipalAnnotator.prototype.activateKeyboardShortcuts = function() {
	var _self = this;

	$(document).bind('keydown', function(event) {
		activeControls = _self.map.getControlsBy('active', true);
		var code = (event.keyCode ? event.keyCode : event.which);
		if (code == 85) {
			var button = $('.number_unsaved_allographs');
			var features = annotator.unsaved_annotations;
			if (!button.hasClass('active')) {
				highlight_unsaved_vectors(button);
			} else {
				unhighlight_unsaved_vectors(button);
			}
		}

		if (event.shiftKey && annotator.isAdmin == 'True') {
			var isFocus = $('input').is(':focus') || $('textarea').is(':focus');
			if (!isFocus) {
				switch (code) {
					case 77:
						toggleAll(activeControls, false);
						_self.modifyFeature.activate();
						break;
					case 8:
						toggleAll(activeControls, false);
						_self.deleteFeature.activate();
						break;
					case 77:
						toggleAll(activeControls, false);
						_self.transformFeature.activate();
						break;
					case 68:
						toggleAll(activeControls, false);
						_self.rectangleFeature.activate();
						break;
					case 71:
						toggleAll(activeControls, false);
						_self.selectFeature.activate();
						break;
					case 87:
						toggleAll(activeControls, false);
						_self.dragFeature.activate();
						break;
					case 90:
						toggleAll(activeControls, false);
						_self.zoomBoxFeature.activate();
						break;
					case 83:
						_self.saveButton.trigger();
						break;
					case 70:
						_self.full_Screen();
						break;
					case 38:
						annotator.map.moveByPx(0, -60);
						annotator.vectorLayer.redraw();
						restoreFullscreenPositions();
						break;
					case 40:
						annotator.map.moveByPx(0, 60);
						annotator.vectorLayer.redraw();
						restoreFullscreenPositions();
						break;
					case 37:
						annotator.map.moveByPx(-60);
						annotator.vectorLayer.redraw();
						restoreFullscreenPositions();
						break;
					case 39:
						annotator.map.moveByPx(60);
						annotator.vectorLayer.redraw();
						restoreFullscreenPositions();
						break;
					case 187:
						annotator.vectorLayer.map.zoomIn();
						break;
					case 189:
						annotator.vectorLayer.map.zoomOut();
						break;
				}
			}
		}
	});
};

function restoreFullscreenPositions() {
	var annotations_layer = $('#OpenLayers_Layer_Vector_27_svgRoot');
	annotations_layer.attr('width', $(window).width())
		.attr('height', $(window).height())
		.attr('viewport', "0 0 " + $(window).width() + " " + $(window).height());

	annotations_layer[0].setAttribute('viewBox', "0 0 " + $(window).width() + " " + $(window).height());
}