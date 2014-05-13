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
            api_root : '/digipal/api/'
        }

        var self = this;

        self.settings = {};

        var $element = $(element), element = element;
        var $e = $element;

        // save the rotation to the DB
        self.save = function() {
            if (!self.is_enabled()) return null;
            
            var ret = $.ajax({
                url: self.settings.api_root + 'annotation/'+self.annotationid+'/?@select=id',
                type: 'PUT',
                dataType: 'json',
                data: {
                    rotation: self.get_rotation(),
                },
            });
            
            return ret;
        }
        
        // reset the graph to edit.
        // this will trigger a call to the server to obtain the current rotation and shape.
        self.set_graphids = function(graphids) {
            // we don't know this yet, but we'll know after the first preview
            self.annotationid = 0;
            self.graphids = graphids;
            if (self.graphids && !(self.graphids instanceof Array)) { 
                self.graphids = [self.graphids] 
            }
            self.$rotation_slider.slider('option', 'disabled', !self.is_enabled());
            self.preview(true);
        }

        // returns the rotation set by the user.
        // return -1 if the tool is disabled.
        self.get_rotation = function() {
            return self.is_enabled() ? self.$rotation_slider.slider('value') : -1;
        }
        
        // returns the rotation set by the user.
        // this will trigger a preview unless skip_preview = true
        self.set_rotation = function(rotation, skip_preview) {
            self.$rotation_slider.slider('value', rotation);
            set_rotation_label(rotation);
            // TODO: implement skip_preview to avoid double request during the first preview.
        }

        // returns true if the UI is enabled.
        // it is enabled only if it has been assigned to a single graph.
        self.is_enabled = function() {
            return (self.graphids && (self.graphids.length == 1) && self.$preview_div.is(':visible'))
        }
        
        // render the cutout of the annotation.
        // get_rotation_from_database = true to set the rotation slider from the value stored in the DB
        self.preview = function(get_rotation_from_database) {
            // get cutout html from server
            if (self.is_enabled()) {
                var data = {
                    '_graph__id': self.graphids[0],
                    '@select': 'rotation,html',
                };
                if (!get_rotation_from_database) { data.rotation = self.get_rotation() };
                
                $.ajax({
                    url: self.settings.api_root + 'annotation/',
                    type: 'GET',
                    dataType: 'json',
                    data: data,
                    success: function(data, status, jqXHR) {
                        var html = '<p>Server error.</p>';
                        if (data && data.success && data.results) {
                            html = data.results[0].html;
                            if (get_rotation_from_database) {
                                self.set_rotation(data.results[0].rotation, true);
                            }
                            self.annotationid = data.results[0].id;
                        }
                        set_preview_html(html);
                        set_needs_refresh(false);
                    }
                });
            } else {
                set_preview_html('<p>This tool works with only one selected graph.</p>');
            }
        }
        
        // Private methods
        
        var on_rotating = function(event, ui) {
            set_rotation_label(ui.value);
            // quick preview
            var $img = self.$preview_div.find('img');
            if ($img.length) {
                var style = $img.attr('style');
                if (style) {
                    $img.attr('style', style.replace(/\d+(\.\d+)?deg/g, ''+self.get_rotation()+'deg'));
                }
                console.log(style);
            }
            set_needs_refresh(true);
        }
        
        var set_needs_refresh = function(need_refresh) {
            self.$preview_div.attr('style', 'opacity:'+(need_refresh ? '0.5' : '1'));
        }
        
        var set_rotation_label = function(rotation) {
            $e.find('label[for=annotation-editor-rotation] span').html(rotation);
        }

        var set_preview_html = function(html) {
            self.$preview_div.html(html);
        }

        // constructor
        // initialise the member variables, the UI and events
        // it also generates an initial preview
        self.init = function() {
            self.settings = $.extend({}, defaults, options);
            self.$rotation_slider = $e.find('#annotation-editor-rotation').slider({
                max : 360,
                slide : on_rotating,
                stop : function() {self.preview();},
            });
            self.$preview_div = $e.find('#annotation-editor-preview');
            
            self.set_graphids();
        }

        self.init();
    };

    // see http://stefangabos.ro/jquery/jquery-plugin-boilerplate-revisited/
    $.fn.annotation_editor = function(options) {

        return this.each(function() {
            if (undefined == $(this).data('annotation_editor')) {
                var self = new $.annotation_editor(this, options);
                $(this).data('annotation_editor', self);
            }
        });

    }

}(jQuery));
