/**
 * Digipal Basket
   -- Digipal Project --> digipal.eu
 */


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

function Collections() {

	var element_basket = $('#collection_link');
	var container_basket = $('#container_collections');
	var selectedCollections = [];

	var init = function() {

		var collections = get_collections();
		show_collections(collections);

		events();

		var loading_div = $(".loading-div");
		if (loading_div.length) {
			loading_div.fadeOut().remove();
		}
		/*if (collections) {
			main(basket, function() {
				events();
			});
		} else {
			var empty_collection_string = '<div class="container alert alert-warning" style="margin-top:5%">The Collection is empty</div>';
			container_basket.html(empty_collection_string);

			var loading_div = $(".loading-div");
			if (loading_div.length) {
				loading_div.fadeOut().remove();
			}

			events();
		}
		*/
	};

	var events = function() {

		var to_lightbox = $('#to_lightbox');
		to_lightbox.on('click', function() {
			methods.to_lightbox();
		});

		var new_collection = $('#new_collection');
		new_collection.on('click', function(event) {
			methods.create_collection();
		});

		var share_collection = $('#share_collection');
		share_collection.on('click', function(event) {
			methods.share();
			event.stopPropagation();
			event.preventDefault();
		});

		var delete_collection = $('#delete_collection');
		delete_collection.on('click', function() {
			methods.delete_collections();
		});

		var filter_input = $('#filter');
		filter_input.on('keydown', function() {
			filter($(this).val());
		}).on('keyup', function() {
			filter($(this).val());
		}).on('change', function() {
			filter($(this).val());
		});


		var collections = $('.collection');
		collections.click(function() {
			select_collection($(this));
		}).dblclick(function() {
			localStorage.setItem('selectedCollection', $(this).attr('id'));
			location.href = window.location.href + $(this).find('span').data('href');
		});

	};


	var show_collections = function(collections) {
		var container = $('#container_collections');
		var _self = this;
		if (collections) {
			$.each(collections, function(index, value) {
				var collection = $('<div>');
				collection.attr('class', 'collection');
				collection.attr('id', value.id);
				collection.data('id', value.id);
				collection.addClass('col-md-2');
				collection.append('<span data-href="' + index.replace(' ', '') + '"><img title="Click to select; Double click to open" src="/static/img/folder.png" /></span>');
				collection.append('<label>' + index + '<label>');
				container.append(collection);
			});
		} else {
			var s = '<div class="container alert alert-warning">No collections saved</div>';
			container.append(s);
		}
		$('.remove_collection').click(function(event) {
			_self.delete($(this));
			event.stopPropagation();
		});
	};


	var get_collections = function() {
		var self = this;
		var collections = JSON.parse(localStorage.getItem('collections'));
		this.collections = collections;
		if (!$.isEmptyObject(collections)) {
			return collections;
		} else {
			return false;
		}
	};

	var methods = {

		create_collection: function() {
			var collections = JSON.parse(localStorage.getItem('collections'));
			var window_save_collection = $('<div>');
			var lightbox_basket = JSON.parse(localStorage.getItem('lightbox_basket'));
			var s = '';
			window_save_collection.attr('class', 'loading-div').attr('id', 'new-collection-div');
			s += '<h3>Create New Collection</h3>';
			s += '<div style="margin-top:0.5em"><input required placeholder="Enter here collection name" type="text" id= "name_collection" class="form-control" />';
			s += '<div style="margin-top:2em"><input type = "button" class="btn btn-sm btn-success" id="save_collection" type="button" value="Create" /> ';
			s += '<input type = "button" class="btn btn-sm btn-danger" id="close_window_collections" value="Cancel" /></div></div>';

			window_save_collection.html(s);

			if (!$('#new-collection-div').length) {
				$('body').append(window_save_collection);
			}

			$('#save_collection').unbind().click(function(event) {
				methods.save(collections, lightbox_basket);
				event.stopPropagation();
				event.preventDefault();
			});

			$(document).on('keydown', function(event) {
				var code = (event.keyCode ? event.keyCode : event.which);
				if ($('#name_collection').is(':focus') && code == 13) {
					methods.save(collections, lightbox_basket);
				}
			});

			$('#close_window_collections').unbind().click(function(event) {
				window_save_collection.fadeOut().remove();
				event.stopPropagation();
			});
		},

		delete_collections: function() {
			var collections = JSON.parse(localStorage.getItem('collections'));
			var window_save_collection = $('<div>');
			var s = '';

			window_save_collection.attr('class', 'loading-div').attr('id', 'delete-collection-div');
			s += '<h3>Delete Collections?</h3>';
			if (selectedCollections.length == 1) {
				s += '<p>You are about to delete 1 collection</p>';
			} else {
				s += '<p>You are about to delete ' + selectedCollections.length + ' collections</p>';
			}

			s += '<div style="margin-top:2em"><input type = "button" class="btn btn-sm btn-danger" id="delete" type="button" value="Delete" /> ';
			s += '<input type = "button" class="btn btn-sm btn-danger" id="close_window_collections" value="Cancel" /></div></div>';

			window_save_collection.html(s);

			if (!$('#delete-collection-div').length) {
				$('body').append(window_save_collection);
			}

			$('#delete').unbind().click(function(event) {
				methods.delete(collections);
				event.stopPropagation();
				event.preventDefault();
			});

			$('#close_window_collections').unbind().click(function(event) {
				window_save_collection.fadeOut().remove();
				event.stopPropagation();
			});


		},

		delete: function(collections) {

			for (var i = 0; i < selectedCollections.length; i++) {
				$.each(collections, function(index, value) {
					if (value.id == selectedCollections[i]) {
						delete collections[index];
						$('#' + value.id).remove();
					}
				});
			}

			localStorage.setItem('collections', JSON.stringify(collections));
			$('#delete-collection-div').fadeOut().remove();
		},

		save: function(collections, lightbox_basket) {
			var collection_name = $('#name_collection').val();
			var window_save_collection = $('#new-collection-div');
			var id = uniqueid();
			if (collection_name) {
				if (collections) {
					collections[collection_name] = {};
					collections[collection_name]['id'] = id;
				} else {
					collections = {};
					collections[collection_name] = {};
					collections[collection_name]['id'] = id;
				}

				localStorage.setItem("collections", JSON.stringify(collections));
				window_save_collection.fadeOut().remove();

				var container = $('#container_collections');
				var collection = $('<div>');
				collection.attr('class', 'collection');
				collection.attr('id', id);
				collection.addClass('col-md-2');
				collection.append('<span data-id=' + id + ' data-href="?collection=' + collection_name + '"><img title="Send collection to Collection" src="/static/img/folder.png" /></span>');
				collection.append('<label>' + collection_name + '<label>');
				container.append(collection);
				collection.click(function() {
					select_collection($(this));
				}).dblclick(function() {
					localStorage.setItem('selectedCollection', $(this).attr('id'));
					location.href = window.location.href + $(this).find('span').data('href');
				});
				notify('<span style="color: #468847;">New Collection succesfully created</span>', "success");
			} else {
				notify('Please enter a name for this collection', "danger");
			}
			return false;
		},

		to_lightbox: function() {
			var graphs = [],
				images = [],
				element,
				basket;

			var selectedCollection = selectedCollections[0];
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
					graphs.push(element);
				}
			}
			if (basket && basket.images && basket.images.length) {
				for (i = 0; i < basket.images.length; i++) {
					element = basket.images[i];
					images.push(element);
				}
			}
			location.href = '/lightbox/?annotations=[' + graphs.toString() + ']&images=[' + images.toString() + ']';
		},

		share: function() {
			var b = {},
				i = 0;

			var selectedCollection = selectedCollections[0];
			var collections = JSON.parse(localStorage.getItem('collections'));
			var basket;

			$.each(collections, function(index, value) {
				if (value.id == selectedCollection) {
					basket = value;
				}
			});

			var url = window.location.hostname +
				document.location.pathname +
				'?collection=' + encodeURIComponent(JSON.stringify(basket));

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
		}

	};

	var select_collection = function(collection) {
		if (collection.hasClass('selected-collection')) {
			collection.removeClass('selected-collection');
			for (var i = 0; i < selectedCollections.length; i++) {
				if (selectedCollections[i] == collection.data('id')) {
					selectedCollections.splice(i, 1);
					i--;
				}
			}
		} else {
			selectedCollections.push(collection.data('id'));
			collection.addClass('selected-collection');
		}

		if (selectedCollections.length == 1) {
			$('#delete_collection').add('#copy_collection').add('#to_lightbox').add('#share_collection').attr('disabled', false);
		} else if (selectedCollections.length > 1) {
			$('#copy_collection').add('#to_lightbox').add('#share_collection').attr('disabled', true);
			$('#delete_collection').attr('disabled', false);
		} else {
			$('#delete_collection').add('#copy_collection').add('#to_lightbox').add('#share_collection').attr('disabled', true);
		}
	};

	var filter = function(pattern) {
		var re = new RegExp(pattern, "gi");
		$.each(this.collections, function(index, value) {
			var element = $('.collection[id="' + value.id + '"]');
			if (!index.match(re)) {
				element.fadeOut();
			} else {
				element.fadeIn();
			}
		});
	};

	return {
		'init': init
	};
}

$(document).ready(function() {
	var collections = new Collections();
	collections.init();
});