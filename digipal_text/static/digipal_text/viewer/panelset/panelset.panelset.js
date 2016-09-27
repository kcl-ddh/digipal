//////////////////////////////////////////////////////////////////////
//
// PanelSet
//
// Represents and manages a set of Panels.
// It deals with adding/removing panels to the frame, syncing their
// locations, reflecting state changes into the browser address bar,
// managing the visual arrangement of the panels on screen.
//
//////////////////////////////////////////////////////////////////////
(function(TextViewer, $, undefined) {

    var PanelSet = TextViewer.PanelSet = function($root) {

        this.uuid = window.dputils.get_uuid();
        this.panels = [];
        this.$root = $root;
        this.$panelset = null;
        this.layout = null;
        this.$messageBox = null;
        this.isReady = false;
        this.panelSet = this;
        this.userIsStaff = false;

        this.registerPanel = function(panel) {
            if (!panel) return;
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

        this.syncWithPanel = function(panel) {
            // sync other panels with <panel>
            var parts = panel.getLoadedAddressParts();
            //this.onPanelContentLoaded(panel, panel.getLocationType(), panel.getLocation());
            this.onPanelContentLoaded(panel, parts.locationType, parts.location);
        };

        this.onPanelContentLoaded = function(panel, locationType, location) {
            this.syncWith(panel.uuid, panel.getContentType(), locationType, panel.getSurroundingLocations(locationType, location), panel.getSubLocationUnresolved(), panel);
        };

        this.syncWith = function(panelUUID, contentType, locationType, surroundingLocations, subLocation, panel) {
            // panel is optional
            if (locationType !== 'sync') {
                //console.log('syncWith ' + contentType);
                // sync other panels with <panel>
                for (var i in this.panels) {
                    this.panels[i].syncLocationWith(panelUUID, contentType, locationType, surroundingLocations, subLocation, panel);
                }
            }
        };

        this.syncPanel = function(panel) {
            //console.log('syncPanel ' + panel.contentType);
            // sync the given panel (with others)
            for (var i in this.panels) {
                // TODO: this won't work when panels[i] is also synced.
                // One option is to trigger a onPanelContentLoaded on that panel
                // but info only in loadedAddress
                // Or we use a getLoadedLocationType() returning the real LT
                // but surrounding locations won't work.
                var parts = this.panels[i].getLoadedAddressParts();
                if (parts) {
                    panel.syncLocationWith(this.panels[i].uuid, this.panels[i].getContentType(), parts.locationType, parts.location, this.panels[i].getSubLocationUnresolved(), this.panels[i]);
                }
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

            // share last URL with other text viewers
            if (panel.loadedAddress) {
                localStorage.textViewer = JSON.stringify({
                    'url': window.location.href,
                    'uuid': this.uuid,
                    'panelUUID': panel.uuid,
                    'contentType': panel.getContentType(),
                    'address': panel.loadedAddress,
                });
            }
        };

        this.setStateFromUrl = function(defaultState) {
            // we merge the defaultState with the state from the Query String
            var args = $.extend(this.getQSArgs(defaultState), this.getQSArgs(window.location.href, true));
            var state = Object.keys(args).reduce(function(pv,cv) {
                return pv + cv + '=' + args[cv] + '&';
            }, '?');
            this.setState(state);
        };

        this.setUserIsStaff = function(isUserStaff) {
            this.userIsStaff = isUserStaff;
        };

        this.isUserStaff = function() {
            return this.userIsStaff;
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
                        ret[arg[0]] = TextViewer.urldecode(arg[1]);
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
            //var height = window.dputils.get_elastic_height(this.$root);
            //this.$panelset.css('height', Math.floor(height - this.$messageBox.outerHeight(true)));
            var height = window.dputils.get_elastic_height(this.$panelset, 10, 0, 1);
            this.$panelset.css('height', height);
            this.$panelset.css('max-height', height);

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

        this.getPanelAddressParts = function(address) {
            // IN: '/digipal/manuscripts/1/texts/location/locus/290r/'
            //OUT: {contentType: location, locationType: locus, location: 290r}
            if (!address) return null;
            var ret = {contentType: '', locationType: 'locus', location: '1r'};

            var baseAddress = this.getBaseAddress();
            if (address.substring(0, baseAddress.length) !== baseAddress) return ret;
            address = address.substring(baseAddress.length);
            // 'translation/locus/271r/'
            var parts = address.split('/').map(function(p) { return decodeURIComponent(p);});
            if (parts.length == 4) {
                ret.contentType = parts[0];
                ret.locationType = parts[1];
                ret.location = parts[2];
            }

            return ret;
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

            window.addEventListener('storage', function(event) {
                // TODO: re-enable this once sync is fixed and UI has a way to
                // let user actively choose cross window sync
                // Bug = EXON TOC, open one location in a new tab
                // then another location a new tab, now both tabs are syncing
                // for ever.
                return;

                // Syncing location following a change made in another browser window
                if (event.key !== 'textViewer') return;
                var data = JSON.parse(event.newValue);
                if (data.uuid === me.uuid) return;
                var baseAddress = me.getBaseAddress();
                if (!data.address || data.address.substring(0, baseAddress.length) !== baseAddress) return;

                var parts = me.getPanelAddressParts(data.address);

                if (parts.contentType) {
                    me.syncWith(data.panelUUID, data.contentType, parts.locationType, parts.location);
                }
            });
        };

        this.ready = function() {
            for (var i in this.panels) {
                this.panels[i].componentIsReady('panelset');
            }
            this.isReady = true;
            this.initEvents();
        };

    };

}( window.TextViewer = window.TextViewer || {}, jQuery ));
