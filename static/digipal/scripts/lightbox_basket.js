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
		var graphs = [];
		if (basket.annotations.length) {

			for (var i = 0; i < basket.annotations.length; i++) {
				graphs.push(basket.annotations[i].graph);
			}

			$.ajax({
				type: 'POST',
				url: 'images/',
				data: {
					'graphs': JSON.stringify(graphs)
				},
				success: function(data) {
					s += "<table class='table table-condensed'>";
					s += '<th>Image</th><th>Allograph</td><th>Hand</th><th>Scribe</th><th>Place</th><th>Date</th><th>Remove</th>';
					s += "<tr data-graph = '" + data[0].annotations[1] + "'><td data-graph = '" + data[0].annotations[1] + "'><a href='/digipal/page/" + data[0].annotations[8] + "/?vector_id=" + data[0].annotations[7] + "'>" + data[0].annotations[0] + "</a>";
					s += "</td>";
					s += "<td>" + data[0].allograph + "</td>";
					s += "<td><a href='/digipal/hands/" + data[0].annotations[9] + "'>" + data[0].annotations[3] + "</a></td>";

					if (data[0].annotations[4] != 'null') {
						s += "<td><a href='/digipal/scribes/" + data[0].annotations[10] + "'>" + data[0].annotations[4] + "</a></td>";
					} else {
						s += "<td>None</td>";
					}

					s += "<td>" + data[0].annotations[5] + "</td>";
					s += "<td>" + data[0].annotations[6] + "</td>";
					s += "<td><button data-graph = '" + data[0].annotations[1] + "' class='remove_graph btn btn-mini btn-danger'>Remove</button></td></tr>";
					for (i = 1; i < data.length; i++) {

						s += "<tr data-graph = '" + data[i].annotations[1] + "'><td data-graph = '" + data[i].annotations[1] + "'><a href='/digipal/page/" + data[i].annotations[8] + "/?vector_id=" + data[i].annotations[7] + "'>" + data[i].annotations[0] + "</a>";
						s += "</td>";
						s += "<td>" + data[i].allograph + "</td>";
						s += "<td><a href='/digipal/hands/" + data[i].annotations[9] + "'>" + data[i].annotations[3] + "</a></td>";
						if (data[i].annotations[4] != 'null') {
							s += "<td><a href='/digipal/scribes/" + data[i].annotations[10] + "'>" + data[i].annotations[4] + "</a></td>";
						} else {
							s += "<td>None</td>";
						}
						s += "<td>" + data[i].annotations[5] + "</td>";
						s += "<td>" + data[i].annotations[6] + "</td>";
						s += "<td><button data-graph = '" + data[i].annotations[1] + "' class='remove_graph btn btn-mini btn-danger'>Remove</button></td></tr>";

					}
					s += "</table>";
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