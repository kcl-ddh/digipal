/**
 * Digipal Basket
   -- Digipal Project --> digipal.eu
 */

$(document).ready(function() {

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

	uniqueid = function() {
		var text = "";
		var possible = "0123456789";

		for (var i = 0; i < 3; i++)
			text += possible.charAt(Math.floor(Math.random() * possible.length));

		return text;
	};

	var csrftoken = getCookie('csrftoken');

	$.ajaxSetup({
		headers: {
			"X-CSRFToken": csrftoken
		}
	});

	var element_basket = $('#lightbox_button a');
	var container_basket = $('#container_basket');

	function main(basket) {

		var s = '';

		var graphs = [],
			images = [],
			data = {};

		if (basket.annotations && basket.annotations.length) {
			s += "<h3 id='header_annotations'>Annotations (" + basket.annotations.length + ")</h3>";
			for (var i = 0; i < basket.annotations.length; i++) {
				if (basket.annotations[i].hasOwnProperty('graph')) {
					graphs.push(basket.annotations[i].graph);
				} else {
					graphs.push(basket.annotations[i]);
				}

			}
			data.annotations = graphs;
		}

		if (basket.images && basket.images.length) {
			for (d = 0; d < basket.images.length; d++) {
				images.push(basket.images[d].id);
			}
			data.images = images;
		}

		$.ajax({
			type: 'POST',
			url: 'images/',
			data: {
				'data': JSON.stringify(data)
			},
			success: function(data) {

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


						s += "<td><button title = 'Remove from basket' data-type='annotation' data-graph = '" + annotation[1] + "' class='remove_graph btn btn-mini btn-danger'>Remove</button></td></tr>";
					}
				}

				s += "</table>";

				if (basket.images && basket.images.length) {
					s += "<h3 id ='header_images'>Images (" + basket.images.length + ")</h3>";
					s += "<table class='table table-condensed'>";
					s += '<th>Page</th><th>Label</td><th>Hand</th><th>Remove</th>';
					for (i = 0; i < data['images'].length; i++) {
						var image = data['images'][i];
						s += "<tr data-graph = '" + image[1] + "'><td data-graph = '" + image[1] + "'><a title ='See manuscript' href='/digipal/page/" + image[1] + "'>" + image[0] + "</a></td>";
						s += "<td data-graph = '" + image[1] + "'><a title ='See manuscript' href='/digipal/page/" + image[1] + "'>" + image[2] + "</a></td>";
						s += "<td>" + image[3] + "</td>";
						s += "<td><button title ='Remove from basket' data-type='image' data-graph = '" + image[1] + "' class='remove_graph btn btn-mini btn-danger'>Remove</button></td></tr>";
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
								element = basket.images[i];
								if (graph == element.id) {
									basket.images.splice(i, 1);
									break;
								}
							}
							$('#header_images').html("Images (" + basket.images.length + ")");
						}

						$('tr[data-graph="' + graph + '"]').fadeOut().remove();

						var length_basket = length_basket_elements(basket);

						if (length_basket == 1) {
							element_basket.html("Lightbox (" + length_basket + " image)");
						} else {
							element_basket.html("Lightbox (" + length_basket + " images)");
						}

						if (!basket.annotations.length && !basket.images.length) {
							s = '<div class="container alert alert-warning">The Basket is empty</div>';
							container_basket.html(s);
						}

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

				var s = '<div class="container alert alert-warning" style="margin-top:5%">Something went wrong.  Please try again refreshing the page.</div>';
				container_basket.html(s);

				var loading_div = $(".loading-div");
				if (loading_div.length) {
					loading_div.fadeOut().remove();
				}
			}
		});

		$('#to_lightbox').click(function() {
			var graphs = [],
				images = [],
				element,
				basket;

			if (getParameter('collection').length) {
				var collection = JSON.parse(localStorage.getItem('collections'));
				basket = collection[getParameter('collection')[0]]['basket'];
			} else {
				basket = JSON.parse(localStorage.getItem('lightbox_basket'));
			}

			if (basket && basket.annotations && basket.annotations.length) {
				for (i = 0; i < basket.annotations.length; i++) {
					if (basket.annotations[i].hasOwnProperty('graph')) {
						element = basket.annotations[i].graph;
					} else {
						element = basket.annotations[i];
					}
					graphs.push(element);
				}
			}
			if (basket && basket.images && basket.images.length) {
				for (i = 0; i < basket.images.length; i++) {
					element = basket.images[i].id;
					images.push(element);
				}
			}
			location.href = '/lightbox/?annotations=[' + graphs.toString() + ']&images=[' + images.toString() + ']';
		});

		$('#add_collection').click(function(event) {
			var collections = JSON.parse(localStorage.getItem('collections'));
			var window_save_collection = $('<div>');
			var lightbox_basket = JSON.parse(localStorage.getItem('lightbox_basket'));
			var s = '';
			window_save_collection.attr('class', 'loading-div');
			s += '<h3>Save Collection</h3><form>';
			s += '<div class="input-append"><input placeholder="Type collection name" type="text" id= "name_collection" />';
			s += '<button class="btn" id="save_collection" type="button">Save</button></div><form>';
			s += '<button style="margin-top:5%" class="btn btn-small pull-right btn-danger" id="close_window_collections" type="button">Close window</button>';
			window_save_collection.html(s);
			window_save_collection.css('height', '20%');
			$('body').append(window_save_collection);

			$('#save_collection').click(function(event) {
				var collection_name = $('#name_collection').val();
				var id;
				if (collection_name) {
					if (collections) {
						id = uniqueid();
						if (collections[collection_name]) {
							collection_name += id;
						}
						collections[collection_name] = {};
						collections[collection_name]['basket'] = lightbox_basket;
						collections[collection_name]['id'] = id;
					} else {
						collections = {};
						id = uniqueid();
						collections[collection_name] = {};
						collections[collection_name]['basket'] = lightbox_basket;
						collections[collection_name]['id'] = id;
					}
					localStorage.setItem("collections", JSON.stringify(collections));
					window_save_collection.fadeOut().remove();
				}
				event.stopPropagation();
			});

			$('#close_window_collections').click(function(event) {
				window_save_collection.fadeOut().remove();
				event.stopPropagation();
			});
		});

		var length_basket = length_basket_elements(basket);

		if (length_basket == 1) {
			element_basket.html("Lightbox (" + length_basket + " image)");
		} else {
			element_basket.html("Lightbox (" + length_basket + " images)");
		}

		global_length_basket = length_basket;
	}


	// Initial call

	var basket;
	if (getParameter('collection').length) {
		var collection = JSON.parse(localStorage.getItem('collections'));
		basket = collection[getParameter('collection')[0]]['basket'];
	} else {
		basket = JSON.parse(localStorage.getItem('lightbox_basket'));
	}

	var length_basket = length_basket_elements(basket);
	if (length_basket) {

		main(basket); // launch main()

		var interval = setInterval(function() {

			if (getParameter('collection').length) {
				var collection = JSON.parse(localStorage.getItem('collections'));
				basket = collection[getParameter('collection')[0]]['basket'];
				clearInterval(interval);
			} else {
				basket = JSON.parse(localStorage.getItem('lightbox_basket'));
			}
			var length_basket = length_basket_elements(basket);

			// if the length of the last called object is different from the newest
			if (global_length_basket != length_basket) {
				main(basket); // recall main
			}

		}, 8000); // Repeat main every 5 seconds

	} else {

		var s = '<div class="container alert alert-warning" style="margin-top:5%">The Basket is empty</div>';
		container_basket.html(s);

		var loading_div = $(".loading-div");
		if (loading_div.length) {
			loading_div.fadeOut().remove();
		}
	}
});