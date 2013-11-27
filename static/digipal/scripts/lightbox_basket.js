$(document).ready(function() {
	(function() {

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

		var s = '';
		var basket = basket_elements;
		var graphs = [],
			images = [],
			data = {};

		if (length_basket_elements()) {
			if (basket.annotations && basket.annotations.length) {
				s += "<h3>Annotations</h3>";
				for (var i = 0; i < basket.annotations.length; i++) {
					graphs.push(basket.annotations[i].graph);
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
					console.log(data)
					s += "<table class='table table-condensed'>";
					s += '<th>Image</th><th>Allograph</td><th>Hand</th><th>Scribe</th><th>Place</th><th>Date</th><th>Remove</th>';

					for (i = 0; i < data['annotations'].length; i++) {
						var annotation = data['annotations'][i];
						s += "<tr data-graph = '" + annotation[1] + "'><td data-graph = '" + annotation[1] + "'><a href='/digipal/page/" + annotation[8] + "/?vector_id=" + annotation[7] + "'>" + annotation[0] + "</a>";
						s += "</td>";
						s += "<td>" + annotation[11] + "</td>";
						s += "<td><a href='/digipal/hands/" + annotation[9] + "'>" + annotation[3] + "</a></td>";
						if (annotation[4] != 'null') {
							s += "<td><a href='/digipal/scribes/" + annotation[10] + "'>" + annotation[4] + "</a></td>";
						} else {
							s += "<td>None</td>";
						}
						s += "<td>" + annotation[5] + "</td>";
						s += "<td>" + annotation[6] + "</td>";
						s += "<td><button data-graph = '" + annotation[1] + "' class='remove_graph btn btn-mini btn-danger'>Remove</button></td></tr>";

					}
					s += "</table>";

					if (basket.images && basket.images.length) {
						s += "<h3>Images</h3>";
					}

					s += "<table class='table table-condensed'>";
					s += '<th>Image</th><th>Label</td><th>Hand</th><th>Remove</th>';
					for (i = 0; i < data['images'].length; i++) {
						var image = data['images'][i];
						s += "<tr data-graph = '" + image[1] + "'><td data-graph = '" + image[1] + "'><a href='/digipal/page/" + image[1] + "'>" + image[0] + "</a></td>";
						s += "<td>" + image[2] + "</td>";
						s += "<td>" + image[3] + "</td>";
						s += "<td><button data-graph = '" + image[1] + "' class='remove_graph btn btn-mini btn-danger'>Remove</button></td></tr>";
					}
					$(s).find('img').on('load', function() {
						$('#container_basket').html(s);

						$('.remove_graph').click(function() {
							var graph = $(this).data('graph');
							for (i = 0; i < basket_elements.annotations.length; i++) {
								var element = basket_elements.annotations[i];
								if (graph == element.graph) {
									basket_elements.annotations.splice(i, 1);
									break;
								}
							}
							$('tr[data-graph="' + graph + '"]').fadeOut().remove();
							$('#lightbox_button a').html('Lightbox (' + basket_elements.annotations.length + ' images)');
							if (!basket_elements.annotations.length) {
								s = '<div class="container alert alert-warning">The Basket is empty</a>';
								$('#container_basket').html(s);
							}
							localStorage.setItem('lightbox_basket', JSON.stringify(basket_elements));
						});
					});

				}

			});



			$('#to_lightbox').click(function() {
				var graphs = [];
				for (i = 0; i < basket_elements.annotations.length; i++) {
					var element = basket_elements.annotations[i].graph;
					graphs.push(element);
				}
				location.href = '/lightbox/?annotations=[' + graphs.toString() + ']';
			});



		} else {
			s += '<div class="container alert alert-warning">The Basket is empty</a>';
			$('#container_basket').html(s);
		}

	})();
});