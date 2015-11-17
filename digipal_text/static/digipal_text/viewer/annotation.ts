/// <reference path="../dts/jquery.d.ts"/>
/// <reference path="../dts/openlayers.d.ts"/>

class AnnotatorOL3 {
    map: ol.Map;
    // source
    source: ol.source.Vector;
    // the annotation layer
    layer: ol.layer.Vector;
    //
    interaction: ol.interaction.Draw;
   
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
        
        this.interaction = new ol.interaction.Draw({
            source: this.source,
            type: /** @type {ol.geom.GeometryType} */ (value),
            geometryFunction: geometryFunction,
            maxPoints: maxPoints
        });
        this.map.addInteraction(this.interaction);
    }
    
    
}
