function Collections() {

	this.init = function() {
		var collections = this.get() || false;
		this.show(collections);
	};

	this.get = function() {
		var self = this;
		var collections = JSON.parse(localStorage.getItem('collections'));
		this.collections = collections;
		if (!$.isEmptyObject(collections)) {
			return collections;
		} else {
			return false;
		}

	};

	this.show = function(collections) {
		var container = $('#container_collections');
		var _self = this;
		if (collections) {
			$.each(collections, function(index, value) {
				var collection = $('<div>');
				collection.attr('class', 'collection');
				collection.attr('id', value.id);
				collection.addClass('col-md-2');
				collection.append('<a href="?collection=' + index + '"><img title="Send collection to basket" src="/static/img/folder.png" /></a>');
				collection.append('<label>' + index + '<label>');
				collection.append("<button id = '" + index + "' data-collection =  '" + value.id + "' class='remove_collection btn btn-danger btn-xs'>Remove</button>");
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

	this.delete = function(collection) {
		var collection_name = collection.data('collection');
		var collection_id = collection.attr('id');
		delete this.collections[collection_id];
		localStorage.setItem('collections', JSON.stringify(this.collections));
		$('#' + collection_name).fadeOut().remove();
		if ($.isEmptyObject(this.collections)) {
			var container = $('#container_collections');
			var s = '<div class="container alert alert-warning">No collections saved</div>';
			container.html(s);
			localStorage.removeItem('collections');
		}
	};

	this.filter = function(pattern) {
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

}

function main() {
	collections = new Collections();
	collections.init();

	var filter = $('#filter');
	filter.on('keydown', function() {
		collections.filter($(this).val());
	});

	filter.on('keyup', function() {
		collections.filter($(this).val());
	});

	filter.on('change', function() {
		collections.filter($(this).val());
	});
}

$(document).ready(function() {
	main();
});