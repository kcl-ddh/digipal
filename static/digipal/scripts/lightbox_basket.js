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

	var csrftoken = getCookie('csrftoken');

	$.ajaxSetup({
		headers: {
			"X-CSRFToken": csrftoken
		}
	});



	function main() {
		var basket = JSON.parse(localStorage.getItem('lightbox_basket'));
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
					s += '<th>Annotation</th><th>Allograph</td><th>Hand</th><th>Scribe</th><th>Place</th><th>Date</th><th>Remove</th>';
					for (i = 0; i < data['annotations'].length; i++) {
						var annotation = data['annotations'][i];
						s += "<tr data-graph = '" + annotation[1] + "'><td data-graph = '" + annotation[1] + "'><a href='/digipal/page/" + annotation[8] + "/?vector_id=" + annotation[7] + "'>" + annotation[0] + "</a>";
						s += "</td>";
						s += "<td><a href='/digipal/search/graph/?character_select=" + annotation[13] + "&allograph_select=" + annotation[12] + "'>" + annotation[11] + "</a></td>";
						s += "<td><a href='/digipal/hands/" + annotation[9] + "'>" + annotation[3] + "</a></td>";
						if (annotation[4] !== null && annotation[4] != 'null') {
							s += "<td><a href='/digipal/scribes/" + annotation[10] + "'>" + annotation[4] + "</a></td>";
						} else {
							s += "<td>None</td>";
						}
						s += "<td><a href='/digipal/page/?town_or_city=" + annotation[5] + "'>" + annotation[5] + "</a></td>";
						s += "<td><a href='/digipal/page/?date=" + annotation[6] + "'>" + annotation[6] + "</a></td>";
						s += "<td><button data-type='annotation' data-graph = '" + annotation[1] + "' class='remove_graph btn btn-mini btn-danger'>Remove</button></td></tr>";
					}
				}

				s += "</table>";

				if (basket.images && basket.images.length) {
					s += "<h3 id ='header_images'>Images (" + basket.images.length + ")</h3>";
					s += "<table class='table table-condensed'>";
					s += '<th>Page</th><th>Label</td><th>Hand</th><th>Remove</th>';
					for (i = 0; i < data['images'].length; i++) {
						var image = data['images'][i];
						s += "<tr data-graph = '" + image[1] + "'><td data-graph = '" + image[1] + "'><a href='/digipal/page/" + image[1] + "'>" + image[0] + "</a></td>";
						s += "<td data-graph = '" + image[1] + "'><a href='/digipal/page/" + image[1] + "'>" + image[2] + "</a></td>";
						s += "<td>" + image[3] + "</td>";
						s += "<td><button data-type='image' data-graph = '" + image[1] + "' class='remove_graph btn btn-mini btn-danger'>Remove</button></td></tr>";
					}
				}

				$(s).find('img').on('load', function() {

					$('#container_basket').html(s);

					$('.remove_graph').click(function() {
						var basket = localStorage.getItem('lightbox_basket');
						var basket_elements = JSON.parse(basket);
						var graph = $(this).data('graph');
						var type = $(this).data('type');
						var element;
						if (type == 'annotation') {
							for (i = 0; i < basket_elements.annotations.length; i++) {
								element = basket_elements.annotations[i];
								if (graph == element.graph) {
									basket_elements.annotations.splice(i, 1);
									break;
								}
							}
							$('#header_annotations').html("Annotations (" + basket_elements.annotations.length + ")");
						} else {
							for (i = 0; i < basket_elements.images.length; i++) {
								element = basket_elements.images[i];
								if (graph == element.id) {
									basket_elements.images.splice(i, 1);
									break;
								}
							}
							$('#header_images').html("Images (" + basket_elements.images.length + ")");
						}

						$('tr[data-graph="' + graph + '"]').fadeOut().remove();

						$('#lightbox_button a').html('Lightbox (' + length_basket_elements(basket_elements) + ' images)');
						if (!basket_elements.annotations.length && !basket_elements.images.length) {
							s = '<div class="container alert alert-warning">The Basket is empty</a>';
							$('#container_basket').html(s);
						}
						localStorage.setItem('lightbox_basket', JSON.stringify(basket_elements));
					});
				});
			}
		});

		$('#to_lightbox').click(function() {
			var graphs = [],
				images = [],
				element;
			if (basket_elements && basket_elements.annotations && basket_elements.annotations.length) {
				for (i = 0; i < basket_elements.annotations.length; i++) {
					if (basket.annotations[i].hasOwnProperty('graph')) {
						element = basket.annotations[i].graph;
					} else {
						element = basket.annotations[i];
					}
					graphs.push(element);
				}
			}
			if (basket_elements && basket_elements.images && basket_elements.images.length) {
				for (i = 0; i < basket_elements.images.length; i++) {
					element = basket_elements.images[i].id;
					images.push(element);
				}
			}
			location.href = '/lightbox/?annotations=[' + graphs.toString() + ']&images=[' + images.toString() + ']';
		});
		$('#lightbox_button a').html('Lightbox (' + length_basket_elements(basket) + ' images)');
	}

	var basket = JSON.parse(localStorage.getItem('lightbox_basket'));
	if (length_basket_elements(basket)) {
		main();
		setInterval(main, 10000);
	} else {
		var s = '<div class="container alert alert-warning">The Basket is empty</a>';
		$('#container_basket').html(s);
	}
});