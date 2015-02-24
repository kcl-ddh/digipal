(function($) {

    TextViewer = window.TextViewer || {};
    
    //
    // PanelSet
    //
    var PanelSet = TextViewer.PanelSet = function($root) {
        this.panels = [];
        this.$root = $root;
        this.$panelset = null;
        this.layout = null;
        this.$messageBox = null;
        this.isReady = false;
        
        this.registerPanel = function(panel) {
            this.panels.push(panel);
            panel.panelSet = this;
            panel.setItemPartid(this.itemPartid);
            if (this.isReady) {
                panel.componentIsReady('panelset');
            }
        };
        
        this.unRegisterPanel = function(panel) {
            for (var i in this.panels) {
                if (this.panels[i] == panel) {
                    this.panels.splice(i, 1);
                }
            }
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
            this.$panelset.css('height', height - this.$messageBox.outerHeight(true));
            
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
            this.isReady = true;
        };
        
    };
    
    /////////////////////////////////////////////////////////////////////////
    // Panel: a Panel managed by the panelset
    // Usage:
    //    var panelset = $('#text-viewer').panelset();
    //    panelset.registerPanel(new Panel($('.ui-layout-center')));
    //
    /////////////////////////////////////////////////////////////////////////
    var Panel = TextViewer.Panel = function($root, contentType) {
        this.$root = $root;
        
        // we set a ref from the root element to its panel 
        // so we can clean up things properly when the panel is replaced
        if ($root[0].textViewerPanel) {
            $root[0].textViewerPanel.onDestroy();
        }
        this.$root[0].textViewerPanel = this;
        
        this.contentType = contentType;
        
        // clone the panel template
        var $panelHtml = $('#text-viewer-panel').clone();
        $panelHtml.attr('id', '');
        this.$root.html($panelHtml);
        
        // assign controls to member variables
        this.$contentTypes = this.$root.find('.dropdown-content-type');
        
        this.$locationTypes = this.$root.find('.dropdown-location-type');
        this.$locationSelect = this.$root.find('select[name=location]');
        this.$root.find('select').chosen();
        
        this.$content = this.$root.find('.panel-content');
        this.$statusBar = this.$root.find('.status-bar');
        
        // loaded is the location of the last successfully loaded text fragment
        // content cannot be saved unless it has been loaded properly
        // This is to avoid a loading error from erasing conent.
        // On a load error the location may still be valid and the next
        // attempt to save will overwrite the fragment.
        this.loadedLocation = null;
        
        // METHODS
        
        this.callApi = function(title, url, onSuccess, requestData, synced) {
            var me = this;
            var onComplete = function(jqXHR, textStatus) {
                if (textStatus !== 'success') {
                    me.setMessage('Error during '+title+' (status: '+textStatus+')', 'error');
                }
            };
            var onSuccessWrapper = function(data, textStatus, jqXHR) {
                data.status = data.status || 'success';
                data.message = data.message || 'done ('+title+').';
                if (data.locations) {
                    me.updateLocations(data.locations);
                }
                if (data.status === 'success') {
                    onSuccess(data, textStatus, jqXHR);
                }
                me.setMessage(data.message, data.status);
            };
            this.setMessage(title+'...', 'info');
            var ret = TextViewer.callApi(url, onSuccessWrapper, onComplete, requestData, synced);
            return ret;
        } 
        
        this.onDestroy = function() {
            // destructor, the place to remove any resource and detach event handlers
            this.panelSet.unRegisterPanel(this);
            // prevent ghost saves (e.g. detached panel still listens to unload events)
            this.setNotDirty();
            this.loadedLocation = null;
        };
        
        this.onResize = function () {
            // resize content to take the remaining height in the panel
            var height = this.$root.innerHeight() - (this.$content.offset().top - $root.offset().top) - this.$statusBar.outerHeight(true);
            this.$content.css('max-height', height+'px');
            this.$content.height(height+'px');
        };
        
        this.setMessage = function(message, status) {
            // status = success|info|warning|error
            this.$statusBar.find('.message').html(message).removeClass('message-success message-info message-warning message-error').addClass('message-'+status);
            this.$statusBar.find('.time').html(TextViewer.getStrFromTime(new Date()));
        };
                
        this.unreadyComponents = ['panelset'];
        
        this.componentIsReady = function(component) {
            // we remove the component from the waiting list
            var index = $.inArray(component, this.unreadyComponents);
            if (index > -1) {
                this.unreadyComponents.splice(index, 1);
            }
            // if the waiting list is empty, we call _ready()
            if (this.unreadyComponents.length == 0) {
                this._ready();
            } 
        };
        
        this._ready = function() {
            var me = this;
            
            this.$contentTypes.dpbsdropdown({
                onSelect: function($el, key, $a) {
                    // the user has selected another view/content type -> we replace this panel
                    me.panelSet.registerPanel(new TextViewer['Panel'+$a.data('class')](me.$root, key));
                },
            });
            this.$contentTypes.dpbsdropdown('setOption', this.contentType, true);

            this.loadContent(true);
            
            this.onResize();

            this.$locationTypes.dpbsdropdown({
                onSelect: function($el, key) { me.onSelectLocationType(key); },
            });
            // fire onSelect event as we want to refresh the list of locations
            //this.$locationTypes.dpbsdropdown('onSelect');

            this.$locationSelect.on('change', function() {
                me.loadContent();
            });

            setInterval(function() {
                me.saveContent();
            }, 2500);
        };
        
        /*
         * Loading and saving
         * 
         * General rules about when the content should be saved:
         *      at regular interval (this class)
         *      when the editor loses the focus (subclass)
         *      before the window/tab/document is closed (subclass)
         * but
         *      only if the content has been changed (this.isDirty() and this.getContentHash())
         *      only if the content has been loaded properly (this.loadedLocation <> null)
         */
        
        /* LOADING CONTENT */

        this.loadContent = function(loadLocations) {
            if (this.loadedLocation != this.getContentAddress()) {
                this.setValid(false);
                // make sure no saving happens from now on
                // until the content is loaded
                this.loadedLocation = null;
                this.loadContentCustom(loadLocations);
            }
        };
        
        this.setValid = function(isValid) {
            //this.tinymce.setContent('');
            var $mask = this.$root.find('.mask');
            if ($mask.length == 0) {
                // TODO: move this HTML to the template.
                // Not good practice to create it with JS
                this.$content.prepend('<div class="mask"></div>');
                $mask = this.$root.find('.mask');
            }

            $mask.css('height', isValid ? '0' : '100%');
        }
        
        this.loadContentCustom = function(loadLocations) {
            // NEVER CALL THIS FUNCTION DIRECTLY
            // ONLY loadContent() can call it
            this.$content.html('Generic Panel Content');
            this.onContentLoaded();
        };
        
        this.onContentLoaded = function(loadedLocation) {
            //this.setMessage('Content loaded.', 'success');
            this.loadedLocation = loadedLocation;
            this.setNotDirty();
            this.setValid(true);
        };
        
        /* SAVING CONTENT */
        
        this.saveContent = function(options) {
            options = options || {};
            if (this.loadedLocation && (this.isDirty() || options.forceSave)) {
                console.log('SAVE '+this.getContentAddress());
                this.setNotDirty();
                this.saveContentCustom(options);
            }
        }
        
        this.saveContentCustom = function(options) {
            // NEVER CALL THIS FUNCTION DIRECTLY
            // ONLY saveContent() can call it
        }
        
        this.onContentSaved = function(data) {
        }

        /* -------------- */
        
        this.isDirty = function() {
            var ret = (this.getContentHash() !== this.lastSavedHash);
            return ret;
        }

        this.setNotDirty = function() {
            this.lastSavedHash = this.getContentHash();
        }

        this.setDirty = function() {
            var d = new Date();
            this.lastSavedHash = (d.toLocaleTimeString() + d.getMilliseconds());
        }
        
        this.getContentHash = function() {
            var ret = null;
            return ret;
            //return ret.length + ret;
        }
        
        // Address / Locations

        this.updateLocations = function(locations) {
            // Update the location drop downs from a list of locations
            // received from the server.

            if (locations) {
                // save the locations
                this.locations = locations;

                // only show the available location types
                var locationTypes = [];
                for (var j in locations) {
                    locationTypes.push(j);
                }
                
                this.$locationTypes.dpbsdropdown('showOptions', locationTypes);
                this.$locationTypes.dpbsdropdown('setOption', locationTypes[0]);
            }
        };

        this.onSelectLocationType = function(locationType) {
            // update the list of locations
            this.$locationSelect.empty();
            var empty = true;
            if (this.locations && this.locations[locationType]) {
                for (var i in this.locations[locationType]) {
                    this.$locationSelect.append('<option value="'+this.locations[locationType][i]+'">'+this.locations[locationType][i]+'</option>');
                    empty = false;
                }
            }
            this.$locationSelect.trigger('liszt:updated');
            this.$locationSelect.next().toggle(!empty);
        };
        
        this.setItemPartid = function(itemPartid) {
            // e.g. '/itemparts/1/'
            this.itemPartid = itemPartid;
        };

        this.getContentAddress = function() {
            return '/digipal/manuscripts/' + this.itemPartid + '/texts/' + this.getContentType() + '/' + this.getLocationType() + '/' + encodeURIComponent(this.getLocation()) + '/';
        };
        
        this.getContentType = function() {
            return this.contentType;
        };
        
        this.getLocationType = function() {
            return this.$locationTypes.dpbsdropdown('getOption');
        };

        this.getLocation = function() {
            return this.$locationSelect.val();
        };
        
    };
    
    Panel.create = function(contentType, selector, write) {
        var panelType = contentType.toUpperCase().substr(0, 1) + contentType.substr(1, contentType.length - 1);
        //if ($.inArray('Panel'+panelType+(write ? 'Write': ''), TextViewer) === -1) {
        var constructor = TextViewer['Panel'+panelType+(write ? 'Write': '')] || TextViewer['PanelText'+(write ? 'Write': '')];
        return new constructor($(selector), contentType);
    };
    
    var PanelText = TextViewer.PanelText = function($root, contentType) {
        TextViewer.Panel.call(this, $root, contentType);
    };

    //
    // PanelTextWrite
    //
    TextViewer.textAreaNumber = 0;
    
    var PanelTextWrite = TextViewer.PanelTextWrite = function($root, contentType) {
        TextViewer.PanelText.call(this, $root, contentType);
        
        this.unreadyComponents.push('tinymce');
        
        //$(editor.editorContainer).trigger('psconvert');
        // TODO: fix with 'proper' prototype inheritance
        this._baseReady = this._ready;
        this._ready = function() {
            var ret = this._baseReady();
            var me = this;
            
            $(this.tinymce.editorContainer).on('psconvert', function() {
                // mark up the content
                // TODO: make sure the editor is read-only until we come back
                me.saveContent({forceSave: true, autoMarkup: true});
            });
            
            $(this.tinymce.editorContainer).on('pssave', function() {
                // mark up the content
                // TODO: make sure the editor is read-only until we come back
                me.saveContent({forceSave: true, saveCopy: true});
            });

            // make sure we save the content if tinymce looses focus or we close the tab/window
            this.tinymce.on('blur', function() {
                me.saveContent();
            });

            $(window).bind('beforeunload', function() {
                me.saveContent({synced: true});
            });
            
            return ret;
        };
        
        this.loadContentCustom = function(loadLocations) {
            // load the content with the API
            var me = this;
            var loadedLocation = this.getContentAddress();
            this.callApi(
                'loading content',
                loadedLocation,
                function(data) {
                    if (data.content !== undefined) {
                        me.tinymce.setContent(data.content);
                        me.tinymce.undoManager.clear();
                        me.tinymce.undoManager.add();
                        me.onContentLoaded(loadedLocation);
                    } else {
                        //me.setMessage('ERROR: no content received from server.');
                    }
                },
                {
                    'load_locations': loadLocations ? 1 : 0,
                }
            );
        };

        
        // TODO: fix with 'proper' prototype inheritance
        this.baseOnResize = this.onResize;
        this.onResize = function () {
            this.baseOnResize();
            if (this.tinymce) {
                // resize tinmyce to take the remaining height in the panel
                var $el = this.$root.find('iframe');
                var height = this.$content.innerHeight() - ($el.offset().top - this.$content.offset().top);
                $el.height(height+'px');
            }
        };
        
        this.getContentHash = function() {
            var ret = this.tinymce.getContent();
            return ret;
            //return ret.length + ret;
        }

        this.saveContentCustom = function(options) {
            // options:
            // synced, autoMarkup, saveCopy
            var me = this;
            this.callApi(
                'saving content',
                this.getContentAddress(), 
                function(data) {
                    //me.tinymce.setContent(data.content);
                    me.onContentSaved(data);
                    if (options.autoMarkup) {
                        me.tinymce.setContent(data.content);
                        me.setNotDirty();
                    }
                },
                {
                    'content': me.tinymce.getContent(), 
                    'convert': options.autoMarkup ? 1 : 0, 
                    'save_copy': options.saveCopy ? 1 : 0,
                    'post': 1,
                },
                options.synced
                );
        };

        this.initTinyMCE = function() {
            TextViewer.textAreaNumber += 1;
            var divid = 'text-area-' + TextViewer.textAreaNumber;
            this.$content.append('<div id="'+ divid + '"></div>');
            var me = this;
            tinyMCE.init({
                skin : 'digipal',
                selector: '#' + divid,
                init_instance_callback: function() {
                    me.tinymce = tinyMCE.get(divid);
                    me.componentIsReady('tinymce');
                    
                    //me.tinymce.on('change', setDirty);

                    /*
                    me.tinymce.on('keydown', function(e) {
                        if (e.keyCode == 8) {
                            e.preventDefault();
                            var sel = me.tinymce.selection;
                            var b = sel.getBookmark();
                            var $p = $(sel.getNode());
                            var $parent = $p.parent();
                            if ($parent.prop('tagName') == 'P') {
                                var pos = $parent.html().indexOf($p[0].outerHTML);
                                if (pos == 0) {
                                    // do we have a p before the parent?
                                    $prev = $p.prev();
                                    if ($prev.prop('tagName') == 'P') {
                                        // we have a p before this p, let's merge them
                                        $prev.append($p.html());
                                        $p.remove();
                                        return false;
                                    }
                                }
                            }
                            
                            var i = 10;
                            var i2 = i + 3;
                        }
                        return true;
                    });
                    */
                },
//                setup : function(ed) {
//                    ed.onPaste.add(function(ed, e) {
//                        // TODO: move the code to the plug in as a tinymce command.
//                        // convert all the Ps into DIVs
//                        ed.setContent(ed.getContent().replace(/<\/?p/g, '<div'));
//                    });
//                },
                plugins: ['paste', 'code', 'panelset'],
                toolbar: 'psclear undo redo pssave | psconvert | psclause | pslocation | psex pssupplied psdel | code ',
                paste_word_valid_elements: 'i,em,p,span',
                paste_postprocess: function(plugin, args) {
                    //args.node is a temporary div surrounding the content that will be inserted
                    //console.log($(args.node).html());
                    //$(args.node).html($(args.node).html().replace(/<(\/?)p/g, '<$1div'));
                    //console.log($(args.node).html());
                },
                menubar : false,
                statusbar: false,
                height: '15em',
                content_css : "/static/digipal_text/viewer/tinymce.css?v=1"
            });
            
        };
        
        this.initTinyMCE();
    };
        
    //
    // PanelImage
    //
    var PanelImage = TextViewer.PanelImage = function($root, contentType) {
        TextViewer.Panel.call(this, $root, contentType);
        
        this.loadContentCustom = function(loadLocations) {
            // load the content with the API
            var me = this;
            var loadedLocation = this.getContentAddress()
            this.callApi(
                'loading image',
                loadedLocation, 
                function(data) {
                    me.$content.html(data.content).find('img').load(function() {me.onContentLoaded(loadedLocation);});
                },
                {
                    'layout': 'width',
                    'width': me.$content.width(),
                    'height': me.$content.height(),
                    'load_locations': loadLocations ? 1 : 0,
                }
            );
        };
    };
    
    //
    // PanelNavigator
    //
    var PanelNavigator = TextViewer.PanelNavigator = function($root, contentType) {
        TextViewer.Panel.call(this, $root, contentType);
    };
    
    // PanelXmlelement
    var PanelXmlelementWrite = TextViewer.PanelXmlelementWrite = function($root, contentType) {
        TextViewer.Panel.call(this, $root, contentType);
    }
        
    // UTILITIES

    TextViewer.callApi = function(url, onSuccess, onComplete, requestData, synced) {
        // See http://stackoverflow.com/questions/9956255.
        // This tricks prevents caching of the fragment by the browser.
        // Without this if you move away from the page and then click back
        // it will show only the last Ajax response instead of the full HTML page.
        url = url ? url : '';
        var url_ajax = url + ((url.indexOf('?') === -1) ? '?' : '&') + 'jx=1';
        
        var getData = {
            url: url_ajax, 
            data: requestData, 
            async: (synced ? false : true), 
            complete: onComplete,
            success: onSuccess
        };
        if (requestData && requestData.post) {
            delete requestData.post;
            getData.type = 'POST';
        }
        var ret = $.ajax(getData);
        
        return ret;
    }
    
    TextViewer.getStrFromTime = function(date) {
        date = date || new Date();
        var parts = [date.getHours(), date.getMinutes(), date.getSeconds()];
        for (var i in parts) {
            if ((i > 0) && (parts[i] < 10)) {parts[i] = '0' + parts[i]};
        }
        return parts.join(':');
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
        };
        $.layout.enableTextSelection = function(){
            var $d  = $(document)
            ,   s   = 'textSelectionDisabled';
            if ($.fn.enableSelection && $d.data(s))
                $d.enableSelection().data(s, false);
        };
    
        var $lrs = $(".ui-layout-resizer");
        
        // affects only the resizer element
        // TODO: GN - had to add this condition otherwise the function call fails.
        if ($.fn.disableSelection) {
            $lrs.disableSelection();
        }
        
        $lrs.on('mousedown', $.layout.disableTextSelection ); // affects entire document
    };
    
    initLayoutAddOns();
    
    // TODO: move to dputils.js
    
    // See https://docs.djangoproject.com/en/1.7/ref/contrib/csrf/#ajax
    // This allows us to POST with Ajax
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", dputils.getCookie('csrftoken'));
            }
        }
    });
    
}( jQuery ));
