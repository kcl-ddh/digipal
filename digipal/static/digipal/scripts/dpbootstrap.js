/*
 * A JQuery plugin to control a Bootstrap dropdown widget.
 *
 * Usage:
 *      var $mydropdown = $('.dropdown something-more-specific');
 *
 *      $mydropdown.dpbsdropdown({onSelect: onSelect});
 *
 *      var currentOption = $mydropdown.dpbsdropdown('getOption');
 *      $mydropdown.dpbsdropdown('setOption', 'option-key');
 *
 *      // return the plug-in instance
 *      $mydropdown.dpbsdropdown();
 *
 *      // This call will keep the same plug in instance and update its opts
 *      // That way we don't create a second instance with both listening to the same events
 *      $mydropdown.dpbsdropdown({onSelect: onSelect2});
 *
 */
;(function ( $, window, document, undefined ) {

    var pluginName = "dpbsdropdown";
    var defaults = {
        onSelect: function() {},
        // if true, a click will always trigger select()
        // if false, only a change triggers select()
        selectIfSame: false,
    };

    function Plugin( el, opts ) {
        this.$el = $(el);

        this.setOpts(opts);

        this._defaults = defaults;
        this._name = pluginName;

        this.init();
    }
    
    Plugin.prototype = {
        
        setOpts: function(opts) {
            this.opts = $.extend({}, defaults, opts);
        },
        
        init: function() {
            this.setOption(undefined, true);
            var me = this;
            
            // bit of a trick to make sure the drop down closes
            // when the user click an item
            // see counterpart in click event below
            this.$el.on('mouseenter', function () {
                me.$el.find('ul').removeClass('dpbs-clicked');
            });
            
            // when the user clicks an option we select it
            // and we close the drop down
            this.$el.find('ul li a').on('click', function() {
                me.setOption($(this).attr('href'));
                document.activeElement.blur();
                
                // That won't work because of mezzanine hacks
                //me.$el.find('.dropdown-toggle').dropdown('toggle');
                // Close the drop down
                $(this).closest('ul').addClass('dpbs-clicked');
                
                return false;
            });
        },
        
        getLabels: function(key, silent) {
            var ret = [];
            this.$el.find('ul.dropdown-menu li a').each(function() {
                ret.push($(this).text());
            });
            return ret;
        },
        
        getOptions: function(key, silent) {
            // return all the options as an array of pairs [value/key,label]
            var ret = [];
            this.$el.find('ul.dropdown-menu li a').each(function() {
                var key = $(this).attr('href');
                if (key && key.length > 1 && key[0] == '#') {
                    key = key.substr(1, key.length - 1);
                }
                ret.push([key, $(this).text()]);
            });
            return ret;
        },

        setOption: function(key, silent) {
            // select the option from its key
            // if key is not provided, leave the selection as it is
            // if no selection yet, select the first visible option
            // If the key has changed and silent is not true,
            // the 'onSelect' user callback is triggered
            key = key || this.getOption();
            
            if (key && key.length > 1 && key[0] == '#') {
                key = key.substr(1, key.length - 1);
            }
            
            var currentOption = this.$el.parent().data('value');
            if (this.opts.selectIfSame || (currentOption != key)) {
                var $selectedA = this.$el.find('a[href=#'+key+']');
                // Replace the dropdown heading label by the selected option
                if ($selectedA.length) {
                    this.$el.find('.dropdown-toggle span:first').replaceWith($selectedA.find('span')[0].outerHTML);
                    
                    // Highlight the selected option
                    $selectedA.closest('ul').find('li').removeClass('bsdp-selected');
                    $selectedA.closest('li').addClass('bsdp-selected');
                                    
                    // save the selected value in the parent data-value attribute
                    this.$el.parent().data('value', key);
                    
                    // call the user callback
                    if (!silent) this.onSelect();
                }
            }
        },
        
        onSelect: function() {
            var key = this.getOption();
            //console.log('Callback ('+this.$el.attr('class')+') key = '+ key);
            this.opts.onSelect(this.$el, key, this.$el.find('a[href="#'+key+'"]'));
        },
        
        getOption: function() {
            // returns the key of the current selection
            // if nothing selected yet, return the first visible item
            var ret = this.$el.parent().data('value');
            if (!ret) {
                this.$el.find('.dropdown-menu li').each(function () {
                    if ($(this).css('display') != 'none') {
                        ret = $(this).find('a').attr('href');
                        return false;
                    }
                });
                ret = ret ? ret.substr(1, ret.length - 1) : '';
            }
            return ret;
        },
        
        showOptions: function(keys) {
            // only show the given options
            this.$el.find('ul li').hide();
            
            for (var j in keys) {
                this.$el.find('ul li a[href=#'+keys[j]+']').parent().show();
            }
            // call this in case the selected option has disappeared
            this.setOption();
        }
    };

    
    // GN: adapted from
    // http://stackoverflow.com/questions/1117086/how-to-create-a-jquery-plugin-with-methods
    // and
    // https://github.com/jquery-boilerplate/jquery-patterns/blob/master/patterns/jquery.basic.plugin-boilerplate.js
    //
    $.fn[pluginName] = function(opts) {
        if ((this.length === 1) && ($.data(this[0], "plugin_" + pluginName))) {
            // plugin already assigned to the DOM element
            var plugin = $.data(this[0], "plugin_" + pluginName);
            if (arguments.length === 0) {
                // no argument => we return the plugin
                return plugin;
            } else {
                // we have arguments
                // this is a function name and we call it with the rest of the arguments
                var method = Plugin.prototype[arguments[0]];
                if (method) {
                    return method.apply(plugin, Array.prototype.slice.call( arguments, 1 ));
                } else {
                    // assume this is a set of options
                    // this allows us to reset the options on an existing plugin rather than creating a new one
                    // client doesn't have to care whether a plugin has already been assigned to this element or not
                    // the result is the same.
                    Plugin.prototype.setOpts.apply(plugin, arguments);
                }
            }
        } else {
            // instantiate a new plug in on the given elements
            return this.each(function () {
                if (!$.data(this, "plugin_" + pluginName)) {
                    $.data(this, "plugin_" + pluginName, new Plugin( this, opts ));
                }
            });
        }
    };
    
})( jQuery, window, document );

/*
jQuery(document).ready(function($) {
    var $dd = $('.dropdown-location-type');
    var onSelect = function($dd, key) {
        console.log('In callback');
        console.log(key);
    };
    var onSelect2 = function($dd, key) {
        console.log('In callback 2');
        console.log(key);
    };
    $dd.dpbsdropdown({onSelect: onSelect});
    $dd.dpbsdropdown('showOptions', ['folio', 'entry']);
    $dd.dpbsdropdown('getOption');
    $dd.dpbsdropdown({onSelect: onSelect2});
    $dd.dpbsdropdown('setOption', 'entry');
    $dd.dpbsdropdown('getOption');
});
*/
