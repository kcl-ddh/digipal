var ABSOLUTE_URL = '/digipal/page/';


var getCookie = function(name) {
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
};


var csrftoken = getCookie('csrftoken');
$.ajaxSetup({
	headers: {
		"X-CSRFToken": csrftoken
	}
});

function delete_annotation(image_id, feature_id, callback) {
	var url = ABSOLUTE_URL + image_id + '/delete/' + feature_id + '/';
	$.ajax({
		url: url,
		data: '',
		error: function(xhr, textStatus, errorThrown) {
			updateStatus('Error in deleting annotation', 'danger');
			throw new Error(textStatus);
		},
		success: function(data) {

			if (callback) {
				callback();
			}
			updateStatus('Annotation successfully deleted', 'success');
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

	var select_allograph = $('.myModal');

	var form = select_allograph.find('.frmAnnotation');
	var obj = {};

	var array_values_checked = [],
		array_values_unchecked = [];

	var features = {};
	var has_features = false;

	if (select_allograph.find('.features_box').length) {
		select_allograph.find('.features_box').each(function() {
			if ($(this).is(':checked') && !$(this).prop('indeterminate')) {
				array_values_checked.push($(this).val());
				has_features = true;
			} else if (!$(this).is(':checked') && !$(this).prop('indeterminate')) {
				array_values_unchecked.push($(this).val());
			}
		});
	}

	var features_labels = [];
	var components = $('.feature_containers');
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
				label_element = $('label[for="' + f_id + '"]');
				features_labels_array.push(label_element.text());
			});

			features_labels.push({
				'feature': features_labels_array,
				'name': component,
				'component_id': parseInt(f_value.split(':')[0], 10)
			});
		}
	});


	features.has_features = has_features;
	features.features = array_values_checked;
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

	var display_note, internal_note;
	display_note = $('#id_display_note');
	internal_note = $('#id_internal_note');
	if (!isNodeEmpty(display_note.html())) {
		form_serialized += "&display_note=" + display_note.html();
	}

	if (!isNodeEmpty(internal_note.html())) {
		form_serialized += "&internal_note=" + internal_note.html();
	}


	if (select_allograph.find('.aspect').length) {
		var aspects = select_allograph.find('.aspect');
		aspects.each(function() {
			if ($(this).is(':checked') && !$(this).prop('indeterminate')) {
				form_serialized += "&aspect=" + $(this).val();
			} else if (!$(this).is(':checked') && !$(this).prop('indeterminate')) {
				form_serialized += "&-aspect=" + $(this).val();
			}
		});
	}

	return {
		'has_features': has_features,
		'features': features,
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

function save(url, feature, data, callback) {
	$.ajax({
		url: url,
		data: data,
		type: 'POST',
		beforeSend: function() {
			updateStatus('Saving annotation ...', 'warning');
		},
		error: function(xhr, textStatus, errorThrown) {
			updateStatus('Error in saving annotation', 'danger');
		},
		success: function(data) {
			if (data['success']) {
				updateStatus('Annotation successfully saved', 'success');
			} else {
				updateStatus('Error in saving annotation', 'danger');
			}
			if (callback) {
				callback(data);
			}
		}
	});
}