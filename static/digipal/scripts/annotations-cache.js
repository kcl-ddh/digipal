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

		if (obj[id]) {
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
			obj[id]['vector_id'] = object['vector_id'];
			obj[id]['image_id'] = object['image_id'];
			obj[id]['hands'] = object['hands'];
		}

		return obj;

	};

	this.clear = function() {
		this.cache.allographs = {};
		this.cache.graphs = {};
	};
}