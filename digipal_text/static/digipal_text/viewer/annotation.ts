/// <reference path="../dts/jquery.d.ts"/>
/// <reference path="../dts/openlayers.d.ts"/>

/**
 * Extension of ol.interaction.Draw
 * with awareness of wether the drawing operation is started.
 */
class Draw extends ol.interaction.Draw {
    started = false;
    
    constructor(options?: olx.interaction.DrawOptions) {
        super(options);
        
        // draw is a reference to ol.interaction.Draw
        this.on('drawstart', function(evt){
            this.started = true;
        });
        
        this.on('drawend', function(evt){
            this.started = false;
        });
    }
    
    setActive(active: boolean): void {
        super.setActive(active);
        if (!active) {
            this.started = false;
        }
    }
    
    /**
     * Returns true if feature drawing has started
     */
    isStarted(): boolean {
        return this.started;
    }
    
}

class Select extends ol.interaction.Select {

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

class AOL3Interactions {
    controler: ol.interaction.Interaction;
    draw: Draw;
    select: Select;
    
    setInteraction(key: string, interaction: ol.interaction.Interaction, map: ol.Map) {
        if (this[key]) map.removeInteraction(interaction);
        this[key] = interaction;
        map.addInteraction(interaction);
    }
    
    setActive(key: string, active: boolean) {
        this[key].setActive(active);
    }
    
    /**
     * Switch between select/draw modes
     * @param {string} key: the key of the interaction to switch to
     */
    switch(key: string) {
        var alternatives = {'select': 'draw', 'draw': 'select'};
        var alt = alternatives[key];
        this.setActive(key, true);
        if (alt) {
            this.setActive(alt, false);
        }
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
    // events
    events = {startDrawing: null, stopDrawing: null};
    // 
    lastDrawnFeature: ol.Feature;
    
    constructor(map: ol.Map) {
        this.map = map;
        
        this.addAnnotationLayer();
        
        this.initInteractions();
    }
    
    addAnnotationLayer(): void {
        // create layer
        this.source = new ol.source.Vector({wrapX: false});
        
        this.layer = new ol.layer.Vector({
          source: this.source,
          style: new ol.style.Style({
            fill: new ol.style.Fill({
              color: 'rgba(255, 255, 255, 0.2)'
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
          })
        });
        
        this.map.addLayer(this.layer);
    }
    
    initInteractions(): void {
        // Interactions are processed in reverse order:
        this.initDraw();
        this.initSelect();
        // Selector BEFORE draw and select 
        // so we can chose which one handle the current event
        this.initInteractionSelector();
    }
    
    initInteractionSelector(): void {
        
        var options = {handleEvent: (e: ol.MapBrowserEvent): boolean => {
            var ctrl = e.originalEvent['ctrlKey'];
            var type = e['type'];
            var key = e['browserEvent']['keyCode'];
            
            if (!((type === 'pointermove') || 
                (type === 'key' && ctrl))) { 
                console.log('> ' + type + ' <------------------');
                console.log(e);
            }
            
            // CTRL + pointerdown
            if (type === 'pointerdown') {
                if (ctrl && !this.interactions.draw.isStarted()) {
                    console.log('CLICK ACTIVATE DRAW');
                    this.interactions.switch('draw');
                }
            }
            
            if (type === 'key') {
                if (this.isDrawing()) {
                    // ESC / DEL
                    if ((key === 46) || (key === 27)) {
                        // abort drawing
                        this.interactions.switch('select');
                    }
                } else {
                    // DEL remove feature
                    if (key === 46) {
                        this.interactions.select.removeFeatures(this.source);
                    }
                }
            }
            
            return true;
         }};
        var interaction = new ol.interaction.Interaction(options);
        
        this.interactions.setInteraction('controller', interaction, this.map);
    }
    
    isDrawing(): boolean {
        return this.interactions.draw.isStarted();
    }

    initSelect(): void {
        var interaction = new Select({
            condition: ol.events.condition.click
        });
        
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
            
            console.log('SELECT '+e['type']);
            var features = this.getSelectedFeatures();
            if (features.getLength() > 0) {
                this.showFeatureInfo(features.item(0));
            } else {
                console.log('No feature selected');
            }
            //console.log(e);
        });
        
        this.interactions.setInteraction('select', interaction, this.map);
    }
    
    showFeatureInfo(feature: ol.Feature): void {
        console.log(feature.getId() + ': ' + feature.getGeometry().getExtent().join(','));        
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
            var ctrl = e.originalEvent['ctrlKey'];
            //var ctrl = ol.events.condition.platformModifierKeyOnly(e);
            
            console.log('DRAW condition '+e['type']);
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
            
            console.log('DRAW START');
        });
        interaction.on('drawend', (evt) => {
            //this.interactions.draw['isStarted'] = false;
            
            this.interactions.switch('select');
            
            // See select interaction. This is a work around.
            this.lastDrawnFeature = evt['feature'];
            
            console.log('DRAW END');
        });    

        this.interactions.setInteraction('draw', interaction, this.map);
    }
    
    getSelectedFeatures(): ol.Collection<ol.Feature> {
        return this.interactions.select.getFeatures();
    }
    
    selectFeature(feature?: ol.Feature): void {
        var features = this.getSelectedFeatures();
        features.clear();
        if (feature) features.push(feature);
    }
    
}
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
