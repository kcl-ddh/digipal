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
	this.url_annotations = 'annotations';
	this.url_allographs = false;
	this.unsaved_annotations = [];
	this.isAdmin = isAdmin;
	this.mediaUrl = mediaUrl;
	this.allow_multiple_dialogs = false;
	this.boxes_on_click = false;
	this.deleteFeature.panel_div.title = 'Delete (shift + Backspace)';
	this.transformFeature.panel_div.title = 'Transform (shift + t)';
	//this.duplicateFeature.panel_div.title = 'Duplicate (shift + d)';
	//this.polygonFeature.panel_div.title = 'Draw Polygon (alt + p)';
	this.rectangleFeature.panel_div.title = 'Create Annotation (shift + r)';
	this.selectFeature.panel_div.title = 'Select (shift + g)';
	//this.dragFeature.panel_div.title = 'Drag (shift + w)';
	this.zoomBoxFeature.panel_div.title = 'Zoom (shift + z)';
	this.saveButton.panel_div.title = 'Save (shift + s)';

}

/**
 * Function that is called after a feature is selected.
 *
 * @param event
 *              The select event.
 */

DigipalAnnotator.prototype.onFeatureSelect = function(event) {
	this.selectedFeature = event.feature;
	console.log(this.selectedFeature)
	if ($('#id_hide').prop('checked')) {
		var layer = this.vectorLayer;
		for (var i = 0; i < layer.features.length; i++) {
			var f = layer.features[i];
			if (event.feature.id != f.id) {
				f.style = {};
				f.style.display = 'none';
			}
		}
		layer.redraw();
	}
	if (this.selectedFeature.last_feature_selected) {
		this.last_feature_selected = this.selectedFeature.last_feature_selected;
	}
	this.showAnnotation(event.feature);


};

/**
 * Function that is called after a feature is unselected.
 *
 * @param event
 *              The unselect event.
 */
DigipalAnnotator.prototype.onFeatureUnSelect = function(event) {
	var _self = this;
	var feature = event.feature;
	if (feature.described) {
		feature.style.fillColor = 'green';
		feature.style.strokeColor = 'green';
		/*
		if (feature.display_note) {
			feature.style.strokeColor = 'yellow';
		} else {
			feature.style.strokeColor = 'green';
		}
		*/

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
		/*
		if (feature.display_note) {
			feature.style.strokeColor = 'yellow';
		} else {
			feature.style.strokeColor = '#ee9900';
		}
		*/
	}
	if (feature.state == 'Insert') {
		this.last_feature_selected = {
			'id': $('#id_allograph').val(),
			'name': $('#id_allograph option:selected').text()
		};
		feature.last_feature_selected = this.last_feature_selected;
	}


	if ($('#id_hide').prop('checked')) {
		for (var i = 0; i < _self.vectorLayer.features.length; i++) {
			var f = _self.vectorLayer.features[i];
			if (_self.selectedFeature.id != f.id) {
				f.style = null;
			}
		}
	}

	this.vectorLayer.redraw();
	this.selectedFeature = null;
	//$('#id_allograph').val(undefined).trigger('liszt:updated');
	$(".number_annotated_allographs .number-allographs").html(0);

};


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
				for (var h = 0; h < allographs.length; h++) {
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
	var hand;
	if (check == 'check') {
		$(checkboxes).attr('checked', true);
		for (var i = 0; i < features.length; i++) {
			for (var h = 0; h < hands.length; h++) {
				hand = $(hands[h]);
				if (features[i].hand == hand.val() && hand.is(':checked')) {
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
		for (var i = 0; i < features.length; i++) {
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
	_self.vectorLayer.redraw();
};

/**
 * Shows the annotation details for the given feature.
 *
 * @param feature
 *              The feature to display the annotation.
 */
DigipalAnnotator.prototype.showAnnotation = function(feature) {
	if (feature.state == 'Insert') {
		var allograph;
		var allograph_list = $('#id_allograph option');
		$.each(allograph_list, function() {
			if ($(this).text() == feature.feature) {
				allograph = $(this).val();
			}
		});
		$('#id_allograph').val(allograph).trigger('liszt:updated');
		var features = annotator.vectorLayer.features;
		var n = 0;
		for (var i = 0; i < features.length; i++) {
			if (features[i].feature == feature.feature && features[i].stored) {
				n++;
			}
		}
		$(".number_annotated_allographs .number-allographs").html(n);
	}

	if (feature !== null) {
		if (feature.style !== null) {
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
		if (!annotation) {
			return false;
		} else {
			if ($('.letters-allograph-container').length) {
				var allograph_id = $('#id_allograph').val();
				var al = $('#id_allograph option:selected').text();
				if (current_allograph === undefined) {
					refresh_letters_container(al, allograph_id);
				}
				if (current_allograph !== undefined && annotation.feature !== current_allograph) {
					refresh_letters_container(al, allograph_id);
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
	var feature;
	for (i = 0; i < features.length; i++) {
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


var stylize = function(feature, fill, stroke, opacity) {
	feature.style = {
		'strokeColor': stroke,
		'fillColor': fill,
		"fillOpacity": opacity
	};
};

/*

    Function to refresh the layer when saved an annotation

*/

DigipalAnnotator.prototype.refresh_layer = function() {
	annotator.vectorLayer.removeAllFeatures();
	annotator.annotations = [];
	var request = $.getJSON('annotations/', function(data) {
		annotator.annotations = data;
	});
	var div = $('<div>');
	div.attr('class', 'loading-div');
	div.html('<p>Reloading annotations. Please wait...</p></p><img src="/static/digipal/images/ajax-loader3.gif" />');
	$('body').append(div.fadeIn());
	var chained = request.done(function(data) {
		if (isEmpty(data)) {
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
	var url;
	var allograph_selected;
	var annotations = annotator.annotations;
	if ($.isNumeric(currentFeatures)) {
		allograph_selected = currentFeatures;
	} else {
		if (typeof currentFeatures == "undefined" || typeof currentFeatures == "null" || !currentFeatures) {
			if ($('#id_allograph').val()) {
				allograph_selected = $('#id_allograph').val();
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
		var allograph = $('#id_allograph option:selected').val();
		$('#hidden_allograph').val(allograph_selected);

		if (annotator.url_allographs) {
			url = '../allograph/' + allograph_selected + '/features/';
		} else {
			url = 'allograph/' + allograph_selected + '/features/';
		}

		/*
		var n = 0;

		for (var i = 0; i < features.length; i++) {
			if (features[i].feature == allograph) {
				n++;
			}
		}

		var number_allographs = $(".number_annotated_allographs");
		if (number_allographs.length) {
			number_allographs.find(".number-allographs").html(n);
		}
	*/
		var s = '';

		if (typeof allograph_selected != 'undefined' && allograph_selected) {
			var get_features = $.getJSON(url);
			get_features.done(function(data) {
				$.each(data, function(idx) {
					component = data[idx].name;
					component_id = data[idx].id;
					var features = data[idx].features;
					s += "<p class='component_labels' data-id='component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component icon-arrow-down'></span></b>";
					s += "<div class='checkboxes_div pull-right' style='margin: 1%;'><button data-component = '" + component_id + "' class='check_all btn btn-small'>All</button> <button data-component = '" + component_id + "' class='btn btn-small uncheck_all'>Clear</button></div>";

					s += "<div id='component_" + component_id + "' data-hidden='false' class='feature_containers'>";

					$.each(features, function(idx) {
						var value = component_id + '::' + features[idx].id;
						var id = component_id + '_' + features[idx].id;

						if (annotator.selectedFeature !== undefined && annotator.selectedFeature.state != 'Insert') {
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
					s += "</p></div>";
				});

				var dialog;
				if (!annotator.url_allographs) {
					dialog = $('#dialog' + id);
					if (dialog.parent().find(".number_annotated_allographs").length) {
						dialog.parent().find(".number_annotated_allographs .number-allographs").html(n);
					}

				} else {
					dialog = $('.modal-body');
				}
				if (!annotator.editorial.active) {
					dialog.parent().find('.allograph_label').html($('#id_allograph option:selected').text());
				}

				dialog.find('#box_features_container').html(s);
				dialog.find('.check_all').click(function(event) {
					var checkboxes = $(this).parent().next().find('input[type=checkbox]');
					checkboxes.attr('checked', true);
					event.stopPropagation();
				});

				dialog.find('.uncheck_all').click(function(event) {
					var checkboxes = $(this).parent().next().find('input[type=checkbox]');
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
					open_allographs($(this));
				});

			});
		}
	}
	return false;
}

// function to check if an object is empty, boolean returned
isEmpty = function(obj) {
	for (var prop in obj) {
		if (obj.hasOwnProperty(prop)) return false;
	}
	return true;
};


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
			console.log('Error: ' + error);
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
		$('.dialog_annotations').parent('.ui-dialog').remove();
		$('.dialog_annotations').remove();
	}

	var dialog = $("<div>");
	dialog.attr('id', 'dialog' + id);
	$('#annotations').append(dialog);
	var path = $("#OpenLayers_Layer_Vector_27_svgRoot");

	if (selectedFeature && selectedFeature.hasOwnProperty('graph')) {
		var vector_id;
		for (var i = 0; i < annotator.vectorLayer.features.length; i++) {
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

	var position = function() {
		var p;
		/*
		try {
			if (typeof annotator.pinned != "undefined" && annotator.pinned.pinned) {
				p = {
					my: "right center",
					at: "right center",
					of: $('#OpenLayers_Map_4_OpenLayers_ViewPort')
				};
			} else {
				p = {
					my: 'right top',
					at: 'right bottom',
					of: $(path)
				};
			}
		} catch (e) {
			p = {
				my: "right center",
				at: "right center",
				of: $('#OpenLayers_Map_4_OpenLayers_ViewPort')
			};
		}
		*/
		p = {
			my: "right center",
			at: "right center",
			of: $('#OpenLayers_Map_4_OpenLayers_ViewPort')
		};
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
						"</span> <span style='position:relative;left:6%;'> <span data-hidden='true' class='url_allograph btn btn-small'>URL</span></span>";
				} else {
					if (annotator.editorial.active) {
						title = "<span class='allograph_label'>Annotation (Note)</span>" +
							" <span style='position:relative;left:6%;'></span><span data-hidden='true' class='url_allograph btn btn-small'>URL</span></span>";
					} else {
						title = "<span class='allograph_label'>Annotation</span>" +
							" <span style='position:relative;left:6%;'></span><span data-hidden='true' class='url_allograph btn btn-small'>URL</span></span>";
					}
				}
			} else {
				if (selectedFeature) {
					title = "<span class='allograph_label'>" + selectedFeature.feature + "</span> <span data-hidden='true' class='url_allograph btn btn-small'>URL</span>";
				} else {
					title = "<input type='text' placeholder = 'Type name' class='name_temporary_annotation' /> <span style='position:relative;left:20%;'><span data-hidden='true'  class='url_allograph btn btn-small'>URL</span></span>";
				}
			}
			return title;
		},
		position: position()
	}).addClass('dialog_annotations');
	var pin;
	if (typeof annotator.pinned != "undefined" && annotator.pinned.pinned) {
		pin = "<span title='Minimize box' style='font-size:20px;line-height:1.5;' class='pull-right pin-box'>&#9633;</span>";
	} else {
		pin = "<span title='Minimize box' class='pull-right pin-box'>-</span>";
	}

	dialog.parent().find('.ui-dialog-title').after(pin);

	// Minimize the dialog

	dialog.parent().find('.pin-box').click(function() {
		var dialog = $(this).parent().parent();
		dialog.css('position', 'fixed');
		var position;
		if (typeof annotator.pinned != "undefined" && annotator.pinned.pinned) {
			dialog.data('pinned', true);
			position = {
				'top': "20%",
				'left': '40%'
			};
			dialog.data('position', position);
		}

		if (dialog.data('pinned')) {
			$(this).html('-').css({
				'line-height': 1,
				'font-size': "30px"
			});
			position = dialog.data('position');
			annotator.pinned = {
				'pinned': false,
				position: position
			};
			dialog.animate({
				'top': position.top,
				'left': position.left
			}, 300).resizable().draggable();
			dialog.data('pinned', false);
		} else {
			annotator.pinned = {
				'pinned': true,
				position: {
					'top': "20%",
					'left': '75%'
				}
			};
			$(this).html('&#9633;').css({
				'line-height': 1.5,
				'font-size': "20px"
			});
			position = dialog.offset();
			var allograph_position = dialog.parent().find('.number_annotated_allographs');

			dialog.animate({
				'top': annotator.pinned.position.top,
				'left': annotator.pinned.position.left,
			}, 300).resizable('destroy').draggable('destroy');
			dialog.data('position', position);
			dialog.data('pinned', true);
		}
	});

	if (annotator.isAdmin == "False") {
		$('.name_temporary_annotation').focus();
		$('.ui-dialog-title').on('click', function() {
			$('.name_temporary_annotation').focus();
		});
	}

	if (typeof selectedFeature === "null" || typeof selectedFeature === "undefined") {
		updateFeatureSelect(null, id);

	} else {
		updateFeatureSelect(selectedFeature, id);
	}

	// Showing all the allographs of a given allograph
	dialog.parent().find('.number_annotated_allographs').click(function() {
		open_allographs($(this));
	});
}

function load_allographs_container(allograph_value, url) {
	var features = $.getJSON(url);

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
	top_div.append("<span>" + allograph_value + "</span><i title='Close box' class='icon pull-right icon-remove close_top_div_annotated_allographs'></i>");
	div.append(top_div);
	var container_div = $("<div id='container-letters-popup'>");
	container_div.css('padding', '1.5%');
	div.append(container_div);
	$('body').append(div);
	var img = $("<img>");
	img.attr('class', 'img-loading');
	img.attr('src', '/static/digipal/images/ajax-loader3.gif');
	$('#top_div_annotated_allographs').find('span').after(img);
	features.done(function(data) {
		var s = '';
		if (data != "False") {
			data = data.sort();
			var j = 0;
			var data_hand;
			if (data.length === 1) {
				j = 1;
				s += "<label class='hands_labels' data-hand = '" + data[0].hand + "' id='hand_" + data[0].hand + "' style='border-bottom:1px dotted #efefef;'>Hand: " + data[0].hand_name + "</label>\n";
				data_hand = data[0].hand;
				s += "<span data-hand = '" + data_hand + "' class='vector_image_link' data-vector-id='" + data[0].vector_id + "' title='Click on the image to center the map'>" + data[0].image + '</span>\n';
			} else {
				for (var i = 0; i < data.length; i++) {
					j++;
					if (i === 0) {
						s += "<label class='hands_labels' data-hand = '" + data[i].hand + "' id='hand_" + data[i].hand + "' style='border-bottom:1px dotted #efefef;'>Hand: " + data[i].hand_name + "</label>\n";
						data_hand = data[i].hand;
					}
					if (typeof data[i - 1] != "undefined" && typeof data[i + 1] != "undefined" && data[i].hand != data[i - 1].hand) {
						j = 1;
						data_hand = data[i].hand;
						s += "<span style='display:block;margin:3px;'></span><label class='hands_labels' data-hand = '" + data[i].hand + "'  id='hand_" + data_hand + "' style='border-bottom:1px dotted #efefef;margin-top:1%;'>Hand: " + data[i + 1].hand_name + "</label>\n";
					}
					if (typeof data[i + 1] == "undefined" && data[i].hand != data[i - 1].hand) {
						j = 1;
						data_hand = data[i].hand;
						s += "<span style='display:block;margin:3px;'></span><label class='hands_labels' data-hand = '" + data[i].hand + "'  id='hand_" + data_hand + "' style='border-bottom:1px dotted #efefef;margin-top:1%;'>Hand: " + data[i].hand_name + "</label>\n";
					}
					s += "<span data-hand = '" + data_hand + "' class='vector_image_link' data-vector-id='" + data[i].vector_id + "' title='Click on the image to center the map'>" + data[i].image + '</span>\n';
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
						$(hand).after(" <span class='num_all_hands label'>" + c + "</span><span style='display:block;margin:3px;'></span>");
					});
				});
			});



		} else {
			s = "<p><label>No Annotations</label></p>";
			container_div.html(s);
		}

	});
}

function open_allographs(allograph) {
	current_allograph = allograph;
	var container = $('.letters-allograph-container');
	if (container.length) {
		container.remove();
	}
	$(this).addClass('active');
	var allograph_value;
	if (annotator.isAdmin == 'True') {
		if (typeof allograph != "undefined") {
			allograph_value = allograph.parent().prev().text();
		} else {
			allograph_value = $('#id_allograph option:selected').text();
		}
	} else {
		allograph_value = annotator.selectedFeature.feature;
	}
	if (allograph_value) {
		var features = annotator.vectorLayer.features;
		var feature;
		var character;
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

		var url = "graph/" + feature + "/" + character + "/allographs_by_graph/";

		load_allographs_container(allograph_value, url);

	}
}


function refresh_letters_container(allograph, allograph_id) {
	current_allograph = allograph;
	var container = $('.letters-allograph-container');
	if (container.length) {
		container.remove();
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
	var url = "allographs/" + allograph_id + "/" + character_id + "/allographs_by_allograph/";

	load_allographs_container(allograph, url);
}

/*

Function to fill the content of a dialog

*/

function fill_dialog(id, annotation) {
	var can_edit = $('#development_annotation').is(':checked');
	var dialog = $('#dialog' + id);
	var s;

	if (can_edit) {
		s = "<input type='hidden' name='allograph' id='hidden_allograph' /> <input type='hidden' id='hidden_hand' name='hand' />";
		s += "<div id='box_features_container'></div>";

		/*
        $('.url_allograph').before(" <span id='save_features_titlebar' class='btn btn-small btn-success'>Save</span> ");
        $('#save_features_titlebar').click(function() {
            annotator.saveAnnotation();
            reload_described_annotations();
        });
        */



		$('#id_allograph').on('change', function() {
			var n = 0;
			var features = annotator.vectorLayer.features;
			var allograph = $('#id_allograph option:selected').text();
			var allograph_id = $(this).val();

			for (var i = 0; i < features.length; i++) {
				if (features[i].feature == allograph && features[i].stored) {
					n++;
				}
			}

			if (annotator.selectedFeature !== undefined && annotator.selectedFeature.state == 'Insert') {
				annotator.selectedFeature.last_feature_selected = {
					'id': allograph_id,
					'name': allograph
				};
				annotator.selectedFeature.allograph = allograph_id;
				annotator.selectedFeature.feature = allograph;
			}

			$(".number_annotated_allographs .number-allographs").html(n);
			updateFeatureSelect(annotation, id);
		});

	} else {
		s = "<textarea class='textarea_temporary_annotation'></textarea>";
	}

	dialog.html(s);
	var url_allograph_button = dialog.parent().find('.url_allograph');

	url_allograph_button.click(function() {
		show_url_allograph(dialog, annotation, $(this));
	});


	var hidden_hand = $('#id_hand').val();
	var hidden_allograph = $('#id_allograph').val();

	$('#hidden_hand').val(hidden_hand);
	$('#hidden_allograph').val(hidden_allograph);

	if ($('.letters-allograph-container').length) {
		var allograph_id = get_allograph(annotation.feature);
		refresh_letters_container(annotation.feature, allograph_id);
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
		var url = $("<div class='allograph_url_div'>");
		var allograph_url;
		var input = $('<input type="text">');
		var title = $('.name_temporary_annotation').val();
		var desc = $('.textarea_temporary_annotation').val();
		var stored;
		if (annotation !== null) {
			for (var i = 0; i < features.length; i++) {
				if (annotation.graph == features[i].graph && features[i].stored) {
					stored = true;
				}
			}
		}
		if (annotation !== null && stored) {
			allograph_url = window.location.hostname + document.location.pathname + '?vector_id=' + annotator.selectedFeature.id;
		} else {
			var geometryObject = annotator.selectedFeature;
			var geoJSONText = JSON.parse(annotator.format.write(geometryObject));
			geoJSONText.title = title;
			geoJSONText.desc = desc;
			allograph_url = window.location.hostname + document.location.pathname + '?temporary_vector=' + JSON.stringify(geoJSONText);
		}
		input.val(allograph_url);
		url.append(input);
		dialog.prepend(url);

		setTimeout(function() {
			input.focus().select();
		}, 0);



	} else {
		button.data('hidden', true);
		var url_allograph_element = dialog.parent().find('.allograph_url_div');
		url_allograph_element.fadeOut().remove();
	}


}

function showBox(selectedFeature) {

	/*
    var ex_id = $('.dialog_annotations').attr('id');
    if($('#' + ex_id).data('feature') == selectedFeature){
        $(this).focus();
    }
    */


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

		var url = 'graph/' + selectedFeature.graph + '/features/';
		if (annotator.selectedFeature.state == 'Insert' && !annotator.selectedFeature.stored) {
			array_features_owned = annotator.selectedFeature.features;
		} else {
			array_features_owned = features_owned(selectedFeature, url);
		}
		create_dialog(selectedFeature, id);
		fill_dialog(id, selectedFeature);
		dialog = $('#dialog' + id);


		if (can_edit) {
			var request = $.getJSON("graph/" + selectedFeature.graph);
			request.done(function(data) {
				var url;
				if (annotator.url_allographs) {
					url = '../allograph/' + data.id + '/features/';
				} else {
					url = 'allograph/' + data.id + '/features/';
				}

				var s = '<form id="frmAnnotation" method="get" name="frmAnnotation">';
				s += "<input type='hidden' name ='allograph' id='hidden_allograph' /> <input type='hidden' id='hidden_hand' name='hand' />";
				var allographs = $.getJSON(url);
				s += "<div id='box_features_container'>";

				allographs.done(function(data) {
					$.each(data, function(idx) {
						component = data[idx].name;
						component_id = data[idx].id;
						var features = data[idx].features;
						s += "<p class='component_labels' data-id='component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component icon-arrow-up'></span></b>";
						s += "<div class='checkboxes_div pull-right' style='margin: 1%;'><input type='button' class='check_all btn btn-small' value='All' /> <input type='button' class='btn btn-small uncheck_all' value='Clear' /></div>";

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
						s += "</p></div>";
						s += "</div>";

						/*
                            $('#id_status').val(annotation.status_id);
                            $('#id_before').val(getKeyFromObjField(annotation, 'before'));
                            $('#id_after').val(getKeyFromObjField(annotation, 'after'));
                    */

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

					$('.check_all').click(function() {
						var checkboxes = $(this).parent().next().children().find('input[type=checkbox]');
						checkboxes.attr('checked', true);
					});

					$('.uncheck_all').click(function() {
						var checkboxes = $(this).parent().next().children().find('input[type=checkbox]');
						checkboxes.attr('checked', false);
					});

					$('.component_labels').click(function() {
						var div = $("#" + $(this).data('id'));
						if (!div.data('hidden')) {
							div.slideUp().data('hidden', true);
							$(this).next('.checkboxes_div').hide();
							$(this).find('.arrow_component').removeClass('icon-arrow-up').addClass('icon-arrow-down');

						} else {
							div.slideDown().data('hidden', false);
							$(this).next('.checkboxes_div').show();
							$(this).find('.arrow_component').removeClass('icon-arrow-down').addClass('icon-arrow-up');
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
					console.log('Error: ' + error);
				},
				success: function(data) {
					var s = '<ul>';
					if (!isEmpty(data)) {
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
		$('#id_hand').val(selectedFeature.hidden_hand);
		$('#id_allograph').val(getKeyFromObjField(selectedFeature, 'hidden_allograph'));
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
 * Updates the select element according to the given values.
 *
 * @param elementId
 *              The id of select element to update.
 * @param values
 *              The values to update the element with.
 */

function updateSelectOptions(elementId, values) {

	$('#' + elementId + ' :selected').removeAttr('selected');

	var detail = '';

	for (var idx in values) {
		var key = values[idx].substring(0, values[idx].indexOf(':'));
		var value = values[idx].substring(values[idx].indexOf(':') + 1);

		$('#' + elementId + ' option').each(function() {
			if ($(this).val() == key) {
				$(this).attr('selected', 'selected');

				detail += value + '; ';
			}
		});
	}

	$('#' + elementId).multiselect('refresh');

	if (detail) {
		$('#' + elementId + '_detail').text(detail);
	} else {
		full_Screen
		$('#' + elementId + '_detail').text('-');
	}
}

/**
 * Updates the Feature select field according to the given letter and
 * annotation.
 *
 * @param letterId
 *              The id of the letter.
 * @param annotation
 *              The annotation.
 */

function updateOptionsForLetter(letterId, annotation) {
	$.getJSON('letter/' + letterId + '/features/', function(data) {
		if (data.has_minim) {
			enableMultiSelect('id_minim');
		} else {
			disableMultiSelect('id_minim');
		}
		if (data.has_ascender) {
			enableMultiSelect('id_ascender');
		} else {
			disableMultiSelect('id_ascender');
			r
		}
		if (data.has_descender) {
			enableMultiSelect('id_descender');
		} else {
			disableMultiSelect('id_descender');
		}

		$('#id_feature option').each(function() {
			$(this).remove();
		});

		$('#id_feature').multiselect('refresh');

		var features = data.features;

		$.each(features, function(idx) {
			var value = features[idx];
			$('#id_feature').append($('<option>', {
				value: idx
			}).text(value));
		});

		$('#id_feature').multiselect('refresh');

		if (annotation !== null) {
			updateSelectOptions('id_feature', annotation.fields['feature']);
		}
	});
}

/**
 * Enables a multiselect element given its id.
 *
 * @param elementId
 *              The id of the element to enable.
 */

function enableMultiSelect(elementId) {
	$('#' + elementId).removeAttr('disabled');
	$('#' + elementId).multiselect('enable');
}

/**
 * Disables a multiselect element given its id.
 *
 * @param elementId
 *              The id of the element to disable.
 */

function disableMultiSelect(elementId) {
	$('#' + elementId + ' option').each(function() {
		$(this).removeAttr('selected');
	});
	$('#' + elementId).multiselect('refresh');
	$('#' + elementId).attr('disabled', 'disabled');
	$('#' + elementId).multiselect('disable');
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

	if (doDelete && feature !== null) {
		var featureId = feature.id;
		var temp = feature;
		updateStatus('Deleting annotations');
		layer.destroyFeatures([feature]);
		var url;
		if (annotator.url_allographs) {
			url = '../delete/' + featureId + '/';
		} else {
			url = 'delete/' + featureId + '/';
		}
		$.ajax({
			url: url,
			data: '',
			error: function(xhr, textStatus, errorThrown) {
				alert('Error: ' + textStatus);
			},
			success: function(data) {
				if (!handleErrors(data)) {
					updateStatus('Annotation deleted.', 'success');
					_self.loadAnnotations();
					if ($('.letters-allograph-container').length) {
						var allograph = $('#id_allograph option:selected').text();
						var allograph_id = $('#id_allograph').val();
						refresh_letters_container(allograph, allograph_id);
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
				}
			}
		});
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
	$('#id_allograph_chzn .active-result').on('mouseover', function() {
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
	$('#id_allograph_chzn .active-result').on('mouseout', function() {
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
	button.addClass('active').addClass('btn-primary').removeClass("btn-warning");
}


function unhighlight_unsaved_vectors(button) {
	var features = annotator.unsaved_annotations;
	for (i = 0; i < features.length; i++) {
		features[i].feature.style.strokeColor = features[i].feature.originalColor;
		features[i].feature.style.strokeWidth = features[i].feature.originalWidth;
	}
	annotator.vectorLayer.redraw();
	button.removeClass('active').removeClass("btn-primary").addClass("btn-warning");
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

function load_annotations_allographs(annotation) {
	if (annotation) {
		if (selectedAnnotations.annotations.length > 1) {
			$('.myModalLabel .label-modal-value').html(annotation.feature + " <span class='badge badge-important'>" + selectedAnnotations.annotations.length + "</span>");
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
		var url;
		if (annotator.hands_page == "True") {
			url = '/digipal/graph/' + annotation.graph + '/features/';
		} else {
			url = '../graph/' + annotation.graph + '/features/';
		}

		$('#id_display_note').parent('p').hide();
		$('#id_internal_note').parent('p').hide();
		var url_features = "../graph/" + annotation.graph;
		if (annotator.hands_page == "True") {
			url_features = "/digipal/page/61/graph/" + annotation.graph;
		}
		var array_features_owned = features_owned(annotation, url);
		var request = $.getJSON(url_features);
		var features = annotator.vectorLayer.features;
		var url2;
		request.done(function(data) {
			var allograph_id = data.id;
			url2 = '../allograph/' + data.id + '/features/';
			if (annotator.hands_page == "True") {
				url2 = "/digipal/page/61/allograph/" + data.id + '/features/';
			}
			var allographs = $.getJSON(url2);
			var s = "<div id='box_features_container'>";
			var string_summary = '';
			allographs.done(function(data) {
				$.each(data, function(idx) {
					var component = data[idx].name;
					var component_id = data[idx].id;
					var is_empty;
					var features = data[idx].features;
					string_summary += "<span class='component_summary'>" + data[idx].name + "</span>";

					s += "<p class='component_labels' data-id='component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component icon-arrow-up'></span></b></p>";

					s += "<div class='checkboxes_div pull-right' style='margin: 1%;'><button data-component = '" + component_id + "' class='check_all btn btn-small'>All</button> <button data-component = '" + component_id + "' class='btn btn-small uncheck_all'>Clear</button></div><div>";

					s += "<div id='component_" + component_id + "' data-hidden='false' class='feature_containers'>";
					var n = 0;

					$.each(features, function(idx) {
						var value = component_id + '::' + features[idx].id;
						var names = component + ':' + features[idx].name;
						var f = selectedAnnotations.annotations;
						var al = '';
						var d = 0;
						var title = '';
						var ann;
						for (var k = 0; k < f.length; k++) {
							for (var j = 0; j < f[k].features.length; j++) {
								if (f[k].features[j] == component_id + '::' + features[idx].id && f[k].feature == annotation.feature) {

									ann = $('input[data-annotation="' + f[k].vector_id + '"]').next().text();

									if (ann) {
										al += '<span class="label">' + ann + '</span> ';
										title += ann + ' ';
									}

									d++;

									temporary_vectors.push(names);
								}

							}
						}
						var id = component_id + '_' + features[idx].id;

						if (temporary_vectors) {
							array_features_owned = array_features_owned.concat(temporary_vectors);
						}

						if (array_features_owned.indexOf(names) >= 0) {

							string_summary += "<span title='" + title + "' class='feature_summary'>" + features[idx].name + ' ' + al + "</span>";

							s += "<p><input checked = 'checked' type='checkbox' value='" + value + "' class='features_box' id='" + id + "' data-feature = '" + features[idx].id + "' /> <label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + id + "'>" + features[idx].name + "</label></p>";
							n++;
						} else {
							s += "<p><input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "'/> <label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + id + "'>" + features[idx].name + "</label></p>";
						}

					});
					s += "</div>";
					if (!n) {
						string_summary += "<span class='feature_summary'>undefined</span>";
					}
				});
				s += "</div>";
				$("#summary").html(string_summary);
				$('#features_container').html(s);
				$('.check_all').click(function(event) {
					var component = $(this).data('component');
					var checkboxes = $('#component_' + component).find("input[type=checkbox]");
					checkboxes.attr('checked', true);
					event.stopPropagation();
				});
				$('.uncheck_all').click(function(event) {
					var component = $(this).data('component');
					var checkboxes = $('#component_' + component).find("input[type=checkbox]");
					checkboxes.attr('checked', false);
					event.stopPropagation();
				});
				$('.myModal select').chosen();

				var maximized = false;
				$('#maximize').click(function(event) {
					event.preventDefault();
					$('#summary').css("bottom", "88%").hide();
					if (!maximized) {
						$('.myModal').animate({
							'position': 'fixed',
							'top': "0px",
							'left': '59.5%',
							"width": '40%',
							"height": '100%'
						}, 200, function() {
							$('#summary').show();
							$('.modal-body').css("max-height", "100%");
						}).draggable("destroy");


						maximized = true;
					} else {
						$('#summary').css("bottom", "88%").hide();
						$('.myModal').animate({
							'position': 'fixed',
							'left': "55%",
							'top': "15%",
							'right': '',
							"width": '30%',
							"height": '60%'
						}, 200, function() {
							$('#summary').show();
							$('#summary').style = null;
							$('.modal-body').css("max-height", "");
						}).draggable();



						maximized = false;
					}
				});

				$('.component_labels').click(function() {
					var div = $("#" + $(this).data('id'));
					if (!div.data('hidden')) {
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
					$('.select_annotation_checkbox').attr('checked', false);
				});

			});
			$('select').on("liszt:ready", function() {
				style_select('#id_hand_chzn');
				style_select('#id_allograph_chzn');
			});
			$('select').chosen();

		});
	}
}


/**
 * Saves an annotation for the currently selected feature.
 */
DigipalAnnotator.prototype.saveAnnotation = function(ann) {
	if (!ann) {
		ann = null;
	}
	updateStatus('-');
	var form = $('#frmAnnotation');
	var array_values = [];
	var obj = {};
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

	if (this.selectedFeature) {

		save('save', this.selectedFeature, form_serialized, ann, features);

		this.loadAnnotations();
	} else {
		for (var idx = 0; idx < this.vectorLayer.features.length; idx++) {
			var feature = this.vectorLayer.features[idx];

			if (!feature.attributes.saved) {
				save('save', feature, form_serialized, ann, features);
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
	if (annotator.url_allographs) {
		url = '../' + url;
	}
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
				if ($('.letters-allograph-container').length) {
					var allograph = $('#id_allograph option:selected').text();
					var allograph_id = $('#id_allograph').val();
					refresh_letters_container(allograph, allograph_id);
				}
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
			}
		},
		complete: function() {
			if (annotator.url_allographs && ann) {
				load_annotations_allographs(ann);
			}
			annotator.vectorLayer.redraw();
		}
	});
	/*
	save_annotations.done(function() {
		annotator.loadAnnotations();
		annotator.vectorLayer.redraw();
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
					for (i in data.errors) {
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

function updateStatus(msg, status) {
	$('#status').html(msg).fadeIn();
	status_class = status ? ' alert-' + status : '';
	$('#status').attr('class', 'alert' + status_class);
	setTimeout(function() {
		$('#status').fadeOut();
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
	if (!(this.fullScreen.active)) {
		this.fullScreen.activate();
		$('#map').css({
			'width': '100%',
			'height': '100%',
			'position': 'fixed',
			'top': 0,
			'left': 0,
			'z-index': 1000,
			'background-color': 'rgba(0, 0, 0, 0.95)'
		});
		$('.olControlEditingToolbar').css("background-color", "rgba(0, 0, 0, 0.85)");
		$(document).keyup(function(e) {
			if (e.keyCode == 27) {
				$('#map').attr('style', null);
				$('#panelImageBox').attr('style', null);
				$('.olControlEditingToolbar').css("background-color", "rgba(0, 0, 0, 0.25)");
				annotator.fullScreen.deactivate();
			}
		});
		$('.olControlFullScreenFeatureItemInactive').attr('title', 'Deactivate Full Screen');
		$('#panelImageBox').css({
			'position': 'fixed',
			"top": "0.5%%",
			"z-index": 2000,
			"width": "80%",
			"height": "30px",
			"left": "8%",
			'border-color': '#333',
			'background-color': 'rgba(10, 10, 10, 0.7)'
		});

	} else {
		this.fullScreen.deactivate();
		$('#map').attr('style', null);
		$('.olControlEditingToolbar').css("background-color", "rgba(0, 0, 0, 0.25)");
		$('.olControlFullScreenFeatureItemInactive').attr('title', 'Activate Full Screen');
		$('#panelImageBox').attr('style', null);
	}
};

/* End FullScreen Mode */

/**
 * Displays annotations overview.
 *
 * @param data
 *              The annotation data.
 */

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

function showAnnotationsOverview(data) {
	var _self = this.annotator;

	$('#overview').children().remove();

	var previousLetter = '';
	var letterCounter = 0;

	$.each(data, function(idx) {
		var a = data[idx];
		var fid = a.vector_id;
		var letter = a.allograph;

		var li = document.createElement('li');
		li.setAttribute('id', fid);

		if (letter != previousLetter) {
			letterCounter = 0;
		}

		previousLetter = letter;

		li.innerHTML = '<dfn>' + (letter ? letter : '-') + ++letterCounter + '</dfn>' + '<a href="javascript: annotator.selectFeatureByIdAndCentre(\'' + fid + '\');"' + 'title="' + fid + '">' + '<img src="' + _self.mediaUrl + 'uploads/annotations/' + idx + '.jpg" width="15px" />' + '</a>';

		$('#overview').append(li);
	});
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


		if (event.shiftKey && annotator.isAdmin == 'Trueuu') {
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
					case 84:
						toggleAll(activeControls, false);
						_self.transformFeature.activate();
						break;
					case 68:
						toggleAll(activeControls, false);
						_self.duplicateFeature.activate();
						break;
					case 82:
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