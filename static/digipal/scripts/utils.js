// dputils namespace
// This is for general functions used on multiple pages

(function($) {
    window.dputils = {
        
        /*
         * Sets a cookie
         */
        setCookie: function(c_name,value,exdays) {
            var exdate=new Date();
            exdate.setDate(exdate.getDate() + exdays);
            var c_value=escape(value) + ((exdays==null) ? "" : "; expires="+exdate.toUTCString());
            document.cookie=c_name + "=" + c_value;
        }
    }
})(jQuery);

$(function() {
    
    /**
     * Save the last selected tab in a cookie
     */    
    $('#myTab a').click(
        function (e) {
          e.preventDefault();
          $(this).tab('show');
          dputils.setCookie('view', this.innerHTML, '-1');
        }
    );
    
    // enable bootstrap tooltip on elements with data-toggle attribute
    $('[data-toggle="tooltip"]').tooltip();
    
    // convert HTML select to chosen drop downs
    $('.use-chosen select, select.use-chosen').chosen();
});

/**
 * Expand thumbnails on mouse overs.
 * 
 * Usage:
 * 
 *  Simply add an 'img-expand' class to the html 'img' element that contains a 
 *  thumbnail requested from IIPImage.
 *  
 *      <img href="http://..." class="img-expand" />
 *  
 *  This script will display an expanded version of the image on one side of 
 *  the thumbnail when the mouse moves over it.
 *  
 */
$(function() {
    
    function show_expanded_img(event, img, hide) {
        var thumbnail_img = $(img);
        
        // abort if the src is not a IIP image
        if (thumbnail_img.attr('src').indexOf('FIF=') == -1) {
            return;
        }
        
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


/**
 * Lazy-loading images.
 * 
 * Usage:
 *     <img src="dummyimg.gif" data-lazy-img-src="realpath.gif" />
 * 
 *  Just add the image URL in the data-lazy-img-src attribute of the img element.
 *  dummyimg.gif is a default image to display, e.g. 1 white pixel or a spinner.
 *  
 * The image will be automatically loaded when it is visible in
 * the browser.
 * 
 */
$(function() {
    function load_lazy_images() {
        // load lazy images which are now visible in the browser window.
        $('img[data-lazy-img-src]').each(function() {
            var jq_img = $(this);
            if (is_element_visible(jq_img)) {
                jq_img.load(function() {
                    $(this).removeAttr('width');
                    $(this).removeAttr('height');
                });
                jq_img.attr('src', jq_img.attr('data-lazy-img-src'));
                jq_img.removeAttr('data-lazy-img-src');
            }
        });
    }
    
    function is_element_visible(jq_element) {
        // Returns true if jq_element is currently on the visible part of 
        // the html page.
        
        // element must not be hidden
        if (!jq_element.is(":visible")) return false;        
        // element is invisible if its bottom is above the top of the window
        if ((jq_element.offset().top + jq_element.height()) < $(window).scrollTop()) return false;
        // or its top below the bottom of the window
        if (jq_element.offset().top > ($(window).scrollTop() + $(window).height())) return false;
        return true;
    }
    
    $(window).scroll(load_lazy_images);
    $(window).resize(load_lazy_images);
    /* try to load when a boostrap tab becomes visible */
    $('a[data-toggle="tab"]').on('shown', load_lazy_images);
    
    load_lazy_images();
})

