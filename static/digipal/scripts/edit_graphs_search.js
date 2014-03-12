/**
 * Script to edit graphs in search pages
   -- Digipal Project --> digipal.eu
 */

/**
 * Every element that match the css selector '[data-graph]' will be attached to the function load_graph.
 * They also require two other attributes:
 *	- data-image-id -> the id of the image they are located in
 *	- data-allograph -> the id of the allograph assigned to them
 * Dependencies:
 *	- dialog.js
 *	- update_dialog.js
 *  - dialog-db-functions.js
 */



function EditGraphsSearch() {

	var self = this;
	self.annotations = {};
	self.selectedAnnotations = [];
	self.selectedAllograph = null;

	self.cache = new AnnotationsCache();

	var cache = self.cache.cache;
	// object dialog inherited from the object of the script dialog.js
	var dialog = new Dialog();

	// constants to be used troughout the script
	self.constants = {
		'ABSOLUTE_URL': '/digipal/api/',
		'PREFIX': 'search_'
	};


	// the init function launch the events function, ant it is the only method returned by the class
	var init = function() {
		events();
	};

	var events = function() {

		var switcher = $('#toggle-state-switch');
		switcher.bootstrapSwitch();

		/*

		matching all elementd which contain the attribute data-graph

		- they also require:
			- data-image_id: the id of the image they are located in
			- data-allograph: the id of the allograph assigned to them

		*/

		var graphs = $('[data-graph]');

		graphs.on('click', function(event) {

			if (switcher.bootstrapSwitch('state')) {
				load_graph($(this));

				// preventing link action
				event.preventDefault();
				event.stopPropagation();
				return false;
			}

		});

		/* applying select all event */
		var select_all = $('.select_all');
		if (select_all.length) {
			select_all.click(function(event) {
				methods.select_all($(this));
			});
		}

		/* applying deselect all event */
		var deselect_all = $('.deselect_all');
		if (deselect_all.length) {
			deselect_all.click(function(event) {
				methods.deselect_all($(this));
			});
		}

	};

	/* given an $(HTML) element, this function loads data about the graph, and initializes the dialog
		@element $(HTMLElement)
	*/
	var load_graph = function(element) {
		var graph = element.data('graph');
		var allograph = element.data('allograph');
		var elements = $("[data-graph='" + graph + "']");
		var image_id = element.data('image-id');
		var data, url, request, content_type = 'graph';
		if (!element.find('img').hasClass('graph_active')) {

			self.selectedAnnotations.push(graph);
			elements.find('img').addClass('graph_active');
			self.selectedAllograph = null;

			// if there's no allograph cached, I make a full AJAX call
			if (!self.cache.search("allograph", allograph)) {

				load_group(element.closest('[data-group="true"]'), self.cache, false, function(data) {
					var output = get_graph(graph, data, cache);
					refresh(output, image_id);
				});

				// else if allograph is cached, I only need the features, therefore I change the URL to omit allographs
			} else if (self.cache.search("allograph", allograph) && (!self.cache.search('graph', graph))) {

				load_group(element.closest('[data-group="true"]'), self.cache, true, function(data) {
					var output = get_graph(graph, data, cache);
					refresh(output, image_id);
				});


				// otherwise I have both cached, I can get them from the cache object
			} else {
				data = {};
				data['allographs'] = cache.allographs[allograph];
				data['features'] = cache.graphs[graph]['features'];
				data['allograph_id'] = cache.graphs[graph]['allograph_id'];
				data['hand_id'] = cache.graphs[graph]['hand_id'];
				data['hands'] = cache.graphs[graph]['hands'];
				refresh(data, image_id);
			}

			self.selectedAllograph = allograph;
		} else {
			removeSelected(elements, graph);
			$('.myModalLabel .badge').html(self.selectedAnnotations.length);

			/*	Hide dialog is there are no annotations selected	*/

			if (!self.selectedAnnotations.length) {
				self.dialog.hide();

				/*	Otherwise load the previous loaded annotation */
			} else {
				var checkboxes = $('.features_box');
				data = {};
				graph = self.selectedAnnotations[self.selectedAnnotations.length - 1];
				if (cache.graphs.hasOwnProperty(graph)) {
					allograph = cache.graphs[graph]['allograph_id'];
					data['allographs'] = cache.allographs[allograph];
					data['features'] = cache.graphs[graph]['features'];
					data['allograph_id'] = allograph;
					data['hand_id'] = cache.graphs[graph]['hand_id'];
					data['hands'] = cache.graphs[graph]['hands'];
					refresh(data, image_id);
					detect_common_features(self.selectedAnnotations, checkboxes, cache);
				} else {
					reload_cache(self.selectedAnnotations, self.cache, false, function() {
						allograph = cache.graphs[graph]['allograph_id'];
						data['allographs'] = cache.allographs[allograph];
						data['features'] = cache.graphs[graph]['features'];
						data['allograph_id'] = allograph;
						data['hand_id'] = cache.graphs[graph]['hand_id'];
						data['hands'] = cache.graphs[graph]['hands'];
						refresh(data, image_id);
						detect_common_features(self.selectedAnnotations, checkboxes, cache);
					});
				}
			}

			self.selectedAllograph = allograph;
		}
	};

	/* this function updates the dialog content
		@data {Object}
		@image_id {Integer}
	*/
	var refresh = function(data, image_id) {
		var allographs = data;
		console.log(data);

		if (self.selectedAnnotations.length > 1) {
			allographs['allographs'] = common_components(self.selectedAnnotations, cache, allographs['allographs']);
		}

		var selectedAnnotation = self.selectedAnnotations[self.selectedAnnotations.length - 1];
		var graph = cache.graphs[selectedAnnotation];
		console.log(graph)
		/* creating dialog */
		dialog(image_id, {
			summary: false
		}, function(dialog_instance) {
			self.dialog = dialog_instance;

			self.dialog.update(self.constants.PREFIX, allographs, self.selectedAnnotations, function(s) {

				/* fill container content */
				self.dialog.selector.find('#features_container').html(s);

				var checkboxes = $('.myModal .features_box');

				var select_hand = $('.myModal .hand_form');

				/* rewriting hands select */
				var string_hand_select = '<option value>------</option>';
				for (var h = 0; h < graph.hands.length; h++) {
					string_hand_select += '<option value="' + graph.hands[h].id + '">' +
						graph.hands[h].label + '</option>';
				}

				select_hand.html(string_hand_select);

				detect_common_features(self.selectedAnnotations, checkboxes, cache);
				common_allographs(self.selectedAnnotations, cache, graph);

				/* launching DOM events */
				self.dialog.events_postLoading();

				/* showing dialog */
				self.dialog.show();

				/* setting dialog label */
				var allograph_label = $('.myModal .allograph_form option:selected').text();
				self.dialog.set_label(allograph_label);

				/* applying delete event to selected feature */
				var delete_button = self.dialog.selector.find('#delete');
				delete_button.click(function(event) {
					methods.delete();
				});

				/* applying delete event to selected feature */
				var save_button = self.dialog.selector.find('#save');
				save_button.click(function(event) {
					methods.save();
				});

				/*  */
				self.dialog.edit_letter.init(self.selectedAnnotations[self.selectedAnnotations.length - 1]);

				/* updating selected annotations count */
				if (self.selectedAnnotations.length > 1) {
					if ($('.myModal .badge').length) {
						$('.myModal .badge').html(self.selectedAnnotations.length);
					} else {
						$('.label-modal-value').after(' <span class="badge badge default"> ' + self.selectedAnnotations.length + '</span>');
					}
				}

			});
		});
	};

	var methods = {

		save: function() {

			var graph, feature;
			var data = make_form();
			var url, image_id;

			var hand, allograph;
			if (self.selectedAnnotations.length == 1) {
				graph = self.selectedAnnotations[0];
				feature = self.annotations[graph];
				vector_id = cache.graphs[graph].vector_id;
				image_id = cache.graphs[graph].image_id;

				url = '/digipal/page/' + image_id + '/save/' + vector_id + '/';

				save(url, feature, data.form_serialized, function(data) {
					var new_graphs = data['graphs'];
					for (var ind = 0; ind < new_graphs.length; ind++) {
						var new_graph = new_graphs[ind].graph,
							new_allograph = new_graphs[ind].allograph_id;
						self.cache.update('graph', new_graph, new_graphs[ind]);
						self.cache.update('allograph', new_allograph, new_graphs[ind]);
					}
				});

			} else {

				for (var i = 0; i < self.selectedAnnotations.length; i++) {
					graph = self.selectedAnnotations[i];
					vector_id = cache.graphs[graph].vector_id;
					image_id = cache.graphs[graph].image_id;
					url = '/digipal/page/' + image_id + '/save/' + vector_id + '/';

					save(url, feature, data.form_serialized, function(data) {
						var new_graphs = data['graphs'];
						for (var ind = 0; ind < new_graphs.length; ind++) {
							var new_graph = new_graphs[ind].graph,
								new_allograph = new_graphs[ind].allograph_id;
							self.cache.update('graph', new_graph, new_graphs[ind]);
							self.cache.update('allograph', new_allograph, new_graphs[ind]);
						}

					});
				}
			}
		},

		delete: function() {
			var image_id = self.dialog.temp.image_id;
			var msg, graph, annotation_id;

			if (self.selectedAnnotations.length == 1) {
				msg = 'You are about to delete 1 annotation. Continue?';
				graph = self.selectedAnnotations[0];
				annotation_id = cache.graphs[graph].vector_id;

				if (confirm(msg)) {
					delete_annotation(image_id, annotation_id, function() {
						var graph_element = $('[data-graph="' + graph + '"]');
						graph_element.fadeOut().remove();

						// deleting graph from cache
						delete cache.graphs[graph];
					});
				}

			} else {
				msg = 'You are about to delete ' + self.selectedAnnotations.length + ' annotation. Continue?';
				if (confirm(msg)) {
					for (var i = 0; i < self.selectedAnnotations.length; i++) {
						graph = self.selectedAnnotations[i];
						annotation_id = cache.graphs[graph].vector_id;
						delete_annotation(image_id, annotation_id);
						var graph_element = $('[data-graph="' + graph + '"]');
						graph_element.fadeOut().remove();

						// deleting graph from cache
						delete cache.graphs[graph];

					}
					self.selectedAnnotations = [];
					$('.label-modal-value').after(' <span class="badge badge default">0</span>');
					self.dialog.hide();
				}
			}
		},

		deselect_all: function(button) {
			var key = button.data('key');
			var ul = $('ul[data-key="' + key + '"]');
			var panel = ul.parent();
			panel.find('.to_lightbox').attr('disabled', true);
			var inputs = $('input[data-key="' + key + '"]');
			var annotations = ul.find('[data-graph] img.graph_active').parent().parent();

			$.each(annotations, function() {
				load_graph($(this));
			});

			if (self.dialog.open) {
				self.dialog.hide();
			}
		},

		select_all: function(button) {
			var key = button.data('key');
			var ul = $('ul[data-key="' + key + '"]');
			var panel = ul.parent();
			panel.find('.to_lightbox').attr('disabled', false);
			var annotations = ul.find('li[data-graph]');
			for (var i = 0; i < annotations.length; i++) {
				load_graph($(annotations[i]));
			}
		},
	};

	var removeSelected = function(elements, graph) {
		elements.find('img').removeClass("graph_active");
		for (var j = 0; j < self.selectedAnnotations.length; j++) {
			if (self.selectedAnnotations[j] == graph) {
				self.selectedAnnotations.splice(j, 1);
				j--;
			}
		}
	};

	return {
		'init': init
	};

}

$(document).ready(function() {
	var editGraphsSearch = new EditGraphsSearch();
	editGraphsSearch.init();
});