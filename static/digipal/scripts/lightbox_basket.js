/**
 * Digipal Basket
   -- Digipal Project --> digipal.eu
 */

var csrftoken = getCookie('csrftoken');

$.ajaxSetup({
	headers: {
		"X-CSRFToken": csrftoken
	}
});

$(document).ready(function() {

	var element_basket = $('#collection_link');
	var container_basket = $('#container_basket');

	function main(basket) {

		var s = '';

		var graphs = [],
			images = [],
			data = {};

		if (basket.annotations && basket.annotations.length) {
			s += "<h3 id='header_annotations'>Annotations (" + basket.annotations.length + ")</h3>";
			for (var i = 0; i < basket.annotations.length; i++) {
				graphs.push(basket.annotations[i]);
			}
			data.annotations = graphs;
		}

		if (basket.images && basket.images.length) {
			for (d = 0; d < basket.images.length; d++) {
				if (typeof basket.images[d] != 'number') {
					images.push(basket.images[d].id);
				} else {
					images.push(basket.images[d]);
				}
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


						s += "<td><button title = 'Remove from basket' data-type='annotation' data-graph = '" + annotation[1] + "' class='remove_graph btn btn-xs btn-danger'>Remove</button></td></tr>";
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
							element_basket.html("Collection (" + length_basket + " <i class='fa fa-picture-o'> </i> )");
						} else {
							element_basket.html("Collection (" + length_basket + " <i class='fa fa-picture-o'> </i> )");
						}

						if (basket.annotations && !basket.annotations.length && basket.images && !basket.images.length) {
							s = '<div class="container alert alert-warning">The Collection is empty</div>';
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

				var s = '<div class="container alert alert-warning" style="margin-top:5%">Something has gone wrong. Please refresh the page and try again.</div>';
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

		function save_collection(collections, lightbox_basket) {
			var collection_name = $('#name_collection').val();
			var window_save_collection = $('.loading-div');
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

				var container = $('#container_collections');
				var collection = $('<div>');
				collection.attr('class', 'collection');
				collection.attr('id', id);
				collection.addClass('col-md-2');
				collection.append('<a href="?collection=' + collection_name + '"><img title="Send collection to Collection" src="/static/img/folder.png" /></a>');
				collection.append('<label>' + collection_name + '<label>');
				collection.append("<button id = '" + collection_name + "' data-collection =  '" + id + "' class='remove_collection btn btn-danger btn-xs'>Remove</button>");
				container.append(collection);

				notify('<span style="color: #468847;">Collection saved succesfully</span>', "success");
			} else {
				notify('Please enter a name for this collection', "danger");
			}
			event.stopPropagation();
		}

		$('#add_collection').click(function(event) {
			var collections = JSON.parse(localStorage.getItem('collections'));
			var window_save_collection = $('<div>');
			var lightbox_basket = JSON.parse(localStorage.getItem('lightbox_basket'));
			var s = '';
			window_save_collection.attr('class', 'loading-div');
			s += '<h3>Save Collection</h3>';
			s += '<div style="margin-top:0.5em"><input required placeholder="Enter here collection name" type="text" id= "name_collection" class="form-control" />';
			s += '<div style="margin-top:2em"><input type = "button" class="btn btn-sm btn-success" id="save_collection" type="button" value="Save" /> ';
			s += '<input type = "button" class="btn btn-sm btn-danger" id="close_window_collections" value="Close Window" /></div></div>';
			window_save_collection.html(s);
			$('body').append(window_save_collection);

			$('#save_collection').click(function(event) {
				save_collection(collections, lightbox_basket);
			});

			$(document).on('keydown', function(event) {
				var code = (event.keyCode ? event.keyCode : event.which);
				if ($('#name_collection').is(':focus') && code == 13) {
					save_collection(collections, lightbox_basket);
				}
			});

			$('#close_window_collections').click(function(event) {
				window_save_collection.fadeOut().remove();
				event.stopPropagation();
			});
		});

		$('#share_collection').click(function(event) {
			var b = {},
				i = 0;

			if (basket.annotations && basket.annotations.length) {
				var annotations = [];
				for (i = 0; i < basket.annotations.length; i++) {
					if (basket.annotations[i].graph) {
						annotations.push(basket.annotations[i].graph);
					}
				}
				b.annotations = annotations;
			}

			if (basket.images && basket.images.length) {
				var images = [];
				for (i = 0; i < basket.images.length; i++) {
					if (basket.images[i].id) {
						images.push(basket.images[i].id);
					}

				}
				b.images = images;
			}

			var url = window.location.hostname +
				document.location.pathname +
				'?basket=' + encodeURIComponent(JSON.stringify(b));

			var scriptTwitter = '<script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0];if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src="https://platform.twitter.com/widgets.js";fjs.parentNode.insertBefore(js,fjs);}}(document,"script","twitter-wjs");</script>';
			var div = $('#share_basket_div');
			if (!div.length) {
				div = $('<div class="loading-div" id="share_basket_div">');
				div.html('<h3>Share Collection URL</h3>');
				div.append('<p><a id="basket_url" ><img src="/static/digipal/images/ajax-loader.gif" /></a></p>');
				div.append('<p><button class="btn btn-danger btn-small">Close</button></p>');
				$('body').append(div);

				div.find('button').click(function() {
					div.fadeOut();
				});
			} else {
				div.fadeIn();
			}

			gapi.client.load('urlshortener', 'v1', function() {

				var request = gapi.client.urlshortener.url.insert({
					'resource': {
						'longUrl': url
					}
				});

				var resp = request.execute(function(resp) {
					if (resp.error) {
						console.log(resp);
						return false;
					} else {

						$("#basket_url").attr('href', resp.id).text(resp.id).addClass('basket_url');
						var linkTwitter = ' <a href="https://twitter.com/share" data-hashtags="digipal" class="twitter-hashtag-button" data-lang="en" data-count="none" data-size="large" data-related="digipal" data-text="' + resp.id + '">Tweet</a>';
						if (!$('.twitter-hashtag-button').length) {
							$('#basket_url').after(linkTwitter + scriptTwitter);
						} else {
							twttr.widgets.load();
						}
					}
				});
			});

			event.stopPropagation();
			event.preventDefault();
			return false;
		});

		var length_basket = length_basket_elements(basket);

		if (length_basket == 1) {
			element_basket.html("Collection (" + length_basket + " <i class='fa fa-picture-o'> </i> )");
		} else {
			element_basket.html("Collection (" + length_basket + " <i class='fa fa-picture-o'> </i> )");
		}

		global_length_basket = length_basket;
	}


	// Initial call

	var tabs = $('a[data-toggle="tab"]');
	tabs.on('shown.bs.tab', function(e) {
		if (e.target.getAttribute('data-target') == '#container_collections') {
			$('#to_lightbox').attr('disabled', true);
			$('#add_collection').attr('disabled', true);
			$('#share_collection').attr('disabled', true);
			$('#filter').attr('disabled', false);
		} else {
			$('#to_lightbox').attr('disabled', false);
			$('#add_collection').attr('disabled', false);
			$('#share_collection').attr('disabled', false);
			$('#filter').attr('disabled', true);
		}
	});

	var basket;
	if (getParameter('collection').length) {
		var collection = JSON.parse(localStorage.getItem('collections'));
		basket = collection[getParameter('collection')[0]]['basket'];
		var header = $('.header1');
		header.html('Collection, ' + getParameter('collection')[0]);
		header.append('<ul class="nav nav-pills pull-right"><li><a style="cursor:pointer;font-size:14px;" title="" id="default_basket">Set as default Collection</a></li></ul>');

		$('#default_basket').click(function() {
			localStorage.setItem('lightbox_basket', JSON.stringify(basket));
			notify(getParameter('collection')[0] + ' set as default basket', "success");
		});
	} else if (getParameter('basket').length) {
		basket = JSON.parse(decodeURIComponent(getParameter('basket')[0]));
	} else {
		basket = JSON.parse(localStorage.getItem('lightbox_basket'));
	}

	var length_basket = length_basket_elements(basket);
	if (length_basket) {

		main(basket); // launch main()

		/*var interval = setInterval(function() {

			if (getParameter('collection').length) {
				var collection = JSON.parse(localStorage.getItem('collections'));
				basket = collection[getParameter('collection')[0]]['basket'];
				clearInterval(intervalSee the last lines in the log produced by 'python );
			} else {
				basket = JSON.parse(localStorage.getItem('lightbox_basket'));
			}
			var length_basket = length_basket_elements(basket);

			// if the length of the last called object is different from the newest
			if (global_length_basket != length_basket) {
				main(basket); // recall main
			}

		}, 8000); // Repeat main every 5 seconds*/

	} else {

		var s = '<div class="container alert alert-warning" style="margin-top:5%">The Collection is empty</div>';
		container_basket.html(s);

		var loading_div = $(".loading-div");
		if (loading_div.length) {
			loading_div.fadeOut().remove();
		}
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

function notify(msg, status) {
	var status_element = $('#status');
	if (!status_element.length) {
		status_element = $('<div id="status">');
		$('body').append(status_element.hide());
	}
	status_class = status ? ' alert-' + status : '';
	status_element.attr('class', 'alert' + status_class);
	status_element.html(msg).fadeIn();

	setTimeout(function() {
		status_element.fadeOut();
	}, 5000);
}

function uniqueid() {
	var text = "";
	var possible = "0123456789";

	for (var i = 0; i < 3; i++)
		text += possible.charAt(Math.floor(Math.random() * possible.length));

	return text;
}