/**
 * Controller for the tool that allows edition of the annotation
 * orientation and shape outside of the OpenLayer environment.
 * 
 * This tool does not support more than one graph at a time. If
 * more than one graph is passed the UI is disabled. This may change
 * in the future.
 * 
 * Usage:
 * 
 * # Instantiate
 * var editor = $(div-selector).annotation_editor().data('annotation_editor');
 * 
 * # (Re)set the id of the graphs to edit
 * editor.set_graphids([100]);
 * 
 * # save the changes to the annotation shape and rotation back to the DB
 * editor.save();
 * 
 * # if you prefer save the information yourself, you can obtain the rotation
 * # using this function.
 * editor.get_rotation();
 * 
 * Implementation notes:
 * 
 * Although the transform could be applied more rapidly on the client side, 
 * this tool will request a new preview from the server after each change. 
 * There are 2 reasons: 
 *      * we don't duplicate the logic and the code for rendering a crop-out
 *      * it is guaranteed that the preview will match exactly what the user 
 *          see on the web pages after saving.
 * 
 */
(function($) {

      $.annotation_editor = function(element, options) {

        var defaults = {
            api_root: '/digipal/api/',
            id_prefix: 'annotation-editor-'
        };

        var self = this;

        self.settings = {};

        var $element = $(element);
        var $e = $element;

        // save the rotation to the DB
        self.save = function() {
            if (!self.is_enabled()) return null;
            
            set_needs_refresh(true);

            var ret = $.ajax({
                url: self.settings.api_root + 'annotation/' + self.annotationid + '/?@select=id,rotation,htmlr',
                type: 'PUT',
                dataType: 'json',
                data: update_request_data_with_sliders(),
                success: function(data, status, jqXHR) { refresh_ui_from_response(data, status, jqXHR, true); }
            });
            
            return ret;
        };
        
        // reset the graph to edit.
        // this will trigger a call to the server to obtain the current rotation and shape.
        self.set_graphids = function(graphids) {
            // we don't know this yet, but we'll know after the first preview
            self.annotationid = 0;
            self.graphids = graphids;
            if (self.graphids && !(self.graphids instanceof Array)) { 
                self.graphids = [self.graphids] 
            }
            for (i in self.sliders) { 
                self.sliders[i].slider('option', 'disabled', !self.is_enabled());
            }
            self.preview(true);
        };

        // returns the rotation set by the user.
        // return -1 if the tool is disabled.
        self.get_rotation = function() {
            return self.is_enabled() ? self.get_slider_value('rotation') : -1;
        };

        self.get_slider_value = function(slider_key) {
            if (!(slider_key in self.sliders)) return false;
            return self.sliders[slider_key].slider('value');
        };
        
        // returns the rotation set by the user.
        // this will trigger a preview unless skip_preview = true
        self.set_rotation = function(rotation, skip_preview) {
            self.set_slider_value('rotation', rotation);
            // TODO: implement skip_preview to avoid double request during the first preview.
        };

        self.set_slider_value = function(slider_key, value) {
            self.sliders[slider_key].slider('value', value);
            set_slider_label(slider_key, value);
        };

        // returns true if the UI is enabled.
        // it is enabled only if it has been assigned to a single graph.
        self.is_enabled = function() {
            return (self.graphids && (self.graphids.length == 1) && self.$preview_div.is(':visible'));
        };
        
        // render the cutout of the annotation.
        // get_rotation_from_database = true to set the rotation slider from the value stored in the DB
        self.preview = function(get_parameters_from_database) {
            // get cutout html from server
            if (self.is_enabled()) {
                var data = {
                    '_graph__id': self.graphids[0],
                    '@select': 'rotation,htmlr',
                };
                if (!get_parameters_from_database) {
                    update_request_data_with_sliders(data);
                };
                
                $.ajax({
                    url: self.settings.api_root + 'annotation/',
                    type: 'GET',
                    dataType: 'json',
                    data: data,
                    success: function(data, status, jqXHR) { refresh_ui_from_response(data, status, jqXHR, get_parameters_from_database); }
                });
            } else {
                set_preview_html('<p>This tool works with only one selected graph.</p>');
            }
        };
        
        // Private methods
        
        var refresh_ui_from_response = function(data, status, jqXHR, refresh_sliders) {
            var html = '<p>Server error.</p>';
            if (data && data.success && data.results) {
                html = data.results[0].htmlr;
                if (refresh_sliders) {
                    for (i in self.sliders) {
                        self.set_slider_value(i, 0);
                    }
                    self.set_rotation(data.results[0].rotation, true);
                }
                self.annotationid = data.results[0].id;
            }
            set_preview_html(html);
            set_needs_refresh(false);
        };
        
        var quick_preview = function() {
            // quick preview
            var $img = self.$preview_div.find('img');
            if ($img.length) {
                var style = $img.attr('style');
                if (style) {
                    $img.attr('style', style.replace(/\d+(\.\d+)?deg/g, '' + self.get_rotation() + 'deg'));
                }
            }
            set_needs_refresh(true);
        };
        
        var update_request_data_with_sliders = function(data) {
            if (!data) data = {};
            data.rotation = self.get_slider_value('rotation');
            param_sliders = {'shape_x_diff': 'right', 'shape_y_diff': 'down', 'shape_width_diff': 'width', 'shape_height_diff': 'height'};
            for (param in param_sliders) {
                slider_key = param_sliders[param];
                val = self.get_slider_value(slider_key);
                if (val !== false) {
                    data[param] = val;
                } 
            }
            return data;
        };

        var on_changing_slider = function(event, ui) {
            set_slider_label(ui.handle.parentElement.id.replace(self.settings.id_prefix, ''), ui.value);
            quick_preview();
        };
        
        var set_needs_refresh = function(need_refresh) {
            self.$preview_div.attr('style', 'opacity:' + (need_refresh ? '0.5' : '1'));
        };
        
        var set_slider_label = function(slider_key, value) {
            $e.find('label[for='+self.settings.id_prefix+slider_key+'] span').html(value);
        };

        var set_preview_html = function(html) {
            self.$preview_div.html(html);
        };

        // constructor
        // initialise the member variables, the UI and events
        // it also generates an initial preview
        self.init = function() {
            self.settings = $.extend({}, defaults, options);
            self.sliders = {};
            $e.find('.slider').each(function() {
                //self.$rotation_slider = $e.find('#annotation-editor-rotation').slider({
                var key = this.id.replace(self.settings.id_prefix, '');
                $this = $(this);
                self.sliders[key] = $(this).slider({
                    min: $this.data('min'),
                    max: $this.data('max'),
                    slide: on_changing_slider,
                    stop: function() {self.preview();}
                });
            });
            self.$preview_div = $e.find('#' + self.settings.id_prefix + 'preview');
            
            self.set_graphids();
        };

        self.init();
    };

    // see http://stefangabos.ro/jquery/jquery-plugin-boilerplate-revisited/
    $.fn.annotation_editor = function(options) {

        return this.each(function() {
            if (undefined === $(this).data('annotation_editor')) {
                var self = new $.annotation_editor(this, options);
                $(this).data('annotation_editor', self);
            }
        });

    };

}(jQuery));
