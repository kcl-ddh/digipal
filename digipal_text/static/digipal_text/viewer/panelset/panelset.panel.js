//
// Panel: an ABSTRACT Panel managed by the PanelSet
//
// This is the base class for all specific panel types (e.g. text, image).
// It provides some basic behaviour for auto-resizing, loading/saving content.
// It displays and manages: a tool bar at the top, content in the middle and
// status bar at the bottom.
// The content can be anything and specifics are dealt with subclasses.
//
/////////////////////////////////////////////////////////////////////////
(function(TextViewer, $, undefined) {

    var Panel = TextViewer.Panel = function($root, contentType, panelType, options) {
        this.uuid = window.dputils.get_uuid();

        this.$root = $root;
        this.$content = $('<div></div>');

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
        
        this.attributionShort = '';
        
        //  undefined: no edit mode at all
        //  true: editing
        //  false: not editing
        this.editingMode = undefined;

        // The address of the last successfully loaded content.
        // e.g. /digipal/manuscripts/1/texts/translation/locus/2r/
        //
        // Note that this may be more specific than locationType and
        // location drop downs. For instance if the panel is synced
        // we could have locationType=sync, location=image but the
        // loadedAddress is the actual address of the content.
        //
        // It is CRUCIAL that this is null when the displayed content
        // doesn't reflect the location drop downs (e.g. not loaded yet
        // being loaded, error loading) otherwise it may cause data
        // loss on the server because of the automated save.
        this.loadedAddress = null;

        this.createUserInterface();

        var me = this;

        // Enabled location selectors
        TextViewer.Located.call(this, $root);

        // METHODS

        this.callApi = function(title, url, onSuccess, requestData, synced) {
            var me = this;

            this.setMessage(title+'...', 'info');

            // pre-process requestData
            if (requestData) {
                if (requestData.sub_location && requestData.sub_location.length) {
                    requestData.sub_location = JSON.stringify(requestData.sub_location);
                } else {
                    delete requestData.sub_location;
                }
                if (requestData.load_locations) {
                    requestData.load_locations = 1;
                } else {
                    delete requestData.load_locations;
                }
            }

            // request event handlers
            var onComplete = function(jqXHR, textStatus) {
                if (textStatus !== 'success') {
                    me.setMessage('Error while '+title+' (status: '+textStatus+')', 'error');
                }
            };
            var onSuccessWrapper = function(data, textStatus, jqXHR) {
                var status_message = ''; 
                me.attributionShort = data.attribution_short;
                
                data.status = data.status || 'success';
                status_message = data.message || 'done ('+title+').';;
                if (data.locations) {
                    me.updateLocations(data.locations, data.is_fake);
                }
                if (data.status === 'success') {
                    onSuccess(data, textStatus, jqXHR);
                    if (data.attribution_short) {
                        status_message = data.attribution_short;
                    }
                }
                me.setMessage(status_message, data.status);
            };

            var ret = null;
            if (!this.callApiFake(url, onSuccessWrapper)) {
                ret = TextViewer.callApi(url, onSuccessWrapper, onComplete, requestData, synced);
            }

            return ret;
        };

        this.callApiFake = function(url, onSuccessWrapper) {
            return false;
            // prevents unnecessary server request for 'sync' location
            // Disabled as it causes issues with display settings from URL
            // being ignored and locations drop down being empty.
            // TODO: Need more work.
            var ret = false;

            var parts = this.panelSet.getPanelAddressParts(url);
            if (parts) {
                // {contentType: "transcription", locationType: "sync", location: "location"}
                if (parts.locationType == 'sync') {
                    var locations = {};
                    locations[parts.locationType] = parts.location;
                    var data = {
                        location_type: parts.locationType,
                        location: parts.location,
                        locations: locations,
                        content: 'Syncing...',
                        message: 'Syncing...',
                        is_fake: 1
                    };
                    onSuccessWrapper(data);
                    ret = true;
                }
            }

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
            if (this.$statusBar) {
                this.$statusBar.find('.message').html(message).removeClass('message-success message-info message-warning message-error').addClass('message-'+status);
                var timestamp = '';
                if (me.editingMode == true) {
                    timestamp = TextViewer.getStrFromTime(new Date());
                }
                this.$statusBar.find('.time').html(timestamp);
            }
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

        this.loadContent = function(loadLocations, address, subLocation) {
            // Important, the argument is ignored, we load if we don't have locations
            loadLocations = this.locationsAreUnloaded;

            subLocation = subLocation || [];

            //console.log(''+this.contentType+' : loadContent('+address+', '+subLocation+')');

            if (!address && (this.getLocationType() == 'sync')) {
                this.panelSet.syncPanel(this);
                return;
            }

            address = address || this.getContentAddress();

            if (this.loadedAddress != address || !this.moveToSubLocation(subLocation)) {
                // make sure no saving happens from now on
                // until the content is loaded
                if (this.loadingAddress !== address) {
                    //console.log('LOAD CONTENT');
                    this.setValid(false);
                    this.loadedAddress = null;
                    this.loadingAddress = address;
                    this.loadContentCustom(loadLocations, address, subLocation);
                } else {
                    //console.log('STOPPED CONCURRENT LOAD '+address);
                }
            }
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
            //this.$statusSelect.closest('.dphidden').toggle(!!contentStatus);
            TextViewer.unhide(this.$statusSelect, !!contentStatus);
        };

        this.arePresentationOptionsDefined = function() {
            var $pres = this.$presentationOptions;
            return ($pres && $pres.length && $pres.data().hasOwnProperty('dropdownCheckbox'));
        };

        // Address / Locations

        this.setItemPartid = function(itemPartid) {
            // e.g. '/itemparts/1/'
            this.itemPartid = itemPartid;
        };

        // Returns a web path from (locationType, location)  
        // If no argument, from locationType and location drop downs
        // Note that this can be /sync/...
        // This is different from the loaded address
        // see getLoadedAddress()
        this.getContentAddress = function(locationType, location) {
            return this.panelSet.getBaseAddress() + this.getContentAddressRelative(locationType, location);
        };

        this.getContentAddressRelative = function(locationType, location) {
            return this.getContentType() + '/' + (locationType || this.getLocationType()) + '/' + encodeURIComponent((location === undefined) ? this.getLocation() : location) + '/';
        };

        this.getContentType = function() {
            return this.contentType;
        };

    };

    Panel.prototype = Object.create(TextViewer.Located.prototype);

    Panel.prototype._ready = function() {
        var me = this;

        // Remove editing rights is user not logged in
        if (!this.panelSet.isUserStaff()) this.editingMode = undefined;
        this.initEditingModeIcon();

        if (this.$contentTypes) {
            this.$contentTypes.dpbsdropdown({
                onSelect: function($el, key, $a) {
                    // the user has selected another view/content type -> we replace this panel
                    //var options = {contentAddress: key+'/sync/location/'};
                    var options = {contentAddress: key+'/'+me.getLocationType()+'/'+me.getLocation()+'/'};
                    me.panelSet.registerPanel(new TextViewer['Panel'+$a.data('class')](me.$root, key, options));
                },
            });
            this.$contentTypes.dpbsdropdown('setOption', this.contentType, true);
        }

        this.loadContent(true, this.loadOptions.contentAddress ?  this.panelSet.getBaseAddress() + this.loadOptions.contentAddress : undefined);

        this.onResize();

        if (this.$statusSelect) {
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
        }

        if (this.$downloadFormats) {
            TextViewer.unhide(this.$downloadFormats, this.isDownloadable());
        }

        if (this.$linkerText) {
            this.$linkerText.on('change', function() {
                me.onLinkerTextChanged();
            });
        }

        if (this.$content) {
            setInterval(function() {
                me.saveContent();
            }, 2500);
        }
    };
    
    Panel.prototype.onSelectDownloadFormat = function(format) {
        var me = this;
        //me.onLocationChanged();
        // http://localhost/digipal/manuscripts/1/texts/codicology/whole/?jx=1&load_locations=0&ds=&format=html&ds=locus
        //var url = me.getContentAddress('whole', '');
        var url = me.getLoadedAddress();
        url += '?ds=' + (me.getListFromPresentationOptions()).join(',')+'&format='+format;
        window.open(url, '_blank');
    };
    		
    Panel.prototype.createUserInterface = function() {
        // clone the panel template
        var $panelHtml = $('#text-viewer-panel').clone();
        $panelHtml.removeAttr('id');
        $panelHtml.addClass('ct-'+this.contentType);
        $panelHtml.addClass('pt-'+this.panelType.toLowerCase());
        this.$root.html($panelHtml);

        // We create bindings for all the html controls on the panel
        this.$contentTypes = this.$root.find('.dropdown-content-type');

        this.$linker = this.$root.find('.linker');
        this.$linkerImage = this.$linker.find('.linker-image');
        this.$linkerText = this.$linker.find('select[name=linker-text]');

        TextViewer.upgrade_selects(this.$root);

        this.$content = this.$root.find('.panel-content');
        this.$statusBar = this.$root.find('.status-bar');

        this.$statusSelect = this.$root.find('select[name=status]');
        this.$presentationOptions = this.$root.find('.presentation-options');

        this.$toggleEdit = this.$root.find('.toggle-edit');

        //this.$downloadButton = this.$root.find('.action-download');
        this.$downloadFormats = this.$root.find('.dropdown-download-formats');
        var me = this;
        this.$downloadFormats.dpbsdropdown({
            onSelect: function($el, key) { me.onSelectDownloadFormat(key); },
            selectIfSame: true,
        });
        
        this.$root.find('[data-toggle=tooltip]').tooltip();
    };

    Panel.prototype.setPresentationOptions = function(presentationOptions) {
        var $pres = this.$presentationOptions;
        if (presentationOptions) {
            //var myData = [{id: 1, label: "Test" }];
            var options = presentationOptions.map(function(v, i) {return {id: v[0], label: v[1]};});
            if (!this.arePresentationOptionsDefined()) {
                var me = this;
                $pres.dropdownCheckbox({
                    data: options,
                    title: 'Display',
                    btnClass: 'btn btn-default btn-sm'
                });
                $pres.find('button').html('<span class="glyphicon glyphicon-eye-open"></span>&nbsp;<span class="caret"></span>');
                $pres.on('mouseenter mouseleave', function($event) {
                    $pres.find('.dropdown-checkbox-content').toggle($event.type === 'mouseenter');
                });

                $pres.on('change', 'input[type=checkbox]', function() {
                    me.applyPresentationOptions();
                    me.panelSet.onPanelStateChanged(me);
                });
            }
        }
        // hide (chosen) select if no status supplied
        TextViewer.unhide($pres, !!presentationOptions && (presentationOptions.length > 0));
    };

    Panel.prototype.loadContentCustom = function(loadLocations, address, subLocation) {
        // NEVER CALL THIS FUNCTION DIRECTLY
        // ONLY loadContent() can call it
        throw "loadContentCustom() must be overridden in the concrete class";
        this.$content.html('Generic Panel Content');
        this.onContentLoaded();
    };

    Panel.prototype.onLinkerTextChanged = function() {
    };

    Panel.prototype.scrollToTopOfContent = function(data) {
        if (this.$content) this.$content.scrollTop(0);
    };

    Panel.prototype.onContentLoaded = function(data) {
        //console.log(''+this.contentType+': onContentLoaded - BEGIN');

        this.scrollToTopOfContent();

        //this.setMessage('Content loaded.', 'success');
        this.loadedAddress = this.getContentAddress(data.location_type, data.location);
        this.setNotDirty();
        this.setValid(true);

        // reset the sublocation because the content has changed
        this.resetSubLocation();

        // update the location drop downs
        this.setLocationTypeAndLocation(data.location_type, data.location);

        // update the status
        this.setStatusSelect(data.content_status);

        // update presentation options
        this.setPresentationOptions(data.presentation_options);
        this.applyPresentationOptions();

        // send signal to other panels so they can sync themselves
        //this.panelSet.onPanelContentLoaded(this, data.location_type, data.location);

        //
        if (this.loadOptions && this.loadOptions.stateDict) {
            this.setStateDict(this.loadOptions.stateDict);
            this.loadOptions.stateDict = null;
        }

        // move to the new sublocation
        if (data.sub_location) this.moveToSubLocation(data.sub_location);

        // asks PanelSet to update URL
        this.panelSet.onPanelStateChanged(this);
        //console.log(''+this.contentType+': onContentLoaded - END');

        // send signal to other panels so they can sync themselves
        this.panelSet.onPanelContentLoaded(this, data.location_type, data.location);

        // allows other addresses to be loaded
        this.loadingAddress = null;
    };

    Panel.prototype.onResize = function () {
        if (this.$statusBar) {
            // resize content to take the remaining height in the panel
            var height = Math.floor(this.$root.innerHeight() - (this.$content.offset().top - this.$root.offset().top) - this.$statusBar.outerHeight(true));
            this.$content.css('max-height', height+'px');
            this.$content.height(height+'px');
        }
    };

    Panel.create = function(contentType, selector, write, options) {
        var constructor = Panel.getPanelClassFromContentType(contentType, write);
        var error = !constructor;
        if (error) {
            // content type not found, we are nice and instantiate a text
            // we display an error message so user understands why
            constructor = Panel.getPanelClassFromContentType('text');
        }
        var ret = null;
        var $root = $(selector);
        if ($root.size() > 0) {
            ret = new constructor($root, contentType, options);
        }
        if (error && ret) ret.setMessage('Invalid content type ('+contentType+')', 'error');
        return ret;
    };

    Panel.prototype.isDownloadable = function() {
        return false;
    };

    Panel.createFromState = function(panelState, key, options) {
        // panelState =
        // transcription/locus/1r/;ds=abbrv
        // transcription/default/
        var metaparts = (panelState || '').split(';');
        var address = metaparts.shift();
        var parts = address.split('/');
        var contentType = (parts.length > 0) ? parts[0] : '';
        var stateDict = metaparts.join(';');

        //Panel.create(Panel.getPanelClassFromContentType(contentType), '.ui-layout-'+key);
        return Panel.create(contentType, '.ui-layout-'+key, false, {contentAddress: address, stateDict: stateDict});
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
        var contentTypeKey = contentType.toLowerCase();
        if (contentTypeKey.match(/[^-0-9a-z_]/gi)) return null;
        var panelType = $('#text-viewer-panel .dropdown-content-type a[href=#'+contentTypeKey+']:first').data('class') || contentType;

        // Force first letter to uppercase. e.g Text
        panelType = panelType.toUpperCase().substr(0, 1) + panelType.substr(1, contentType.length - 1);

        var ret = 'Panel' + panelType + (write ? 'Write' : '');
        return TextViewer[ret] || null;
    };

    Panel.prototype.enablePresentationOptions = function(options) {
        if (options) {
            var $pres = this.$presentationOptions;
            if (this.arePresentationOptionsDefined()) {
                $pres.find('li').each(function() {
                    var $li = $(this);
                    if (options.indexOf($li.data('id')) > -1) {
                        $li.find('input:not(:checked)').trigger('click');
                    }
                });
            }
        }
    };

    Panel.prototype.applyPresentationOptions = function() {
        if (this.arePresentationOptionsDefined()) {
            var classes = this.$presentationOptions.dropdownCheckbox("unchecked").map(function(v) { return v.id; }).join(' ');
            this.$content.removeClass(classes);
            classes = this.$presentationOptions.dropdownCheckbox("checked").map(function(v) { return v.id; }).join(' ');
            this.$content.addClass(classes);
        }
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
        ret = [];
        if (this.arePresentationOptionsDefined()) {
            ret = this.$presentationOptions.dropdownCheckbox("checked").map(function(v) { return v.id; });
        }
        return ret;
    };

    Panel.prototype.getStateDict = function() {
        var ret = {};
        //ret.dis = this.$presentationOptions.dropdownCheckbox("checked").map(function(v) { return v.id; }).join(' ');
        ret.dis = (this.getListFromPresentationOptions()).join(' ');
        var subl = this.getSubLocationUnresolved();
        if (subl && subl.length) ret.subl = JSON.stringify(subl);
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
        if (name == 'subl') {
            //this.enablePresentationOptions(value.split(' '));
            this.moveToSubLocation(JSON.parse(value));
        }
    };

    Panel.prototype.getPanelKey = function() {
        var ret = this.$root.attr('class');
        // ' .ui-layout-pane-north ' -> north
        ret = ret.replace(/.*.ui-layout-pane-(\w+)\b.*/, '$1');
        return ret;
    };

    Panel.prototype.onLocationChanged = function() {
        this.loadContent();
    };
    
    // EDITING MODE

    Panel.prototype.getEditingMode = function() {
        return this.editingMode;
    };

    Panel.prototype.setEditingMode = function(mode) {
        if (this.editingMode !== mode) {
            this.editingMode = mode;
            this.updateEditingModeIcon();
            this.onChangedEditingMode(mode);
        }
    }

    Panel.prototype.initEditingModeIcon = function() {
        if (this.$toggleEdit) {
            this.updateEditingModeIcon();

            var me = this;
            this.$toggleEdit.on('click', function() {
                me.setEditingMode(!me.getEditingMode());
            });
        }
    };

    Panel.prototype.updateEditingModeIcon = function() {
        if (this.$toggleEdit) {
            var mode = this.getEditingMode();
            
            TextViewer.unhide(this.$toggleEdit, ((mode === true) || (mode === false)));
    
            this.$toggleEdit.toggleClass('active', (mode === true));
    
            this.$toggleEdit.attr('data-original-title', (mode === true) ? 'Stop editing' : 'Start editing');
        }
    }

    Panel.prototype.onChangedEditingMode = function(mode) {
        // By default we replace this panel with another of the same type 
        // but for the specific Editing Mode. E.g. PanelText -> PanelTextWrite
        // the new panel is loaded with the same addres.
        var options = {
            contentAddress: this.getContentAddressRelative(),
        };
        var panel = Panel.create(this.contentType, this.$root, this.getEditingMode(), options);
        this.panelSet.registerPanel(panel);
        return false;
    };

}( window.TextViewer = window.TextViewer || {}, jQuery ));

