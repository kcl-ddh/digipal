/// <reference path="../dts/jquery.d.ts"/>
/// <reference path="../dts/openlayers.d.ts"/>

function applyMixins(derivedCtor: any, baseCtors: any[]) {
    baseCtors.forEach(baseCtor => {
        Object.getOwnPropertyNames(baseCtor.prototype).forEach(name => {
            derivedCtor.prototype[name] = baseCtor.prototype[name];
        });
    });
}

class InteractionMode {
    started = false;
    startedEvents = ['drawstart', 'drawend'];

    initModeDetection(interaction: ol.Observable): void {
        // draw is a reference to ol.interaction.Draw
        interaction.on(this.startedEvents[0], function(evt) {
            this.started = true;
        });

        interaction.on(this.startedEvents[1], function(evt) {
            this.started = false;
            if (evt['features']) {
                evt.features.forEach((feature) => {
                    feature.changed();
                });
            }
        });

        interaction.on(ol['ObjectEventType'].PROPERTYCHANGE, function(evt) {
            if (evt.key === 'active' && !evt.target['getActive']()) this.started = false;
        })
    }

    /**
     * Returns true if feature drawing has started
     */
    isStarted(): boolean {
        return this.started;
    }

}

/**
 * Extension of ol.interaction.Draw
 * with awareness of whether the drawing operation is started.
 */
class Draw extends ol.interaction.Draw implements InteractionMode {
    started = false;
    startedEvents = ['drawstart', 'drawend'];
    initModeDetection: (interaction: ol.Observable) => void;
    isStarted: () => boolean;
}
applyMixins(Draw, [InteractionMode]);


/**
 * Extension of ol.interaction.Select
 * - with some helper functions
 * - and a way to find the smallest feature under the cursor
 * - also dispatch 'hover' event for such feature
 */
class Select extends ol.interaction.Select {

    handleEventDefault = null;
    // the vector layer that contains all the annotations
    vectorLayer: ol.layer.Vector = null;

    //featureHovered: ol.Feature = null;
    layerHover: ol.layer.Vector = null;

    constructor(options?: olx.interaction.SelectOptions, vectorLayer?: ol.layer.Vector, map?: ol.Map) {
        super(options);

        this.vectorLayer = vectorLayer;

        // Create a Hover Layer
        // Used to highlight the feature above which the cursor is placed
        var sourceHover = new ol.source.Vector({});
        var styleHover = new ol.style.Style({
            fill: new ol.style.Fill({
                color: 'rgba(255, 255, 255, 0.07)'
            }),
            stroke: new ol.style.Stroke({
                color: '#808000',
                width: 2
            })
        });
        this.layerHover = new ol.layer.Vector({ source: sourceHover });
        this.layerHover.setStyle(styleHover);
        map.addLayer(this.layerHover);
        this.layerHover['setZIndex'](10);

        // That's the important bit... which is excluding Select overlay from
        // being chosen for selecting a feature on click.
        this['layerFilter_'] = (layer) => {
            return layer === this.layerHover;
        };

        // Tweak to the default Select handler:
        // * highlight hovered feature
        // * make sure the selection pick from the hovered layer
        // (b/c default Select is unable to select nested features)
        this.handleEventDefault = this['handleEvent'];
        this['handleEvent'] = (mapBrowserEvent: ol.MapBrowserEvent) => {
            /*
                Problem: OL3 selection algorithm doesn't allow selection of a
                feature nested within another selected feature. Because
                the selected feature is on the Select overlay which takes
                precedence. Custom layer and feature filters are bypassed
                for overlays.

                Solution: we temporarily configure the overlay to be ignored
                by the default algorithms.

                Failed solutions: unselecting before the default handler doesn't
                work. Not entirely sure why, perhaps b/c replay drawing history
                to detect hit. (this.getFeatures().clear())
            */

            this.highlightHoveredFeature(mapBrowserEvent);

            // default call
            var ret = this.handleEventDefault(mapBrowserEvent);

            return ret;
        };
    }

    findSmallestFeatureAtPixel(pixel: ol.Pixel, map: ol.Map): ol.Feature {
        var ret = null;
        var bestSize = null;
        var coordinates = map.getCoordinateFromPixel(pixel);
        this.vectorLayer.getSource()['forEachFeatureAtCoordinateDirect'](coordinates, function(feature) {
            var extent = feature.getGeometry().getExtent();
            var size = Math.abs(extent[2] - extent[0]) * Math.abs(extent[3] - extent[1]);
            if (!bestSize || bestSize > size) {
                bestSize = size;
                ret = feature;
            }
        });
        return ret;
    }

    highlightHoveredFeature(mapBrowserEvent: ol.MapBrowserEvent): void {
        /*
            Highlight hovered feature.
            If more than one, highlight the smallest one.

            NOTE that this has a side effect of solving a major issue with the
            default Select algorithm. That is, multiple features are below the
            cursor on click, the one drawned last has priority. So a nested
            feature may be unselectable.

            Because we add the hovered feature in a dedicated, top, Vector layer,
            which the Select algo can pick from, we ensure that it has priority
            over any other feature.
        */
        var feature = this.findSmallestFeatureAtPixel(mapBrowserEvent.pixel, mapBrowserEvent.map);

        this.layerHover.getSource()['clear']();

        if (feature) this.layerHover.getSource()['addFeature'](feature);

        this['dispatchEvent']({ type: 'hover', feature: feature });
    }

    /**
    * Remove selected features from the Vector layer
    * Clear the selection
    */
    removeFeatures(source: ol.source.Vector): void {
        var features = this.getFeatures();

        features.forEach((feature, i, featureArray) => {
            source.removeFeature(feature);
        });

        features.clear();
    }

}

class Translate extends ol.interaction.Translate implements InteractionMode {
    started = false;
    startedEvents = ['translatestart', 'translateend'];
    isStarted: () => boolean;
    initModeDetection: (interaction: ol.Observable) => void;
}
applyMixins(Translate, [InteractionMode]);

class Modify extends ol.interaction.Pointer implements InteractionMode {
    started = false;
    startedEvents = ['modifystart', 'modifyend'];
    isStarted: () => boolean;
    initModeDetection: (interaction: ol.Observable) => void;

    pointerCoordinate = [];
    features_;
    pixelTolerance_ = 15;
    overlay_: ol.layer.Vector;
    vertexFeature_: ol.Feature;
    //nearestVertexCoordinates_: ;

    constructor(options?: olx.interaction.ModifyOptions, vectorLayer?: ol.layer.Vector, map?: ol.Map) {
        super(options);
        this.features_ = options.features;
        this.pixelTolerance_ = options.pixelTolerance !== undefined ? options.pixelTolerance : 15;

        this['handleDownEvent_'] = (mapBrowserEvent): boolean => {
            var ret = this.isPointerNearSelectedVertex(mapBrowserEvent.pixel);
            if (ret) {
                this.dispatchEvent(new ol.interaction.ModifyEvent('modifystart', this.features_, mapBrowserEvent));
            }
            return ret;
        };

        this['handleUpEvent_'] = (mapBrowserEvent) => {
            var ret = false;
            if (!ret) {
                this.dispatchEvent(new ol.interaction.ModifyEvent('modifyend', this.features_, mapBrowserEvent));
            }
            return ret;
        };

        // We only want to move existing vertices so no highlight and
        // modification of edges or creation of new vertices.
        this['handleEvent'] = (mapBrowserEvent: ol.MapBrowserEvent): boolean => {

            if (!(mapBrowserEvent instanceof ol.MapBrowserPointerEvent)) return true;

            this.pointerCoordinate = mapBrowserEvent.coordinate;

            if (!this.isStarted() && !this.isPointerNearSelectedVertex(mapBrowserEvent.pixel)) {
                return true
            };

            // default handlers
            ol.interaction.Pointer.handleEvent.call(this, mapBrowserEvent);

            return false;
        };

        this['handleDragEvent_'] = (mapBrowserEvent: ol.MapBrowserEvent) => {
            // preserve the rectangular shape while modifying the feature
            var map = this.getMap();

            this['features_'].forEach((feature) => {
                var geo = feature.getGeometry();
                if (geo.getType() === 'Polygon' || geo.getType() === 'MultiPolygon') {
                    // e.g. [482.52956397333946, -233.56917532670974, 810.2463886407656, -40.794572581164886]
                    var xt2 = geo.getExtent();
                    var xt = [
                        this.pointerCoordinate[0],
                        this.pointerCoordinate[1],
                        Math.abs(xt2[0] - this.pointerCoordinate[0]) > Math.abs(xt2[2] - this.pointerCoordinate[0]) ? xt2[0] : xt2[2],
                        Math.abs(xt2[1] - this.pointerCoordinate[1]) > Math.abs(xt2[3] - this.pointerCoordinate[1]) ? xt2[1] : xt2[3],
                    ];
                    var coordinates = [[
                        [xt[0], xt[1]],
                        [xt[0], xt[3]],
                        [xt[2], xt[3]],
                        [xt[2], xt[1]],
                        [xt[0], xt[1]]
                    ]];

//                    var s = '';
//                    coordinates[0].map((p) => {
//                        s += '(' + p[0] + ',' + p[1] + '), ';
//                    });
                    geo.setCoordinates(coordinates, geo.getLayout());
                    //feature.changed();
                }
            });
        }
    }

    /**
     * Returns true if the pointer is near one of the vertices of a selected
     * feature.
     * 'near' means within this.pixelTolerance pixels.
     */
    isPointerNearSelectedVertex(pointerxy): boolean {
        var ret = false;
        var map = this.getMap();

        this['features_'].forEach((feature) => {
            var geo = feature.getGeometry();
            if (geo.getType() === 'Polygon' || geo.getType() === 'MultiPolygon') {
                var fcs = geo.getFlatCoordinates();
                for (var i = 0; i < fcs.length; i+=2) {
                    var fcxy = map.getPixelFromCoordinate([fcs[i], fcs[i+1]]);
                    var dist = Math.sqrt(ol.coordinate['squaredDistance'](fcxy, pointerxy));
                    if (dist <= this['pixelTolerance_']) {
                        ret = true;

                        // show the resize pointer to indicate that Modify mode works
                        var elem = this.getMap().getTargetElement();
                        elem['style'].cursor = 'move';
                    }
                }
            }
        });
        return ret;
    }

}
applyMixins(Modify, [InteractionMode]);

/**
 * An dynamic collection of interaction on a map
 */
class AOL3Interactions {

    controler: ol.interaction.Interaction;
    // TODO: remove those members and use interactions member instead
    draw: Draw;
    select: Select;
    translate: Translate;
    modify: Modify;
    // Provide easy access to all defined interactions
    interactions: {[id: string] : ol.interaction.Interaction} = {};

    setInteraction(key: string, interaction: ol.interaction.Interaction, map: ol.Map) {
        if (this[key]) map.removeInteraction(interaction);
        this[key] = interaction;
        var initModeDetection = interaction['initModeDetection'];
        if (initModeDetection) initModeDetection.call(interaction, interaction);
        this.interactions[key] = interaction;
        map.addInteraction(interaction);
    }

    setActive(key: string, active: boolean): boolean {
        var interaction = this[key];
        if (interaction) interaction.setActive(active);
        return !!interaction;
    }

    /**
     * Switch between select/draw modes
     * @param {string} key: the key of the interaction to switch to
     */
    switch(key: string) {
        var groups = {
            'select': ['select', 'translate', 'modify'],
            'draw': ['draw']
        };
        for (var member in this) {
            if ((member != 'controller') && (this[member] instanceof ol.interaction.Interaction)) {
                this.setActive(member, groups[key].indexOf(member) > -1);
            }
        }
    }

    isDrawing(): boolean {
        return (this.draw && this.draw.isStarted());
    }

    /**
     * Returns true if any of the interaction is started and not yet finished
     * E.g. drawing, modifying or translating a feature.
     */
    isStarted(): boolean {
        var ret = false;
        for(var key in this.interactions) {
            if (this.hasOwnProperty(key)) {
                let interaction = this.interactions[key];
                var isStarted = interaction['isStarted'];
                if (isStarted && isStarted.call(interaction)) ret = true;
            }
        }
        return ret;
    }

}

class AnnotatorOL3 {
    map: ol.Map;
    // source
    source: ol.source.Vector;
    // the annotation layer
    layer: ol.layer.Vector;
    //
    interactions: AOL3Interactions = new AOL3Interactions();
    //
    lastDrawnFeature: ol.Feature;
    //
    theme: string = '';
    //
    canEdit: boolean;

    constructor(map: ol.Map, canEdit = false) {
        this.map = map;
        this.canEdit = canEdit;

        this.addAnnotationLayer();

        this.initInteractions();
    }

    addAnnotationLayer(): void {
        // create layer
        this.source = new ol.source.Vector({ wrapX: false });

        this.layer = new ol.layer.Vector({
            source: this.source,
            style: this.getStyles(),
        });

        this.map.addLayer(this.layer);
    }

    initInteractions(): void {
        // Interactions are processed in reverse order:
        if (this.canEdit) this.initDraw();
        this.initSelect();
        if (this.canEdit) this.initTranslate();
        if (this.canEdit) this.initModify();
        // Selector BEFORE draw and select
        // so we can chose which one handle the current event
        this.initInteractionSelector();
    }

    initTranslate(): void {
        var options = { features: this.interactions.select.getFeatures() };
        var translate = new Translate(options);

        this.interactions.setInteraction('translate', translate, this.map);
    }

    initModify(): void {
        var options = { features: this.interactions.select.getFeatures() };
        var modify = new Modify(options);

        this.interactions.setInteraction('modify', modify, this.map);
    }

    /*
    * Add a new custom interaction that selects which interaction to enable
    * based on the user action (mouse and keyboard) as well as the currently
    * selected interaction.
    */
    initInteractionSelector(): void {

        var options = {
            handleEvent: (e: ol.MapBrowserEvent): boolean => {
                var ctrl = e.originalEvent['ctrlKey'] || e.originalEvent['metaKey'];
                var type = e['type'];
                var key = e.originalEvent['keyCode'] || 0;

                if (!((type === 'pointermove') ||
                    (type === 'key' && ctrl))) {
                    //console.log('> ' + type + ' <------------------');
                    //console.log(e);
                }

                // CTRL + pointerdown
                if (type === ol.MapBrowserEvent['EventType'].POINTERDOWN) {
                    if (ctrl && !this.isDrawing()) {
                        //console.log('CTRL-CLICK ACTIVATE DRAW');
                        this.interactions.switch('draw');
                    }
                }

                if (type === ol.events['EventType'].KEYDOWN) {
                    if (this.isDrawing()) {
                        // DEL / ESC
                        if ((key === 46) || (key === 27)) {
                            // abort drawing
                            this.interactions.switch('select');
                        }
                    } else {
                        // DEL remove feature
                        if (key === 46) {
                            this.removeSelectedFeatures();
                        }
                    }
                }

                return true;
            }
        };
        var interaction = new ol.interaction.Interaction(options);

        this.interactions.setInteraction('controller', interaction, this.map);
    }

    removeSelectedFeatures(): void {
        if (!this.canEdit) return;

        var features = this.getSelectedFeatures();
        // clone the selection before it is cleared
        var featuresDeleted = features.getArray().map((v) => v);

        this.interactions.select.removeFeatures(this.source);
    }

    isDrawing(): boolean {
        return this.interactions.isDrawing();
    }

    // Set a style theme, possible values:
    //      'default'
    //      'hidden'
    setStyleTheme(theme): void {
        this.theme = theme;
        if (theme === 'hidden') {
            this.layer.setStyle(null);
        } else {
            this.layer.setStyle(this.getStyles());
        }
    }

    initSelect(): void {
        var interaction = new Select({
            condition: ol.events.condition.click,
            //condition: ol.events.condition.pointerMove,
            style: (feature, resolution) => {
                return [this.getStyles('select')];
            }
        }, this.layer, this.map);

        interaction.on('select', (e) => {
            // After drawing ends a 'click' event is generated
            // and the feature under the pointer is
            // the end point (endgeometry) of the drawn feature.
            // Because OL replay the drawing instructions to detect a hit.

            // Here we detect that situation and force the selection of the
            // last drawn feature.
            if (this.lastDrawnFeature) {
                this.selectFeature(this.lastDrawnFeature);
                this.lastDrawnFeature = null;
            }

        });

        this.interactions.setInteraction('select', interaction, this.map);
    }

    initDraw(): void {
        var geometryFunction, maxPoints;
        var value = 'LineString';
        maxPoints = 2;
        geometryFunction = function(coordinates, geometry) {
            if (!geometry) {
                geometry = new ol.geom.Polygon(null);
            }
            var start = coordinates[0];
            var end = coordinates[1];
            geometry.setCoordinates([
                [start, [start[0], end[1]], end, [end[0], start[1]], start]
            ]);
            return geometry;
        };

        var condition = (e: ol.MapBrowserEvent): boolean => {
            var ctrl = e.originalEvent['ctrlKey'] || e.originalEvent['metaKey'];
            //var ctrl = ol.events.condition.platformModifierKeyOnly(e);

            //console.log('DRAW condition '+e['type']);
            return this.interactions.draw.isStarted() || ctrl;
        }

        var interaction = new Draw({
            source: this.source,
            type: (value),
            geometryFunction: geometryFunction,
            condition: condition,
            maxPoints: maxPoints
        });
        interaction['setActive'](false);

        interaction.on('drawstart', (evt) => {
            //this.interactions.draw['isStarted'] = true;

            // clear any selection
            this.selectFeature();

            //console.log('DRAW START');
        });
        interaction.on('drawend', (evt) => {
            //this.interactions.draw['isStarted'] = false;

            this.interactions.switch('select');

            // See select interaction. This is a work around.
            this.lastDrawnFeature = evt['feature'];

            //console.log('DRAW END');
        });

        this.interactions.setInteraction('draw', interaction, this.map);
    }

    getSelectedFeatures(): ol.Collection<ol.Feature> {
        return this.interactions.select.getFeatures();
    }

    /*
    findFeature(geojson_query): ol.Feature {
        var ret = [];

        var geojsons = JSON.parse((new ol.format.GeoJSON()).writeFeatures(this.source['getFeatures']()));

        geojsons['features'].map((geojson) => {
            var geojson2 = $.extend(true, {}, geojson, geojson_query);
            if (JSON.stringify(geojson2) === JSON.stringify(geojson)) {
                ret.push(geojson);
            }
        });

        return ret ? ret[0] : null;
    }
    */

    getFeatureFromElementId(elementid: Array<any>): ol.Feature {
        if (elementid && elementid.length > 0) {
            var features = this.source['getFeatures']();
            for (var i in features) {
                if (JSON.stringify(features[i].get('elementid')) == JSON.stringify(elementid)) return features[i];
            }
        }

        return null;
    }

    getGeoJSONFromFeature(feature?: ol.Feature): string {
        var options = {
            //dataProjection: this.getProjection(),
            // TODO: check if correct
            dataProjection: null,
            featureProjection: this.getProjection()
        };
        return (new ol.format.GeoJSON()).writeFeature(feature, options);
    }

    selectFeature(feature?: ol.Feature): void {
        var features = this.getSelectedFeatures();
        features.clear();
        if (feature) features.push(feature);
    }

    zoomToFeature(feature?: ol.Feature, onlyIfOutOfFrame = false): void {
        if (feature) {
            var featureExtent = feature.getGeometry().getExtent();
            // TODO: ideally we might want to make minimal changes to zoom level
            // and framing to enclose the feature.
            // Currently we just make the best fit.
            if (!onlyIfOutOfFrame || !ol.extent.containsExtent(this.map.getView().calculateExtent(this.map.getSize()), featureExtent)) {
                this.map.getView().fit(featureExtent, this.map.getSize());
            }
        }
    }

    getProjection(): ol.proj.Projection {
        return this.map.getView().getProjection();
    }

    addAnnotations(annotations?: Array<any>): void {
        var geojsonObject = {
            'type': 'FeatureCollection',
            'crs': {
                'type': 'name',
                'properties': {
                }
            },
            'features': annotations.map((v) => { return v.geojson })
        };
        var options = {
            //dataProjection: this.getProjection(),
            // TODO: check if correct
            dataProjection: null,
            featureProjection: this.getProjection()
        };
        var features = (new ol.format.GeoJSON()).readFeatures(JSON.stringify(geojsonObject), options);
        this.source.addFeatures(features);
    }

    /**
     * Register an event listener for the OL features
     *
     * listener: function({annotator: this, action: 'select'|'unselect'|'changed'|'deleted'|'hovered'})
     */
    addListener(listener): void {
        var features = this.getSelectedFeatures();
        features.on('add', () => { var e = { annotator: this, action: 'select' }; listener(e); });
        features.on('remove', () => { var e = { annotator: this, action: 'unselect' }; listener(e); });

        this.interactions.select['on']('hover', (event) => { var e = { annotator: this, action: 'hover', features: [event['feature']] }; listener(e); });

        //features.on('deleted', (event) => {var e = {annotator: this, action: 'deleted', features: event['features']}; listener(e);});
        this.source['on']('changefeature', (event) => {
            if (!this.interactions.isStarted()) {
                var e = { annotator: this, action: 'changed', features: [event['feature']] };
                listener(e);
            }
        });
        this.source['on']('removefeature', (event) => { var e = { annotator: this, action: 'deleted', features: [event['feature']] }; listener(e); });

        var e = { annotator: this, action: 'init' };
        listener(e);
    }

    getStyles(part?: string): ol.style.Style {
        var ret: ol.style.Style = null;

        if (part === 'select') {
            // TODO: avoid creating new style object each time!!!
            if (this.theme && this.theme === 'hidden') {
                ret = new ol.style.Style({
                    fill: new ol.style.Fill({
                        color: 'rgba(255, 255, 255, 0.07)'
                    }),
                    stroke: new ol.style.Stroke({
                        color: 'rgba(0,153,255, 0.4)',
                        width: 3
                    }),
                })
            } else {
                ret = new ol.style.Style({
                    fill: new ol.style.Fill({
                        color: 'rgba(255, 255, 255, 0.07)'
                    }),
                    stroke: new ol.style.Stroke({
                        color: 'rgba(0,153,255, 1)',
                        width: 3
                    }),
                })
            }
        } else {
            ret = new ol.style.Style({
                fill: new ol.style.Fill({
                    color: 'rgba(255, 255, 255, 0.07)'
                }),
                stroke: new ol.style.Stroke({
                    color: '#ffcc33',
                    width: 2
                }),
                image: new ol.style.Circle({
                    radius: 7,
                    fill: new ol.style.Fill({
                        color: '#ffcc33'
                    })
                })
            });
        }

        return ret;
    }
}


var example_link_in_geojson = [
    [["", "clause"], ["type", "address"]], // deprecated
    {
        "type": "Feature",
        id: 101, // DB: Annotation.id
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[270, -1632], [270, -984], [3006, -984], [3006, -1632], [270, -1632]]],
            "properties": {
                elementid: [["", "clause"], ["type", "address"]], // DB: TextAnnotation.elementid
                clientid: '3812738127319:1223', // DB: TextAnnotation.clientid
            }
        }
    }
];

/*

------------
annotation.12c61fcb81d0.js:79 pointermove
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 pointermove
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 pointerdown
annotation.12c61fcb81d0.js:83 CLICK ACTIVATE DRAW
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 pointerup
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 click
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 pointermove
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 singleclick
annotation.12c61fcb81d0.js:122 DRAW condition pointerdown
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 pointerdown
annotation.12c61fcb81d0.js:83 CLICK ACTIVATE DRAW
annotation.12c61fcb81d0.js:136 DRAW START
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 pointerup
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 click
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 pointermove
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 singleclick
annotation.12c61fcb81d0.js:78 ------------
annotation.12c61fcb81d0.js:79 pointermove
*/
