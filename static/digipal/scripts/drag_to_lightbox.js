/**
 * Every element that match the css selector '.imageDatabase a.droppable_image'
 * will become draggable to a basket. The element must have an data-id attribute
 * which contains the ID of the digipal image record to add to the basket.
 *
 * Requires a <div id="basket_collector"> that will serve as a drop target
 * which is made visible as soon as we start dragging an item.
 *
 * Dependency: add_to_lightbox.js
 */

/*

 add_to_lightbox(element, type, element.data('id'), false)

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
		elements.closest(defaults.parentName).on('mouseenter', function(event) {
			dialog.init($(this).find(defaults.className));
			event.stopPropagation();
		}).on('mouseleave', function(event) {
			dialog.hide();
			event.stopPropagation();
		});
	};

	var dialog = {

		init: function(image) {
			var _self = this;
			_self.element = _self.create(image);
			if (!image.find(_self.element).length) {
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
			data.type += 's';
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
			var element = this.element;
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
		var type, id;
		if (image.data('id')) {
			type = 'image';
			id = image.data('id');
		} else {
			type = 'annotation';
			id = image.data('graph');
		}
		return {
			'type': type,
			'id': id
		};
	};

	var addToCollection = function(image) {
		var data = getData(image);
		data.type += 's';
		add_to_lightbox(image, data.type, data.id, false);
	};

	var removeFromCollection = function(image, type) {
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
		if (collection.hasOwnProperty(type)) {
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

	return {
		'init': init
	};
};

$(document).ready(function() {
	var star = new Star();
	star.init();
});