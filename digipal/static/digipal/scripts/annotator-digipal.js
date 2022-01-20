/**
 * DigipalAnnotator: a class to kind of encapsulate the OpenLayers canvas and 
 *                  the annotation interactions and display
 * 
 * A lot of extra functions to deal with dialogs
 * 
 * TODO: IN DIRE NEED OF CLEAN UP AND REFACTORING!
 * 
 */

var SHOW_NOTE_ON_HOVER = false;

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

function DigipalAnnotator(mediaUrl, imageUrl, imageWidth, imageHeight, imageServerUrl, isAdmin) {
    if (imageServerUrl && imageServerUrl != 'None' && imageServerUrl.length) {
        Annotator.call(this, imageServerUrl, imageWidth, imageHeight, true);
    } else {
        Annotator.call(this, imageUrl, imageWidth, imageHeight, false);
    }

    this.annotations = null;
    this.annotating = true;
    this.has_changed = false;
    this.events = false;
    this.url_allographs = false;
    this.unsaved_annotations = [];
    this.isAdmin = isAdmin;
    this.mediaUrl = mediaUrl;
    this.allow_multiple_dialogs = false;
    this.boxes_on_click = false;
    this.deleteFeature.panel_div.title = 'Delete (del)';
    this.transformFeature.panel_div.title = 'Modify (m)';
    this.rectangleFeature.panel_div.title = 'Draw Annotation (d)';
    if (isAdmin !== 'True') {
        this.rectangleFeature.panel_div.title = 'Create Annotation (d)';
    }
    this.selectFeature.panel_div.title = 'Select (g)';
    this.zoomBoxFeature.panel_div.title = 'Zoom (z)';
    this.saveButton.panel_div.title = 'Save (s)';
    this.selectedAnnotations = [];
    this.cacheAnnotations = new AnnotationsCache();
    this.cacheHiddenFilters = [];

    var self = this;

    self.api = new DigipalAPI({
        crossDomain: false,
        root: '/digipal/api'
    });

    var _Star = new Star();

    this.isMobile = function() {
        return (window.innerWidth <= 800);
    };

    /**
     * Shows the annotation details for the given feature.
     *
     * @param feature
     *              The feature to display the annotation.
     */

    /*
     ** caching most used selectors
     */

    var number_allographs_element = $(".number_annotated_allographs .number-allographs");

    ////////////////////////////////////////
    
    this.set_focus_postponed = function() {
        window.dputils.postpone(function() {
            self.set_focus();
        });
    };

    this.set_focus = function() {
        // make sure the chosen dropdown is no longer highlighted
        var cls = 'chzn-container-active';
        $('.'+cls).removeClass(cls);
        // refocus OL
        //$('#map').focus();
        // If OL is bigger than the viewport, each time the
        // user close a drop down the focus would scroll back to
        // get the whole OL (pushing DD offscreen).
        // So we disable scrolling.
        window.dputils.focusWithoutScrolling($('#map'));
    };
    
    this.open_allograph_selector = function() {
        get_forms().allograph_form.trigger('liszt:open');
    };

    this.showAnnotation = function(feature) {
        var select_allograph = get_forms().allograph_form;

        if (feature) {
            stylize(feature, 'blue', 'blue', 0.4);
            self.vectorLayer.redraw();
        }

        var features = annotator.vectorLayer.features;
        var features_length = features.length;

        /*
        var i = 0;
        while (i < features_length && features[i].feature == feature.feature && features[i].stored) {
            i++;
        }
        */
        //number_allographs_element.html(i);

        if (self.annotations) {
            var annotation = self.vectorLayer.getFeatureById(feature.id);
            if (!annotation || !annotation.stored) {
                annotation = {};
            }
            showBox(annotation, function() {
                var allograph_id = $('#panelImageBox .allograph_form').val();
                var al = select_allograph.find('option:selected').text();

                self.annotationsGroup.check_if_linked($('.dialog_annotations'));
                if (annotator.selectedAnnotations.length > 1) {
                    detect_common_features_init();
                }
                highlight_vectors();
            });
        }
    };

    /*
        * function load_annotations
        @parameter callback
            - actions to be done after all the annotations get loaded
    */

    this.load_annotations = function(callback, isRefresh) {
        var request = $.getJSON(annotator.url_annotations, function(data) {
            annotator.annotations = data;
        });

        var chained = request.then(function(data) {

            var map = annotator.map;

            if (!isRefresh) {
                // zooms to the max extent of the map area
                map.zoomToMaxExtent();
            }

            var layer = annotator.vectorLayer;
            var format = annotator.format;
            var annotations = data;

            // Loading vectors

            $('#loading_allographs_image').remove();
            var features = [];
            var f;
            for (var i in annotations) {

                f = format.read(annotations[i].geo_json)[0];
                var allograph = annotations[i]['feature'];
                var character_id = annotations[i]['character_id'];
                var graph = annotations[i]['graph'];
                var character = annotations[i]['character'];
                var hand = annotations[i]['hand'];
                var image_id = annotations[i]['image_id'];
                var num_features = annotations[i]['num_features'];
                var display_note = annotations[i]['display_note'];
                var internal_note = annotations[i]['internal_note'];
                var allograph_id = annotations[i]['allograph_id'];
                var id = annotations[i]['id'];
                var is_editorial = annotations[i]['is_editorial'];
                if (graph || is_editorial) {
                    f.feature = allograph;
                    f.character_id = character_id;
                    f.graph = graph;
                    f.character = character;
                    f.hand = hand;
                    f.image_id = image_id;
                    f.num_features = num_features;
                    f.display_note = display_note;
                    f.internal_note = internal_note;
                    f.allograph_id = allograph_id;
                    if (graph) {
                        f.id = graph;
                    } else {
                        f.id = id;
                    }
                    f.is_editorial = is_editorial;
                    // it serves to differentiate stored and temporary annotations
                    f.stored = true;
                    f.linked_to = [];
                    /* annotator.vectorLayer.features is the array to access to all the features */
                    features.push(f);
                }
            }

            // adds all the vectors to the vector layer
            layer.addFeatures(features);
            var vectors = annotator.vectorLayer.features;

            var navigation = new OpenLayers.Control.Navigation({
                'zoomBoxEnabled': false,
                defaultDblClick: function(event) {
                    return;
                }
            });

            map.addControl(navigation);

            if (!annotator.events) {
                // GN: 2020 trying to fix a bug where dbl click event to open
                // an annotation popup is only declared after moving or zooming
                // the map! See below. Not sure at all why it was done that way.
                // It seems wasteful to call that EACH time those operations
                // happen. I.e. each time the events are destroyed and recreated!
                registerEvents();

                // var annotations_layer = $('#OpenLayers_Layer_Vector_27_svgRoot');
                map.events.register("moveend", map, function() {
                    registerEvents();
                    restoreFullscreenPositions();
                });

                map.events.register("zoomend", map, function() {
                    registerEvents();
                    restoreFullscreenPositions();
                });

            }

            if (callback) {
                $('#toolbar').fadeIn();

                if (self.hide_annotations && (self.isAdmin === 'True')) {
                    // Logged-in but Graphs content type is not enabled
                    // so we hide all the annotation tools.
                    // TODO: all the annotation tools
                    self.toolbar.toggle_tools(['.olControlDrawFeaturePolygon']);
                }

                callback(data); // calling all events on elements after all annotations get loaded
            }

        });
    };

    /**
     * Function that is called after a feature is selected.
     *
     * @param event
     *              The select event.
     */

    this.onFeatureSelect = function(event) {
        this.selectedFeature = event.feature;

        if (self.selectedFeature.linked_to && !$.isEmptyObject(self.selectedFeature.linked_to[0]) && allow_multiple()) {
            $.each(self.selectedFeature.linked_to[0], function(index, value) {
                if (value) {
                    annotator.selectedAnnotations.push(value);
                    select_feature(value);
                }
            });
            notifySelectedAnnotations();
        } else if (typeof self.selectedFeature.linked_to != 'undefined' && $.isEmptyObject(self.selectedFeature.linked_to[0]) && allow_multiple()) {
            annotator.selectedAnnotations.push(this.selectedFeature);
            select_feature(self.selectedFeature);
            notifySelectedAnnotations();
        } else {
            select_feature(this.selectedFeature);
        }

        restoreFullscreenPositions();
    };

    /**
     * Function that is called after a feature is unselected.
     *
     * @param event
     *              The unselect event.
     */

    this.onFeatureUnSelect = function(event, is_event) {
        var _self = this;
        var feature;
        if (is_event) {
            feature = event.feature;
        } else {
            feature = event;
        }
        var boxes = $('.dialog_annotations');
        if (allow_multiple()) {
            for (var i = 0; i < this.selectedAnnotations.length; i++) {
                if (feature.graph == this.selectedAnnotations[i].graph) {
                    this.selectedAnnotations.splice(i, 1);
                    i--;
                    break;
                }
            }
            if (this.selectedAnnotations.length && boxes.length && !annotator.allow_multiple_dialogs) {
                if (feature.graph & !$.isEmptyObject(feature.linked_to[0])) {
                    boxes.remove();
                }
            }
            if (!this.selectedAnnotations.length) {
                boxes.remove();
            }
            if (this.selectedAnnotations.length < 2) {
                var group_button = $('.link_graphs');
                group_button.addClass('disabled');
            }
            notifySelectedAnnotations();
        } else {
            if (!annotator.allow_multiple_dialogs) {
                boxes.remove();
            }
        }
        let style_name = 'undescribed';
        if (feature.described) {
            style_name = 'described';
        } else if (feature.is_editorial && $('#show_editorial_annotations').is(':checked')) {
            style_name = 'editorial';
        } else {
            if (feature.state == 'Insert' && $('.number_unsaved_allographs').hasClass('active') && !feature.stored) {
                style_name = 'unsaved';
            }
        }
        stylize_predefined(feature, style_name);
        this.vectorLayer.redraw();
        if (this.selectedAnnotations.length) {
            this.selectedFeature = this.selectedAnnotations[0];
        } else {
            this.selectedFeature = null;
        }
        //$(".number_annotated_allographs .number-allographs").html(0);
        restoreFullscreenPositions();
    };

    this.annotationsGroup = {

        linkAnnotations: function(dialog) {
            var self = this;
            var features = annotator.selectedAnnotations;
            if (features.length) {
                for (var i = 0; i < features.length; i++) {
                    if (!$.isEmptyObject(features[i].linked_to[0]) || typeof features[i].linked_to == 'undefined') {
                        features[i].linked_to = [];
                    }
                    var feature = {};
                    for (var j = 0; j < features.length; j++) {
                        feature[features[j].id] = features[j];
                    }
                    features[i].linked_to.push(feature);
                }
            }
            this.check_if_linked(dialog);
        },

        check_if_linked: function(dialog) {
            var self = this;
            if (!annotator.editorial.active && annotator.selectedFeature && annotator.isAdmin == 'True') {
                if (annotator.selectedFeature.linked_to && !$.isEmptyObject(annotator.selectedFeature.linked_to[0])) {
                    var num_linked = 0,
                        elements_linked = [];
                    for (var g in annotator.selectedFeature.linked_to[0]) {
                        num_linked++;
                        elements_linked.push(annotator.selectedFeature.linked_to[0][g]);
                    }

                    if (num_linked > 1) {
                        var allograph_label = $('.allograph_label');
                        allograph_label.html("Group (<span class='num_linked'>" + num_linked + '</span>) <i title="Show group elements" data-placement="bottom" data-container="body" data-toggle="tooltip" class="glyphicon glyphicon-list show_group" data-hidden="true" />')
                            .css('cursor', 'pointer')
                            .data('hidden', true);

                        allograph_label.unbind().click(function() {

                            var element = "<div class='elements_linked'>";

                            $.each(elements_linked, function() {
                                element += "<p data-id='" + this.id + "'>" + this.feature + "<i title='ungroup' class='pull-right glyphicon glyphicon-remove ungroup' data-id='" + this.id + "' /></p>";
                            });

                            element += '</div>';

                            if ($('.elements_linked').length) {
                                $('.elements_linked').replaceWith(element);
                            } else {
                                $('#box_features_container').prepend(element);
                            }

                            var el_link = $('.elements_linked');
                            if ($(this).data('hidden')) {
                                el_link.slideDown();
                                $(this).data('hidden', false);
                            } else {
                                el_link.slideUp(500);
                                $(this).data('hidden', true);
                            }

                            el_link.find('p').unbind().on('mouseover', function(event) {
                                var id = $(this).data('id');
                                for (var i = 0; i < annotator.vectorLayer.features.length; i++) {
                                    var f = annotator.vectorLayer.features[i];
                                    if (f.id == id) {
                                        f.style.strokeColor = 'red';
                                        f.style.strokeWidth = 6;
                                    }
                                }
                                annotator.vectorLayer.redraw();
                                restoreFullscreenPositions();
                            }).on('mouseout', function(event) {
                                var id = $(this).data('id');
                                for (var i = 0; i < annotator.vectorLayer.features.length; i++) {
                                    var f = annotator.vectorLayer.features[i];
                                    if (f.id == id) {
                                        f.style.strokeColor = 'blue';
                                        f.style.strokeWidth = 2;
                                    }
                                }
                                annotator.vectorLayer.redraw();
                                restoreFullscreenPositions();
                            }).on('click', function() {
                                var id = $(this).data('id');
                                var feature;
                                for (var i = 0; i < annotator.vectorLayer.features.length; i++) {
                                    if (annotator.vectorLayer.features[i].id == id) {
                                        feature = annotator.vectorLayer.features[i];
                                    }
                                }
                                annotator.map.zoomToExtent(feature.geometry.getBounds());
                                restoreFullscreenPositions();
                            });

                            var ungroup_elements = $('.ungroup');

                            ungroup_elements.unbind().click(function() {
                                var id = $(this).data('id');
                                $(this).parent('p').fadeOut().remove();
                                self.ungroup(id);
                                var i = 0;
                                $.each(elements_linked, function(index, value) {
                                    if (this.id == id) {
                                        elements_linked.splice(i, 1);
                                    }
                                    i++;
                                });
                                restoreFullscreenPositions();
                            });

                        });
                    }
                } else {
                    if (annotator.annotating) {
                        dialog.parent().find('.allograph_label').html($('#panelImageBox .allograph_form option:selected').text());
                    }
                }
                restoreFullscreenPositions();
            }
        },

        ungroup: function(element_id) {
            var a;

            for (var i = 0; i < annotator.selectedAnnotations.length; i++) {
                var annotation = annotator.selectedAnnotations[i];
                if (!$.isEmptyObject(annotation.linked_to[0]) && typeof annotation.linked_to[0][element_id] !== "undefined") {
                    delete annotation.linked_to[0][element_id];
                }

                if (annotation.id == element_id) {
                    var group_items = 0;

                    for (var j in annotation.linked_to[0]) {
                        group_items++;
                    }

                    if (group_items <= 1) {
                        $('.allograph_label').html(annotation.feature);
                        $('.elements_linked').remove();
                    }

                    annotation.linked_to = [];
                    a = annotation;
                }

            }

            annotator.selectFeature.unselect(a);

            for (i = 0; i < annotator.vectorLayer.features.length; i++) {
                var f = annotator.vectorLayer.features[i];

                if (f.id == element_id) {
                    f.style.strokeWidth = 2;
                }
            }

            annotator.vectorLayer.redraw();
            var element_num_linked = $('.num_linked');
            var num_linked = parseInt(element_num_linked.text(), 10) - 1;
            if (!num_linked) {
                var boxes = $('.dialog_annotations');
                boxes.remove();
            } else {
                element_num_linked.html(num_linked);
            }

            if (annotator.selectedAnnotations.length) {
                var lastAnnotation = annotator.selectedAnnotations[annotator.selectedAnnotations.length - 1];
                annotator.showAnnotation(lastAnnotation);
            }

        },

        toggleGroupButton: function() {
            var group_button = $('.link_graphs');
            if (group_button.length && annotator.selectedAnnotations.length > 1) {
                group_button.removeClass('disabled').attr('disabled', false);
            } else {
                group_button.addClass('disabled').attr('disabled', true);
            }
        }

    };


    this.filters = {

        filterAnnotation: function(checkboxes, formal_attribute, formal_attribute2) {
            var features = self.vectorLayer.features;
            var feature;
            var attribute, attribute2;
            var hand;
            var allograph;
            for (var i in features) {
                if (formal_attribute == 'hand') {
                    if (!features[i].is_editorial && features[i].stored) {
                        attribute = features[i].hand;
                        attribute2 = features[i].allograph_id;
                        hand = $('#hand_input_' + attribute);
                        allograph = $('#allograph_' + attribute2);
                        var allographs = $('.checkVectors');
                        if (!($(checkboxes).is(':checked'))) {
                            if ($(checkboxes).val() == attribute && features[i].hand == hand.val()) {
                                features[i].style.fillOpacity = 0;
                                features[i].style.strokeOpacity = 0;
                            }
                        } else {
                            var max = allographs.length;
                            for (var h = 0; h < max; h++) {
                                var a = $(allographs[h]);
                                if (a.is(':checked') && a.val().replace(/[\.;,\s]/gi, '') == attribute2) {
                                    if ($(checkboxes).val() == attribute) {
                                        features[i].style.fillOpacity = 0.4;
                                        features[i].style.strokeOpacity = 0.4;
                                    }
                                }
                            }
                        }
                    }
                } else if (formal_attribute == 'feature') {
                    if (!features[i].is_editorial) {
                        attribute = features[i].allograph_id;
                        attribute2 = features[i].hand;
                        hand = $('#hand_input_' + attribute2);
                        allograph = $('#hand_input_' + attribute2);
                        if (!($(checkboxes).is(':checked'))) {
                            if ($(checkboxes).val() == attribute && features[i].hand == hand.val()) {
                                features[i].style.fillOpacity = 0;
                                features[i].style.strokeOpacity = 0;
                            }
                        } else {
                            if ($(checkboxes).val() == attribute && features[i].hand == hand.val() && hand.is(':checked')) {
                                features[i].style.fillOpacity = 0.4;
                                features[i].style.strokeOpacity = 0.4;
                            }
                        }
                    }
                } else if (formal_attribute == 'editorial') {
                    attribute = features[i].is_editorial;
                    if (attribute) {
                        if (!($(checkboxes).is(':checked'))) {
                            features[i].style.fillOpacity = 0;
                            features[i].style.strokeOpacity = 0;
                        } else {
                            features[i].style.fillOpacity = 0.4;
                            features[i].style.strokeOpacity = 0.4;
                        }
                    }
                } else {
                    attribute = features[i].stored;
                    if (!attribute && features[i].state) {
                        if (!($(checkboxes).is(':checked'))) {
                            features[i].style.fillOpacity = 0;
                            features[i].style.strokeOpacity = 0;
                            $('polyline').add('circle').hide();
                        } else {
                            features[i].style.fillOpacity = 0.4;
                            features[i].style.strokeOpacity = 0.4;
                            $('polyline').add('circle').show();
                        }
                    }
                }
            }
            self.vectorLayer.redraw();
            restoreFullscreenPositions();
        },

        filterCheckboxes: function(checkboxes, check) {
            var features = self.vectorLayer.features;
            var show_editorial_annotations = $('#show_editorial_annotations').is(':checked');
            var allographs = $('.checkVectors');
            var hands = $('.checkVectors_hands');
            var hand, i;
            if (check == 'check') {
                $(checkboxes).attr('checked', true);
                var features_length = features.length;
                var hands_length = hands.length;
                for (i = 0; i < features_length; i++) {
                    for (var h = 0; h < hands_length; h++) {
                        hand = $(hands[h]);
                        if (features[i].hand == hand.val() && hand.is(':checked') && features[i].stored || features[i].is_editorial) {
                            if (!features[i].style) {
                                features.style = {};
                            }
                            features[i].style.fillOpacity = 0.4;
                            features[i].style.strokeOpacity = 0.4;
                        }
                    }
                }

            } else if (check == 'uncheck') {
                $(checkboxes).attr('checked', false);
                var max = features.length;
                for (i = 0; i < max; i++) {
                    if (features[i].stored || features[i].is_editorial) {
                        if (!features[i].style) {
                            features[i].style = {};
                        }
                        features[i].style.fillOpacity = 0;
                        features[i].style.strokeOpacity = 0;

                    }
                }
            }

            self.vectorLayer.redraw();
            restoreFullscreenPositions();
        }
    };


    this.dialog = {

        init: function(selectedFeature, id, callback) {
            var _self = this;
            _self.create(selectedFeature, id, function(dialog_instance) {
                _self.fill(dialog_instance, selectedFeature, function() {
                    _self.events(dialog_instance, selectedFeature);
                    if (callback) {
                        callback();
                    }
                });
            });
        },

        events: function(dialog_instance, selectedFeature) {
            var url_allograph_button = dialog_instance.parent().find('.url_allograph');

            url_allograph_button.off('click').on('click', function() {
                show_url_allograph(dialog_instance, selectedFeature, $(this));
            });
            if (!window.digipal_settings.ARCHETYPE_GOOGLE_SHORTENER_CLIENTID) {
                url_allograph_button.hide();
            }
            

            // Changes in the name/title of the public note
            var name_temporary_annotation = $('.name_temporary_annotation');
            //var content_temporary_annotation = $('.textarea_temporary_annotation');

            if (annotator.selectedFeature.contentTitle) {
                name_temporary_annotation.val(annotator.selectedFeature.contentTitle);
            }

            if (name_temporary_annotation.length) {
                name_temporary_annotation.focus();
            }

            name_temporary_annotation.on('keyup', function() {
                annotator.selectedFeature.contentTitle = $(this).val();
                remove_url_div();
            });

            init_note_field('.textarea_temporary_annotation', annotator, 'contentAnnotation');

            // Showing all the allographs of a given allograph
            dialog_instance.parent().find('.number_annotated_allographs').on('click', function() {
                open_allographs($(this), true);
            });

            if (annotator.selectedFeature && !selectedFeature) {
                selectedFeature = annotator.selectedFeature;
            }

            var to_lightbox = $('.ui-dialog').find('.to_lightbox');

            to_lightbox.unbind().on('click', function() {
                var type;
                if (!$(this).find('span').hasClass("starred")) {
                    if (!annotator.selectedFeature) {
                        annotator.selectedFeature = annotator.selectedAnnotations[annotator.selectedAnnotations.length];
                    }
                    if (annotator.selectedAnnotations.length > 1) {
                        var links = [];
                        for (var l in annotator.selectedAnnotations) {
                            if (!annotator.selectedAnnotations[l].is_editorial) {
                                links.push(parseInt(annotator.selectedAnnotations[l].graph, 10));
                            }
                        }
                        if (add_to_lightbox($(this), 'annotation', links, true)) {
                            $(this).find('span').addClass('starred').removeClass('unstarred');
                        }
                    } else {
                        var _gr = parseInt(selectedFeature.graph, 10);
                        type = 'annotation';
                        if (selectedFeature.is_editorial) {
                            _gr = selectedFeature.id;
                            type = 'editorial';
                        }
                        if (add_to_lightbox($(this), type, _gr, false)) {
                            $(this).find('span').addClass('starred').removeClass('unstarred');
                        }
                    }
                } else {
                    if ((annotator.selectedFeature.hasOwnProperty('graph') && annotator.selectedFeature.graph) || annotator.selectedFeature.is_editorial) {
                        type = 'annotation';
                        if (annotator.selectedFeature.is_editorial) {
                            type = 'editorial';
                        }
                        _Star.removeFromCollection($(this), type);
                        $(this).find('span').addClass('unstarred').removeClass('starred');
                    }
                }

            });

            var link_graphs = $('.link_graphs');
            link_graphs.on('click', function() {
                annotator.annotationsGroup.linkAnnotations(dialog_instance);
            });

            if (annotator.isAdmin == "False" || !annotator.annotating) {
                $('.name_temporary_annotation').focus();
                $('.ui-dialog-title').on('click', function() {
                    $('.name_temporary_annotation').focus();
                });
                annotator.selectedFeature.isTemporary = true;
            }

            $('.save_trigger').unbind().on('click', function() {
                annotator.saveButton.trigger();
            });

            $('.delete_trigger').unbind().on('click', function() {
                if (annotator.selectedAnnotations.length) {
                    var features = annotator.selectedAnnotations;
                    var msg = 'You are about to delete ' + features.length + ' annotations. They cannot be restored at a later time! Continue?';
                    var doDelete = confirm(msg);
                    if (doDelete) {
                        for (var i = 0; i < features.length; i++) {
                            delete_annotation(annotator.vectorLayer, features[i], features.length);
                        }
                    }
                } else {
                    if (annotator.selectedFeature) {
                        annotator.deleteAnnotation(annotator.vectorLayer, annotator.selectedFeature, 1);
                    }
                }
                $('.tooltip').add('circle').add('polyline').remove();
            });

            $('*[data-toggle="tooltip"]').tooltip({
                container: 'body',
                placement: 'bottom'
            });
        },

        /* Function to create a new dialog for each allograph clicked */

        create: function(selectedFeature, id, callback) {
            var _self = this;
            if (typeof annotator.allow_multiple_dialogs == "undefined") {
                annotator.allow_multiple_dialogs = false;
            }
            
            var can_open_box = !annotator.noInitialDialog && annotator.boxes_on_click;
            annotator.noInitialDialog = false;

            if (!annotator.allow_multiple_dialogs || !can_open_box) {
                var dialog_annotations = $('.dialog_annotations');
                dialog_annotations.parent('.ui-dialog').remove();
                dialog_annotations.remove();
            }

            var dialog = $("<div id = 'dialog" + id + "'>");

            $('#annotations').append(dialog);
            var path = $("#OpenLayers_Layer_Vector_27_svgRoot");

            if (selectedFeature && selectedFeature.hasOwnProperty('graph')) {
                var geometry_id;
                var features_length = annotator.vectorLayer.features.length;
                for (var i = 0; i < features_length; i++) {
                    var feature = annotator.vectorLayer.features[i];
                    if (feature.graph == selectedFeature.graph) {
                        geometry_id = feature.geometry.id;
                        break;
                    }
                }
                path = document.getElementById(geometry_id);
            }

            dialog.data('feature', selectedFeature);

            var position = _self.position(path);
            var absolute_position = position.absolute_position;

            if (can_open_box) {
                dialog.dialog({
                    draggable: true,
                    //height: 340,
                    //minHeight: 340,
                    height: 340,
                    //minWidth: 340,
                    resizable: false,

                    close: function(event, ui) {
                        $(this).dialog('destroy').empty().remove();
                        annotator.selectFeature.unselectAll();
                        $('.tooltip').remove();
                    },

                    title: _self.label.init(selectedFeature),

                    position: position.p

                }).addClass('dialog_annotations');

                if (absolute_position) {
                    var top_page_position = $(window).scrollTop();
                    var window_height = ($(window).height() / 100) * 25;
                    if (annotator.isMobile()) {
                        dialog.parent().css({
                            'position': 'absolute',
                            'top': top_page_position + window_height,
                            'left': '4%'
                        });
                    } else {
                        var left = '68%';
                        if (!$.isEmptyObject(selectedFeature)) {
                            var vectorPosition = $("#" + selectedFeature.geometry.id).position();
                            if (vectorPosition) {
                                if (vectorPosition.left > $('#map').width() - ($('#map').width() * 38) / 100) {
                                    left = '25%';
                                }
                            }
                        }
                        dialog.parent().css({
                            'position': 'absolute',
                            'top': top_page_position + window_height,
                            'left': left
                        });
                    }
                }
            } else {
                $('#annotations').html('');
            }
            callback(dialog);
        },

        fill: function(dialog, selectedFeature, callback) {

            var can_edit = $('#development_annotation').is(':checked');
            var s = '';
            var panel = $('#panelImageBox');
            var _self = this;
            var allograph = $('#panelImageBox .allograph_form option:selected');
            var allograph_id = allograph.val();

            s += "<div id='box_features_container'>";
            s += "<ul class='nav nav-tabs'><li class='active in'><a data-toggle='tab' data-target='#components_tab'>Components</a></li>";
            s += "<li><a data-toggle='tab' data-target='#aspects_tab'>Aspects</a></li>";
            s += "<li><a data-toggle='tab' data-target='#notes_tab'>Notes</a></li>";
            s += "</ul>";
            s += "<div class='tabbable'><div class='tab-content'>";
            s += "<div class='tab tab-pane active in fade' id='components_tab'></div>";
            s += "<div class='tab tab-pane fade' id='aspects_tab'></div>";
            s += "<div class='tab tab-pane fade' id='notes_tab'></div>";
            s += "</div></div></div>";
            dialog.html(s);
            if (annotator.boxes_on_click) {
                var notes = "";
                if (annotator.isAdmin == 'True' && annotator.annotating) {
                    if (annotator.selectedFeature.is_editorial || annotator.editorial.active && !annotator.selectedFeature.stored || annotator.selectedFeature.hasOwnProperty('contentAnnotation')) {

                        if (annotator.selectedFeature.is_editorial || annotator.editorial.active) {
                            notes += '<label>Internal Note</label>';
                            notes += '<div placeholder="Type here internal note" class="form-control" id="internal_note" name="internal_note" style="width:95%;margin-bottom:0.5em;margin-left:0.1em;"></div>';
                            notes += '<label>Public Note</label>';
                            notes += '<div placeholder="Type here display note" class="form-control" id="display_note" name="display_note" style="width:95%;margin-left:0.1em;"></div>';
                            dialog.css("margin", "1%");
                            dialog.find('#notes_tab').html(notes);
                            
                            init_note_field(dialog.find('#display_note'), annotator, 'display_note', 'Type display note here...');
                            init_note_field(dialog.find('#internal_note'), annotator, 'internal_note', 'Type internal note here...');

                            $('#panelImageBox .allograph_form').val('------');
                            $('#panelImageBox .hand_form').val('------');
                            $('select').trigger("liszt:updated");
                            annotator.editorial.activate();
                            dialog.find('#notes_tab').tab('show');
                            var targets = $('[data-target="#components_tab"]').add($('[data-target="#aspects_tab"]')).add($("[data-target='#notes_tab']"));
                            targets.hide();
                        } else if (annotator.selectedFeature.contentAnnotation) {
                            notes += "<div style='height:95%;width:100%;' class='textarea_temporary_annotation form-control' placeholder='Describe annotation ...'></div>";
                            dialog.find('#notes_tab').html(notes);
                            if (annotator.selectedFeature.hasOwnProperty('contentAnnotation')) {
                                $('.textarea_temporary_annotation').html(annotator.selectedFeature.contentAnnotation);
                            }
                            dialog.find("[data-target='#components_tab']").add(dialog.find("[data-target='#aspects_tab']")).each(function() {
                                $(this).parent('li').addClass('disabled');
                            });
                            $("[data-target='#notes_tab']").tab('show');

                            var targets = $('[data-target="#components_tab"]').add($('[data-target="#aspects_tab"]')).add($("[data-target='#notes_tab']"));
                            targets.hide();

                        }
                        dialog.find("[data-target='#components_tab']").add(dialog.find("[data-target='#aspects_tab']")).each(function() {
                            $(this).parent('li').addClass('disabled');
                        });
                        $("[data-target='#notes_tab']").tab('show');
                        return callback();
                    } else if (!$.isEmptyObject(selectedFeature) && !selectedFeature.is_editorial && annotator.editorial.active) {
                        annotator.editorial.deactivate();
                    }

                    self.updateFeatureSelect.init(dialog, selectedFeature, callback);

                    panel.find('.allograph_form').unbind('change').on('change', function() {
                        var features = annotator.vectorLayer.features;
                        var allograph = $('#panelImageBox .allograph_form option:selected').text();
                        var allograph_id = $(this).val();
                        var n = 0;
                        for (var i = 0; i < features.length; i++) {
                            if (features[i].feature == allograph && features[i].stored) {
                                n++;
                            }
                        }
                        load_data({}, dialog);
                        $(".number_annotated_allographs .number-allographs").html(n);
                        self.dialog.label.set_label(allograph);
                        panel.data('event', true);
                    });

                } else {
                    if (selectedFeature.state == 'Insert' || selectedFeature.contentAnnotation || $.isEmptyObject(selectedFeature)) {
                        notes += "<div placeholder='Describe annotation...' style='height:100%;width:100%;' class='textarea_temporary_annotation form-control' data-ph='Describe annotation ...'></div>";
                        dialog.find("[data-target='#components_tab']").add(dialog.find("[data-target='#aspects_tab']")).each(function() {
                            $(this).parent('li').addClass('disabled');
                        });
                        dialog.find('#notes_tab').html(notes);
                        $("[data-target='#notes_tab']").tab('show');
                        if (annotator.selectedFeature.hasOwnProperty('contentAnnotation')) {
                            $('.textarea_temporary_annotation').html(annotator.selectedFeature.contentAnnotation).focus();
                        }
                        var targets = $('[data-target="#components_tab"]').add($('[data-target="#aspects_tab"]')).add($("[data-target='#notes_tab']"));
                        targets.hide();
                        callback();
                    }
                }
                if (annotator.selectedFeature.hasOwnProperty('contentAnnotation') || annotator.selectedFeature.is_editorial) {
                    dialog.find("[data-target='#components_tab']").add(dialog.find("[data-target='#aspects_tab']")).each(function() {
                        $(this).parent('li').addClass('disabled');
                    });
                    $("[data-target='#notes_tab']").tab('show');
                }

            }
            self.updateFeatureSelect.init(dialog, selectedFeature, callback);

            refresh_letters_container_init(selectedFeature, selectedFeature.feature, selectedFeature.allograph_id, true);
        },

        label: {
            dialog_label_element: '.allograph_label',
            init: function(selectedFeature) {
                var _self = this;
                var html_string_label;
                var html_string_buttons;
                if (selectedFeature.feature && selectedFeature.feature.length > 8) {
                    html_string_buttons = "<div class='buttons_div'>";
                } else {
                    html_string_buttons = "<div class='pull-right buttons_div'>";
                }

                if (annotator.editorial.active || selectedFeature.is_editorial) {
                    html_string_label = "<span class='allograph_label'>Editorial Ann.</span>";
                    if (annotator.isAdmin == "True") {
                        html_string_buttons += " <button class='btn btn-xs btn-success save_trigger'><span data-toggle='tooltip' data-container='body' title='Save Annotation' class='glyphicon glyphicon-ok'></span></button> <button class='btn btn-xs btn-danger delete_trigger'><span class='glyphicon glyphicon-remove' data-toggle='tooltip' data-container='body' title = 'Delete Annotation'></span></button>";
                    }
                    html_string_buttons += " <button title='Share URL' data-toggle='tooltip' data-container='body' data-hidden='true' class='url_allograph btn-default btn btn-xs'><i class='fa fa-link' ></i></button>";
                } else {
                    if (annotator.isAdmin == "True") {
                        if (selectedFeature && annotator.annotating) {
                            html_string_label = "<span class='allograph_label'>" + selectedFeature.feature + '</span>';
                            if (selectedFeature.feature && selectedFeature.feature.length > 8) {
                                html_string_buttons += "<br>";
                            }
                            html_string_buttons += " <button class='btn btn-xs btn-success save_trigger'><span class='glyphicon glyphicon-ok' data-toggle='tooltip' data-container='body' title='Save Annotation'></span></button>";

                            html_string_buttons += " <button class='btn btn-xs btn-danger delete_trigger'><span class='glyphicon glyphicon-remove' data-toggle='tooltip' data-container='body' title = 'Delete Annotation'></span></button> <button title='Share URL' data-toggle='tooltip' data-container='body' data-hidden='true' class='url_allograph btn-default btn btn-xs'><i class='fa fa-link' ></i></button> <button data-toggle='tooltip' data-placement='bottom' data-container='body' type='button' title='Check by default' class='btn btn-xs btn-default set_all_by_default'><i class='fa fa-plus-square'></i></button>";

                        } else if (!annotator.annotating) {
                            if (!selectedFeature.hasOwnProperty('graph')) {
                                html_string_label = "<span class='allograph_label pull-left'><input type='text' placeholder = 'Type name' class='name_temporary_annotation' /></span>";
                            } else {
                                html_string_label = "<span class='allograph_label'>" + selectedFeature.feature + "</span>";
                            }
                            html_string_buttons += "<span class='pull-right' style='position: relative;right: 5%;'><button data-toggle='tooltip' data-container='body' title='Share URL' data-hidden='true' class='url_allograph btn btn-xs btn-default'><i class='fa fa-link'></i></button> ";
                        } else {

                            if (annotator.selectedFeature) {
                                html_string_label = "<span class='allograph_label'>" + annotator.selectedFeature.feature + "</span> <button data-hidden='true' class='url_allograph btn btn-default btn-xs' data-toggle='tooltip' data-container='body' title='Share URL'><i class='fa fa-link'></i></button> ";
                            } else {
                                html_string_label = "<span class='allograph_label'>Annotation</span>";
                                html_string_buttons += " <button data-hidden='true' class='url_allograph btn btn-default btn-xs' data-toggle='tooltip' data-container='body' title='Share URL'><i class='fa fa-link'></i></button> ";
                            }
                        }
                    } else {
                        if (selectedFeature && selectedFeature.hasOwnProperty('graph')) {
                            html_string_label = "<span class='allograph_label'>" + selectedFeature.feature + "</span>";
                            html_string_buttons += "<span class='pull-right' style='position: relative;right: 5%;'><button data-toggle='tooltip' title='Share URL' data-hidden='true' class='url_allograph btn btn-default btn-xs'><i class='fa fa-link'></i></button>";
                        } else {
                            html_string_label = "<span class='allograph_label'><input type='text' placeholder = 'Type name' class='name_temporary_annotation' /></span>";
                            html_string_buttons += "<span class='pull-right' style='position: relative;right: 5%;'><button data-hidden='true' class='url_allograph btn btn-default btn-xs' data-toggle='tooltip' title='Share URL'><i class='fa fa-link'></i></button>";
                        }
                    }
                }
                var buttons = _self.set_dialog_buttons(html_string_buttons);
                var label = html_string_label + ' ' + buttons;
                return label;
            },


            get_dialog_label: function() {
                return $(this.dialog_label_element);
            },

            set_label: function(label) {
                $(this.dialog_label_element).html(label);
                $(this.dialog_label_element).parent().find('br').remove();
                if (label.length > 8) {
                    $('.allograph_label').after('<br>');
                    $('.buttons_div').removeClass("pull-right");
                } else {
                    $('.buttons_div').addClass("pull-right");
                }
            },

            set_dialog_buttons: function(html_string) { // selectedFeature.graph
                var _self = this;
                var current_collection = _Star.getCurrentCollection();

                if (((annotator.selectedFeature.hasOwnProperty('graph') && annotator.selectedFeature.graph) || annotator.selectedFeature.is_editorial)) {
                    var graph = annotator.selectedFeature.graph;
                    if (annotator.selectedFeature.is_editorial) {
                        graph = annotator.selectedFeature.graph;
                    }
                    var button = $("<button class='to_lightbox btn btn-default btn-xs' data-graph = '" + graph + "'  data-type='annotation'>");
                    var span = $("<span data-toggle='tooltip' data-container='body' title='Add to Collection' class='glyphicon glyphicon-star'>");
                    if (_Star.isInCollection(current_collection, graph, 'annotation')) {
                        span.addClass("starred").attr('data-original-title', 'Remove graph from collection');
                    } else {
                        span.addClass("unstarred").attr('data-original-title', 'Add graph to collection');
                    }
                    button.append(span);
                    html_string += ' ' + button.get(0).outerHTML;
                }

                if (annotator.isAdmin == 'True') {
                    if (allow_multiple() && annotator.selectedAnnotations.length > 1) {
                        html_string += " <button data-toggle='tooltip' data-container='body' title = 'Group Annotations' class='btn btn-default btn-xs link_graphs'><i class='fa fa-users'></i></button>";
                    } else {
                        html_string += " <button class='btn btn-default btn-xs link_graphs disabled' disabled><i class='fa fa-users'></i></button>";
                    }
                }
                html_string += "</div>";
                return html_string;
            },

        },

        position: function(path) {
            var p;
            var multiple = annotator.allow_multiple_dialogs;
            var absolute_position = false;
            if (multiple) {
                p = {
                    my: 'right top',
                    at: 'right bottom',
                    of: $(path)
                };
            } else {
                absolute_position = true;
                p = ['60%', '30%'];
            }
            return {
                'p': p,
                'absolute_position': absolute_position
            };
        },

        destroy: function(dialog) {
            dialog.remove();
        },

        destroyAll: function() {
            $('.dialog_annotations').parent().remove();
        }
    };

    this.utils = {

        Base64: {
            // private property
            _keyStr: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",

            // public method for encoding
            encode: function(input) {
                var output = "";
                var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
                var i = 0;
                var Base64 = annotator.utils.Base64;
                input = Base64._utf8_encode(input);

                while (i < input.length) {

                    chr1 = input.charCodeAt(i++);
                    chr2 = input.charCodeAt(i++);
                    chr3 = input.charCodeAt(i++);

                    enc1 = chr1 >> 2;
                    enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
                    enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
                    enc4 = chr3 & 63;

                    if (isNaN(chr2)) {
                        enc3 = enc4 = 64;
                    } else if (isNaN(chr3)) {
                        enc4 = 64;
                    }

                    output = output +
                        Base64._keyStr.charAt(enc1) + Base64._keyStr.charAt(enc2) +
                        Base64._keyStr.charAt(enc3) + Base64._keyStr.charAt(enc4);

                }

                return output;
            },

            // public method for decoding
            decode: function(input) {
                var output = "";
                var chr1, chr2, chr3;
                var enc1, enc2, enc3, enc4;
                var i = 0;
                var Base64 = annotator.utils.Base64;
                input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

                while (i < input.length) {

                    enc1 = Base64._keyStr.indexOf(input.charAt(i++));
                    enc2 = Base64._keyStr.indexOf(input.charAt(i++));
                    enc3 = Base64._keyStr.indexOf(input.charAt(i++));
                    enc4 = Base64._keyStr.indexOf(input.charAt(i++));

                    chr1 = (enc1 << 2) | (enc2 >> 4);
                    chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
                    chr3 = ((enc3 & 3) << 6) | enc4;

                    output = output + String.fromCharCode(chr1);

                    if (enc3 != 64) {
                        output = output + String.fromCharCode(chr2);
                    }
                    if (enc4 != 64) {
                        output = output + String.fromCharCode(chr3);
                    }

                }

                output = Base64._utf8_decode(output);

                return output;

            },

            // private method for UTF-8 encoding
            _utf8_encode: function(string) {
                string = string.replace(/\r\n/g, "\n");
                var utftext = "";

                for (var n = 0; n < string.length; n++) {

                    var c = string.charCodeAt(n);

                    if (c < 128) {
                        utftext += String.fromCharCode(c);
                    } else if ((c > 127) && (c < 2048)) {
                        utftext += String.fromCharCode((c >> 6) | 192);
                        utftext += String.fromCharCode((c & 63) | 128);
                    } else {
                        utftext += String.fromCharCode((c >> 12) | 224);
                        utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                        utftext += String.fromCharCode((c & 63) | 128);
                    }

                }

                return utftext;
            },

            // private method for UTF-8 decoding
            _utf8_decode: function(utftext) {
                var string = "";
                var i = 0;
                var c = c1 = c2 = 0;

                while (i < utftext.length) {

                    c = utftext.charCodeAt(i);

                    if (c < 128) {
                        string += String.fromCharCode(c);
                        i++;
                    } else if ((c > 191) && (c < 224)) {
                        c2 = utftext.charCodeAt(i + 1);
                        string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                        i += 2;
                    } else {
                        c2 = utftext.charCodeAt(i + 1);
                        c3 = utftext.charCodeAt(i + 2);
                        string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                        i += 3;
                    }

                }
                return string;
            }
        },

        getParameter: function(paramName) {
            var searchString = window.location.search.substring(1),
                i, val, params = searchString.split("&");
            var parameters = [];
            for (i = 0; i < params.length; i++) {
                val = params[i].split(/={1}/);
                if (val[0] == paramName) {
                    parameters.push(unescape(val[1]));
                }
            }
            if (!parameters.length) {
                return false;
            }
            return parameters;
        },

        getCookie: function(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        /**
         * Turns on keyboard shortcuts for the controls.
         */

        toggleAll: function(activeControls, active) {
            for (i = 0; i < activeControls.length; i++) {
                if (activeControls[i].title && activeControls[i].displayClass != 'olControlFullScreenFeature' && activeControls[i].displayClass != "olControlEditorialFeature") {
                    if (active) {
                        activeControls[i].activate();
                    } else {
                        activeControls[i].deactivate();
                    }
                }
            }
        },

        removeDuplicate: function(element, attribute, text) {
            var seen = {};
            var txt;
            $(element).each(function() {
                if (text) {
                    txt = $(this).text();
                    attribute = null;
                } else {
                    txt = $(this).attr(attribute);
                }
                if (seen[txt])
                    $(this).remove();
                else
                    seen[txt] = true;
            });
        }
    };
    
    // See MOA-205
    // This is true when the user passes &dlg=0 in the URL
    // it means that the desc. dialog should not open the first time a box is selected
    // This should always be used in conjunction with &graph=X
    this.noInitialDialog = (window.dputils.get_query_string_param('dlg') === '0');

    /**

     * Updates the feature select according to the currently selected allograph.

     */

    this.updateFeatureSelect = {

        init: function(dialog, selectedFeature, callback) {
            var _self = this;
            _self.update(dialog, selectedFeature, function(dialog_instance) {
                _self.events(dialog_instance);
                if (callback) {
                    callback();
                }
            });

        },

        events: function(dialog_instance) {
            if (annotator.selectedFeature && annotator.selectedFeature.state == 'Insert') {
                $('.features_box').on('change', function() {
                    var checkbox = $(this);
                    var val = checkbox.val();
                    if (checkbox.is(':checked')) {
                        if (annotator.selectedFeature.features.indexOf(val) !== 0) {
                            annotator.selectedFeature.features.push(val);
                        }
                    } else {
                        if (annotator.selectedFeature.features.indexOf(val) !== 0) {
                            annotator.selectedFeature.features.splice(annotator.selectedFeature.features.indexOf(val), 1);
                        }
                    }
                });
            }

        },

        update: function(dialog, selectedFeature, callback) {
            if (!selectedFeature.is_editorial) {
                load_data(selectedFeature, dialog, function() {
                    var select_allograph = get_forms().allograph_form;
                    var select_hand = get_forms().hand_form;
                    var cache = annotator.cacheAnnotations;
                    var allograph, hand;
                    var selectedFeature = annotator.selectedFeature;
                    if (selectedFeature && selectedFeature.stored) {
                        var graph = selectedFeature.graph;
                        if (cache.search('graph', graph)) {
                            allograph = cache.cache.graphs[graph].allograph_id;
                            hand = cache.cache.graphs[graph].hand_id;
                        } else {
                            allograph = selectedFeature.allograph_id;
                            hand = selectedFeature.hand;
                        }
                        select_allograph.val(allograph);

                        select_hand.val(hand);
                        select_allograph.add(select_hand).trigger('liszt:updated');
                    }
                    callback(dialog);
                });
            } else {
                var data = {};
                data['display_note'] = selectedFeature.display_note;
                refresh_features_dialog(selectedFeature, dialog);
                if (callback) {
                    return callback();
                }
            }
        }
    };

    this.load_allographs_container = {

        init: function(allograph_value, url, show, allograph_id) {
            var _self = this;
            _self.load(url, allograph_value, show, function(s) {
                _self.events(s);
            });
        },

        load: function(url, allograph_value, show, callback) {
            var features = $.getJSON(url);

            if (show === undefined) {
                show = true;
            }

            if (show) {
                var div = $("<div class='letters-allograph-container'>");
                div.draggable({
                    handle: '#top_div_annotated_allographs',
                    cursor: "move"
                }).css({
                    position: "fixed",
                    top: "20%",
                    left: "33%"
                });

                var top_div = $("<div id='top_div_annotated_allographs'>");
                var number_allographs = $('.number-allographs');
                top_div.append("<span>" + allograph_value + "</span> <i title='Close box' class='icon pull-right glyphicon glyphicon-remove close_top_div_annotated_allographs'></i>");
                div.append(top_div);
                var container_div = $("<div id='container-letters-popup'>");
                var img = $("<img class='img-loading' src='/static/digipal/images/ajax-loader3.gif'>");
                $('#top_div_annotated_allographs').find('span').after(img);
                div.append(container_div);
                $('#annotator').append(div);
                features.done(function(data) {
                    number_allographs.html(data.length);
                    var s = '';

                    if (data != "False") {
                        data = data.sort(function(x, y) {
                            if (x.hand < y.hand)
                                return -1;
                            if (x.hand > y.hand)
                                return 1;
                            return 0;
                        });
                        var j = 0;
                        var data_hand;
                        if (data.length === 1) {
                            j = 1;
                            s += "<label class='hands_labels' data-hand = '" + data[0].hand + "' id='hand_" + data[0].hand + "'>Hand: " + data[0].hand_name + "</label>\n";
                            data_hand = data[0].hand;
                            s += "<span data-hand = '" + data_hand + "' class='vector_image_link' data-graph='" + data[0].graph + "' title='Hover over a graph to highlight it on the image; click on a graph to move to it'>" + data[0].image + '</span>\n';
                        } else {
                            for (var i = 0; i < data.length; i++) {
                                j++;
                                if (i === 0) {
                                    s += "<label class='hands_labels' data-hand = '" + data[i].hand + "' id='hand_" + data[i].hand + "'>Hand: " + data[i].hand_name + "</label>\n";
                                    data_hand = data[i].hand;
                                }
                                if (typeof data[i - 1] != "undefined" && typeof data[i + 1] != "undefined" && data[i].hand != data[i - 1].hand) {
                                    j = 1;
                                    data_hand = data[i].hand;
                                    s += "<label class='hands_labels' data-hand = '" + data[i].hand + "'  id='hand_" + data_hand + "'>Hand: " + data[i + 1].hand_name + "</label>\n";
                                }
                                if (typeof data[i + 1] == "undefined" && data[i].hand != data[i - 1].hand) {
                                    j = 1;
                                    data_hand = data[i].hand;
                                    s += "<label class='hands_labels' data-hand = '" + data[i].hand + "'  id='hand_" + data_hand + "'>Hand: " + data[i].hand_name + "</label>\n";
                                }
                                s += "<span data-hand = '" + data_hand + "' class='vector_image_link' data-graph='" + data[i].graph + "' title='Hover over a graph to highlight it on the image; click on a graph to move to it'>" + data[i].image + '</span>\n';
                            }
                        }
                    } else {
                        s = "<p><label>No Annotations</label></p>";
                        container_div.html(s);
                    }
                    if (callback) {
                        callback(s);
                    }
                });
            }
        },

        events: function(s) {
            var button = $('.close_top_div_annotated_allographs');
            var container = $('.letters-allograph-container');
            var container_div = container.find('#container-letters-popup');
            var container_number = $('.number_annotated_allographs');
            var annotations_layer = $('#OpenLayers_Layer_Vector_27_svgRoot');
            var features = annotator.vectorLayer.features;
            var img = $(".img-loading");
            var images = $(s).find('img');

            container_div.html(s);

            button.on('click', function() {
                container.fadeOut().remove();
                container_number.removeClass('active');
            });

            var hands = $('.hands_labels');
            var images_link = $('.vector_image_link');
            $.each(hands, function(index_hands, hand) {
                var c = 0;
                $.each(images_link, function(index_images, image) {
                    if ($(image).data('hand') == $(hand).data('hand')) {
                        c++;
                    }
                });
                $(hand).append(" <span class='num_all_hands badge'>" + c + "</span>");
            });

            images_link.on('click', function() {
                var vector = $(this);
                annotator.centreById(vector.data('graph'));
            }).on("mouseover", function() {
                var vector = $(this);
                for (var i = 0; i < features.length; i++) {
                    if (features[i].graph == vector.data('graph')) {
                        features[i].originalColor = features[i].style.fillColor;
                        features[i].style.strokeColor = 'red';
                        features[i].style.strokeWidth = 6;
                        break;
                    }
                }
                annotator.vectorLayer.redraw();
                restoreFullscreenPositions();
            }).on('mouseout', function() {
                var vector = $(this);
                for (var i = 0; i < features.length; i++) {
                    if (features[i].graph == vector.data('graph')) {
                        features[i].style.strokeColor = features[i].originalColor;
                        features[i].style.strokeWidth = 2;
                        break;
                    }
                }
                annotator.vectorLayer.redraw();
                restoreFullscreenPositions();
            }).on('dblclick', function() {
                var vector = $(this);
                annotator.selectFeatureByIdAndCentre(vector.data('graph'));
            }).fadeIn();

            images_link.fadeIn();
            if (img.length) {
                img.remove();
            };
            
            document.load_lazy_images();
        }
    };

    this.toolbar = {

        toggle_tools: function(toolnames, enable) {
            var classes = '';
            for (i in toolnames) {
                if (toolnames[i].substring(0,1) === '.') {
                    classes += ',' + toolnames[i];
                } else {
                    classes += ',.olControl'+toolnames[i]+'Feature';
                    classes += ',.olControl'+toolnames[i]+'Features';
                    classes += ',.olControl'+toolnames[i]+'FeatureItemActive';
                    classes += ',.olControl'+toolnames[i]+'FeatureItemInactive';
                    classes += ',.olControl'+toolnames[i]+'FeaturesItemActive';
                    classes += ',.olControl'+toolnames[i]+'FeaturesItemInactive';
                }
            }
            if (classes) {
                classes = classes.substring(1);
                if (enable) {
                    $(classes).fadeIn();
                } else {
                    $(classes).fadeOut();
                }
            }
        },

        toggle_annotation_tools: function(enable) {
            this.toggle_tools(['Editorial', 'Save', 'Delete', 'Transform'], enable);
        },
    };

    this.select_default_hand_and_allograph = function() {
        // GN: if no hand and allograph is selected
        // and only one hand is available, we select that hand.
        // This is more efficient for editors.
        // See MOA-195
        var controls = get_forms();
        if (controls) {
            // the hand-select control
            var select = controls.hand_form;
            // any hand selected?
            if (!(select.val())) {
                var new_value = '';
                
                select.find('option').each(function(i, option) {
                    if (option.value) {
                        if (new_value) {
                            // more than one hand, we don't pick any
                            // it could be misleading for editors
                            new_value = '';
                            return false;
                        }
                        new_value = option.value;
                    }
                });
                if (new_value) {
                    select.val(new_value);
                    select.trigger("liszt:updated");
                }
            }
        }
    };

    /**
     * Saves an annotation for the currently selected feature.
     */
    this.saveAnnotation = function(ann, allographs_page) {

        var isModifyToolActive = annotator.transformFeature.active;
        annotator.transformFeature.deactivate();

        if (!ann) {
            ann = null;
        }

        if (typeof allographs_page == 'undefined') {
            allographs_page = false;
        }
        if (!annotator.selectedFeature && !annotator.selectedAnnotations.length) {
            updateStatus('Select annotations to proceed', 'danger');
            return false;
        }

        var forms = get_forms();

        var select_allograph = forms.panel;

        var allograph_form = forms.allograph_form;
        var hand_form = forms.hand_form;

        if (!annotator.editorial.active && (!allograph_form.val() || !hand_form.val())) {
            updateStatus('Hand and Allograph are required', 'danger');
            return false;
        }

        if (this.selectedAnnotations.length) {
            this.selectedAnnotations.reverse();
        }

        updateStatus('Saving Annotation...', 'warning');

        var image_id = annotator.image_id;
        var graphs = [],
            vector = {},
            geoJson;
        var feature;
        var data = make_form();
        data['isModifyToolActive'] = isModifyToolActive;
        var url = annotator.absolute_image_url + 'save';
        var cache = this.cacheAnnotations.cache;
        if (!annotator.editorial.active) {
            if (allow_multiple() && this.selectedAnnotations.length > 1 && !allographs_page) {

                var msg = 'You are about to save ' + this.selectedAnnotations.length + ' annotations. Do you want to continue?';

                if (confirm(msg)) {
                    for (var i = 0; i < this.selectedAnnotations.length; i++) {

                        feature = this.selectedAnnotations[i];
                        geoJson = annotator.format.write(feature);

                        vector = {};
                        vector['id'] = feature.graph;
                        vector['image'] = image_id;
                        vector['geoJson'] = geoJson;
                        if (!feature.stored) {
                            vector['vector_id'] = feature.id;
                        }
                        graphs.push(vector);
                    }

                    url = '/digipal/api/graph/save/' + JSON.stringify(graphs) + '/';
                    save(url, graphs, data, ann, data.features);

                }

            } else {

                if (allographs_page) {

                    for (ind2 = 0; ind2 < ann.length; ind2++) {
                        geoJson = annotator.format.write(ann[ind2]);
                        graphs.push({
                            'id': ann[ind2].graph,
                            'image': image_id,
                            // GN: commented out to avoid clashes with the annotation editor
                            // modifying the shape. See JIRA DIGIPAL-479 and DIGIPAL-477
                            //'geoJson': geoJson,
                            //'vector_id': ann[ind2].id
                        });
                    }

                    url = '/digipal/api/graph/save/' + JSON.stringify(graphs) + '/';
                    save(url, graphs, data, ann, data.features);

                } else {
                    if (this.selectedFeature) {
                        feature = this.selectedFeature;
                        geoJson = annotator.format.write(feature);

                        vector = {};
                        vector['id'] = feature.graph;
                        vector['image'] = image_id;
                        vector['geoJson'] = geoJson;

                        if (!feature.stored) {
                            vector['vector_id'] = feature.id;
                        }

                        graphs.push(vector);
                        url = '/digipal/api/graph/save/' + JSON.stringify(graphs) + '/';
                        save(url, graphs, data, ann, data.features);

                    }

                }
            }
        } else {
            if (!allow_multiple() || !this.selectedAnnotations.length) {
                this.selectedAnnotations.push(annotator.selectedFeature);
            }
            for (var i = 0; i < this.selectedAnnotations.length; i++) {
                feature = this.selectedAnnotations[i];

                geoJson = annotator.format.write(feature);
                vector = {};
                vector['image'] = image_id;
                vector['geoJson'] = geoJson;
                if (feature.hasOwnProperty('id') && !feature.stored) {
                    vector['vector_id'] = feature.id;
                }
                vector['id'] = feature.id;
                graphs.push(vector);

            }
            url = '/digipal/api/graph/save_editorial/' + JSON.stringify(graphs) + '/';
            save(url, graphs, data, ann, data.features);
        }

    };


    /**
     * Deletes the annotation for the selected feature.
     *
     * @param layer
     *              The feature's layer.
     * @param feature
     *              The feature to delete the annotation for.
     */
    this.deleteAnnotation = function(layer, feature, number_annotations) {
        var _self = this;
        var msg;
        if (typeof number_annotations == 'undefined' || !number_annotations) {
            msg = 'You are about to delete this annotation. It cannot be restored at a later time! Continue?';
        } else {
            var plural = number_annotations > 1;
            if (!plural) {
                msg = 'You are about to delete ' + number_annotations + ' annotation. It cannot be restored at a later time! Continue?';
            } else {
                msg = 'You are about to delete ' + number_annotations + ' annotations. They cannot be restored at a later time! Continue?';
            }
        }

        var doDelete = confirm(msg);
        if (doDelete) {
            if (feature !== null && feature !== undefined) {
                delete_annotation(layer, feature, number_annotations);
            }
        }

        updateTabCounter();

    };


    /* Function to refresh the layer when saved an annotation */
    this.refresh_layer = function() {
        var _activeControls = annotator.map.getControlsBy('active', true);
        for (var j = 0; j < annotator.map.controls.length; j++) {
            annotator.map.controls[j].deactivate();
        }
        annotator.vectorLayer.destroyFeatures();
        annotator.vectorLayer.addFeatures([]);
        annotator.annotations = [];
        annotator.selectedFeature = null;
        annotator.selectedAnnotations = [];
        annotator.cacheAnnotations.clear();
        $('.dialog_annotations').parent().remove();
        // GN: commented this out because load_annotations() below will load the
        // annotation anyway.
        //         var request = $.getJSON(annotator.absolute_image_url + 'annotations/', function(data) {
        //             annotator.annotations = data;
        //         });
        var div = $('<div>');
        div.attr('class', 'loading-div');
        div.html('<p>Reloading annotations. Please wait...</p><img src="/static/digipal/images/ajax-loader3.gif" />');
        $('#annotator').append(div.fadeIn());
        $('.number_unsaved_allographs').html(0);
        this.unsaved_annotations = [];
        $('.checkVectors').add('.checkVectors_hands').prop('checked', true);
        this.load_annotations(function(data) {
            reload_described_annotations(div);
            restoreFullscreenPositions();

            var selectFeature = 0;
            for (j = 0; j < _activeControls.length; j++) {

                if (_activeControls[j].displayClass != "olControlNavigation") {
                    _activeControls[j].activate();
                }

                if (_activeControls[j].id == "OpenLayers_Control_SelectFeature_78") {
                    selectFeature++;
                }
            }

            if (!selectFeature) {
                annotator.selectFeature.deactivate();
            }

            $('circle').remove();
            $('polyline').remove();

        }, true);

    };


    /* FullScreen Mode */

    this.full_Screen = function() {
        var map = $('#map');
        var panel = $('#panelImageBox');
        var toolbar = $('#toolbar');
        var map_size;
        var input_toolbar_position = $("input[name='toolbar_position']:checked");
        if (!(this.fullScreen.active)) {
            $('body').addClass('annotator-fullscreen')
            $('html, body').animate({
                scrollTop: map.position().top
            }, 0);

            this.fullScreen.activate();
            map.addClass("fullScreenMap");

            $(document).keyup(function(e) {
                if (e.keyCode == 27) {
                    $('body').removeClass('annotator-fullscreen')
                    map.removeClass('fullScreenMap');
                    panel.removeClass('fullScreenPanel');
                    toolbar.removeClass('mapHorizontalFullscreen');
                    toolbar.removeClass('fullScreenToolbarVertical');
                    annotator.fullScreen.deactivate();
                }
            });

            $('.olControlFullScreenFeatureItemInactive').attr('title', 'Deactivate Full Screen');
            panel.addClass('fullScreenPanel');

            if (input_toolbar_position.val() != 'Vertical') {
                toolbar.addClass('mapHorizontalFullscreen');
                toolbar.removeClass('fullScreenToolbarVertical');
            } else {
                toolbar.removeClass('mapHorizontalFullscreen');
                toolbar.addClass('fullScreenToolbarVertical');
            }
        } else {
            this.fullScreen.deactivate();
            $('body').removeClass('annotator-fullscreen')
            map.removeClass('fullScreenMap');

            $('.olControlFullScreenFeatureItemInactive').attr('title', 'Activate Full Screen');
            panel.removeClass('fullScreenPanel');
            toolbar.removeClass('mapHorizontalFullscreen');
            toolbar.removeClass('fullScreenToolbarVertical');

            $('html, body').animate({
                scrollTop: map.position().top
            }, 0);

            if (input_toolbar_position.val() == 'Vertical') {
                loader.toolbar_position();
            }
        }
        restoreFullscreenPositions();
    };
}



function notifySelectedAnnotations() {
    var msg;
    if (annotator.selectedAnnotations.length > 1 || !annotator.selectedAnnotations.length) {
        msg = annotator.selectedAnnotations.length + ' annotations selected';
    } else {
        msg = annotator.selectedAnnotations.length + ' annotation selected';
    }
    updateStatus(msg, 'success');
}

// --------------------------------------------------------------------------
// --------------------------------------------------------------------------
// --------------------------------------------------------------------------
// --------------------------------------------------------------------------

function select_feature(feature) {
    annotator.showAnnotation(feature);
    annotator.annotationsGroup.toggleGroupButton();
}

// TODO: simplify by havinh a pale fill color, same color bu darker for stroke
// Same opacity for all styles.
var FEATURE_STYLES = {
    'selected': {
        'fill': 'blue',
        'stroke': 'blue',
        'opacity': 0.4,
    },
    'described': {
        'fill': '#90ff90',
        'stroke': 'green',
        'opacity': 0.4,
    },
    'undescribed': {
        // yellow
        'fill': '#ee9900',
        'stroke': '#994400',
        'opacity': 0.4,
    },
    'unsaved': {
        // red/pink
        'fill': '#fe2deb',
        'stroke': '#fe2deb',
        'opacity': 0.4,
    },
    'editorial': {
        'fill': '#222',
        'stroke': '#222',
        'opacity': 0.4,
    },
    'wrong_name': {
        'fill': '#202020',
        'stroke': '#B00000',
        'opacity': 0.4,
    },
}

function stylize_predefined(feature, style_name) {
    let style = FEATURE_STYLES[style_name];
    if (!style) {
        console.log('Style name not found: "'+style_name+'"');
        style = FEATURE_STYLES.wrong_name;
    }
    stylize(feature, style.fill, style.stroke, style.opacity);
}

/* Applies style to a vector */
var stylize = function(feature, fill, stroke, opacity) {
    if (!feature.hasOwnProperty('style')) {
        feature.style = {};
    }
    feature.style = {
        'strokeColor': stroke,
        'strokeOpacity': Math.max(opacity + 0.3, 1.0),
        'fillColor': fill,
        "fillOpacity": opacity
    };
};


/* Checks whether it is possible to select multiple annotations or not */

function allow_multiple() {
    var multiple_checkbox = $("#multiple_annotations");
    return multiple_checkbox.is(':checked') || annotator.selectFeature.multiple;
}


function createPopup(feature) {
    var map = annotator.map;
    feature.popup = new OpenLayers.Popup("pop",
        feature.geometry.getBounds().getCenterLonLat(),
        null,
        '<div class="markerContent">' + feature.display_note + '</div>',
        true);

    feature.popup.backgroundColor = 'transparent';
    feature.popup.closeDiv = false;
    feature.popup.autoSize = true;
    feature.popup.maxSize = new OpenLayers.Size(600, 200);
    feature.popup.keepInMap = true;
    //feature.popup.closeOnMove = true;
    map.addPopup(feature.popup);
}

function deletePopup(feature) {
    feature.popup.destroy();
    feature.popup = null;
}

/*

Feature to discover the already described allographs and
render the layer according to each allograph

*/

function reload_described_annotations(div) {
    var show_editorial_annotations = $('#show_editorial_annotations').is(':checked');

    var feature = annotator.vectorLayer.features;
    var selectedFeature;
    if (typeof annotator.selectedFeature !== "undefined" && typeof annotator.selectedFeature != "null") {
        selectedFeature = annotator.selectedFeature;
    }
    var h = 0;
    var path;

    while (h < feature.length) {
        var num_features = feature[h].num_features;

        if (feature[h].is_editorial && !show_editorial_annotations) {
            stylize(feature[h], '#222', '#222', 0);
        } else if (feature[h].is_editorial && show_editorial_annotations) {
            stylize(feature[h], '#222', '#222', 0.4);
        } else {
            if (num_features) {
                stylize_predefined(feature[h], 'described')
                feature[h].described = true;

                if (typeof selectedFeature != "undefined" && typeof selectedFeature != "null" && selectedFeature && feature[h].graph == selectedFeature.graph) {
                    //stylize(feature[h], 'blue', 'blue', 0.4);
                    feature[h].described = true;
                    annotator.selectFeatureById(feature[h].id);
                }

            } else {
                stylize_predefined(feature[h], 'undescribed');
                feature[h].described = false;

                if (typeof selectedFeature != "undefined" && typeof selectedFeature != "null" && selectedFeature) {
                    if (feature[h].graph == selectedFeature.graph) {
                        //stylize(feature[h], 'blue', 'blue', 0.4);
                        feature[h].described = false;
                        annotator.selectFeatureById(feature[h].id);
                    }
                }
            }
        }
        h++;
    }

    annotator.vectorLayer.redraw();
    if (typeof div != "undefined") {
        div.fadeOut().remove();
    }

}

function open_allographs(allograph, show) {
    current_allograph = allograph;
    var container = $('.letters-allograph-container');
    if (container.length) {
        container.remove();
    }
    $(this).addClass('active');
    var allograph_value, allograph_id;

    if (typeof allograph != "undefined") {
        allograph_value = allograph.parent().prev().text();
    } else {
        allograph_value = $('#panelImageBox .allograph_form option:selected').text();
        allograph_id = $('#panelImageBox .allograph_form').val();
    }

    if (allograph_value) {
        var features = annotator.vectorLayer.features;
        var feature;
        for (var i = 0; i < features.length; i++) {
            if (features[i].feature == allograph_value) {
                feature = features[i].graph;
                break;
            }
        }
        if (!feature) {
            return false;
        }
        var url = annotator.absolute_image_url + "graph/" + feature + "/allographs_by_graph/";
        annotator.load_allographs_container.init(allograph_value, url, show, allograph_id);
    }
}


function detect_common_features_init() {
    var checkboxes = $('.dialog_annotations').find('.features_box');
    var graphs = [];

    for (var g = 0; g < annotator.selectedAnnotations.length; g++) {
        if (annotator.selectedAnnotations[g].hasOwnProperty('graph') && annotator.selectedAnnotations[g].graph) {
            graphs.push(annotator.selectedAnnotations[g].graph);
        }
    }

    if (graphs.length > 1) {
        var cache = $.extend(true, {}, annotator.cacheAnnotations.cache);
        detect_common_features(graphs, checkboxes, cache);
    }
}

function refresh_letters_container_init(annotation, allograph, allograph_id, show) {
    if ($('.letters-allograph-container').length && annotation && $('.tab-pane.active').attr('id') == 'annotator') {
        refresh_letters_container(allograph, allograph_id, true);
    }
}

function refresh_letters_container(allograph, allograph_id, show) {
    current_allograph = allograph;
    var features = annotator.vectorLayer.features;
    var character_id;
    for (var i = 0; i < features.length; i++) {
        if (features[i].feature == allograph) {
            character_id = features[i].character_id;
        }
    }
    var container = $('.letters-allograph-container');
    if (container.length) {
        container.remove();
        show = true;
    } else {
        show = false;
    }
    var url = annotator.absolute_image_url + "allographs/" + allograph_id + "/" + character_id + "/allographs_by_allograph/";
    annotator.load_allographs_container.init(allograph, url, show);
}

function get_allograph(allograph) {
    var annotations = annotator.annotations;
    var allograph_id;
    $.each(annotations, function() {
        if (this.feature == allograph) {
            allograph_id = this.hidden_allograph.split('::')[0];
        }
    });
    return allograph_id;
}

function show_url_allograph(dialog, annotation, button) {
    var features = annotator.vectorLayer.features;
    if (button.data('hidden')) {
        button.data('hidden', false);
        $('.link_graphs').after(' <img src="/static/digipal/images/ajax-loader3.gif" id="url_allograph_gif" />');
        var url = $("<div class='allograph_url_div' data-url-type='short'>");
        var allograph_url, stored = false;
        var a = $('<input type="text">');
        a.css('width', '100%');
        var title = $('.name_temporary_annotation').val();
        var desc = $('.editor_active').html();
        if (desc) {
            desc.replace('contenteditable="true"', '');
        }
        // get annotations visibility status
        var getAnnotationsVisibility = $('.toggle-state-switch').bootstrapSwitch('state');
        var layerExtent = annotator.map.getExtent();
        var dialogPosition = $('.dialog_annotations').offset();
        var checkboxesOff = [];
        var checkboxes = $('.checkVectors');
        var i;
        var stored = false;
        checkboxes.each(function() {
            if (!$(this).is(':checked')) {
                checkboxesOff.push($(this).parent('p').data('annotation'));
            }
        });

        if (annotation !== null && annotation && !$.isEmptyObject(annotation)) {
            for (i = 0; i < features.length; i++) {
                if (annotation.graph == features[i].graph && features[i].stored) {
                    stored = true;
                }
            }
        }

        if (annotator.selectedFeature.stored) {
            annotation = annotator.selectedFeature;
            stored = true;
        }

        var uncheckedAllographs = (function() {
            var checkboxesList = {
                'allographs': [],
                'hands': []
            };
            var allographs = $('.checkVectors').not(':checked');
            var hands = $('.checkVectors_hands').not(':checked');
            allographs.each(function() {
                checkboxesList.allographs.push($(this).attr("value"));
            });
            hands.each(function() {
                checkboxesList.hands.push($(this).attr("value"));
            });
            return checkboxesList;
        })();

        var personal_annotation = (function() {
            var element = $('.public_text_dialog_div');
            if (element.length) {
                var value = element.html();
                if ($.trim(value) && !isNodeEmpty(value)) {
                    return value;
                }
            }
            return false;
        })();

        var multiple = false,
            url_temp;
        if (annotation !== null && typeof annotation !== "undefined" && !$.isEmptyObject(annotation) && stored) {

            if (annotator.selectedAnnotations.length &&
                annotator.selectedFeature.linked_to != 'undefined' &&
                annotator.selectedFeature.linked_to.length && allow_multiple()) {

                multiple = true;
                allograph_url = [];

                for (i = 0; i < annotator.selectedAnnotations.length; i++) {
                    if (annotator.selectedAnnotations[i].is_editorial) {
                        url_temp = 'graph=' + annotator.selectedAnnotations[i].vector_id;
                    } else {
                        url_temp = 'graph=' + annotator.selectedAnnotations[i].graph;
                    }
                    allograph_url.push(url_temp);

                }

                allograph_url = window.location.hostname + document.location.pathname + '?' + allograph_url.join('&') + '&map_extent=' + JSON.stringify(layerExtent);

            } else {
                if (annotator.selectedFeature.is_editorial) {
                    allograph_url = window.location.hostname + document.location.pathname + '?graph=' + annotator.selectedFeature.vector_id;
                } else {
                    allograph_url = window.location.hostname + document.location.pathname + '?graph=' + annotator.selectedFeature.graph;
                }
            }

        } else {
            var geometryObject, geoJSONText;
            if (annotator.selectedAnnotations.length > 1 && allow_multiple()) {

                allograph_url = [];

                for (i = 0; i < annotator.selectedAnnotations.length; i++) {

                    geometryObject = annotator.selectedAnnotations[i];
                    geoJSONText = JSON.parse(annotator.format.write(geometryObject));

                    geoJSONText.title = title;
                    geoJSONText.desc = encodeURIComponent(desc);
                    geoJSONText.dialogPosition = dialogPosition;
                    geoJSONText.extent = layerExtent;
                    geoJSONText.visibility = getAnnotationsVisibility;

                    if (checkboxesOff.length) {
                        geoJSONText.checkboxes = checkboxesOff;
                    }

                    url_temp = 'temporary_vector=' + annotator.utils.Base64.encode(JSON.stringify(geoJSONText));

                    allograph_url.push(url_temp);

                }
                allograph_url = window.location.hostname +
                    document.location.pathname + '?' + allograph_url.join('&');
            } else {

                geometryObject = annotator.selectedFeature;
                geoJSONText = JSON.parse(annotator.format.write(geometryObject));

                geoJSONText.title = title;
                geoJSONText.desc = encodeURIComponent(desc);
                geoJSONText.dialogPosition = dialogPosition;
                geoJSONText.extent = layerExtent;
                geoJSONText.visibility = getAnnotationsVisibility;

                if (checkboxesOff.length) {
                    geoJSONText.checkboxes = checkboxesOff;
                }
                allograph_url = window.location.hostname +
                    document.location.pathname + '?temporary_vector=' + annotator.utils.Base64.encode(JSON.stringify(geoJSONText));
            }
        }

        if (uncheckedAllographs.hands.length || uncheckedAllographs.allographs.length) {
            allograph_url += '&hidden=' + annotator.utils.Base64.encode(JSON.stringify(uncheckedAllographs));
        }

        if (personal_annotation) {
            allograph_url += '&note=' + annotator.utils.Base64.encode(personal_annotation);
        }

        var settings = loader.digipal_settings;
        allograph_url += '&settings=' + annotator.utils.Base64.encode(JSON.stringify(settings));

        dputils.gapi_shorten_url(allograph_url, function(short_url) {
            $('#url_allograph_gif').fadeOut().remove();
            a.attr('value', short_url);
            a.attr('title', 'Copy link to annotation and share it');
            button.data('url', short_url);
            var p = $('<div>');
            p.css('text-align', 'right');
            p.css('margin-top', '0.34em');
            url.append(a);

            p.append("<button data-container='body' data-placement='bottom' data-toggle='tooltip' title='Display long url' style='font-size: 12px;' class='btn btn-default btn-xs' id='long_url'>Long URL?</button> ");
            p.append(" <button data-container='body' data-placement='bottom' data-toggle='tooltip' title='Hide URL' style='font-size: 12px;' class='btn btn-default btn-xs' id='close_div_url'><span class='glyphicon glyphicon-remove'></span></button>");

            url.append(p);
            dialog.prepend(url);
            $("[data-toggle='tooltip']").tooltip();
            var long_url_button = $('#long_url');
            long_url_button.on('click', function() {
                if (url.data('url-type') == 'short') {
                    a.attr('value', 'http://' + allograph_url);
                    button.data('url', 'http://' + allograph_url);
                    url.data('url-type', 'long');
                    long_url_button.text('Short URL?');
                    long_url_button.data('original-title', 'Show short URL');
                } else {
                    a.attr('value', short_url);
                    button.data('url', short_url);
                    url.data('url-type', 'short');
                    long_url_button.text('Long URL?');
                    long_url_button.data('original-title', 'Show long URL');
                }
            });

            $('#close_div_url').on('click', function() {
                remove_url_div();
            });
        });

    } else {
        button.data('hidden', true);
        var url_allograph_element = dialog.parent().find('.allograph_url_div');
        url_allograph_element.fadeOut().remove();
    }
}

function showBox(selectedFeature, callback) {

    var features = annotator.vectorLayer.features;
    var id = Math.random().toString(36).substring(7);
    var can_edit = $('#development_annotation').is(':checked');
    var n = 0;
    for (var i = 0; i < features.length; i++) {
        if (features[i].feature == annotator.selectedFeature.feature && features[i].hand == annotator.selectedFeature.hand && features[i].stored) {
            n++;
        }
    }

    if ($(".number_annotated_allographs").length) {
        $(".number_annotated_allographs .number-allographs").html(n);
    }

    annotator.dialog.init(selectedFeature, id, function() {
        if (callback) {
            callback();
        }
    });

}

function load_data(selectedFeature, dialog, callback) {
    var content_type = 'graph';
    var prefix = 'annotator_';
    var url, request;
    var cache = annotator.cacheAnnotations;
    var can_edit = $('#development_annotation').is(':checked');

    var select_allograph = get_forms().allograph_form;
    var allograph;

    if (!$.isEmptyObject(selectedFeature)) {
        allograph = selectedFeature.allograph_id;
    } else {
        allograph = select_allograph.val();
    }

    if (typeof selectedFeature == "null" || $.isEmptyObject(selectedFeature) || !selectedFeature.hasOwnProperty('graph')) {

        if (can_edit) {
            if (!allograph) {
                dialog.find('#components_tab').html('<p class="component_labels">Choose an allograph from the dropdown</p>');
                var targets = $('[data-target="#components_tab"]').add($('[data-target="#aspects_tab"]')).add($("[data-target='#notes_tab']"));
                targets.hide();
                if (callback) {
                    return callback();
                }
            }
            content_type = 'allograph';
            url = 'old/' + content_type + '/' + allograph + '/';
            annotator.api.request(url, function(data) {
                cache.update('allograph', data[0]['allograph_id'], data[0]);
                refresh_dialog(dialog, data[0], selectedFeature, callback);
            });
        } else {
            refresh_features_dialog(selectedFeature, dialog);
            if (callback) {
                callback();
            }
        }
    } else {

        var graph = selectedFeature.graph;

        // if there's no allograph cached, I make a full AJAX call
        if (!cache.search("allograph", allograph)) {

            url = 'old/' + content_type + '/' + selectedFeature.graph + '/';
            annotator.api.request(url, function(data) {
                cache.update('allograph', data[0]['allograph_id'], data[0]);
                cache.update('graph', graph, data[0]);
                data[0]['user_note'] = selectedFeature.user_note;
                data[0]['graph_id'] = graph;
                refresh_dialog(dialog, data[0], selectedFeature, callback);
            });

            // else if allograph is cached, I only need the features, therefore I change the URL to omit allographs
        } else if (cache.search("allograph", allograph) && (!cache.search('graph', graph))) {

            url = 'old/' + content_type + '/' + selectedFeature.graph + '/features';
            annotator.api.request(url, function(data) {
                data[0]['allographs'] = cache.cache.allographs[allograph];
                cache.update('graph', graph, data[0]);
                data[0]['user_note'] = selectedFeature.user_note;
                data[0]['graph_id'] = graph;
                refresh_dialog(dialog, data[0], selectedFeature, callback);
            });

            // otherwise I have both cached, I can get them from the cache object
        } else {
            var data = {};
            data['allographs'] = cache.cache.allographs[allograph];
            data['features'] = cache.cache.graphs[graph]['features'];
            data['allograph_id'] = cache.cache.graphs[graph]['allograph_id'];
            data['graph_id'] = graph;
            data['hand_id'] = cache.cache.graphs[graph]['hand_id'];
            data['hands'] = cache.cache.graphs[graph]['hands'];
            data['display_note'] = cache.cache.graphs[graph]['display_note'];
            data['internal_note'] = cache.cache.graphs[graph]['internal_note'];
            data['user_note'] = selectedFeature.user_note;
            data['aspects'] = cache.cache.graphs[graph]['aspects'];
            refresh_dialog(dialog, data, selectedFeature, callback);
        }
    }
}

function refresh_features_dialog(data, dialog) {
    var features = data.features;
    var notes = "";
    var s = '<ul>';
    if (data.hasOwnProperty('features') && !$.isEmptyObject(features)) {
        var components = [];
        for (i = 0; i < features.length; i++) {
            var component = features[i].name;
            if (components.indexOf(component) < 0) {
                s += "<li class='component'><b>" + component + "</b></li>";
            }
            for (j = 0; j < features[i].feature.length; j++) {
                var feature = features[i].feature[j];
                s += "<li class='feature'>" + feature + "</li>";
            }
            components.push(component);
        }
    } else if (data.hasOwnProperty('features') && $.isEmptyObject(features)) {
        s += window.ANNOTATOR_UNDESCRIBED_GRAPH_HTML;
        //dialog.css('height', '100px');
    }

    s += "</ul>";

    if (data.hasOwnProperty('display_note') && data.display_note) {
        notes += "<label class='label-dialog'>Public Note</label>";
        notes += "<div class='static_text_dialog_div'>" + data.display_note + '</div>';
    }

    if (annotator.isAdmin == 'True' && data.hasOwnProperty('internal_note') && data.internal_note) {
        notes += "<label class='label-dialog'>Internal Note</label>";
        notes += "<div class='static_text_dialog_div'>" + data.internal_note + '</div>';
    }

    notes += "<label class='label-dialog'>Your Note</label>";
    notes += "<div class='public_text_dialog_div form-control'></div>";

    dialog.find('#components_tab').html(s);
    dialog.find('#notes_tab').html(notes);

    init_note_field('.public_text_dialog_div', annotator, 'user_note');
                            
    if ($.isEmptyObject(data) || data && data.components && !data.components.length) {
        dialog.find('#components_tab').hide();
        $('[data-target="#components_tab"]').hide();
        $('[data-target="#notes_tab"]').tab('show');
    }

    var aspects = "<ul>";
    if (data.hasOwnProperty('aspects') && data.aspects.length) {
        for (var i = 0; i < data.aspects.length; i++) {
            aspects += "<li class='component'><b>" + data.aspects[i].name + "</b></li>";
            for (var j = 0; j < data.aspects[i].features.length; j++) {
                aspects += "<li class='feature'>- " + data.aspects[i].features[j].name + "</li>";
            }
        }
    } else {
        aspects += "<li class='component'>No aspects defined</li>";
        $('[data-target="#aspects_tab"]').hide();
    }
    aspects += "</ul>";

    dialog.find('#aspects_tab').html(aspects);

}

function refresh_dialog(dialog, data, selectedFeature, callback) {

    var can_edit = $('#development_annotation').is(':checked');

    var copy_data = $.extend(true, {}, data);
    var copy_cache = $.extend(true, {}, annotator.cacheAnnotations.cache);
    if (can_edit) {

        if (annotator.selectedAnnotations.length > 1) {
            var selected = [];

            for (var g = 0; g < annotator.selectedAnnotations.length; g++) {
                if (annotator.selectedAnnotations[g].hasOwnProperty('graph') && annotator.selectedAnnotations[g].graph) {
                    selected.push(annotator.selectedAnnotations[g].graph);
                }
            }

            if (selected.length > 1) {
                copy_data.allographs.components = common_components(selected, copy_cache, copy_data.allographs.components);
                copy_data.allographs.aspects = common_components(selected, copy_cache, copy_data.allographs.aspects, "aspects");
            }
        }

        update_dialog('annotator_', copy_data, annotator.selectedAnnotations, function(s) {

            $('#id_internal_note').remove();
            $('#id_display_note').remove();

            var cache = annotator.cacheAnnotations.cache;
            var aspects_list = load_aspects(annotator.cacheAnnotations.cache.allographs[data.allograph_id].aspects, data.graph_id, cache);
            var aspects = annotator.cacheAnnotations.cache.allographs[data.allograph_id].aspects;
            var components = annotator.cacheAnnotations.cache.allographs[data.allograph_id].components;

            setNotes(selectedFeature, dialog.find('#notes_tab'));
            dialog.find('#components_tab').html(s);
            dialog.find('#aspects_tab').html(aspects_list);
            if (!aspects.length) {
                $('[data-target="#aspects_tab"]').hide();
            } else {
                $('[data-target="#aspects_tab"]').show();
            }
            var check_all = $('.check_all');
            check_all.click(function(event) {
                var checkboxes = $(this).parent().parent().next().find('input[type=checkbox]');
                checkboxes.attr('checked', true);
                event.stopPropagation();
            });

            var uncheck_all = $('.uncheck_all');
            uncheck_all.click(function(event) {
                var checkboxes = $(this).parent().parent().next().find('input[type=checkbox]');
                checkboxes.attr('checked', false);
                event.stopPropagation();
            });

            var set_by_default = dialog.find('.set_by_default');
            set_by_default.on('click', function(event) {
                var component_id = $(this).data('component');
                var allograph = $('#panelImageBox .allograph_form').val();
                check_features_by_default(component_id, allograph, annotator.cacheAnnotations.cache);
                event.stopPropagation();
            });

            var set_all_by_default = $('.set_all_by_default');
            set_all_by_default.on('click', function(event) {
                var components = [];
                var allograph = $('#panelImageBox .allograph_form').val();

                for (var i in annotator.cacheAnnotations.cache.allographs) {
                    for (var j = 0; j < annotator.cacheAnnotations.cache.allographs[i].components.length; j++) {
                        var component = annotator.cacheAnnotations.cache.allographs[i].components[j].id;
                        components.push(component);
                    }
                }

                for (var c in components) {
                    check_features_by_default(components[c], allograph, annotator.cacheAnnotations.cache);
                }

                event.stopPropagation();
            });

            var component_labels = dialog.find('.component_labels');
            component_labels.click(function() {
                var component = $(this);
                var div = $("#" + $(this).data('id'));
                if (!div.data('hidden')) {
                    div.slideUp().data('hidden', true);
                    component.next('.checkboxes_div').hide();
                    component.find('.arrow_component').removeClass('fa-angle-double-up').addClass('fa-angle-double-down');
                } else {
                    div.slideDown().data('hidden', false);
                    component.next('.checkboxes_div').show();
                    component.find('.arrow_component').removeClass('fa-angle-double-down').addClass('fa-angle-double-up');
                }
            });

            var annotation;
            var features = annotator.vectorLayer.features;
            for (var i = 0; i < features.length; i++) {
                for (var j in annotator.annotations) {
                    if (annotator.annotations[j].graph == features[i].graph) {
                        annotation = annotator.annotations[j];
                    }
                }
            }
            var feature_checkboxes = $(".features_box");
            feature_checkboxes.on('change', function() {
                var value = $(this).val();
                if (annotation && annotation.state == 'Insert') {
                    var index = annotation.features.indexOf(value);
                    if (index < 0) {
                        annotation.features.push(value);
                    } else {
                        annotation.features.splice(index, 1);
                    }
                }
            });

            if (callback) {
                callback();
            }
        });

    } else {

        refresh_features_dialog(data, dialog);
        if (callback) {
            callback();
        }
    }
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

function get_forms() {
    var panel;
    var modal;
    if ($('.tab-pane.active').attr('id') == 'annotator') {
        panel = $('#panelImageBox');
        modal = $('.dialog_annotations');
    } else {
        panel = $('.modal-body');
        modal = $('.myModal');
    }

    return {
        'allograph_form': panel.find('.allograph_form'),
        'hand_form': panel.find('.hand_form'),
        'frmAnnotation': panel.find('.frmAnnotation'),
        'panel': panel,
        'modal': modal
    };
}


function highlight_vectors() {

    var allograph_form_id = get_forms().allograph_form.attr('id');
    var features = annotator.vectorLayer.features;

    $('#' + allograph_form_id + '_chzn').find('li').on('mouseover', function() {
        var text = $(this).text();

        for (i = 0; i < features.length; i++) {
            if (features[i].feature == text) {
                features[i].originalColor = features[i].style.fillColor;
                features[i].originalWidth = 2;
                features[i].style.strokeColor = 'red';
                features[i].style.strokeWidth = 6;
            }
        }
        annotator.vectorLayer.redraw();
        restoreFullscreenPositions();
    });

    $('#' + allograph_form_id + '_chzn').find('li').on('mouseout', function() {
        var text = $(this).text();
        for (i = 0; i < features.length; i++) {
            if (features[i].feature == text) {
                features[i].style.strokeColor = features[i].originalColor;
                features[i].style.strokeWidth = features[i].originalWidth;
            }
        }
        annotator.vectorLayer.redraw();
        restoreFullscreenPositions();
    });

}

function highlight_unsaved_vectors(button) {
    var features = annotator.unsaved_annotations;
    var color = "#fe2deb";
    for (i = 0; i < features.length; i++) {
        features[i].feature.originalColor = '#ee9900';
        if (features[i].feature.style) {
            features[i].featureoriginalWidth = 2;
            features[i].feature.style.strokeColor = color;
            features[i].feature.style.fillColor = color;
        } else {
            features[i].feature.style = {};
            features[i].feature.fillopacity = 0.3;
            features[i].featureoriginalWidth = 2;
            features[i].feature.style.strokeColor = color;
            features[i].feature.style.fillColor = color;
        }
    }
    annotator.vectorLayer.redraw();
    button.addClass('active');
    restoreFullscreenPositions();
}


function unhighlight_unsaved_vectors(button) {
    var features = annotator.unsaved_annotations;
    for (i = 0; i < features.length; i++) {
        features[i].feature.style.strokeColor = features[i].feature.originalColor;
        features[i].feature.style.fillColor = features[i].feature.originalColor;
        features[i].feature.style.strokeWidth = features[i].feature.originalWidth;
    }
    annotator.vectorLayer.redraw();
    button.removeClass('active');
    restoreFullscreenPositions();
}

function trigger_highlight_unsaved_vectors() {
    $('.number_unsaved_allographs').on('click', function() {
        if (!$(this).hasClass('active')) {
            highlight_unsaved_vectors($(this));
        } else {
            unhighlight_unsaved_vectors($(this));
        }
    });
}

function CollectionFromImage(button) {
    var id = button.attr('id');
    var label = button.data('label');
    var id = Math.random().toString(36).substring(7);
    var collections = JSON.parse(localStorage.getItem('collections'));

    var collection = {
        "id": id,
        'editorial': [],
        'annotations': []
    };

    var features = annotator.vectorLayer.features;

    for (var i = 0; i < features.length; i++) {
        if (features[i].stored && features[i].is_editorial) {
            collection.editorial.push(features[i].id);
        } else if (features[i].stored && features[i].graph) {
            collection.annotations.push(parseInt(features[i].graph, 10));
        }
    }

    collections[label] = collection;
    localStorage.setItem('collections', JSON.stringify(collections));
    localStorage.setItem('selectedCollection', id);
    notify("<a style='color:#468847;' href='/digipal/collection/" + label + "'>Collection created</a>", "success");
    update_collection_counter();
    $(window).bind('storage', function(e) {
        update_collection_counter();
    });
}

/**
 * Displays an alert for each error in the Ajax response (json).
 * Returns true only if data is invalid (contains error or empty).
 *
 * @param data
 *              JSON response from the server
 *              E.g. {'errors': ['allograph: This field is required.',
 *              'hand: This field is required.'], 'success': False}
 */

function handleErrors(data) {
    if (data && 'success' in data && data.success) return false;
    // something is not right
    var message = 'Internal error: the AJAX response is empty';
    if (data) {
        message = 'Internal error: no "success" in AJAX response';
        if ('success' in data) {
            message = '';
            if (!data.success) {
                message = 'Unknown error.';
                if ('errors' in data) {
                    message = '';
                    for (var i in data.errors) {
                        message += '<p>' + data.errors[i] + '</p>';
                    }
                }
            }
        }
    }

    if (message) {
        updateStatus(message, 'danger');
    }

    return (message.length > 0);
}

/**
 * Updates the status message and style of the last operation.
 *
 * @param msg
 *              Status message to display.
 * @param status
 *              Either 'error', 'success' or ''
 */



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

function updateTabCounter() {
    var tab_link = $('a[data-target="#allographs"]');
    var unsaved_link = $('.number_unsaved_allographs');
    var f = annotator.vectorLayer.features;
    annotator.unsaved_annotations = [];
    var d = 0;
    var x = 0;
    for (y = 0; y < f.length; y++) {
        if (f[y].stored) {
            d++;
        } else if (!f[y].stored && f[y].state == 'Insert') {
            x++;
            annotator.unsaved_annotations.push(f[y]);
        }
    }

    tab_link.html('Annotations (' + d + ')');
    unsaved_link.html(x);
}

function delete_annotation(layer, feature, number_annotations) {
    var featureId = feature.graph || feature.id;
    var temp = feature;
    updateStatus('Deleting annotations', 'warning');
    layer.destroyFeatures([feature]);
    var isNotStored = false;
    var url = annotator.absolute_image_url + 'delete/' + featureId + '/';
    var _callback = function() {
        if (number_annotations > 1) {
            updateStatus('Annotations deleted.', 'success');
        } else {
            updateStatus('Annotation deleted.', 'success');
        }

        var allograph = $('#panelImageBox .allograph_form option:selected').text();
        var allograph_id = $('#panelImageBox .allograph_form').val();

        refresh_letters_container_init(temp, temp.feature, allograph_id, true);

        if (temp['state'] == 'Insert') {
            var element = $('.number_unsaved_allographs');
            var number_unsaved = element.html();
            var annotations = annotator.unsaved_annotations;
            for (var i = 0; i < annotations.length; i++) {
                if (annotations[i].feature.id == feature.id) {
                    annotations.splice(i, 1);
                    break;
                }
            }
            element.html(annotations.length);
            temp = null;
        }

        annotator.selectedAnnotations = [];

        var boxes = $(".dialog_annotations");
        if (boxes.length) {
            boxes.remove();
        }

        updateTabCounter();
        annotator.has_changed = true;
    };

    if (feature.popup) {
        deletePopup(feature);
    }

    $('.olPopup').remove();

    if (!feature.stored) {
        updateStatus('Annotation deleted locally', 'success');
        isNotStored = true;
        _callback();
        return false;
    }

    $.ajax({
        url: url,
        data: '',
        error: function(xhr, textStatus, errorThrown) {
            throw new Error(textStatus);
        },
        success: function(data) {
            if (!handleErrors(data)) {
                _callback();
            }
        }
    });
}

function make_form() {

    if (!annotator.selectedFeature && !annotator.selectedAnnotations.length) {
        updateStatus('Select annotations to proceed', 'danger');
        return false;
    }

    var forms = get_forms();
    var allograph_form = forms.allograph_form;
    var hand_form = forms.hand_form;
    var form = forms.frmAnnotation;
    var panel = forms.modal;
    if (!annotator.editorial.active && (!allograph_form.val() || !hand_form.val())) {
        updateStatus('Hand and Allograph are required', 'danger');
        return false;
    }

    var obj = {};
    var array_values_checked = [],
        array_values_unchecked = [];
    var features = {};
    var has_features = false;

    if (panel.find('.features_box').length) {
        panel.find('.features_box').each(function() {
            if ($(this).is(':checked') && !$(this).prop('indeterminate')) {
                array_values_checked.push($(this).val());
                has_features = true;
            } else if (!$(this).is(':checked') && !$(this).prop('indeterminate')) {
                array_values_unchecked.push($(this).val());
            }
        });
    }

    var features_labels = [];
    var components = panel.find('.feature_containers');
    $.each(components, function() {
        if ($(this).find('.features_box:checked').length) {
            var component_id = $(this).attr('id');
            var component_name = $('[data-id="' + component_id + '"]');
            var component = $.trim(component_name.children('b').text());
            var features_labels_array = [];
            var features_input = $(this).find('.features_box:checked');

            var f_id, f_value, label_element;
            $.each(features_input, function() {
                f_id = $(this).attr('id');
                f_value = $(this).val();
                label_element = $('label[for="' + f_id + '"]');
                features_labels_array.push(label_element.text());
            });

            features_labels.push({
                'feature': features_labels_array,
                'name': component,
                'component_id': parseInt(f_value.split(':')[0], 10)
            });
        }
    });


    obj['feature'] = array_values_checked;

    var form_serialized = form.find(":input").filter(function() {
        return $.trim(this.value).length > 0;
    }).serialize();
    var s = '';

    for (i = 0; i < array_values_checked.length; i++) {
        s += '&feature=' + array_values_checked[i];
    }

    for (i = 0; i < array_values_unchecked.length; i++) {
        s += '&-feature=' + array_values_unchecked[i];
    }

    form_serialized += s;

    var display_note, internal_note;
    if (annotator.editorial.active) {
        display_note = $('#display_note');
        internal_note = $('#internal_note');
    } else {
        display_note = $('#id_display_note');
        internal_note = $('#id_internal_note');
    }
    if (display_note.length && !isNodeEmpty(display_note.html())) {
        form_serialized += "&display_note=" + display_note.html();
    }

    if (internal_note.length && !isNodeEmpty(internal_note.html())) {
        form_serialized += "&internal_note=" + internal_note.html();
    }

    if (panel.find('.aspect').length) {
        var aspects = panel.find('.aspect');
        aspects.each(function() {
            if ($(this).is(':checked') && !$(this).prop('indeterminate')) {
                form_serialized += "&aspect=" + $(this).val();
            } else if (!$(this).is(':checked') && !$(this).prop('indeterminate')) {
                form_serialized += "&-aspect=" + $(this).val();
            }
        });
    }

    return {
        'form_serialized': form_serialized,
        'features_labels': features_labels
    };

}


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

function save(url, graphs, data, ann, features) {

    var isModifyToolActive = data.isModifyToolActive;
    $.ajax({
        url: url,
        type: 'POST',
        data: data['form_serialized'],
        beforeSend: function() {
            updateStatus('Saving annotation ...', 'warning');
        },
        error: function(xhr, textStatus, errorThrown) {
            updateStatus(textStatus, 'danger');
            // annotator.setSavedAttribute(feature, Annotator.UNSAVED, false);
        },
        success: function(data) {
            if (!handleErrors(data)) {
                updateStatus('Saved annotation.', 'success');

                var forms = get_forms();
                var select_allograph = forms.allograph_form;

                var allograph = select_allograph.find('option:selected').text();
                var allograph_id = select_allograph.val();

                refresh_letters_container_init(true, allograph, allograph_id, true);

                var f = annotator.vectorLayer.features;
                var f_length = annotator.vectorLayer.features.length;
                var feature, id, temp;
                var form_serialized = data;

                var new_graphs = data.graphs;

                for (var i = 0; i < new_graphs.length; i++) {

                    /*  Updating cache  */

                    var is_editorial = false;
                    var new_graph = new_graphs[i].graph,
                        new_allograph = new_graphs[i].allograph_id;
                    annotator.cacheAnnotations.update('graph', new_graph, new_graphs[i]);
                    annotator.cacheAnnotations.update('allograph', new_allograph, new_graphs[i]);
                    if (typeof new_graph == 'undefined' || !new_graph) {
                        allographsPage.cache.update('graph', new_graphs[i].vector_id, new_graphs[i]);
                        is_editorial = true;
                    } else {
                        allographsPage.cache.update('graph', new_graph, new_graphs[i]);
                    }
                    allographsPage.cache.update('allograph', new_allograph, new_graphs[i]);

                    for (var k = 0; k < annotator.selectedAnnotations.length; k++) {
                        var crntFt = annotator.selectedAnnotations[k];
                        if (!crntFt.hasOwnProperty('graph') && !crntFt.graph && crntFt.stored) {
                            if (crntFt.id == new_graphs[i].id || crntFt.id == new_graphs[i].vector_id) {
                                crntFt.is_editorial = true;
                                if ($('#show_editorial_annotations').is(':checked')) {
                                    stylize(crntFt, '#222', '#222', 0.4);
                                } else {
                                    stylize(crntFt, '#222', '#222', 0);
                                }
                            }
                        }
                    }

                    /*  Updating annotator features */
                    var n = 0;
                    for (var feature_ind = 0; feature_ind < f_length; feature_ind++) {
                        if (f[feature_ind].id == new_graphs[i].vector_id || f[feature_ind].id == new_graphs[i].annotation_id || (new_graphs[i].hasOwnProperty('graph') && f[feature_ind].graph == new_graphs[i].graph)) {
                            feature = f[feature_ind];
                            n++;
                            //id = feature.id;
                            feature.feature = allograph;
                            feature.graph = new_graph;
                            feature.state = null;

                            if (feature.is_editorial || !new_graph) {
                                feature.vector_id = new_graphs[i].annotation_id.toString();
                                feature.id = new_graphs[i].annotation_id.toString();
                                feature.is_editorial = true;
                            }

                            if (new_graphs[i].hasOwnProperty('hand_id')) {
                                feature.hand = new_graphs[i].hand_id;
                            }

                            if (new_graphs[i].hasOwnProperty('internal_note')) {
                                feature.internal_note = new_graphs[i].internal_note;
                            }

                            if (new_graphs[i].hasOwnProperty('display_note')) {
                                feature.display_note = new_graphs[i].display_note;
                            }

                            if (new_graphs[i].hasOwnProperty('allograph_id')) {
                                feature.allograph_id = new_graphs[i].allograph_id;
                            }

                            annotator.setSavedAttribute(feature, Annotator.SAVED, false);

                            var color;

                            if (new_graphs[i].hasOwnProperty('features')) {
                                feature.features = new_graphs[i].features;
                                var num_features = new_graphs[i].features.length;
                            }

                            var element = $('.number_unsaved_allographs');
                            var number_unsaved = element.html();
                            var unsaved_annotations = annotator.unsaved_annotations;

                            for (var ind = 0; ind < unsaved_annotations.length; ind++) {
                                if (unsaved_annotations[ind].feature.new_graph == new_graph) {
                                    unsaved_annotations.splice(ind, 1);
                                    ind--;
                                    break;
                                }
                            }

                            element.html(unsaved_annotations.length);

                            var flag = 0,
                                ann;
                            for (ann in annotator.annotations) {
                                if (annotator.annotations[ann].graph == new_graph) {
                                    annotator.annotations[ann].hidden_allograph = new_allograph + '::' + $.trim(allograph.split(',')[1]);
                                    annotator.annotations[ann].feature = allograph;
                                    annotator.annotations[ann].graph = new_graph;
                                    flag = 1;
                                }
                            }

                            if (!flag) {
                                ann = parseInt(ann, 10) + 1;
                                annotator.annotations[ann] = {};
                                annotator.annotations[ann].hidden_allograph = new_allograph + '::' + $.trim(allograph.split(',')[1]);
                                annotator.annotations[ann].feature = allograph;
                                annotator.annotations[ann].graph = new_graph;
                                //annotator.annotations[ann].vector_id = feature.vector_id;
                            }

                            let style_name = 'described';
                            if (new_graphs[i].hasOwnProperty('features') && new_graphs[i].features.length && !feature.is_editorial) {
                                feature.described = true;
                                feature.num_features = feature.features.length + 1;
                            } else if (new_graphs[i].hasOwnProperty('features') && !new_graphs[i].features.length && !feature.is_editorial) {
                                let style_name = 'undescribed';
                                feature.described = false;
                                feature.num_features = 0;
                            } else {
                                let style_name = 'editorial';
                                feature.described = false;
                                feature.num_features = 0;
                            }

                            stylize_predefined(feature, style_name);
                            feature.style.originalColor = color;
                            feature.style.strokeWidth = 2;
                            feature.stored = true;

                            if (new_graphs[i].hasOwnProperty('display_note')) {
                                feature.display_note = new_graphs[i].display_note;
                            }
                            if (new_graphs[i].hasOwnProperty('internal_note')) {
                                feature.internal_note = new_graphs[i].internal_note;
                            }
                            feature.last_feature_selected = null;
                            element.html(annotations.length);

                            var n = 0,
                                d = 0;
                            for (g = 0; g < f_length; g++) {
                                if (f[g].feature == feature.feature && f[g].stored) {
                                    n++;
                                }

                                if (f[g].stored) {
                                    d++;
                                }
                            }

                            $(".number_annotated_allographs .number-allographs").html(n);

                            $('[data-target="#allographs"]').html('Annotations (' + d + ')');
                        }
                    }
                }
                console.warn(n);
                annotator.selectedAnnotations = [];
            }

        },
        complete: function() {
            // GN: MOA-140: modify tool remains de-activated after save
            if (0 && isModifyToolActive) {
                annotator.transformFeature.activate();
            }
            annotator.has_changed = true;
            updateTabCounter();
        }
    });

}


function registerEvents() {
    var paths = $('#OpenLayers_Layer_Vector_27_vroot').find("path");

    if (paths.length < 1) return;

    annotator.events = true;

    if (annotator.isAdmin == 'True') {
        if (SHOW_NOTE_ON_HOVER) {
            // mouseover and mouseout events
            // for displaying popups when a graphs has a display note field
            paths.unbind('mouseenter').on('mouseenter', function() {
                var features = annotator.vectorLayer.features;
                for (var i = 0; i < features.length; i++) {
                    if ($(this).attr('id') == features[i].geometry.id) {
                        if (features[i].display_note) {
                            createPopup(features[i]);
                        }
                    }
                }
            }).unbind('mouseleave').on('mouseleave', function() {
                var features = annotator.vectorLayer.features;
                for (var i = 0; i < features.length; i++) {
                    if (features[i].popup) {
                        deletePopup(features[i]);
                    }
                }
            });
        }

    }

    // GN: if not in admin/edit mode then a single click opens the box.
    // so no need for supporting the double click.
    if (annotator.isAdmin == 'True') {
        paths.unbind('dblclick').on('dblclick', function(event) {

            if (annotator.boxes_on_click) {
                boxes_on_click = true;
            }

            if (annotator.selectFeature.active && !annotator.boxes_on_click) {

                annotator.boxes_on_click = true;
                var boxes_on_click_element = $("#boxes_on_click");
                boxes_on_click_element.prop('checked', true);
                var boxes_on_click = false;
                var annotation;

                for (var a in annotator.vectorLayer.features) {
                    if (annotator.vectorLayer.features[a].graph == annotator.selectedFeature.graph) {
                        annotation = annotator.vectorLayer.features[a];
                    }
                }
                showBox(annotation, function() {
                    if (!boxes_on_click) {
                        annotator.boxes_on_click = false;
                        boxes_on_click_element.prop('checked', false);
                        restoreFullscreenPositions();
                        highlight_vectors();
                    }
                });

            }
            /*
            showBox(annotation, function() {
                if (!boxes_on_click) {
                    annotator.boxes_on_click = false;
                    boxes_on_click_element.prop('checked', false);
                }
            });
            */
        });
    }
}


DigipalAnnotator.prototype.activateKeyboardShortcuts = function() {
    var _self = this;
    var toggleAll = _self.utils.toggleAll;
    $(document).bind('keydown', function(event) {
        activeControls = _self.map.getControlsBy('active', true);
        var code = event.which || event.keyCode;

        //if (event.shiftKey && annotator.isAdmin == 'True') {
        if (annotator.isAdmin == 'True') {
            var activeElement = document.activeElement;
            var isActiveElementEditable = activeElement && (
                activeElement.isContentEditable
                || activeElement.tagName.toLowerCase() == 'input'
            );

            //var focused_tag = $(':focus').first().prop('tagName');
            if (!isActiveElementEditable) {
                switch (code) {
                    case 109: // m
                    case 77: // M
                        // not set if no vector selected
                        if (_self.transformFeature) {
                            toggleAll(activeControls, false);
                            _self.transformFeature.activate();
                            //_self.modifyFeature.activate();
                        }
                        break;
                    case 46: //  DEL
                        toggleAll(activeControls, false);
                        _self.deleteFeature.activate();
                        break;
                    case 100: // d
                    case 68: // D
                        toggleAll(activeControls, false);
                        _self.rectangleFeature.activate();
                        break;
                    case 103: // g
                    case 71: // G
                        toggleAll(activeControls, false);
                        _self.selectFeature.activate();
                        break;
                    case 32: // space
                        var select_active = annotator.selectFeature.active;
                        toggleAll(activeControls, false);
                        if (select_active) {
                            _self.rectangleFeature.activate();
                        } else {
                            _self.selectFeature.activate();
                        }
                        event.preventDefault();
                        break;
                    case 87: // W
                        toggleAll(activeControls, false);
                        _self.dragFeature.activate();
                        break;
                    case 122: // z
                    case 90: // Z
                        toggleAll(activeControls, false);
                        _self.zoomBoxFeature.activate();
                        break;
                    case 115: // s
                    case 83: // S
                        _self.saveButton.trigger();
                        break;
                    case 102: // f
                    case 70: // F
                        _self.full_Screen();
                        break;
                    case 65: // a
                        if (annotator) annotator.open_allograph_selector();
                        event.preventDefault();
                        break;
                    case 38: // &
                        annotator.map.moveByPx(0, -60);
                        annotator.vectorLayer.redraw();
                        restoreFullscreenPositions();
                        break;
                    case 40: // (
                        annotator.map.moveByPx(0, 60);
                        annotator.vectorLayer.redraw();
                        restoreFullscreenPositions();
                        break;
                    case 37: // %
                        annotator.map.moveByPx(-60);
                        annotator.vectorLayer.redraw();
                        restoreFullscreenPositions();
                        break;
                    case 39: // '
                        annotator.map.moveByPx(60);
                        annotator.vectorLayer.redraw();
                        restoreFullscreenPositions();
                        break;
                    case 187: // >> ?
                        annotator.vectorLayer.map.zoomIn();
                        break;
                    case 189: // 1/2
                        annotator.vectorLayer.map.zoomOut();
                        break;
                }
            }
        }
    });
};

function restoreFullscreenPositions() {
    var annotations_layer = $('#OpenLayers_Layer_Vector_27_svgRoot');
    annotations_layer.attr('width', $(window).width())
        .attr('height', $(window).height())
        .attr('viewport', "0 0 " + $(window).width() + " " + $(window).height());

    annotations_layer[0].setAttribute('viewBox', "0 0 " + $(window).width() + " " + $(window).height());
}
