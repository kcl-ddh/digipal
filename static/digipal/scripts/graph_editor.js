/**
 * 
 */
(function($) {

      $.graph_editor = function(element, options) {

        var defaults = {
            color : "#556b2f",
            backgroundColor : "white"
        }

        var self = this;

        self.settings = {};

        var $element = $(element), element = element;
        var $e = $element;

        self.init = function() {
            self.settings = $.extend({}, defaults, options);
            self.$rotation_slider = $e.find("#graph-rotation").slider({
                max : 360,
                slide : on_rotating,
                stop : self.preview
            });
            self.$preview_div = $e.find("#edit_graph_preview");
            self.preview();
        }

        var on_rotating = function(event, ui) {
            $e.find("label[for=graph-rotation] span").html(ui.value);
        }

        self.get_rotation = function() {
            return self.$rotation_slider.slider('value');
        }
        
        self.preview = function() {
            // get cropout html from server
            $.getJSON('/digipal/api/annotation', {graphids: '', rotation: self.get_rotation()}, 
                function(data, status, jqXHR) {
                    console.log(data);
                    self.$preview_div.html(self.get_rotation());
                }
            );
        }

        self.init();
    };

    $.fn.graph_editor = function(options) {

        return this.each(function() {
            if (undefined == $(this).data('graph_editor')) {
                var self = new $.graph_editor(this, options);
                $(this).data('graph_editor', self);
            }
        });

    }

}(jQuery));
