//////////////////////////////////////////////////////////////////////
//
// PanelLocation
// A 'master' location widget, it has no content, just locationType, 
// location drop downs. Other panels can be sync'ed with it.
//
//////////////////////////////////////////////////////////////////////
(function(TextViewer, $, undefined) {

    var PanelLocation = TextViewer.PanelLocation = function($root, contentType, options) {
        TextViewer.Panel.call(this, $root, contentType, 'Location', options);
    }

    PanelLocation.prototype = Object.create(TextViewer.Panel.prototype);

    PanelLocation.prototype.createUserInterface = function() {
        // create the location controls
        var $buttons = this.$root.find('.location-buttons');
        $buttons.html($('#text-viewer-panel .location-buttons').html());

        // show them
        TextViewer.unhide($buttons.find('.dphidden'), true);
        
    }
    
    PanelLocation.prototype.loadContentCustom = function(loadLocations, address, subLocation) {
        // Load all the possible locations with the API
        // Special case: we only load the first time to get all the locations.
        // Next times (see lese branch), we don't need to load any content.
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
            parts = this.panelSet.getPanelAddressParts(address);
            if (parts.contentType) {
                // this will for a change of location and sync other panels, etc.
                this.onContentLoaded({location: parts.location, location_type: parts.locationType});
            }
        }
    };

}( window.TextViewer = window.TextViewer || {}, jQuery ));
