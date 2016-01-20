/**
 * New operations / modes /controls for Open layers 2:
 *      DuplicateFeature
 *      TransformFeature
 *      
 * This is modified version of the kcl-ddh/openlayers-image-annotation
 * TODO: fork it on github and commit the changes
 */
DuplicateFeature = OpenLayers.Class(OpenLayers.Control, {
	initialize: function(layer, options) {
		OpenLayers.Control.prototype.initialize.apply(this, [options]);
		this.layer = layer;
		this.handler = new OpenLayers.Handler.Feature(this, layer, {
			click: this.clickFeature
		});
	},
	clickFeature: function(feature) {
		var f = feature.clone();
		a = f;
		var pos = feature.geometry.bounds.getCenterLonLat();
		pos.lon += 30;
		pos.lat -= 30;
		this.layer.addFeatures([a]);
		var geo = new OpenLayers.LonLat(pos.lon, pos.lat);
		a.move(geo);

	},
	setMap: function(map) {
		this.handler.setMap(map);
		OpenLayers.Control.prototype.setMap.apply(this, arguments);
	},
	CLASS_NAME: 'OpenLayers.Control.DuplicateFeature'
});

/**
 * TransformFeature that support irregular transformations.
 */
TransformFeature = OpenLayers.Class(OpenLayers.Control.TransformFeature, {
	/**
	 * APIProperty: irregular
	 * {Boolean} Make scaling/resizing work irregularly. If true then
	 * dragging a handle causes the feature to resize in the direction
	 * of movement. If false then the feature resizes symetrically
	 * about it's center.
	 */
	irregular: false,
	/**
	 * Method: createBox
	 * Creates the box with all handles and transformation handles.
	 */
	createBox: function() {
		var control = this;

		this.center = new OpenLayers.Geometry.Point(0, 0);
		var box = new OpenLayers.Feature.Vector(
			new OpenLayers.Geometry.LineString([
				new OpenLayers.Geometry.Point(-1, -1),
				new OpenLayers.Geometry.Point(0, -1),
				new OpenLayers.Geometry.Point(1, -1),
				new OpenLayers.Geometry.Point(1, 0),
				new OpenLayers.Geometry.Point(1, 1),
				new OpenLayers.Geometry.Point(0, 1),
				new OpenLayers.Geometry.Point(-1, 1),
				new OpenLayers.Geometry.Point(-1, 0),
				new OpenLayers.Geometry.Point(-1, -1)
			]), null,
			typeof this.renderIntent == "string" ? null : this.renderIntent
		);

		// Override for box move - make sure that the center gets updated
		box.geometry.move = function(x, y) {
			control._moving = true;
			OpenLayers.Geometry.LineString.prototype.move.apply(this, arguments);
			control.center.move(x, y);
			delete control._moving;
		};

		// Overrides for vertex move, resize and rotate - make sure that
		// handle and rotationHandle geometries are also moved, resized and
		// rotated.
		var vertexMoveFn = function(x, y) {
			OpenLayers.Geometry.Point.prototype.move.apply(this, arguments);
			this._rotationHandle && this._rotationHandle.geometry.move(x, y);
			this._handle.geometry.move(x, y);
		};
		var vertexResizeFn = function(scale, center, ratio) {
			OpenLayers.Geometry.Point.prototype.resize.apply(this, arguments);
			this._rotationHandle && this._rotationHandle.geometry.resize(
				scale, center, ratio);
			this._handle.geometry.resize(scale, center, ratio);
		};
		var vertexRotateFn = function(angle, center) {
			OpenLayers.Geometry.Point.prototype.rotate.apply(this, arguments);
			this._rotationHandle && this._rotationHandle.geometry.rotate(
				angle, center);
			this._handle.geometry.rotate(angle, center);
		};

		// Override for handle move - make sure that the box and other handles
		// are updated, and finally transform the feature.
		var handleMoveFn = function(x, y) {
			var oldX = this.x,
				oldY = this.y;
			OpenLayers.Geometry.Point.prototype.move.call(this, x, y);
			if (control._moving) {
				return;
			}
			var evt = control.dragControl.handlers.drag.evt;
			var preserveAspectRatio = !control._setfeature &&
				control.preserveAspectRatio;
			var reshape = !preserveAspectRatio && !(evt && evt.shiftKey);
			var oldGeom = new OpenLayers.Geometry.Point(oldX, oldY);
			var centerGeometry = control.center;
			this.rotate(-control.rotation, centerGeometry);
			oldGeom.rotate(-control.rotation, centerGeometry);
			var dx1 = this.x - centerGeometry.x;
			var dy1 = this.y - centerGeometry.y;
			var dx0 = dx1 - (this.x - oldGeom.x);
			var dy0 = dy1 - (this.y - oldGeom.y);

			// jvieira: patch to support irregular transformations
			if (control.irregular && !control._setfeature) {
				dx1 -= (this.x - oldGeom.x) / 2;
				dy1 -= (this.y - oldGeom.y) / 2;
			}
			// end patch

			this.x = oldX;
			this.y = oldY;
			var scale, ratio = 1;
			if (reshape) {
				scale = Math.abs(dy0) < 0.00001 ? 1 : dy1 / dy0;
				ratio = (Math.abs(dx0) < 0.00001 ? 1 : (dx1 / dx0)) / scale;
			} else {
				var l0 = Math.sqrt((dx0 * dx0) + (dy0 * dy0));
				var l1 = Math.sqrt((dx1 * dx1) + (dy1 * dy1));
				scale = l1 / l0;
			}

			// rotate the box to 0 before resizing - saves us some
			// calculations and is inexpensive because we don't drawFeature.
			control._moving = true;
			control.box.geometry.rotate(-control.rotation, centerGeometry);
			delete control._moving;

			control.box.geometry.resize(scale, centerGeometry, ratio);
			control.box.geometry.rotate(control.rotation, centerGeometry);
			control.transformFeature({
				scale: scale,
				ratio: ratio
			});

			// jvieira: patch to support irregular transformations
			if (control.irregular && !control._setfeature) {
				var newCenter = centerGeometry.clone();
				newCenter.x += Math.abs(oldX - centerGeometry.x) < 0.00001 ? 0 : (this.x - oldX);
				newCenter.y += Math.abs(oldY - centerGeometry.y) < 0.00001 ? 0 : (this.y - oldY);
				control.box.geometry.move(this.x - oldX, this.y - oldY);
				control.transformFeature({
					center: newCenter
				});
			}
			// end patch
		};

		// Override for rotation handle move - make sure that the box and
		// other handles are updated, and finally transform the feature.
		var rotationHandleMoveFn = function(x, y) {
			var oldX = this.x,
				oldY = this.y;
			OpenLayers.Geometry.Point.prototype.move.call(this, x, y);
			if (control._moving) {
				return;
			}
			var evt = control.dragControl.handlers.drag.evt;
			var constrain = (evt && evt.shiftKey) ? 45 : 1;
			var centerGeometry = control.center;
			var dx1 = this.x - centerGeometry.x;
			var dy1 = this.y - centerGeometry.y;
			var dx0 = dx1 - x;
			var dy0 = dy1 - y;
			this.x = oldX;
			this.y = oldY;
			var a0 = Math.atan2(dy0, dx0);
			var a1 = Math.atan2(dy1, dx1);
			var angle = a1 - a0;
			angle *= 180 / Math.PI;
			control._angle = (control._angle + angle) % 360;
			var diff = control.rotation % constrain;
			if (Math.abs(control._angle) >= constrain || diff !== 0) {
				angle = Math.round(control._angle / constrain) * constrain -
					diff;
				control._angle = 0;
				control.box.geometry.rotate(angle, centerGeometry);
				control.transformFeature({
					rotation: angle
				});
			}
		};

		var handles = new Array(8);
		var rotationHandles = new Array(4);
		var geom, handle, rotationHandle;
		for (var i = 0; i < 8; ++i) {
			geom = box.geometry.components[i];
			handle = new OpenLayers.Feature.Vector(geom.clone(), null,
				typeof this.renderIntent == "string" ? null :
				this.renderIntent);
			if (i % 2 == 0) {
				rotationHandle = new OpenLayers.Feature.Vector(geom.clone(),
					null, typeof this.rotationHandleSymbolizer == "string" ?
					null : this.rotationHandleSymbolizer);
				rotationHandle.geometry.move = rotationHandleMoveFn;
				geom._rotationHandle = rotationHandle;
				rotationHandles[i / 2] = rotationHandle;
			}
			geom.move = vertexMoveFn;
			geom.resize = vertexResizeFn;
			geom.rotate = vertexRotateFn;
			handle.geometry.move = handleMoveFn;
			geom._handle = handle;
			handles[i] = handle;
		}

		this.box = box;
		this.rotationHandles = rotationHandles;
		this.handles = handles;
	},
});
