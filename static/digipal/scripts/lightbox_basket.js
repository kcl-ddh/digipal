(function() {
	var csrftoken = getCookie('csrftoken');
	$.ajaxSetup({
		headers: {
			"X-CSRFToken": csrftoken
		}
	});
})();

var sum_images_collection = function(basket) {
	var n = 0;
	if (basket.annotations) {
		n += basket.annotations.length;
	}

	if (basket.images) {
		n += basket.images.length;
	}
	return n;
};

var selectedAnnotations = function() {
	var checkboxes = $('.checkbox_image');
	var graphs = {};
	var n = 0;
	$.each(checkboxes, function() {
		if ($(this).is(':checked')) {
			graphs[$(this).data('graph')] = $(this).data('type');
			n++;
		}
	});
	return {
		'graphs': graphs,
		'graphs_number': n
	};
};

function update_counter() {
	var checkboxes = $('.checkbox_image');
	var check_annotations_all = $('#check_annotations_all');
	var check_images_all = $('#check_images_all');
	var annotations = 0;
	var images = 0;
	$.each(checkboxes, function() {
		if ($(this).is(':checked')) {
			if ($(this).data('type') == 'image') {
				images++;
			} else {
				annotations++;
			}
		}
	});
	$('#counter-annotations').html(annotations);
	$('#counter-images').html(images);

	if (!annotations) {
		check_annotations_all.prop('checked', false).prop('indeterminate', false);
	} else if ($('#table-annotations .table-row').length == annotations) {
		check_annotations_all.prop('checked', true).prop('indeterminate', false);
	} else {
		check_annotations_all.prop('indeterminate', true);
	}

	if (!images) {
		check_images_all.prop('checked', false).prop('indeterminate', false);
	} else if ($('#table-images .table-row').length == images) {
		check_images_all.prop('checked', true).prop('indeterminate', false);
	} else {
		check_images_all.prop('indeterminate', true);
	}

	if (!images && !annotations) {
		$('#remove_from_collection').attr('disabled', true);
	} else {
		$('#remove_from_collection').attr('disabled', false);
	}

}

function main() {

	var s = '';
	var element_basket = $('#collection_link');
	var container_basket = $('#container_basket');
	var collection, collection_name, data = {};
	var isExternal = false;

	if (!getParameter('collection').length) {
		var collections = JSON.parse(localStorage.getItem('collections'));
		var url = location.href;
		var collection_name_from_url = url.split('/')[url.split('/').length - 2];
		var selectedCollection = localStorage.getItem('selectedCollection');

		$.each(collections, function(index, value) {
			if (index.replace(/\s+/gi, '') == collection_name_from_url) {
				collection = value;
				collection_name = index;
			}
		});

		if (!collection) {
			location.href = "../";
		}

		var graphs = [],
			images = [];

		if (typeof collection.annotations !== 'undefined' && collection.annotations.length) {
			s += "<h3 id='header_annotations'>Graphs (" + collection.annotations.length + ")</h3>";
			for (var i = 0; i < collection.annotations.length; i++) {
				graphs.push(collection.annotations[i]);
			}
			data.annotations = graphs;
		}

		if (typeof collection.images !== 'undefined' && collection.images.length) {
			for (d = 0; d < collection.images.length; d++) {
				if (typeof collection.images[d] != 'number') {
					images.push(collection.images[d].id);
				} else {
					images.push(collection.images[d]);
				}
			}
			data.images = images;
		}

	} else {
		/*
		var external_collection = JSON.parse(getParameter('collection'));
		data = external_collection;
		collection_name = data['name'];
		collection = data;
		isExternal = true;
		*/

		// GN: hack here to unescape the param, although it should already have been unescaped in GetParam
		// so I imagine the param has been escaped twice before...
		var collection_param = getParameter('collection');
		if (collection_param.length) {
			collection_param = collection_param[0];
			if (collection_param.lastIndexOf('%', 0) === 0) {
				collection_param = unescape(collection_param);
			}
			var external_collection = JSON.parse(collection_param);

			data = external_collection;
			collection_name = data['name'];
			collection = data;
			isExternal = true;
		}

	}

	var header = $('.page-header');
	header.find('.collection-title').html(collection_name);
	$('#breadcrumb-current-collection').html(collection_name);
	var length_basket = length_basket_elements(collection) || 0;

	$('#delete-collection').attr('data-original-title', 'Delete ' + collection_name);
	$('#share-collection').attr('data-original-title', 'Share ' + collection_name);

	if (!$.isEmptyObject(data)) {

		var request = $.ajax({
			type: 'POST',
			url: '/digipal/collection/' + collection_name.replace(/\s*/gi, '') + '/images/',
			contentType: 'application/json',
			data: {
				'data': JSON.stringify(data)
			},
			success: function(data) {

				if (data['annotations']) {
					s += "<table id='table-annotations' class='table'>";
					s += '<th><span id="counter-annotations"></span><input data-toggle="tooltip" title="Toggle all" type="checkbox" id="check_annotations_all" /></th><th>Graph</th><th>Manuscript</th><th>Allograph</td><th>Hand</th><th>Scribe</th><th>Place</th>';
					for (i = 0; i < data['annotations'].length; i++) {
						var annotation = data['annotations'][i];

						s += "<tr class='table-row' data-graph = '" + annotation[1] + "'><td><input data-toggle='tooltip' title='Toggle item' data-graph = '" + annotation[1] + "' type='checkbox' data-type='annotation' class='checkbox_image' /></td><td data-graph = '" + annotation[1] + "'><a title='Inspect letter in manuscript viewer' href='/digipal/page/" + annotation[8] + "/?vector_id=" + annotation[7] + "'>" + annotation[0] + "</a>";
						s += "</td>";

						s += "<td data-graph = '" + annotation[1] + "'><a title='Go to manuscript page' href='/digipal/page/" + annotation[8] + "'>" + annotation[14] + "</a>";
						s += "</td>";

						s += "<td><a title='Go to " + annotation[11] + "' href='/digipal/search/graph/?character_select=" + annotation[13] + "&allograph_select=" + annotation[12] + "'>" + annotation[11] + "</a></td>";

						if (annotation[3] !== null && annotation[3] != 'Unknown') {
							s += "<td><a title='Go to Hand' href='/digipal/hands/" + annotation[9] + "'>" + annotation[3] + "</a></td>";
						} else {
							s += "<td>Unknown</td>";
						}


						if (annotation[4] !== null && annotation[4] != 'Unknown') {
							s += "<td><a title = 'Go to Scribe' href='/digipal/scribes/" + annotation[10] + "'>" + annotation[4] + "</a></td>";
						} else {
							s += "<td>Unknown</td>";
						}

						if (annotation[5] !== null && annotation[5] != 'Unknown') {
							s += "<td><a title = 'Explore manuscripts in " + annotation[5] + "' href='/digipal/page/?town_or_city=" + annotation[5] + "'>" + annotation[5] + "</a></td>";
						} else {
							s += "<td>Unknown</td>";
						}

						/*if (annotation[6] !== null && annotation[6] != 'Unknown') {
							s += "<td><a title = 'Explore manuscripts written in " + annotation[6] + "' href='/digipal/page/?date=" + annotation[6] + "'>" + annotation[6] + "</a></td>";
						} else {
							s += "<td>Unknown</td>";
						}*/

					}
				}

				s += "</table>";

				if (collection.images && collection.images.length) {
					s += "<h3 id ='header_images'>Images (" + collection.images.length + ")</h3>";
					s += "<table id='table-images' class='table'>";
					s += '<th><span id="counter-images"></span><input data-toggle="tooltip" title="Toggle all" type="checkbox" id="check_images_all" /></th><th>Page</th><th>Label</td><th>Hand</th>';
					for (i = 0; i < data['images'].length; i++) {
						var image = data['images'][i];
						s += "<tr data- class='table-row' data-graph = '" + image[1] + "'><td><input data-toggle='tooltip' title='Toggle item' data-graph = '" + image[1] + "' type='checkbox' data-type='image' class='checkbox_image' /><td data-graph = '" + image[1] + "'><a title ='See manuscript' href='/digipal/page/" + image[1] + "'>" + image[0] + "</a></td>";
						s += "<td data-graph = '" + image[1] + "'><a title ='See manuscript' href='/digipal/page/" + image[1] + "'>" + image[2] + "</a></td>";
						s += "<td>" + image[3] + "</td>";
					}
					s += "</table>";
				}

				if (isExternal) {
					var alert_string = "<div id='alert-save-collection' class='alert alert-success'>This is an external collection. Do you want to save it?  <div class='pull-right'><input type='button' id='save-collection' class='btn btn-xs btn-success' value='Save' /> <input id='close-alert' type='button' class='btn btn-xs btn-danger' value='Close' /></div> </div>";
					s = alert_string + s;
				}

				container_basket.html(s);
				update_counter();
				$('#check_images_all').on('change', function() {
					if ($(this).is(':checked')) {
						$('#table-images').find('input[type="checkbox"]').prop('checked', true);
						$('#table-images').find('.table-row').addClass('selected');
					} else {
						$('#table-images').find('input[type="checkbox"]').prop('checked', false);
						$('#table-images').find('.table-row').removeClass('selected');
					}
					update_counter();
				});

				$('#check_annotations_all').on('change', function() {
					if ($(this).is(':checked')) {
						$('#table-annotations').find('input[type="checkbox"]').prop('checked', true);
						$('#table-annotations').find('.table-row').addClass('selected');
					} else {
						$('#table-annotations').find('input[type="checkbox"]').prop('checked', false);
						$('#table-annotations').find('.table-row').removeClass('selected');
					}
					update_counter();
				});

				$('#remove_from_collection').on('click', function() {

					var basket;
					$.each(collections, function(index, value) {
						if (value.id == selectedCollection) {
							basket = value;
							basket['name'] = index;
						}
					});

					var graph, type;
					var element;
					var selectedannotations = selectedAnnotations();
					var graphs = selectedannotations.graphs;
					var graphs_number = selectedannotations.graphs_number;

					if (!$(".loading-div").length) {
						var loading_div = $("<div class='loading-div'>");
						var background = $("<div class='dialog-background'>");
						loading_div.html('<h2>Removing images</h2>');
						loading_div.append("<p>You are about to remove " + graphs_number + " images. Continue?");
						loading_div.append("<p><button class='btn btn-success btn-sm' id='remove_images_from_collection'>Remove</button> <button class='btn btn-danger btn-sm' id='cancel'>Cancel</button></p>");
						background.append(loading_div);
						$('body').append(background);
					}
					$('#remove_images_from_collection').on('click', function() {
						$.each(graphs, function(index, value) {
							graph = index;
							type = value;
							if (type == 'annotation') {
								if (basket.annotations && basket.annotations.length) {
									for (i = 0; i < basket.annotations.length; i++) {
										element = basket.annotations[i];
										var element_graph;
										if (element.hasOwnProperty('graph')) {
											element_graph = element.graph;
										} else {
											element_graph = element;
										}
										if (graph == element_graph) {
											basket.annotations.splice(i, 1);
											break;
										}
									}
								}
								$('#header_annotations').html("Annotations (" + basket.annotations.length + ")");
							} else {
								if (basket.images && basket.images.length) {
									for (i = 0; i < basket.images.length; i++) {
										image_id = basket.images[i];
										if (graph == image_id) {
											basket.images.splice(i, 1);
											break;
										}
									}
								}
								$('#header_images').html("Images (" + basket.images.length + ")");
							}

							$('tr[data-graph="' + graph + '"]').fadeOut().remove();
							update_counter();
						});

						if (!sum_images_collection(basket)) {
							var s = '<div class="container alert alert-warning"><p>The collection is empty.</p>';
							s += '<p>Start adding images from <a href="/digipal/page">Browse Images</a> or using the Digipal <a href="/digipal/search/?from_link=true">search engine</a></div>';
							container_basket.html(s);
						}

						localStorage.setItem('collections', JSON.stringify(collections));
						background.fadeOut().remove();
						update_collection_counter();
					});

					$('#cancel').on('click', function() {
						background.fadeOut().remove();
					});

				});

				$('#to_lightbox').on('click', function() {
					var graphs = [],
						images = [],
						element,
						basket;

					var selectedCollection = localStorage.getItem('selectedCollection');
					var collections = JSON.parse(localStorage.getItem('collections'));

					$.each(collections, function(index, value) {
						if (value.id == selectedCollection) {
							basket = value;
						}
					});

					if (basket && basket.annotations && basket.annotations.length) {
						for (i = 0; i < basket.annotations.length; i++) {
							if (basket.annotations[i].hasOwnProperty('graph')) {
								element = basket.annotations[i].graph;
							} else {
								element = basket.annotations[i];
							}
							if ($('input[type="checkbox"][data-graph="' + element + '"]').is(':checked')) {
								graphs.push(element);
							}
						}
					}
					if (basket && basket.images && basket.images.length) {
						for (i = 0; i < basket.images.length; i++) {
							element = basket.images[i];
							if ($('input[type="checkbox"][data-graph="' + element + '"]').is(':checked')) {
								images.push(element);
							}
						}
					}
					location.href = '/lightbox/?annotations=[' + graphs.toString() + ']&images=[' + images.toString() + ']';
				});

				$('tr.table-row').on('click', function(event) {

					var checkbox = $(this).find('.checkbox_image');

					if ($(this).hasClass('selected')) {
						$(this).removeClass('selected');
						checkbox.prop('checked', false);
					} else {
						$(this).addClass('selected');
						checkbox.prop('checked', true);
					}
					update_counter();
					event.stopPropagation();
					event.stopImmediatePropagation();
				});

				$('#close-alert').click(function() {
					$('#alert-save-collection').fadeOut().remove();
				});

				$('#save-collection').click(function() {
					save_collection(collection);
					$('#alert-save-collection').fadeOut().remove();
					notify('Collection successfully saved', 'success');
				});

				$('[data-toggle="tooltip"]').tooltip();

			},

			complete: function() {
				var loading_div = $(".loading-div");
				if (loading_div.length) {
					loading_div.fadeOut().remove();
				}
			},

			error: function() {

				var s = '<div class="container alert alert-warning">Something has gone wrong. Please refresh the page and try again.</div>';
				container_basket.html(s);

				var loading_div = $(".loading-div");
				if (loading_div.length) {
					loading_div.fadeOut().remove();
				}
			}
		});

	} else {
		s = '<div class="container alert alert-warning"><p>The collection is empty.</p>';
		s += '<p>Start adding images from <a href="/digipal/page">Browse Images</a> or using the Digipal <a href="http://127.0.0.1:8000/digipal/search/?from_link=true">search engine</a></div>';

		container_basket.html(s);

		var loading_div = $(".loading-div");
		if (loading_div.length) {
			loading_div.fadeOut().remove();
		}
	}

	$('#delete-collection').add($('#share-collection')).tooltip();

	header.find('.collection-title').on('blur', function() {
		if (!$(this).data('active')) {
			$(this).data('active', true);
			var collections = JSON.parse(localStorage.getItem('collections'));
			var name = $(this).text(),
				flag = false;

			$.each(collections, function(index, value) {
				if (name == index) {
					flag = false;
					return false;
				} else {
					if (value.id == selectedCollection) {
						var re = /^\w*$/;
						name = name.replace(/\s+/gi, '');
						if (name && re.test(name) && name.length <= 30) {
							collections[name] = collections[index];
							delete collections[index];
							basket = value;
							history.pushState(null, null, '../' + name);
							flag = true;
							return false;
						} else {
							notify("Ensure the name entered doesn't contain special chars, nor exceeds 30 chars", 'danger');
							$('.collection-title').html(index);
							return false;
						}
					}
				}
			});

			if (flag) {
				localStorage.setItem('collections', JSON.stringify(collections));
				element_basket.html(name + ' (' + sum_images_collection(basket) + ' <i class="fa fa-picture-o"></i> )');
				element_basket.attr('href', '/digipal/collection/' + name.replace(/\s+/gi), '');
				$('#breadcrumb-current-collection').html(name);
				notify("Collection renamed as " + name, 'success');
			} else {
				return false;
			}
		}
	}).on('focus', function(event) {
		$(this).on('keyup', function(event) {
			var code = (event.keyCode ? event.keyCode : event.which);
			if (code == 13) {
				$(this).blur();
				event.preventDefault();
				return false;
			}
		}).on('keydown', function(event) {
			var code = (event.keyCode ? event.keyCode : event.which);
			if (code == 13) {
				$(this).blur();
				event.preventDefault();
				return false;
			}
		}).data('active', false);
	});

	$('#share-collection').on('click', function() {
		share([collection['id']]);
	});

	$('#delete-collection').on('click', function() {
		delete_collections([collection['id']], false, true);
	});

}

$(document).ready(function() {
	main();
});