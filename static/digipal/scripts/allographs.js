function Allographs() {

	var self = this;

	self.dialog = dialog;
	self.selectedAnnotations = {
		'allograph': null,
		'annotations': []
	};

	var temporary_vectors = [];


	var init = function() {
		events();
	};

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

			/* event to show summary */
			var show_summary = $('#show_summary');
			show_summary.click(function() {
				self.dialog.show_summary($(this));
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
			var annotation = getFeatureById(this_annotation.data('annotation'));
			var current_basket;
			var annotation_li = this_annotation;
			var a = self.selectedAnnotations.allograph;
			if (self.selectedAnnotations.allograph && self.selectedAnnotations.allograph != annotation.feature) {
				self.selectedAnnotations.allograph = null;
				self.selectedAnnotations.annotations = [];
				$('.annotation_li').removeClass('selected').data('selected', false);
				temporary_vectors = [];
			}
			if (annotation_li.data('selected')) {
				utils.clean_annotations(annotation, self.selectedAnnotations.annotations);
				annotation_li.data('selected', false).removeClass('selected');
			} else {
				self.selectedAnnotations.allograph = annotation.feature;
				self.selectedAnnotations.annotations.push(annotation);
				annotation_li.data('selected', true).addClass('selected');
				modal = true;
			}

			main(annotation);

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
			var checkboxes = ul.find('li');
			self.selectedAnnotations.annotations = [];
			temporary_vectors = [];
			self.selectedAnnotations.allograph = null;

			checkboxes.data('selected', false).removeClass('selected');
			$.each($('input'), function() {
				$(this).attr('checked', false);
			});

			var modal_features = $("#modal_features");
			if (modal_features.css('display') == 'block') {
				modal_features.fadeout();
			}
		},

		select_all: function(button) {
			self.selectedAnnotations.annotations = [];
			var annotations_li = $('.annotation_li');
			annotations_li.removeClass('selected');
			annotations_li.find('input').attr('checked', false);
			var key = button.data('key');
			var ul = $('ul[data-key="' + key + '"]');
			var panel = ul.parent();
			panel.find('.to_lightbox').attr('disabled', false);
			var checkboxes = ul.find('li');
			var annotation;
			for (var i = 0; i < checkboxes.length; i++) {
				annotation = getFeatureById($(checkboxes[i]).data('annotation'));
				if (self.selectedAnnotations.allograph && self.selectedAnnotations.allograph != annotation.feature) {
					self.selectedAnnotations.allograph = null;
					self.selectedAnnotations.annotations = [];
					ul.find('.annotation_li').removeClass('selected');
					ul.find('.annotation_li').data('selected', false);
					temporary_vectors = [];
				}
				self.selectedAnnotations.annotations.push(annotation);
				var a = self.selectedAnnotations.allograph;

				main(annotation);
			}
			self.selectedAnnotations.allograph = annotation.feature;
			checkboxes.data('selected', true);
			checkboxes.addClass('selected');
			checkboxes.find('input').attr('checked', true);
			modal = true;
			$.each(checkboxes, function() {
				if ($(this).data('allograph') !== self.selectedAnnotations.allograph) {
					$(this).attr('checked', false);
				}
			});
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


	var main = function(annotation) {
		if (!annotation) {
			return false;
		}
		var panel = $('ul[data-allograph="' + self.selectedAnnotations.allograph + '"]').parent();
		if (self.dialog.open) {
			if (self.selectedAnnotations.annotations.length > 1) {
				self.dialog.set_label(annotation.feature + " <span class='badge badge-important'>" + self.selectedAnnotations.annotations.length + "</span>");
			} else {
				self.dialog.set_label(annotation.feature);
			}
		}

		if (!self.selectedAnnotations.annotations.length) {
			self.dialog.hide();
			$('.select_annotation_checkbox').attr('checked', false);
			panel.find('.to_lightbox').attr('disabled', true);
		} else {
			self.dialog.show();
			panel.find('.to_lightbox').attr('disabled', false);
		}

		load_annotations_allographs.init(annotation);

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

		init: function(annotation) {

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

				});
			} else {
				return false;
			}
		},

		get_features: function(annotation, callback) {
			var url = '/digipal/' + 'graph/' + annotation.graph;
			self.dialog.temp.graph = annotation.graph;

			var request = $.getJSON(url);
			var features = annotator.vectorLayer.features;
			var url2;

			request.done(function(data) {
				var allograph_id = data.id;
				self.dialog.temp.allograph_id = allograph_id;
				var s = "<div id='box_features_container'>";
				var string_summary = '';
				var prefix = 'allographs_';
				var array_features_owned = features_saved(annotation, data['features']);
				var allographs = data['allographs'];
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

				callback(s, string_summary);
			});

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