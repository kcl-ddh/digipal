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
	this.isAdmin = isAdmin;
	this.mediaUrl = mediaUrl;
	this.allow_multiple_dialogs = false;
	this.boxes_on_click = false;
	this.deleteFeature.panel_div.title = 'Delete (shift + Backspace)';
	this.transformFeature.panel_div.title = 'Transform (shift + t)';
	this.duplicateFeature.panel_div.title = 'Duplicate (shift + d)';
	//this.polygonFeature.panel_div.title = 'Draw Polygon (alt + p)';
	this.rectangleFeature.panel_div.title = 'Draw Rectangle (shift + r)';
	this.selectFeature.panel_div.title = 'Select (shift + g)';
	this.dragFeature.panel_div.title = 'Drag (shift + w)';
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

	this.showAnnotation(event.feature);
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

	} else {
		feature.style.fillColor = '#ee9900';
		feature.style.strokeColor = '#ee9900';
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
};

/**
 * Shows the annotation details for the given feature.
 *
 * @param feature
 *              The feature to display the annotation.
 */
DigipalAnnotator.prototype.showAnnotation = function(feature) {
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
	}
	this.vectorLayer.redraw();

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
				var allograph_id = $('#id_allograph').val();
				var allograph = $('#id_allograph option:selected').text();
				refresh_letters_container(allograph, allograph_id);
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

/*

    Function to refresh the layer when saved an annotation

*/

DigipalAnnotator.prototype.refresh_layer = function() {
	annotator.vectorLayer.destroyFeatures();
	var request = $.getJSON('annotations/', function(data) {
		annotator.annotations = data;
	});
	var div = $('<div>');
	div.attr('class', 'loading-div');
	div.html('<p>Reloading annotations. Please wait...</p></p><img src="/static/digipal/images/ajax-loader3.gif" />');
	$('body').append(div.fadeIn());
	var chained = request.then(function(data) {
		var layer = annotator.vectorLayer;
		var format = annotator.format;
		var annotations = data;
		var features_request = $.getJSON('vectors/');
		features_request.then(function(data) {
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
					if (f.id == annotations[i]['vector_id']) {
						f.feature = allograph;
						f.character_id = character_id;
						f.graph = graph;
						f.character = character;
						f.hand = hand;
						f.image_id = image_id;
						f.num_features = num_features;
						f.stored = true;
					}
				}
				features.push(f);
			}
			layer.addFeatures(features);
			var vectors = annotator.vectorLayer.features;
			if (vectors) {
				reload_described_annotations(div);
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
	if (typeof currentFeatures == "undefined" || typeof currentFeatures == "null" || !currentFeatures) {
		allograph_selected = $('#id_allograph').val();
	} else {
		if (annotator.isAdmin == "False") {
			var annotations = annotator.annotations;
			$.each(annotations, function() {
				if (currentFeatures.feature == this.feature) {
					allograph_selected = this.hidden_allograph.split('::')[0];
				}
			});
		} else {
			allograph_selected = currentFeatures;
		}
	}
	var allograph = $('#id_allograph option:selected').val();
	$('#hidden_allograph').val(allograph_selected);

	if (annotator.url_allographs) {
		url = '../allograph/' + allograph_selected + '/features/';
	} else {
		url = 'allograph/' + allograph_selected + '/features/';
	}

	var n = 0;

	for (var i = 0; i < features.length; i++) {
		if (features[i].feature == allograph) {
			n++;
		}
	}

	if ($(".number_annotated_allographs").length) {
		$(".number_annotated_allographs .number-allographs").html(n);
	}

	var s = '';
	var get_features = $.getJSON(url);
	if (allograph_selected) {
		get_features.done(function(data) {
			$.each(data, function(idx) {
				component = data[idx].name;
				component_id = data[idx].id;
				var features = data[idx].features;
				s += "<p class='component_labels' data-id='component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component icon-arrow-down'></span></b>";
				s += "<div class='checkboxes_div pull-right' style='margin: 1%;'><button class='check_all btn btn-small'>All</button> <button class='btn btn-small uncheck_all'>Clear</button></div>";

				s += "<div id='component_" + component_id + "' data-hidden='true' class='feature_containers'>";

				$.each(features, function(idx) {
					var value = component_id + '::' + features[idx].id;
					s += "<p><input type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "'/> <label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + features[idx].id + "'>" + features[idx].name + "</label>";
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
			dialog.parent().find('.allograph_label').html($('#id_allograph option:selected').text());


			dialog.find('#box_features_container').html(s);
			dialog.find('.check_all').click(function() {
				var checkboxes = $(this).parent().next().children().find('input[type=checkbox]');
				checkboxes.attr('checked', true);
			});

			dialog.find('.uncheck_all').click(function() {
				var checkboxes = $(this).parent().next().children().find('input[type=checkbox]');
				checkboxes.attr('checked', false);
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

			dialog.find('#box_features_container p').click(function() {
				var checkbox = $(this).find('input');
				if (checkbox.is(':checked')) {
					checkbox.attr('checked', false);
				} else {
					checkbox.attr('checked', "checked");
				}
			});

			// Showing all the allographs of a given allograph
			dialog.parent().find('.number_annotated_allographs').click(function() {
				open_allographs($(this));
			});

		});
	}



}

// function to check if an object is empty, boolean returned
isEmpty = function(obj) {
	for (var prop in obj) {
		if (obj.hasOwnProperty(prop)) return false;
	}
	return true;
};

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
		async: false
	});


	features.done(function(f) {
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
	return array_features_owned;
}

/*

Feature to discover the already described allographs and
render the layer according to each allograph

*/

function reload_described_annotations(div) {
	var stylize = function(feature, fill, stroke, opacity) {
		feature.style = {
			'strokeColor': stroke,
			'fillColor': fill,
			"fillOpacity": opacity
		};
	};

	var check_described = null;

	$.each(annotator.annotations, function(index, annotation) {
		var feature = annotator.vectorLayer.features;
		if (annotator.selectedFeature !== undefined) {
			var selectedFeature = annotator.selectedFeature;
		}
		var num_features = annotation.num_features;
		var h = 0;
		check_described = $.each(feature, function(index, data) {
			while (h < feature.length) {
				if (annotation.graph == feature[h].graph) {
					if (num_features) {
						stylize(feature[h], 'green', 'green', 0.4);
						feature[h].described = true;
						if (typeof selectedFeature != "undefined" && feature[h].graph == selectedFeature.graph) {
							stylize(feature[h], 'blue', 'blue', 0.4);
							feature[h].described = true;
						}
					} else {
						stylize(feature[h], '#ee9900', '#ee9900', 0.4);
						feature[h].described = false;
						if (typeof selectedFeature != "undefined" && feature[h].graph == selectedFeature.graph) {
							stylize(feature[h], 'blue', 'blue', 0.4);
							feature[h].described = false;
						}
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

	if (typeof allow_multiple_dialogs == "undefined") {
		allow_multiple_dialogs = false;
	}

	if (!allow_multiple_dialogs) {
		$('.dialog_annotations').parent('.ui-dialog').remove();
		$('.dialog_annotations').remove();
	}

	var dialog = $("<div>");
	dialog.attr('id', 'dialog' + id);
	$('#annotations').append(dialog);
	var path;

	if (selectedFeature) {
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
	} else {
		path = document.getElementById("#OpenLayers_Layer_Vector_27_svgRoot");
	}

	dialog.data('feature', selectedFeature);

	var position = function() {
		var p;
		if (typeof annotator.pinned != "undefined" && annotator.pinned.pinned) {
			var w = $(window).scrollTop();
			p = {
				my: "right center + " + w,
				at: "right top" + w,
				of: window
			};
		} else {

			p = {
				my: 'right top',
				at: 'right top',
				of: $(path),
				collision: 'flipfit flipfit'
			};
		}
		return p;
	};

	$('#boxes_on_click').attr('checked', true);
	dialog.dialog({
		draggable: true,
		height: 340,
		minHeight: 340,
		minWidth: 335,
		resizable: true,
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
				if (selectedFeature) {
					title = "<span class='allograph_label'>" + selectedFeature.feature +
						"</span> <span style='position:relative;left:6%;'> <span class='url_allograph btn btn-small'>URL</span></span>";
				} else {
					title = "<span class='allograph_label'>Annotation</span>" +
						" <span style='position:relative;left:6%;'></span><span class='url_allograph btn btn-small'>URL</span></span>";
				}
			} else {
				if (selectedFeature) {
					title = "<span class='allograph_label'>" + selectedFeature.feature + "</span> <span class='url_allograph btn btn-small'>URL</span>";
				} else {
					title = "<input type='text' placeholder = 'Type name' class='name_temporary_annotation' /> <span style='position:relative;left:24%;'><span class='url_allograph btn btn-small'>URL</span></span>";
				}
			}
			return title;
		},
		position: position()
	}).addClass('dialog_annotations');

	var pin = "<span title='Minimize box' class='pull-right pin-box'>-</span>";
	dialog.parent().find('.ui-dialog-title').after(pin);

	// Minimize the dialog
	dialog.parent().find('.pin-box').click(function() {
		var dialog = $(this).parent().parent();
		var position;
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
					'top': parseInt($(window).scrollTop()) + 10,
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



	if (typeof selectedFeature === "null" || typeof selectedFeature === "undefined") {
		updateFeatureSelect(null, id);
		if (annotator.isAdmin == "False") {
			$('.name_temporary_annotation').focus();
			$('.ui-dialog-title').on('click', function() {
				$('.name_temporary_annotation').focus();
			});
		}
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
				s += "<span data-hand = '" + data_hand + "' class='vector_image_link' data-vector-id='" + data[i].vector_id + "'>" + data[i].image + '</span>\n';
			}


			$(s).find('img').each(function() {
				$(this).on('load', function() {
					$('.img-loading').remove();
					container_div.html(s);
					$('.close_top_div_annotated_allographs').click(function() {
						$('.letters-allograph-container').fadeOut().remove();
						$('.number_annotated_allographs').removeClass('active');
					});

					$('.vector_image_link').click(function() {
						var vector = $(this);
						annotator.centreById(vector.data('vector-id'));
					});

					var features = annotator.vectorLayer.features;


					// waiting for all images to be loaded
					$('.vector_image_link').on("mouseover", function() {
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


					$('.vector_image_link').mouseout(function() {
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

					$('.vector_image_link').dblclick(function() {
						var vector = $(this);
						annotator.selectFeatureByIdAndCentre(vector.data('vector-id'));
					});


					var images = $('.vector_image_link');
					var hands = $('.hands_labels');
					$.each(hands, function(index_hands, hand) {
						var c = 0;
						$.each(images, function(index_images, image) {
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
	if ($('.letters-allograph-container').length) {
		$('.letters-allograph-container').remove();
	}
	$(this).addClass('active');
	var allograph_value;
	if (typeof allograph != "undefined") {
		allograph_value = allograph.parent().prev().text();
	} else {
		allograph_value = $('#id_allograph option:selected').text();
	}
	if (allograph_value) {
		var features = annotator.vectorLayer.features;
		for (var i = 0; i < features.length; i++) {
			if (features[i].feature == allograph_value) {
				var feature = features[i].graph;
				var character = features[i].character_id;
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
	if ($('.letters-allograph-container').length) {
		$('.letters-allograph-container').remove();
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
			updateFeatureSelect(annotation, id);
		});

		$('#id_hand').on('change', function() {
			$('#hidden_hand').val($(this).val());
		});

	} else {
		s = "<textarea class='textarea_temporary_annotation'></textarea>";
	}

	dialog.html(s);

	dialog.parent().find('.url_allograph').click(function() {
		if (!dialog.parent().find('.allograph_url_div').length) {
			var url = $("<div class='allograph_url_div'>");
			var allograph_url;
			var input = $('<input type="text" disabled>');
			var title = $('.name_temporary_annotation').val();
			var desc = $('.textarea_temporary_annotation').val();
			if (annotation !== null && annotation.stored) {
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
			input.select();
		} else {
			dialog.find('.allograph_url_div').fadeOut().remove();
		}
	});

	var hidden_hand = $('#id_hand').val();
	var hidden_allograph = $('#id_allograph').val();

	$('#hidden_hand').val(hidden_hand);
	$('#hidden_allograph').val(hidden_allograph);

}

function show_url_allograph(dialog) {
	var url_allograph_div = false;
	dialog.parent().find('.url_allograph').click(function() {
		if (!url_allograph_div) {
			if (!dialog.find('.allograph_url_div').length) {
				var url = $("<div class='allograph_url_div'>");
				var input = $('<input type="text" disabled>');
				var allograph_url = window.location.hostname + document.location.pathname + '?vector_id=' + annotator.selectedFeature.id;
				input.val(allograph_url);
				url.html(input);
				dialog.prepend(url);
				dialog.parent().find('.allograph_url_div input').select();
				url_allograph_div = true;
			}
		} else {
			var url = dialog.parent().find(".allograph_url_div");
			url.fadeOut().remove();
			url_allograph_div = false;
		}
	});
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

		if (selectedFeature === null || typeof selectedFeature == "undefined") {
			create_dialog(null, id);
			fill_dialog(id, null);
			return false;
		}

		var url = 'graph/' + selectedFeature.graph + '/features/';
		array_features_owned = features_owned(selectedFeature, url);
		create_dialog(selectedFeature, id);
		var can_edit = $('#development_annotation').is(':checked');
		var dialog = $('#dialog' + id);

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
						s += "<p class='component_labels' data-id='component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component icon-arrow-down'></span></b>";
						s += "<div class='checkboxes_div pull-right' style='margin: 1%;'><input type='button' class='check_all btn btn-small' value='All' /> <input type='button' class='btn btn-small uncheck_all' value='Clear' /></div>";

						s += "<div id='component_" + component_id + "' data-hidden='true' class='feature_containers'>";
						$.each(features, function(idx) {
							var value = component_id + '::' + features[idx].id;
							var names = component + ':' + features[idx].name;
							if (array_features_owned.indexOf(names) >= 0) {
								s += "<p><input id='" + features[idx].id + "' checked = 'checked' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + names + "' /> <label style='font-size:12px;display:inline;' for='" + features[idx].id + "'>" + features[idx].name + "</label>";
							} else {
								s += "<p><input id='" + features[idx].id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + names + "'/> <label style='font-size:12px;display:inline;' for='" + features[idx].id + "'>" + features[idx].name + "</label>";
							}
						});
						s += "</p></div>";
					});
					s += "</div>";
					dialog.html(s);
					$('.check_all').click(function() {
						var checkboxes = $(this).parent().next().children().find('input[type=checkbox]');
						checkboxes.attr('checked', true);
					});
					$('.uncheck_all').click(function() {
						var checkboxes = $(this).parent().next().children().find('input[type=checkbox]');
						checkboxes.attr('checked', false);
					});
					show_url_allograph(dialog);
					$('.component_labels').click(function() {
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


					/*
                            $('#id_status').val(annotation.status_id);
                            $('#id_before').val(getKeyFromObjField(annotation, 'before'));
                            $('#id_after').val(getKeyFromObjField(annotation, 'after'));
                            */


					//$('#id_display_note').val(selectedFeature.display_note);
					//$('#id_internal_note').val(selectedFeature.internal_note);


				});
			});

		} else {
			$.ajax({
				url: url,
				dataType: 'json',
				cache: false,
				type: 'GET',
				async: true,
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
			show_url_allograph(dialog);
		}

		dialog.find('#box_features_container p').click(function() {
			var checkbox = $(this).find('input');
			if (checkbox.is(':checked')) {
				checkbox.attr('checked', false);
			} else {
				checkbox.attr('checked', "checked");
			}
		});


	}


	if (selectedFeature) {
		var n = 0;
		var annotations = annotator.annotations;

		(function() {
			for (var i = 0; i < features.length; i++) {
				if (features[i].feature == annotator.selectedFeature.feature && features[i].hand == annotator.selectedFeature.hand) {
					n++;
				}
			}

			if ($(".number_annotated_allographs").length) {
				$(".number_annotated_allographs .number-allographs").html(n);
			}
		})();


		$('#hidden_hand').val(selectedFeature.hidden_hand);
		$('#hidden_allograph').val(getKeyFromObjField(selectedFeature, 'hidden_allograph'));
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
DigipalAnnotator.prototype.deleteAnnotation = function(layer, feature) {
	var _self = this;

	var msg = 'You are about to delete this annotation. It cannot be restored at a later time! Continue?';
	var doDelete = confirm(msg);

	if (doDelete && feature !== null) {
		var featureId = feature.id;

		updateStatus('-');
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
/**
 * Saves an annotation for the currently selected feature.
 */
DigipalAnnotator.prototype.saveAnnotation = function() {
	updateStatus('-');
	form = $('#frmAnnotation');

	array_values = [];
	obj = {};
	$('.features_box').each(function() {
		if ($(this).is(':checked')) {
			array_values.push($(this).val());
		}
	});
	obj['feature'] = array_values;
	var form_serialized = form.serialize();
	var s = '';
	for (i = 0; i < array_values.length; i++) {
		s += '&feature=' + array_values[i];
	}
	form_serialized += s;
	if (this.selectedFeature) {

		save('save', this.selectedFeature, form_serialized);

		this.loadAnnotations();
	} else {
		for (var idx = 0; idx < this.vectorLayer.features.length; idx++) {
			var feature = this.vectorLayer.features[idx];

			if (!feature.attributes.saved) {
				save('save', feature, form_serialized);
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

function save(url, feature, data) {
	var id = feature.id;

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
				if ($('.letters-allograph-container').length) {
					var allograph = $('#id_allograph option:selected').text();
					var allograph_id = $('#id_allograph').val();
					refresh_letters_container(allograph, allograph_id);
				}
			}
		}
	});
	save_annotations.done(function() {
		annotator.loadAnnotations();
		annotator.vectorLayer.redraw();
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
					for (i in data.errors) {
						message += '<p>' + data.errors[i] + '</p>';
					}
				}
			}
		}
	}

	if (message) {
		updateStatus(message, 'error')
	};

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
	$('#status').html(msg);

	status_class = status ? ' alert-' + status : '';
	$('#status').attr('class', 'alert' + status_class);

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
		this.fullScreen.active = true;
		$(document).keyup(function(e) {
			if (e.keyCode == 27) {
				$('#map').attr('style', null);
				this.fullScreen.active = null;
			}
		});
		$('.olControlFullScreenFeatureItemInactive').css('background-image', 'url(/static/digipal/scripts/libs/openlayers/theme/default/img/fullscreen_on.gif)');
		$('.olControlFullScreenFeatureItemInactive').attr('title', 'Deactivate Full Screen')
	} else {
		$('#map').attr('style', null);
		$('.olControlEditingToolbar').css("background-color", "rgba(0, 0, 0, 0.25)");
		this.fullScreen.active = null;
		$('.olControlFullScreenFeatureItemInactive').css('background-image', 'url(/static/digipal/scripts/libs/openlayers/theme/default/img/fullscreen.gif)');
		$('.olControlFullScreenFeatureItemInactive').attr('title', 'Activate Full Screen')
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
	_self.dragFeature.handler = OpenLayers.Handler.MOD_SHIFT;
	var deactivateAll = function(activeControls) {
		for (i = 0; i < activeControls.length; i++) {
			if (activeControls[i].title) {
				activeControls[i].deactivate();
			}
		}
	}
	$(document).bind('keydown', function(event) {
		var activeControls = _self.map.getControlsBy('active', true);
		var code = (event.keyCode ? event.keyCode : event.which);
		if (event.shiftKey) {
			switch (code) {
				case 77:
					deactivateAll(activeControls);
					_self.modifyFeature.activate();
					break;
				case 8:
					deactivateAll(activeControls);
					_self.deleteFeature.activate();
					break;
				case 84:
					deactivateAll(activeControls);
					_self.transformFeature.activate();
					break;
				case 68:
					deactivateAll(activeControls);
					_self.duplicateFeature.activate();
					break;
				case 82:
					deactivateAll(activeControls);
					_self.rectangleFeature.activate();
					break;
				case 71:
					deactivateAll(activeControls);
					_self.selectFeature.activate();
					break;
				case 87:
					deactivateAll(activeControls);
					_self.dragFeature.activate();
					break;
				case 90:
					deactivateAll(activeControls);
					_self.zoomBoxFeature.activate();
					break;
				case 83:
					_self.saveButton.trigger();
					break;
				case 38:
					_self.full_Screen();
					break;
			}
		}

	});
};