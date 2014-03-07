function Allographs() {

	// referencing class to variable self
	var self = this;

	// assigning dialog class as a property of this class
	self.dialog = dialog;

	self.selectedAnnotations = {
		'allograph': null,
		'annotations': []
	};

	var temporary_vectors = [];

	// importing cache class
	self.allographs_cache = new AnnotationsCache();

	// returning actual class object
	var allographs_cache = self.allographs_cache.init();

	// launcing init function
	var init = function() {
		events();
	};


	// this function declares all events at loading
	var events = function() {

		/* creating dialog */
		self.dialog.init(annotator.image_id, {
			'container': '#allographs'
		}, function() {

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

		});

		/* applying select event to annotations */
		var annotations_li = $('.annotation_li');
		annotations_li.unbind().click(function(event) {
			methods.select_annotation($(this));
		});

		/* applying select all event */
		var select_all = $('.select_all');
		select_all.click(function(event) {
			methods.select_all($(this));
		});

		/* applying deselect all event */
		var deselect_all = $('.deselect_all');
		deselect_all.click(function(event) {
			methods.deselect_all($(this));
		});

		/* applying to_lightbox function */
		var to_lightbox = $('.to_lightbox');
		to_lightbox.click(function(event) {
			if (self.selectedAnnotations.annotations.length > 1) {
				var annotations = [];
				for (var i = 0; i < self.selectedAnnotations.annotations.length; i++) {
					annotations.push(self.selectedAnnotations.annotations[i].graph);
				}

				methods.to_lightbox($(this), annotations, true);
			} else {

				methods.to_lightbox($(this), self.selectedAnnotations.annotations[0].graph, false);
			}

		});

		/* event to redirect from letters to annotator */
		var a_images = $('.annotation_li a');
		a_images.click(function(event) {
			var id = $(this).parent('.annotation_li').data('annotation');
			methods.to_annotator(id);

			/*
			var panel = $('#panelImageBox');
			$('body').animate({
				scrollLeft: panel.position().left,
				scrollTop: panel.position().top
			});
			*/

			event.stopPropagation();
			event.preventDefault();
		});

		keyboard_shortcuts.init();

	};

	var methods = {

		select_annotation: function(this_annotation) {
			b = self.selectedAnnotations.annotations;
			cache = allographs_cache;
			var annotation = getFeatureById(this_annotation.data('annotation'));
			var current_basket;
			var annotation_li = this_annotation;
			var a = self.selectedAnnotations.allograph;
			/*
			if (self.selectedAnnotations.allograph && self.selectedAnnotations.allograph != annotation.feature) {
				self.selectedAnnotations.allograph = null;
				self.selectedAnnotations.annotations = [];
				$('.annotation_li').removeClass('selected').data('selected', false);
				temporary_vectors = [];
			}
			*/
			if (annotation_li.data('selected')) {
				utils.clean_annotations(annotation, self.selectedAnnotations.annotations);
				annotation_li.data('selected', false).removeClass('selected');
				select_annotation(annotation, false);
			} else {
				self.selectedAnnotations.allograph = annotation.feature;
				self.selectedAnnotations.annotations.push(annotation);
				annotation_li.data('selected', true).addClass('selected');
				modal = true;
				select_annotation(annotation, true);
			}
		},

		save: function() {
			var features = annotator.vectorLayer.features;
			var features_length = features.length;
			var selected_features = [];
			for (var i = 0; i < features_length; i++) {
				for (var j = 0; j < self.selectedAnnotations.annotations.length; j++) {
					if (features[i].graph == self.selectedAnnotations.annotations[j].graph) {
						selected_features.push(features[i]);
					}
				}
			}
			for (i = 0; i < selected_features.length; i++) {
				annotator.selectedFeature = selected_features[i];
				annotator.saveAnnotation(annotation, false);
			}
			//annotator.vectorLayer.redraw();

			/*
			var annotations_li = $('.annotation_li');
			annotations_li.unbind().click(function(event) {
				self.select_annotation($(this));
			});
			*/
		},

		delete: function() {
			var features = annotator.vectorLayer.features;
			var features_length = features.length;
			var selected_features = [];
			var vectors_list = [];
			var i, j;
			for (i = 0; i < features_length; i++) {
				for (j = 0; j < self.selectedAnnotations.annotations.length; j++) {
					if (features[i].graph == self.selectedAnnotations.annotations[j].graph) {
						selected_features.push(features[i]);
					}
				}
			}

			j = 0;
			var msg = 'You are about to delete ' + self.selectedAnnotations.annotations.length + ' annotations. It cannot be restored at a later time! Continue?';
			if (confirm(msg)) {
				var nextAll, element, value;
				for (i = 0; i < selected_features.length; i++) {
					delete_annotation(annotator.vectorLayer, selected_features[i], selected_features.length);
					element = $('.annotation_li[data-graph="' + selected_features[i].graph + '"]');
					nextAll = element.nextAll();
					$.each(nextAll, function() {
						value = parseInt($(this).find('.label').text(), 10);
						$(this).find('.label').text(value - 1);
					});
					element.fadeOut().remove();
				}

				self.selectedAnnotations.annotations = [];
				self.dialog.hide();


			}
		},

		deselect_all: function(button) {
			var key = button.data('key');
			var ul = $('ul[data-key="' + key + '"]');
			var panel = ul.parent();
			panel.find('.to_lightbox').attr('disabled', true);
			var inputs = $('input[data-key="' + key + '"]');
			var checkboxes = ul.find('li.selected');

			//self.selectedAnnotations.annotations = [];
			temporary_vectors = [];
			//self.selectedAnnotations.allograph = null;

			$.each(checkboxes, function() {
				methods.select_annotation($(this));
			});

			$.each($('input'), function() {
				$(this).attr('checked', false);
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
			var checkboxes = ul.find('li');
			for (var i = 0; i < checkboxes.length; i++) {
				methods.select_annotation($(checkboxes[i]));
			}
		},

		to_lightbox: function(button, annotations, multiple) {
			add_to_lightbox(button, 'annotation', annotations, multiple);
		},

		to_annotator: function(annotation_id) {
			var tab = $('a[data-target="#annotator"]');
			tab.tab('show');
			annotator.selectFeatureByIdAndZoom(annotation_id);
			var select_allograph = $('#panelImageBox');
			var features = annotator.vectorLayer.features;
			select_allograph.find('.hand_form').val(annotator.selectedFeature.hand);
			var annotation_graph;
			for (var i = 0; i < features.length; i++) {
				for (var j in annotator.annotations) {
					if (annotator.annotations[j].graph == features[i].graph) {
						annotation_graph = annotator.annotations[j];
					}
				}
			}
			select_allograph.find('.allograph_form').val(getKeyFromObjField(annotation_graph, 'hidden_allograph'));
			$('select').trigger('liszt:updated');
		}
	};


	var select_annotation = function(annotation, select) {

		if (typeof annotation === 'undefined') {
			return false;
		}

		var panel = $('ul[data-allograph="' + self.selectedAnnotations.allograph + '"]').parent();
		var temp = annotation;

		if (self.selectedAnnotations.annotations.length > 1) {
			self.dialog.set_label(annotation.feature + " <span class='badge badge-important'>" + self.selectedAnnotations.annotations.length + "</span>");
		} else {
			self.dialog.set_label(annotation.feature);
		}


		if (!self.selectedAnnotations.annotations.length) {
			self.dialog.hide();
			$('.select_annotation_checkbox').attr('checked', false);
			panel.find('.to_lightbox').attr('disabled', true);
		} else {
			self.dialog.show();
			panel.find('.to_lightbox').attr('disabled', false);
		}

		var graphs = [];
		var checkboxes;
		for (var g = 0; g < self.selectedAnnotations.annotations.length; g++) {
			graphs.push(self.selectedAnnotations.annotations[g].graph);
		}

		if (select) {
			load_annotations_allographs.init(annotation, function() {
				checkboxes = $('.features_box');
				detect_common_features(graphs, checkboxes, allographs_cache);
			});

			return false;
		} else {
			annotation = self.selectedAnnotations.annotations[self.selectedAnnotations.annotations.length - 1];
			if (typeof annotation !== 'undefined') {
				load_annotations_allographs.init(annotation, function() {
					checkboxes = $('.features_box');
					detect_common_features(graphs, checkboxes, allographs_cache);
				});
			}

			if (typeof temp !== 'undefined') {
				var graphs_annotation = temp.graph;
				var element_value = $('li[data-graph="' + graphs_annotation + '"]').find('.label-default').text();
				$('.label-summary:contains(' + element_value + ')').remove();
			}
		}



	};

	var utils = {

		clean_annotations: function(annotation, annotations) {
			var length_annotations = annotations.length;
			for (i = 0; i < length_annotations; i++) {
				if (annotations[i].vector_id == annotation.vector_id) {
					annotations.splice(i, 1);
					i--;
					break;
				}
			}
		},

		style_select: function(select) {

			$(select).css({
				"float": "left",
				"margin": "0%",
				"margin-left": "3%",
				"margin-right": "3%",
				"margin-bottom": "3%",
				"margin-top": "2%"
			}).addClass('important_width');
		},

		anchorify: function(string) {
			return string.toLowerCase().replace(' ', '-');
		}

	};

	var load_annotations_allographs = {

		init: function(annotation, callback) {

			if (annotation) {

				var select_allograph = $('.myModal');

				if (self.selectedAnnotations.annotations.length > 1) {
					self.dialog.set_label(annotation.feature + " <span class='badge badge-important'>" + self.selectedAnnotations.annotations.length + "</span>");
				} else {
					self.dialog.set_label(annotation.feature);
				}

				select_allograph.find('.hand_form').val(annotation.hidden_hand);
				select_allograph.find('.allograph_form').val(getKeyFromObjField(annotation, 'hidden_allograph'));

				$('#id_display_note').val(annotation.display_note).parent('p').hide();
				$('#id_internal_note').val(annotation.internal_note).parent('p').hide();

				var all_select = $('select');
				all_select.trigger('liszt:updated');

				this.get_features(annotation, function(s, string_summary) {
					var myModal = $('.myModal');
					var select_allograph = $('.myModal .allograph_form');
					var summary = $('#summary');
					var features_container = $('#features_container');
					summary.html(string_summary);
					features_container.html(s);

					var check_all = $('.check_all');
					var uncheck_all = $('.uncheck_all');
					var prefix = 'allographs_';

					check_all.on('click', function(event) {
						var component = $(this).data('component');
						var checkboxes = $('#' + prefix + 'component_' + component).find("input[type=checkbox]");
						checkboxes.attr('checked', true);
						event.stopPropagation();
					});

					uncheck_all.on('click', function(event) {
						var component = $(this).data('component');
						var checkboxes = $('#' + prefix + 'component_' + component).find("input[type=checkbox]");
						checkboxes.attr('checked', false);
						event.stopPropagation();
					});

					myModal.find('select').chosen();

					myModal.find('.component_labels').click(function() {
						var div = $("#" + $(this).data('id'));
						if (!div.data('hidden')) {
							$(this).next('.checkboxes_div').hide();
							div.slideUp(500).data('hidden', true);
							$(this).find('.arrow_component').removeClass('icon-arrow-up').addClass('icon-arrow-down');
						} else {
							div.slideDown().data('hidden', false);
							$(this).next('.checkboxes_div').show();
							$(this).find('.arrow_component').removeClass('icon-arrow-down').addClass('icon-arrow-up');
						}
					});

					//updateFeatureSelect(annotation.features, feature);
					$('#modal_features .close').click(function() {
						$("#modal_features").fadeOut();
						$('#status').html('-');
						modal = false;
						self.selectedAnnotations.allograph = null;
						self.selectedAnnotations.annotations = [];
						$('.to_lightbox').attr('disabled', true);
						$('.annotation_li').removeClass('selected');
						$('.select_annotation_checkbox').attr('checked', false);
					});

					var select_list = $('select');
					select_list.chosen().trigger('liszt:updated');

					self.dialog.edit_letter.init(annotation.graph);

					if (callback) {
						callback();
					}

				});
			} else {
				return false;
			}
		},

		get_features: function(annotation, callback) {
			var url = '/digipal/api/' + 'graph/' + annotation.graph;
			self.dialog.temp.graph = annotation.graph;

			var features = annotator.vectorLayer.features;

			var allograph = parseInt(annotation.hidden_allograph.split(':')[0], 10);
			var graph = annotation.graph;
			var image_id = annotator.image_id;

			// if there's no allograph cached, I make a full AJAX call
			if (!self.allographs_cache.search("allograph", allograph)) {

				request = $.getJSON(url);
				request.done(function(data) {
					self.allographs_cache.update('allograph', data[0]['allograph_id'], data[0]);
					self.allographs_cache.update('graph', graph, data[0]);
					load_annotations_allographs.refresh(data[0], image_id, callback);
				});

				// else if allograph is cached, I only need the features, therefore I change the URL to omit allographs
			} else if (self.allographs_cache.search("allograph", allograph) && (!self.allographs_cache.search('graph', graph))) {

				url += '/features';
				request = $.getJSON(url);
				request.done(function(data) {
					data[0]['allographs'] = allographs_cache.allographs[allograph];
					self.allographs_cache.update('graph', graph, data[0]);
					load_annotations_allographs.refresh(data[0], image_id, callback);
				});

				// otherwise I have both cached, I can get them from the cache object
			} else {
				var data = {};
				data['allographs'] = allographs_cache.allographs[allograph];
				data['features'] = allographs_cache.graphs[graph]['features'];
				data['allograph_id'] = allographs_cache.graphs[graph]['allograph_id'];
				data['hand_id'] = allographs_cache.graphs[graph]['hand_id'];
				data['hands'] = allographs_cache.graphs[graph]['hands'];
				load_annotations_allographs.refresh(data, image_id, callback);
			}

		},

		refresh: function(data, image_id, callback) {
			var allograph_id = data.id;
			self.dialog.temp.allograph_id = allograph_id;
			var s = "<div id='box_features_container'>";
			var string_summary = '';
			var prefix = 'allographs_';
			var array_features_owned = features_saved(annotation, data['features']);
			var allographs = data['allographs'];
			if (self.selectedAnnotations.annotations.length > 1) {
				var selected = [];

				for (var g = 0; g < self.selectedAnnotations.annotations.length; g++) {
					selected.push(self.selectedAnnotations.annotations[g].graph);
				}
				allographs = common_components(selected, allographs_cache, allographs);
			}
			if (!allographs.length) {
				s += '<p class="component" style="margin:0;">No common components</p>';
			} else {
				$.each(allographs, function(idx) {

					var component = allographs[idx].name;
					var component_id = allographs[idx].id;
					var is_empty;
					var features = allographs[idx].features;
					string_summary += "<span class='component_summary'>" + allographs[idx].name + "</span>";

					s += "<div class='component_labels' data-id='" + prefix + "component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component icon-arrow-up'></span></b>";

					s += "<div class='checkboxes_div btn-group'><span data-component = '" + component_id + "' class='check_all btn btn-xs btn-default'><i class='fa fa-check-square-o'></i></span> <span data-component = '" + component_id + "' class='uncheck_all btn btn-xs btn-default'><i class='fa fa-square-o'></i></span></div></div>";

					s += "<div id='" + prefix + "component_" + component_id + "' data-hidden='false' class='feature_containers'>";
					var n = 0;

					$.each(features, function(idx) {
						var value = component_id + '::' + features[idx].id;
						var names = component + ':' + features[idx].name;
						var f = self.selectedAnnotations.annotations;
						var al = '';
						var d = 0;
						var title = '';
						var ann;
						for (var k = 0; k < f.length; k++) {
							for (var j = 0; j < f[k].features.length; j++) {
								if (f[k].features[j] == component_id + '::' + features[idx].id && f[k].feature == annotation.feature) {
									ann = $('li[data-annotation="' + f[k].vector_id + '"]').find('.label').text();
									if (ann) {
										al += '<span class="label label-default label-summary">' + ann + '</span> ';
										title += ann + ' ';
									}
									d++;
									temporary_vectors.push(names);
								}
							}
						}

						var id = component_id + '_' + features[idx].id;

						var array_features_owned_temporary = array_features_owned.concat(temporary_vectors);

						s += "<div class='row row-no-margin'>";

						if (array_features_owned.indexOf(names) >= 0) {

							s += "<p class='col-md-2'><input checked = 'checked' type='checkbox' value='" + value + "' class='features_box' id='" + id + "' data-feature = '" + features[idx].id + "' /></p>";
							s += "<p class='col-md-10'><label class='string_summary_label' for='" + id + "'>" + features[idx].name + "</label></p>";

						} else {
							s += "<p class='col-md-2'><input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "'/></p>";
							s += "<p class='col-md-10'><label class='string_summary_label' for='" + id + "'>" + features[idx].name + "</label></p>";
						}

						if (array_features_owned_temporary.indexOf(names) >= 0) {
							string_summary += "<span title='" + features[idx].name + "' class='feature_summary'>" + features[idx].name + ' ' + al + "</span>";
							n++;
						}

						s += "</div>";
					});

					s += "</div>";
					if (!n) {
						string_summary += "<span class='feature_summary'>undefined</span>";
					}

				});
			}


			if (callback) {
				callback(s, string_summary);
			}
		}

	};

	var refresh = function() {
		var allographs_container = $('#allographs');
		var img = $("<img id='allographs_tab_loader' src='/static/digipal/images/ajax-loader4.gif' />");
		self.dialog.hide();
		var request = $.ajax({
			url: annotator.absolute_image_url + 'image_allographs/',
			type: 'GET',

			beforeSend: function() {
				allographs_container.html(img);
			},

			success: function(output) {
				allographs_container.html(output);
			},
			complete: function() {

				img.fadeOut().remove();
				annotator.has_changed = false;

				$('[data-toggle="tooltip"]').tooltip({
					container: 'body'
				});

				self.dialog.selector = $("#modal_features");

				init();

			}
		});
	};

	var keyboard_shortcuts = {
		init: function() {
			$(document).on('keydown', function(event) {
				var code = (event.keyCode ? event.keyCode : event.which);
				if (event.ctrlKey) {
					var currentTab = $('.tab-pane.active'),
						tab;
					if (code == 37) { // left
						var prevTab;
						if (!currentTab.prev().length) {
							return false;
						} else {
							prevTab = currentTab.prev();
							tab = $('a[data-target="#' + prevTab.attr('id') + '"]');
							tab.tab('show');
						}
					}
					if (code == 39) { // right
						var nextTab;
						if (!currentTab.next().length) {
							return false;
						} else {
							nextTab = currentTab.next();
							tab = $('a[data-target="#' + nextTab.attr('id') + '"]');
							tab.tab('show');
						}
					}
				}
			});
		}
	};

	return {
		'init': init,
		'refresh': refresh
	};

}


DigipalAnnotator.prototype.Allographs = Allographs;
var allographsPage = new annotator.Allographs();
allographsPage.init();