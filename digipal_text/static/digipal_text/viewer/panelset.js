(function(TextViewer, $, undefined) {

    //////////////////////////////////////////////////////////////////////
    //
    // PanelSet
    //
    //////////////////////////////////////////////////////////////////////
    TextViewer.PanelSet = function($root) {
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
        
        this.onPanelContentLoaded = function(panel, locationType, location) {
            for (var i in this.panels) {
                this.panels[i].syncLocationWith(panel, locationType, location);
            }
        };
        
        this.syncPanel = function(panel) {
            for (var i in this.panels) {
                panel.syncLocationWith(this.panels[i], this.panels[i].getLocationType(), this.panels[i].getLocation());
            }
        };
        
        this.getBaseAddress = function() {
            return '/digipal/manuscripts/' + this.itemPartid + '/texts/';
        };
        
        this.onPanelStateChanged = function(panel) {
            var state = panel.getState();
            var key = panel.getPanelKey();
            
            // update the URL
            var url = window.location.href;
            // add qs if none yet
            if (url.indexOf('?') == -1) {
                if (url.indexOf('#') == -1) {
                    url = url + '?';
                } else {
                    url = url.replace('#', '?#');
                }
            }
            // add qs param if none yet
            if (url.indexOf(key+'=') == -1) {
                url = url.replace('?', '?'+key+'='+'&');
            }
            // replace existing query string param
            url = url.replace(new RegExp(key+"=[^&#]*"), key+'='+encodeURI(state));
            window.history.replaceState('', window.title, url);
            
        };
        
        this.setStateFromUrl = function(defaultState) {
            // we merge the defaultState with the state from the Query String
            var args = $.extend(this.getQSArgs(defaultState), this.getQSArgs(window.location.href, true));
            var state = Object.keys(args).reduce(function(pv,cv) {
                return pv + cv + '=' + args[cv] + '&';
            }, '?');
            this.setState(state);
        };
        
        this.getQSArgs = function(queryString, decode) {
            // in: '?k1=v1&k2=v2'
            // out: {'k1': 'v1', 'k2': 'v2'}
            var ret = {};
            if (queryString && queryString.length) {
                var match = (queryString.match(/(&|\?)(\w+)=([^&#]+)/g));
                if (match) {
                    match.map(function(v) {
                        var arg = v.replace(/[\?#&]/g, '').split('=');
                        ret[arg[0]] = decodeURI ? decodeURI(arg[1]) : arg[1];
                        return '';
                    });
                }
            }
            return ret;
        };

        this.setState = function(state) {
            // '?center=transcription/default/&east=translation/default/&north=image/default/';
            var me = this;
            if (state && state.length) {
                var args = (state.match(/(&|\?)(\w+)=([^&#]+)/g)).map(function(v) { return v.replace(/[\?#&]/g, '').split('='); });
                args.map(function(arg) {
                    var key = arg[0];
                    var panelState = arg[1];
                    me.registerPanel(TextViewer.Panel.createFromState(panelState, key));
                });
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
            if (size === 0) {
                this.layout.close(panelLocation);
            } else {
                var fullLength = this.$panelset[(panelLocation == 'east' || panelLocation == 'west') ? 'width': 'height']();
                this.layout.open(panelLocation);
                this.layout.sizePane(panelLocation, size * fullLength);
            }
        };

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
            var height = window.dputils.get_elastic_height(this.$root);

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
            for (var i in this.panels) {
                this.panels[i].componentIsReady('panelset');
            }
            this.isReady = true;
        };
        
    };
    
    /////////////////////////////////////////////////////////////////////////
    // Panel: an abstract Panel managed by the panelset
    // This is the base class for all specific panel types (e.g. text, image)
    // It provides some basic behaviour for auto-resizing, loading/saving content
    //
    // Usage:
    //    var panelset = $('#text-viewer').panelset();
    //    panelset.registerPanel(new Panel($('.ui-layout-center')));
    //
    //    options
    //      locationType
    //      location
    //
    /////////////////////////////////////////////////////////////////////////
    var Panel = TextViewer.Panel = function($root, contentType, panelType, options) {
        this.$root = $root;
        
        this.loadOptions = options || {};
        
        // we set a ref from the root element to its panel
        // so we can clean up things properly when the panel is replaced
        if ($root[0].textViewerPanel) {
            $root[0].textViewerPanel.onDestroy();
        }
        this.$root[0].textViewerPanel = this;
        
        this.panelType = panelType;
        this.contentType = contentType;
        
        this.panelSet = null;
        
        // loaded is the location of the last successfully loaded text fragment
        // content cannot be saved unless it has been loaded properly
        // This is to avoid a loading error from erasing conent.
        // On a load error the location may still be valid and the next
        // attempt to save will overwrite the fragment.
        this.loadedAddress = null;

        // clone the panel template
        var $panelHtml = $('#text-viewer-panel').clone();
        $panelHtml.removeAttr('id');
        $panelHtml.addClass('ct-'+contentType);
        $panelHtml.addClass('pt-'+panelType.toLowerCase());
        this.$root.html($panelHtml);
        
        // We create bindings for all the html controls on the panel
        
        this.$contentTypes = this.$root.find('.dropdown-content-type');
        
        this.$locationTypes = this.$root.find('.dropdown-location-type');
        this.$locationSelect = this.$root.find('select[name=location]');
        this.$linker = this.$root.find('.linker');
        this.$linkerImage = this.$linker.find('.linker-image');
        this.$linkerText = this.$linker.find('select[name=linker-text]');
        
        var me = this;
        
        this.canAddLocation = function() {
            return this.getEditingMode();
        };
        
        this.$root.find('select').each(function() {
            $(this).chosen({
                disable_search: $(this).hasClass('no-search'),
                no_results_text: $(this).hasClass('can-add') ? 'Not found, select to add' : 'Location not found'
            });
        });
        
        this.$content = this.$root.find('.panel-content');
        this.$statusBar = this.$root.find('.status-bar');
        
        this.$statusSelect = this.$root.find('select[name=status]');
        this.$presentationOptions = this.$root.find('.presentation-options');
        
        this.$toggleEdit = this.$root.find('.toggle-edit');
        
        this.$downloadButton = this.$root.find('.action-download');
        
        // METHODS
        
        this.callApi = function(title, url, onSuccess, requestData, synced) {
            var me = this;
            var onComplete = function(jqXHR, textStatus) {
                if (textStatus !== 'success') {
                    me.setMessage('Error while '+title+' (status: '+textStatus+')', 'error');
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
        };
        
        this.onDestroy = function() {
            // destructor, the place to remove any resource and detach event handlers
            this.panelSet.unRegisterPanel(this);
            // prevent ghost saves (e.g. detached panel still listens to unload events)
            this.setNotDirty();
            this.loadedAddress = null;
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
            if (this.unreadyComponents.length === 0) {
                this._ready();
            }
        };
        
        this._ready = function() {
            var me = this;
            
            this.updateEditingModeIcon();
            
            this.$contentTypes.dpbsdropdown({
                onSelect: function($el, key, $a) {
                    // the user has selected another view/content type -> we replace this panel
                    me.panelSet.registerPanel(new TextViewer['Panel'+$a.data('class')](me.$root, key));
                },
            });
            this.$contentTypes.dpbsdropdown('setOption', this.contentType, true);

            this.loadContent(true, this.loadOptions.contentAddress ?  this.panelSet.getBaseAddress() + this.loadOptions.contentAddress : undefined);
            
            this.onResize();

            this.$locationTypes.dpbsdropdown({
                onSelect: function($el, key) { me.onSelectLocationType(key); },
            });
            // fire onSelect event as we want to refresh the list of locations
            //this.$locationTypes.dpbsdropdown('onSelect');
            
            this.$statusSelect.on('change', function() {
                // digipal/api/textcontentxml/?_text_content__item_part__id=1628&_text_content__type__slug=translation&status__id=7
                var ret = TextViewer.callApi('/digipal/api/textcontentxml/', null, null, {
                    'method': 'PUT',
                    '_text_content__item_part__id': me.itemPartid,
                    '_text_content__type__slug': me.getContentType(),
                    'status__id': $(this).val(),
                    '@select': 'id'
                });
            });
            
            this.$presentationOptions.on('change', 'input[type=checkbox]', function() {
                me.applyPresentationOptions();
                me.panelSet.onPanelStateChanged(me);
            });

            this.$locationSelect.on('change', function() {
                me.loadContent();
            });
            
            this.$downloadButton.closest('.dphidden').toggle(this.isDownloadable());
            this.$downloadButton.on('click', function() {
                // http://localhost/digipal/manuscripts/1/texts/codicology/whole/?jx=1&load_locations=0&ds=&format=html&ds=locus
                var url = me.getContentAddress('whole', '');
                url += '?ds=' + (me.getListFromPresentationOptions()).join(',');
                window.open(url, '_blank');
            });
            
            this.$linkerText.on('change', function() {
                me.onLinkerTextChanged();
            });

            setInterval(function() {
                me.saveContent();
            }, 2500);
        };
        
        this.syncLocationWith = function(panel, locationType, location) {
            if ((panel !== this) && (this.getLocationType() === 'sync') && (this.getLocation().toLowerCase() == panel.getContentType().toLowerCase())) {
                this.loadContent(false, this.getContentAddress(locationType, location));
            }
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
         *      only if the content has been loaded properly (this.loadedAddress <> null)
         */
        
        /* LOADING CONTENT */

        this.loadContent = function(loadLocations, address) {
            if (!address && (this.getLocationType() == 'sync')) {
                this.panelSet.syncPanel(this);
                return;
            }
            
            address = address || this.getContentAddress();
            
            if (this.loadedAddress != address) {
                this.setValid(false);
                // make sure no saving happens from now on
                // until the content is loaded
                this.loadedAddress = null;
                this.loadContentCustom(loadLocations, address);
            }
        };
        
        this.loadContentCustom = function(loadLocations, address) {
            // NEVER CALL THIS FUNCTION DIRECTLY
            // ONLY loadContent() can call it
            this.$content.html('Generic Panel Content');
            this.onContentLoaded();
        };
        
        /* SAVING CONTENT */
        
        this.saveContent = function(options) {
            options = options || {};
            if (this.loadedAddress && (this.isDirty() || options.forceSave)) {
                //console.log('SAVE '+this.loadedAddress);
                this.setNotDirty();
                this.saveContentCustom(options);
            }
        };
        
        this.saveContentCustom = function(options) {
            // NEVER CALL THIS FUNCTION DIRECTLY
            // ONLY saveContent() can call it
        };
        
        this.onContentSaved = function(data) {
        };

        /* -------------- */
        
        this.setValid = function(isValid) {
            // tells us if the content is invalid
            // if it is invalid we have to block editing
            // visually inform the user the content is not valid.
            var $mask = this.$root.find('.mask');
            if ($mask.length === 0) {
                // TODO: move this HTML to the template.
                // Not good practice to create it with JS
                this.$content.prepend('<div class="mask"></div>');
                $mask = this.$root.find('.mask');
            }

            $mask.css('height', isValid ? '0' : '100%');
        };

        this.isDirty = function() {
            var ret = (this.getContentHash() !== this.lastSavedHash);
            return ret;
        };

        this.setNotDirty = function() {
            this.lastSavedHash = this.getContentHash();
        };

        this.setDirty = function() {
            var d = new Date();
            this.lastSavedHash = (d.toLocaleTimeString() + d.getMilliseconds());
        };
        
        this.getContentHash = function() {
            var ret = null;
            return ret;
            //return ret.length + ret;
        };
        
        // Content Status
        this.setStatusSelect = function(contentStatus) {
            if (contentStatus) {
                // select the given status in the drop down
                this.$statusSelect.val(contentStatus);
                this.$statusSelect.trigger('liszt:updated');
            }
            // hide (chosen) select if no status supplied
            this.$statusSelect.closest('.dphidden').toggle(!!contentStatus);
        };
        
        this.setPresentationOptions = function(presentationOptions) {
            var $pres = this.$presentationOptions;
            if (presentationOptions) {
                //var myData = [{id: 1, label: "Test" }];
                var options = presentationOptions.map(function(v, i) {return {id: v[0], label: v[1]};});
                if (!$pres.data().hasOwnProperty('dropdownCheckbox')) {
                    $pres.dropdownCheckbox({
                        data: options,
                        title: "Display",
                        btnClass: 'btn btn-default btn-sm'
                    });
                    $pres.find('button').append('<span class="caret"></span>');
                    $pres.on('mouseenter mouseleave', function($event) {
                        $pres.find('.dropdown-checkbox-content').toggle($event.type === 'mouseenter');
                    });
                }
            }
            // hide (chosen) select if no status supplied
            $pres.closest('.dphidden').toggle(!!presentationOptions && (presentationOptions.length > 0));
        };
        
        // Address / Locations

        this.updateLocations = function(locations) {
            // Update the location drop downs from a list of locations
            // received from the server.
            
            if (locations) {
                var empty = true;
                for (var k in locations) {
                    empty = false;
                    break;
                }
                if (!empty) {
                    locations.sync = this.$contentTypes.dpbsdropdown('getOptions');
                    
                    // save the locations
                    this.locations = locations;
    
                    // only show the available location types
                    var locationTypes = [];
                    for (var j in locations) {
                        locationTypes.push(j);
                    }
                    
                    this.$locationTypes.dpbsdropdown('showOptions', locationTypes);
                    this.$locationTypes.dpbsdropdown('setOption', locationTypes[0]);
                    this.$locationTypes.show();
                } else {
                    // save the locations
                    this.locations = locations;
                }
            }
        };

        this.onSelectLocationType = function(locationType) {
            // update the list of locations
            var htmlstr = '';
            if (this.locations && this.locations[locationType]) {
                $(this.locations[locationType]).each(function (index, value) {
                    // we accept either a list of string or a list or [value,label]
                    var val = value;
                    var label = value;
                    if (value.sort) {
                        val = value[0];
                        label = value[1];
                    }
                    htmlstr += '<option value="'+val+'">'+label+'</option>';
                });
            }
            this.$locationSelect.html(htmlstr);
            this.$locationSelect.trigger('liszt:updated');
            this.$locationSelect.closest('.dphidden').toggle(htmlstr ? true : false);
            if (!htmlstr) this.loadContent();
        };
        
        this.setItemPartid = function(itemPartid) {
            // e.g. '/itemparts/1/'
            this.itemPartid = itemPartid;
        };

        this.getContentAddress = function(locationType, location) {
            return this.panelSet.getBaseAddress() + this.getContentAddressRelative(locationType, location);
        };
        
        this.getContentAddressRelative = function(locationType, location) {
            return this.getContentType() + '/' + (locationType || this.getLocationType()) + '/' + encodeURIComponent((location === undefined) ? this.getLocation() : location) + '/';
        };
        
        this.getContentType = function() {
            return this.contentType;
        };

        this.setLocationTypeAndLocation = function(locationType, location) {
            // this may trigger a content load
            if (this.getLocationType() !== 'sync') {
                this.$locationTypes.dpbsdropdown('setOption', locationType);
                if (this.$locationSelect.val() != location) {
                    this.$locationSelect.val(location);
                    this.$locationSelect.trigger('liszt:updated');
                    this.$locationSelect.trigger('change');
                }
            }
        };
        
        this.getLocationType = function() {
            var ret = 'default';
            if (this.$locationTypes.is(':visible')) {
                ret = this.$locationTypes.dpbsdropdown('getOption');
            }
            return ret;
        };

        this.getLocation = function() {
            var ret = '';
            if (this.$locationSelect.closest('.dphidden').is(':visible')) {
                ret = this.$locationSelect.val();
            }
            return ret;
        };
        
        this.getEditingMode = function() {
            // returns:
            //  undefined: no edit mode at all
            //  true: editing
            //  false: not editing
            return undefined;
        };
        
        this.updateEditingModeIcon = function() {
            if (this.$toggleEdit) {
                var mode = this.getEditingMode();
                
                this.$toggleEdit.toggleClass('dphidden', !((mode === true) || (mode === false)));
                
                this.$toggleEdit.toggleClass('active', (mode === true));
                
                this.$toggleEdit.attr('title', (mode === true) ? 'Preview the text' : 'Edit the text');
                
                this.$toggleEdit.tooltip();
                
                var me = this;
                this.$toggleEdit.on('click', function() {
                    var options = {
                        contentAddress: me.getContentAddressRelative()
                    };
                    me.panelSet.registerPanel(new TextViewer['PanelText'+(mode ? '' : 'Write')](me.$root, me.getContentType(), options));
                    return false;
                });
            }
        };
        
    };

    Panel.prototype.onLinkerTextChanged = function() {
    };
    
    Panel.prototype.onContentLoaded = function(data) {
        //this.setMessage('Content loaded.', 'success');
        // TODO: update the current selections in the location dds
        // TODO: make sure no event is triggered while doing that
        
        this.loadedAddress = this.getContentAddress(data.location_type, data.location);
        this.setNotDirty();
        this.setValid(true);
        
        // update the location drop downs
        this.setLocationTypeAndLocation(data.location_type, data.location);

        // update the status
        this.setStatusSelect(data.content_status);
        
        // update presentation options
        this.setPresentationOptions(data.presentation_options);
        this.applyPresentationOptions();
        
        // send signal to other panels so they can sync themselves
        this.panelSet.onPanelContentLoaded(this, data.location_type, data.location);
        
        //
        if (this.loadOptions && this.loadOptions.stateDict) {
            this.setStateDict(this.loadOptions.stateDict);
            this.loadOptions.stateDict = null;
        }

        // asks PanelSet to update URL
        this.panelSet.onPanelStateChanged(this);
    };
    
    Panel.prototype.onResize = function () {
        // resize content to take the remaining height in the panel
        var height = this.$root.innerHeight() - (this.$content.offset().top - this.$root.offset().top) - this.$statusBar.outerHeight(true);
        this.$content.css('max-height', height+'px');
        this.$content.height(height+'px');
    };

    Panel.create = function(contentType, selector, write, options) {
        var constructor = Panel.getPanelClassFromContentType(contentType, write);
        var error = !constructor;
        if (error) {
            // content type not found, we are nice and instantiate a text
            // we display an error message so user understands why
            constructor = Panel.getPanelClassFromContentType('text');
        }
        var ret = new constructor($(selector), contentType, options);
        if (error) ret.setMessage('Invalid content type ('+contentType+')', 'error');
        return ret;
    };
    
    Panel.prototype.isDownloadable = function() {
        return false;
    };
    
    Panel.createFromState = function(panelState, key, options) {
        // panelState =
        // transcription/locus/1r/
        // transcription/default/
        var metaparts = panelState.split(';');
        var parts = metaparts[0].split('/');
        var contentType = parts[0];
        var stateDict = (metaparts.length > 1) ? metaparts[1]: null;
        
        //Panel.create(Panel.getPanelClassFromContentType(contentType), '.ui-layout-'+key);
        return Panel.create(contentType, '.ui-layout-'+key, false, {contentAddress: metaparts[0], stateDict: stateDict});
    };

    // Returns the Panel class that manages contentType
    // e.g. Translation => <PanelText>
    // contentType can also be panel type
    // e.g. text => <PanelText>
    // Returns null if not found
    Panel.getPanelClassFromContentType = function(contentType, write) {
        // Get panel type from content type
        // lookup in the dropdown of the panel template
        // E.g. Translation => text
        var panelType = $('#text-viewer-panel .dropdown-content-type a[href=#'+contentType.toLowerCase()+']:first').data('class') || contentType;
        
        // Force first letter to uppercase. e.g Text
        panelType = panelType.toUpperCase().substr(0, 1) + panelType.substr(1, contentType.length - 1);

        var ret = 'Panel' + panelType + (write ? 'Write' : '');
        return TextViewer[ret] || null;
    };
    
    Panel.prototype.enablePresentationOptions = function(options) {
        if (options) {
            var $pres = this.$presentationOptions;
            $pres.find('li').each(function() {
                var $li = $(this);
                if (options.indexOf($li.data('id')) > -1) {
                    $li.find('input').trigger('click');
                }
            });
        }
    };

    Panel.prototype.applyPresentationOptions = function() {
        var classes = this.$presentationOptions.dropdownCheckbox("unchecked").map(function(v) { return v.id; }).join(' ');
        this.$content.removeClass(classes);
        classes = this.$presentationOptions.dropdownCheckbox("checked").map(function(v) { return v.id; }).join(' ');
        this.$content.addClass(classes);
    };
    
    Panel.prototype.getState = function() {
        var ret = this.getContentAddressRelative();
        var dict = this.getStateDict();
        ret += Object.keys(dict).reduce(function(pv,cv) {
            if (dict[cv]) {
                return pv + cv + ':' + dict[cv] + ';';
            }
            return pv;
        }, ';');
        return ret;
    };

    Panel.prototype.getListFromPresentationOptions = function() {
        return this.$presentationOptions.dropdownCheckbox("checked").map(function(v) { return v.id; });
    };
    
    Panel.prototype.getStateDict = function() {
        var ret = {};
        //ret.dis = this.$presentationOptions.dropdownCheckbox("checked").map(function(v) { return v.id; }).join(' ');
        ret.dis = (this.getListFromPresentationOptions()).join(' ');
        return ret;
    };

    Panel.prototype.setStateDict = function(stateDict) {
        // dis:abbreviated entry;x:y;a:b c;
        var me = this;
        var args = stateDict.split(';');
        args.map(function(arg) {
            var pair = arg.split(':');
            if (pair.length == 2) {
                me.setStateDictArg(pair[0], pair[1]);
            }
        });
    };
    
    Panel.prototype.setStateDictArg = function(name, value) {
        if (name == 'dis') {
            this.enablePresentationOptions(value.split(' '));
        }
    };

    Panel.prototype.getPanelKey = function() {
        var ret = this.$root.attr('class');
        // ' .ui-layout-pane-north ' -> north
        ret = ret.replace(/.*.ui-layout-pane-(\w+)\b.*/, '$1');
        return ret;
    };

    
    //////////////////////////////////////////////////////////////////////
    //
    // PanelText
    //
    //////////////////////////////////////////////////////////////////////
    var PanelText = TextViewer.PanelText = function($root, contentType, options) {
        TextViewer.Panel.call(this, $root, contentType, 'Text', options);

        this.getEditingMode = function() {
            return false;
        };
        
        this.loadContentCustom = function(loadLocations, address) {
            // load the content with the API
            var me = this;
            this.callApi(
                'loading content',
                address,
                function(data) {
                    if (data.content !== undefined) {
                        me.onContentLoaded(data);
                    } else {
                        //me.setMessage('ERROR: no content received from server.');
                    }
                },
                {
                    'load_locations': loadLocations ? 1 : 0,
                }
            );
        };
        
    };
    
    PanelText.prototype = Object.create(Panel.prototype);
    
    PanelText.prototype.onContentLoaded = function(data) {
        this.$content.addClass('mce-content-body').addClass('preview ct-'+this.getContentType());
        this.$content.html(data.content);
        Panel.prototype.onContentLoaded.call(this, data);
    };

    PanelText.prototype.isDownloadable = function() {
        return true;
    };
    
    
    //////////////////////////////////////////////////////////////////////
    //
    // PanelTextWrite
    //
    //////////////////////////////////////////////////////////////////////
    TextViewer.textAreaNumber = 0;
    
    var PanelTextWrite = TextViewer.PanelTextWrite = function($root, contentType, options) {
        TextViewer.PanelText.call(this, $root, contentType, options);
        
        this.unreadyComponents.push('tinymce');
        
        this.getEditingMode = function() {
            return true;
        };

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
        };

        this.saveContentCustom = function(options) {
            // options:
            // synced, autoMarkup, saveCopy
            var me = this;
            this.callApi(
                'saving content',
                this.loadedAddress,
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
                    'method': 'POST',
                },
                options.synced
            );
        };

        this.initTinyMCE = function() {
            TextViewer.textAreaNumber += 1;
            var divid = 'text-area-' + TextViewer.textAreaNumber;
            this.$content.append('<div id="'+ divid + '"></div>');
            var me = this;

            var options = {
                skin : 'digipal',
                selector: '#' + divid,
                init_instance_callback: function() {
                    me.tinymce = window.tinyMCE.get(divid);
                    me.componentIsReady('tinymce');
                },
                plugins: ['paste', 'code', 'panelset'],
                toolbar: 'psclear undo redo pssave | psconvert | psclause | psClauseSecondary | pslocation | psex pssupplied psdel | code ',
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
                content_css : "/static/digipal_text/viewer/tinymce.css?v=8"
            };
            
            if (this.contentType == 'codicology') {
                options.toolbar = 'psclear undo redo pssave | psh1 psh2 | italic | pshand | pscodparch pscodfol pscodsign pscodperf pscodruling pscodothers | code';
                options.paste_as_text = true;
                options.paste_postprocess = function(plugin, args) {
                    //args.node is a temporary div surrounding the content that will be inserted
                    //console.log($(args.node).html());
                    //$(args.node).html($(args.node).html().replace(/<(\/?)p/g, '<$1div'));
                    //console.log($(args.node).html());
                    //console.log(args.node);
                    
                    // remove all tags except <p>s
                    var content = $(args.node).html();
                    content = content.replace(/<(?!\/?p(?=>|\s.*>))\/?.*?>/gi, '');
                    // remove attributes from all the elements
                    content = content.replace(/<(\/?)([a-z]+)\b[^>]*>/gi, '<$1$2>');
                    // remove &nbsp;
                    content = content.replace(/&nbsp;/gi, '');
                    // remove empty elements
                    content = content.replace(/<[^>]*>\s*<\/[^>]*>/gi, '');
                    $(args.node).html(content);
                };
            }
            
            window.tinyMCE.init(options);
            
        };
        
        this.initTinyMCE();
    };

    PanelTextWrite.prototype = Object.create(PanelText.prototype);

    PanelTextWrite.prototype.onContentLoaded = function(data) {
        this.tinymce.setContent(data.content);
        this.tinymce.focus();
        this.tinymce.undoManager.clear();
        this.tinymce.undoManager.add();
        // We skip PanelText
        Panel.prototype.onContentLoaded.call(this, data);
    };

    //////////////////////////////////////////////////////////////////////
    //
    // PanelImage
    //
    //////////////////////////////////////////////////////////////////////
    
    var PanelImage = TextViewer.PanelImage = function($root, contentType, options) {

        var me = this;
        
        Panel.call(this, $root, contentType, 'Image', options);

        this.loadContentCustom = function(loadLocations, address) {
            // load the content with the API
            var me = this;
            this.callApi(
                'loading image',
                address,
                function(data) {
//                    me.$content.html(data.content).find('img').load(function() {
//                        me.onContentLoaded(data);
//                    });
                    //me.$content.text(data.content);
                    
                    me.onContentLoaded(data);
                },
                {
                    'layout': 'width',
                    'width': me.$content.width(),
                    'height': me.$content.height(),
                    'load_locations': loadLocations ? 1 : 0,
                }
            );
        };
        
        this.applyOpenLayer = function(data) {
            
            if (!data || !data.zoomify_url) {
                // TODO: this is shortcut
                // we may arrive here if selection doesn't return an zoomify url
                // the general message below should only be shown when the
                // list of locations from the server is empty
                this.$content.html('<p>&nbsp;Full resolution image not available.</p>');
                return;
            }
            
            // TODO: think about reusing the OL objects and only changing the underlying image
            // rather than recreating everything each time
            // See http://openlayers.org/en/v3.5.0/examples/zoomify.html
            var me = this;
            
            // empty the content as OL appends to it
            this.$content.html('');
            
            this.map = window.dputils.add_open_layer({
                $target: this.$content,
                image_url: data.zoomify_url,
                image_height: data.height,
                image_width: data.width,
                zoom: this.map ? this.map.getView().getZoom() : 0,
                load_tile_callback: function() {me.loadTile.apply(me, arguments);},
                can_rotate: true,
            });
            
            this.annotator = window.ann3 = new window.AnnotatorOL3(this.map);
            
            this.annotator.addListener(function (e) { me.annotatorEventHandler(e); });

            this.clipImageToTop();

            // Update address bar after panning & zooming
            var view = this.map.getView();
            view.on('change:center', function (event){me.panelSet.onPanelStateChanged(me);});
            view.on('change:resolution', function (event){me.panelSet.onPanelStateChanged(me);});
            view.on('change:rotation', function (event){me.panelSet.onPanelStateChanged(me);});
             
            // tooltip to OL icon
            this.$content.find('.ol-attribution').tooltip({title: 'Viewer by OpenLayers (link to external site)'});
        };

        
        /*
            Open Layer Callback that keep count of the tile loading
            We display a laoding status message to the user
            
            incdec:
                the number of tiles loading (-1 if a new one is loaded)
                'reset': to reset the count (e.g. we load a new image)
            error:
                true  if an error occured during the tile loading
        */
        this.loadTile = function(incdec, error) {
            if (incdec === 'reset') {
                this.tileLoadingCount = 0;
                this.tileLoadError = false;
                return;
            }

            if (error) this.tileLoadError += 1;
            if (incdec !== undefined) {
                this.tileLoadingCount += incdec;
            }
            if (this.tileLoadingCount <= 0) {
                if (this.tileLoadError) {
                    this.setMessage('Error while loading image.', 'error');
                } else {
                    this.setMessage('Image loaded.', 'success');
                }
                this.tileLoadError = 0;
            } else {
                this.setMessage('Loading image...', 'info');
            }
        };

        this.clipImageToTop = function() {
            var map = this.map;
            var view = map.getView();
            var imageFullHeight = view.getProjection().getExtent()[3];
            var viewerFullHeight = map.getSize()[1] * view.getResolution();
            if (viewerFullHeight < imageFullHeight) {
                view.setCenter([view.getCenter()[0], - (viewerFullHeight / 2)]);
            }
        };
        
    };
    
    PanelImage.prototype = Object.create(Panel.prototype);

    PanelImage.prototype.onContentLoaded = function(data) {
        // OL
        this.applyOpenLayer(data);
        
        // annotations
        this.annotator.addAnnotations(data.annotations);
    
        // text-image links
        this.$linker.closest('.dphidden').toggle(true);
        this.resetLinker(data);
        Panel.prototype.onContentLoaded.call(this, data);
    };

    PanelImage.prototype.resetLinker = function(data) {
        // eg.:  "text_elements": [[["", "clause"], ["type", "address"]], [["", "clause"], ["type", "disposition"]], [["", "clause"], ["type", "witnesses"]]]
        var me = this;
        var elements = data.text_elements;

        var htmlstr = '<option value="">Unspecified</option>';
        elements.map(function(el) {
            var key = JSON.stringify(el);
            var label = (el.map(function(attr) { return attr[1]; })).join(' > ');
            htmlstr += '<option value="'+window.dputils.escapeHtml(key)+'">'+label+'</option>';
        });
        this.$linkerText.html(htmlstr);
        this.$linkerText.trigger('liszt:updated');
    };

    PanelImage.prototype.annotatorEventHandler = function(e) {
        var me = this;
        console.log(e);
        
        // update the selection count
        var selections = e.annotator.getSelectedFeatures();
        this.$linkerImage.html('' + selections.getLength());
        
        // set unique client id if no server id exists (unsaved feature)
        selections.forEach(function (feature) {
            if (!feature.getId() && !feature.get('clientid')) {
                feature.set('clientid', '' + (new Date()).getTime() + ':' + Math.floor((Math.random() * 10000)));
            }
        });

        // update the selected text element in the drop down
        var elementid = '';
        selections.forEach(function (feature) {
            elementid = JSON.stringify(feature.get('elementid') || '[]');
        });
        this.$linkerText.val(elementid);
        this.$linkerText.trigger('liszt:updated');
        
        // send the changes to the server
        if (e.action === 'changed' || e.action === 'deleted') {
            this.onAnnotationChanged(e.features, e.action);
        }
    };

    PanelImage.prototype.onLinkerTextChanged = function() {
        var feature = null;
        var elementid = JSON.parse(this.$linkerText.val() || '[]');
        if (elementid) {
            //feature = this.annotator.findFeature({properties: {elementid: JSON.parse(elementid)} });
            feature = this.annotator.getFeatureFromElementId(elementid);
        }
        
        if (!feature) {
            // no feature for this element
            // assign the element to the currently selected feature
            this.annotator.getSelectedFeatures().forEach(function(afeature) {
                afeature.set('elementid', elementid);
                feature = afeature;
            });
        }

        this.annotator.selectFeature(feature);
    
        // send the changes to the server
        //this.onAnnotationChanged();
    };

    PanelImage.prototype.onAnnotationChanged = function(features, action) {
        // Selection in linker has changed: either annotation or text element.
        // Save the new link.
        // features: a list of features to convert into links
        //  if currently selected feature, we can leave the arg undefined
        var me = this;
        
        if (!(features instanceof Array)) {
            features = this.annotator.getSelectedFeatures().getArray();
        }
        
        var links = [];
        (features).map(function(feature) {
            var geojson = JSON.parse(me.annotator.getGeoJSONFromFeature(feature));
            if (action) geojson.action = action;
            var link = [JSON.parse(me.$linkerText.val() || 'null'), geojson];
            links.push(link);
        });
        links = JSON.stringify(links);
        
        console.log(links);
        
        this.callApi(
            'saving text-image link',
            this.loadedAddress,
            function(data) {
                //me.tinymce.setContent(data.content);
                //me.onContentSaved(data);
            },
            {
                'links': links,
                'method': 'POST'
            },
            false
        );
        
    };

    PanelImage.prototype.getStateDict = function() {
        var ret = Panel.prototype.getStateDict.call(this);

        var map = this.map;
        if (map) {
            var view = map.getView();
            var olv = [Math.round(view.getResolution()),
                        Math.round(view.getCenter()[0]),
                        Math.round(view.getCenter()[1]),
                        Math.round(view.getRotation() * 180 / Math.PI)];
            ret.olv = olv.join(',');
        }
        
        return ret;
    };
    
    PanelImage.prototype.onResize = function() {
        Panel.prototype.onResize.call(this);
        if (this.map) {
            this.map.updateSize();
        }
    };
    
    PanelImage.prototype.setStateDictArg = function(name, value) {
        // olv:RES,CX,CY
        if (name === 'olv') {
            var parts = value.split(',');
            var map = this.map;
            var view = map.getView();
            view.setResolution(parseFloat(parts[0]));
            view.setCenter([parseFloat(parts[1]), parseFloat(parts[2])]);
            if (parts.length > 3) {
                view.setRotation(parseFloat(parts[3]) * Math.PI / 180);
            }
        }
    };

    //////////////////////////////////////////////////////////////////////
    //
    // PanelSearch
    //
    //////////////////////////////////////////////////////////////////////
    var PanelSearch = TextViewer.PanelSearch = function($root, contentType, options) {
        TextViewer.Panel.call(this, $root, contentType, 'Search', options);
        
        this.loadContentCustom = function(loadLocations, address) {
            // load the content with the API
            var me = this;
            this.callApi(
                'loading search',
                address,
                function(data) {
                    me.$content.html(data.content);
                    me.onContentLoaded(data);
                    me.$content.find('form').on('submit', function() {
                        var query = me.$content.find('input[name=query]').val();
                        me.search(address, query);
                        return false;
                    });
                },
                {
                    'load_locations': loadLocations ? 1 : 0,
                }
            );
        };
        
        this.search = function(address, query) {
            var me = this;
            this.callApi(
                'searching',
                address,
                function(data) {
                    me.$content.html(data.content);
                    me.$content.find('form').on('submit', function() {
                        var query = me.$content.find('input[name=query]').val();
                        me.search(address, query);
                        return false;
                    });
                    me.$content.find('a[data-location-type]').on('click', function() {
                        me.panelSet.onPanelContentLoaded(me, 'entry', $(this).attr('href'));
                        //this.panelSet.onPanelContentLoaded(this, data.location_type, data.location);
                        return false;
                    });
                },
                {
                    'query': query,
                }
            );
        };
        
    };
    
    PanelSearch.prototype = Object.create(Panel.prototype);
    
    //////////////////////////////////////////////////////////////////////
    //
    // PanelXmlelement
    //
    //////////////////////////////////////////////////////////////////////
    var PanelXmlelementWrite = TextViewer.PanelXmlelementWrite = function($root, contentType) {
        TextViewer.Panel.call(this, $root, contentType);
    };
        
    //////////////////////////////////////////////////////////////////////
    //
    // Utilities
    //
    //////////////////////////////////////////////////////////////////////
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
        if (requestData && requestData.method) {
            getData.type = requestData.method;
            delete requestData.method;
        }
        var ret = $.ajax(getData);
        
        return ret;
    };
    
    TextViewer.getStrFromTime = function(date) {
        date = date || new Date();
        var parts = [date.getHours(), date.getMinutes(), date.getSeconds()];
        for (var i in parts) {
            if ((i > 0) && (parts[i] < 10)) parts[i] = '0' + parts[i];
        }
        return parts.join(':');
    };

    // These are external init steps for JSLayout
    function initLayoutAddOns() {
        //
        //  DISABLE TEXT-SELECTION WHEN DRAGGING (or even _trying_ to drag!)
        //  this functionality will be included in RC30.80
        //
        $.layout.disableTextSelection = function(){
            var $d  = $(document),
                    s   = 'textSelectionDisabled',
                    x   = 'textSelectionInitialized'
            ;
            if ($.fn.disableSelection) {
                if (!$d.data(x)) // document hasn't been initialized yet
                    $d.on('mouseup', $.layout.enableTextSelection ).data(x, true);
                if (!$d.data(s))
                    $d.disableSelection().data(s, true);
            }
        };
        $.layout.enableTextSelection = function(){
            var $d  = $(document),
                    s   = 'textSelectionDisabled';
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
    }
    
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
    
    initLayoutAddOns();
    
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", window.dputils.getCookie('csrftoken'));
            }
        }
    });
    
}( window.TextViewer = window.TextViewer || {}, jQuery ));
