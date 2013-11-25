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
		if (basket) {

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
					console.log(data)
					s += "<table class='table'>";
					s += '<th>Image</th><th>Allograph</td><th>Hand</th><th>Scribe</th><th>Place</th><th>Date</th><th>Remove</th>';
					s += "<tr><td class='image_label' data-graph = '" + data[0].annotations[1] + "'>" + data[0].annotations[0];
					s += "</td>";
					s += "<td>" + data[0].allograph + "<td>";
					s += "<td>" + data[0].annotations[3] + "<td>";
					s += "<td>" + data[0].annotations[4] + "<td>";
					s += "<td>" + data[0].annotations[5] + "<td>";
					s += "<td>" + data[0].annotations[6] + "<td>";
					s += "<td><button style='margin-left:5%;' data-graph = '" + data[0].annotations[1] + "' class='remove_graph btn btn-mini btn-danger'>Remove</button></td></tr>";
					for (i = 1; i < data.length; i++) {

						s += "<div class='image_label' data-graph = '" + data[i].annotations[1] + "'>" + data[i].annotations[0];
						s += "<tr><td class='image_label' data-graph = '" + data[0].annotations[1] + "'>" + data[i].annotations[0];
						s += "</td>";
						s += "<td>" + data[i].allograph + "<td>";
						s += "<td>" + data[i].annotations[3] + "<td>";
						s += "<td>" + data[i].annotations[4] + "<td>";
						s += "<td>" + data[i].annotations[5] + "<td>";
						s += "<td>" + data[i].annotations[6] + "<td>";
						s += "<td><button style='margin-left:5%;' data-graph = '" + data[i].annotations[1] + "' class='remove_graph btn btn-mini btn-danger'>Remove</button></td></tr>";

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
							$('*[data-graph="' + graph + '"]').fadeOut().remove();
							$('#lightbox_button a').html('Lightbox (' + basket_elements.annotations.length + ' images)');
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
			s += '<div class="alert alert-warning">The Basket is empty</a>';
			$('#container_basket').html(s);
		}

	})();
});