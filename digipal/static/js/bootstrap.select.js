$.fn.bootstrapSelect = function(options, callback) {

	var $element = $(this);

	/*
		@label {String|Boolean}
		** The default label of the button to show the dropdown is the first element of the select
		** Overwrite this option to have an initial label for the button

		@parent {Object}
		** The default values for parent is selector: false, placement: ''.
		** If not overwritten, the new elements will be created just after the select element

		** @parent.selector is the selector where to put the new elements generated
		** @parent.placement is where to put the new elements inside the parent selector. It could be:
			- append: it will append the elements at the end of the node
			- prepend: it will append the elements at the beginning of the node
			- inner: it will overwrite the whole node element with the new elements

		@input_group {Boolean}
		** Specifies if the select is contained into an input group div

		@class
		** Specifies the Bootstrap class to be applied to the button

		*/



	var default_options = {
		label: false,
		input_group: false,
		class: 'default',
		parent: {
			selector: $element.parent(),
			placement: 'append'
		}
	};

	default_options = $.extend(default_options, options);

	var parent = default_options.parent;
	var parentSelector = $(default_options.parent.selector);
	var caret = ' <span class="caret"></span>';

	var _id = "select-" + $element.attr('id');

	var init = function() {
		createElements(function() {
			events();
			if (callback) {
				callback();
			}
		});
	};

	var Button = function(_id) {

		var element = $('<button class="btn" type="button" role="button" data-toggle="dropdown" id="' + _id + '">');
		element.addClass("btn-" + default_options.class);

		var set_label = function(label) {
			element.html(label + caret);
		};

		return {
			'selector': element,
			'set_label': set_label
		};
	};

	var Dropdown = function(_id) {

		var element = $('<ul class="dropdown-menu" aria-labelledby=' + _id + ' role="menu">');

		if (default_options.input_group) {
			element.css("top", "88.5%");
		}

		var options = '',
			option, option_inner_a;

		$element.find('option').each(function() {
			option = $('<li>');
			option_inner_a = $('<a>');
			option_inner_a.data('value', $(this).val()).html($(this).text()).css('cursor', 'pointer');

			if ($(this).attr('disabled') == 'true' || $(this).attr('disabled') == 'disabled') {
				option_inner_a.attr('disabled', 'disabled');
			}

			option.append(option_inner_a);
			element.append(option);
		});

		return element;
	};

	var events = function() {

		/*	The select element gets hidden	*/
		$element.hide();

		/*	Selecting button and dropdown elements	*/
		var button_element = $('#' + _id);
		var select = $('[aria-labelledby="' + _id + '"]');

		/*
		 ** Actvating event on click on dropdown elements to change
		 ** the value of the actual select
		 */

		select.find('a').on('click', function(event) {

			var _val = $(this).data('value');
			var _label = $(this).text();

			/*	Assigning values to button (label) and real select (value)	*/
			$element.val(_val.toString()).trigger('change');
			button_element.html(_label + caret);

			/*	Preventing link action	*/
			event.preventDefault();
		}).css('cursor', 'pointer');

		button_element.on('focus', function(event) {
			$element.trigger('focusin');
			event.stopPropagation();
		}).on('blur', function(event) {
			$element.trigger('blur');
			event.stopPropagation();
		});

	};

	var createElements = function(callback) {

		var element = $('<div class="dropdown">');

		if (default_options.input_group) {
			element.addClass('input-group-btn');
		}

		var _label;

		var button = new Button(_id);
		var dropdown = new Dropdown(_id);

		if (default_options.label) {
			_label = default_options.label;
		} else {
			_label = $element.find('option')[0].innerHTML;
		}

		button.set_label(_label);
		element.append(button.selector).append(dropdown);
		inject(element);
		callback();
	};

	var inject = function(elements) {

		if (!parent.placement || parent.placement == 'append') {
			parentSelector.append(elements);
		} else {
			if (parent.placement == 'prepend') {
				parentSelector.prepend(elements);
			} else if (parent.placement == 'inner') {
				parentSelector.html(elements);
			}
		}
	};

	init();
	return $element;
};