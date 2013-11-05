(function() {

	/*

declaring function to get parameteres from URL

*/

	function getParameter(paramName) {
		var searchString = window.location.search.substring(1),
			i, val, params = searchString.split("&");
		var parameters = [];
		for (i = 0; i < params.length; i++) {
			val = params[i].split("=");
			if (val[0] == paramName) {
				parameters.push(unescape(val[1]));
			}
		}
		return parameters;
	}


	/*

  Setting keyboard shortcuts

  */

	annotator.activateKeyboardShortcuts();



	/*

  Loading annotations

*/

	var request = $.getJSON('annotations/', function(data) {
		annotator.annotations = data;
	});

	var chained = request.then(function(data) {
		var map = annotator.map;
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

				/*

      annotator.vectorLayer.features is the array to access to all the features

      */

				features.push(f);
			}
			// adds all the vectors to the vector layer
			layer.addFeatures(features);
			var vectors = annotator.vectorLayer.features;

			// [was] zooms to the max extent of the map area
			// Now the maps zooms just one step ahead
			map.zoomIn();
			var navigation = new OpenLayers.Control.Navigation({
				'zoomBoxEnabled': false
			});
			map.addControl(navigation);



			/*

			checking
			if there 's a temporary vector as URL parameter

			*/

			var temporary_vectors = getParameter('temporary_vector');
			if (temporary_vectors.length) {
				var geoJSON = new OpenLayers.Format.GeoJSON();
				var temporary_vector = getParameter('temporary_vector');
				var geo_json = JSON.parse(temporary_vector);
				for (var i = 0; i < temporary_vector.length; i++) {
					var object = geoJSON.read(temporary_vector[i]);
					var objectGeometry = object[0];
					objectGeometry.layer = annotator.vectorLayer;
					objectGeometry.style = {
						'fillColor': 'red',
						'strokeColor': 'red',
						"fillOpacity": 0.4
					};
					objectGeometry.described = false;
					objectGeometry.stored = false;
					annotator.vectorLayer.features.push(object[0]);
					annotator.selectFeatureByIdAndZoom(objectGeometry.id);
				}
				if ($('.dialog_annotations').length) {
					var title = geo_json.title;
					var desc = geo_json.desc;
					$('.name_temporary_annotation').val(title);
					$('.textarea_temporary_annotation').val(desc);
				}
			}

			if (typeof vector_id != "undefined" && vector_id && vectors) {
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
					annotator.selectFeatureByIdAndZoom(vector_id_value);
				}, 500);
			}
			trigger_highlight_unsaved_vectors();
			reload_described_annotations();

			if (annotator.isAdmin == 'True') {
				setTimeout(function() {
					var paths = $('#OpenLayers_Layer_Vector_27_vroot').find("path");
					paths.unbind();
					paths.mouseenter(function() {
						var features = annotator.vectorLayer.features;
						for (var i = 0; i < features.length; i++) {
							if ($(this).attr('id') == features[i].geometry.id) {
								if (features[i].display_note) {
									createPopup(features[i]);
								}
							}
						}
					});

					paths.mouseleave(function() {
						var features = annotator.vectorLayer.features;
						for (var i = 0; i < features.length; i++) {
							if (features[i].popup) {
								deletePopup(features[i]);
							}
						}
					});
				}, 1000);
			}


		});



		allographs_box = false;
		allographs_loaded = false;

		/*

  declaring function to filter allographs when clicking #filterAllographs

  */
		$('#filterAllographs').click(function() {

			$(this).addClass('active');


			var checkOutput = '<div class="span6" style="padding:2%;border-right:1px dotted #efefef;"><span class="btn btn-small pull-left" id="checkAll">All</span> <span class="btn btn-small pull-right" id="unCheckAll">Clear</span><br clear="all" />';
			var annotations = annotator.annotations;

			if (!isEmpty(annotations)) {
				var list = [];
				var vectors = [];
				for (var i in annotations) {
					list.push([annotations[i]['feature']]);
				}
				list.sort();
				for (var h = 0; h < list.length; h++) {
					checkOutput += "<p class='paragraph_allograph_check' style='padding:2%;' data-annotation = '" + list[h] + "'>" +
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
		$('#map').css('border', '1px solid #efefef');
		$('#map').css('border-radius', '3px');
		//$("a[data-toggle=tooltip]").tooltip()


		var showImages = 0;
		$('#showImages').click(function() {
			if (!showImages) {
				var position = $(this).position();
				$('#popupImages').css('top', position['top'] + 40);
				$('#popupImages').css('left', position['left'] - 40);
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


		// activating bootstrap plugin for switching on and off annotations
		$('#toggle-state-switch').bootstrapSwitch('toggleState');

		$('#toggle-state-switch').on('click', function() {
			$('#toggle-state-switch').bootstrapSwitch('toggleState');
		});


		$('#toggle-state-switch').on('switch-change', function(e, data) {
			if ($(this).bootstrapSwitch('status')) {
				annotator.vectorLayer.setVisibility(true);
			} else {
				annotator.vectorLayer.setVisibility(false);
			}
		});

		if (typeof get_annotations != "undefined" && get_annotations == "false") {
			$('#toggle-state-switch').bootstrapSwitch('toggleState');
		}

		var modal = false;
		$("#modal_features").draggable({
			zIndex: 1005,
			stack: ".ui-dialog"
		});
		$('#editGraph').click(function() {
			if (modal) {
				modal = false;
				$("#modal_features").fadeOut();
			} else {
				modal = true;
				$("#modal_features").fadeIn();
				$('#modal_features .close').click(function() {
					$("#modal_features").fadeOut();
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
					height: 500,
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
				$('#id_allograph option').removeAttr('disabled');
			} else {
				$('#id_allograph option').attr('disabled', 'disabled');
				$('#id_allograph option[class=type-' + type_id + ']').removeAttr('disabled');
			}
			$('#id_allograph').trigger("liszt:updated");
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
			} else {
				$('.olControlEditingToolbar')[0].style.setProperty("position", "absolute", "important");
				$('.olControlEditingToolbar').css({
					"left": "72%",
					"top": 0,
					"width": "320px",
					"z-index": 1000
				});
			}
		});

	});

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
		} else {
			$('#multiple_boxes').attr('disabled', false);
			$('#boxes_on_click').attr('checked', true).trigger('change');
		}
	});


	$('#id_allograph').on('change', function() {
		var n = 0;
		var features = annotator.vectorLayer.features;
		var allograph = $('#id_allograph option:selected').text();
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
		if (annotator.isAdmin == "False") {
			annotator.user_annotations.push(feature.feature.id);
		}

		annotator.selectFeatureById(feature.feature.id);
		//annotator.rectangleFeature.deactivate();
		//annotator.selectFeature.activate();
		annotator.unsaved_annotations.push(feature);
		$('.number_unsaved_allographs').html(annotator.unsaved_annotations.length);
		var last_feature_selected = annotator.last_feature_selected;
		if (last_feature_selected) {
			$('#id_allograph').val(last_feature_selected.id).trigger('liszt:updated');
			var features = annotator.vectorLayer.features;
			var n = 0;
			for (var i = 0; i < features.length; i++) {
				if (features[i].feature == last_feature_selected.name && features[i].stored) {
					n++;
				}
			}
			$(".number_annotated_allographs .number-allographs").html(n);
		}

	}

	$('#boxes_on_click').on('change', function() {
		if ($(this).is(':checked')) {
			annotator.boxes_on_click = true;
		} else {
			annotator.boxes_on_click = false;
		}
	});

	$("#id_allograph").on("liszt:ready", function() {
		highlight_vectors();
		/*
		$("#id_allograph").append($("#id_allograph option").remove().sort(function(a, b) {
			var at = $(a).text(),
				bt = $(b).text();
			return (at > bt) ? 1 : ((at < bt) ? -1 : 0);
		}));
		$(this).trigger("liszt:update");
		*/
	});

	$('select').chosen();


	if ($('#boxes_on_click').is(':checked')) {
		annotator.boxes_on_click = true;
	}



})();