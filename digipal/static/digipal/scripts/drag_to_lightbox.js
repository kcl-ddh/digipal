/**
 * Every element that match the css selector 'a.droppable_image'
 * will be detected by the script to be "starrable". The element must have an data-id attribute
 * which contains the ID of the digipal image record to add to the basket, or
 * data graph if this is an annotation
 *
 * Dependency: add_to_lightbox.js
 */
/*

 from add_to_lightbox.js:
 add_to_lightbox(element, type, id, multiple)

 */

var Star = function(options) {

	var self = this;

	var defaults = {
		className: '.droppable_image',
		parentName: '.folio-image-wrapper'
	};

	if (options && !$.isEmptyObject(options)) {
		defaults = $.extend(defaults, options);
	}

	var elements = $(defaults.className);

	var init = function() {
		events();
	};

	var events = function() {
		findStarredInPage();
		elements.closest(defaults.parentName).on('mouseenter', function(event) {
			dialog.init($(this).find(defaults.className));
		}).on('mouseleave', function(event) {
			dialog.hide();
		});

	};

	var dialog = {

		init: function(image) {
			var _self = this;
			if (!$("#dialog-star").length) {
				_self.element = _self.create(image);
				_self.show(image);
			}
		},

		create: function(image) {
			var element = $('<div id="dialog-star">');
			return this.fill(image, element);
		},

		fill: function(image, element) {
			var data = getData(image);
			var star = $('<span data-toggle="tooltip" data-container="body" title="Add image to collection" class="glyphicon glyphicon-star unstarred">');
			var selectedCollection = getCurrentCollection();
			if (isInCollection(selectedCollection, data.id, data.type)) {
				star.addClass('starred').removeClass("unstarred");
				star.attr('title', 'Image added to collection');
			}
			star.tooltip();
			element.append(star);
			return element;
		},

		show: function(image) {
			var element = this.element;
			image.append(element);
			this.events(element, image);
		},

		hide: function() {
			var element = $("#dialog-star");
			element.fadeOut().remove();
		},

		events: function(element, image) {
			element.on('click', function(event) {
				event.preventDefault();
				event.stopPropagation();
				event.stopImmediatePropagation();
			});

			element.find('span').on('click', function() {
				if ($(this).hasClass('starred')) {
					removeFromCollection(image);
				} else {
					addToCollection(image);
				}
			});
		}

	};

	var getData = function(image) {
		var id;
		if (image.data('type') == 'image') {
			id = image.data('id');
		} else {
			id = image.data('graph');
		}
		return {
			'type': image.data('type'),
			'id': id
		};
	};

	var addToCollection = function(image) {
		var data = getData(image);
		if (add_to_lightbox(image, data.type, data.id, false)) {
			dialog.element.find('span').addClass('starred').removeClass('unstarred');
			var _type;
			if (data.type == 'image') {
				_type = 'id';
			} else {
				_type = 'graph';
			}
			var element = $('[data-' + _type + '=' + data.id + ']');
			if (typeof element.data('add-star') !== 'undefined' && !element.data('add-star')) {
				return false;
			}
			var star = "<span class='glyphicon glyphicon-star starred-image'></span>";
			element.append(star);
		}
	};

	var removeFromCollection = function(image, type) {
		var _self = this;
		var collections = JSON.parse(localStorage.getItem('collections'));
		var collection_id = getCurrentCollection();
		var collection = getCollection(collection_id);
		var data = getData(image);
		data.type += 's';
		for (var i = 0; i < collection[data.type].length; i++) {
			if (collection[data.type][i] == data.id) {
				collection[data.type].splice(i, 1);
				i--;
				notify('Image removed from Collection', 'success');
				break;
			}
		}
		if (dialog.element) {
			dialog.element.find('span').addClass('unstarred').removeClass('starred');
		}
		var _type;
		if (data.type == 'images') {
			_type = 'id';
		} else {
			_type = 'graph';
		}

		$('[data-' + _type + '=' + data.id + ']').find('.starred-image').remove();
		collections[collection.name] = collection;
		localStorage.setItem('collections', JSON.stringify(collections));
		update_collection_counter();
	};

	var getElementsFromCollections = function() {
		var collections = JSON.parse(localStorage.getItem('collections'));
		var collection;
		var arrays = ['images', 'annotations'];
		var allElements = {};
		$.each(collections, function(index, value) {
			for (var i = 0; i < arrays.length; i++) {
				if (value.hasOwnProperty(values[i])) {
					for (var j = 0; j < value[arrays[i]].length; j++) {
						allElements[value[arrays[i]][j]] = value.id;
					}
				}
			}
		});
		return allElements;
	};

	var getCollection = function(collection_id) {
		var collections = JSON.parse(localStorage.getItem('collections'));
		var collection;
		$.each(collections, function(index, value) {
			if (value.id == collection_id) {
				collection = value;
				collection['name'] = index;
				return false;
			}
		});
		return collection;
	};

	var isInCollection = function(collection_id, id, type) {
		var collection = getCollection(collection_id);
		var found = false;
		type += 's';
		if (collection && collection.hasOwnProperty(type)) {
			for (var i = 0; i < collection[type].length; i++) {
				if (collection[type][i] == id) {
					found = true;
					break;
				}
			}
		}
		return found;
	};

	var getCurrentCollection = function() {
		return localStorage.getItem('selectedCollection');
	};

	var findStarredInPage = function() {
		var collection_id = getCurrentCollection();
		var graphs = $('[data-graph]').add($('[data-id]'));
		$.each(graphs, function() {
			var id;
			if ($(this).data('graph')) {
				id = $(this).data('graph');
				type = 'annotation';
			} else {
				id = $(this).data('id');
				type = 'image';
			}

			if (isInCollection(collection_id, id, type)) {
				if (typeof $(this).data('add-star') !== 'undefined' && !$(this).data('add-star')) {
					return false;
				}
				var star = "<span class='glyphicon glyphicon-star starred-image'></span>";
				$(this).append(star);
			}
		});
	};

	return {
		'init': init,
		"removeFromCollection": removeFromCollection,
		"getCurrentCollection": getCurrentCollection,
		"isInCollection": isInCollection
	};
};

$(document).ready(function() {
	var star = new Star();
	star.init();
});