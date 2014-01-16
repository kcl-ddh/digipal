/**
 * Intiial annotator script loading
   -- Digipal Project --> digipal.eu
 */

(function() {


	/*

	Setting keyboard shortcuts

	*/

	annotator.activateKeyboardShortcuts();

	/*

	Setting default settings

	*/

	var annotating = false;

	if (annotator.isAdmin == 'True') {
		annotating = true;
	}

	var digipal_settings = localStorage.getItem('digipal_settings');

	if (!digipal_settings) {
		digipal_settings = {
			'allow_multiple_dialogs': false,
			'toolbar_position': 'Vertical',
			'boxes_on_click': false,
			'annotating': annotating,
			'select_multiple_annotations': false
		};
	} else {
		digipal_settings = JSON.parse(digipal_settings);
	}

	localStorage.setItem('digipal_settings', JSON.stringify(digipal_settings));


	/*

	Loading annotations

	*/

	var request = $.getJSON('annotations/', function(data) {
		annotator.annotations = data;
	});

	var chained = request.then(function(data) {

		var map = annotator.map;
		// zooms to the max extent of the map area
		map.zoomToMaxExtent();
		var layer = annotator.vectorLayer;
		var format = annotator.format;
		var annotations = data;

		// Loading vectors

		var features_request = $.getJSON('vectors/');
		features_request.done(function(data) {
			var features = [];
			for (var j in data) {
				var f = format.read(data[j])[0];
				f.id = j;
				for (var i in annotations) {
					var allograph = annotations[i]['feature'];
					var character_id = annotations[i]['character_id'];
					var graph = annotations[i]['graph'];
					var character = annotations[i]['character'];
					var hand = annotations[i]['hand'];
					var image_id = annotations[i]['image_id'];
					var num_features = annotations[i]['num_features'];
					var display_note = annotations[i]['display_note'];
					if (f.id == annotations[i]['vector_id']) {
						f.feature = allograph;
						f.character_id = character_id;
						f.graph = graph;
						f.character = character;
						f.hand = hand;
						f.image_id = image_id;
						f.num_features = num_features;
						f.display_note = display_note;

						// it serves to differentiate stored and temporary annotations
						f.stored = true;
					}
				}
				f.linked_to = [];
				/*

      annotator.vectorLayer.features is the array to access to all the features

      */

				features.push(f);
			}
			// adds all the vectors to the vector layer
			layer.addFeatures(features);
			var vectors = annotator.vectorLayer.features;

			var navigation = new OpenLayers.Control.Navigation({
				'zoomBoxEnabled': false,
				defaultDblClick: function(event) {
					return;
				}
			});

			map.addControl(navigation);

			/*

			checking
			if there 's a temporary vector as URL parameter

			*/

			var temporary_vectors = getParameter('temporary_vector');
			if (temporary_vectors.length && !no_image_reason) {
				var geoJSON = new OpenLayers.Format.GeoJSON();
				var geo_json, extent, extent_parsed;

				if (temporary_vectors.length > 1) {
					annotator.selectFeature.multiple = true;
				}

				for (var t = 0; t < temporary_vectors.length; t++) {

					var temp = temporary_vectors[t];
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
					objectGeometry.contentAnnotation = geo_json.desc;
					objectGeometry.contentTitle = geo_json.title;

					annotator.vectorLayer.features.push(object[0]);

					// select feature
					annotator.selectFeatureById(objectGeometry.id);

					//annotator.map.setCenter(objectGeometry.geometry.getBounds().getCenterLonLat());

					// zoom map to extent
					extent_parsed = geo_json.extent;
					console.log(extent_parsed)
					extent = new OpenLayers.Bounds(extent_parsed.left, extent_parsed.bottom, extent_parsed.right, extent_parsed.top);


					// switch annotations if not visible
					if (!geo_json.visibility) {
						switcher.bootstrapSwitch('toggleState');
					}

				}

				annotator.map.zoomToExtent(extent);

				if ($('.dialog_annotations').length) {
					var title = geo_json.title;
					var desc = geo_json.desc;
					$('.name_temporary_annotation').val(title);
					$('.textarea_temporary_annotation').val(desc);
				}

				$('div[role=dialog]').css({
					'top': geo_json.dialogPosition.top,
					'left': geo_json.dialogPosition.left
				});

				/*
				if (typeof geo_json.checkboxes != 'undefined') {
					var checkboxes = $('.checkboxes');
					for (var i = 0; i < geo_json.checkboxes.length; i++) {
						var checkboxOff = geo_json.checkboxes[i];
						$('.paragraph_allograph_check[data-annotation="' + checkboxOff + '"]').find('input').attr('checked', false);
					}
				}
				*/
			}

			if (typeof vector_id != "undefined" && vector_id && vectors && !no_image_reason) {
				// vectorLayer event moveend is triggered on first load so flag this
				initialLoad = true;

				// tries to centre the map every 1/2 second
				interval = setTimeout(function() {

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
					if (getParameter('map_extent').length) {
						var extent_parsed = JSON.parse(getParameter('map_extent')[0]);
						var extent = new OpenLayers.Bounds(extent_parsed.left, extent_parsed.bottom, extent_parsed.right, extent_parsed.top);

						annotator.map.zoomToExtent(extent);
					}

					if (vector_id_value.length == 1) {
						annotator.selectFeatureByIdAndZoom(vector_id_value[0]);
					} else {

						for (var i = 0; i < vector_id_value.length; i++) {
							annotator.selectFeature.multiple = true;
							//annotator.selectFeature.toggle = true;

							annotator.selectFeatureById(vector_id_value[i]);
						}
					}

					// zoom map to extent
					// annotator.map.zoomToExtent(extent);

				}, 500);
			}

			reload_described_annotations();
			trigger_highlight_unsaved_vectors();

		});



		allographs_box = false;
		allographs_loaded = false;

		/*

  declaring function to filter allographs when clicking #filterAllographs

  */
		$('#filterAllographs').click(function() {

			$(this).addClass('active');


			var checkOutput = '<div class="span6" style="padding:2%;"><span class="btn btn-small pull-left" id="checkAll">All</span> <span class="btn btn-small pull-right" id="unCheckAll">Clear</span><br clear="all" />';
			var annotations = annotator.annotations;

			if (!isEmpty(annotations)) {
				var list = [];
				var vectors = [];
				for (var i in annotations) {
					list.push([annotations[i]['feature']]);
				}
				list.sort();
				for (var h = 0; h < list.length; h++) {
					checkOutput += "<p class='paragraph_allograph_check' data-annotation = '" + list[h] + "'>" +
						"<input checked='checked' value = '" + list[h] + "' class='checkVectors' id='allograph_" + list[h] + "' type='checkbox' /> <label for='allograph_" + list[h] + "'' style='display:inline;'>" + list[h] + "</label></p>";
				}
			}
			checkOutput += "</div>";
			checkOutput += '<div class="span6" style="padding:2%;"><span class="btn btn-small pull-left" id="checkAll_hands">All</span> <span class="btn btn-small pull-right" id="unCheckAll_hands">Clear</span><br clear="all" />';
			if (!isEmpty(annotations)) {
				var hands = annotator.hands;
				for (var h = 0; h < hands.length; h++) {
					checkOutput += "<p style='padding:2%;' data-hand = '" + hands[h].id + "'>" +
						"<input checked='checked' value = '" + hands[h].id + "' class='checkVectors_hands' id='hand_input_" + hands[h].id + "' type='checkbox' /> <label for ='hand_input_" + hands[h].id + "'' style='display:inline;'>" + hands[h].name + "</label></p>";
				}
			}
			checkOutput += "</div>";


			$('#allographs_filtersBox').dialog({
				draggable: true,
				height: 300,
				resizable: false,
				width: 320,
				title: "Filter Annotations",
				close: function() {
					$('#filterAllographs').removeClass('active');
				}
			});

			/*$('#ui-dialog-title-allographs_filtersBox').after("<span title='Close box' class='pin-filters-box pull-right'>-</span>");*/

			annotator.removeDuplicate('.paragraph_allograph_check', 'data-annotation', false);
			$('#allographs_filtersBox').html(checkOutput);

			annotator.removeDuplicate('.paragraph_allograph_check', 'data-annotation', false);

			$('.checkVectors').change(function() {
				annotator.filterAnnotation($(this), 'feature');
			});

			$('.checkVectors_hands').change(function() {
				annotator.filterAnnotation($(this), 'hand');
			});

			$('#checkAll').click(function() {
				annotator.filterCheckboxes('.checkVectors', 'check');
			});

			$('#checkAll_hands').click(function() {
				annotator.filterCheckboxes('.checkVectors_hands', 'check');

			});

			$('#unCheckAll').click(function() {
				annotator.filterCheckboxes('.checkVectors', 'uncheck');
			});

			$('#unCheckAll_hands').click(function() {
				annotator.filterCheckboxes('.checkVectors_hands', 'uncheck');

			});

			/*
				$('.pin-filters-box').click(function() {
					$('#filterAllographs').removeClass('active');
					$(this).parent().parent().fadeOut();
				});
				*/



		});
		//$("a[data-toggle=tooltip]").tooltip()
		// activating bootstrap plugin for switching on and off annotations


		var showImages = 0;
		$('#showImages').click(function() {
			if (!showImages) {
				var position = $(this).position();
				$('#popupImages').css('top', position['top'] + 40);
				$('#popupImages').css('left', position['left'] - 55);
				$('#popupImages').fadeIn();
				showImages = 1;
			} else {
				$('#popupImages').fadeOut();
				showImages = 0;
			}
		});

		$('#closeBox').click(function() {
			$('#popupImages').fadeOut();
			showImages = 0;
		});

		var modal = false;
		var modal_element = $("#modal_features");
		modal_element.draggable({
			zIndex: 1005,
			stack: ".ui-dialog"
		});

		$('#editGraph').click(function() {
			if (modal) {
				modal = false;
				modal_element.fadeOut();
			} else {
				modal = true;
				modal_element.fadeIn();
				modal_element.find('.close').click(function() {
					modal_element.fadeOut();
					modal = false;
				});
			}
		});



		/* Set up the Settings Modal */
		var modal_settings = false;
		$('#settings_annotator').click(function() {
			if (modal_settings) {
				modal_settings = false;
				$(this).removeClass('active');
				$("#modal_settings").parent().remove();
			} else {
				modal_settings = true;
				$(this).addClass('active');
				$('#modal_settings').dialog({
					draggable: true,
					resizable: false,
					width: 320,
					title: "Settings",
					close: function(event, ui) {
						modal_settings = false;
						$("#modal_settings").parent().remove();
						$('#settings_annotator').removeClass('active');
					}
				});
			}
		});

		// Filter the allograph by ontograph type.
		// Each time an ontograph type is selected in the settings,
		// we enable only the relevant options in the allograph Select.
		$("#ontograph_type").change(function(event) {
			var type_id = $(event.target).val();
			if (type_id == '0') {
				$('.allograph_form option').removeAttr('disabled');
			} else {
				$('.allograph_form option').attr('disabled', 'disabled');
				$('.allograph_form option[class=type-' + type_id + ']').removeAttr('disabled');
			}
			$('.allograph_form').trigger("liszt:updated");
			highlight_vectors();
		});
		// Filter just after page is loaded.
		$("#ontograph_type").change();

		allow_multiple_dialogs = false;
		$('#multiple_boxes').change(function() {
			if ($(this).is(':checked')) {
				annotator.allow_multiple_dialogs = true;
			} else {
				annotator.allow_multiple_dialogs = false;
			}
		});

		$('input[name=toolbar_position]').change(function() {
			if ($(this).val() == "Vertical") {
				$('.olControlEditingToolbar')[0].style.setProperty("position", "fixed", "important");
				$('.olControlEditingToolbar').css({
					"position": "fixed !important",
					"left": "0px",
					"top": "245px",
					"width": "25px",
					"z-index": 1000
				});
				digipal_settings.toolbar_position = 'Vertical';
			} else {
				$('.olControlEditingToolbar')[0].style.setProperty("position", "absolute", "important");
				digipal_settings.toolbar_position = 'Horizontal';
				if (annotator.isAdmin == 'False') {
					$('.olControlEditingToolbar').css({
						"left": "89%",
						"top": 0,
						"width": "120px",
						'border-top-left-radius': '4px',
						'border-bottom-left-radius': '4px',
						"z-index": 1000
					});
				} else {
					$('.olControlEditingToolbar').css({
						"left": "86%",
						"top": 0,
						'border-top-left-radius': '4px',
						'border-bottom-left-radius': '4px',
						"width": "145px",
						"z-index": 1000
					});
				}
			}
			localStorage.setItem('digipal_settings', JSON.stringify(digipal_settings));
		});

	});

	var switcher = $('#toggle-state-switch');
	switcher.bootstrapSwitch();
	switcher.bootstrapSwitch('setSizeClass', 'switch-small');
	switcher.on('click', function() {
		switcher.bootstrapSwitch('toggleState');
	});


	switcher.on('switch-change', function(e, data) {
		if ($(this).bootstrapSwitch('state')) {
			annotator.vectorLayer.setVisibility(true);
		} else {
			annotator.vectorLayer.setVisibility(false);
		}
	});

	if (typeof get_annotations != "undefined" && get_annotations == "false") {
		switcher.bootstrapSwitch('toggleState');
	}

	$('#modal_features').click(function() {
		$(this).focus();
	});


	$('.ui-dialog').click(function() {
		$(this).focus();
	});

	$('#save').click(function() {
		annotator.saveAnnotation();
	});

	var can_edit = $('#development_annotation');

	can_edit.on('change', function() {
		if ($(this).is(':checked')) {
			$('#multiple_boxes').attr('disabled', 'disabled').attr('checked', false);
			annotator.allow_multiple_dialogs = false;
			annotator.annotating = true;
			digipal_settings.annotating = true;
			localStorage.setItem('digipal_settings', JSON.stringify(digipal_settings));
			enable_annotation_tools();
		} else {
			$('#multiple_boxes').attr('disabled', false);
			$('#boxes_on_click').attr('checked', true).trigger('change');
			annotator.annotating = false;
			digipal_settings.annotating = false;
			localStorage.setItem('digipal_settings', JSON.stringify(digipal_settings));
			disable_annotation_tools();
		}
	});


	$('#panelImageBox .allograph_form').on('change', function() {
		var n = 0;
		var features = annotator.vectorLayer.features;
		var allograph = $('#panelImageBox .allograph_form option:selected').text();
		var allograph_id = $(this).val();

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

	});


	$('.number_annotated_allographs').click(function() {
		open_allographs();
	});

	annotator.rectangleFeature.events.register('featureadded', annotator.rectangleFeature,
		findRectangleFeatureAdded);

	/*
	function check_transform_permission(feature) {
		var vectors = annotator.user_annotations;
		console.log(vectors);
		var flag = false;
		for (var i = 0; i < vectors.length; i++) {
			if (vectors[i] == feature.feature.id) {
				flag = true;
				break;
			}
		}
		console.log(flag);
		if (!flag) {
			annotator.transformFeature.unsetFeature();
		}
	}

	if (annotator.isAdmin == "False") {
		annotator.transformFeature.events.register('beforesetfeature', annotator.transformFeature, check_transform_permission);
	}
	*/

	function findRectangleFeatureAdded(feature) {
		var unsaved_allographs_button = $('.number_unsaved_allographs');
		var last_feature_selected = annotator.last_feature_selected;
		feature.feature.features = [];
		feature.feature.linked_to = [];
		feature.feature.stored = false;
		feature.feature.originalSize = feature.feature.geometry.bounds.clone();
		if (feature.feature.geometry.bounds.top - feature.feature.geometry.bounds.bottom < 10 || feature.feature.geometry.bounds.right - feature.feature.geometry.bounds.left < 15) {
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

		if (unsaved_allographs_button.hasClass('active')) {
			setTimeout(highlight_unsaved_vectors(unsaved_allographs_button), 100);
		}

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

		highlight_vectors();

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

	}

	$('#boxes_on_click').on('change', function() {
		if ($(this).is(':checked')) {
			annotator.boxes_on_click = true;
			digipal_settings.boxes_on_click = true;
			localStorage.setItem('digipal_settings', JSON.stringify(digipal_settings));
		} else {
			annotator.boxes_on_click = false;
			digipal_settings.boxes_on_click = false;
			localStorage.setItem('digipal_settings', JSON.stringify(digipal_settings));
		}
	});

	$("#panelImageBox .allograph_form").on("liszt:ready", function() {
		highlight_vectors();
		/*
		$("#panelImageBox .allograph_form").append($("#panelImageBox .allograph_form option").remove().sort(function(a, b) {
			var at = $(a).text(),
				bt = $(b).text();
			return (at > bt) ? 1 : ((at < bt) ? -1 : 0);
		}));
		$(this).trigger("liszt:update");
		*/
	});

	var select_elements = $('select');
	select_elements.chosen();

	if ($('#boxes_on_click').is(':checked')) {
		annotator.boxes_on_click = true;
		digipal_settings.boxes_on_click = true;
		localStorage.setItem('digipal_settings', JSON.stringify(digipal_settings));
	}

	$("#image_to_lightbox").click(function() {
		add_to_lightbox($(this), 'image', annotator.image_id, false);
	});

	$('#multiple_annotations').on('change', function() {
		if (!$(this).is(':checked')) {
			annotator.selectedAnnotations = [];
			annotator.selectFeature.multiple = false;
			//annotator.selectFeature.toggle = false;
			digipal_settings.select_multiple_annotations = false;

		} else {
			annotator.selectFeature.multiple = true;
			digipal_settings.select_multiple_annotations = true;
			//annotator.selectFeature.toggle = true;
			if (annotator.selectedFeature) {
				annotator.selectedAnnotations.push(annotator.selectedFeature);
			}
		}
		localStorage.setItem('digipal_settings', JSON.stringify(digipal_settings));
	});


	$('a[data-toggle="tab"]').on('shown', function(e) {
		var dialog = $('.ui-dialog');
		if (e.target.innerHTML != 'View Manuscript') {
			if (dialog.length) {
				dialog.fadeOut();
			}
		} else {
			if (dialog.length) {
				dialog.fadeIn();
			}
		}
		return false;
	});

	(function() {
		$('#allow_multiple_dialogs').attr('checked', digipal_settings.allow_multiple_dialogs).trigger('change');
		if (digipal_settings.toolbar_position == 'Vertical') {
			//$('input[name=toolbar_position]').val('Vertical').trigger('change');
			$('#vertical').attr('checked', true).trigger('change');
		} else {
			//$('input[name=toolbar_position]').val('Horizontal').trigger('change');
			$('#horizontal').attr('checked', true).trigger('change');
		}
		$('#boxes_on_click').attr('checked', digipal_settings.boxes_on_click).trigger('change');
		$('#development_annotation').attr('checked', digipal_settings.annotating).trigger('change');
		$('#multiple_annotations').attr('checked', digipal_settings.select_multiple_annotations).trigger('change');
	})();

})();