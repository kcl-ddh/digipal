var ABSOLUTE_URL = '/digipal/page/';

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
			updateStatus('Annotation succesfully deleted', 'success');
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
	var array_values = [];
	var features = {};
	var has_features = false;
	var features_labels = [];

	var form_serialized = form.serialize();
	var allograph = form_serialized.match('allograph=[0-9]*')[0].split('=')[1];

	if ($('.features_box').length) {
		has_features = true;
		$('.features_box').each(function() {
			if ($(this).is(':checked')) {
				array_values.push($(this).val());
			}
		});
	}

	var components = $('.feature_containers');
	$.each(components, function() {
		if ($(this).find('.features_box:checked').length) {
			var component_id = $(this).attr('id');
			var component_name = $('[data-id="' + component_id + '"]');
			var component = $.trim(component_name.children('b').text());
			var features_labels_array = [];
			var features_input = $(this).find('.features_box:checked');
			$.each(features_input, function() {
				var f_id = $(this).attr('id');
				var label_element = $('label[for="' + f_id + '"');
				features_labels_array.push(label_element.text());
			});
			features_labels.push({
				'feature': features_labels_array,
				'name': component
			});
		}
	});

	features.has_features = has_features;
	features.features = array_values;
	obj['feature'] = array_values;

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
	var id = self.dialog.temp.vector_id;

	$.ajax({
		url: url + '/' + id,
		data: data,
		beforeSend: function() {
			updateStatus('Saving annotation', 'success');
		},
		error: function(xhr, textStatus, errorThrown) {
			console.log(textStatus, 'error');
			updateStatus('Error in saving annotation', 'danger');
		},
		success: function(data) {
			if (callback) {
				callback();
			}
			updateStatus('Annotation successfully saved', 'success');
		}
	});
}