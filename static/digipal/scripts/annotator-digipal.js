// inherits from Annotator
DigipalAnnotator.prototype = new Annotator();

// corrects the contructor pointer because it points to Annotator
DigipalAnnotator.prototype.constructor = DigipalAnnotator;

/**
 * Annotator implementation for DigiPal.
 *
 * @param imageUrl
 *              URL of the image to annotate.
 * @param imageWidth
 *              Width of the image to annotate.
 * @param imageHeight
 *              Height of the image to annotate.
 * @param imageServerUrl
 *              URL of the image on an image server.
 */
function DigipalAnnotator(mediaUrl, imageUrl, imageWidth, imageHeight,
                                                    imageServerUrl, isAdmin) {
    if (imageServerUrl && imageServerUrl != 'None' && imageServerUrl.length > 0) {
        Annotator.call(this, imageServerUrl, imageWidth, imageHeight, true);
    } else {
        Annotator.call(this, imageUrl, imageWidth, imageHeight, false);
    }
    this.annotations = null;
    this.isAdmin = isAdmin;
    this.mediaUrl = mediaUrl;
    this.deleteFeature.panel_div.title = 'Delete (ctrl + d)';
    this.modifyFeature.panel_div.title = 'Modify (ctrl + m)';
    this.transformFeature.panel_div.title = 'Transform (ctrl + t)';
    this.duplicateFeature.panel_div.title = 'Duplicate (ctrl + d)';
    this.polygonFeature.panel_div.title = 'Draw Polygon (ctrl + p)';
    this.rectangleFeature.panel_div.title = 'Draw Rectangle (ctrl + r)';
    this.selectFeature.panel_div.title = 'Select (ctrl + f)';
    this.dragFeature.panel_div.title = 'Drag (ctrl + w)';
    this.zoomBoxFeature.panel_div.title = 'Zoom (ctrl + z)';
    this.saveButton.panel_div.title = 'Save (ctrl + s)';
}

/**
 * Function that is called after a feature is selected.
 *
 * @param event
 *              The select event.
 */

DigipalAnnotator.prototype.onFeatureSelect = function(event) {
    this.selectedFeature = event.feature;
    if ($('#id_hide').prop('checked')) {
        var layer = this.vectorLayer;

        for (var i = 0; i < layer.features.length; i++) {
            var f = layer.features[i];

            if (event.feature.id != f.id) {
                f.style = {};
                f.style.display = 'none';
            }
        }

        layer.redraw();
    }
    this.showAnnotation(event.feature);
};

DigipalAnnotator.prototype.removeDuplicate = function(element, attribute, text){
    var seen = {};
    $(element).each(function() {
        if(text == true){
          var txt = $(this).text();
          attribute = null;
        } else {
          var txt = $(this).attr(attribute);
        }
        if (seen[txt])
            $(this).remove();
        else
            seen[txt] = true;
    });
  }

 DigipalAnnotator.prototype.filterAnnotation = function(checkboxes){
    var _self = this;
    features = _self.vectorLayer.features;
    for(i in features){
        if(!($(checkboxes).is(':checked'))){
          if($(checkboxes).val() == features[i].feature){
            features[i].style = {'fillOpacity': 0, 'strokeOpacity': 0};
            _self.vectorLayer.redraw();
          }
        } else {
          if($(checkboxes).val() == features[i].feature){
            features[i].style = '';
            _self.vectorLayer.redraw();
          }
        }
    }
};

DigipalAnnotator.prototype.filterCheckboxes = function(checkboxes, check){
    var _self = this;
    if(check == 'check'){
        $(checkboxes).attr('checked', true);
        features = _self.vectorLayer.features;
        for(i = 0; i < features.length; i++){
            features[i].style = '';
            _self.vectorLayer.redraw();
        }
    } else if(check == 'uncheck'){
        $(checkboxes).attr('checked', false);
        features = _self.vectorLayer.features;
        for(i = 0; i < features.length; i++){
            features[i].style = {'fillOpacity': 0, 'strokeOpacity': 0};
            _self.vectorLayer.redraw();
        }
    }
};
/**
 * Function that is called after a feature is unselected.
 *
 * @param event
 *              The unselect event.
 */
DigipalAnnotator.prototype.onFeatureUnSelect = function(event) {
    var _self = this;

    if ($('#id_hide').prop('checked')) {
        for (i = 0; i < _self.vectorLayer.features.length; i++) {
            var f = _self.vectorLayer.features[i];

            if (_self.selectedFeature.id != f.id) {
                f.style = null;
            }
        }

        this.vectorLayer.redraw();
    }

    this.selectedFeature = null;
};

/**
 * Shows the annotation details for the given feature.
 *
 * @param feature
 *              The feature to display the annotation.
 */
DigipalAnnotator.prototype.showAnnotation = function(feature) {
    if (this.annotations) {
        var annotation = null;
       for (var idx in this.annotations) {
            annotation = this.annotations[idx];

            if (annotation.vector_id == feature.id) {
                break;
            } else {
                annotation = null;
            }
        }
        if(annotation){
            showBox(annotation);
            $('#id_hand').val(annotation.hand_id);
            $('#id_status').val(annotation.status_id);
            $('#id_before').val(getKeyFromObjField(annotation, 'before'));
            $('#id_allograph').val(getKeyFromObjField(annotation, 'allograph'));
            $('#id_after').val(getKeyFromObjField(annotation, 'after'));
            $('#id_display_note').val(annotation.display_note);
            $('#id_internal_note').val(annotation.internal_note);

            updateFeatureSelect(annotation.features);
            
        }
    }
    
};

/**
 * Updates the feature select according to the currently selected allograph.
 */
function updateFeatureSelect(currentFeatures) {
    $('#id_feature option').each(function() {
        $(this).remove();
    });

    $.getJSON('allograph/' + $('#id_allograph option:selected').val() + '/features/',
                function(data) {
        $.each(data, function(idx) {
            component = data[idx].name;
            component_id = data[idx].id;
            features = data[idx].features;

            $.each(features, function(idx) {
                var value = component_id + '::' + features[idx].id;

                $('#id_feature').append($('<option>', {
                    value : value
                }).text(component + ': ' + features[idx].name));
            });

            if (currentFeatures) {
                $('#id_feature option').each(function() {
                    if (currentFeatures.indexOf($(this).val()) >= 0) {
                        $(this).attr('selected', 'selected');
                    }
                });
            }
        });

        $('#id_feature').multiselect('refresh');

    });
}


isEmpty = function(obj) {
    for (var prop in obj) {
        if (obj.hasOwnProperty(prop)) return false;
    }
    return true;
};


function showBox(selectedFeature){

    id = Math.random().toString(36).substring(7);
    $('#annotations').append('<div id="dialog' + id + '"></div>');
    url = 'graph/' + selectedFeature.graph + '/features/';
    $('#dialog' + id).dialog({
        draggable: true,
        height: 270, 
        title: function(){
            if(annotator.isAdmin == "True"){
                title = selectedFeature.feature +
                 " <a style='position:absolute;right:35px;top:2px;' class='btn' href='/admin/digipal/graph/" +
                 selectedFeature.graph + "/'>Edit</a>";
            } else {
                title = selectedFeature.feature;
            }
            return title;
        },
        position: [250 + Math.floor(Math.random() * 150), 130 + Math.floor(Math.random() * 150)]
    });
    $.ajax({
        url: url,
        dataType: 'json',
        cache: false,
        type: 'GET',
        async: true,
        success:function(data){
            s = '<ul>';
            if(!isEmpty(data)){
                for(i = 0; i < data.length; i++){
                    component = data[i]['name'];
                    s += "<li class='component'><b>" + component + "</b></li>"
                    for (j = 0; j < data[i]['feature'].length; j++){
                        s += "<li class='feature'>" + (data[i]['feature'][j]) + "</li>";
                    }
                }
            } else {
                s += "<li class='component'>This graph has not yet been described.</li>"
            }
            s += "</ul>";
            $('#dialog' + id).html(s);
        }
    });
}


/**
 * Some fields are stored in the database as key:value. This function returns
 * the key.
 */
function getKeyFromObjField(obj, field) {
    var key = null;

    if (obj[field]) {
        key = obj[field];
        key = key.substring(0, key.indexOf('::'));
    }

    return key;
}

/**
 * This function returns the value.
 */
function getValueFromObjField(obj, field) {
    var value = null;

    if (obj[field]) {
        value = obj[field];
        value = value.substring(value.indexOf('::') + 1);
    }

    return value;
}

/**
 * Updates the select element according to the given values.
 *
 * @param elementId
 *              The id of select element to update.
 * @param values
 *              The values to update the element with.
 */
function updateSelectOptions(elementId, values) {
    
    $('#' + elementId + ' :selected').removeAttr('selected');

    var detail = '';

    for ( var idx in values) {
        var key = values[idx].substring(0, values[idx].indexOf(':'));
        var value = values[idx].substring(values[idx].indexOf(':') + 1);

        $('#' + elementId + ' option').each(function() {
            if ($(this).val() == key) {
                $(this).attr('selected', 'selected');

                detail += value + '; ';
            }
        });
    }

    $('#' + elementId).multiselect('refresh');

    if (detail) {
        $('#' + elementId + '_detail').text(detail);
    } else {
        $('#' + elementId + '_detail').text('-');
    }
}

/**
 * Updates the Feature select field according to the given letter and
 * annotation.
 *
 * @param letterId
 *              The id of the letter.
 * @param annotation
 *              The annotation.
 */
function updateOptionsForLetter(letterId, annotation) {
    $.getJSON('letter/' + letterId + '/features/', function(data) {
        if (data.has_minim) {
            enableMultiSelect('id_minim');
        } else {
            disableMultiSelect('id_minim');
        }
        if (data.has_ascender) {
            enableMultiSelect('id_ascender');
        } else {
            disableMultiSelect('id_ascender');
        }
        if (data.has_descender) {
            enableMultiSelect('id_descender');
        } else {
            disableMultiSelect('id_descender');
        }

        $('#id_feature option').each(function() {
            $(this).remove();
        });

        $('#id_feature').multiselect('refresh');

        var features = data.features;
        
        $.each(features, function(idx) {
            var value = features[idx];
            $('#id_feature').append($('<option>', {
                value : idx
            }).text(value));
        });

        $('#id_feature').multiselect('refresh');

        if (annotation !== null) {
            updateSelectOptions('id_feature', annotation.fields['feature']);
        }
    });
}

/**
 * Enables a multiselect element given its id.
 *
 * @param elementId
 *              The id of the element to enable.
 */
function enableMultiSelect(elementId) {
    $('#' + elementId).removeAttr('disabled');
    $('#' + elementId).multiselect('enable');
}

/**
 * Disables a multiselect element given its id.
 *
 * @param elementId
 *              The id of the element to disable.
 */
function disableMultiSelect(elementId) {
    $('#' + elementId + ' option').each(function() {
        $(this).removeAttr('selected');
    });
    $('#' + elementId).multiselect('refresh');
    $('#' + elementId).attr('disabled', 'disabled');
    $('#' + elementId).multiselect('disable');
}

/**
 * Deletes the annotation for the selected feature.
 *
 * @param layer
 *              The feature's layer.
 * @param feature
 *              The feature to delete the annotation for.
 */
DigipalAnnotator.prototype.deleteAnnotation = function(layer, feature) {
    var _self = this;

    var msg = 'You are about to delete this annotation. It cannot be restored at a later time! Continue?';
    var doDelete = confirm(msg);

    if (doDelete && feature !== null) {
    var featureId = feature.id;

    updateStatus('-');
        layer.destroyFeatures([ feature ]);

        $.ajax({
            url : 'delete/' + featureId + '/',
            data : '',
            error : function(xhr, textStatus, errorThrown) {
                alert('Error: ' + textStatus);
            },
            success : function(data) {
                if (data.success === false) {
                    handleErrors(data);
                } else {
                    $('#status').addClass('alert alert-error');
                    updateStatus('Deleted annotation.');
                    _self.loadAnnotations();
                }
            }
        });
    }
};

/**
 * Deletes the annotation for the feature with the given id.
 *
 * @param id
 *              The feature id.
 */
function deleteAnnotationByFeatureId(id) {
    annotator.selectFeatureByIdAndCentre(id);
    annotator.deleteAnnotation(annotator.vectorLayer, annotator.vectorLayer.getFeatureById(id));
}

/**
 * Saves an annotation for the currently selected feature.
 */
DigipalAnnotator.prototype.saveAnnotation = function() {
  updateStatus('-');

    if (this.modifyFeature.feature) {
        this.modifyFeature.selectControl.unselectAll();
    }

    if (this.selectedFeature) {
        var form = $('#frmAnnotation');

        save('save', this.selectedFeature, form.serialize());

        this.loadAnnotations();
    } else {
        var form = $('#frmAnnotation');
        
        for ( var idx = 0; idx < this.vectorLayer.features.length; idx++) {
            var feature = this.vectorLayer.features[idx];

            if (!feature.attributes.saved) {
                save('save', feature, form.serialize());
            }
        }

        this.loadAnnotations();
        this.vectorLayer.redraw();
    }
};

/**
 * Executes an Ajax call to save a feature/annotation.
 *
 * @param url
 *              The save url.
 * @param feature
 *              The feature.
 * @param data
 *              Additional data for the annotation.
 */
function save(url, feature, data) {
    var id = feature.id;
    
    annotator.setSavedAttribute(feature, Annotator.SAVED, false);
    
    var geoJson = annotator.format.write(feature);
    
    $.ajax({
        url : url + '/' + id + '/?geo_json=' + geoJson,
        data : data,
        error : function(xhr, textStatus, errorThrown) {
            $('#status').attr('class', 'alert alert-error');
            updateStatus(textStatus);
            annotator.setSavedAttribute(feature, Annotator.UNSAVED, false);
        },
        success : function(data) {
            console.log(data)
            if (data.success === false) {
                handleErrors(data);
            } else {
                $('#status').attr('class', 'alert alert-success');
                updateStatus('Saved annotation.');
            }
        }
    });
}

/**
 * Displays an alert for each error in the data.
 *
 * @param data
 *              Object with errors.
 */
function handleErrors(data){
    $('#status').attr('class', 'alert alert-error');
    errors = '';
    for ( var e in data.errors) {
        errors += e;
    }
    updateStatus(errors);
}

/**
 * Updates the status message of the last operation.
 *
 * @param msg
 *              Status message to display.
 */
function updateStatus(msg) {
    $('#status').text(msg);
    //
    // GN: bugfix, JIRA 77
    // The message will push the openlayer div down and cause
    // the drawing symbol to appear below the mosue cursor.
    // To avoid this we force a render on the OL map to tell it 
    // to refresh it internal location variable.
    //
    if (typeof annotator !== 'undefined') {
    	annotator.map.render(annotator.map.div);
    }
}

/**
 * Loads existing vectors into the vectors layer.
 *
 * @param layer
 *              The layer where the vectors will be rendered.
 */
DigipalAnnotator.prototype.loadVectors = function() {
    var map = this.map;
    var layer = this.vectorLayer;
    var format = this.format;
    $.getJSON('vectors/', function(data) {
        var features = [];
        $.each(data, function(id, vector) {
            var f = format.read(vector)[0];
            f.id = id;
            $.getJSON('annotations/', function(annotations){
                $.each(annotations, function(index) {
                    allograph = annotations[index]['feature'];
                    graph = annotations[index]['graph'];
                    if(f.id == annotations[index]['vector_id']){
                        f['feature'] = allograph;
                        f['graph'] = graph;
                    }
                });
            });
            features.push(f);
        });

        // adds all the vectors to the vector layer
        layer.addFeatures(features);

        // zooms to the max extent of the map area
        map.zoomToMaxExtent();
    });
};

/**
 * Loads existing annotations.
 */
DigipalAnnotator.prototype.loadAnnotations = function() {
    var _self = this;
    var selectedFeature = this.selectedFeature;

    $.getJSON('annotations/', function(data) {
        _self.annotations = data;
        //showAnnotationsOverview(data);
    });
    
};

/* FullScreen Mode */

DigipalAnnotator.prototype.full_Screen = function(){
    if(!(this.fullScreen.active) || (this.fullScreen.active == null) || (this.fullScreen.active == undefined)){
        $('#map').css({'width': '100%', 'height': '100%', 'position': 'absolute', 'top': 0, 'left': 0, 'z-index': 1000,
'background-color': 'rgba(0, 0, 0, 0.95)'});
        this.fullScreen.active = true;
        $(document).keyup(function(e){
            if(e.keyCode == 27){
                 $('#map').attr('style', null);
                 this.fullScreen.active = null;
            }
        });
        $('.olControlFullScreenFeatureItemInactive').css('background-image', 'url(/static/digipal/scripts/libs/openlayers/theme/default/img/fullscreen_on.gif)');
        $('.olControlFullScreenFeatureItemInactive').attr('title','Deactivate Full Screen')
    } else {
        $('#map').attr('style', null);
        this.fullScreen.active = null;
        $('.olControlFullScreenFeatureItemInactive').css('background-image', 'url(/static/digipal/scripts/libs/openlayers/theme/default/img/fullscreen.gif)');
        $('.olControlFullScreenFeatureItemInactive').attr('title','Activate Full Screen')
    }
}

/* End FullScreen Mode */

/**
 * Displays annotations overview.
 *
 * @param data
 *              The annotation data.
 */
function showAnnotationsOverview(data) {
    var _self = this.annotator;
    
    $('#overview').children().remove();

    var previousLetter = '';
    var letterCounter = 0;
    
    $.each(data, function(idx) {
        var a = data[idx];
        var fid = a.vector_id;
        var letter = a.allograph;

        var li = document.createElement('li');
        li.setAttribute('id', fid);
        
        if (letter != previousLetter) {
            letterCounter = 0;
        }
        
        previousLetter = letter;
        
        li.innerHTML = '<dfn>' + (letter ? letter : '-')
                + ++letterCounter
                + '</dfn>'
                + '<a href="javascript: annotator.selectFeatureByIdAndCentre(\''
                + fid
                + '\');"'
                + 'title="'
                + fid
                + '">'
                + '<img src="' + _self.mediaUrl
                + 'uploads/annotations/'
                + idx
                + '.jpg" width="15px" />'
                + '</a>';

        $('#overview').append(li);
    });
}


/**
 * Turns on keyboard shortcuts for the controls.
 
DigipalAnnotator.prototype.activateKeyboardShortcuts = function() {
    var _self = this;
    var activeControls = _self.map.getControlsBy('active', true);

    $(document).bind('keydown', 'ctrl+backspace', function(event) {
        activeControls[activeControls.length - 1].deactivate();
        _self.deleteFeature.activate();
        return false;
    });
    
    $(document).bind('keydown', 'ctrl+m', function(event) {
        activeControls[activeControls.length - 1].deactivate();
        _self.modifyFeature.activate();
        return false;
    });
    $(document).bind('keydown', 'ctrl+t', function(event) {
        activeControls[activeControls.length - 1].deactivate();
        _self.transformFeature.activate();
        return false;
    });
    $(document).bind('keydown', 'ctrl+d', function(event) {
        activeControls[activeControls.length - 1].deactivate();
        _self.duplicateFeature.activate();
        return false;
    });
    $(document).bind('keydown', 'ctrl+p', function(event) {
        activeControls[activeControls.length - 1].deactivate();
        _self.polygonFeature.activate();
        return false;
    });
    $(document).bind('keydown', 'ctrl+r', function(event) {
        activeControls[activeControls.length - 1].deactivate();
        _self.rectangleFeature.activate();
        return false;
    });
    $(document).bind('keydown', 'ctrl+f', function(event) {
        activeControls[activeControls.length - 1].deactivate();
        _self.selectFeature.activate();
        return false;
    });
    $(document).bind('keydown', 'ctrl+w', function(event) {
        activeControls[activeControls.length - 1].deactivate();
        _self.dragFeature.activate();
        return false;
    });
    $(document).bind('keydown', 'ctrl+z', function(event) {
        activeControls[activeControls.length - 1].deactivate();
        _self.zoomBoxFeature.activate();
        return false;
    });
    $(document).bind('keydown', 'ctrl+s', function(event) {
        _self.saveButton.trigger();
        return false;
    });
};
*/
