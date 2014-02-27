var dialog = {
    open: false,
    summary: true,
    self: this,
    temp: {},

    init: function(image_id, options, callback) {

        this.defaultOptions = {
            'container': 'body',
            'draggable': true,
            'summary': true,
        };

        $.extend(this.defaultOptions, options);

        this.create_dialog(image_id, callback);
    },

    create_dialog: function(image_id, callback) {
        var modal_features;
        var ABSOLUTE_URL = '/digipal/page/dialog/';
        var show_summary_button = $('#show_summary');
        var summary = $('#summary');

        if (!$('#modal_features').length) {
            modal_features = $("<div class='myModal' id='modal_features'>");
            $(this.defaultOptions.container).append(modal_features);
        } else {
            modal_features = $('#modal_features');
        }

        if (self.dialog.defaultOptions.summary) {
            summary.show();
            self.dialog.summary = true;
            show_summary_button.addClass('active');
        } else {
            summary.hide();
            self.dialog.summary = false;
            show_summary_button.removeClass('active');
        }

        self.dialog.selector = modal_features;
        self.dialog.temp.image_id = image_id;

        var url;

        if (!self.dialog.cache) {
            url = ABSOLUTE_URL + image_id + '/';
            $.ajax({
                type: 'GET',
                url: url,
                success: function(data) {
                    if (!self.dialog.cache) {
                        modal_features.html(data);
                        self.dialog.cache = data;
                    }
                    if (callback) {
                        callback();
                    }
                },
                complete: function() {
                    self.dialog.events();
                }
            });
        } else {
            modal_features.html(self.dialog.cache);
            if (callback) {
                callback();
            }
        }

    },

    events: function() {
        var show_summary_button = $('#show_summary');
        var summary = $('#summary');

        show_summary_button.unbind().click(function() {
            self.dialog.show_summary(show_summary_button, summary);
        });

        /* updates dialog when changing allograph */
        var allograph_form = self.dialog.selector.find('.allograph_form');
        allograph_form.on('change', function() {
            self.dialog.update_onChange($(this).val());
        });

        self.dialog.selector.find('.close').click(function() {
            self.dialog.hide();
        });

        /* making box draggable */
        if (this.defaultOptions.draggable) {
            self.dialog.selector.draggable();
        }

        var maximized = false;
        var maximize_icon = $('#maximize');
        var myModal = self.dialog.selector;
        maximize_icon.click(function() {

            if (self.dialog.summary) {
                summary.hide();
            }

            if (!maximized) {
                myModal.animate({
                    'position': 'fixed',
                    'top': "0px",
                    'left': '59.5%',
                    "width": '40%',
                    "height": '100%'
                }, 400, function() {

                    if (self.dialog.summary) {
                        summary.show();
                    }

                    myModal.find('.modal-body').css("max-height", "100%");
                    maximize_icon.attr('title', 'Minimize box').removeClass('icon-resize-full').addClass('icon-resize-small');

                });
                maximized = true;
                $('.row-min-admin').css('width', '60%');
            } else {
                if (self.dialog.summary) {
                    summary.show();
                }
                myModal.animate({
                    'position': 'fixed',
                    'left': "55%",
                    'top': "15%",
                    'right': '',
                    "width": '30%',
                    "height": '60%'
                }, 400, function() {
                    if (self.dialog.summary) {
                        summary.show();
                    }
                    myModal.find('.modal-body').css("max-height", "");
                    maximize_icon.attr('title', 'Maximize box').removeClass('icon-resize-small').addClass('icon-resize-full');
                }).draggable();
                maximized = false;
                $('.row-min-admin').css('width', '70%');
            }

        });

        self.dialog.selector.find("[data-toggle='tooltip']").tooltip();

        $('select').chosen().trigger('liszt:updated');
    },

    events_postLoading: function() {
        self.dialog.selector.find('.check_all').click(function(event) {
            var checkboxes = $(this).parent().parent().next().find('input[type=checkbox]');
            checkboxes.attr('checked', true);
            event.stopPropagation();
        });

        self.dialog.selector.find('.uncheck_all').click(function(event) {
            var checkboxes = $(this).parent().parent().next().find('input[type=checkbox]');
            checkboxes.attr('checked', false);
            event.stopPropagation();
        });

        self.dialog.selector.find('.component_labels').click(function() {
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
    },

    show_summary: function(button, summary) {

        if (self.dialog.summary) {

            summary.animate({
                'right': 0,
                'opacity': 0,
            }, 350, function() {
                $(this).css({
                    'display': 'none'
                });
            });

            self.dialog.summary = false;
            button.removeClass('active');

        } else {

            summary.css({
                'display': 'block'
            }).animate({
                'right': "40.3%",
                'opacity': 1
            }, 350);

            self.dialog.summary = true;
            button.addClass('active');

        }
    },

    hide: function() {
        self.dialog.selector.fadeOut();
        self.open = false;
    },

    show: function() {
        self.dialog.selector.fadeIn();
        self.open = true;
        self.dialog.events();
    },

    set_label: function(label_value) {
        var label = $('.myModalLabel .label-modal-value');
        label.html(label_value);
    },

    update_onChange: function(allograph) {
        var ABSOLUTE_URL = '/digipal/';
        var PREFIX = 'search_';
        var content_type = 'allograph';
        if (!cache.search("allograph", allograph)) {
            var url = ABSOLUTE_URL + content_type + '/' + allograph;
            var request = $.getJSON(url);

            request.done(function(allographs) {
                self.dialog.update(PREFIX, allographs, function(s) {
                    self.dialog.selector.find('#features_container').html(s);
                    self.dialog.events_postLoading();
                });
                cache.allographs[allograph] = allographs;
            });

        } else {
            var allographs = cache.allographs[allograph];
            self.dialog.update(PREFIX, allographs, function(s) {
                self.dialog.selector.find('#features_container').html(s);
                self.dialog.events_postLoading();
            });
        }
    },

    edit_letter: {
        self: this,
        init: function(graph) {
            var editor_space = $('#image-editor-space');
            var img = $('a[data-graph="' + graph + '"]').find('img');
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
            var temp = self.dialog.edit_letter.temp;
            var url = self.dialog.edit_letter.url;
            var old_url = self.dialog.edit_letter.parameters.RGN;
            var newRGN = self.dialog.edit_letter.parameters.RGN.split(',');
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
            self.dialog.edit_letter.url = url;
            //self.dialog.edit_letter.makeBounds(newRGN);
            self.dialog.edit_letter.img.attr('src', url);
            self.dialog.edit_letter.img.on('load', function() {
                $('#editor-space-image').fadeOut();
            });
            self.dialog.edit_letter.parameters.RGN = newRGN.toString();
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
            var resize_up = $('#resize-up');
            var resize_down = $('#resize-down');
            var resize_width = $('#resize-right');
            var resize_left = $('#resize-left');

            var move_up = $('#move-up');
            var move_down = $('#move-down');
            var move_right = $('#move-right');
            var move_left = $('#move-left');

            var edit_letter = self.dialog.edit_letter;
            var value = 0.005;

            /*
                resize functions
            */
            resize_up.on('click', function() {

                if (!edit_letter.temp['height']) {
                    edit_letter.temp['height'] = parseFloat(edit_letter.parameters.height);
                }

                edit_letter.temp['height'] += value;

                resize('height', edit_letter.temp['height']);
            });

            resize_down.on('click', function() {

                if (!edit_letter.temp['height']) {
                    edit_letter.temp['height'] = parseFloat(edit_letter.parameters.height);
                }

                edit_letter.temp['height'] -= value;

                resize('height', edit_letter.temp['height']);
            });

            resize_left.on('click', function() {
                if (!edit_letter.temp['width']) {
                    edit_letter.temp['width'] = parseFloat(edit_letter.parameters.width);
                }

                edit_letter.temp['width'] -= value;

                resize('width', edit_letter.temp['width']);
            });

            resize_width.on('click', function() {
                if (!edit_letter.temp['width']) {
                    edit_letter.temp['width'] = parseFloat(edit_letter.parameters.width);
                }

                edit_letter.temp['width'] += value;

                resize('width', edit_letter.temp['width']);
            });

            /*
                end resize functions
            */

            /*
                move functions
            */


            move_up.on('click', function() {
                if (!edit_letter.temp['top']) {
                    edit_letter.temp['top'] = parseFloat(edit_letter.parameters.top);
                }

                edit_letter.temp['top'] -= value;

                resize('top', edit_letter.temp['top']);
            });

            move_down.on('click', function() {
                if (!edit_letter.temp['top']) {
                    edit_letter.temp['top'] = parseFloat(edit_letter.parameters.top);
                }

                edit_letter.temp['top'] += value;

                resize('top', edit_letter.temp['top']);
            });

            move_left.on('click', function() {
                if (!edit_letter.temp['left']) {
                    edit_letter.temp['left'] = parseFloat(edit_letter.parameters.left);
                }

                edit_letter.temp['left'] -= value;

                resize('left', edit_letter.temp['left']);
            });

            move_right.on('click', function() {
                if (!edit_letter.temp['left']) {
                    edit_letter.temp['left'] = parseFloat(edit_letter.parameters.left);
                }

                edit_letter.temp['left'] += value;

                resize('left', edit_letter.temp['left']);
            });

            /*
                end move functions
            */
        },

        get_parameters: function() {
            var WID = this.getParameter('WID', self.dialog.edit_letter.url);
            var RGN = this.getParameter('RGN', self.dialog.edit_letter.url).toString().split('&')[0];
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

    },

    update: update_dialog

};