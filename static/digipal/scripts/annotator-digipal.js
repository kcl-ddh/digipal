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
	this.selectFeature.panel_div.title = 'Select (shift + g)';
	this.zoomBoxFeature.panel_div.title = 'Zoom (shift + z)';
	this.saveButton.panel_div.title = 'Save (shift + s)';
	this.selectedAnnotations = [];
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

	if (!annotator.events) {
		registerEvents();
	}

	var group_button = $('.link_graphs');
	if (self.selectedFeature.linked_to && !$.isEmptyObject(self.selectedFeature.linked_to[0]) && allow_multiple()) {
		$.each(self.selectedFeature.linked_to[0], function(index, value) {
			if (value) {
				self.showAnnotation(value);
				self.selectedAnnotations.push(value);
				var msg = self.selectedAnnotations.length + ' annotation selected';
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
		var msg = self.selectedAnnotations.length + ' annotation selected';
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

		var msg = this.selectedAnnotations.length + ' annotations selected';
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
		feature.style.fillColor = '#ee9900';
		var color;
		if (feature.state == 'Insert' && $('.number_unsaved_allographs').hasClass('active') && !feature.stored) {
			if (feature.features.length) {
				color = 'blue';
			} else {
				color = 'red';
			}
			feature.style.strokeColor = color;
		} else {
			feature.style.strokeColor = '#ee9900';
		}

	}

	this.vectorLayer.redraw();

	if (this.selectedAnnotations.length) {
		this.selectedFeature = this.selectedAnnotations[0];
	} else {
		this.selectedFeature = null;
	}

	$(".number_annotated_allographs .number-allographs").html(0);

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
		allograph_label.html("Group (<span class='num_linked'>" + num_linked + '</span>) <i title="Show group elements" class="icon-th-list show_group" data-hidden="true" />').css('cursor', 'pointer').data('hidden', true);

		allograph_label.unbind().click(function() {
			var element = "<div class='elements_linked'>";

			$.each(elements_linked, function() {
				this.feature = this.feature || 'Undefined annotation';
				element += "<p data-id='" + this.id + "'>" + this.feature + "<i title='ungroup' class='pull-right icon-remove ungroup' data-id='" + this.id + "' /></p>";
			});

			element += '</div>';


			if ($('.elements_linked').length) {
				$('.elements_linked').replaceWith(element);
			} else {
				$('.ui-dialog .frmAnnotation').prepend(element);
			}

			var el_link = $('.elements_linked');
			if ($(this).data('hidden')) {
				el_link.slideDown();
				$(this).data('hidden', false);
			} else {
				el_link.slideUp(500);
				$(this).data('hidden', true);
			}

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
			}).on('click', function() {
				var id = $(this).data('id');
				var temp = annotator.selectedFeature.linked_to[0][id];
				$.each(annotator.selectedFeature.linked_to[0], function() {
					console.log(this.linked_to[0][id]);
					delete this.linked_to[0][id];
					this.linked_to[0][id] = temp;
				});
				annotator.selectFeatureByIdAndZoom(id);
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
			attribute2 = features[i].feature;
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
					if (a.is(':checked') && a.val() == attribute2) {
						if ($(checkboxes).val() == attribute) {
							features[i].style.fillOpacity = 0.4;
							features[i].style.strokeOpacity = 1;
						}
					}
				}
			}
		} else {
			attribute = features[i].feature;
			attribute2 = features[i].hand;
			hand = $('#hand_input_' + attribute2);
			allograph = $('#hand_input_' + attribute2);
			if (!($(checkboxes).is(':checked'))) {
				if ($(checkboxes).val() == attribute && features[i].hand == hand.val()) {
					features[i].style.fillOpacity = 0;
					features[i].style.strokeOpacity = 0;
				}
			} else {
				if ($(checkboxes).val() == attribute && features[i].hand == hand.val() && hand.is(':checked')) {
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
		var features = annotator.vectorLayer.features;
		var features_length = features.length;
		var n = 0;
		for (var i = 0; i < features_length; i++) {
			if (features[i].feature == feature.feature && features[i].stored) {
				n++;
			}
		}
		$(".number_annotated_allographs .number-allographs").html(n);
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
		showBox(annotation);
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
	annotator.annotations = [];
	annotator.selectedFeature = null;
	annotator.selectedAnnotations = [];
	$('div[role=dialog').remove();
	var request = $.getJSON('annotations/', function(data) {
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
		var features_request = $.getJSON('vectors/');
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
		});
	});
};

/**

 * Updates the feature select according to the currently selected allograph.

 */
function updateFeatureSelect(currentFeatures, id) {
	var features = annotator.vectorLayer.features;
	var allograph_selected, select_allograph;
	if ($('.tab-pane.active').attr('id') == 'annotator') {
		select_allograph = $('#panelImageBox .allograph_form');
	} else {
		select_allograph = $('.modal-body .allograph_form');
	}
	var annotations = annotator.annotations;
	if ($.isNumeric(currentFeatures)) {
		allograph_selected = currentFeatures;
	} else {
		if (typeof currentFeatures == "undefined" || typeof currentFeatures == "null" || !currentFeatures) {
			if (select_allograph.val()) {
				allograph_selected = select_allograph.val();
			}
		} else {
			$.each(annotations, function() {
				if (currentFeatures.feature == this.feature) {
					allograph_selected = this.hidden_allograph.split('::')[0];
				}
			});
		}
	}

	if (annotator.isAdmin === "True") {
		var allograph = select_allograph.val();
		var url = annotator.absolute_image_url + 'allograph/' + allograph_selected + '/features/';
		var s = '';

		if (typeof allograph_selected != 'undefined' && allograph_selected) {
			var get_features = $.getJSON(url);
			get_features.done(function(data) {
				$.each(data, function(idx) {
					component = data[idx].name;
					component_id = data[idx].id;
					var features = data[idx].features;
					s += "<div class='component_labels' data-id='component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component icon-arrow-down'></span></b>";

					s += "<div class='checkboxes_div btn-group'><span data-component = '" + component_id + "' class='check_all btn btn-mini'>All</span> <span data-component = '" + component_id + "' class='btn btn-mini uncheck_all'>Clear</span></div></div>";

					s += "<div id='component_" + component_id + "' data-hidden='false' class='feature_containers'>";

					$.each(features, function(idx) {
						var value = component_id + '::' + features[idx].id;
						var id = component_id + '_' + features[idx].id;

						if (annotator.selectedFeature !== undefined && annotator.selectedFeature !== null && annotator.selectedFeature.state != 'Insert') {
							s += "<p><input name='checkboxes[]' id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "'/>";
							s += "<label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + id + "'>" + features[idx].name + "</label>";
						} else {
							var array_features_owned = annotator.selectedFeature.features;
							if (array_features_owned.indexOf(value) >= 0) {
								s += "<p><input name='checkboxes[]' id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "' checked /> ";
							} else {
								s += "<p><input name='checkboxes[]' id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "' /> ";
							}
							s += "<label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + id + "'>" + features[idx].name + "</label>";
						}

					});
					s += "</div>";
				});

				var dialog;
				if ($('.tab-pane.active').attr('id') == 'annotator') {
					dialog = $('#dialog' + id);
					if (dialog.parent().find(".number_annotated_allographs").length) {
						dialog.parent().find(".number_annotated_allographs .number-allographs").html(n);
					}

				} else {
					dialog = $('.modal-body');
				}

				if (!annotator.editorial.active) {
					if (annotator.selectedFeature.linked_to && !$.isEmptyObject(annotator.selectedFeature.linked_to[0])) {
						var num_linked = 0;
						elements_linked = [];
						for (var g in annotator.selectedFeature.linked_to[0]) {
							num_linked++;
							elements_linked.push(annotator.selectedFeature.linked_to[0][g]);
						}

						var allograph_label = $('.allograph_label');
						allograph_label.html("Group (<span class='num_linked'>" + num_linked + '</span>) <i title="Show group elements" class="icon-th-list show_group" data-hidden="true" />')
							.css('cursor', 'pointer')
							.data('hidden', true);

						allograph_label.unbind().click(function() {

							var element = "<div class='elements_linked'>";

							$.each(elements_linked, function() {
								element += "<p data-id='" + this.id + "'>" + this.feature + "<i title='ungroup' class='pull-right icon-remove ungroup' data-id='" + this.id + "' /></p>";
							});

							element += '</div>';

							if ($('.elements_linked').length) {
								$('.elements_linked').replaceWith(element);
							} else {
								$('.dialog_annotations').prepend(element);
							}

							var el_link = $('.elements_linked');
							if ($(this).data('hidden')) {
								el_link.slideDown();
								$(this).data('hidden', false);
							} else {
								el_link.slideUp(500);
								$(this).data('hidden', true);
							}

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
							}).on('click', function() {
								var id = $(this).data('id');
								annotator.selectFeatureById(id);
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

				dialog.find('.component_labels').click(function() {
					var div = $("#" + $(this).data('id'));
					if (div.data('hidden') === false) {
						div.slideUp().data('hidden', true);
						$(this).next('.checkboxes_div').hide();
						$(this).find('.arrow_component').removeClass('icon-arrow-up').addClass('icon-arrow-down');
					} else {
						div.slideDown().data('hidden', false);
						$(this).next('.checkboxes_div').show();
						$(this).find('.arrow_component').removeClass('icon-arrow-down').addClass('icon-arrow-up');
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

Function to get the features of a described allograph
@params feature selected, url
*/

function features_owned(selectedFeature, url) {
	var features = $.ajax({
		url: url,
		dataType: 'json',
		cache: false,
		type: 'GET',
		async: false,
		error: function(xhr, status, error) {
			console.warn('Error: ' + error);
		}
	});

	var array_features_owned = [];
	features.done(function(f) {
		for (var i = 0; i < f.length; i++) {
			for (var j = 0; j < f[i].feature.length; j++) {
				s = f[i].name;
				s += ':' + f[i].feature[j];
				array_features_owned.push(s);
			}
			s = '';
		}
	});
	return array_features_owned;
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

				var button = <span class='btn btn-small btn-primary number_annotated_allographs' data-feature = '" + selectedFeature.feature + "' title='Show all the images of this allograph'><i class= 'icon-eye-open'></i> <span class='number-allographs'></span></span>

				*/
				if (selectedFeature && !annotator.editorial.active) {
					title = "<span class='allograph_label'>" + selectedFeature.feature +
						"</span> <button data-hidden='true' class='url_allograph btn btn-mini'><i title='Share URL' class='fa fa-link' title='Share URL' data-toggle='tooltip'></i></button> <button class='to_lightbox btn btn-mini' data-graph = '" + selectedFeature.graph + "'><i data-toggle='tooltip' title='Add graph to collection' class='fa fa-folder-open'></i></button>";
					if (allow_multiple() && annotator.selectedAnnotations.length > 1) {
						title += " <button class='btn btn-mini link_graphs'>Group</button>";
					} else {
						title += " <button class='btn btn-mini link_graphs disabled' disabled>Group</button>";
					}
				} else if (!annotator.annotating) {
					title = "<input type='text' placeholder = 'Type name' class='name_temporary_annotation' /> <span style='margin-left: 8%;'><button data-hidden='true' class='url_allograph btn btn-mini pull-right'><i class='fa fa-link' data-toggle='tooltip'></i></button> ";

				} else {
					if (annotator.editorial.active) {
						title = "<span class='allograph_label'>Annotation</span>" +
							" <button data-hidden='true' class='url_allograph btn btn-mini'><i title='Share URL' class='fa fa-link' data-toggle='tooltip'></i></button> ";
						if (allow_multiple() && annotator.selectedAnnotations.length > 1) {
							title += " <button class='btn btn-mini link_graphs'>Group</button>";
						} else {
							title += " <button class='btn btn-mini link_graphs disabled' disabled>Group</button>";
						}
					} else {
						title = "<span class='allograph_label'>Annotation</span> <button data-hidden='true' class='url_allograph btn btn-mini'><i data-toggle='tooltip' title='Share URL' class='fa fa-link'></i></button> ";
						if (annotator.selectedFeature) {
							title += "<button class='to_lightbox btn btn-mini' data-graph = '" + annotator.selectedFeature.graph + "'><i data-toggle='tooltip' title='Add graph to collection' class='fa fa-folder-open'></i></button>";
						}
						if (allow_multiple() && annotator.selectedAnnotations.length > 1) {
							title += " <button class='btn btn-mini link_graphs'>Group</button>";
						} else {
							title += " <button class='btn btn-mini link_graphs disabled' disabled>Group</button>";
						}
					}
				}
			} else {
				if (selectedFeature) {
					title = "<span class='allograph_label'>" + selectedFeature.feature + "</span> <button data-hidden='true' class='url_allograph btn btn-mini'><i data-toggle='tooltip' title='Share URL' class='fa fa-link'></i></button> <button class='to_lightbox btn btn-mini' data-graph = '" + selectedFeature.graph + "'><i data-toggle='tooltip' title='Add graph to collection' class='fa fa-folder-open'></i></button>";
				} else {
					title = "<input type='text' placeholder = 'Type name' class='name_temporary_annotation' /> <span style='margin-left: 8%;'><button data-hidden='true' class='url_allograph btn btn-mini pull-right'><i title='Share URL' class='fa fa-link' data-toggle='tooltip'></i></button>";
				}
			}
			return title;
		},
		position: position()
	}).addClass('dialog_annotations');

	if (absolute_position) {
		dialog.parent().css({
			'position': 'fixed',
			'top': '30%',
			'left': '70%'
		});
	}

	if (annotator.isAdmin == "False" || !annotator.annotating) {
		$('.name_temporary_annotation').focus();
		$('.ui-dialog-title').on('click', function() {
			$('.name_temporary_annotation').focus();
		});
		annotator.selectedFeature.isTemporary = true;
	}

	if (typeof selectedFeature === "null" || typeof selectedFeature === "undefined") {
		updateFeatureSelect(null, id);
	} else {
		updateFeatureSelect(selectedFeature, id);
	}

	// Showing all the allographs of a given allograph
	dialog.parent().find('.number_annotated_allographs').click(function() {
		open_allographs($(this), true);
	});

	if (annotator.selectedFeature && !selectedFeature) {
		selectedFeature = annotator.selectedFeature.graph;
	}

	$('.to_lightbox').click(function() {
		if (!annotator.selectedFeature) {
			annotator.selectedFeature = annotator.selectedAnnotations[annotator.selectedAnnotations.length];
		}
		if (annotator.selectedFeature.linked_to && !$.isEmptyObject(annotator.selectedFeature.linked_to[0])) {
			var links = [];
			for (var l in annotator.selectedFeature.linked_to[0]) {
				links.push(annotator.annotations[annotator.selectedFeature.linked_to[0][l].graph]);
			}
			add_to_lightbox($(this), 'annotation', links, true);
		} else {
			add_to_lightbox($(this), 'annotation', selectedFeature, false);
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
	}).resizable({
		minHeight: "25%",
		minWidth: 300
	});

	var top_div = $("<div id='top_div_annotated_allographs'>");

	var number_allographs = $('.number-allographs');
	top_div.append("<span>" + allograph_value + "</span><i title='Close box' class='icon pull-right icon-remove close_top_div_annotated_allographs'></i>");

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
	var s;
	var panel = $('#panelImageBox');
	if (can_edit) {
		s = "<input type='hidden' name='allograph' id='hidden_allograph' /> <input type='hidden' id='hidden_hand' name='hand' />";
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

	} else {
		s = "<textarea class='textarea_temporary_annotation' placeholder='Type description here...'></textarea>";
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

	name_temporary_annotation.on('keydown', function() {
		annotator.selectedFeature.contentTitle = $(this).val();
	});

	content_temporary_annotation.on('keydown', function() {
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
	if (name_temporary_annotation.length) {
		$('.ui-dialog-title').css('margin-left', '-2.5%');
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
		$('.link_graphs').after(' <img src="/static/images/ajax-loader3.gif" id="url_allograph_gif" />');
		var url = $("<div class='allograph_url_div'>");
		var allograph_url, stored = false;
		var a = $('<a>');
		a.attr('target', '_tab');
		var title = $('.name_temporary_annotation').val();
		var desc = $('.textarea_temporary_annotation').val();

		// get annotations visibility status
		var getAnnotationsVisibility = $('#toggle-state-switch').bootstrapSwitch('state');
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
					return false;
				} else {
					$('#url_allograph_gif').fadeOut().remove();
					a.attr('href', resp.id);
					a.text(resp.id);
					button.data('url', resp.id);
					url.append(a);
					dialog.prepend(url);
				}
			});
		});

	} else {
		button.data('hidden', true);
		var url_allograph_element = dialog.parent().find('.allograph_url_div');
		url_allograph_element.fadeOut().remove();
	}
}

function showBox(selectedFeature) {

	var features = annotator.vectorLayer.features;
	var id = Math.random().toString(36).substring(7);
	if (annotator.boxes_on_click) {
		var dialog;
		var can_edit = $('#development_annotation').is(':checked');
		if (selectedFeature === null || typeof selectedFeature == "undefined") {
			create_dialog(null, id);
			fill_dialog(id, null);
			dialog = $('#dialog' + id);
			if (annotator.editorial.active && can_edit) {
				var s = '<label>Editorial Note</label>';
				s += '<textarea id="editorial_note" name="editorial_note" style="width:90%;height:40%;"></textarea>';
				s += '<label>Public Note</label>';
				s += '<textarea id="public_note" name="public_note" style="width:90%;height:40%;"></textarea>';
				dialog.css('margin', '3%');
				dialog.html(s);
			}
			return false;
		}

		var url = annotator.absolute_image_url + 'graph/' + selectedFeature.graph + '/features/';
		if (annotator.selectedFeature.state == 'Insert' && !annotator.selectedFeature.stored) {
			array_features_owned = annotator.selectedFeature.features;
		} else {
			array_features_owned = features_owned(selectedFeature, url);
		}
		create_dialog(selectedFeature, id);

		fill_dialog(id, selectedFeature);
		dialog = $('#dialog' + id);
		if (can_edit) {
			var request = $.getJSON('/digipal/page/' + annotator.image_id + "/graph/" + selectedFeature.graph);
			request.done(function(data) {
				var url = annotator.absolute_image_url + 'allograph/' + data.id + '/features/';
				var s = '<form class="frmAnnotation" method="get" name="frmAnnotation">';
				s += "<input type='hidden' name ='allograph' id='hidden_allograph' /> <input type='hidden' id='hidden_hand' name='hand' />";
				var allographs = $.getJSON(url);
				s += "<div id='box_features_container'>";

				allographs.done(function(data) {
					$.each(data, function(idx) {
						component = data[idx].name;
						component_id = data[idx].id;
						var features = data[idx].features;
						s += "<div class='component_labels' data-id='component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component icon-arrow-up'></span></b>";
						s += "<div class='checkboxes_div btn-group'>";
						s += "<span class='check_all btn btn-mini'>All</span> <span class='btn btn-mini uncheck_all'>Clear</span>";
						s += "</div></div>";
						s += "<div id='component_" + component_id + "' data-hidden='false' class='feature_containers'>";
						$.each(features, function(idx) {
							var value = component_id + '::' + features[idx].id;
							var id = component_id + '_' + features[idx].id;

							var names = component + ':' + features[idx].name;
							if (array_features_owned.indexOf(names) >= 0) {
								s += "<p><input name='checkboxes[]' id='" + id + "' checked = 'checked' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + names + "' /> <label style='font-size:12px;display:inline;' for='" + id + "'>" + features[idx].name + "</label>";
							} else {
								s += "<p><input name='checkboxes[]' id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + names + "'/> <label style='font-size:12px;display:inline;' for='" + id + "'>" + features[idx].name + "</label>";
							}
						});
						s += "</div>";
					});

					$('#id_internal_note').remove();
					$('#id_display_note').remove();

					var display_note = $('<textarea>');
					display_note.attr('id', 'id_display_note').attr('name', 'display_note').addClass('feature_containers').data('hidden', true).val(selectedFeature.display_note);

					var internal_note = $('<textarea>');
					internal_note.attr('id', 'id_internal_note').attr('name', 'internal_note').addClass('feature_containers').data('hidden', true).val(selectedFeature.internal_note);

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

					var component_labels = $('.component_labels');
					component_labels.click(function() {
						var component = $(this);
						var div = $("#" + $(this).data('id'));
						if (!div.data('hidden')) {
							div.slideUp().data('hidden', true);
							component.next('.checkboxes_div').hide();
							component.find('.arrow_component').removeClass('icon-arrow-up').addClass('icon-arrow-down');
						} else {
							div.slideDown().data('hidden', false);
							component.next('.checkboxes_div').show();
							component.find('.arrow_component').removeClass('icon-arrow-down').addClass('icon-arrow-up');
						}
					});

				});
			});

		} else {
			$.ajax({
				url: url,
				dataType: 'json',
				cache: false,
				type: 'GET',
				async: true,
				error: function(xhr, status, error) {
					console.warn('Error: ' + error);
					throw new Error(error);
				},
				success: function(data) {
					var s = '<ul>';
					if (!$.isEmptyObject(data)) {
						for (i = 0; i < data.length; i++) {
							var component = data[i]['name'];
							s += "<li class='component'><b>" + component + "</b></li>";
							for (j = 0; j < data[i]['feature'].length; j++) {
								s += "<li class='feature'>" + (data[i]['feature'][j]) + "</li>";
							}
						}
					} else {
						s += "<li class='component'>This graph has not yet been described.</li>";
					}
					s += "</ul>";
					dialog.html(s);
				}
			});
		}
	}

	if (selectedFeature) {
		var n = 0;
		var annotations = annotator.annotations;
		var select_allograph;
		if ($('.tab-pane.active').attr('id') == 'annotator') {
			select_allograph = $('#panelImageBox');
		} else {
			select_allograph = $('.modal-body');
		}
		(function() {
			for (var i = 0; i < features.length; i++) {
				if (features[i].feature == annotator.selectedFeature.feature && features[i].hand == annotator.selectedFeature.hand && features[i].stored) {
					n++;
				}
			}
			if ($(".number_annotated_allographs").length) {
				$(".number_annotated_allographs .number-allographs").html(n);
			}
		})();

		//$('#hidden_hand').val(selectedFeature.hidden_hand);
		//$('#hidden_allograph').val(getKeyFromObjField(selectedFeature, 'hidden_allograph'));
		select_allograph.find('.hand_form').val(selectedFeature.hidden_hand);
		select_allograph.find('.allograph_form').val(getKeyFromObjField(selectedFeature, 'hidden_allograph'));
		$('select').trigger('liszt:updated');
		if (annotator.isAdmin == "True") {
			highlight_vectors();
		}
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
			console.warn('Error: ' + textStatus);
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
				refresh_letters_container(allograph, allograph_id, true);
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

				// deleting from annotations by allograph
				$('li[data-graph="' + feature.graph + ']"').remove();
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
	});

}

function highlight_unsaved_vectors(button) {
	var features = annotator.unsaved_annotations;
	var color;
	for (i = 0; i < features.length; i++) {
		if (!features[i].feature.style) {
			stylize('#ee9900', features[i].feature);
		}
		features[i].feature.originalColor = features[i].feature.style.fillColor;
		features[i].featureoriginalWidth = 2;
		color = 'red';
		if (features[i].feature.features.length) {
			color = 'blue';
		}
		features[i].feature.style.strokeColor = color;
		features[i].feature.style.strokeWidth = 6;
	}
	annotator.vectorLayer.redraw();
	button.addClass('active');
}


function unhighlight_unsaved_vectors(button) {
	var features = annotator.unsaved_annotations;
	for (i = 0; i < features.length; i++) {
		features[i].feature.style.strokeColor = features[i].feature.originalColor;
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


function make_form() {
	if ($('.tab-pane.active').attr('id') == 'annotator') {
		select_allograph = $('#panelImageBox');
	} else {
		select_allograph = $('.myModal');
	}
	var form = select_allograph.find('.frmAnnotation');
	var obj = {};
	var array_values = [];
	var features = {};
	var has_features = false;

	if ($('.features_box').length) {
		has_features = true;
		$('.features_box').each(function() {
			if ($(this).is(':checked')) {
				array_values.push($(this).val());
			}
		});
	}

	features.has_features = has_features;
	features.features = array_values;
	obj['feature'] = array_values;

	var form_serialized = form.serialize();
	var s = '';

	for (i = 0; i < array_values.length; i++) {
		s += '&feature=' + array_values[i];
	}

	form_serialized += s;

	if ($('#id_display_note').val()) {
		form_serialized += "&display_note=" + $('#id_display_note').val();
	}

	if ($('#id_internal_note').val()) {
		form_serialized += "&internal_note=" + $('#id_internal_note').val();
	}

	return {
		'has_features': has_features,
		'features': features,
		'form_serialized': form_serialized
	};
}

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

	updateStatus('-');

	var feature;
	var data = make_form();
	var url = annotator.absolute_image_url + 'save';
	if (allow_multiple() && this.selectedAnnotations.length > 1 && !allographs_page) {
		var msg = 'You are about to save ' + this.selectedAnnotations.length + ' annotations. Do you want to continue?';
		if (confirm(msg)) {
			for (var i = 0; i < this.selectedAnnotations.length; i++) {
				feature = this.selectedAnnotations[i];
				save(url, feature, data.form_serialized, ann, data.features);
			}
		} else {
			return false;
		}
	} else {

		if (this.selectedFeature) {

			save(url, this.selectedFeature, data.form_serialized, ann, data.features);

			//this.loadAnnotations();
		} else {
			for (var idx = 0; idx < this.vectorLayer.features.length; idx++) {
				feature = this.vectorLayer.features[idx];

				if (!feature.attributes.saved) {
					save(url, feature, data.form_serialized, ann, data.features);
				}
			}
		}
	}

};

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

function save(url, feature, data, ann, features) {
	var id = feature.id;
	var temp = feature;
	annotator.setSavedAttribute(feature, Annotator.SAVED, false);
	var geoJson = annotator.format.write(feature);
	var save_annotations = $.ajax({
		url: url + '/' + id + '/?geo_json=' + geoJson,
		data: data,
		beforeSend: function() {
			updateStatus('Saving annotation ...');
		},
		error: function(xhr, textStatus, errorThrown) {
			updateStatus(textStatus, 'error');
			annotator.setSavedAttribute(feature, Annotator.UNSAVED, false);
		},
		success: function(data) {
			if (!handleErrors(data)) {
				updateStatus('Saved annotation.', 'success');
				/*
				$('.number_annotated_allographs span').html(function() {
					return parseInt($(this).text()) + 1;
				});
*/
				//annotator.refresh_layer();
				//if ($('.letters-allograph-container').length) {
				if ($('.tab-pane.active').attr('id') == 'annotator') {
					select_allograph = $('#panelImageBox');
				} else {
					select_allograph = $('.modal-body');
				}
				var allograph = select_allograph.find('.allograph_form option:selected').text();
				var allograph_id = select_allograph.find('.allograph_form').val();
				refresh_letters_container(allograph, allograph_id, true);
				//}
				var color;
				if (temp.state == 'Insert') {
					var num_features;
					if (temp.stored) {
						num_features = features.features.length;
					} else {
						num_features = feature.features.length || 0;
					}
					var element = $('.number_unsaved_allographs');
					var number_unsaved = element.html();
					var annotations = annotator.unsaved_annotations;
					for (var i = 0; i < annotations.length; i++) {
						if (annotations[i].feature.id == feature.id) {
							annotations.splice(i, 1);
							break;
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
					stylize(feature, color, 'blue', 0.4);
					feature.style.originalColor = color;
					feature.style.strokeWidth = 2;
					feature.stored = true;
					feature.last_feature_selected = null;
					element.html(annotations.length);
					temp = null;
				} else {
					if (features.has_features) {
						if (features.features.length) {
							color = 'green';
							feature.described = true;
						} else {
							color = '#ee9900';
							feature.described = false;
						}
						stylize(feature, color, color, 0.4);
					}
				}
				annotator.selectedAnnotations = [];
			}
			var f = annotator.vectorLayer.features;
			var f_length = annotator.vectorLayer.features.length;
			var n = 0;
			for (g = 0; g < f_length; g++) {
				if (f[g].feature == feature.feature && f[g].stored) {
					n++;
				}
			}
			$(".number_annotated_allographs .number-allographs").html(n);

			// refresh allographs

		},
		complete: function() {
			if (annotator.url_allographs && ann) {
				load_annotations_allographs(ann);
			}
			annotator.vectorLayer.redraw();
		}
	});
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

	if (message) {
		updateStatus(message, 'error');
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

function updateStatus(msg, status) {
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

	status_element.html(msg).fadeIn();


	var timeout =
		setTimeout(function() {
			status_element.fadeOut();
			running = false;
		}, 5000);
	//
	// GN: bugfix, JIRA 77
	// The message will push the openlayer div down and cause
	// the drawing symbol to appear below the mosue cursor.
	// To avoid this we force a render on the OL map to tell it
	// to refresh it internal location variable.
	//
	if (typeof annotator !== 'undefined') {
		annotator.map.render(annotator.map.div);
	}
}


function registerEvents() {
	if (annotator.isAdmin == 'True') {
		annotator.events = true;
		var paths = $('#OpenLayers_Layer_Vector_27_vroot').find("path");
		paths.unbind();
		paths.mouseenter(function() {
			var features = annotator.vectorLayer.features;
			for (var i = 0; i < features.length; i++) {
				if ($(this).attr('id') == features[i].geometry.id) {
					if (features[i].display_note) {
						createPopup(features[i]);
					}
				}
			}
		});

		paths.mouseleave(function() {
			var features = annotator.vectorLayer.features;
			for (var i = 0; i < features.length; i++) {
				if (features[i].popup) {
					deletePopup(features[i]);
				}
			}
		});


		paths.dblclick(function(event) {
			var id = $(this).attr('id');
			var feature, boxes_on_click = false;
			var features = annotator.vectorLayer.features;
			for (var i = 0; i < features.length; i++) {
				if (features[i].geometry.id == id) {
					feature = features[i].id;
				}
			}
			if (annotator.boxes_on_click) {
				boxes_on_click = true;
			}
			annotator.boxes_on_click = true;
			annotator.showAnnotation(feature);
			if (!boxes_on_click) {
				annotator.boxes_on_click = false;
				var boxes_on_click_element = $("#boxes_on_click");
				boxes_on_click_element.attr('checked', false);
			}
			event.stopPropagation();
			return false;
		});
	}
	return false;
}

function disable_annotation_tools() {
	var editorial, delete_icon, edit;

	if ($('.olControlEditorialFeatureItemInactive').length) {
		editorial = $('.olControlEditorialFeatureItemInactive');
	} else {
		$('.olControlEditorialFeatureItemActive');
	}

	var save_icon = $('.olControlSaveFeaturesItemInactive');

	if ($('.olControlDeleteFeatureItemInactive').length) {
		delete_icon = $('.olControlDeleteFeatureItemInactive');
	} else {
		delete_icon = $('.olControlDeleteFeatureItemActive');
	}

	if ($('.olControlTransformFeatureItemInactive').length) {
		edit = $('.olControlTransformFeatureItemInactive');
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

	if ($('.olControlEditorialFeatureItemInactive').length) {
		editorial = $('.olControlEditorialFeatureItemInactive');
	} else {
		$('.olControlEditorialFeatureItemActive');
	}

	var save_icon = $('.olControlSaveFeaturesItemInactive');

	if ($('.olControlDeleteFeatureItemInactive').length) {
		delete_icon = $('.olControlDeleteFeatureItemInactive');
	} else {
		delete_icon = $('.olControlDeleteFeatureItemActive');
	}

	if ($('.olControlTransformFeatureItemInactive').length) {
		edit = $('.olControlTransformFeatureItemInactive');
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
	if (!(this.fullScreen.active)) {
		this.fullScreen.activate();
		map.addClass("fullScreenMap");
		$('.olControlEditingToolbar').css("background-color", "rgba(0, 0, 0, 0.85)");

		$(document).keyup(function(e) {
			if (e.keyCode == 27) {
				map.removeClass('fullScreenMap');
				panel.removeClass('fullScreenPanel');
				$('.olControlEditingToolbar').css("background-color", "rgba(0, 0, 0, 0.25)");
				annotator.fullScreen.deactivate();
			}
		});

		$('.olControlFullScreenFeatureItemInactive').attr('title', 'Deactivate Full Screen');
		panel.addClass('fullScreenPanel');

	} else {
		this.fullScreen.deactivate();
		map.removeClass('fullScreenMap');
		$('.olControlEditingToolbar').css("background-color", "rgba(0, 0, 0, 0.25)");
		$('.olControlFullScreenFeatureItemInactive').attr('title', 'Activate Full Screen');
		panel.removeClass('fullScreenPanel');
	}
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

DigipalAnnotator.prototype.activateKeyboardShortcuts = function() {
	var _self = this;
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
						break;
					case 40:
						annotator.map.moveByPx(0, 60);
						annotator.vectorLayer.redraw();
						break;
					case 37:
						annotator.map.moveByPx(-60);
						annotator.vectorLayer.redraw();
						break;
					case 39:
						annotator.map.moveByPx(60);
						annotator.vectorLayer.redraw();
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