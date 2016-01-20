/**
 * Class to control the Annotations with OpenLayers.
 * It add a Vector layer and a tool bar to edit annotations.
 *
 * @param imageUrl
 *						URL of the image to annotate.
 * @param imageWidth
 *						Width of the image to annotate.
 * @param imageHeight
 *						Height of the image to annotate.
 * @param isZoomify
 *						Indicates if the imageUrl refers to a zoomify URL.
 *
 * This is modified version of the kcl-ddh/openlayers-image-annotation
 * TODO: fork it on github and commit the changes
 * 
 */

function Annotator(imageUrl, imageWidth, imageHeight, isZoomify) {
    if (!imageUrl) {
        return;
    }

    // to make it accessible when 'this' loses scope
    var _self = this;

    var isEmpty = function(obj) {
        for (var prop in obj) {
            if (obj.hasOwnProperty(prop)) return false;
        }
        return true;
    };

    this.imageUrl = imageUrl;
    this.imageWidth = imageWidth;
    this.imageHeight = imageHeight;

    var maxExtent = new OpenLayers.Bounds(0, 0, this.imageWidth,
        this.imageHeight);

    if (isZoomify) {
        // creates a new ZoomifyLayer for the image being annotated
        this.imageLayer = new OpenLayers.Layer.Zoomify('Zoomify', imageUrl,
            new OpenLayers.Size(this.imageWidth, this.imageHeight), {
                isBaseLayer: true
            });
    } else {
        // creates a new ImageLayer to display the image being annotated
        this.imageLayer = new OpenLayers.Layer.Image('Image', this.imageUrl,
            maxExtent, new OpenLayers.Size(this.imageWidth / 7,
                this.imageHeight / 7, {
                    isBaseLayer: true,
                    numZoomLevels: 1,
                    ratio: 1.0
                }));
    }
    
    this.map = window.dputils.add_open_layer({
        version: 2,
        $target: '#map',
        image_width: this.imageWidth,
        image_height: this.imageHeight,
        max_resolution: Math.pow(2, this.imageLayer.numberOfTiers - 1),
        eventListeners: {
            featureover: function(e) {
                if (e.feature.display_note && $('#show_editorial_annotations').is(':checked') && (!$('#editorial_filter').length || $('#editorial_filter').is(':checked'))) {
                    createPopup(e.feature);
                }
            },
            featureout: function(e) {
                if (e.feature.popup && $('#show_editorial_annotations').is(':checked') && (!$('#editorial_filter').length || $('#editorial_filter').is(':checked'))) {
                    deletePopup(e.feature);
                }
            },
        }
    });

    // creates a new OpenLayers map
    /*
    this.map = new OpenLayers.Map('map', {
        maxExtent: maxExtent,
        maxResolution: Math.pow(2, this.imageLayer.numberOfTiers - 1),
        numZoomLevels: annotator_zoom_levels,
        projection: 'EPSG:3785',
        units: 'm',
        eventListeners: {
            featureover: function(e) {
                if (e.feature.display_note && $('#show_editorial_annotations').is(':checked') && (!$('#editorial_filter').length || $('#editorial_filter').is(':checked'))) {
                    createPopup(e.feature);
                }
            },
            featureout: function(e) {
                if (e.feature.popup && $('#show_editorial_annotations').is(':checked') && (!$('#editorial_filter').length || $('#editorial_filter').is(':checked'))) {
                    deletePopup(e.feature);
                }
            },
        }
    });
    */

    //// adds the image layer to the map
    this.map.addLayer(this.imageLayer);

    // creates a StyleMap
    var styleMap = new OpenLayers.StyleMap();

    // creates a lookup table width different symbolizers for the styles
    var lookup = {
        0: {
            fillColor: 'red'
        },
        1: {
            fillColor: '#ee9900'
        }
    };

    // adds rules from the lookup table, with the keys mapped to the
    // 'state' property of the features, for the 'default' intent
    styleMap.addUniqueValueRules('default', Annotator.SAVED_ATTRIBUTE, lookup);

    // workaround to make the stylemap work with modify feature
    var rules = [new OpenLayers.Rule({
        symbolizer: {},
        elseFilter: true
    })];
    styleMap.styles['default'].addRules(rules);

    // creates a new OpenLayers.Layer to draw and render vectors
    this.vectorLayer = new OpenLayers.Layer.Vector('Vector', {
        maxExtent: maxExtent,
        strategies: [new OpenLayers.Strategy.Save()],
        styleMap: styleMap
    });

    // turns events on the vector layer to detect when a feature is selected
    this.vectorLayer.events.on({
        'featureselected': function(e) {
            _self.onFeatureSelect(e);
            var hand = $('#panelImageBox .hand_form').val();
            var allograph = $('#panelImageBox .allograph_form').val();
            if (e.feature.state == 'Insert') {
                e.feature.hand = parseInt(hand, 10);
                e.feature.allograph_id = parseInt(allograph, 10);
                e.feature.feature = $('#panelImageBox .allograph_form option:selected').text();
            }
        },
        'featureunselected': function(e) {
            // function to check if an object is empty, boolean returned


            if (typeof e.feature.linked_to !== "undefined" && !isEmpty(e.feature.linked_to[0])) {
                $.each(e.feature.linked_to[0], function(index, value) {
                    _self.onFeatureUnSelect(value, false);
                });
            } else {
                _self.onFeatureUnSelect(e, true);
            }
        },
        'featuremodified': function(e) {
            _self.setSavedAttribute(e.feature, Annotator.UNSAVED, true);
            _self.selectFeatureById(e.feature.id);
        }
    });

    // adds the vector layer to the map
    this.map.addLayer(this.vectorLayer);

    // creates a new format to serialize/deserialize the vectors as GeoJSON
    this.format = new OpenLayers.Format.GeoJSON();

    // creates a new panel for all the tools
    var container = document.getElementById("toolbar");
    this.toolbarPanel = new OpenLayers.Control.Panel({
        allowDepress: true,
        div: container,
        type: OpenLayers.Control.TYPE_TOGGLE,
        displayClass: 'olControlEditingToolbar'
    });

    // OpenLayers Control to delete features
    DeleteFeature = OpenLayers.Class(OpenLayers.Control, {
        initialize: function(layer, options) {
            OpenLayers.Control.prototype.initialize.apply(this, [options]);
            this.layer = layer;
            this.handler = new OpenLayers.Handler.Feature(this, layer, {
                click: this.clickFeature
            });
        },
        clickFeature: function(feature) {
            var msg, doDelete;
            if (allow_multiple() && annotator.selectedAnnotations && annotator.selectedAnnotations.length) {

                msg = 'You are about to delete ' + annotator.selectedAnnotations.length + ' annotations. They cannot be restored at a later time! Continue?';
                doDelete = confirm(msg);
                if (doDelete) {
                    for (var i = 0; i < annotator.selectedAnnotations.length; i++) {
                        var f = annotator.selectedAnnotations[i];
                        delete_annotation(this.layer, f, annotator.selectedAnnotations.length);
                    }

                    annotator.selectedAnnotations = [];
                }
            } else {
                msg = 'You are about to delete this annotation. It cannot be restored at a later time! Continue?';
                doDelete = confirm(msg);
                if (doDelete) {
                    delete_annotation(this.layer, feature);
                }
            }
        },
        setMap: function(map) {
            this.handler.setMap(map);
            OpenLayers.Control.prototype.setMap.apply(this, arguments);
        },
        CLASS_NAME: 'OpenLayers.Control.DeleteFeature'
    });

    // creates a delete feature
    this.deleteFeature = new DeleteFeature(this.vectorLayer, {
        displayClass: 'olControlDeleteFeature fa fa-times ',
        title: 'Delete'
    });

    // creates a modify feature
    /*
    this.modifyFeature = new OpenLayers.Control.ModifyFeature(this.vectorLayer, {
        mode: OpenLayers.Control.ModifyFeature.RESHAPE | OpenLayers.Control.ModifyFeature.DRAG,
        displayClass: 'olControlModifyFeature',
        title: 'Modify'
    });

    */
    // creates a transform feature
    this.transformFeature = new TransformFeature(this.vectorLayer, {
        renderIntent: 'transform',
        irregular: true,
        rotate: false,
        displayClass: 'olControlTransformFeature fa fa-arrows-alt ',
        title: 'Transform'
    });

    this.transformFeature.events.on({
        'transformcomplete': function(e) {
            _self.setSavedAttribute(e.feature, Annotator.UNSAVED, true);
            _self.selectFeatureById(e.feature.id);

        },
        'transform': function(e) {

        },
        'beforeset': function(e) {

        },
        'setfeature': function(e) {
            var hand = $('#panelImageBox .hand_form').val();
            var allograph = $('#panelImageBox .allograph_form').val();
            if (e.feature.state == 'Insert') {
                e.feature.hand = parseInt(hand, 10);
                e.feature.allograph_id = parseInt(allograph, 10);
                e.feature.feature = $('#panelImageBox .allograph_form option:selected').text();
            }
            if (annotator.isAdmin == 'False') {
                if (e.feature.stored !== undefined && e.feature.stored !== null && e.feature.stored) {
                    annotator.transformFeature.unsetFeature();
                    return false;
                }
            }
        }
    });

    // creates a duplicate feature
    /*this.duplicateFeature = new DuplicateFeature(this.vectorLayer, {
        displayClass: 'olControlDuplicateFeature',
        title: 'Duplicate'
    });
    */

    // creates a polygon feature
    /*
    this.polygonFeature = new OpenLayers.Control.DrawFeature(this.vectorLayer,
        OpenLayers.Handler.Polygon, {
            displayClass: 'olControlDrawFeaturePath',
            title: 'Draw Polygon'
        });
    */
    // creates a rectangle feature
    this.rectangleFeature = new OpenLayers.Control.DrawFeature(
        this.vectorLayer, OpenLayers.Handler.RegularPolygon, {
            displayClass: 'olControlDrawFeaturePolygon fa fa-pencil-square-o ',
            handlerOptions: {
                sides: 4,
                irregular: true
            },
            title: 'Draw Rectangle'
        });

    this.rectangleFeature.events.on({
        'featureadded': function(e) {
            var geometry = e.feature;
            _self.transformFeature.setFeature(geometry);
        },
        'activate': function() {
            var switcher = $('.toggle-state-switch');
            var public_annotations_check = $('[data-attribute="public"]');
            if (!switcher.bootstrapSwitch('state')) {
                switcher.bootstrapSwitch('toggleState');
            }
            if (!public_annotations_check.is(':checked')) {
                public_annotations_check.prop('checked', true).trigger('change');
            }

        }
    });

    // creates a select feature
    this.selectFeature = new OpenLayers.Control.SelectFeature(this.vectorLayer, {
        displayClass: 'olControlDragFeature fa fa-hand-o-up ',
        title: 'Select',
        clickout: true,
        toggle: false,
        multiple: false,
        hover: false,
        toggleKey: 'shiftKey',
        box: false
    });

    this.selectFeature.events.on({
        activate: function() {
            if (_self.editorial.active) {
                _self.editorial.deactivate();
            }
        }
    });


    // creates a drag feature
    this.dragFeature = new OpenLayers.Control.DragFeature(this.vectorLayer, {
        displayClass: 'olControlSelectFeature',
        title: 'Drag'
    });

    this.dragFeature.onComplete = function(feature, pixel) {
        _self.setSavedAttribute(feature, Annotator.UNSAVED, true);
    };

    // creates a zoom box feature
    this.zoomBoxFeature = new OpenLayers.Control.ZoomBox({
        alwaysZoom: true,
        keyMask: false,
        displayClass: 'olControlZoomBox fa fa-search-plus '
    });



    // creates a button to save features
    this.saveButton = new OpenLayers.Control.Button({
        title: 'Save',
        trigger: function() {
            _self.saveAnnotation();
        },
        displayClass: 'olControlSaveFeatures fa fa-save '
    });

    /* FullScreen Mode */


    /* End FullScreen Mode */


    // Full screen feature

    FullScreen = OpenLayers.Class(OpenLayers.Control, {
        initialize: function(layer, options) {
            OpenLayers.Control.prototype.initialize.apply(this, [options]);
            this.layer = layer;
        },

        CLASS_NAME: 'OpenLayers.Control.FullScreen'
    });

    Refresh = OpenLayers.Class(OpenLayers.Control, {
        initialize: function(layer, options) {
            OpenLayers.Control.prototype.initialize.apply(this, [options]);
            this.layer = layer;
        },

        CLASS_NAME: 'OpenLayers.Control.Refresh'
    });

    EditorialAnnotations = OpenLayers.Class(OpenLayers.Control, {
        initialize: function(layer, options) {
            OpenLayers.Control.prototype.initialize.apply(this, [options]);
            this.layer = layer;
        },

        CLASS_NAME: 'OpenLayers.Control.EditorialAnnotations'
    });

    this.fullScreen = new OpenLayers.Control.Button({
        displayClass: 'olControlFullScreenFeature fa fa-desktop ',
        title: 'Full Screen',
        active: false,
        trigger: function() {
            _self.full_Screen();
        }
    });

    this.refresh = new OpenLayers.Control.Button({
        displayClass: 'olControlRefreshFeature fa fa-refresh ',
        title: 'Refresh',
        trigger: function() {
            _self.refresh_layer();
        }
    });

    this.editorial = new OpenLayers.Control.Button({
        displayClass: 'olControlEditorialFeature fa fa-pencil ',
        title: 'Create Editorial Annotation',
        active: false,
        trigger: function() {
            var activeControls = this.map.getControlsBy('active', true);
            if (this.active) {
                /*
                _self.boxes_on_click = false;
                $('#boxes_on_click').attr('checked', false);
                */
                this.deactivate();
            } else {
                /*
                _self.boxes_on_click = true;
                $('#boxes_on_click').attr('checked', true);
                */
                _self.toggleAll(activeControls, false);
                this.activate();
                _self.rectangleFeature.activate();
                var forms = get_forms();
                forms.allograph_form.val('------');
                forms.hand_form.val('------');
                $('select').trigger('liszt:updated');
            }
        }
    });



    // adds all the control features to the toolbar panel
    this.toolbarPanel.addControls([this.fullScreen, this.selectFeature,
        this.zoomBoxFeature, this.refresh, this.editorial, this.saveButton,
        this.deleteFeature, this.transformFeature, this.rectangleFeature
    ]);

    // sets the default control to be the drag feature
    this.toolbarPanel.defaultControl = this.selectFeature;

    // adds the toolbar panel to the map
    this.map.addControl(this.toolbarPanel);

    // loads existing vectors into the vector layer
    this.loadVectors();

    // loads existing annotations
    this.loadAnnotations();

    // automatically selects a feature after its inserted into the vector layer
    this.vectorLayer.preFeatureInsert = function(feature) {
        if (_self.getSavedAttribute(feature) != Annotator.SAVED) {
            _self.setSavedAttribute(feature, Annotator.UNSAVED, false);
        }
    };


    /*
    this.vectorLayer.onFeatureInsert = function(feature) {
        _self.selectFeatureById(feature.id);
        //_self.selectFeature.unselect(feature);
    }
    */
}

Annotator.SAVED = 1;
Annotator.SAVED_ATTRIBUTE = 'saved';
Annotator.UNSAVED = 0;



/**
 * Function that is called after a feature is selected.
 *
 * @param event
 *						The select event.
 */
Annotator.prototype.onFeatureSelect = function(event) {
    this.selectedFeature = event.feature;
    this.showAnnotation(event.feature);
};

/**
 * Function that is called after a feature is unselected.
 *
 * @param event
 *						The unselect event.
 */
Annotator.prototype.onFeatureUnSelect = function(event) {
    this.selectedFeature = null;
};

/**
 * Shows the annotation details for the given feature.
 *
 * @param feature
 *						The feature to display the annotation.
 */
Annotator.prototype.showAnnotation = function(feature) {};

/**
 * Deletes the annotation for the selected feature.
 *
 * @abstract
 * @param layer
 *						The feature's layer.
 * @param feature
 *						The feature to delete the annotation for.
 */
Annotator.prototype.deleteAnnotation = function(layer, feature) {};

/**
 * Saves the selected feature annotation.
 *
 * @abstract
 */
Annotator.prototype.saveAnnotation = function() {};

/**
 * Loads existing vectors into a layer.
 *
 * @abstract
 */
Annotator.prototype.loadVectors = function() {};

/**
 * Loads existing annotations.
 *
 * @abstract
 */
Annotator.prototype.loadAnnotations = function() {};

/**
 * Turns on keyboard shortcuts for the controls.
 */
Annotator.prototype.activateKeyboardShortcuts = function(event) {};

/**
 * Selects a feature by ID.
 *
 * @param featureId
 *						The id of the feature to select.
 */
Annotator.prototype.selectFeatureById = function(featureId) {
    var feature;
    if ($.isNumeric(featureId)) {
        feature = this.vectorLayer.getFeatureById(featureId);
    } else {
        feature = this.getGraphByVectorId(featureId);
    }
    this.selectFeature.clickFeature(feature);
    return feature;
};

Annotator.prototype.getGraphByVectorId = function(featureId) {
    var feature;
    for (var i = 0; i < this.vectorLayer.features.length; i++) {
        if (this.vectorLayer.features[i].hasOwnProperty('id')) {
            var vector_id = this.vectorLayer.features[i].vector_id || this.vectorLayer.features[i].id;
            if (vector_id instanceof String && featureId instanceof String) {
                featureId = featureId.replace(/\./gi, '_');
                vector_id = vector_id.replace(/\./gi, '_');
            }

            if (featureId == vector_id) {
                feature = this.vectorLayer.features[i];
                break;
            }
        }
    }
    return feature;
};

/**
 * Selects a feature by ID and centres on the feature.
 *
 * @param featureId
 *						The id of the feature to select.
 */
Annotator.prototype.selectFeatureByIdAndCentre = function(featureId) {
    var feature = this.vectorLayer.getFeatureById(featureId);
    this.selectFeature.clickFeature(feature);
    this.map.setCenter(feature.geometry.getBounds().getCenterLonLat());
};

/**
 * Selects a feature by ID and zooms to the feature extent.
 *
 * @param featureId
 *						The id of the feature to select.
 */
Annotator.prototype.selectFeatureByIdAndZoom = function(featureId) {
    var feature = this.selectFeatureById(featureId);
    this.map.zoomToExtent(feature.geometry.getBounds());
    this.map.zoomTo(this.map.getZoom() - 1);
    this.scrollToImage();
};

Annotator.prototype.scrollToImage = function() {
    // scroll to the heading so more of the image is visible
    if ($(window).scrollTop() <= 1) {
        $('html, body').animate({scrollTop: $('#annotator_heading').offset().top }, 100);
    }
}

Annotator.prototype.centreById = function(featureId) {
    var feature = this.vectorLayer.getFeatureById(featureId);
    this.map.setCenter(feature.geometry.getBounds().getCenterLonLat());
};
/**
 * Returns the saved attribute for the given feature.
 *
 * @param feature
 *						The value of the saved attribute.
 */
Annotator.prototype.getSavedAttribute = function(feature) {
    var attribute = Annotator.SAVED_ATTRIBUTE;

    return feature.attributes['saved'];
};

/**
 * Sets the saved attribute of the feature to the given value. If redraw is true
 * the layer will redraw the feature.
 *
 * @param feature
 *						The feature to update.
 * @param saved
 *						The value for the saved attribute.
 * @param redraw
 *						Whether the layer should redraw the feature.
 */
Annotator.prototype.setSavedAttribute = function(feature, saved, redraw) {
    var attribute = Annotator.SAVED_ATTRIBUTE;
    feature.attributes = {
        'saved': saved
    };

    if (redraw) {
        this.vectorLayer.drawFeature(feature, 'default');
    }
};

Annotator.prototype.toggleAll = function(activeControls, active) {
    for (i = 0; i < activeControls.length; i++) {
        if (activeControls[i].title) {
            if (activeControls[i].displayClass != 'olControlFullScreenFeature') {
                if (active) {
                    activeControls[i].activate();
                } else {
                    activeControls[i].deactivate();
                    annotator.editorial.deactivate();
                }
            }
        }
    }
};
