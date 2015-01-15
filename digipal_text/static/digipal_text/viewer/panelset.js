(function($) {
 
    $.fn.panelset = function() {
        
        this.panels = [];
        
        this.registerPanel = function(panel) {
            this.panels.push(panel);
        } 

        return this;
    };
    
    
    Panel = function($root) {
        this.$root = $root;
    }
    
}( jQuery ));



/*
    var $text_viewer = $('#text-viewer');
    var $panels = $text_viewer.find('.panels:first');
    var $layout = null;
    
    function resize_text_viewer() {
        // resize the div to the available height on the browser viewport
        var window_height = $(window).height();
        var height = window_height - $text_viewer.offset().top + $('body').scrollTop();
        height = (height < 1) ? 0 : height;
        height = (height > window_height) ? window_height : height;
        //$text_viewer.css('height', height);
        $panels.css('height', height - $text_viewer.find(':first').outerHeight());
    }
    
    resize_text_viewer();
    
    $(window).resize(resize_text_viewer);
    $(window).scroll(function() {
        resize_text_viewer(); 
        if ($layout) {
            $layout.resizeAll();
        }
    });

    $layout = $panels.layout({ 
        applyDefaultStyles: true,
        closable: true,
        resizable: true,
        slidable: true,
        livePaneResizing: true,
    });

    //
    //  DISABLE TEXT-SELECTION WHEN DRAGGING (or even _trying_ to drag!)
    //  this functionality will be included in RC30.80
    //
    $.layout.disableTextSelection = function(){
        var $d  = $(document)
        ,   s   = 'textSelectionDisabled'
        ,   x   = 'textSelectionInitialized'
        ;
        if ($.fn.disableSelection) {
            if (!$d.data(x)) // document hasn't been initialized yet
                $d.on('mouseup', $.layout.enableTextSelection ).data(x, true);
            if (!$d.data(s))
                $d.disableSelection().data(s, true);
        }
        //console.log('$.layout.disableTextSelection');
    };
    $.layout.enableTextSelection = function(){
        var $d  = $(document)
        ,   s   = 'textSelectionDisabled';
        if ($.fn.enableSelection && $d.data(s))
            $d.enableSelection().data(s, false);
        //console.log('$.layout.enableTextSelection');
    };

    $(".ui-layout-resizer")
    .disableSelection() // affects only the resizer element
    .on('mousedown', $.layout.disableTextSelection ); // affects entire document
*/
