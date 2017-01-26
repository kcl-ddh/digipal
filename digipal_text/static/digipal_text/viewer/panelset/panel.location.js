//
// PanelLocation
// A 'master' location widget, it has no content, just locationType,
// location drop downs. Other panels can be sync'ed with it.
//
//////////////////////////////////////////////////////////////////////
(function(TextViewer, $, undefined) {

    var PanelLocation = TextViewer.PanelLocation = function($root, contentType, options) {
    	// table of content
    	this.toc = {};
    	
        TextViewer.Panel.call(this, $root, contentType, 'Location', options);
    };

    PanelLocation.prototype = Object.create(TextViewer.Panel.prototype);

    PanelLocation.prototype.createUserInterface = function() {
        // create the location controls
        var $buttons = this.$root.find('.location-buttons');
        $buttons.html($('#text-viewer-panel .location-buttons').html());

        // unhide location drop down otherwise the widget is entirely
        // hidden and the panelset frame has the wrong initial size
        TextViewer.unhide($buttons.find('select[name=location]'), 1);

        // enable the prev/next
        $buttons.find('.btn-page-nav').addClass('enabled');
        
        this.$location_description = this.$root.find('.location-description');
    };

    PanelLocation.prototype.loadContentCustom = function(loadLocations, address, subLocation) {
        // Load all the possible locations with the API
        // Special case: we only load the first time to get all the locations.
        // Next times (see else branch), we don't need to load any content.
        if (loadLocations) {
            var me = this;
            this.callApi(
                'loading content',
                address,
                function(data) {
                    me.onContentLoaded(data);
                },
                {
                    'load_locations': loadLocations ? 1 : 0,
                }
            );
        } else {
            var parts = this.panelSet.getPanelAddressParts(address);
            if (parts.contentType) {
                // this will for a change of location and sync other panels, etc.
                this.onContentLoaded({location: parts.location, location_type: parts.locationType});
            }
        }
    };

    PanelLocation.prototype.onContentLoaded = function(data) {
    	if (data.toc) this.toc = data.toc;

        TextViewer.Panel.prototype.onContentLoaded.call(this, data);

        // display the Table of Content entries for the current location
        var toc_entries = this.toc[this.getLocation()] || '';
    	this.$location_description.html(toc_entries);
    };
    
}( window.TextViewer = window.TextViewer || {}, jQuery ));
