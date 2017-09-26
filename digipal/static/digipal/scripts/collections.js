/**
 * Digipal Basket
   -- Digipal Project --> digipal.eu
 */

function Collections() {

	var element_basket = $('#collection_link');
	var container_basket = $('#container_collections');
	var selectedCollections = [];
	var self = this;
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
			methods.share(selectedCollections);
			event.stopPropagation();
			event.preventDefault();
		});
		if (!window.digipal_settings.ARCHETYPE_GOOGLE_SHORTENER_CLIENTID) {
		    share_collection.hide();
		}

		var delete_collection = $('#delete_collection');
		delete_collection.on('click', function() {
			methods.delete_collections(selectedCollections, methods.delete, false);
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
			$(this).next('.tooltip').remove();
			event.stopPropagation();
			event.stopImmediatePropagation();
		});

		collections.find('img').on('click', function(event) {
			localStorage.setItem('selectedCollection', $(this).closest('.collection').attr('id'));
			location.href = window.location.href + encodeURIComponent($(this).closest('.collection').find('span').data('href'));
			event.stopPropagation();
		});

		var check_collections = $('#check_collections');
		check_collections.on('change', function() {
			methods.check_collections($(this));
		}).prop('checked', false);

		var copy_collection = $('#copy_collection');
		copy_collection.on('click', function() {
			methods.copy_collection();
		});

	};


	var show_collections = function(collections) {
		var container = $('#container_collections');
		var _self = this;
		var d = 0;
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
				if (this['editorial']) {
					n += this['editorial'].length;
				}
				collection.attr('class', 'collection');
				collection.attr('id', value.id);
				collection.data('id', value.id);
				collection.addClass('col-md-2 col-xs-5 col-sm-3');
				collection.append('<span data-href="' + index.replace(/\s+/gi, '') + '"><img src="/static/img/folder.png" /></span>');
				collection.append('<label for= "' + index + '">' + index + ' (' + n + ')<label>');
				collection.append('<input data-toggle="tooltip" data-placement="top" title="Check to select collection" type="checkbox" id="' + index + '" />');
				if (!$('#' + value.id).length) {
					if (d % 4 === 0) {
						container.append('<br clear="all"/>');
					}

					container.append(collection);
				}
				$('[data-toggle="tooltip"]').tooltip();
				d++;
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

	var update_toolbar = function() {

		this.collections = JSON.parse(localStorage.getItem('collections'));
		var collections = $.extend({}, this.collections);

		var n = 0;
		$.each(collections, function() {
			n++;
		});

		if (!selectedCollections.length) {
			$('#delete_collection').add('#copy_collection').add('#to_lightbox').add('#share_collection').attr('disabled', true);
			$('#check_collections').prop('indeterminate', false).prop('checked', false);
		} else if (selectedCollections.length == 1) {
			$('#delete_collection').add('#copy_collection').add('#to_lightbox').add('#share_collection').attr('disabled', false);
			if (n !== 1) {
				$('#check_collections').prop('indeterminate', true);
			} else {
				$('#check_collections').prop('indeterminate', false).prop('checked', true);
			}
		} else if (selectedCollections.length > 1) {
			$('#copy_collection').add('#to_lightbox').add('#share_collection').attr('disabled', true);
			$('#delete_collection').attr('disabled', false);
			if (selectedCollections.length != n) {
				$('#check_collections').prop('indeterminate', true);
			} else {
				$('#check_collections').prop('indeterminate', false).prop('checked', true);
			}
		}

		$('#counter-collections').html(selectedCollections.length);

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

		delete_collections: delete_collections,

		delete: function() {
			var collections = JSON.parse(localStorage.getItem('collections'));

			for (var i = 0; i < selectedCollections.length; i++) {
				$.each(collections, function(index, value) {
					if (value.id == selectedCollections[i]) {
						delete collections[index];
						$('#' + value.id).fadeOut().remove();
					}
				});
			}

			localStorage.setItem('collections', JSON.stringify(collections));
			localStorage.removeItem('selectedCollection');
			$('#delete-collection-div').parent().fadeOut().remove();

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
			var collection_name_trimmed = collection_name.replace(/\s+/gi, '');
			if ((collection_name_trimmed)) {
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
				window_save_collection.parent().fadeOut().remove();

				var container = $('#container_collections');
				var collection = $('<div>');
				collection.attr('class', 'collection');
				collection.attr('id', id);
				collection.data('id', id);
				collection.addClass('col-md-2 col-xs-5 col-sm-3');
				collection.append('<span data-id=' + id + ' data-href="' + collection_name.replace(/\s+/gi, '') + '"><img title="Send collection to Collection" src="/static/img/folder.png" /></span>');
				collection.append('<label for ="' + collection_name + '">' + collection_name + ' (0)<label>');
				collection.append('<input data-toggle="tooltip" data-placement="top" title="Check to select collection" type="checkbox" id="' + collection_name + '" />');
				container.append(collection);

				collection.find('input').on('change', function(event) {
					select_collection($(this).parent());
					event.stopPropagation();
					event.stopImmediatePropagation();
				});

				collection.find('img').on('click', function(event) {
					localStorage.setItem('selectedCollection', $(this).closest('.collection').attr('id'));
					location.href = window.location.href + encodeURIComponent($(this).closest('.collection').find('span').data('href'));
					event.stopPropagation();
				});

				notify('<span style="color: #468847;">New Collection successfully created</span>', "success");
				$('.alert').remove();
			} else {
				notify('Please enter a name for this collection', "danger");
			}

			return false;
		},

		to_lightbox: function() {
			var graphs = [],
				images = [],
				editorial = [],
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
			if (basket && basket.editorial && basket.editorial.length) {
				for (i = 0; i < basket.editorial.length; i++) {
					element = basket.editorial[i].toString();
					editorial.push(element);
				}
			}
			location.href = '/lightbox/?annotations=[' + graphs.toString() + ']&images=[' + images.toString() + ']&editorial=[' + editorial.toString() + ']&from=' + location.pathname;
		},

		share: share,

		check_collections: function(checkbox) {
			var is_checked = checkbox.is(':checked');
			if (is_checked) {
				$('.collection').not('.selected-collection').find('input').trigger('change').prop('checked', true);
			} else {
				$('.selected-collection').find('input').trigger('change').prop('checked', false);
			}
			checkbox.prop('indeterminate', false);
		},

		copy: function(selectedCollection, new_collection_name) {
			var id = uniqueid();
			var flag = false;
			var collections = JSON.parse(localStorage.getItem('collections'));

			$.each(collections, function(index, value) {
				var collection_name_trimmed = new_collection_name.replace(/\s+/gi, '');
				if ($.trim(new_collection_name) == $.trim(index)) {
					var new_re = /^[\w]*([0-9])$/;
					if (!new_re.test(new_collection_name)) {
						new_collection_name += '0';
					}
					while (collections[new_collection_name]) {
						new_collection_name = increment_last(new_collection_name);
					}
				}
				flag = true;
			});


			$.each(collections, function(index, value) {
				if (value.id == selectedCollection && flag) {
					var object_clone = $.extend({}, value);
					collections[new_collection_name] = object_clone;
					collections[new_collection_name].id = id;
					notify('Collection successfully copied', 'success');
				}
			});

			if (!flag) {
				notify("Please provide a valid name", 'danger');
				return false;
			}

			localStorage.setItem('collections', JSON.stringify(collections));
			show_collections(collections);

			var collection = $('#' + id);
			collection.find('input').on('change', function(event) {
				select_collection($(this).parent());
				event.stopPropagation();
				event.stopImmediatePropagation();
			});

			collection.find('img').on('click', function(event) {
				localStorage.setItem('selectedCollection', $(this).closest('.collection').attr('id'));
				location.href = window.location.href + encodeURIComponent($(this).closest('.collection').find('span').data('href'));
				event.stopPropagation();
			});
		},

		copy_collection: function() {
			var current_collection = selectedCollections[0];
			var window_save_collection = $('<div>');
			var background_div = $('<div class="dialog-background">');
			var lightbox_basket = JSON.parse(localStorage.getItem('lightbox_basket'));
			var s = '';
			window_save_collection.attr('class', 'loading-div').attr('id', 'new-collection-div');
			s += '<h3>Copy Collection</h3>';
			s += '<div style="margin-top:2em"><input required placeholder="Enter a name to copy collection" type="text" id= "name_collection" class="form-control" />';
			s += '<div style="margin-top:2em"><input type = "button" class="btn btn-sm btn-success" id="copy_collection_button" type="button" value="Copy" /> ';
			s += '<input type = "button" class="btn btn-sm btn-danger" id="close_window_collections" value="Cancel" /></div></div>';

			window_save_collection.html(s);

			if (!$('#new-collection-div').length) {
				background_div.html(window_save_collection);
				$('body').append(background_div);
			}

			$('#copy_collection_button').unbind().click(function(event) {
				methods.copy(current_collection, $('#name_collection').val());
				background_div.fadeOut().remove();
				event.stopPropagation();
				event.preventDefault();
			});

			$(document).on('keydown', function(event) {
				var code = (event.keyCode ? event.keyCode : event.which);
				if ($('#name_collection').is(':focus') && code == 13) {
					methods.copy(current_collection, $('#name_collection').val());
					background_div.fadeOut().remove();
				}
			});

			$('#name_collection').focus();

			$('#close_window_collections').unbind().click(function(event) {
				background_div.fadeOut().remove();
				event.stopPropagation();
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

	var deselect_all = function() {
		selectedCollections = [];
		$('.selected-collection').removeClass('selected-collection').find('input').prop('checked', false);
		update_toolbar();
	};

	var filter = function(pattern) {
		var re = new RegExp('^' + $.trim(pattern), "mi");
		var element, test;
		$.each(this.collections, function(index, value) {
			element = $('#' + value.id);
			test = re.test($.trim(index));
			if (!test && pattern) {
				element.fadeOut();
			} else {
				element.fadeIn();
			}
		});

		deselect_all();
	};

	return {
		'init': init
	};
}

$(document).ready(function() {
	var collections = new Collections();
	collections.init();

	$(window).bind('storage', function(e) {
		$("#container_collections").html("");
		collections.init();
	});
});

