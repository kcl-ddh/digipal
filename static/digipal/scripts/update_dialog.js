/**
 * function to update the dialog
   -- Digipal Project --> digipal.eu
 */

/**
 * The function update_dialog() allows to update the current content of the a dialog.
 * It requires two parameters:
 *	@prefix: a prefix for unifying DOM elements, can be an empty string
 *	@data: an array which contains two objects: allographs and features: this array has to be obtained
 *		from the function get_features() in annotation.py
 */

function update_dialog(prefix, data, callback) {

	var s = '<div id="box_features_container">';
	var array_features_owned = features_saved(null, data['features']);
	var allographs = data['allographs'];
	$.each(allographs, function(idx) {
		component = allographs[idx].name;
		component_id = allographs[idx].id;
		var features = allographs[idx].features;

		s += "<div class='component_labels' data-id='" + prefix + "component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component fa fa-angle-double-down'></span></b>";

		s += "<div class='checkboxes_div btn-group'><span data-toggle='tooltip' data-container='body'  title='Check all' data-component = '" + component_id + "' class='check_all btn btn-xs btn-default'><i class='fa fa-check-square-o'></i></span> <span title='Unheck all' data-toggle='tooltip' data-container='body' data-component = '" + component_id + "' class='uncheck_all btn btn-xs btn-default'><i class='fa fa-square-o'></i></span></div></div>";

		s += "<div id='" + prefix + "component_" + component_id + "' data-hidden='false' class='feature_containers'>";

		$.each(features, function(idx) {
			var value = component_id + '::' + features[idx].id;
			var id = component_id + '_' + features[idx].id;
			var names = component + ':' + features[idx].name;
			s += '<div class="row row-no-margin">';

			if (typeof annotator !== 'undefined') {
				if (annotator.selectedFeature !== undefined && annotator.selectedFeature !== null && annotator.selectedFeature.state == 'Insert') {
					array_features_owned = annotator.selectedFeature.features;
				} else {
					value = names;
				}
				if (array_features_owned.indexOf(value) >= 0) {
					s += "<p class='col-md-2'><input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "' checked /> ";
				} else {
					s += "<p class='col-md-2'><input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "' /> ";
				}
				s += "<p class='col-md-10'><label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + id + "'>" + features[idx].name + "</label></p>";
			} else {
				if (array_features_owned.indexOf(names) >= 0) {
					s += "<p class='col-md-2'> <input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "' checked />";
				} else {
					s += "<p class='col-md-2'> <input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "'/>";
				}

				s += "<p class='col-md-10'><label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + id + "'>" + features[idx].name + "</label></p>";
			}

			s += '</div>';
		});

		s += "</div>";
	});

	s += "</div>";

	callback(s);

}

/*

Function to get the features of a described allograph
@params feature selected, url
*/

function features_saved(selectedFeature, features) {
	var array_features_owned = [];
	for (var i = 0; i < features.length; i++) {
		for (var j = 0; j < features[i].feature.length; j++) {
			s = features[i].name;
			s += ':' + features[i].feature[j];
			array_features_owned.push(s);
		}
		s = '';
	}
	return array_features_owned;
}

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