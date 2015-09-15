function Dialog() {

    var open = false;
    var summary = true;
    var element_cache = false;
    var temp = {};
    var defaultOptions = {
        'container': 'body',
        'draggable': true,
        'summary': true,
    };

    var init = function(image_id, options, callback) {

        $.extend(defaultOptions, options);

        create_dialog(image_id, function(selector) {

            var d = {
                'hide': hide,
                'update': update,
                'show': show,
                'selector': selector,
                'events': events,
                'edit_letter': edit_letter,
                'open': open,
                'set_label': set_label,
                'events_postLoading': events_postLoading
            };

            if (callback) {
                callback(d);
            }

        });

    };

    var create_dialog = function(image_id, callback) {
        var modal_features;
        var ABSOLUTE_URL = '/digipal/page/dialog/';

        if (!$('.myModal#modal_features').length) {
            var modal_element = $("<div class='myModal' id='modal_features'>");
            $(defaultOptions.container).append(modal_element);
        }

        modal_features = $('.myModal');
        temp.image_id = image_id;

        var url;

        if (!element_cache) {
            url = ABSOLUTE_URL + image_id + '/';
            $.ajax({
                type: 'GET',
                url: url,
                success: function(data) {
                    if (!element_cache) {
                        modal_features.html(data);
                        modal_features.append("<div id='summary'>");
                        element_cache = data;
                    }
                    selector = modal_features;
                    if (callback) {
                        callback(selector);
                    }
                    events(selector);
                }

            });

        } else {
            modal_features.html(element_cache);
            selector = modal_features;
            if (!$('#summary').length) {
                selector.append("<div id='summary'>");
            }
            if (callback) {
                callback(selector);
            }
            events(selector);
        }

    };

    var events = function(selector) {
        var show_summary_button = $('#show_summary');
        var summary_element = $('#summary');
        if (defaultOptions.summary) {
            summary_element.show();
            summary = true;
            show_summary_button.addClass('active');
            show_summary_button.unbind().click(function() {
                show_summary(show_summary_button, summary_element);
            });
        } else {
            summary_element.remove();
            summary = false;
            show_summary_button.remove();
        }

        /* updates dialog when changing allograph */

        var allograph_form = selector.find('.allograph_form');
        allograph_form.unbind('change').on('change', function() {
            update_onChange($(this).val(), selector);
        });


        selector.find('.close').click(function() {
            hide();
        });

        /* making box draggable */
        if (defaultOptions.draggable) {
            selector.draggable({
                handle: '.modal_header'
            });
        }

        var maximized = false;
        var maximize_icon = $('#maximize');
        var myModal = selector;

        maximize_icon.on('click', function() {

            if (summary) {
                summary_element.hide();
            }

            if (!maximized) {
                myModal.animate({
                    'position': 'fixed',
                    'top': "0px",
                    'left': '59.5%',
                    "width": '40%',
                    "height": '100%'
                }, 400, function() {

                    if (summary) {
                        summary_element.show();
                        summary_element.css('bottom', '95%');
                    }

                    myModal.find('.modal-body').css("max-height", "100%");
                    maximize_icon.attr('title', 'Minimize box').removeClass('icon-resize-full').addClass('icon-resize-small');

                });

                maximized = true;
                $('.row-min-admin').css('width', '60%');

            } else {

                if (summary) {
                    summary_element.show();
                }

                myModal.animate({
                    'position': 'fixed',
                    'left': "55%",
                    'top': "15%",
                    'right': '',
                    "width": '30%',
                    "height": '60%'
                }, 400, function() {

                    if (summary) {
                        summary_element.show();
                        summary_element.css('bottom', '90%');
                    }

                    myModal.find('.modal-body').css("max-height", "");
                    maximize_icon.attr('title', 'Maximize box').removeClass('icon-resize-small').addClass('icon-resize-full');

                }).draggable();

                maximized = false;
                $('.row-min-admin').css('width', '70%');
            }

        });

        selector.find("[data-toggle='tooltip']").tooltip();

        $('select').chosen().trigger('liszt:updated');
    };

    var events_postLoading = function(selector) {
        selector.find('.check_all').click(function(event) {
            var checkboxes = $(this).parent().parent().next().find('input[type=checkbox]');
            checkboxes.attr('checked', true);
            event.stopPropagation();
        });

        selector.find('.uncheck_all').click(function(event) {
            var checkboxes = $(this).parent().parent().next().find('input[type=checkbox]');
            checkboxes.attr('checked', false);
            event.stopPropagation();
        });

        selector.find('.component_labels').click(function() {
            var div = $("#" + $(this).data('id'));
            if (div.data('hidden') === false) {
                div.slideUp().data('hidden', true);
                $(this).next('.checkboxes_div').hide();
                $(this).find('.arrow_component').removeClass('fa-angle-double-up').addClass('fa-angle-double-down');
            } else {
                div.slideDown().data('hidden', false);
                $(this).next('.checkboxes_div').show();
                $(this).find('.arrow_component').removeClass('fa-angle-double-down').addClass('fa-angle-double-up');
            }
        });

        var set_by_default = selector.find('.set_by_default');
        set_by_default.on('click', function(event) {
            var component_id = $(this).data('component');
            var allograph = selector.find('.allograph_form').val();
            check_features_by_default(component_id, allograph, editGraphsSearch.cache);
            event.stopPropagation();
        });

        $('[data-tooltip]').tooltip();
    };

    var show_summary = function(button, summary_element) {

        if (summary) {

            summary_element.animate({
                'right': 0,
                'opacity': 0,
            }, 350, function() {
                $(this).css({
                    'display': 'none'
                });
            });

            summary = false;
            button.removeClass('active');

        } else {

            summary_element.css({
                'display': 'block'
            }).animate({
                'right': "40.3%",
                'opacity': 1
            }, 350);

            summary = true;
            button.addClass('active');

        }
    };

    var hide = function() {
        selector.hide();
        open = false;
    };

    var show = function() {
        selector.show();
        open = true;
    };

    var set_label = function(label_value) {
        var label = $('.myModalLabel .label-modal-value');
        label.html(label_value);
    };

    var update_onChange = function(allograph, selector) {
        var ABSOLUTE_URL = '/digipal/api/old/';
        var PREFIX = 'search_';
        var content_type = 'allograph';
        var url = ABSOLUTE_URL + content_type + '/' + allograph;
        var request = $.getJSON(url);

        request.done(function(allographs) {
            update(PREFIX, allographs[0], [], function(s) {
                selector.find('#features_container').html(s);
                events_postLoading(selector);
            });
        });

    };

    var edit_letter = {

        init: function(graph) {
            var editor_space = $('#image-editor-space');
            var img = $('[data-graph="' + graph + '"]').find('img');
            this.img = img.clone();
            this.temp = {};
            editor_space.html(this.img);
            this.url = this.img.attr('src');
            this.parameters = this.get_parameters();
            this.events();
        },

        getParameter: function(paramName, searchString) {
            var i, val, params = searchString.split("&");
            var parameters = [];
            for (i = 0; i < params.length; i++) {
                val = params[i].split("=");
                if (val[0] == paramName) {
                    parameters.push(unescape(val[1]));
                }
            }
            return parameters;
        },

        resize: function(side, value) {
            $('#editor-space-image').fadeIn();
            var temp = edit_letter.temp;
            var url = edit_letter.url;
            var old_url = edit_letter.parameters.RGN;
            var newRGN = edit_letter.parameters.RGN.split(',');

            if (side == 'top') {
                //par = this.parameters.RGN[1];
                newRGN[1] = value;
            } else if (side == 'left') {
                //par = this.parameters.RGN[0];
                newRGN[0] = value;
            } else if (side == 'width') {
                //par = this.parameters.RGN[3];
                newRGN[2] = value;
            } else {
                //par = this.parameters.RGN[2];
                newRGN[3] = value;
            }

            url = url.replace('RGN=' + old_url, 'RGN=' + newRGN.toString());
            edit_letter.url = url;

            edit_letter.img.attr('src', url).on('load', function() {
                $('#editor-space-image').fadeOut();
            });

            edit_letter.parameters.RGN = newRGN.toString();
        },

        makeBounds: function(RGN) {
            var W = annotator.dimensions[0];
            var H = annotator.dimensions[1];
            var left = RGN[0] * W;
            var top = H - (RGN[1] * H);
            var width = (RGN[2] * W);
            var height = (RGN[3] * H);
            //annotator.selectedFeature.move(p);
        },

        events: function() {
            var resize = this.resize;
            var temp = this.temp;
            var parameters = this.parameters;

            var resize_up = $('#resize-up');
            var resize_down = $('#resize-down');
            var resize_width = $('#resize-right');
            var resize_left = $('#resize-left');

            var move_up = $('#move-up');
            var move_down = $('#move-down');
            var move_right = $('#move-right');
            var move_left = $('#move-left');

            var edit_letter = self;
            var value = 0.005;

            /*
                resize functions
            */
            resize_up.on('click', function() {

                if (!temp['height']) {
                    temp['height'] = parseFloat(parameters.height);
                }

                temp['height'] += value;

                resize('height', temp['height']);
            });

            resize_down.on('click', function() {

                if (!temp['height']) {
                    temp['height'] = parseFloat(parameters.height);
                }

                temp['height'] -= value;

                resize('height', temp['height']);
            });

            resize_left.on('click', function() {
                if (!temp['width']) {
                    temp['width'] = parseFloat(parameters.width);
                }

                temp['width'] -= value;

                resize('width', temp['width']);
            });

            resize_width.on('click', function() {
                if (!temp['width']) {
                    temp['width'] = parseFloat(parameters.width);
                }

                temp['width'] += value;

                resize('width', temp['width']);
            });

            /*
                end resize functions
            */

            /*
                move functions
            */


            move_up.on('click', function() {
                if (!temp['top']) {
                    temp['top'] = parseFloat(parameters.top);
                }

                temp['top'] -= value;

                resize('top', temp['top']);
            });

            move_down.on('click', function() {
                if (!temp['top']) {
                    temp['top'] = parseFloat(parameters.top);
                }

                temp['top'] += value;

                resize('top', temp['top']);
            });

            move_left.on('click', function() {
                if (!temp['left']) {
                    temp['left'] = parseFloat(parameters.left);
                }

                temp['left'] -= value;

                resize('left', temp['left']);
            });

            move_right.on('click', function() {
                if (!temp['left']) {
                    temp['left'] = parseFloat(parameters.left);
                }

                temp['left'] += value;

                resize('left', temp['left']);
            });

            /*
                end move functions
            */
        },

        get_parameters: function() {
            var WID = this.getParameter('WID', this.url);
            var RGN = this.getParameter('RGN', this.url).toString().split('&')[0];
            var coords = RGN.split(',');
            var left = coords[0];
            var top = coords[1];
            var height = coords[2];
            var width = coords[3];

            return {
                'WID': WID,
                'RGN': RGN,
                'left': left,
                'top': top,
                'height': height,
                'width': width
            };

        }

    };

    var update = update_dialog;

    return init;
}
