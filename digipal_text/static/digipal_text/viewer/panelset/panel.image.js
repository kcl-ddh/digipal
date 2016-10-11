//////////////////////////////////////////////////////////////////////
//
// PanelImage
//
// An Image viewer panel. The content is displayed with OpenLayers.
// It also allows the creation of text-image annotations.
//
//////////////////////////////////////////////////////////////////////
(function(TextViewer, $, undefined) {

    var PanelImage = TextViewer.PanelImage = function($root, contentType, options) {
        TextViewer.Panel.call(this, $root, contentType, 'Image', options);
        
        var me = this;
        
        this.editingMode = false;

        this.loadContentCustom = function(loadLocations, address, subLocation) {
            // load the content with the API
            var me = this;

            var payload = {
                'layout': 'width',
                'width': me.$content.width(),
                'height': me.$content.height(),
                'load_locations': loadLocations,
                'sub_location': subLocation,
            };

            this.callApi(
                'loading image',
                address,
                function(data) {
                    me.onContentLoaded(data);
                },
                payload
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

            this.annotator = window.ann3 = new window.AnnotatorOL3(this.map, this.getEditingMode());

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
            if (map) {
                var view = map.getView();
                var imageFullHeight = view.getProjection().getExtent()[3];
                var viewerFullHeight = map.getSize()[1] * view.getResolution();
                if (viewerFullHeight < imageFullHeight) {
                    view.setCenter([view.getCenter()[0], - (viewerFullHeight / 2)]);
                }
            }
        };

    };

    PanelImage.prototype = Object.create(TextViewer.Panel.prototype);

    PanelImage.prototype.onContentLoaded = function(data) {
        // avoid reloading the same image
        if (!(this.last_data && this.last_data.zoomify_url == data.zoomify_url)) {
            // OL
            this.applyOpenLayer(data);

            // annotations
            if (this.annotator) {
                this.annotator.addAnnotations(data.annotations);
            }

            // text-image links
            TextViewer.unhide(this.$linker, true);
            this.resetLinker(data);
        }

        TextViewer.Panel.prototype.onContentLoaded.call(this, data);

        this.last_data = data;
    };

    PanelImage.prototype.moveToSubLocation = function(subLocation) {
        var ret = false;
        if (this.annotator) {
            var feature = this.annotator.getFeatureFromElementId(subLocation);
            this.annotator.selectFeature(feature);
            this.annotator.zoomToFeature(feature);
            if (feature) this.setSubLocation(subLocation);
            ret = !!feature;
        }
        return ret;
    };

    PanelImage.prototype.resetLinker = function(data) {
        /* eg.:  data = {
            "text_elements": [
                [["", "clause"], ["type", "address"]],
                [["", "person"], ["type", "name"], ["@text", "willelmus-cumin"]]
            ]
           }
        */
        var me = this;
        var elements = data.text_elements;

        var htmlstr = '<option value="">Unspecified</option>';
        if (elements) {
            elements.map(function(el) {
                // e.g. el = [ [["", "person"], ["type", "name"], ["@text", "willelmus-cumin"]] , 'willelmus-cumin (name)' ]
                var key = JSON.stringify(el[0]);
                htmlstr += '<option value="'+window.dputils.escapeHtml(key)+'">'+el[1]+'</option>';
            });
        }
        this.$linkerText.html(htmlstr);
        this.refreshLinkerText();
    };

    PanelImage.prototype.getLabelFromElementid = function(elementid) {
        var parts = elementid || [];
        var ret = '';
        for (var i = 0; i < parts.length; i++) {
            if (i) ret += ' > ';
            ret += parts[i][1];
        }
        return ret;
    };

    PanelImage.prototype.annotatorEventHandler = function(e) {
        var elementid = '';
        if (e.action === 'hover') {
            var feature = e.features && e.features.length ? e.features[0] : null;
            elementid = null;
            if (feature) {
                elementid = feature.get('elementid');
            }

            this.setMessage(''+this.getLabelFromElementid(elementid), 'info');

            return;
        }

        var me = this;

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
        selections.forEach(function (feature) {
            elementid = JSON.stringify(feature.get('elementid') || '[]');
        });
        this.$linkerText.val(elementid);
        this.refreshLinkerText();

        // send the changes to the server
        if (e.action === 'changed' || e.action === 'deleted') {
            this.onAnnotationChanged(e.features, e.action);
        }
    };

    PanelImage.prototype.refreshLinkerText = function() {
        this.$linkerText.trigger('liszt:updated');
        var self = this;

        // color the elements in the drop down which have no annotation
        if (this.annotator) {
            var feature = null;
            var $lis = this.$linkerText.next('.chzn-container').find('li');
            this.$linkerText.find('option').each(function(i) {
                var elid = $(this).attr('value');
                if (elid && elid.startsWith('[')) {
                    feature = self.annotator.getFeatureFromElementId(JSON.parse(elid || '[]'));
                }
                $($lis[i]).toggleClass('unlinked', !feature);
            });
        }
    };

    PanelImage.prototype.onLinkerTextChanged = function() {
        var feature = null;
        var elementid = JSON.parse(this.$linkerText.val() || '[]');
        if (elementid) {
            //feature = this.annotator.findFeature({properties: {elementid: JSON.parse(elementid)} });
            feature = this.annotator.getFeatureFromElementId(elementid);
        }

        var me = this;

        if (!feature) {
            // no feature for this element
            // assign the element to the currently selected feature
            this.annotator.getSelectedFeatures().forEach(function(afeature) {
                if (me.getEditingMode()) afeature.set('elementid', elementid);
                feature = afeature;
            });
        }

        this.annotator.selectFeature(feature);
        this.annotator.zoomToFeature(feature, true);

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
        var ret = TextViewer.Panel.prototype.getStateDict.call(this);

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
        TextViewer.Panel.prototype.onResize.call(this);
        if (this.map) {
            this.map.updateSize();
        }
    };

    PanelImage.prototype.setStateDictArg = function(name, value) {
        // olv:RES,CX,CY
        if (name == 'dis') {
            this.enablePresentationOptions(value.split(' '));
        }
        if (name === 'olv') {
            var parts = value.split(',');
            var map = this.map;
            if (map) {
                var view = map.getView();
                view.setResolution(parseFloat(parts[0]));
                view.setCenter([parseFloat(parts[1]), parseFloat(parts[2])]);
                if (parts.length > 3) {
                    view.setRotation(parseFloat(parts[3]) * Math.PI / 180);
                }
            }
        }
    };

    PanelImage.prototype.applyPresentationOptions = function() {
        var classes = this.getListFromPresentationOptions();

        if (this.annotator) {
            this.annotator.setStyleTheme((classes.indexOf('highlight') > -1) ? '' : 'hidden');
        }
    };

    //////////////////////////////////////////////////////////////////////
    //
    // PanelImageWrite
    //
    // An Image panel with text-annotation editor.
    //
    //////////////////////////////////////////////////////////////////////
    var PanelImageWrite = TextViewer.PanelImageWrite = function($root, contentType, options) {
        TextViewer.PanelImage.call(this, $root, contentType, options);
        
        this.editingMode = true;
    }
    PanelImageWrite.prototype = Object.create(PanelImage.prototype);

    PanelImageWrite.prototype.setPresentationOptions = function(presentationOptions) {
        // we always want the annotations to be highlighted when we go into edit mode
        var ret = PanelImage.prototype.setPresentationOptions.call(this, presentationOptions);
        this.enablePresentationOptions(['highlight']);
        return ret;
    };

}( window.TextViewer = window.TextViewer || {}, jQuery ));
