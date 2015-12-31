/**
 * Set of general utilities functions used in both the front and back end.
 * Also a set of initialisation done on page load to provide additional
 * services based on particular HTML constructs.
 *
 * !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
 *
 * Note that some libraries are not loaded in the admin (e.g. BS) so we
 * have to check if the functions exists before calling them.
 *
 * e.g.
 *
 * if ($.fn.tooltip) {
 *      $('[data-toggle="tooltip"]').tooltip();
 * }
 *
 * !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
 */


/**
 * dputils namespace
 *
 * General purpose utilities functions.
 *
 * Call them with the dputil. namespace prefix.
 *
 */
(function($) {
    $(function() {
        window.dputils = {
        
            entityMap: {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': '&quot;',
                "'": '&#39;',
                "/": '&#x2F;'
            },
            
            escapeHtml: function(string) {
                return String(string).replace(/[&<>"'\/]/g, function (s) {
                    return window.dputils.entityMap[s];
                });
            },

            /*
             * Sets a cookie
             */
            setCookie: function(c_name,value,exdays) {
                var exdate=new Date();
                exdate.setDate(exdate.getDate() + exdays);
                var c_value=escape(value) + ((exdays==null) ? "" : "; expires="+exdate.toUTCString());
                document.cookie=c_name + "=" + c_value;
            },

            // get a cookie
            // see https://docs.djangoproject.com/en/1.7/ref/contrib/csrf/#ajax
            getCookie: function(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
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
            },

            /*
             * Update the browser address bar with the given URL.
             *
             * Some browser don't support updating the @ bar.
             * In this case, if address_bar_must_change is true then
             * we force the change by doing a standard loading of page.
             * If address_bar_must_change is false, this loading will
             * never occur.
             *
             * If add_to_history is true, the previous address is kept
             * in the history otherwise the new one replaces it.
             *
             * address_bar_must_change = false by default.
             * add_to_history = false by default
             */
            update_address_bar: function(url, address_bar_must_change, add_to_history) {
                if (window.history && window.history.replaceState) {
                    if (add_to_history) {
                        window.history.pushState({ url: '', id: url, label: '' }, null, url);
                    } else {
                        window.history.replaceState(null, null, url);
                    }
                } else {
                    // The browser does not support replaceState (e.g. IE 9),
                    // we just load the page.
                    if (address_bar_must_change) {
                        window.location.href = url;
                    }
                }
            },

            /*
             * Returns the value of a parameter from the query string
             */
            get_query_string_param: function(name) {
                name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
                var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
                    results = regex.exec(location.search);
                return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
            },

            /*
             * Returns the url without the qury string and fragment parts
             */
            get_page_url: function(url) {
                var ret = url;
                ret = ret.replace(/\?.*$/gi, '');
                ret = ret.replace(/#.*$/gi, '');
                ret = ret.replace(/\/$/gi, '');
                ret += '/';
                return ret;
            },

            /*
             * first authenticate then call the callback
             * callback(google_api_client)
            */
            gapi_call: function(callback) {
                //      var clientId = '540110892086-927kglgctu9s6lbv0aa4k3b80s1j9pmr.apps.googleusercontent.com';
                //      var apiKey = 'AIzaSyATws00qmNrMh9LTfLy_VUOhcA2OjYj8Ps';
                //      var scopes = 'https://www.googleapis.com/auth/plus.me';
                //var clientId = '148045849681-nacb9abh96ti4omlm0ldjk0spju0pc22.apps.googleusercontent.com';
                //var apiKey = 'AIzaSyCBfvqrlpUmHFJBlTIIISHrM8AUmqe2xHs';
                var clientId = '5476717076-8g5hi8hum8g48180bkbslf9u2ov3mnmj.apps.googleusercontent.com';
                var apiKey = 'AIzaSyBPAzXEowbmq1oQbp65HIOBm_8ntfAFAaE';
                var scopes = 'https://www.googleapis.com/auth/plus.me';

                // TODO: Where does gapi come from?
                gapi.client.setApiKey(apiKey);

                gapi.auth.authorize({client_id: clientId, scope: scopes, immediate: true}, function() { callback(gapi.client) });
            },

            /* call google shortener api
             *  callback(short_url)
            */
            gapi_shorten_url: function(long_url, callback) {
                dputils.gapi_call(function(google_api_client) {

                    google_api_client.load('urlshortener', 'v1', function() {

                        var request = google_api_client.urlshortener.url.insert({
                            'resource': {
                                'longUrl': long_url
                            }
                        });

                        var resp = request.execute(function(resp) {
                            if (resp.error) {
                                throw new Error('Got error in requesting short url');
                            } else {
                                callback(resp.id);
                            }
                        });
                    });
                });
            },
            
            /*
                Returns the height $element should have to fill the remaining
                space in the viewport.
            */
            get_elastic_height: function($element, min, margin) {
                var height = 0;
                
                // This is a hack for OL - we force 100% height when it is in
                // full screen mode. See zoom view of images on the faceted search.
                if ($element.find('.ol-full-screen-true').length > 0) {
                    return '100%';
                }
                
                min = min || 0;
                margin = margin || 0;
                
                var window_height = $(window).height() - margin;
                height = window_height - $element.offset().top + $(document).scrollTop();
                height = (height <= min) ? min : height;
                height = (height > window_height) ? window_height : height;
                
                return height;
            },
            
            /*
                Make $target height elastic. It will take the rest of the
                viewport space. This is automatically updated when the user
                scrolls or change the viewport size.
                
                $callback is called each time the height is updated.
            */
            elastic_element: function($target, callback, min, margin) {
                var on_resize = function() {
                    $target.css('height', dputils.get_elastic_height($target, min, margin));
                    callback();
                };
                $(window).on('resize scroll', function() {on_resize();});
                on_resize();
            },

            /* Set up Open layer on a DOM element
                options = {
                    target *:
                        JQuery element to convert to Open Layer,
                    image_height *: ,
                    image_width *: ,
                    image_url *: ,
                    zoom:
                        initial zoom level (e.g. 1),
                    (zoom_levels:)
                    load_tile_callback:
                        a callback to keep track of the tile loading
                    can_rotate:
                        true,
                    can_fullscreen:
                        true,
                        
                    version:
                        2|3
                    max_resolution (version 2)
                    event_listeners (version 2)
                }
            */
            add_open_layer: function(options) {
                options.version = options.version || 3;
                options.zoom = options.zoom || 0;
                
                //options.zoom_levels = options.zoom_levels || window.digipal_settings.ANNOTATOR_ZOOM_LEVELS;
                if (!options.max_resolution) {
                    // calculate max resolution so the image maximizes the viewport
                    var div_dims = [700, 700];
                    if (options.$target && $(options.$target).length) {
                        div_dims = [$(options.$target).width(), $(options.$target).height()];
                    }
                    options.max_resolution = options.image_width / div_dims[0];
                    if ((options.max_resolution * options.image_height) > div_dims[1]) {
                        options.max_resolution = options.image_height / div_dims[1];
                    }
                }
                // don't go lower than the 1 resolution to avoid pixelation
                //options.min_resolution = options.min_resolution || 1;
                options.resolutions = [];
                var new_res = options.max_resolution;
                var zoom_factor = window.digipal_settings.ANNOTATOR_ZOOM_FACTOR;
                while (true) {
                    options.resolutions.push(new_res);
                    if (new_res < 1) break;
                    new_res /= zoom_factor;
                }
                // add one resolution under the 1
                if (new_res > 0.5) {
                    options.resolutions.push((new_res / zoom_factor));
                }
                
                var function_name = 'add_open_layer' + ((options.version < 3) ? '2' : '3');
                var ret = window.dputils[function_name](options);
                return ret;
            },

            add_open_layer2: function(options) {
            
                var $target = $(options.$target);

                var maxExtent = new window.OpenLayers.Bounds(0, 0, options.image_width, options.image_height);
            
                // creates a new OpenLayers map
                var map_options = {
                    maxExtent: maxExtent,
                    projection: 'EPSG:3785',
                    units: 'm',
                    //units: 'pixels',
                    //resolutions: options.resolutions,
                    //maxResolution: options.resolutions[0],
                    //minResolution: options.resolutions[options.resolutions.length - 1],
                    maxResolution: options.max_resolution,
                    //numZoomLevels: options.resolutions.length,
                    numZoomLevels: window.digipal_settings.ANNOTATOR_ZOOM_LEVELS,
                    //numZoomLevels: options.zoom_levels,
                };
                
                if (options.event_listeners) {
                    map_options.eventListeners = options.event_listeners;
                }
                
                options.map = new window.OpenLayers.Map($target.attr('id'), map_options);
                
                return options.map;
            },
            
            add_open_layer3: function(options) {
                var ol = window.ol;
                
                var $target = $(options.$target);
                
                // Maps always need a projection, but Zoomify layers are not geo-referenced, and
                // are only measured in pixels.  So, we create a fake projection that the map
                // can use to properly display the layer.
                var proj = new ol.proj.Projection({
                  code: 'ZOOMIFY',
                  units: 'pixels',
                  extent: [0, 0, options.image_width, options.image_height]
                });
                
                var source = new ol.source.Zoomify({
                    url: options.image_url,
                    size: [options.image_width, options.image_height],
                    crossOrigin: 'anonymous'
                });
                
                if (options.load_tile_callback) {
                    options.load_tile_callback('reset');
                
                    source.on('tileloadstart', function(event) {
                      options.load_tile_callback(1);
                    });
                    source.on('tileloadend', function(event) {
                      options.load_tile_callback(-1);
                    });
                    source.on('tileloaderror', function(event) {
                      options.load_tile_callback(-1, true);
                    });
                }
            
                var tileLayer = new ol.layer.Tile({
                    source: source
                });
                
                var view_options = {
                    projection: proj,
                    center: [options.image_width / 2, - options.image_height / 2],
                    zoom: options.zoom,
                    //maxResolution: options.max_resolution,
                    //minResolution: options.min_resolution,
                    //zoomFactor: options.zoom_factor,
                    resolutions: options.resolutions,
                    //minZoom: 0,
                    //maxZoom: options.zoom_levels - 1,
                    // constrain the center: center cannot be set outside
                    // this extent
                    extent: [0, -options.image_height, options.image_width, 0]
                };
                
                var map_options = {
                    layers: [tileLayer],
                    // overview is not great, see EXON-28
                    // controls: ol.control.defaults().extend([
                    //   new ol.control.OverviewMap({layers: [tileLayer]})
                    // ]),
                    target: $target[0],
                    view: new ol.View(view_options)
                };
                
                if (options.can_fullscreen) {
                    map_options.controls = ol.control.defaults().extend([
                        new ol.control.FullScreen()
                    ]);
                }
            
                if (options.can_rotate) {
                    map_options.interactions = ol.interaction.defaults().extend([
                        new ol.interaction.DragRotate()
                    ]);
                }
            
                options.map = new ol.Map(map_options);
                
                return options.map;
            }

        };
    });
})(jQuery);

/**
 * Initialisation after any page load.
 */
(function($) {
    $(function() {

        /*
         *  Update the URL in the address bar when the link is clicked.
         *  Default Bootstrap behaviour is preserved.
         *  See JIRA 155, 140
         *  Usage:
         *      <a data-target="#T" href="URL">my link</a>
         *      <div id="T">
         *
         *  When the link is clicked, the address bar will be updated
         *  with URL.
         *
         *  Note that some browsers don't support changing the
         *  address bar. So if it fails the bar remains unchanged.
         *  Add attribute data-address-bar="1" to force the change
         *  even if the browser does not support it. This will cause
         *  a page load.
        */
        $('a[data-target][href]').on('click', function(e) {
            var href = $(this).attr('href');
            if (href.search(/^(#|\.)/) == -1) {
                dputils.update_address_bar(href, $(this).data('update-address-bar'));
                e.preventDefault();
            }
        });

        // Follow the link in tab if it has no data-target.
        // Used to load the slow searches tabs on the search page.
        $('a[data-toggle=tab][href]:not([data-target])').on('click', function(e) {
            var href = $(this).attr('href');
            if (href.search(/^#/) == -1) {
                window.location.href = $(this).attr('href');
            }
        });

        // Any <a data-alt-label="Hide">Show</a>
        // will have 'Show' replaced by 'Hide' each time the element is clicked
        $('a[data-alt-label]').on('click', function(e){
            var label = $(this).html();
            $(this).html($(this).data('alt-label'));
            $(this).data('alt-label', label);
            e.preventDefault();
        });

        // enable bootstrap tooltip on elements with data-toggle="tooltip" attribute
        if ($.fn.tooltip) {
            $('[data-toggle="tooltip"]').tooltip();
        }

        // convert HTML select to chosen drop downs
        if ($.fn.chosen) {
            $('.use-chosen select, select.use-chosen').chosen();
        }

        // carousel rotation
        if ($.fn.carousel) {
            $('.carousel').carousel({
                interval: 8000
            });
        }

        // fancybox
        if ($.fn.fancybox) {
            // add a <a class="fancybox"> around the images which have no link around them.
            $(".mddoc img").each(function () {
                var $img = $(this);
                if ($img.parent().prop('tagName') != 'A') {
                    $img.wrap('<a class="fancybox" rel="group" href="'+$img.attr('src')+'" ></a>');
                }
            });
            // enable fancybox on the .fancybox elements
            $(".fancybox").fancybox();
        }
        
    });
})(jQuery);

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
(function($) {
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
                $('body').append('<div id="img-expand-div" style="background-color:white;line-height:0px;display:none;position:fixed;top:0px;padding:20px;margin:10px;border:1px solid grey; box-shadow: 5px 5px 5px #888888; z-index: 10000;"><img style="border:1px solid grey;" src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="/><p>Loading the image, please wait...</p></div>');
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
                //expanded_div.css('left', '' + (expanded_img_x[right_or_left]) + 'px');

                // GN 2015/12/10: patch: if image to the right of thumb, we clip it to the window right edge
                expanded_div.css(right_or_left ? 'right' : 'left', '0');

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
})(jQuery);


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
(function($) {
    $(function() {
        function load_lazy_images() {
            // load lazy images which are now visible in the browser window.
            $('img[data-lazy-img-src]').each(function() {
                var jq_img = $(this);
                if (is_element_visible(jq_img)) {
                    /*
                    jq_img.load(function() {
                        $(this).removeAttr('width');
                        $(this).removeAttr('height');
                    });
                    */
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
        $('a[data-toggle="tab"], a[data-toggle="pill"]').on('shown.bs.tab', load_lazy_images);

        load_lazy_images();

        document.load_lazy_images = load_lazy_images;
    });
})(jQuery);

