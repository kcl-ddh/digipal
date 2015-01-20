(function($) {
    
    //
    // PanelSet
    //
    PanelSet = function() {
        this.panels = [];
        this.$root = null;
        this.layout = null;
        this.$messageBox = null;
        
        this.registerPanel = function(panel) {
            this.panels.push(panel);
        };

        this.setLayout = function($root) {
            this.$root = $root;
            this.layout = $root.layout({ 
                applyDefaultStyles: true,
                closable: true,
                resizable: true,
                slidable: true,
                livePaneResizing: true,
            });
        };
        
        this.setMessageBox = function($messageBox) {
            this.$messageBox = $messageBox;
        };

        this._resize = function(refreshLayout) {
            // resize the div to the available height on the browser viewport
            var window_height = $(window).height();
            var height = window_height - this.$root.offset().top + $(document).scrollTop();
            height = (height < 1) ? 0 : height;
            height = (height > window_height) ? window_height : height;
            console.log('----');
            console.log(window_height);
            console.log(this.$root.offset().top);
            console.log($(document).scrollTop());
            console.log(this.$messageBox.outerHeight());
            this.$root.css('height', height - this.$messageBox.outerHeight());
            
            if (refreshLayout && this.layout) {
                this.layout.resizeAll();
            }
        };

        this.initEvents = function() {
            
            this._resize(true);
            var me = this;
            
            $(window).resize(function() { 
                me._resize();
                });
            $(window).scroll(function() { 
                me._resize(true);
                });
        };
        
        this.ready = function() {
            this.initEvents();
        };
        
    };
    
    //
    // Panel: a Panel managed by the panelset
    // Usage:
    //    var panelset = $('#text-viewer').panelset();
    //    panelset.registerPanel(new Panel($('.ui-layout-center')));
    Panel = function($root) {
        this.$root = $root;
    };
    
    PanelText = function($root) {
        Panel.call(this, $root);
    };

    PanelTextWrite = function($root) {
        PanelText.call(this, $root);
        
        this.initTinyMCE();
    };
    
    PanelTextWrite.prototype.initTinyMCE = function() {
        this.$root.append('<div id="text-area"></div>');
        tinyMCE.init({
            selector: "#text-area",
            /* init_instance_callback: tinymce_ready, */
            plugins: ["paste"],
            toolbar: "undo redo", 
            menubar : false,
            statusbar: false,
            height: '15em',
            content_css : "/static/digipal_text/viewer/tinymce.css"
        });
    }
    
    // These are external init steps for JSLayout
    function initLayoutAddOns() {
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
    };
    
    initLayoutAddOns();
    
}( jQuery ));
