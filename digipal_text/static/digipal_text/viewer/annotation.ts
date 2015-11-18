/// <reference path="../dts/jquery.d.ts"/>
/// <reference path="../dts/openlayers.d.ts"/>

/*
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
    
    isStarted(): boolean {
        return this.started;
    }
    
}
*/

class AnnotatorOL3 {
    map: ol.Map;
    // source
    source: ol.source.Vector;
    // the annotation layer
    layer: ol.layer.Vector;
    //
    interaction: ol.interaction.Draw;
    // events
    events = {startDrawing: null, stopDrawing: null};
   
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
        this.initDraw();
        this.initSelect();
    }

    initSelect(): void {
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

        if (this.interaction) this.map.removeInteraction(this.interaction);
        
        var condition = (e: ol.MapBrowserEvent): boolean => {
            var ctrl = e.originalEvent['ctrlKey'];
            //var ctrl = ol.events.condition.platformModifierKeyOnly(e);
            
            //console.log('' + ctrl + '' + ctrl2);
            return this.interaction['isStarted'] || ctrl;
        }
        
        this.interaction = new ol.interaction.Draw({
            source: this.source,
            type: (value),
            geometryFunction: geometryFunction,
            condition: condition,
            maxPoints: maxPoints
        });


        // draw is a reference to ol.interaction.Draw
        this.interaction.on('drawstart', (evt) =>{
            this.interaction['isStarted'] = true;
        });
        this.interaction.on('drawend', (evt) => {
            this.interaction['isStarted'] = false;
        });    

        this.map.addInteraction(this.interaction);
        
        /*
        this.events.startDrawing = this.map.on('pointerdrag', (e) => {
            // if (e.originalEvent.ctrlKey )
            // var coord = e.coordinate;
            console.log(e);
        });
        this.map.on('mouseup', (e) => {
            // if (e.originalEvent.ctrlKey )
            // var coord = e.coordinate;
            console.log('MOUSEUP');
        });
        */
    }
    
    
}
