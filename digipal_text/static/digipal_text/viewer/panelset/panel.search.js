//////////////////////////////////////////////////////////////////////
//
// PanelSearch
//
// A Panel for doing text search in the current document
// Snippets are displayed with links that can sync other 
// panels.
//
//////////////////////////////////////////////////////////////////////
(function(TextViewer, $, undefined) {

    var PanelSearch = TextViewer.PanelSearch = function($root, contentType, options) {
        TextViewer.Panel.call(this, $root, contentType, 'Search', options);

        this.loadContentCustom = function(loadLocations, address, subLocation) {
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

    PanelSearch.prototype = Object.create(TextViewer.Panel.prototype);

}( window.TextViewer = window.TextViewer || {}, jQuery ));
