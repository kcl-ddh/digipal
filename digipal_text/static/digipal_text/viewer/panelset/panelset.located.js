//////////////////////////////////////////////////////////////////////
//
// Located
//
// For location aware objects (e.g. Panel)
// Manages the internal location and the associated UI (drop downs)
// A position in a document is made of at least two parts:
// (locationType, location), e.g. ('locus', '2r') or ('entry', '2a3')
// An address is a string representation of a complete position,
// e.g. locus/2r/, or translation/locus/2r/
//
// TODO: many dependencies with Panel class that need to disappear.
// e.g. rely on Panel methods and properties.
//
//////////////////////////////////////////////////////////////////////
(function(TextViewer, $, undefined) {

    var Located = TextViewer.Located = function($root) {
        var me = this;

        this.locationsAreUnloaded = true;

        this.resetSubLocation();

        this.$locationTypes = $root.find('.dropdown-location-type');
        this.$locationSelect = $root.find('select[name=location]');

        TextViewer.upgrade_selects($root);

        this.$locationTypes.dpbsdropdown({
            onSelect: function($el, key) { me.onSelectLocationType(key); },
        });

        this.$locationSelect.on('change', function() {
            me.onLocationChanged();
        });

        $root.find('.btn-page-nav').on('click', function() {
            me.onNextPage($(this).hasClass('btn-page-previous') ? -1 : +1);
        });

    };

    Located.prototype.onNextPage = function(offset) {
        this.moveBy(offset);
    };

    // Move location by <offset> units
    Located.prototype.moveBy = function(offset) {
        this.setLocationTypeAndLocation(this.getLocationType(), this.getLocationWithOffset(null, null, offset));
    };

    Located.prototype.getSurroundingLocations = function(locationType, location) {
        var ret = {};
        var me = this;
        [-1,0,1].map(function(offset) { ret[offset] = me.getLocationWithOffset(locationType, location, offset); });
        return ret;
    };

    Located.prototype.onLocationChanged = function() {
        // to be overridden
    };

    Located.prototype.getLoadedAddress = function() {
        return this.loadedAddress;
    };

    Located.prototype.getLoadedAddressParts = function() {
        //OUT: {contentType: location, locationType: locus, location: 290r}
        return this.panelSet.getPanelAddressParts(this.loadedAddress);
    };

    // Returns the selected Location Type from the drop down
    Located.prototype.getLocationType = function() {
        var ret = this.$locationTypes.dpbsdropdown('getOption') || 'default';
        return ret;
    };

    // Returns the selected Location from the location drop down
    // e.g. '2r'
    // Returns empty string if not found
    // This is the full value, so it may include the offset, e.g. 'location+1'
    Located.prototype.getLocation = function() {
        var ret = '';
        if (TextViewer.getCtrl(this.$locationSelect).closest('.dphidden,.dpunhidden').hasClass('dpunhidden')) {
            ret = this.$locationSelect.val();
        }
        return ret;
    };

    // e.g. ('locus', '2r', 2) => '3r'
    // any argument can be null, default values are (current LocType, current Location, 0)
    Located.prototype.getLocationWithOffset = function(locationType, location, offset) {
        var ret = location || this.getLocation();

        locationType = locationType || this.getLocationType();

        if (this.locations) {
            var locations = this.locations[locationType];
            if (locations) {
                var idx = locations.indexOf(ret);
                if (idx >= 0) {
                    idx += (offset || 0);
                    if (idx >= 0 && idx < locations.length) {
                        ret = locations[idx];
                    }
                }
            }
        }
        return ret;
    };

    // Same as getLocation() but without the offset (if any)
    // E.g. if the location type is 'sync' and location is 'location+1'
    // the function returns 'location'
    Located.prototype.getLocationWithoutOffset = function() {
        var info = this.getLocationParts();
        return info.location;
    };

    // Returns the location without offset and the offset
    // E.g. if the location type is 'sync' and location is 'X+1'
    // the function returns {'location': 'X', 'offset': 1}
    Located.prototype.getLocationParts = function() {
        // if location is 'X+1', returns {location: 'X', offset: 1}
        var ret = {location: this.getLocation(), offset: 0};

        if (ret.location) {
            var offset = ret.location.match(/[+-]\d+$/g);
            if (offset) {
                offset = offset[0];
                ret.offset = parseInt(offset);
                ret.location = ret.location.substring(0, ret.location.length - offset.length);
            }
        }

        return ret;
    };

    Located.prototype.setLocationTypeAndLocation = function(locationType, location) {
        // this may trigger a content load
        if (this.getLocationType() !== 'sync') {
            this.$locationTypes.dpbsdropdown('setOption', locationType);
            if (this.getLocation() != location) {
                this.$locationSelect.val(location);
                this.$locationSelect.trigger('liszt:updated');
                this.$locationSelect.trigger('change');
            }
        }
    };

    Located.prototype.updateLocations = function(locations, fake) {
        // Update the location drop downs from a list of locations
        // received from the server.

        if (locations) {
            var empty = true;
            for (var k in locations) {
                empty = false;
                break;
            }
            if (!empty) {
                // See Active Collab VisigtohicPal #13
                var canBeSynced = false;

                for (var j in locations) {
                    if (locations[j].length > 0) {
                        canBeSynced = true;
                        break;
                    }
                }
                
                if (canBeSynced && this.$contentTypes) {
                    locations.sync = [['location', 'Top Location'], ['location+1', 'Top location (next)'], ['location-1', 'Top location (previous)']];
                    locations.sync = locations.sync.concat(this.$contentTypes.dpbsdropdown('getOptions'));
                }

                // save the locations
                this.locations = locations;

                // only show the available location types
                var locationTypes = [];
                for (var j in locations) {
                    locationTypes.push(j);
                }

                // Note that we only SHOW the given location types, we don't
                // add new entries in the drop down
                this.$locationTypes.dpbsdropdown('showOptions', locationTypes);
                if (locationTypes.length > 0) {
                    this.$locationTypes.dpbsdropdown('setOption', locationTypes[0]);
                }
                //TextViewer.unhide(this.$locationTypes, 1);
                TextViewer.unhide(this.$locationTypes, (locationTypes.length > 1));
            } else {
                // save the locations
                this.locations = locations;
            }
            this.locationsAreUnloaded = fake;
        }
    };

    Located.prototype.onSelectLocationType = function(locationType) {
        // update the list of locations
        var me = this;
        var htmlstr = '';
        var locationsCount = 0;
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
                locationsCount += 1;
            });
        }
        this.$locationSelect.html(htmlstr);
        // refresh the chosen dropdown
        this.$locationSelect.trigger('liszt:updated');

        // hide the drop down if no option
        TextViewer.unhide(this.$locationSelect, htmlstr ? true : false);

        // don't auto-hide locations if not synced
        this.$root.find('.location-buttons').toggleClass('dpauto-hide', (locationType === 'sync'));

        // hide prev/next buttons if only one location available
        TextViewer.unhide(this.$root.find('.btn-page-nav.enabled'), (locationsCount > 1));

        // disable drop down appearance if only one option
        TextViewer.getCtrl(this.$locationSelect).toggleClass('disabled', (locationsCount < 2));

        //             if (!htmlstr) { this.loadContent(); }
        //             else
        //             {
        //                 // force a load bc the location has changed
        //                 // This will create infinite event recursion on startup:
        //                 // this.loadContent();
        //                 // this.loadContent(false, this.getContentAddress(locationType));
        //                 window.setTimeout(function() { me.$locationSelect.trigger('change'); }, 0);
        //             };
        // Try to reload bc the location has changed.
        // Allows synced panels to sync on page load.
        // Allows user change of LT to trigger reload b/c (LT,L) is different
        // Note that no request is sent if address hasn't changed.
        // Also note that this will reset the sublocation!
        //
        
        // GN: 18-20 Aug 2017: AC MOA #20
        // Why this condition was designed in the first place?
        // If &above=location/default;subl:... on page load then when we 
        // receive default loc from server => updateLocations() calls
        // setOption on the LT dropdown and this in turns call this function
        // the trigger below resets the sublocation and it's never used when
        // other panels later sync with this one...
        // The logic is really convoluted but it's hard to make it work and test 
        // on all possible use cases from various projects. So we end up with this
        // solution below.
        // TODO: check if updateLocations() really need to call setOption
        //
        // if ((locationType === 'sync') || (this.loadedAddress)) {
        //
        // Relaxed condition to fix the following bug:
        // If you sync a text to 1v and there is no 1v, this.loadedAddress is null.
        // Then user select Whole but that won't load the whole text because this.loadAddress.
        //
        if ((locationType === 'sync') || (!this.locationsAreUnloaded)) {
            window.setTimeout(function() { me.$locationSelect.trigger('change'); }, 0);
        }
    };

    // SubLocation: a reference within the content
    // e.g. entry 1a1 within page 1r
    // e.g. 'address' clause within whole text or entry 1a1
    // it is a location at a deeper level than the address
    // ALWAYS return a NON EMPTY array
    Located.prototype.getSubLocation = function() {
        var ret = this.subLocation;

        if (ret.length <= 0) {
            ret = this.getSubLocationFromLocaton();
        }

        return ret;
    };

    // Can return an empty array if the sublocation is not more specific
    // than the location
    Located.prototype.getSubLocationUnresolved = function() {
        return this.subLocation;
    };

    Located.prototype.getSubLocationFromLocaton = function() {
        // create a subLocation from the location
        return [['','location'], ['loctype', this.getLocationType()], ['@text', this.getLocation()]];
    };

    Located.prototype.setSubLocation = function(subLocation) {
        // clone and set the location
        var subLocationOld = JSON.stringify(this.subLocation || []);
        var subLocationNew = JSON.stringify(subLocation || []);

        if (subLocationOld != subLocationNew) {
            this.resetSubLocation(subLocation);

            if (this.panelSet) {
                // state has changed
                this.panelSet.onPanelStateChanged(this);
                // dispatch the element we are on
                this.panelSet.syncWithPanel(this);
            }
        }
    };

    Located.prototype.resetSubLocation = function(subLocation) {
        if (0 && this.subLocation && this.subLocation.length > 0) {
            console.log('Reset sublocation '+this.panelType);
            console.log(this.subLocation);
        }
        this.subLocation = JSON.parse(JSON.stringify(subLocation || []));
    };

    // TO BE OVERRIDEN
    // Move to a sublocation
    // if successful:
    //  next time getSubLocation is called, the sublocation should be returned
    //  return true
    Located.prototype.moveToSubLocation = function(subLocation) {
        var ret = true;
        this.setSubLocation(subLocation);
        return true;
    };

    Located.prototype.syncLocationWith = function(panelUUID, contentType, locationType, surroundingLocations, subLocation, panel) {
        // panel is optional
        // <surroundingLocations> is a string ('2r') or a dict {0: '2r', 1: '2v', -1: '1v'}
        if (panelUUID === this.uuid) return;

        // if string convert to dict, but with same loc for +-1
        if (surroundingLocations.substring) surroundingLocations = {0: surroundingLocations};
        if (!surroundingLocations.hasOwnProperty('1')) surroundingLocations[1] = surroundingLocations[0];
        if (!surroundingLocations.hasOwnProperty('-1')) surroundingLocations[-1] = surroundingLocations[0];

        var addressParts = this.getLoadedAddressParts();

        var parts = this.getLocationParts();

        var syncAddress = null;

        // Load new address only if:
        // a) we are synced with emitting location type
        if ((this.getLocationType() === 'sync' && (parts.location.toLowerCase() == contentType.toLowerCase())) ||
            // OR b) cross web-page sync: both this panel and the emitting one are location widgets
            (contentType.toLowerCase() === 'location' && contentType.toLowerCase() === this.getContentType().toLowerCase())) {

            syncAddress = this.getContentAddress(locationType, surroundingLocations[parts.offset]);
            //console.log(''+this.contentType+' SYNC with ('+contentType+', '+locationType+', '+surroundingLocations[parts.offset]+', '+subLocation+')');
        }

        // OR c) bidir sync: we are a master location panel and the emitting panel is synced with us
        // the location is the same and we have a particular sublocation
        if (!syncAddress &&
            (1 && addressParts && panel && this.getContentType().toLowerCase() === 'location' &&
                panel.getLocationType() === 'sync' && panel.getLocation() === 'location' &&
                subLocation && subLocation.length > 0 // &&
                //locationType == addressParts.locationType && surroundingLocations[parts.offset] == addressParts.location
            )
        ) {
            // We don't change the (LT, L), only sublocation.
            // e.g. synced panel = /transcription/whole/ ; master location = /location/locus/face/
            syncAddress = this.getLoadedAddress();
        }

        if (syncAddress) {
            this.loadContent(!(this.locations), syncAddress, subLocation);
        }
    };

}( window.TextViewer = window.TextViewer || {}, jQuery ));
