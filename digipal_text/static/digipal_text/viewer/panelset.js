(function($) {

    function callApi(url, onSuccess, requestData) {
        // See http://stackoverflow.com/questions/9956255.
        // This tricks prevents caching of the fragment by the browser.
        // Without this if you move away from the page and then click back
        // it will show only the last Ajax response instead of the full HTML page.
        url = url ? url : '';
        var url_ajax = url + ((url.indexOf('?') === -1) ? '?' : '&') + 'jx=1';
        
        $.get(url_ajax, requestData)
            .success(function(data) {
                if (onSuccess) {
                    onSuccess(data);
                    //set_message(data.message, data.status);
                }
            })
            .fail(function(data) {
            });
    }

    
    //
    // PanelSet
    //
    PanelSet = function($root) {
        this.panels = [];
        this.$root = $root;
        this.$panelset = null;
        this.layout = null;
        this.$messageBox = null;
        
        this.registerPanel = function(panel) {
            this.panels.push(panel);
            panel.setItemPartid(this.itemPartid);
        };
        
        this.setItemPartid = function(itemPartid) {
            // e.g. '/itemparts/1/'
            this.itemPartid = itemPartid;
        };

        this.setLayout = function($panelset) {
            this.$panelset = $panelset;
            var me = this;
            var resize = function() { me._resizePanels(); };
            this.layout = $panelset.layout({ 
                applyDefaultStyles: true,
                closable: true,
                resizable: true,
                slidable: true,
                livePaneResizing: true,
                onopen: resize,
                onclose: resize,
                onshow: resize,
                onhide: resize,
                onresize: resize
            });
        };
        
        // Change the relative size of the panel
        // panelLocation: west|north|south|east
        // size: a ratio. e.g. 1/2.0 for half the full length
        this.setPanelSize = function(panelLocation, size) {
            if (size == 0) {
                this.layout.close(panelLocation);
            } else {
                var fullLength = this.$panelset[(panelLocation == 'east' || panelLocation == 'west') ? 'width': 'height']();
                this.layout.open(panelLocation);
                this.layout.sizePane(panelLocation, size * fullLength);
            }
        }

        this.setMessageBox = function($messageBox) {
            this.$messageBox = $messageBox;
        };

        this.setExpandButton = function($expandButton) {
            this.$expandButton = $expandButton;
            var me = this;
            this.$expandButton.on('click', function() { me.$panelset.css('height', $(window).height()); return true; });
        };

        this._resize = function(refreshLayout) {
            // resize the div to the available height on the browser viewport
            var window_height = $(window).height();
            var height = window_height - this.$root.offset().top + $(document).scrollTop();
            height = (height < 1) ? 0 : height;
            height = (height > window_height) ? window_height : height;
//            console.log('----');
//            console.log(window_height);
//            console.log(this.$root.offset().top);
//            console.log($(document).scrollTop());
//            console.log(this.$messageBox.outerHeight());
            this.$panelset.css('height', height - this.$messageBox.outerHeight());
            
            if (refreshLayout && this.layout) {
                this.layout.resizeAll();
            }
            
            this._resizePanels();
        };
        
        this._resizePanels = function() {
            for (var i in this.panels) {
                this.panels[i].onResize();
            }
        }

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
            for (var i in this.panels) {
                this.panels[i].componentIsReady('panelset');
            }
        };
        
    };
    
    //
    // Panel: a Panel managed by the panelset
    // Usage:
    //    var panelset = $('#text-viewer').panelset();
    //    panelset.registerPanel(new Panel($('.ui-layout-center')));
    Panel = function($root) {
        this.$root = $root;
        this.contentType = null;
        this.dirty = false;
        
        var $panelHtml = $('#text-viewer-panel').clone();
        $panelHtml.attr('id', '');
        this.$root.html($panelHtml);
        
        this.$locationSelect = this.$root.find('select[name=location]');
        this.$root.find('select').chosen();
        
        this.$content = this.$root.find('.panel-content');
        
        this.onResize = function () {
        };
        
        this.unreadyComponents = ['panelset'];
        
        this.componentIsReady = function(component) {
            var index = $.inArray(component, this.unreadyComponents);
            if (index > -1) {
                this.unreadyComponents.splice(index, 1);
            }
            if (this.unreadyComponents.length == 0) {
                this._ready();
            } 
        }
        
        this._ready = function(readyComponent) {
            var me = this;
            this.$locationSelect.on('change', function() {me.loadContent();});
            this.loadContent();
            this.onResize();

            setInterval(function() {
                me.saveContent();
            }, 1000);
        };

        this.loadContent = function() {
            this.$content.html('DUMMY CONTENT');
        };
        
        this.setItemPartid = function(itemPartid) {
            // e.g. '/itemparts/1/'
            this.itemPartid = itemPartid;
        };

        this.getContentAddress = function() {
            return '/digipal/manuscripts/' + this.itemPartid + '/texts/' + this.getContentType() + '/' + this.getLocationType() + '/' + this.getLocation() + '/';
        };
        
        this.getContentType = function() {
            return 'transcription';
        };
        
        this.getLocationType = function() {
            return 'folio';
        };

        this.getLocation = function() {
            return this.$locationSelect.val();
        };
                
        this.saveContent = function() {
        }
    };
    
    PanelText = function($root) {
        Panel.call(this, $root);
    };

    window.text_area_number = 0;
    
    PanelTextWrite = function($root) {
        PanelText.call(this, $root);
        
        this.unreadyComponents.push('tinymce');
        
        this.loadContent = function() {
            // load the content with the API
            var me = this;
            callApi(
                this.getContentAddress(), 
                function(data) {
                    me.tinymce.setContent(data.content); 
                } 
            );
        };

        this.onResize = function () {
            if (this.tinymce) {
                var $el = this.$root.find('iframe');
                var height = this.$root.innerHeight() - ($el.offset().top - $root.offset().top);
                $el.height(height+'px');
            }
        };

        this.saveContent = function() {
            var me = this;
            if (this.tinymce.isDirty()) {
                this.tinymce.isNotDirty = true;
                callApi(
                    this.getContentAddress(), 
                    function(data) {
                        //me.tinymce.setContent(data.content); 
                    },
                    {'content': me.tinymce.getContent()}
                );
            }
        }
        
        this.initTinyMCE();
    };
    
    PanelTextWrite.prototype.initTinyMCE = function() {
        window.text_area_number += 1;
        var divid = 'text-area-' + window.text_area_number;
        this.$content.append('<div id="'+ divid + '"></div>');
        var me = this;
        tinyMCE.init({
            selector: '#' + divid,
            init_instance_callback: function() {
                me.tinymce = tinyMCE.get(divid);
                me.componentIsReady('tinymce');
                },
            plugins: ["paste"],
            toolbar: "undo redo", 
            menubar : false,
            statusbar: false,
            height: '15em',
            content_css : "/static/digipal_text/viewer/tinymce.css"
        });
        
    }
    
    PanelImage = function($root) {
        Panel.call(this, $root);
    };
    
    PanelNavigator = function($root) {
        Panel.call(this, $root);
    };

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
