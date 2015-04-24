jQuery(document).ready(function($) {

	/*

    defining default options

    */

	$.
	default = {
		scribe: '#id_scribe',
		components: '#id_form-0-component',
		allographs: '#id_form-0-allograph',
		features: '#features_container'
	};


	/*

    defining the main class $.main

    */

	$.main = {
		scribe: $(
			$.
			default.scribe),
		components: $(
			$.
			default.components),
		allographs: $(
			$.
			default.allographs),
		features: $(
			$.
			default.features),
		idiographSelected: null,

		/*

        defining the method to initiate the whole class

        */

		init: function() {

			$features = [];
			this.events();

		},

		/*

        defining the method to attach events to each method

        */

		events: function() {

			/*

            defining the method to attach the event on
            the scribe select

            */

			$.main.scribe.on('change', function(event) {

				// scribe is the id got from the select to select a scribe
				var scribe = $(this).val(); // scribe id

				// loading idiographs
				$.main.load_idiographs(scribe);
				$.main.new_idiograph();

				// reset all features
				$features = [];
			});


			$.main.allographs.on('change', function(event) {

				// id of the allograph
				var allograph = $(this).val();

				// loading components according to the allograph selected
				$.main.load_components(allograph);

				// reset features list
				$features = [];
			});

			// Enable events on buttons to check/uncheck all checkboxes
			this.check_all();
			this.uncheck_all();

			// new idiograph
			$('#new_idiograph_Button').click(function() {
				$.main.new_idiograph();
			});

			$('#subButton').click(function() {
				$.main.window_save_idiograph();
			});

		},


		/*
        
        Method to load idiographs
        pass the list of idiographs to @show_idiographs

        */

		load_idiographs: function(scribe) {

			var idiographs = [];
			var gif = $('#ajax_loader');
			gif.fadeIn();
			var load_idiographs = $.getJSON('get_idiographs/', {
				'scribe': scribe
			});

			load_idiographs.done(function(data) {
				gif.fadeOut();
				$.each(data, function() {
					idiographs.push(this);
				});
				$.main.show_idiographs(idiographs);
				$.each(data, function(index, value) {
					if (value.num_features > 0) {
						var p_idiographs = $('.idiograph_label');
						$.each(p_idiographs, function() {
							if ($(this).data('idiograph') == value.id) {
								$(this).data('has_features', true);
								$(this).css({
									'background': 'hsl(76, 21%, 52%)',
									'color': '#fff'
								});
							}
						});
					}
				});
			});

		},

		/*
        
        Method to show idiographs in the right section got
        from the method @load_idiographs

        */

		show_idiographs: function(idiographs) {
			var s;
			var i;
			if (idiographs.length > 0) {
				s = '';
				for (i = 0; i < idiographs.length; i++) {
					s += "<p data-idiograph = '" + idiographs[i].id + "' class='idiograph_label row-fluid' data-id = '" + idiographs[i].id + "' ><span class='span7'>" + idiographs[i].idiograph + "</span> <input type='button' data-idiograph = '" + idiographs[i].id + "' class='view_idiograph span2' value='View' /><input type='button' data-idiograph = '" + idiographs[i].id + "' class='delete_idiograph span2' value='Delete' /></p>";
				}
			} else {
				s = '<p style="padding:1%;">No Idiographs for this scribe</p>';
				i = 0;
			}
			$("#number_idiographs").html("(" + i + ")");
			var idiographs_div = $('#idiographs_container');
			idiographs_div.html(s);
			$('.idiograph_label').click(function() {
				event.preventDefault();
				$.main.select_idiograph($(this));
			});
			$('.delete_idiograph').click(function(event) {
				event.preventDefault();
				$.main.window_delete_idiograph($(this).data('data-idiograph'));
			});
			$('.view_idiograph').click(function(event) {
				event.preventDefault();
				event.stopPropagation();
				$.main.select_idiograph($(this).parent('.idiograph_label'), true);
			});
		},

		/*
        
        Method to load components into the select
        according to the allograph selected

        */

		load_components: function(allograph, idiograph_component) {
			$.main.components.data('idiograph_component', idiograph_component);
			var allographs = $.getJSON("get_allographs/", {
				'allograph': allograph
			});

			allographs.done(function(data) {
				var components_select = '';
				var features_select = '';
				var features_list = [];
				$.each(data, function(idx) {
					var component = data[idx].name;
					var component_id = data[idx].id;
					components_select += "<option value = '" + component_id + "'>" + component + "</option>";
					var features = data[idx].features;
					var feature = {
						'component': component,
						'component_id': component_id,
						'features': features
					};
					features_list.push(feature);
					$.main.components.html(components_select).trigger('liszt:updated');
					var component_selected = $.main.components.val();
					$.main.show_features(component_selected, features_list);
				});
				if (typeof features != "undefined") {
					$.main.check_common_features(features);
				}
				$.main.components.on('change', function() {
					var component = $(this).val();
					$.main.show_features(component, features_list);
					if (typeof features != "undefined") {
						$.main.check_common_features(features);
					}
				});
			});
		},


		/*
        
        Method to load features into the select
        according to the component selected

        */

		show_features: function(component, features_list) {
			var s = '';
			for (var i = 0; i < features_list.length; i++) {
				if (component == features_list[i].component_id) {
					if (features_list[i].features.length > 0) {
						for (var j = 0; j < features_list[i].features.length; j++) {
							var name = features_list[i].features[j].name;
							var id = features_list[i].features[j].id;
							s += "<p class='feature'>";
							s += "<input type='checkbox' data-name = '" + name + "' id='feature_" + id + "' value = '" + id + "' />";
							s += " <label for='feature_" + id + "' class='label_feature'>" + name + "</label>";
							s += "</p>";
						}
					} else {
						break;
					}
				}
			}
			// load features into div #features_container
			$.main.features.html(s);

			$('input[type=checkbox]').on('change', function(event) {
				event.stopPropagation();
				event.preventDefault();
				var component = $('#id_form-0-component').val();
				if (!$(this).is(':checked')) {
					for (var i = 0; i < $features.length; i++) {
						for (var j = 0; j < $features[i].features.length; j++) {
							if ($(this).val() == $features[i].features[j].id) {
								$features[i].features.splice(j, 1);
								j--;
								break;
							}
						}
					}
				} else {
					var feature = {
						'id': $(this).val(),
						'name': $(this).data('name')
					}
					if (!$features.length) {
						$features.push({
							'id': component,
							'idiograph_component': false,
							'features': [feature]
						});
					} else {
						var f = false;
						for (var i = 0; i < $features.length; i++) {
							if ($features[i].id == component) {
								$features[i].features.push(feature);
								f = false;
								break;
							} else {
								f = true;
							}
						}
						if (f) {
							$features.push({
								'id': component,
								'idiograph_component': false,
								'features': [feature]
							});
						}
					}
				}
			});

			if (typeof features != "undefined") {
				$features.concat(features);
			}
			$.main.check_common_features($features);

		},

		/*
        
        Method to select an idiograph

        */

		select_idiograph: function(idiograph, view) {
			if (this.idiographSelected !== null) {
				if (this.idiographSelected.data('has_features')) {
					this.idiographSelected.css({
						'background-color': 'hsl(76, 21%, 52%)',
						'color': '#fff'
					});
				} else {
					this.idiographSelected.css({
						'background-color': '#fff',
						'color': '#444'
					});
				}
			}
			this.idiographSelected = idiograph;
			$features = [];
			$('#idiograph_selected').html(this.idiographSelected.find('span').text());
			var id = this.idiographSelected.data('id');
			this.idiographSelected.css({
				'background-color': '#ddd',
				'color': '#444'
			});
			var load_idiograph = $.getJSON('get_idiograph/', {
				'idiograph': id
			});
			load_idiograph.done(function(data) {
				var data = data[0];
				var allograph = data['allograph_id'][0];
				$features = data.components;
				$.main.allographs.val(allograph).trigger('liszt:updated');
				$.main.load_components(allograph, data.components.idiograph_component);
				var n = 0;
				for (var i = 0; i < data.components.length; i++) {
					var features_length = data.components[i].features.length;
					n += features_length;
				}
				$('#num_features').html("(" + n + " features described)");
				if (typeof view != "undefined" && view) {
					$.main.view_idiograph()
				}
			});
		},

		check_common_features: function(features) {
			var checkboxes = $('#features_container').find("input[type=checkbox]");
			for (var i = 0; i < $features.length; i++) {
				var local_features = features[i].features;
				for (var h = 0; h < local_features.length; h++) {
					var feature = local_features[h];
					for (var j = 0; j < checkboxes.length; j++) {
						if (feature.id == checkboxes[j].value) {
							checkboxes[j].checked = true;
						}
					}
				}
			}
			return false;
		},

		/*
        
        Method to load save the current idiograph

        */

		save_idiograph: function(scribe) {
			var allograph = $('#id_form-0-allograph').val();
			var scribe = $('#id_scribe').val();
			var data = {
				'scribe': scribe,
				'allograph': allograph,
				"data": JSON.stringify($features)
			};
			$.ajax({
				url: 'save_idiograph/',
				data: data,
				type: 'POST',
				beforeSend: function() {
					$('#ajax_loader2').fadeIn();
				},
				success: function(data) {
					if (!data['errors']) {
						var num = parseInt($('#number_idiographs').text());
						$('#number_idiographs').html(num + 1);
						var scribe = $('#id_scribe').val()
						$.main.load_idiographs(scribe);
						$(".window").fadeOut().remove();
					} else {
						$($(".window").find('p')[0]).html('Error during transaction');
					}
				},
				complete: function(data) {
					$('#ajax_loader2').fadeOut();
				},
				error: function() {
					$($(".window").find('p')[0]).html('Error during transaction');
				}
			});
		},

		update_idiograph: function(idiograph) {
			var allograph = $('#id_form-0-allograph').val();
			var idiograph_id = idiograph.data('id');
			var data = {
				'allograph': allograph,
				'idiograph_id': idiograph_id,
				"data": JSON.stringify($features)
			};
			$.ajax({
				url: 'update_idiograph/',
				data: data,
				type: 'POST',
				beforeSend: function() {
					$('#ajax_loader2').fadeIn();
				},
				success: function(data) {
					//console.log(data);
					if (!data['errors']) {
						var scribe = $('#id_scribe').val()
						$.main.load_idiographs(scribe);
						$(".window").fadeOut().remove();
						scribe = null;
					} else {
						$($(".window").find('p')[0]).html('Error during transaction');
					}
				},
				complete: function() {
					$('#ajax_loader2').fadeOut();
					allograph = null;
				},
				error: function(data) {
					//console.log(data);
					$($(".window").find('p')[0]).html('Error during transaction');
				}
			});
		},

		delete_idiograph: function(idiograph) {
			var idiograph_id = idiograph.data('id');
			$.ajax({
				url: 'delete_idiograph/',
				type: 'POST',
				data: {
					"idiograph_id": idiograph_id
				},
				beforeSend: function() {
					$('#ajax_loader2').fadeIn();
				},
				success: function(data) {
					if (!data['errors']) {
						var scribe = $('#id_scribe').val()
						$.main.load_idiographs(scribe);
						$(".window").fadeOut().remove();
						scribe = null;
					} else {
						$($(".window").find('p')[0]).html('Error during transaction');
					}
				},
				complete: function() {
					$('#ajax_loader2').fadeOut();
					idiograph_id = null;
					$.main.new_idiograph();
				},
				error: function() {
					$($(".window").find('p')[0]).html('Error during transaction');
				}
			});
		},

		view_idiograph: function() {

			var s = '';
			var window_div;
			var label;

			if ($features.length) {
				for (var i = 0; i < $features.length; i++) {
					var component = $features[i].name;
					s += "<h2>" + component + "</h2>";
					var features = $features[i].features;
					for (var j = 0; j < features.length; j++) {
						s += "<p class='idiographs_p'>" + features[j].name + "</p>";
					}
				}
			} else {
				s += "<p>Idiograph not described</p>";
			}

			if (!$(".window_idiographs").length) {
				window_div = $('<div class="window_idiographs">').draggable();
				label = $.main.idiographSelected.children('.span7').text();
				$('body').append(window_div);

			} else {
				window_div = $(".window_idiographs");
				label = $.main.idiographSelected.children('.span7').text();
				window_div.fadeIn();
			}

			window_div.html("<h1 style='margin:0;margin-bottom:1%;border-bottom:1px dotted #efefef:'>" + label + "<span class='close pull-right'>X</span></h1>");
			window_div.append(s);

			$('.close').click(function() {
				window_div.fadeOut();
			});


		},


		window_save_idiograph: function(idiograph) {
			if (!$(".window").length) {
				var window_save = $('<div>');
				window_save.attr('class', 'window');
				var label_save;
				var button_function;
				if ($.main.idiographSelected) {
					label_save = "update";
				} else {
					label_save = "add";
				}
				var scribe = $('#id_scribe');
				var allograph = $('#id_form-0-allograph');

				if (scribe.val() && allograph.val()) {
					var s = '<p>Do you want to <u>' + label_save + '</u> this idiograph? <img src="/static/images/ajax-loader-ball.gif" id ="ajax_loader2" style="display:none" /></p>';
					s += "<p style='margin-top:4%'><input value='Save' type='button' class='success' id='save' /> <input type='button' value='Cancel' class='close' />";
				} else {
					var s = "<p>Did you select all the required fields?</p>";
					s += "<p>Please select <b>Scribe</b> and <b>Allograph</b>";
					s += "<p style='margin-top:4%'><input type='button' value='Back' class='close' />";

				}
				window_save.html(s);
				$('#frmAnnotation').append(window_save);
				$('#save').click(function() {
					if ($.main.idiographSelected) {
						$.main.update_idiograph($.main.idiographSelected);
					} else {
						$.main.save_idiograph();
					}
				});
				$('.close').click(function() {
					window_save.fadeOut().remove();
				});
			}
		},

		window_delete_idiograph: function(idiograph) {
			if (!$(".window").length) {
				var window_delete = $('<div>');
				window_delete.attr('class', 'window');
				var s = '<p>Do you want to delete this idiograph?</p>';
				s += "<p style='margin-top:4%'><input value='Delete' type='button' class='confirm' id='delete' /> <input type='button' value='Cancel' class='close' />";
				window_delete.html(s);
				$('#frmAnnotation').append(window_delete);
				$('#delete').click(function() {
					$.main.delete_idiograph($.main.idiographSelected);
				});
				$('.close').click(function() {
					window_delete.fadeOut().remove();
				});
			}
		},

		new_idiograph: function() {
			this.components.html('').trigger('liszt:updated');
			this.allographs.val('').trigger('liszt:updated');
			if (this.idiographSelected !== null) {
				this.idiographSelected.css('background-color', '');
			}
			this.idiographSelected = null;
			$('#idiograph_selected').html('Null (Defining new Idiograph)');
			$('#features_container').html('');
			$('#num_features').html('');
			$features = [];
		},

		check_all: function() {
			var input = $('#check_all');
			input.click(function() {
				$('input[type=checkbox]').attr('checked', true);
			});
		},

		uncheck_all: function() {
			var input = $('#uncheck_all');
			input.click(function() {
				$('input[type=checkbox]').attr('checked', false);
			});
		}


	};

	// utils functions

	$.utils = {
		getParameter: function(paramName) {
			var searchString = window.location.search.substring(1),
				i, val, params = searchString.split("&");
			var parameters = [];
			for (i = 0; i < params.length; i++) {
				var val = params[i].split("=");
				if (val[0] == paramName) {
					parameters.push(unescape(val[1]));
				}
			}
			return parameters;
		},

		getCookie: function(name) {
			var cookieValue = null;
			if (document.cookie && document.cookie !== '') {
				var cookies = document.cookie.split(';');
				for (var i = 0; i < cookies.length; i++) {
					var cookie = jQuery.trim(cookies[i]);
					// Does this cookie string begin with the name we want?
					if (cookie.substring(0, name.length + 1) == (name + '=')) {
						cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
						break;
					}
				}
			}
			return cookieValue;
		}
	};

	// declaring the whole script

	function main() {
		var csrftoken = $.utils.getCookie('csrftoken');
		$.ajaxSetup({
			headers: {
				"X-CSRFToken": csrftoken
			}
		});
		$.main.init();
		$('select').chosen();
		var scribe = $.utils.getParameter('scribe');
		if (scribe[0] !== undefined && scribe[0] !== "") {
			$.main.load_idiographs(scribe[0]);
			$.main.scribe.val(scribe[0]);
			$.main.scribe.trigger('liszt:updated');
		}
	}

	// launching the whole script
	main();

});