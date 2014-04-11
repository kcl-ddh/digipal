var csrftoken = getCookie('csrftoken');
$.ajaxSetup({
	headers: {
		"X-CSRFToken": csrftoken
	}
});

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
			s += "<h3 id='header_annotations'>Annotations (" + collection.annotations.length + ")</h3>";
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
		var external_collection = JSON.parse(getParameter('collection'));
		data = external_collection;
		collection_name = data['name'];
		collection = data;
		isExternal = true;
	}

	var header = $('.page-header');
	header.find('.collection-title').html(collection_name);
	$('#breadcrumb-current-collection').html(collection_name);
	var length_basket = length_basket_elements(collection) || 0;

	if (!$.isEmptyObject(data)) {

		var request = $.ajax({
			type: 'POST',
			url: '/digipal/collection/' + collection_name.replace(' ', '') + '/images/',
			data: {
				'data': JSON.stringify(data),
				"X-CSRFToken": csrftoken
			},
			success: function(data) {

				if (data['annotations']) {
					s += "<table id='table-annotations' class='table'>";
					s += '<th><input data-toggle="tooltip" title="Toggle all" type="checkbox" id="check_annotations_all" checked /></th><th>Annotation</th><th>Manuscript</th><th>Allograph</td><th>Hand</th><th>Scribe</th><th>Place</th><th>Remove</th>';
					for (i = 0; i < data['annotations'].length; i++) {
						var annotation = data['annotations'][i];

						s += "<tr data-graph = '" + annotation[1] + "'><td><input data-toggle='tooltip' title='Toggle item' data-graph = '" + annotation[1] + "' type='checkbox' checked /></td><td data-graph = '" + annotation[1] + "'><a title='Inspect letter in manuscript viewer' href='/digipal/page/" + annotation[8] + "/?vector_id=" + annotation[7] + "'>" + annotation[0] + "</a>";
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


						s += "<td><button data-toggle='tooltip' title = 'Remove from collection' data-type='annotation' data-graph = '" + annotation[1] + "' class='remove_graph btn btn-xs btn-danger'><i class='glyphicon glyphicon-remove'></i></button></td></tr>";
					}
				}

				s += "</table>";

				if (collection.images && collection.images.length) {
					s += "<h3 id ='header_images'>Images (" + collection.images.length + ")</h3>";
					s += "<table id='table-images' class='table'>";
					s += '<th><input data-toggle="tooltip" title="Toggle all" type="checkbox" id="check_images_all" checked /></th><th>Page</th><th>Label</td><th>Hand</th><th>Remove</th>';
					for (i = 0; i < data['images'].length; i++) {
						var image = data['images'][i];
						s += "<tr data-graph = '" + image[1] + "'><td><input data-toggle='tooltip' title='Toggle item' data-graph = '" + image[1] + "' type='checkbox' checked /><td data-graph = '" + image[1] + "'><a title ='See manuscript' href='/digipal/page/" + image[1] + "'>" + image[0] + "</a></td>";
						s += "<td data-graph = '" + image[1] + "'><a title ='See manuscript' href='/digipal/page/" + image[1] + "'>" + image[2] + "</a></td>";
						s += "<td>" + image[3] + "</td>";
						s += "<td><button data-toggle='tooltip' title ='Remove from collection' data-type='image' data-graph = '" + image[1] + "' class='remove_graph btn btn-xs btn-danger'><i class='glyphicon glyphicon-remove'></i></button></td></tr>";
					}
					s += "</table>";
				}

				if (isExternal) {
					var alert_string = "<div id='alert-save-collection' class='alert alert-success'>This is an external collection. Do you want to save it?  <div class='pull-right'><input type='button' id='save-collection' class='btn btn-xs btn-success' value='Save' /> <input id='close-alert' type='button' class='btn btn-xs btn-danger' value='Close' /></div> </div>";
					s = alert_string + s;
				}

				container_basket.html(s);

				$('.remove_graph').click(function() {
					var basket;
					$.each(collections, function(index, value) {
						if (value.id == selectedCollection) {
							basket = value;
							basket['name'] = index;
						}
					});

					var graph = $(this).data('graph');
					var type = $(this).data('type');
					var element;
					if (type == 'annotation') {
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
						$('#header_annotations').html("Annotations (" + basket.annotations.length + ")");
					} else {
						for (i = 0; i < basket.images.length; i++) {
							image_id = basket.images[i];
							if (graph == image_id) {
								basket.images.splice(i, 1);
								break;
							}
						}
						$('#header_images').html("Images (" + basket.images.length + ")");
					}

					$('tr[data-graph="' + graph + '"]').fadeOut().remove();
					element_basket.html(basket['name'] + ' (' + sum_images_collection(basket) + ' <i class="fa fa-picture-o"></i> )');

					if (!sum_images_collection(basket)) {
						var s = '<div class="container alert alert-warning"><p>The collection is empty.</p>';
						s += '<p>Start adding images from <a href="/digipal/page">Browse Images</a> or using the Digipal <a href="http://127.0.0.1:8000/digipal/search/?from_link=true">search engine</a></div>';
						container_basket.html(s);
					}

					localStorage.setItem('collections', JSON.stringify(collections));

				});

				$('#check_images_all').on('change', function() {
					if ($(this).is(':checked')) {
						$('#table-images').find('input[type="checkbox"]').prop('checked', true);
					} else {
						$('#table-images').find('input[type="checkbox"]').prop('checked', false);
					}
				});

				$('#check_annotations_all').on('change', function() {
					if ($(this).is(':checked')) {
						$('#table-annotations').find('input[type="checkbox"]').prop('checked', true);
					} else {
						$('#table-annotations').find('input[type="checkbox"]').prop('checked', false);
					}
				});

				$('#to_lightbox').click(function() {
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

				$('#close-alert').click(function() {
					$('#alert-save-collection').fadeOut().remove();
				});

				$('#save-collection').click(function() {
					save_collection(collection);
					$('#alert-save-collection').fadeOut().remove();
					notify('Collection succesfully saved', 'success');
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


	header.find('.collection-title').on('blur', function() {

		var name = $(this).text(),
			flag = false;

		$.each(collections, function(index, value) {
			if (name == index) {
				flag = false;
				return false;
			} else {
				if (value.id == selectedCollection) {
					collections[name] = collections[index];
					delete collections[index];
					basket = value;
					history.pushState(null, null, '../' + name);
					flag = true;
					return false;
				}
			}
		});

		if (flag) {
			localStorage.setItem('collections', JSON.stringify(collections));
			element_basket.html(name + ' (' + sum_images_collection(basket) + ' <i class="fa fa-picture-o"></i> )');
			$('#breadcrumb-current-collection').html(name);
			notify("Collection renamed as " + name, 'success');
		} else {
			return false;
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
		});
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