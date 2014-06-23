/**
 * Intiial annotator script loading
   -- Digipal Project --> digipal.eu
 */

function AnnotatorLoader() {

	var self = this;

	this.init = function() {
		self.digipal_settings = self.get_initial_settings(); // loading settings

		var csrftoken = annotator.utils.getCookie('csrftoken');
		$.ajaxSetup({
			headers: {
				"X-CSRFToken": csrftoken
			}
		});

		annotator.annotating = false;
		if (annotator.isAdmin == 'True') { // checking if user is logged in as admin
			annotator.annotating = true; // if logged in as admin, the variable annotations is set as true
		}
		var allographs_box = false,
			allographs_loaded = false;
		var select_elements = $('select');
		select_elements.chosen();
		self.switch_annotations();
		annotator.load_annotations(function() { // once annotations get loaded ...
			self.events(); // events get launched
			self.set_settings(self.digipal_settings); // setting settings
		});
	};

	this.events = function() {

		reload_described_annotations();
		trigger_highlight_unsaved_vectors();

		// activating event on filter button
		var filter_allographs_button = $('#filterAllographs');
		filter_allographs_button.click(function() {

			if ($(this).data('toggle-button') == 'open') {
				self.filter_allographs($(this));
				$(this).data('toggle-button', 'close');
			} else {
				$('#allographs_filtersBox').dialog('close');
				$(this).data('toggle-button', 'open');
				$(this).removeClass('active');
			}
		});

		// activating event on settings button

		var settings_button = $('#settings_annotator');
		settings_button.click(function() {

			if (!$(this).data('toggled')) {
				self.show_settings_window($(this));
				$(this).data('toggled', true);
				$(this).addClass('active');
			}

			if ($(this).data('toggle-button') == 'open' && $("#modal_settings").hasClass('ui-dialog-content')) {
				$("#modal_settings").dialog('open');
				$(this).data('toggle-button', 'close');
				$(this).addClass('active');
			} else {
				$("#modal_settings").dialog('close');
				$(this).data('toggle-button', 'open');
				$(this).removeClass('active');
			}
		});

		var ontograph_type = $("#ontograph_type");
		ontograph_type.on('change', function(event) {
			self.change_ontograph($(event.target).val());
		});

		ontograph_type.trigger('change'); // Filter just after page is loaded.

		var allow_multiple_dialogs = false;
		var multiple_boxes = $('#multiple_boxes');
		multiple_boxes.on('change', function() {
			if ($(this).is(':checked')) {
				annotator.allow_multiple_dialogs = true;
			} else {
				annotator.allow_multiple_dialogs = false;
			}
		});

		var toolbar_checkbox = $('input[name=toolbar_position]');
		toolbar_checkbox.change(function() {
			self.change_toolbar_position($(this).val());
		});

		var can_edit = $('#development_annotation');
		can_edit.on('change', function() {
			self.switch_mode($(this).is(':checked'));
		});

		var modal_features = $('#modal_features');
		modal_features.click(function() {
			$(this).focus();
		});

		var dialogs = $('.ui-dialog');
		dialogs.click(function() {
			$(this).focus();
		});

		annotator.rectangleFeature.events.register('featureadded', annotator.rectangleFeature,
			self.findRectangleFeatureAdded);

		var allograph_form = $('#panelImageBox .allograph_form');
		allograph_form.on('change', function() {
			self.update_allographs_counter($(this).val());
			if (annotator.selectedFeature && annotator.selectedFeature.state === "Insert") {
				annotator.selectedFeature.allograph_id = $(this).val();
				annotator.selectedFeature.feature = $(this).find('option:selected').text();
			}
		});

		var hand_form = $('#panelImageBox .hand_form');
		hand_form.on('change', function(event) {
			if (annotator.selectedFeature && annotator.selectedFeature.state === "Insert") {
				annotator.selectedFeature.hand = $(this).val();
			}
		});

		$('.number_annotated_allographs').click(function() {
			open_allographs();
		});

		allograph_form.on("liszt:ready", function() {
			highlight_vectors();
		});

		var boxes_on_click = $('#boxes_on_click');
		boxes_on_click.on('change', function() {
			self.boxes_on_click($(this).is(':checked'));
		});

		if (boxes_on_click.is(':checked')) {
			annotator.boxes_on_click = true;
			self.digipal_settings.boxes_on_click = true;
			localStorage.setItem('self.digipal_settings', JSON.stringify(self.digipal_settings));
		}

		var star = new Star();
		var selectedCollection = star.getCurrentCollection();
		var image_to_lightbox = $("#image_to_lightbox");

		if (star.isInCollection(selectedCollection, annotator.image_id, 'image')) {
			image_to_lightbox.children().addClass('starred').removeClass('unstarred');
			image_to_lightbox.attr('data-original-title', 'Remove image from collection');
		}

		image_to_lightbox.click(function() {
			if ($(this).children().hasClass('starred')) {
				star.removeFromCollection(image_to_lightbox, 'image');
				$(this).children().removeClass('starred').addClass('unstarred');
				image_to_lightbox.attr('data-original-title', 'Add image to collection');
			} else {
				add_to_lightbox($(this), 'image', annotator.image_id, false);
				$(this).children().removeClass('unstarred').addClass('starred');
				image_to_lightbox.attr('data-original-title', 'Remove image from collection');
			}
		}).tooltip();

		var multiple_annotations = $('#multiple_annotations');
		multiple_annotations.on('change', function() {
			self.multiple_annotations($(this).is(':checked'));
		});

		var show_editorial_annotations = $('#show_editorial_annotations');
		show_editorial_annotations.on('change', function() {
			var features = annotator.vectorLayer.features;
			var is_checked = $(this).is(':checked');
			self.digipal_settings.show_editorial_annotations = is_checked;
			for (var i = 0; i < features.length; i++) {
				if (features[i].is_editorial) {
					if (is_checked) {
						stylize(features[i], 'green', 'green', 0.4);
					} else {
						stylize(features[i], 'green', 'green', 0);
					}
				}
			}
			annotator.vectorLayer.redraw();
			localStorage.setItem('digipal_settings', JSON.stringify(self.digipal_settings));
		});
		annotator.activateKeyboardShortcuts(); // calling keyboard events

		self.toolbar_position();

		// loading annotations through URL (if there are)
		self.load_temporary_vector();
		self.load_stored_vector();

		$('#toolbar div').tooltip({
			container: 'body',
			placement: 'right'
		});

	};

	this.get_initial_settings = function() {
		var digipal_settings = localStorage.getItem('digipal_settings'); // load settings from LS

		/* Setting default settings */

		if (!digipal_settings) {

			digipal_settings = {
				'allow_multiple_dialogs': false,
				'toolbar_position': 'Vertical',
				'boxes_on_click': false,
				'annotating': annotator.annotating,
				'show_editorial_annotations': true,
				'select_multiple_annotations': false
			};

		} else {
			digipal_settings = JSON.parse(digipal_settings);
		}

		localStorage.setItem('digipal_settings', JSON.stringify(digipal_settings));
		return digipal_settings;
	};

	/*
	this.change_tab = function() {
		var pathArray = window.location.pathname.split('/');
		for (var i = 0; i < pathArray.length; i++) {
			if (pathArray[i] === '') {
				pathArray.splice(i, 1);
				i--;
			}
		}
		var part = pathArray[pathArray.length - 1];
		var tabs = $('a[data-toggle="tab"]');
		$.each(tabs, function() {
			if ('#' + part == $(this).data('target')) {
				$(this).tab('show');
			}
		});
	};
	*/
	/*
		* function set_settings
		@parameter self.digipal_settings
			- settings loaded through the function @get_initial_settings
	*/

	this.set_settings = function(digipal_settings) {
		$('#allow_multiple_dialogs').attr('checked', self.digipal_settings.allow_multiple_dialogs).trigger('change');
		if (self.digipal_settings.toolbar_position == 'Vertical') {
			//$('input[name=toolbar_position]').val('Vertical').trigger('change');
			$('#vertical').attr('checked', true).trigger('change');
		} else {
			//$('input[name=toolbar_position]').val('Horizontal').trigger('change');
			$('#horizontal').attr('checked', true).trigger('change');
		}
		$('#boxes_on_click').attr('checked', self.digipal_settings.boxes_on_click).trigger('change');
		$('#development_annotation').attr('checked', self.digipal_settings.annotating).trigger('change');
		$('#multiple_annotations').attr('checked', self.digipal_settings.select_multiple_annotations).trigger('change');
		$('#show_editorial_annotations').attr('checked', self.digipal_settings.show_editorial_annotations).trigger('change');
	};

	/*
		* function load_temporary_vector
			- loads temporary vectors through URL
	*/

	this.load_temporary_vector = function() {
		var temporary_vectors = annotator.utils.getParameter('temporary_vector');
		if (temporary_vectors.length && !no_image_reason) {

			$('html').animate({
				scrollTop: $('#map').position().top + 'px'
			}, 0);

			var geoJSON = new OpenLayers.Format.GeoJSON();
			var geo_json, extent, extent_parsed;

			if (temporary_vectors.length > 1) {
				annotator.selectFeature.multiple = true;
			}

			for (var t = 0; t < temporary_vectors.length; t++) {

				var temp = annotator.utils.Base64.decode(temporary_vectors[t]).normalize();
				geo_json = JSON.parse(temp);
				var object = geoJSON.read(temp);
				var objectGeometry = object[0];

				objectGeometry.layer = annotator.vectorLayer;

				objectGeometry.style = {
					'fillColor': 'red',
					'strokeColor': 'red',
					"fillOpacity": 0.4
				};

				objectGeometry.described = false;
				objectGeometry.stored = false;
				objectGeometry.contentAnnotation = decodeURIComponent(geo_json.desc);
				objectGeometry.contentTitle = geo_json.title;
				objectGeometry.state = 'Insert';
				annotator.vectorLayer.features.push(object[0]);

				// select feature
				annotator.selectFeatureById(objectGeometry.id);
				//annotator.map.setCenter(objectGeometry.geometry.getBounds().getCenterLonLat());

				// zoom map to extent
				extent_parsed = geo_json.extent;
				extent = new OpenLayers.Bounds(extent_parsed.left, extent_parsed.bottom, extent_parsed.right, extent_parsed.top);


				// switch annotations if not visible
				if (!geo_json.visibility) {
					switcher.bootstrapSwitch('toggleState');
				}

			}

			annotator.map.zoomToExtent(extent);
			$('.dialog_annotations').attr('contenteditable', false);
			if ($('.dialog_annotations').length) {
				var title = geo_json.title;
				var desc = unescape(geo_json.desc);
				$('.name_temporary_annotation').val(title);
				$('.textarea_temporary_annotation').html(desc).
				attr('contenteditable', false).
				attr('title', 'Click to edit').
				addClass("noteditable").tooltip({
					'placement': 'right',
					'container': 'body'
				}).
				on('click', function(event) {
					if (event.target.nodeName == 'A') {
						document.location.href = event.target.getAttribute('href');
						return false;
					}
					$(this).attr('contenteditable', true).removeClass("noteditable").tooltip('disable').focus();
				});
			}

			var dialogs = $('div[role=dialog]');
			dialogs.css({
				'top': geo_json.dialogPosition.top,
				'left': geo_json.dialogPosition.left
			});

		} else {
			return false;
		}
	};

	/*
		* function load_stored_vector
			- loads stored vectors through URL
	*/

	this.load_stored_vector = function() {
		if (typeof vector_id_value != "undefined" && vector_id_value && !no_image_reason) {
			$('html').animate({
				scrollTop: $('#map').position().top + 'px'
			}, 0);
			// vectorLayer event moveend is triggered on first load so flag this

			// tries to centre the map every 1/2 second

			/* listen for the moveend event
					annotator.vectorLayer.events.register('moveend',
						annotator.vectorLayer, function() {
							// checks if it is a first load, if not kill the interval
							if (initialLoad) {
								initialLoad = false;
							} else {
								clearInterval(interval);
			annotator.vectorLayer.events.remove('moveend');
							}
						});
					*/
			//annotator.selectFeatureByIdAndCentre(vector_id_value);
			// zoom map to extent

			if (annotator.utils.getParameter('map_extent').length) {
				var extent_parsed = JSON.parse(decodeURI(annotator.utils.getParameter('map_extent')[0]));
				var extent = new OpenLayers.Bounds(extent_parsed.left, extent_parsed.bottom, extent_parsed.right, extent_parsed.top);

				annotator.map.zoomToExtent(extent);
			}

			if (vector_id_value.length == 1) {
				//annotator.selectFeatureByIdAndZoom(getGraphByVectorId(vector_id_value[0]).id);
				annotator.selectFeatureByIdAndZoom(vector_id_value[0]);
			} else {

				for (var i = 0; i < vector_id_value.length; i++) {
					annotator.selectFeature.multiple = true;
					//annotator.selectFeature.toggle = true;

					annotator.selectFeatureById(vector_id_value[i]);
				}
			}

		} else {
			return false;
		}

	};

	/*
		* function filter_allographs
			-  filter allographs according to hands and allographs
	*/

	this.filter_allographs = function(button) {
		button.addClass('active');
		var checkOutput = "<div id='annotations-switcher-alert' class='alert-danger hidden' style='padding: 0.5em;padding-left: 1.5em;font-size: 13px;'>Annotations are turned off</div>";
		checkOutput += '<div style="margin-left: 0;margin-right: 0;padding: 2%;"><div class="col-lg-6">';
		checkOutput += ' <span style="cursor:pointer;" title = "Toggle All" class="pull-left btn btn-xs btn-default" id="checkAll" data-toggle="uncheck">Toggle All</span><br clear="all" />';
		var annotations = annotator.annotations;
		var h;
		if (!$.isEmptyObject(annotations)) {
			var list = [];
			var vectors = [];
			for (var i in annotations) {
				list.push([annotations[i]['feature']]);
			}
			list.sort();
			for (h = 0; h < list.length; h++) {
				checkOutput += "<p class='paragraph_allograph_check' data-annotation = '" + list[h] + "'>";
				checkOutput += "<input checked='checked' value = '" + list[h] + "' class='checkVectors' id='allograph_";
				checkOutput += list[h] + "' type='checkbox' /> <label for='allograph_" + list[h] + "'' style='display:inline;'>" + list[h] + "</label></p>";
			}
		}
		checkOutput += "</div>";
		checkOutput += '<div class="col-lg-6">';
		checkOutput += ' <span style="cursor:pointer;" title = "Toggle All" class="pull-left btn btn-xs btn-default" id="checkAll_hands" data-toggle="uncheck">Toggle All</span><br clear="all" />';



		if (!$.isEmptyObject(annotations)) {
			var hands = annotator.hands;
			for (h = 0; h < hands.length; h++) {
				checkOutput += "<p style='padding:2%;' data-hand = '" + hands[h].id + "'>" +
					"<input checked='checked' value = '" + hands[h].id + "' class='checkVectors_hands' id='hand_input_" + hands[h].id + "' type='checkbox' /> <label for ='hand_input_" + hands[h].id + "'' style='display:inline;'>" + hands[h].name + "</label></p>";
			}
		}

		checkOutput += "</div></div>";
		var switcherClone = $('.toggle-state-switch').clone();
		var allographs_filter_box = $('#allographs_filtersBox');
		if (!allographs_filter_box.hasClass('ui-dialog-content')) {
			allographs_filter_box.dialog({
				draggable: true,
				height: 300,
				resizable: false,
				width: 320,
				title: "<i class='fa fa-filter'></i> Filter Annotations" + switcherClone[0].outerHTML,
				close: function() {
					$('#filterAllographs').removeClass('active');
					button.data('toggle-button', 'open');
				}

			});

			annotator.utils.removeDuplicate('.paragraph_allograph_check', 'data-annotation', false);
			allographs_filter_box.html(checkOutput).css('margin-right', '1px');

			annotator.utils.removeDuplicate('.paragraph_allograph_check', 'data-annotation', false);

			/* launching events */
			var check_vectors = $('.checkVectors');
			check_vectors.change(function() {
				annotator.filters.filterAnnotation($(this), 'feature');
			});

			var check_vectors_hands = $('.checkVectors_hands');
			check_vectors_hands.change(function() {
				annotator.filters.filterAnnotation($(this), 'hand');
			});

			var CheckAll = $('#checkAll');
			CheckAll.click(function() {
				if ($(this).data('toggle') == 'uncheck') {
					annotator.filters.filterCheckboxes('.checkVectors', 'uncheck');
					$(this).data('toggle', 'check');
				} else {
					annotator.filters.filterCheckboxes('.checkVectors', 'check');
					$(this).data('toggle', 'uncheck');
				}
			});

			var checkAll_hands = $('#checkAll_hands');
			checkAll_hands.click(function() {
				if ($(this).data('toggle') == 'uncheck') {
					annotator.filters.filterCheckboxes('.checkVectors_hands', 'uncheck');
					$(this).data('toggle', 'check');
				} else {
					annotator.filters.filterCheckboxes('.checkVectors_hands', 'check');
					$(this).data('toggle', 'uncheck');
				}
			});


			var switcher = $('#allographs_filtersBox').parent().find('.toggle-state-switch');
			var switcherCloned = $('#panelImageBox').find('.toggle-state-switch');
			switcher.bootstrapSwitch();
			switcher.bootstrapSwitch('setSizeClass', 'switch-small');
			switcher.bootstrapSwitch('setState', switcherCloned.bootstrapSwitch('state'));
			switcher.on('click', function() {
				$('.toggle-state-switch').bootstrapSwitch('toggleState');
			});


			switcher.on('switch-change', function(e, data) {
				var checkboxes = $(".checkVectors");
				var checkboxes_hands = $(".checkVectors_hands");
				var toggleButtons = $('#checkAll').add('#checkAll_hands');
				var switcher_alert = $('#annotations-switcher-alert');
				if ($(this).bootstrapSwitch('state')) {
					annotator.vectorLayer.setVisibility(true);
					toggleButtons.attr('disabled', false);

					/* selecting all checkboxes */

					switcher_alert.addClass('hidden');
					checkboxes.add(checkboxes_hands).prop('disabled', false);
				} else {
					annotator.vectorLayer.setVisibility(false);
					switcher_alert.removeClass('hidden');

					/* deselecting all checkboxes */

					toggleButtons.attr('disabled', true);
					checkboxes.add(checkboxes_hands).prop('disabled', true);
				}

				switcherCloned.bootstrapSwitch('setState', switcher.bootstrapSwitch('state'));

				/* fixing annotations placement */
				var container;
				if (annotator.fullScreen.active) {
					container = $(window);
				} else {
					container = $('#map');
				}
				restoreFullscreenPositions();
			});

			if (!$('.toggle-state-switch').bootstrapSwitch('state')) {
				allographs_filter_box.find('input').attr('disabled', true);
				$('#checkAll').add('#checkAll_hands').attr('disabled', true);
				var switcher_alert = $('#annotations-switcher-alert');
				switcher_alert.removeClass('hidden');
			}

		} else {
			allographs_filter_box.dialog('open');
		}

	};

	// activating bootstrap plugin for switching on and off annotations

	this.switch_annotations = function() {
		var switcher = $('.toggle-state-switch');
		switcher.bootstrapSwitch();
		switcher.bootstrapSwitch('setSizeClass', 'switch-small');
		switcher.on('click', function() {
			$('.toggle-state-switch').bootstrapSwitch('toggleState');
		});


		switcher.on('switch-change', function(e, data) {
			var checkboxes = $(".checkVectors");
			var checkboxes_hands = $(".checkVectors_hands");
			var toggleButtons = $('#checkAll').add('#checkAll_hands');
			if ($(this).bootstrapSwitch('state')) {
				annotator.vectorLayer.setVisibility(true);

				/* selecting all checkboxes */
				toggleButtons.attr('disabled', false);
				checkboxes.add(checkboxes_hands).prop('disabled', false);
			} else {
				annotator.vectorLayer.setVisibility(false);

				/* deselecting all checkboxes */
				toggleButtons.attr('disabled', true);
				checkboxes.add(checkboxes_hands).prop('disabled', true);
			}

			var clonedSwitcher = $('#allographs_filtersBox').parent().find('.toggle-state-switch');
			if (clonedSwitcher.length) {
				clonedSwitcher.bootstrapSwitch('setState', switcher.bootstrapSwitch('state'));
			}

			/* fixing annotations placement */
			var container;
			if (annotator.fullScreen.active) {
				container = $(window);
			} else {
				container = $('#map');
			}
			restoreFullscreenPositions();
		});

		if (typeof get_annotations != "undefined" && get_annotations == "false") {
			switcher.bootstrapSwitch('toggleState');
		}

	};

	// shows settings window

	this.show_settings_window = function(button) {
		var modal_settings = false;
		var modal_settings_window = $("#modal_settings");
		if (modal_settings) {
			modal_settings = false;
			button.removeClass('active');
			modal_settings_window.parent('.ui-dialog').remove();
		} else {
			modal_settings = true;
			button.addClass('active');
			modal_settings_window.dialog({
				draggable: true,
				resizable: false,
				width: 320,
				title: "<i class='fa fa-wrench'></i> Settings",
				close: function(event, ui) {
					modal_settings = false;
					button.data('toggle-button', 'open');
					button.removeClass('active');
				}
			});
		}

	};

	// Filter the allograph by ontograph type.
	// Each time an ontograph type is selected in the settings,
	// we enable only the relevant options in the allograph Select.
	this.change_ontograph = function(type_id) {
		var allograph_form = $('#panelImageBox .allograph_form');
		if (type_id == '0') {
			allograph_form.find('option').removeAttr('disabled');
		} else {
			allograph_form.find('option').attr('disabled', 'disabled');
			allograph_form.find('option[class=type-' + type_id + ']').removeAttr('disabled');
		}
		allograph_form.trigger("liszt:updated");
		highlight_vectors();
	};

	// changes toolbar position
	this.change_toolbar_position = function(checkbox_value) {
		var map = $('#map');
		var toolbar = $('#toolbar');
		var toolbar_elements = toolbar.find('div');

		if (checkbox_value == "Vertical") {
			self.digipal_settings.toolbar_position = 'Vertical';

			toolbar_elements.css({
				'width': '100%',
				'font-size': '20px'
			});

			toolbar.css({
				'position': 'fixed',
				"left": map.position().left - 60,
				"top": map.position().top - 150,
				"width": "60px",
				'border-left': '1px solid #ccc',
				'border-top-left-radius': '4px',
				'border-bottom-left-radius': '4px',
				"z-index": 1000
			});

			if (annotator.fullScreen.active) {
				toolbar.removeClass('mapHorizontalFullscreen');
				toolbar.addClass('fullScreenToolbarVertical');
			}

			if ($(window).width() < 860) {
				toolbar.css({
					top: map.position().top - 150,
					left: 0
				});
			} else {
				toolbar.css({
					top: map.position().top - 150,
					left: map.position().left - 60
				});
			}

		} else {
			self.digipal_settings.toolbar_position = 'Horizontal';
			var map_offset = (map.width() + map.position().left);
			if (annotator.isAdmin == 'False') {
				toolbar.css({
					'position': 'absolute',
					"left": map_offset - 296,
					"top": map.position().top,
					"width": "296px",
					'border-left': '1px solid #ccc',
					'border-top-left-radius': '0px',
					'border-top-right-radius': '0px',
					'border-bottom-left-radius': '4px',
					"z-index": 1000
				});

				toolbar_elements.css({
					'width': '17%',
					'font-size': '15px'
				});

			} else {
				toolbar.css({
					'position': 'absolute',
					"left": (map.width() + map.position().left) - 385,
					"top": map.position().top,
					'border-left': '1px solid #ccc',
					'border-top-left-radius': '4px',
					'border-bottom-left-radius': '4px',
					"width": "385px",
					"z-index": 1000
				});

				toolbar_elements.css({
					'width': '35px',
					'font-size': '12px',
					'margin': '2px'
				});
			}

			if (annotator.fullScreen.active) {
				toolbar.removeClass('fullScreenToolbarVertical');
				toolbar.addClass('mapHorizontalFullscreen');
			}
		}

		localStorage.setItem('digipal_settings', JSON.stringify(self.digipal_settings));
		if (annotator.isAdmin) {
			toggle_fixed_toolbar();
		}
	};


	var toggle_fixed_toolbar = function() {
		var toolbar = $('#panelImageBox');
		var toolbar_position = toolbar.offset().top;
		$(document).on('scroll', function() {

			if ($(this).scrollTop() >= toolbar_position) {
				toolbar.addClass('fixed_toolbar');
			} else {
				toolbar.removeClass('fixed_toolbar');
			}
		});
	};

	// switches mode annotating or not annotating
	this.switch_mode = function(checkbox) {
		var multiple_boxes = $('#multiple_boxes');
		var boxes_on_click = $('#boxes_on_click');
		if (checkbox) {
			multiple_boxes.attr('disabled', 'disabled').attr('checked', false);
			annotator.allow_multiple_dialogs = false;
			annotator.annotating = true;
			self.digipal_settings.annotating = true;
			localStorage.setItem('digipal_settings', JSON.stringify(self.digipal_settings));
			annotator.toolbar.enable_annotation_tools();
		} else {
			multiple_boxes.attr('disabled', false);
			boxes_on_click.attr('checked', true).trigger('change');
			annotator.annotating = false;
			self.digipal_settings.annotating = false;
			localStorage.setItem('digipal_settings', JSON.stringify(self.digipal_settings));
			annotator.toolbar.disable_annotation_tools();
		}

	};

	// updated allographs counter of selected allograph according to the allographs select
	this.update_allographs_counter = function(allograph_id) {
		var n = 0;
		var features = annotator.vectorLayer.features;
		var allograph = $('#panelImageBox .allograph_form option:selected').text();

		for (var i = 0; i < features.length; i++) {
			if (features[i].feature == allograph && features[i].stored) {
				n++;
			}
		}

		//updateFeatureSelect($(this).val());

		if ($('.letters-allograph-container').length) {
			open_allographs();
		}

		$(".number_annotated_allographs .number-allographs").html(n);
	};

	// function to be called as a new features gets drawn
	this.findRectangleFeatureAdded = function(feature) {
		var unsaved_allographs_button = $('.number_unsaved_allographs');
		var last_feature_selected = annotator.last_feature_selected;
		feature.feature.features = [];
		feature.feature.linked_to = [];
		feature.feature.stored = false;
		feature.feature.hand = $('#panelImageBox .hand_form').val();
		feature.feature.originalSize = feature.feature.geometry.bounds.clone();
		if (feature.feature.geometry.bounds.top - feature.feature.geometry.bounds.bottom < 5 || feature.feature.geometry.bounds.right - feature.feature.geometry.bounds.left < 10) {
			feature.feature.destroy();
			$('circle').remove();
			$('polyline').remove();
			return false;
		}

		if (annotator.isAdmin == "False") {
			annotator.user_annotations.push(feature.feature.id);
		}

		annotator.selectFeatureById(feature.feature.id);
		//annotator.rectangleFeature.deactivate();
		//annotator.selectFeature.activate();
		annotator.unsaved_annotations.push(feature);

		unsaved_allographs_button.html(annotator.unsaved_annotations.length);

		if (last_feature_selected) {
			//$('#panelImageBox .allograph_form').val(last_feature_selected.id).trigger('liszt:updated');
			var features = annotator.vectorLayer.features;
			var n = 0;
			for (var i = 0; i < features.length; i++) {
				if (features[i].feature == last_feature_selected.name && features[i].stored) {
					n++;
				}
			}
			$(".number_annotated_allographs .number-allographs").html(n);
		}

		var path = $('#' + feature.feature.geometry.id);
		path.dblclick(function(event) {
			var id = $(this).attr('id');
			var feature, boxes_on_click = false;
			var features = annotator.vectorLayer.features;
			for (var i = 0; i < features.length; i++) {
				if (features[i].geometry.id == id) {
					feature = features[i].id;
				}
			}
			if (annotator.boxes_on_click) {
				boxes_on_click = true;
			}
			annotator.boxes_on_click = true;
			annotator.showAnnotation(feature);
			if (!boxes_on_click) {
				annotator.boxes_on_click = false;
				var boxes_on_click_element = $("#boxes_on_click");
				boxes_on_click_element.attr('checked', false);
			}
			event.stopPropagation();
			return false;
		});


	};

	// sets options to open or not boxes when a vector gets clicked on
	this.boxes_on_click = function(is_checked) {
		if (is_checked) {
			annotator.boxes_on_click = true;
			self.digipal_settings.boxes_on_click = true;
			localStorage.setItem('digipal_settings', JSON.stringify(self.digipal_settings));
		} else {
			annotator.boxes_on_click = false;
			self.digipal_settings.boxes_on_click = false;
			localStorage.setItem('digipal_settings', JSON.stringify(self.digipal_settings));
		}
	};

	// sets options to select multiple vectors
	this.multiple_annotations = function(is_checked) {
		if (!is_checked) {
			annotator.selectedAnnotations = [];
			annotator.selectFeature.multiple = false;
			//annotator.selectFeature.toggle = false;
			self.digipal_settings.select_multiple_annotations = false;

		} else {
			annotator.selectFeature.multiple = true;
			self.digipal_settings.select_multiple_annotations = true;
			//annotator.selectFeature.toggle = true;
			if (annotator.selectedFeature) {
				annotator.selectedAnnotations.push(annotator.selectedFeature);
			}
		}
		localStorage.setItem('digipal_settings', JSON.stringify(self.digipal_settings));
	};

	this.toolbar_position = function() {
		var map = $('#map');
		var toolbar = $('#toolbar');

		function set_map() {
			var input_toolbar_position = $("input[name='toolbar_position']:checked");

			toolbar.css({
				'position': 'fixed',
				"width": "60px",
				'border-left': '1px solid #ccc',
				'border-top-left-radius': '4px',
				'border-bottom-left-radius': '4px',
				"z-index": 1000
			});

			if (input_toolbar_position.val() == 'Vertical') {


				if ($(window).width() < 860) {
					toolbar.css({
						top: map.position().top - 150,
						left: 0
					});
				} else {
					toolbar.css({
						top: map.position().top - 150,
						left: map.position().left - 60
					});
				}

			} else {

				toolbar.css({
					top: map.position().top,
					left: map.width() + map.position().left - toolbar.width()
				});

			}
		}

		$(window).resize(function() {
			set_map();
		});

		set_map();

	};


	var getGraphByVectorId = function(vector_id) {
		var annotation;
		$.each(annotator.vectorLayer.features, function() {
			if (this.vector_id == vector_id) {
				annotation = this;
				return false;
			}
		});
		return annotation;
	};

}

var loader = new AnnotatorLoader();
loader.init();