function Allographs(dialog, cache) {

    var selectedAnnotations = {
        'allograph': null,
        'annotations': []
    };

    var temporary_vectors = [];

    // returning actual class object
    var allographs_cache = cache.init();

    // launcing init function
    var init = function() {
        events();
    };

    var self = this;

    // this function declares all events at loading
    var events = function() {

        var switcher = $('#toggle-annotations-mode');
        switcher.bootstrapSwitch();

        switcher.on('switch-change', function(e, data) {
            var graphs = $('[data-graph]');
            if ($(this).bootstrapSwitch('state')) {
                graphs.attr('data-original-title', 'Edit Graph');
            } else {
                graphs.attr('data-original-title', 'View Graph in Manuscript Viewer');
            }
        });

        /* creating dialog */
        dialog(annotator.image_id, {
            'container': '#allographs'
        }, function(dialog_instance) {

            self.dialog_instance = dialog_instance;

            /* applying delete event to selected feature */
            var delete_button = dialog_instance.selector.find('#delete');
            delete_button.click(function(event) {
                methods.delete();
            });

            var tabs = $('.myModal a[data-toggle="tab"]');
            tabs.on('shown.bs.tab', function(e) {
                if (e.target.getAttribute('data-target') == '#edit') {
                    self.dialog_instance.edit_letter.init(annotation.graph);
                } else if (e.target.getAttribute('data-target') == '#annotation-editor-tab') {
                    self.annotation_editor.set_graphids(get_graphs_from_annotations(selectedAnnotations.annotations));
                }
            });

            self.annotation_editor = $(self.dialog_instance.selector.find('#annotation-editor-tab')).annotation_editor().data('annotation_editor');

            /* applying delete event to selected feature */
            var save_button = dialog_instance.selector.find('#save');
            save_button.click(function(event) {
                methods.save();
                self.annotation_editor.save();
            });

        });

        /* applying select event to annotations */
        var annotations_li = $('.annotation_li');
        annotations_li.unbind().click(function(event) {
            methods.select_annotation($(this));
        });

        /* applying select all event */
        var select_all = $('.select_all');
        select_all.click(function(event) {
            methods.select_all($(this));
        });

        /* applying deselect all event */
        var deselect_all = $('.deselect_all');
        deselect_all.click(function(event) {
            methods.deselect_all($(this));
        });

        /* applying to_lightbox function */
        var to_lightbox = $('.to_lightbox');
        to_lightbox.on('click', function(event) {
            for (var i = 0; i < selectedAnnotations.annotations.length; i++) {
                methods.to_lightbox($(this), parseInt(selectedAnnotations.annotations[i].graph, 10), false);
            }
        });


        /* event to redirect from letters to annotator */
        var a_images = $('.annotation_li a');
        a_images.on('click', function(event) {
            if (!switcher.bootstrapSwitch('state')) {
                var id = $(this).closest('.annotation_li').data('graph');
                methods.to_annotator(id);

                /*
                var panel = $('#panelImageBox');
                $('body').animate({
                    scrollLeft: panel.position().left,
                    scrollTop: panel.position().top
                });
                */
                event.stopPropagation();

            }
            event.preventDefault();

        });

        keyboard_shortcuts.init();

    };


    var get_graphs_from_annotations = function(annotations) {
        var graphs = [];
        for (var i = 0; i < annotations.length; i++) {
            graphs.push(annotations[i].graph);
        }
        return graphs;
    };

    var methods = {

        select_annotation: function(this_annotation, callback) {
            var annotation = this.getFeatureById(this_annotation.data('graph'));
            var current_basket;
            var annotation_li = this_annotation;
            var a = selectedAnnotations.allograph;

            if (annotation_li.data('selected')) {
                utils.clean_annotations(annotation, selectedAnnotations.annotations);
                annotation_li.data('selected', false).removeClass('selected');
                select_annotation(annotation, false, callback);
            } else {
                selectedAnnotations.allograph = annotation.feature;
                selectedAnnotations.annotations.push(annotation);
                annotation_li.data('selected', true).addClass('selected');
                modal = true;
                select_annotation(annotation, true, callback);
                if (!self.dialog_instance.open) {
                    self.dialog_instance.show();
                }
            }

        },

        save: function() {
            if (!selectedAnnotations.annotations.length) {
                updateStatus('Select annotations to proceed', 'danger');
                return false;
            }
            var features = annotator.vectorLayer.features;
            var features_length = features.length;
            var selected_features = [];
            for (var i = 0; i < features_length; i++) {
                for (var j = 0; j < selectedAnnotations.annotations.length; j++) {
                    if (features[i].graph == selectedAnnotations.annotations[j].graph) {
                        selected_features.push(features[i]);
                    }
                }
            }
            annotator.saveAnnotation(selected_features, true);
        },

        delete: function() {
            var features = annotator.vectorLayer.features;
            var features_length = features.length;
            var selected_features = [];
            var vectors_list = [];
            var i, j;
            for (i = 0; i < features_length; i++) {
                for (j = 0; j < selectedAnnotations.annotations.length; j++) {
                    if (features[i].graph == selectedAnnotations.annotations[j].graph) {
                        selected_features.push(features[i]);
                    }
                }
            }

            j = 0;
            var msg = 'You are about to delete ' + selectedAnnotations.annotations.length + ' annotations. It cannot be restored at a later time! Continue?';
            if (confirm(msg)) {
                var nextAll, element, value;
                for (i = 0; i < selected_features.length; i++) {
                    delete_annotation(annotator.vectorLayer, selected_features[i], selected_features.length);
                    element = $('.annotation_li[data-graph="' + selected_features[i].graph + '"]');
                    nextAll = element.nextAll();
                    $.each(nextAll, function() {
                        value = parseInt($(this).find('.label').text(), 10);
                        $(this).find('.label').text(value - 1);
                    });
                    element.fadeOut().remove();
                }


                selectedAnnotations.annotations = [];
                self.dialog_instance.hide();

            }
        },

        deselect_all: function(button) {
            var key = button.data('key');
            var ul = $('.list-allographs[data-key="' + key + '"]');
            var panel = ul.parent();
            panel.find('.to_lightbox').attr('disabled', true);
            var inputs = $('input[data-key="' + key + '"]');
            var checkboxes = ul.find('.annotation_li.selected');

            //selectedAnnotations.annotations = [];
            temporary_vectors = [];
            //selectedAnnotations.allograph = null;

            for (var i = 0; i < checkboxes.length; i++) {
                methods.select_annotation($(checkboxes[i]));
            }

            $.each($('input'), function() {
                $(this).attr('checked', false);
            });

            if (self.dialog_instance.open) {
                self.dialog_instance.hide();
            }
        },

        select_all: function(button) {
            var key = button.data('key');
            var ul = $('.list-allographs[data-key="' + key + '"]');
            var panel = ul.parent();
            panel.find('.to_lightbox').attr('disabled', false);
            var checkboxes = ul.find('.annotation_li').not('.selected');
            var i = 0;
            for (i = 0; i < checkboxes.length; i++) {
                methods.select_annotation($(checkboxes[i]));
            }
        },

        to_lightbox: function(button, annotation, multiple) {
            var star = "<span class='glyphicon glyphicon-star starred-image'></span>";
            var el = $('[data-graph="' + annotation + '"]');
            if (add_to_lightbox(button, 'annotation', annotation, multiple) && !el.find('.starred-image').length) {
                el.append(star);
            }
        },

        to_annotator: function(annotation_graph_id) {
            annotator.vectorLayer.map.zoomToMaxExtent();
            var tab = $('a[data-target="#annotator"]');
            tab.tab('show');
            $('html, body').animate({
                scrollTop: $('#map').position().top + 'px'
            }, 150, function() {
                var annotation_graph;
                var select_allograph = $('#panelImageBox');
                for (var j in annotator.annotations) {
                    if (annotator.annotations[j].graph == annotation_graph_id) {
                        annotation_graph = annotator.annotations[j];
                        break;
                    }
                }
                annotator.selectFeatureByIdAndZoom(annotation_graph_id);
                select_allograph.find('.hand_form').val(annotator.selectedFeature.hand);
                select_allograph.find('.allograph_form').val(getKeyFromObjField(annotation_graph, 'hidden_allograph'));
                $('select').trigger('liszt:updated');
            });
        },

        getFeatureById: function(id) {
            var selectedFeature = id;
            var features = annotator.vectorLayer.features;
            var features_length = features.length;
            var feature, annotation;
            for (i = 0; i < features_length; i++) {
                feature = features[i];
                if (selectedFeature == feature.graph) {
                    annotator.selectedFeature = feature;
                    break;
                }
            }

            for (var idx in annotator.annotations) {
                annotation = annotator.annotations[idx];
                if (annotation.graph == feature.graph) {
                    break;
                }
            }
            return annotation;
        }
    };


    var select_annotation = function(annotation, select, callback) {

        if (typeof annotation === 'undefined') {
            return false;
        }

        var graph;
        var panel = $('.list-allographs[data-allograph="' + selectedAnnotations.allograph + '"]').parent();
        var temp = annotation;

        if (selectedAnnotations.annotations.length > 1) {
            self.dialog_instance.set_label(annotation.feature + " <span class='badge badge-important'>" + selectedAnnotations.annotations.length + "</span>");
        } else {
            self.dialog_instance.set_label(annotation.feature);
        }
        var switcher = $('#toggle-annotations-mode');
        var graphs = [];
        var checkboxes;
        for (var g = 0; g < selectedAnnotations.annotations.length; g++) {
            graphs.push(selectedAnnotations.annotations[g].graph);
        }

        if (!selectedAnnotations.annotations.length) {
            self.dialog_instance.hide();
            $('.select_annotation_checkbox').attr('checked', false);
            panel.find('.to_lightbox').attr('disabled', true);
        } else {
            if (switcher.bootstrapSwitch('state')) {
                self.dialog_instance.show();
            }
            panel.find('.to_lightbox').attr('disabled', false);
        }

        if (select) {
            load_annotations_allographs.init(annotation, function() {
                graph = allographs_cache.graphs[annotation.graph];
                checkboxes = self.dialog_instance.selector.find('.features_box');
                detect_common_features(graphs, checkboxes, allographs_cache);
                common_allographs(graphs, allographs_cache, graph);
                update_summary();
                events_on_labels();
                if (callback) {
                    callback();
                }
            });
            self.annotation_editor.set_graphids(get_graphs_from_annotations(selectedAnnotations.annotations));
            return false;
        } else {
            annotation = selectedAnnotations.annotations[selectedAnnotations.annotations.length - 1];
            if (typeof annotation !== 'undefined') {
                load_annotations_allographs.init(annotation, function() {
                    graph = allographs_cache.graphs[annotation.graph];
                    checkboxes = self.dialog_instance.selector.find('.features_box');
                    detect_common_features(graphs, checkboxes, allographs_cache);
                    common_allographs(graphs, allographs_cache, graph);
                    update_summary();
                    events_on_labels();
                    if (callback) {
                        callback();
                    }
                });
            } else {
                graphs_annotation = temp.graph;
                graph = allographs_cache.graphs[temp.graph];
                var element_value = $('li[data-graph="' + graphs_annotation + '"]').find('.label-default').text();
                $('.label-summary:contains(' + element_value + ')').remove();
                common_allographs(graphs, allographs_cache, graph);
                update_summary();
                events_on_labels();
                if (callback) {
                    callback();
                }
            }
            self.annotation_editor.set_graphids(get_graphs_from_annotations(selectedAnnotations.annotations));
        }

    };

    var utils = {

        clean_annotations: function(annotation, annotations) {
            var length_annotations = annotations.length;
            for (i = 0; i < length_annotations; i++) {
                if (annotations[i].vector_id == annotation.vector_id) {
                    annotations.splice(i, 1);
                    i--;
                    break;
                }
            }
        },

        style_select: function(select) {

            $(select).css({
                "float": "left",
                "margin": "0%",
                "margin-left": "3%",
                "margin-right": "3%",
                "margin-bottom": "3%",
                "margin-top": "2%"
            }).addClass('important_width');
        },

        anchorify: function(string) {
            return string.toLowerCase().replace(' ', '-');
        }

    };

    var load_annotations_allographs = {

        init: function(annotation, callback) {

            if (annotation) {

                var select_allograph = $('.myModal');

                if (selectedAnnotations.annotations.length > 1) {
                    self.dialog_instance.set_label(annotation.feature + " <span class='badge badge-important'>" + selectedAnnotations.annotations.length + "</span>");
                } else {
                    self.dialog_instance.set_label(annotation.feature);
                }

                select_allograph.find('.hand_form').val(annotation.hidden_hand);
                select_allograph.find('.allograph_form').val(annotation.hidden_allograph.split('::')[0]);

                $('#id_display_note').val(annotation.display_note).parent('p').hide();
                $('#id_internal_note').val(annotation.internal_note).parent('p').hide();

                var all_select = $('select');
                all_select.trigger('liszt:updated');

                this.get_features(annotation, function(s, aspects_list, string_summary) {
                    var myModal = $('.myModal');
                    var select_allograph = $('.myModal .allograph_form');
                    var summary = $('#summary');
                    var features_container = $('#features_container');
                    var aspects_container = $('#dialog_aspects');
                    var notes_container = $('#dialog_notes');
                    summary.html(string_summary);
                    features_container.html(s);
                    aspects_container.html(aspects_list);

                    setNotes(annotation, notes_container);

                    var check_all = $('.check_all');
                    var uncheck_all = $('.uncheck_all');
                    var set_by_default = $('.set_by_default');

                    var set_all_by_default = $('.set_all_by_default');
                    set_all_by_default.on('click', function(event) {
                        var components = [];
                        var allograph = $('.myModal .allograph_form').val();

                        for (var i in allographs_cache.allographs) {
                            for (var j = 0; j < allographs_cache.allographs[i].components.length; j++) {
                                var component = allographs_cache.allographs[i].components[j].id;
                                components.push(component);
                            }
                        }

                        for (var c in components) {
                            check_features_by_default(components[c], allograph, allographs_cache);
                        }

                        event.stopPropagation();
                    });
                    var prefix = 'allographs_';

                    check_all.on('click', function(event) {
                        var component = $(this).data('component');
                        var checkboxes = $('#' + prefix + 'component_' + component).find("input[type=checkbox]");
                        checkboxes.attr('checked', true);
                        event.stopPropagation();
                    });

                    uncheck_all.on('click', function(event) {
                        var component = $(this).data('component');
                        var checkboxes = $('#' + prefix + 'component_' + component).find("input[type=checkbox]");
                        checkboxes.attr('checked', false);
                        event.stopPropagation();
                    });

                    set_by_default.on('click', function(event) {
                        var component_id = $(this).data('component');
                        var allograph_id = select_allograph.val();
                        check_features_by_default(component_id, allograph_id, allographs_cache);
                        event.stopPropagation();
                    });

                    var deselect_all_graphs = $('.deselect_all_graphs');
                    deselect_all_graphs.click(function() {
                        $('.annotation_li.selected').removeClass('selected').data('selected', false);
                        selectedAnnotations.annotations = [];
                        self.dialog_instance.hide();
                    });

                    myModal.find('select').chosen();

                    myModal.find('.component_labels').click(function() {
                        var div = $("#" + $(this).data('id'));
                        if (!div.data('hidden')) {
                            $(this).next('.checkboxes_div').hide();
                            div.slideUp(500).data('hidden', true);
                            $(this).find('.arrow_component').removeClass('icon-arrow-up').addClass('icon-arrow-down');
                        } else {
                            div.slideDown().data('hidden', false);
                            $(this).next('.checkboxes_div').show();
                            $(this).find('.arrow_component').removeClass('icon-arrow-down').addClass('icon-arrow-up');
                        }
                    });

                    //updateFeatureSelect(annotation.features, feature);
                    $('#modal_features .close').click(function() {
                        $("#modal_features").fadeOut();
                        $('#status').html('-');
                        modal = false;
                        selectedAnnotations.allograph = null;
                        selectedAnnotations.annotations = [];
                        $('.to_lightbox').attr('disabled', true);
                        $('.annotation_li').removeClass('selected').data('selected', false);
                        $('.select_annotation_checkbox').attr('checked', false);
                    });

                    var select_list = $('select');
                    select_list.trigger('liszt:updated');

                    if (callback) {
                        callback();
                    }

                });
            } else {
                return false;
            }
        },

        get_features: function(annotation, callback) {
            var features = annotator.vectorLayer.features;
            var allograph = parseInt(annotation.hidden_allograph.split(':')[0], 10);
            var graph = annotation.graph;
            var image_id = annotator.image_id;
            var element = $('.annotation_li[data-graph="' + graph + '"]');

            // if there's no allograph cached, I make a full AJAX call
            if (!cache.search("allograph", allograph)) {
                load_group(element.closest('[data-group="true"]'), cache, false, function(data) {
                    var output = get_graph(graph, data, allographs_cache);
                    load_annotations_allographs.refresh(output, image_id, callback);
                });

                // else if allograph is cached, I only need the features, therefore I change the URL to omit allographs
            } else if (cache.search("allograph", allograph) && (!cache.search('graph', graph))) {

                load_group(element.closest('[data-group="true"]'), cache, true, function(data) {
                    var output = get_graph(graph, data, allographs_cache);
                    load_annotations_allographs.refresh(output, image_id, callback);
                });

                // otherwise I have both cached, I can get them from the cache object
            } else {
                var data = {};
                data['allographs'] = allographs_cache.allographs[allograph];
                data['features'] = allographs_cache.graphs[graph]['features'];
                data['allograph_id'] = allographs_cache.graphs[graph]['allograph_id'];
                data['graph_id'] = graph;
                data['hand_id'] = allographs_cache.graphs[graph]['hand_id'];
                data['hands'] = allographs_cache.graphs[graph]['hands'];
                load_annotations_allographs.refresh(data, image_id, callback);
            }

        },

        refresh: function(data, image_id, callback) {
            var allograph_id = data.id;
            var s = "<div id='box_features_container'>";

            var string_summary = '';
            var prefix = 'allographs_';
            var array_features_owned = features_saved(data['features']);
            var allographs = data['allographs'].components;
            var aspects_list = load_aspects(data['allographs'].aspects, data['graph_id'], allographs_cache);
            if (selectedAnnotations.annotations.length > 1) {
                var selected = [];

                for (var g = 0; g < selectedAnnotations.annotations.length; g++) {
                    selected.push(selectedAnnotations.annotations[g].graph);
                }
                allographs = common_components(selected, allographs_cache, allographs);
            }
            if (!allographs.length) {
                s += '<p class="component" style="margin:0;">No common components</p>';
                string_summary = "<span class='component_summary'>No componensts</span>";
            } else {
                $.each(allographs, function(idx) {
                    var component = allographs[idx].name;
                    var component_id = allographs[idx].id;
                    var is_empty;
                    var features = allographs[idx].features;
                    string_summary += "<span class='component_summary' data-component='" + component_id + "'>" + allographs[idx].name + "</span>";

                    s += "<div class='component_labels' data-id='" + prefix + "component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component icon-arrow-up'></span></b>";

                    s += "<div class='checkboxes_div btn-group'><span data-component = '" + component_id + "' class='check_all btn btn-xs btn-default'><i class='fa fa-check-square-o'></i></span> <span data-component = '" + component_id + "' class='uncheck_all btn btn-xs btn-default'><i class='fa fa-square-o'></i></span><span data-component = '" + component_id + "' title='Check by default' data-toggle='tooltip' data-container='body' class='set_by_default btn btn-xs btn-default'><i class='fa fa-plus-square'></i></span></div></div>";

                    s += "<div id='" + prefix + "component_" + component_id + "' data-hidden='false' class='feature_containers'>";
                    var n = 0;

                    $.each(features, function(idx) {
                        var value = component_id + '::' + features[idx].id;
                        var names = component + ':' + features[idx].name;
                        var f = selectedAnnotations.annotations;
                        var al = '';
                        var d = 0;
                        var title = '';
                        var ann;
                        for (var k = 0; k < f.length; k++) {
                            var graph = allographs_cache.graphs[f[k].graph];
                            var features_graph = graph.features;
                            for (var j = 0; j < features_graph.length; j++) {
                                if (features_graph[j].component_id == component_id && features_graph[j].feature.indexOf(features[idx].name) >= 0) {
                                    ann = $('div[data-graph="' + f[k].graph + '"]').find('.label');
                                    if (ann) {
                                        al += '<a href="#label_' + ann.data('graph-id') + '" data-graph-id="' + ann.data('graph-id') + '" class="label label-default label-summary">' + ann.text() + '</a> ';
                                        title += ann.text() + ' ';
                                    }
                                    d++;
                                    temporary_vectors.push(names);
                                }
                            }
                        }

                        var id = component_id + '_' + features[idx].id;

                        var array_features_owned_temporary = array_features_owned.concat(temporary_vectors);

                        s += "<div class='row row-no-margin'>";

                        if (array_features_owned.indexOf(names) >= 0) {

                            s += "<p class='col-md-2'><input checked = 'checked' type='checkbox' value='" + value + "' class='features_box' id='" + id + "' data-feature = '" + features[idx].id + "' /></p>";
                            s += "<p class='col-md-10'><label class='string_summary_label' for='" + id + "'>" + features[idx].name + "</label></p>";

                        } else {
                            s += "<p class='col-md-2'><input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "'/></p>";
                            s += "<p class='col-md-10'><label class='string_summary_label' for='" + id + "'>" + features[idx].name + "</label></p>";
                        }

                        if (array_features_owned_temporary.indexOf(names) >= 0) {
                            string_summary += "<span data-component='" + component_id + "' title='" + features[idx].name + "' data-feature = '" + features[idx].id + "' class='feature_summary'>" + features[idx].name + ' ' + al + "</span>";
                            n++;
                        }

                        s += "</div>";
                    });

                    s += "</div>";
                    if (!n) {
                        string_summary += "<span class='feature_summary' data-feature = '0' data-component='" + component_id + "'>undefined</span>";
                    }
                });
            }


            if (callback) {
                callback(s, aspects_list, string_summary);
            }
        }

    };

    var refresh = function() {
        var allographs_container = $('#allographs');
        var img = $("<img id='allographs_tab_loader' src='/static/digipal/images/ajax-loader4.gif' />");
        self.dialog_instance.hide();
        var cached_dialog = $(".myModal#modal_features");
        var request = $.ajax({
            url: annotator.absolute_image_url + 'image_allographs/',
            type: 'GET',

            beforeSend: function() {
                allographs_container.html(img);
            },

            success: function(output) {
                allographs_container.html(output);
            },
            complete: function() {

                img.fadeOut().remove();
                annotator.has_changed = false;

                $('[data-toggle="tooltip"]').tooltip({
                    container: 'body'
                });

                self.dialog_instance.selector = cached_dialog;
                selectedAnnotations.annotations = [];
                init();

            }
        });
    };


    var events_on_labels = function() {

        $('.label-summary').unbind().on('mouseover', function() {
            var graph = $(this).data('graph-id');
            $('#label_' + graph).closest('.annotation_li').addClass('hovered_allograph');
        }).on('mouseout', function() {
            var graph = $(this).data('graph-id');
            $('#label_' + graph).closest('.annotation_li').removeClass('hovered_allograph');
        });
    };


    var update_summary = function() {
        var summary = $('#summary');
        $('.features_box').on('change', function() {
            var id = $(this).attr('id');
            var component_id = $(this).val().split('::')[0];
            var feature_id = $(this).val().split('::')[1];
            var feature = $("label[for='" + id + "']").text();
            if ($(this).is(':checked') && !$(this).prop('indeterminate')) {

                var selected = '';
                for (var i = 0; i < selectedAnnotations.annotations.length; i++) {
                    var graph = selectedAnnotations.annotations[i].graph;
                    var label_number = $('.label[data-graph-id="' + graph + '"]');
                    selected += ' <a href="#label_' + graph + '" data-graph-id="' + graph + '" class="label label-default label-summary">' + label_number.html() + '</a>';
                }

                var html_feature_string = "<span data-feature='" + feature_id + "' data-component='" + component_id + "' class='feature_summary'>" + feature + selected + "</span>";

                summary.find('.feature_summary[data-component="' + component_id + '"]').last().after(html_feature_string);
                summary.find('.feature_summary[data-component="' + component_id + '"][data-feature=0]').remove();
            } else {
                summary.find('.feature_summary[data-component="' + component_id + '"][data-feature="' + feature_id + '"]').remove();
                if (!summary.find('.feature_summary[data-component="' + component_id + '"]').length) {
                    var undefined_feature_string = "<span data-feature='0' data-component='" + component_id + "' class='feature_summary'>undefined</span>";
                    summary.find('.component_summary[data-component="' + component_id + '"]').after(undefined_feature_string);
                }
            }
            events_on_labels();
        });
    };


    var keyboard_shortcuts = {
        init: function() {
            $(document).on('keydown', function(event) {
                var code = (event.keyCode ? event.keyCode : event.which);
                if (event.ctrlKey) {
                    var currentTab = $('.tab-pane.active'),
                        tab;
                    if (code == 37) { // left
                        var prevTab;
                        if (!currentTab.prev().length) {
                            return false;
                        } else {
                            prevTab = currentTab.prev();
                            tab = $('a[data-target="#' + prevTab.attr('id') + '"]');
                            tab.tab('show');
                        }
                    }
                    if (code == 39) { // right
                        var nextTab;
                        if (!currentTab.next().length) {
                            return false;
                        } else {
                            nextTab = currentTab.next();
                            tab = $('a[data-target="#' + nextTab.attr('id') + '"]');
                            tab.tab('show');
                        }
                    }
                }
            });
        }
    };

    return {
        'init': init,
        'refresh': refresh,
        'cache': cache
    };

}


var allographs_cache = new AnnotationsCache();
var allographs_dialog = new Dialog();
var allographsPage = new Allographs(allographs_dialog, allographs_cache);
allographsPage.init();
