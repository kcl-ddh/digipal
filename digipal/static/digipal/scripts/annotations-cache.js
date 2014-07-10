function AnnotationsCache() {

	this.cache = {};
	this.cache.allographs = {};
	this.cache.graphs = {};

	this.init = function() {
		return this.cache;
	};

	this.search = function(type, id) {
		var obj;

		if (type == 'allograph') {
			obj = this.cache.allographs;
		} else {
			obj = this.cache.graphs;
		}

		if (obj.hasOwnProperty(id)) {
			return true;
		}

		return false;
	};

	this.update = function(type, id, object) {
		var obj;

		if (type == 'allograph') {
			obj = this.cache.allographs;
			obj[id] = object['allographs'];

		} else {
			obj = this.cache.graphs;
			obj[id] = {};
			obj[id]['features'] = object['features'];
			obj[id]['allograph_id'] = object['allograph_id'];
			obj[id]['hand_id'] = object['hand_id'];
			obj[id]['image_id'] = object['image_id'];
			obj[id]['hands'] = object['hands'];
			obj[id]['item_part'] = object['item_part'];
			obj[id]['aspects'] = object['aspects'];
			if (object.hasOwnProperty('internal_note')) {
				obj[id]['internal_note'] = object['internal_note'];
			}
			if (object.hasOwnProperty('display_note')) {
				obj[id]['display_note'] = object['display_note'];
			}
		}

		return obj;

	};

	this.clear = function() {
		this.cache.allographs = {};
		this.cache.graphs = {};
	};
}