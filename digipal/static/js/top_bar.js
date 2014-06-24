(function() {
	var is_menu_hidden;
	var resize_menu_icon = $('#resize_menu');
	var top_menu = $('#contentNav');
	var navbar_inner = $('.navbar-inner');
	var nav_collapse = $('.nav-collapse');

	if (typeof localStorage.getItem('menu') === 'undefined' || localStorage.getItem('menu') === null) {
		is_menu_hidden = 'false';
	} else {
		is_menu_hidden = localStorage.getItem('menu');
	}

	resize_menu_icon.on('click', function() {
		if (is_menu_hidden === 'false') {
			top_menu.slideUp();
			$(this).removeClass('icon-resize-small')
				.addClass('icon-resize-full')
				.attr('title', 'Show top bar');
			navbar_inner.css('min-height', 'inherit');
			nav_collapse.addClass('nav_collapse_up');
			is_menu_hidden = "true";
			localStorage.setItem('menu', "true");
		} else {
			top_menu.slideDown();
			$(this).removeClass('icon-resize-full')
				.addClass('icon-resize-small')
				.attr('title', 'Hide top bar');
			navbar_inner.css('min-height', '40px');
			nav_collapse.removeClass('nav_collapse_up');
			is_menu_hidden = "false";
			localStorage.setItem('menu', "false");
		}
	});

	if (is_menu_hidden === 'true') {
		top_menu.slideUp();
		navbar_inner.css('min-height', 'inherit');
		nav_collapse.addClass('nav_collapse_up');
	}

})();