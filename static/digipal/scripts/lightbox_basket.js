var csrftoken = getCookie('csrftoken');
$.ajaxSetup({
	headers: {
		"X-CSRFToken": csrftoken
	}
});

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

function main() {

	var s = '';
	var collections = JSON.parse(localStorage.getItem('collections')),
		collection, collection_name;
	var url = location.href;
	var collection_name_from_url = url.split('/')[url.split('/').length - 2];
	var element_basket = $('#collection_link');
	var container_basket = $('#container_basket');

	$.each(collections, function(index, value) {
		if (index.replace(' ', '') == collection_name_from_url) {
			collection = value;
			collection_name = index;
		}
	});

	var header = $('.page-header');
	header.find('h1').html(collection_name);
	var length_basket = length_basket_elements(collection.basket) || 0;

	var graphs = [],
		images = [],
		data = {};

	if (collection.basket.annotations && collection.basket.annotations.length) {
		s += "<h3 id='header_annotations'>Annotations (" + collection.basket.annotations.length + ")</h3>";
		for (var i = 0; i < collection.basket.annotations.length; i++) {
			graphs.push(collection.basket.annotations[i]);
		}
		data.annotations = graphs;
	}

	if (collection.basket.images && collection.basket.images.length) {
		for (d = 0; d < collection.basket.images.length; d++) {
			if (typeof collection.basket.images[d] != 'number') {
				images.push(collection.basket.images[d].id);
			} else {
				images.push(collection.basket.images[d]);
			}
		}
		data.images = images;
	}

	if (!$.isEmptyObject(data)) {

		var request = $.ajax({
			type: 'POST',
			url: 'images/',
			data: {
				'data': JSON.stringify(data),
				"X-CSRFToken": csrftoken
			},
			success: function(data) {
				console.log(data);
				if (data['annotations']) {
					s += "<table class='table table-condensed'>";
					s += '<th>Annotation</th><th>Manuscript</th><th>Allograph</td><th>Hand</th><th>Scribe</th><th>Place</th><th>Date</th><th>Remove</th>';
					for (i = 0; i < data['annotations'].length; i++) {
						var annotation = data['annotations'][i];

						s += "<tr data-graph = '" + annotation[1] + "'><td data-graph = '" + annotation[1] + "'><a title='Inspect letter in manuscript viewer' href='/digipal/page/" + annotation[8] + "/?vector_id=" + annotation[7] + "'>" + annotation[0] + "</a>";
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

						if (annotation[6] !== null && annotation[6] != 'Unknown') {
							s += "<td><a title = 'Explore manuscripts written in " + annotation[6] + "' href='/digipal/page/?date=" + annotation[6] + "'>" + annotation[6] + "</a></td>";
						} else {
							s += "<td>Unknown</td>";
						}


						s += "<td><button title = 'Remove from basket' data-type='annotation' data-graph = '" + annotation[1] + "' class='remove_graph btn btn-xs btn-danger'>Remove</button></td></tr>";
					}
				}

				s += "</table>";

				if (collection.basket.images && collection.basket.images.length) {
					s += "<h3 id ='header_images'>Images (" + collection.basket.images.length + ")</h3>";
					s += "<table class='table table-condensed'>";
					s += '<th>Page</th><th>Label</td><th>Hand</th><th>Remove</th>';
					for (i = 0; i < data['images'].length; i++) {
						var image = data['images'][i];
						s += "<tr data-graph = '" + image[1] + "'><td data-graph = '" + image[1] + "'><a title ='See manuscript' href='/digipal/page/" + image[1] + "'>" + image[0] + "</a></td>";
						s += "<td data-graph = '" + image[1] + "'><a title ='See manuscript' href='/digipal/page/" + image[1] + "'>" + image[2] + "</a></td>";
						s += "<td>" + image[3] + "</td>";
						s += "<td><button title ='Remove from basket' data-type='image' data-graph = '" + image[1] + "' class='remove_graph btn btn-xs btn-danger'>Remove</button></td></tr>";
					}
					s += "</table>";
				}

				$(s).find('img').on('load', function() {

					container_basket.html(s);

					$('.remove_graph').click(function() {
						var basket = JSON.parse(localStorage.getItem('lightbox_basket'));
						var graph = $(this).data('graph');
						var type = $(this).data('type');
						var element;
						if (type == 'annotation') {
							for (i = 0; i < collection.basket.annotations.length; i++) {
								element = collection.basket.annotations[i];
								var element_graph;
								if (element.hasOwnProperty('graph')) {
									element_graph = element.graph;
								} else {
									element_graph = element;
								}
								if (graph == element_graph) {
									collection.basket.annotations.splice(i, 1);
									break;
								}
							}
							$('#header_annotations').html("Annotations (" + collection.basket.annotations.length + ")");
						} else {
							for (i = 0; i < collection.basket.images.length; i++) {
								element = collection.basket.images[i];
								if (graph == element.id) {
									basket.images.splice(i, 1);

									break;
								}
							}
							$('#header_images').html("Images (" + collection.basket.images.length + ")");
						}

						$('tr[data-graph="' + graph + '"]').fadeOut().remove();

						var length_basket = length_basket_elements(basket);

						if (length_basket == 1) {
							element_basket.html("Collection (" + length_basket + " <i class='fa fa-picture-o'> </i> )");
						} else {
							element_basket.html("Collection (" + length_basket + " <i class='fa fa-picture-o'> </i> )");
						}

						/*

						if (basket.annotations && !basket.annotations.length && basket.images && !basket.images.length) {
							s = '<div class="container alert alert-warning">The Collection is empty</div>';
							container_basket.html(s);
						}

						*/

						localStorage.setItem('lightbox_basket', JSON.stringify(basket));

					});
				});
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
		s = '<div class="container alert alert-warning">The collection is empty.</div>';
		container_basket.html(s);

		var loading_div = $(".loading-div");
		if (loading_div.length) {
			loading_div.fadeOut().remove();
		}
	}

	length_basket = length_basket_elements(collection.basket);

	if (length_basket == 1) {
		element_basket.html("Collection (" + length_basket + " <i class='fa fa-picture-o'> </i> )");
	} else {
		element_basket.html("Collection (" + length_basket + " <i class='fa fa-picture-o'> </i> )");
	}

	global_length_basket = length_basket;

}

main();