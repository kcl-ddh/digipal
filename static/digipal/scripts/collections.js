/**
 * Digipal Basket
   -- Digipal Project --> digipal.eu
 */

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
		filter_input.on('keyup', function() {
			filter($(this).val());
		}).on('change', function() {
			filter($(this).val());
		});


		var collections = $('.collection');
		collections.find('input').on('change', function(event) {
			select_collection($(this).parent());
			event.stopPropagation();
			event.stopImmediatePropagation();
		});

		collections.find('img').on('click', function(event) {
			localStorage.setItem('selectedCollection', $(this).closest('.collection').attr('id'));
			location.href = window.location.href + $(this).closest('.collection').find('span').data('href');
			event.stopPropagation();
		});

	};


	var show_collections = function(collections) {
		var container = $('#container_collections');
		var _self = this;
		if (collections) {
			$.each(collections, function(index, value) {
				var collection = $('<div>');
				var n = 0;
				if (this['images']) {
					n += this['images'].length;
				}
				if (this['annotations']) {
					n += this['annotations'].length;
				}
				collection.attr('class', 'collection');
				collection.attr('id', value.id);
				collection.data('id', value.id);
				collection.addClass('col-md-1');
				collection.append('<span data-href="' + index.replace(' ', '') + '"><img src="/static/img/folder.png" /></span>');
				collection.append('<label for= "' + index + '" data-placement="bottom" data-toggle="tooltip" title="' + index + ' has ' + n + ' items">' + index + ' (' + n + ')<label>');
				collection.append('<input data-toggle="tooltip" data-placement="top" title="Check to select collection" type="checkbox" id="' + index + '" />');
				container.append(collection);
				$('[data-toggle="tooltip"]').tooltip();
			});
		} else {
			var s = '<div class="container alert alert-warning">No collections</div>';
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
			var background_div = $('<div class="dialog-background">');
			var lightbox_basket = JSON.parse(localStorage.getItem('lightbox_basket'));
			var s = '';
			window_save_collection.attr('class', 'loading-div').attr('id', 'new-collection-div');
			s += '<h3>Create New Collection</h3>';
			s += '<div style="margin-top:2em"><input required placeholder="Enter here collection name" type="text" id= "name_collection" class="form-control" />';
			s += '<div style="margin-top:2em"><input type = "button" class="btn btn-sm btn-success" id="save_collection" type="button" value="Create" /> ';
			s += '<input type = "button" class="btn btn-sm btn-danger" id="close_window_collections" value="Cancel" /></div></div>';

			window_save_collection.html(s);

			if (!$('#new-collection-div').length) {
				background_div.html(window_save_collection);
				$('body').append(background_div);
			}

			$('#save_collection').unbind().click(function(event) {
				methods.save(collections, lightbox_basket);
				event.stopPropagation();
				event.preventDefault();
			});

			$('#name_collection').focus();

			$(document).on('keydown', function(event) {
				var code = (event.keyCode ? event.keyCode : event.which);
				if ($('#name_collection').is(':focus') && code == 13) {
					methods.save(collections, lightbox_basket);
				}
			});

			$('#close_window_collections').unbind().click(function(event) {
				background_div.fadeOut().remove();
				event.stopPropagation();
			});
		},

		delete_collections: function() {
			var collections = JSON.parse(localStorage.getItem('collections'));
			var background_div = $('<div class="dialog-background">');
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
				background_div.html(window_save_collection);
				$('body').append(background_div);
			}

			$('#delete').unbind().click(function(event) {
				methods.delete(collections);
				event.stopPropagation();
				event.preventDefault();
			});

			$('#close_window_collections').unbind().click(function(event) {
				background_div.fadeOut().remove();
				event.stopPropagation();
			});


		},

		delete: function(collections) {

			for (var i = 0; i < selectedCollections.length; i++) {
				$.each(collections, function(index, value) {
					if (value.id == selectedCollections[i]) {
						delete collections[index];
						$('#' + value.id).fadeOut().remove();
					}
				});
			}
			localStorage.setItem('collections', JSON.stringify(collections));
			$('#delete-collection-div').fadeOut().remove();

			if ($.isEmptyObject(collections)) {
				var s = '<div class="container alert alert-warning">No collections</div>';
				container_basket.append(s);
			}

			selectedCollections = [];
			update_toolbar();
		},

		save: function(collections, lightbox_basket) {
			var collection_name = $('#name_collection').val();
			var window_save_collection = $('#new-collection-div');
			var id = uniqueid();
			var re = /^\w*$/;
			var collection_name_trimmed = collection_name.replace(' ', '');
			if (collection_name && re.test(collection_name_trimmed)) {
				if (collections) {
					if (collections[collection_name]) {
						var new_re = /^[\w]*([0-9])$/;
						if (!new_re.test(collection_name)) {
							collection_name += '0';
						}
						while (collections[collection_name]) {
							collection_name = increment_last(collection_name);
						}

					}
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
				collection.addClass('col-md-1');
				collection.append('<span data-id=' + id + ' data-href="' + collection_name.replace(' ', '') + '"><img title="Send collection to Collection" src="/static/img/folder.png" /></span>');
				collection.append('<label>' + collection_name + ' (0)<label>');
				container.append(collection);
				collection.click(function() {
					select_collection($(this));
				}).dblclick(function() {
					localStorage.setItem('selectedCollection', $(this).attr('id'));
					location.href = window.location.href + $(this).find('span').data('href');
				});
				notify('<span style="color: #468847;">New Collection succesfully created</span>', "success");
				$('.alert').remove();
			} else {
				notify('Please enter a name for this collection (Do not use special characters)', "danger");
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
					basket = this;
					basket['name'] = index;
				}
			});
			var url = window.location.hostname + '/digipal/collection/shared/1/' +
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
			selectedCollections.push(collection.attr('id'));
			collection.addClass('selected-collection');
		}

		update_toolbar();
	};

	var filter = function(pattern) {
		var re = new RegExp('^' + $.trim(pattern), "gi");
		var element;
		$.each(this.collections, function(index, value) {
			element = $('.collection[id="' + value.id + '"]');
			if (!re.test($.trim(index)) && $.trim(pattern) !== '') {
				console.log(index, pattern, element);
				element.fadeOut();
			} else {
				element.fadeIn();
			}
		});
	};

	var update_toolbar = function() {
		if (selectedCollections.length == 1) {
			$('#delete_collection').add('#copy_collection').add('#to_lightbox').add('#share_collection').attr('disabled', false);
		} else if (selectedCollections.length > 1) {
			$('#copy_collection').add('#to_lightbox').add('#share_collection').attr('disabled', true);
			$('#delete_collection').attr('disabled', false);
		} else {
			$('#delete_collection').add('#copy_collection').add('#to_lightbox').add('#share_collection').attr('disabled', true);
		}
	};

	return {
		'init': init
	};
}

$(document).ready(function() {
	var collections = new Collections();
	collections.init();
});