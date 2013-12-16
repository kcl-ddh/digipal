/*
 * Expand thumbnails on mouse overs.
 * 
 * Usage:
 * 
 *  Simply add an 'img-expand' class to the html 'img' element that contains a 
 *  thumbnail requested from IIPImage.
 *  
 *  	<img href="http://..." class="img-expand" />
 *  
 *  This script will display an expanded version of the image on one side of 
 *  the thumbnail when the mouse moves over it.
 *  
 */
$(function() {
	
	function show_expanded_img(event, img, hide) {
		var thumbnail_img = $(img);
		
		// get or create the div that contains the image
		var expanded_div = $('#img-expand-div');
		// difference between size of the div and size of the contained image
		// 2 * ((margin + padding + border) for image and div) 
		var total_padding = 62;
		if (!expanded_div.size()) {
			// we create a permanent div 
			$('body').append('<div id="img-expand-div" style="background-color:white;line-height:0px;display:none;position:fixed;top:0px;padding:20px;margin:10px;border:1px solid grey; box-shadow: 5px 5px 5px #888888;"><img style="border:1px solid grey;" src="img-expand-div"/><p>Loading the image, please wait...</p></div>');
			expanded_div = $('#img-expand-div');
			var expanded_img = expanded_div.children('img');
			expanded_img.load(function () { expanded_img.show(); expanded_div.children('p').hide(); });
		}
		
		if (!hide) {
			var expanded_img = expanded_div.children('img');
			expanded_img.hide();
			expanded_div.children('p').show();
			
			var expanded_img_x = [0, (thumbnail_img.offset()).left + thumbnail_img.width() - $(document).scrollLeft()];
			
			// Compute how much of the image we can show on screen.
			// We want to fill as much as possible of the space on the right of the cursor.
			// Constraints: we must maintain the aspect ratio and we want to show the whole image in the browser window.
			
			// Get the aspect ratio
			var img_ratio = thumbnail_img.width() / thumbnail_img.height();
			var expanded_max_height = $(window).height() - total_padding;
			
			var max_expanded_width = [(thumbnail_img.offset()).left - total_padding, $(window).width() - expanded_img_x[1] - total_padding]

			// 0 if expanded image appears on the left, 1 if it appears on the right.
			// Choose the widest side. 
			var right_or_left = (max_expanded_width[1] > max_expanded_width[0]) ? 1 : 0;
			
			// Find out which dimensions to request from IIP image
			var expanded_img_ratio = max_expanded_width[right_or_left] / expanded_max_height;
			var dimension_request = '';
			if (img_ratio < expanded_img_ratio) {
				// use the full height
				dimension_request = '&HEI=' + Math.round(expanded_max_height);
			} else {
				// use the full width
				dimension_request = '&WID=' + Math.round(max_expanded_width[right_or_left]);
			}
			dimension_request += '&QLT=100&CVT=JPG';
			
			// reposition the div to the right of the cursor
			expanded_div.css('left', '' + (expanded_img_x[right_or_left]) + 'px');

			// update the image in the div
			var img_url = thumbnail_img.attr('src').replace(/^([^?]+)\?.*(FIF=[^&]+).*$/i, '$1?$2');
			// Trick: need to clear the src attribute first. This solves the problem were the user
			// moves the mouse over the same thumbnail again. Browsers won't trigger a load event
			// and the img element will therefore not be made visible.
			expanded_img.attr('src', '');
			expanded_img.attr('src', img_url + dimension_request);
		}
		
		// show or hide the div
		expanded_div.toggle(!hide);
	}
	
	$('.img-expand').mouseenter(function(event){ show_expanded_img(event, this, false); });
	$('.img-expand').mouseleave(function(event){ show_expanded_img(event, this, true); });
});
