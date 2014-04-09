/**
 * Every element that match the css selector '.imageDatabase a.droppable_image'
 * will become draggable to a basket. The element must have an data-id attribute
 * which contains the ID of the digipal image record to add to the basket.
 *
 * Requires a <div id="basket_collector"> that will serves as a drop target
 * which is made visible as soon as we start dragging an item.
 *
 * Dependency: add_to_lightbox.js
 */
$(document).ready(function() {
	//$('select').chosen();

	var basket_collector = $('#basket_collector');
	basket_collector.droppable({
		accept: "a.droppable_image",
		hoverClass: "ui-state-active",

		drop: function(event, ui) {
			var element = $(ui.helper[0]);
			var type = element.data('type');
			var s;
			if (add_to_lightbox(element, type, element.data('id'), false)) {

				s = '<p>Image added to Collection!</p>';
				s += '<p><img src="/static/digipal/images/success-icon.png" /></p>';
				$(this).html(s);

			}

			setTimeout(function() {
				s = '<p>Drop Image here</p>';
				basket_collector.html(s);

			}, 3000);

		},

		out: function() {
			$(this).css('background', '#fff');
		},

		over: function() {
			$(this).css('background', 'rgba(255, 255, 255, 0.8)');
		}
	});

	var switcher = $('#toggle-annotations-mode');
	var images = $('a.droppable_image');
	images.draggable({
		containment: false,
		cursor: 'move',
		revert: true,
		scroll: false,
		zIndex: 1001,
		start: function(event) {
			if (switcher.length && switcher.bootstrapSwitch('state')) {
				$('html, body').css('cursor', 'initial');
				return false;
			}
			basket_collector.animate({
				bottom: '0'
			}, 350);

			$(event.target).find('.drag_caption').hide();
			//event.stopPropagation();
		},

		stop: function(event) {
			setTimeout(function() {
				basket_collector.animate({
					bottom: '-28%'
				}, 350);
			}, 500);

			$(event.target).find('.drag_caption').show();
			//event.stopPropagation();
		}
	});


	$('.imageDatabase').on('mouseenter', function(event) {
		$(this).find('.drag_caption').fadeIn(250);
		event.stopPropagation();
		return false;
	}).on('mouseleave', function(event) {
		$(this).find('.drag_caption').fadeOut(250);
		event.stopPropagation();
		return false;
	});

});