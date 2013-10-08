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
	this.deleteFeature.panel_div.title = 'Delete (alt + Backspace)';
	this.transformFeature.panel_div.title = 'Transform (alt + t)';
	this.duplicateFeature.panel_div.title = 'Duplicate (alt + d)';
	//this.polygonFeature.panel_div.title = 'Draw Polygon (alt + p)';
	this.rectangleFeature.panel_div.title = 'Draw Rectangle (alt + r)';
	this.selectFeature.panel_div.title = 'Select (alt + g)';
	this.dragFeature.panel_div.title = 'Drag (alt + w)';
	this.zoomBoxFeature.panel_div.title = 'Zoom (alt + z)';
	this.saveButton.panel_div.title = 'Save (alt + s)';

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
	$(element).each(function() {
		if (text == true) {
			var txt = $(this).text();
			attribute = null;
		} else {
			var txt = $(this).attr(attribute);
		}
		if (seen[txt])
			$(this).remove();
		else
			seen[txt] = true;
	});
}

DigipalAnnotator.prototype.filterAnnotation = function(checkboxes) {
	var _self = this;
	var features = _self.vectorLayer.features;
	for (var i in features) {
		if (!($(checkboxes).is(':checked'))) {
			if ($(checkboxes).val() == features[i].feature) {
				features[i].style.fillOpacity = 0;
				features[i].style.strokeOpacity = 0;
			}
		} else {
			if ($(checkboxes).val() == features[i].feature) {
				features[i].style.fillOpacity = 0.4;
				features[i].style.strokeOpacity = 1;
			}
		}
	}
	_self.vectorLayer.redraw();
};

DigipalAnnotator.prototype.filterCheckboxes = function(checkboxes, check) {
	var _self = this;
	var features = _self.vectorLayer.features;
	if (check == 'check') {
		$(checkboxes).attr('checked', true);
		for (var i = 0; i < features.length; i++) {
			if (features[i].style === undefined || features[i].style === null) {
				features[i].style = {
					'fillOpacity': 0.4,
					'strokeOpacity': 1
				};
				if (features[i].described) {
					features[i].style.fillColor = 'green';
					features[i].style.strokeColor = 'green';

				} else {
					features[i].style.fillColor = '#ee9900';
					features[i].style.strokeColor = '#ee9900';

				}
			} else {
				features[i].style.fillOpacity = 0.4;
				features[i].style.strokeOpacity = 1;
				if (features[i].described) {
					features[i].style.fillColor = 'green';
					features[i].style.strokeColor = 'green';

				} else {
					features[i].style.fillColor = '#ee9900';
					features[i].style.strokeColor = '#ee9900';

				}
			}
		}
	} else if (check == 'uncheck') {
		$(checkboxes).attr('checked', false);
		for (var i = 0; i < features.length; i++) {
			if (features[i].style === undefined || features[i].style === null) {
				features[i].style = {
					'fillOpacity': 0,
					'strokeOpacity': 0
				};
				if (features[i].described) {
					features[i].style.fillColor = 'green';
					features[i].style.strokeColor = '#ee9900';

				} else {
					features[i].style.fillColor = '#ee9900';
					features[i].style.strokeColor = '#ee9900';

				}
			} else {
				features[i].style.fillOpacity = 0;
				features[i].style.strokeOpacity = 0;
				if (features[i].described) {
					features[i].style.fillColor = 'green';
					features[i].style.strokeColor = '#ee9900';

				} else {
					features[i].style.fillColor = '#ee9900';
					features[i].style.strokeColor = '#ee9900';

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
					var graph = annotations[i]['graph'];
					var character = annotations[i]['character'];
					if (f.id == annotations[i]['vector_id']) {
						f.feature = allograph;
						f.graph = graph;
						f.character = character;
					}
				}
				features.push(f);
			}
			layer.addFeatures(features);
			var vectors = annotator.vectorLayer.features;
		});
		reload_described_annotations();
	});
}
/**
 
 * Updates the feature select according to the currently selected allograph.
 
 */

function updateFeatureSelect(currentFeatures) {
	var features = annotator.vectorLayer.features;
	var url;
	$('#hidden_allograph').val($('#id_allograph option:selected').val());
	if (annotator.url_allographs) {
		url = '../allograph/' + $('#id_allograph option:selected').val() + '/features/';
	} else {
		url = 'allograph/' + $('#id_allograph option:selected').val() + '/features/';
	}
	$('.allograph_label').html($('#id_allograph option:selected').text());
	var n = 0;
	var features = annotator.vectorLayer.features;
	for (var i = 0; i < features.length; i++) {
		if (features[i].feature == $('#id_allograph option:selected').text()) {
			n++;
		}
	}
	if ($(".number_annotated_allographs").length) {
		$(".number_annotated_allographs .number-allographs").html(n);
	}
	var s = '';
	$.getJSON(url, function(data) {
		$.each(data, function(idx) {
			component = data[idx].name;
			component_id = data[idx].id;
			var features = data[idx].features;
			s += "<p class='component_labels' data-id='component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component icon-arrow-down'></span></b>";
			s += "<div id='component_" + component_id + "' data-hidden='true' class='feature_containers'>";
			$.each(features, function(idx) {
				var value = component_id + '::' + features[idx].id;
				s += "<p><input type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "'/> " + features[idx].name;
			});
			s += "</p></div>";
		});
		$('#box_features_container').html(s);
		$('.component_labels').click(function() {
			var div = $("#" + $(this).data('id'));
			if (div.data('hidden') === false) {
				div.slideUp().data('hidden', true);
				$(this).find('.arrow_component').removeClass('icon-arrow-up').addClass('icon-arrow-down');
			} else {
				div.slideDown().data('hidden', false);
				$(this).find('.arrow_component').removeClass('icon-arrow-down').addClass('icon-arrow-up');

			}
		});
		$('#box_features_container p').click(function() {
			var checkbox = $(this).find('input');
			if (checkbox.is(':checked')) {
				checkbox.attr('checked', false);
			} else {
				checkbox.attr('checked', "checked");
			}
		});


	});
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

function reload_described_annotations() {
	var stylize = function(feature, fill, stroke, opacity) {
		feature.style = {
			'strokeColor': stroke,
			'fillColor': fill,
			"fillOpacity": opacity
		};
	};
	$.each(annotator.annotations, function(index, annotation) {
		var feature = annotator.vectorLayer.features;
		if (annotator.selectedFeature !== undefined) {
			var selectedFeature = annotator.selectedFeature;
		}
		var url = 'graph/' + annotation.graph + '/features/';
		var h = 0;
		check_described = $.getJSON(url, function(data) {
			var vector = (data);
			var is_empty = isEmpty(vector);
			while (h < feature.length) {
				var path = $("#" + feature[h].geometry.id);
				if (annotation.graph == feature[h].graph) {
					if (is_empty === false) {
						stylize(feature[h], 'green', 'green', 0.4);
						feature[h].described = true;
						if (selectedFeature !== undefined && feature[h].graph == selectedFeature.graph) {
							stylize(feature[h], 'blue', 'blue', 0.4);
							feature[h].described = true;
						}
					} else {
						stylize(feature[h], '#ee9900', '#ee9900', 0.4);
						feature[h].described = false;
						if (selectedFeature !== undefined && feature[h].graph == selectedFeature.graph) {
							stylize(feature[h], 'blue', 'blue', 0.4);
							feature[h].described = false;
						}
					}
				}
				h++;
			}
		});

	});
	check_described.done(function() {
		annotator.vectorLayer.redraw();
	});
}



/*

Function to create a new dialog for each allograph clicked

*/

function create_dialog(selectedFeature, id) {
	if (typeof allow_multiple_dialogs == "undefined") {
		allow_multiple_dialogs = false;
	}
	if (allow_multiple_dialogs === false) {
		$('.dialog_annotations').parent('.ui-dialog').remove();
		$('.dialog_annotations').remove();
	}

	$('#annotations').append('<div id="dialog' + id + '"></div>');
	var path;
	if (selectedFeature !== null) {
		var vector_id;
		for (var i = 0; i < annotator.vectorLayer.features.length; i++) {
			var feature = annotator.vectorLayer.features[i];
			if (feature.graph == selectedFeature.graph) {
				vector_id = feature.geometry.id;
				break;
			}
		}
		path = $('#' + vector_id);
	} else {
		path = $('#OpenLayers_Layer_Vector_27_svgRoot');
	}
	$('#dialog' + id).data('feature', selectedFeature);
	$('#dialog' + id).dialog({
		draggable: true,
		height: 340,
		minHeight: 340,
		resizable: true,
		close: function(event, ui) {
			$(this).dialog('destroy').empty().remove();
			$('.dialog_annotations').remove();
		},
		title: function() {
			var title;
			if (annotator.isAdmin == "True" && selectedFeature !== null) {
				title = "<span class='allograph_label'>" + selectedFeature.feature +
					"</span> <span style='position:relative;left:6%;'><span class='btn btn-small btn-primary number_annotated_allographs' data-feature = '" + selectedFeature.feature + "' title='Show all the images of this allograph'><i class= 'icon-eye-open'></i> <span class='number-allographs'></span></span><span class='url_allograph btn btn-small'>URL</span></span>";
			} else {
				if (selectedFeature !== null) {
					title = "<span class='allograph_label'>" + selectedFeature.feature + "</span> <span class='url_allograph btn btn-small'>URL</span>";
				} else {
					title = "<span class='allograph_label'>Annotation</span> <span style='position:relative;left:6%;'><span class='url_allograph btn btn-small'>URL</span></span>";
				}
			}
			return title;
		},
		position: {
			my: "right",
			at: "right",
			of: path
		}
	}).addClass('dialog_annotations');
	var pin = "<span title='Minimize box' class='pull-right pin-box'>-</span>";
	$('.ui-dialog-title').after(pin);

	// Minimize the dialog
	$('.pin-box').click(function() {
		var dialog = $('.pin-box').parent().parent();
		if (dialog.data('pinned')) {
			$(this).html('-').css({
				'line-height': 1,
				'font-size': "30px"
			});
			var position = dialog.data('position');
			var height = dialog.data('height');
			$('.dialog_annotations').show();
			dialog.animate({
				'top': position.top,
				'left': position.left,
				'height': height,
				'box-shadow': '0px 0px 12px rgba(45, 45, 45, 0.498039)'
			}, 300).resizable().draggable();
			dialog.data('pinned', false);
		} else {
			$(this).html('&#9633;').css({
				'line-height': 1.5,
				'font-size': "20px"
			});
			var position = dialog.position();
			console.log(position);
			var height = dialog.css('height');
			var allograph_position = $('.number_annotated_allographs');
			$('.dialog_annotations').hide();
			dialog.animate({
				'top': allograph_position.position().top - 10,
				'left': allograph_position.position().left + 60,
				'height': '40px',
				'box-shadow': 'none'
			}, 300).resizable('destroy').draggable('destroy');
			dialog.data('position', position);
			dialog.data('height', height);
			dialog.data('pinned', true);
		}
	});


	// Showing all the allographs of a given allograph
	$('.number_annotated_allographs').click(function() {
		open_allographs();
	});
}

function open_allographs() {
	if ($('.letters-allograph-container').length) {
		$('.letters-allograph-container').remove();
	}
	$(this).addClass('active');
	var allograph = $('#id_allograph option:selected').text();
	if (allograph) {
		var features = annotator.vectorLayer.features;
		for (var i = 0; i < features.length; i++) {
			if (features[i].feature == allograph) {
				var feature = features[i].graph;
				var character = features[i].character_id;
				break;
			}
		}
		if (!feature && !character) {
			return false;
		}

		var url = "graph/" + feature + "/" + character + "/allographs_by_graph/";
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
		div.draggable().resizable();
		var top_div = $("<div id='top_div_annotated_allographs'>");
		top_div.append("<span>" + allograph + "</span><i title='Close box' class='icon pull-right icon-remove close_top_div_annotated_allographs'></i>");
		div.append(top_div);
		var container_div = $("<div id='container-letters-popup'>");
		container_div.css('padding', '1.5%');
		div.append(container_div);
		$('body').append(div);
		var img = $("<img>");
		img.attr('src', '/static/images/ajax-loader3.gif');
		$('#top_div_annotated_allographs').find('span').after(img);
		features.done(function(data) {
			if (data != "False") {
				img.remove();
				var s = '';
				for (i = 0; i < data.length; i++) {
					if (i == 0) {
						s += "<label style='border-bottom:1px dotted #efefef;'>Hand: " + data[i].hand_name + "</label>\n";
					}
					if (typeof data[i + 1] != "undefined" && data[i].hand != data[i + 1].hand) {
						s += "<label style='border-bottom:1px dotted #efefef;margin-top:1%;'>Hand: " + data[i + 1].hand_name + "</label>\n";
					}
					s += "<span class='vector_image_link' data-vector-id='" + data[i].vector_id + "'>" + data[i].image + '</span>\n';
				}
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
			} else {
				img.remove();
				var s = "<p><label>No Annotations</label></p>";
				container_div.html(s);
			}

		});
	}
}


function refresh_letters_container(allograph, allograph_id) {
	var features = annotator.vectorLayer.features;
	var character;
	for (i = 0; i < features.length; i++) {
		if (features[i].feature == allograph) {
			character_id = features[i].character_id;
			break;
		}
	}
	var url = "allographs/" + allograph_id + "/" + character_id + "/allographs_by_allograph/";
	var features = $.getJSON(url);
	var img = $("<img>");
	img.attr('src', '/static/images/ajax-loader3.gif');
	$('#top_div_annotated_allographs').find('span').html(allograph).after(img);
	features.done(function(data) {
		img.remove();
		var container_div = $('#container-letters-popup');
		var s = '';
		for (i = 0; i < data.length; i++) {
			if (i == 0) {
				s += "<label style='border-bottom:1px dotted #efefef;'>Hand: " + data[i].hand_name + "</label>\n";
			}
			if (typeof data[i + 1] != "undefined" && data[i].hand != data[i + 1].hand) {
				s += "<label style='border-bottom:1px dotted #efefef;margin-top:1%;'>Hand: " + data[i + 1].hand_name + "</label>\n";
			}
			s += "<span class='vector_image_link' data-vector-id='" + data[i].vector_id + "'>" + data[i].image + '</span>\n';
		}
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
	});
}

/*

Function to fill the content of a dialog

*/

function fill_dialog(id, annotation) {
	var can_edit = $('#development_annotation').is(':checked');
	if (can_edit) {
		var s = "<input type='hidden' name='allograph' id='hidden_allograph' /> <input type='hidden' id='hidden_hand' name='hand' />";
		s += "<div id='box_features_container'></div>";
		$('#dialog' + id).html(s);

		/*
		$('.url_allograph').before(" <span id='save_features_titlebar' class='btn btn-small btn-success'>Save</span> ");
		$('#save_features_titlebar').click(function() {
			annotator.saveAnnotation();
			reload_described_annotations();
		});
		*/

		$('#id_allograph').on('change', function() {
			updateFeatureSelect(annotation);
		});
		$('#id_hand').on('change', function() {
			$('#hidden_hand').val($(this).val());
		});
	}

	$('.url_allograph').click(function() {
		if ($('#dialog' + id).find('.allograph_url_div').length === 0) {
			var url = $("<div class='allograph_url_div'>");
			var allograph_url;
			var input = $('<input type="text" disabled>');
			if (annotation !== null && annotation.stored) {
				allograph_url = window.location.hostname + document.location.pathname + '?vector_id=' + annotator.selectedFeature.id;
			} else {
				var geometryObject = annotator.selectedFeature;
				var geoJSONText = annotator.format.write(geometryObject);
				allograph_url = window.location.hostname + document.location.pathname + '?temporary_vector=' + geoJSONText;
			}
			input.val(allograph_url);
			url.append(input);
			$('#dialog' + id).prepend(url);
			$('.allograph_url_div input').select();
		} else {
			$('.allograph_url_div').fadeOut().remove();
		}
	});

	var hidden_hand = $('#id_hand').val();
	var hidden_allograph = $('#id_allograph').val();

	$('#hidden_hand').val(hidden_hand);
	$('#hidden_allograph').val(hidden_allograph);

}

function showBox(selectedFeature) {

	/*
    var ex_id = $('.dialog_annotations').attr('id');
    if($('#' + ex_id).data('feature') == selectedFeature){
        $(this).focus();
    }
    */


	var id = Math.random().toString(36).substring(7);

	if (selectedFeature === null) {
		create_dialog(null, id);
		fill_dialog(id, selectedFeature);
		return false;
	}


	if (annotator.boxes_on_click) {
		var url = 'graph/' + selectedFeature.graph + '/features/';
		array_features_owned = features_owned(selectedFeature, url);
		create_dialog(selectedFeature, id);
		var can_edit = $('#development_annotation').is(':checked');
		if (can_edit) {
			var request = $.getJSON("graph/" + selectedFeature.graph, function(data) {
				return data;
			});
			var features = annotator.vectorLayer.features;
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
						s += "<div id='component_" + component_id + "' data-hidden='true' class='feature_containers'>";
						$.each(features, function(idx) {
							var value = component_id + '::' + features[idx].id;
							var names = component + ':' + features[idx].name;
							if (array_features_owned.indexOf(names) >= 0) {
								s += "<p><input checked = 'checked' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + names + "' /> " + features[idx].name;
							} else {
								s += "<p><input type='checkbox' value='" + value + "' class='features_box' data-feature = '" + names + "'/> " + features[idx].name;
							}
						});
						s += "</p></div>";
					});
					s += "</div>";
					$('#dialog' + id).html(s);

					var url_allograph_div = false;

					$('.url_allograph').click(function() {
						if (!url_allograph_div) {
							if ($('#dialog' + id).find('.allograph_url_div').length === 0) {
								var url = $("<div class='allograph_url_div'>");
								var input = $('<input type="text" disabled>');
								var allograph_url = window.location.hostname + document.location.pathname + '?vector_id=' + annotator.selectedFeature.id;
								input.val(allograph_url);
								url.html(input);
								$('#dialog' + id).prepend(url);
								$('.allograph_url_div input').select();
								url_allograph_div = true;
							}
						} else {
							var url = $(".allograph_url_div");
							url.fadeOut().remove();
							url_allograph_div = false;
						}
					});

					$('.component_labels').click(function() {
						var div = $("#" + $(this).data('id'));
						if (div.data('hidden') === false) {
							div.slideUp().data('hidden', true);
							$(this).find('.arrow_component').removeClass('icon-arrow-up').addClass('icon-arrow-down');

						} else {
							div.slideDown().data('hidden', false);
							$(this).find('.arrow_component').removeClass('icon-arrow-down').addClass('icon-arrow-up');
						}
					});

					var n = 0;
					var features = annotator.vectorLayer.features;
					for (var i = 0; i < features.length; i++) {
						if (features[i].feature == annotator.selectedFeature.feature) {
							n++;
						}
					}
					if ($(".number_annotated_allographs").length) {
						$(".number_annotated_allographs .number-allographs").html(n);
					}
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
					$('#dialog' + id).html(s);
				}
			});

			var url_allograph_div = false;
			$('.url_allograph').click(function() {
				if (!url_allograph_div) {
					if ($('#dialog' + id).find('.allograph_url_div').length === 0) {
						var url = $("<div class='allograph_url_div'>");
						var input = $('<input type="text" disabled>');
						var allograph_url = window.location.hostname + document.location.pathname + '?vector_id=' + annotator.selectedFeature.id;
						input.val(allograph_url);
						url.html(input);
						$('#dialog' + id).prepend(url);
						$('.allograph_url_div input').select();
						url_allograph_div = true;
					}
				} else {
					var url = $(".allograph_url_div");
					url.fadeOut().remove();
					url_allograph_div = false;
				}
			});

		}
	}

	$('#hidden_hand').val(selectedFeature.hidden_hand);
	$('#hidden_allograph').val(getKeyFromObjField(selectedFeature, 'hidden_allograph'));
	$('#id_hand').val(selectedFeature.hidden_hand);
	$('#id_allograph').val(getKeyFromObjField(selectedFeature, 'hidden_allograph'));
	$('select').trigger('liszt:updated');
	highlight_vectors();
	updateFeatureSelect();
	$('#box_features_container p').click(function() {
		var checkbox = $(this).find('input');
		if (checkbox.is(':checked')) {
			checkbox.attr('checked', false);
		} else {
			checkbox.attr('checked', "checked");
		}
	});

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

		$.ajax({
			url: 'delete/' + featureId + '/',
			data: '',
			error: function(xhr, textStatus, errorThrown) {
				alert('Error: ' + textStatus);
			},
			success: function(data) {
				if (data.success === false) {
					handleErrors(data);
				} else {
					$('#status').addClass('alert alert-error');
					updateStatus('Deleted annotation.');
					_self.loadAnnotations();
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
};

function highlight_vectors() {
	$('.active-result').on('mouseover', function() {
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
	$('.active-result').on('mouseout', function() {
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
			$('#status').html('Saving ...');
		},
		error: function(xhr, textStatus, errorThrown) {
			$('#status').attr('class', 'alert alert-error');
			updateStatus(textStatus);
			annotator.setSavedAttribute(feature, Annotator.UNSAVED, false);
		},
		success: function(data) {
			if (data.success === false) {
				handleErrors(data);
			} else {
				$('#status').attr('class', 'alert alert-success');
				$('#status').html('Saved annotation.');
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
 * Displays an alert for each error in the data.
 *
 * @param data
 *              Object with errors.
 */

function handleErrors(data) {
	$('#status').attr('class', 'alert alert-error');
	if (data != "error") {
		var errors = [];
		for (var e in data.errors) {
			errors.push(e);
		}
	} else {
		var errors = "Errors"
	}
	updateStatus(errors);
}

/**
 * Updates the status message of the last operation.
 *
 * @param msg
 *              Status message to display.
 */

function updateStatus(msg) {
	var s = '';
	if (typeof msg == 'object') {
		for (var i = 0; i < msg.length; i++) {
			s += "<p>Select the " + msg[i] + "</p>";
		}
	} else {
		s = msg;
	}
	$('#status').html(s);

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
	if (!(this.fullScreen.active) || (this.fullScreen.active == null) || (this.fullScreen.active == undefined)) {
		$('#map').css({
			'width': '100%',
			'height': '100%',
			'position': 'absolute',
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
}

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
	var activeControls = _self.map.getControlsBy('active', true);
	$(document).bind('keyup', function(event) {
		if (event.shiftKey) {
			_self.rectangleFeature.activate();
			_self.dragFeature.deactivate();
		}
	});
	$(document).bind('keydown', function(event) {
		var code = (event.keyCode ? event.keyCode : event.which);
		if (event.altKey) {
			switch (code) {
				case 77:
					activeControls[activeControls.length - 1].deactivate();
					_self.modifyFeature.activate();
					break;
				case 8:
					activeControls[activeControls.length - 1].deactivate();
					_self.deleteFeature.activate();
					break;
				case 84:
					activeControls[activeControls.length - 1].deactivate();
					_self.transformFeature.activate();
					break;
				case 68:
					activeControls[activeControls.length - 1].deactivate();
					_self.duplicateFeature.activate();
					break;
				case 80:
					activeControls[activeControls.length - 1].deactivate();
					_self.polygonFeature.activate();
					break;
				case 82:
					activeControls[activeControls.length - 1].deactivate();
					_self.rectangleFeature.activate();
					break;
				case 71:
					activeControls[activeControls.length - 1].deactivate();
					_self.selectFeature.activate();
					break;
				case 87:
					activeControls[activeControls.length - 1].deactivate();
					_self.dragFeature.activate();
					break;
				case 90:
					activeControls[activeControls.length - 1].deactivate();
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
}