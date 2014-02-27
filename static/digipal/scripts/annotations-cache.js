var cache = cache || {};

cache.allographs = {};
cache.graphs = {};

cache.search = function(type, id) {
	var obj;

	if (type == 'allograph') {
		obj = cache.allographs;
	} else {
		obj = cache.graphs;
	}

	if (obj[id]) {
		return true;
	}

	return false;
};

cache.update = function(type, id, object) {
	var obj;

	if (type == 'allograph') {
		obj = cache.allographs;
		obj[id] = object['allographs'];

	} else {
		obj = cache.graphs;
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