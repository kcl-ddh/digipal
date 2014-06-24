$(document).ready(function() {

	$(window).resize(resizeMenu);
	resizeMenu();

});

function resizeMenu() {
	if ($(window).width() < 757) {
		$('#menu').find('.navbar-collapse').css('background-image', 'none');
		$('#menu .nav').find('a.navLink').addClass('responsive-li');
		$('#menu .nav').find('ul').find('a').addClass('responsive-li');
		$('.navbar-collapse').css('margin-top', '2%');
		$('.navbar .nav > li > a').css('height', 'auto');
		$('.navbar .nav').css('margin-left', ' 2%');
		$('#navQuickSearch').css('background', '#fff');
	} else {
		$('#menu').find('.navbar-collapse').css('background-image', 'url(/static/digipal/images/nav_bg.png)');
		$('#menu').find('a.navLink').removeClass('responsive-li');
		$('#menu .nav').find('ul').find('a').removeClass('responsive-li');
		$('.navbar-collapse').css('margin-top', '-1.5em');
		$('.navbar .nav').css('margin-left', ' 6%');
		$('.navbar .nav > li > a').css('height', '32px');
		$('#navQuickSearch').attr('style', null);
	}
}