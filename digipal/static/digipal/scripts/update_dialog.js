/**
 * function to update the dialog
   -- Digipal Project --> digipal.eu
 */

/**
 * The function update_dialog() allows to update the current content of the a dialog.
 * It requires two parameters:
 *	@prefix: a prefix for unifying DOM elements, can be an empty string
 *	@data: an array which contains two objects: allographs and features: this array has to be obtained
 *		from the function get_features() in annotation.py
 */



var api = new DigipalAPI({
    crossDomain: false,
    root: '/digipal/api'
});

var local_cache = {};

function update_dialog(prefix, data, selectedAnnotations, callback, cache) {

    if (typeof annotator !== 'undefined' && annotator.selectedFeature !== 'undefined' && annotator.selectedFeature && annotator.selectedFeature.isTemporary) {
        callback('');
    }

    var s = '<div id="box_features_container">';
    var array_features_owned = features_saved(data.features);
    var allographs = data.allographs.components;
    var string_summary = "";
    if (!allographs.length) {
        s += '<p class="component" style="margin:0;">No common components</p>';
        string_summary = "<span class='component_summary'>No componensts</span>";
    } else {

        $.each(allographs, function(idx) {
            component = allographs[idx].name;
            component_id = allographs[idx].id;
            var features = allographs[idx].features;
            s += "<div class='component_labels' data-id='" + prefix + "component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component fa fa-angle-double-down'></span></b>";

            s += "<div class='checkboxes_div btn-group'><span data-toggle='tooltip' data-container='body'  title='Check all' data-component = '" + component_id + "' class='check_all btn btn-xs btn-default'><i class='fa fa-check-square-o'></i></span> <span title='Unheck all' data-toggle='tooltip' data-container='body' data-component = '" + component_id + "' class='uncheck_all btn btn-xs btn-default'><i class='fa fa-square-o'></i></span><span data-component = '" + component_id + "' title='Check by default' data-toggle='tooltip' data-container='body' class='set_by_default btn btn-xs btn-default'><i class='fa fa-plus-square'></i></span></div></div>";

            s += "<div id='" + prefix + "component_" + component_id + "' data-hidden='false' class='feature_containers'>";
            string_summary += "<span class='component_summary' data-component='" + component_id + "'>" + allographs[idx].name + "</span>";
            var n = 0;
            $.each(features, function(idx) {
                var value = component_id + '::' + features[idx].id;
                var id = component_id + '_' + features[idx].id;
                var names = component + ':' + features[idx].name;
                s += '<div class="row row-no-margin">';

                if (cache) {
                    var f = selectedAnnotations;
                    var al = '';
                    var d = 0;
                    var temporary_vectors = [];
                    var title = '';
                    var ann;
                    for (var k = 0; k < f.length; k++) {
                        var graph = cache.graphs[f[k]];
                        var features_graph = graph.features;
                        for (var j = 0; j < features_graph.length; j++) {
                            if (features_graph[j].component_id == component_id && features_graph[j].feature.indexOf(features[idx].name) >= 0) {
                                d++;
                                temporary_vectors.push(names);
                            }
                        }
                    }

                    var array_features_owned_temporary = array_features_owned.concat(temporary_vectors);

                    if (array_features_owned_temporary.indexOf(names) >= 0) {
                        string_summary += "<span data-component='" + component_id + "' title='" + features[idx].name + "' data-feature = '" + features[idx].id + "' class='feature_summary'>" + features[idx].name + ' ' + al + "</span>";
                        n++;
                    }
                }

                if (typeof annotator !== 'undefined') {
                    if (typeof annotator.selectedFeature !== "undefined" && annotator.selectedFeature !== null && annotator.selectedFeature.state == 'Insert') {
                        array_features_owned = annotator.selectedFeature.features;
                        names = value;
                    }
                    if (array_features_owned.indexOf(names) >= 0) {
                        s += "<p class='col-md-2'><input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "' checked /> ";
                    } else {
                        s += "<p class='col-md-2'><input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "' /> ";
                    }
                    s += "<p class='col-md-10'><label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + id + "'>" + features[idx].name + "</label></p>";
                } else {
                    if (array_features_owned.indexOf(names) >= 0) {
                        s += "<p class='col-md-2'> <input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "' checked />";
                    } else {
                        s += "<p class='col-md-2'> <input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "'/>";
                    }

                    s += "<p class='col-md-10'><label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + id + "'>" + features[idx].name + "</label></p>";
                }

                s += '</div>';
            });
            if (!n) {
                string_summary += "<span class='feature_summary' data-feature = '0' data-component='" + component_id + "'>undefined</span>";
            }
            s += "</div>";
        });
    }

    s += "</div>";
    if (callback) {
        callback(s, string_summary);
    }
}

/*

Function to get the features of a described allograph
@params feature selected, url
*/

function features_saved(features) {
    var array_features_owned = [];
    if (features && features.length) {
        for (var i = 0; i < features.length; i++) {
            for (var j = 0; j < features[i].feature.length; j++) {
                s = features[i].name;
                s += ':' + features[i].feature[j];
                array_features_owned.push(s);
            }
            s = '';
        }
    }
    return array_features_owned;
}


var load_group = function(group_element, cache, only_features, callback) {

    if (!$('#allographs_loader_gif').length) {
        $('.myModalLabel .deselect_all_graphs').after(" <img id='allographs_loader_gif' src='/static/digipal/images/ajax-loader3.gif' />");
    }

    var graphs, graph, url, graphs_list = [];
    var content_type = 'graph';
    graphs = group_element.find('[data-graph]');
    $.each(graphs, function() {
        graph = $(this).data('graph');
        if (!cache.search('graph', graph)) {
            graphs_list.push(graph);
        }
    });
    reload_cache(graphs_list, cache, only_features, callback);
    $("#allographs_loader_gif").remove();

};

var reload_cache = function(graphs, cache, only_features, callback) {

    var url, content_type = 'graph';
    $('#features_container').html('<img style="position:absolute;top:40%;left:40%;" src="/static/digipal/images/ajax-loader4.gif" />');
    if (graphs.length) {
        url = 'old/' + content_type + '/' + graphs.toString() + '/';

        if (only_features) {
            url += 'features';
        }

        if (local_cache[url]) return local_cache[url];

        api.request(url, function(data) {
            for (var i = 0; i < data.length; i++) {
                var graph = data[i].graph;
                var allograph = data[i].allograph_id;

                if (!cache.search("allograph", allograph) && !only_features) {
                    cache.update('allograph', allograph, data[i]);
                }

                if (!cache.search("graph", graph)) {
                    cache.update('graph', graph, data[i]);
                }
            }

            local_cache[url] = data;

            if (callback) {
                callback(data);
            }
        });

    } else {
        if (callback) {
            callback();
        }
    }
};

var get_graph = function(graph_id, data, cache) {

    var result = {};
    var graphs = cache.graphs;

    var graph = cache.graphs[graph_id];
    result['allographs'] = cache.allographs[graph.allograph_id];
    result['features'] = graph['features'];
    result['allograph_id'] = graph.allograph_id;
    result['graph_id'] = graph_id;
    result['hand_id'] = graph['hand_id'];
    result['hands'] = graph['hands'];
    result['aspects'] = graph['aspects'];
    result['item_part'] = graph['item_part'];
    return result;

};


function intersect(a, b) {
    var intersection = [].concat(a);
    var temp = [];

    for (var i = 0; i < b.length; i++) {
        if (intersection.indexOf(b[i]) < 0) {
            temp.push(b[i]);
        }
    }

    for (i = 0; i < intersection.length; i++) {
        if (b.indexOf(intersection[i]) < 0) {
            temp.push(intersection[i]);
        }
    }

    for (i = 0; i < intersection.length; i++) {
        for (var g = 0; g < temp.length; g++) {
            if (temp[g] == intersection[i]) {
                intersection.splice(i, 1);
                i--;
            }
        }
    }

    return intersection;
}

function common_allographs(selectedAnnotations, cacheAnn, graph) {
    // Reset allograph and hand <select>s
    // so that their current value is a common allograph/hand among all
    // selected annotations.
    // If nothing in common, select ---- .
	
    var allographs = [],
        hands = [],
        item_parts = [];

    var cache = $.extend(true, {}, cacheAnn);
    var select_hand = $('.myModal .hand_form');
    var select_allograph = $('.myModal .allograph_form');

    for (var j = 0; j < selectedAnnotations.length; j++) {
        var allograph_id = cache.graphs[selectedAnnotations[j]].allograph_id;
        var hand_id = cache.graphs[selectedAnnotations[j]].hand_id;
        var item_part = cache.graphs[selectedAnnotations[j]].item_part;
        allographs.push(allograph_id);
        hands.push(hand_id);
        item_parts.push(item_part);
    }

	// Set flag_X = 0 if more than one X associated to the selected annotations 
    var flag_allograph = 1,
        flag_hand = 1,
        flag_ip = 1;

    for (var h = 1; h < allographs.length; h++) {
        if (allographs[0] != allographs[h]) {
            flag_allograph = 0;
            break;
        }
    }

    for (h = 1; h < hands.length; h++) {
        if (hands[0] != hands[h]) {
            flag_hand = 0;
            break;
        }
    }

    for (h = 1; h < item_parts.length; h++) {
        if (item_parts[0] != item_parts[h]) {
            flag_ip = 0;
            break;
        }
    }

	// Change <select> to common allograph (if single one) 
    if (!flag_allograph) {
        select_allograph.val('------');
    } else {
        select_allograph.val(graph.allograph_id);
    }

	// Change <hand> to common hand (if single one) 
    if (!flag_hand && flag_ip) {
        select_hand.text('------');
        select_hand.val('');
    } else if (!flag_hand && !flag_ip) {
        select_hand.html('<option selected value>------</option>');
    } else {
        select_hand.val(graph.hand_id);
    }

    select_hand.add(select_allograph).trigger('liszt:updated');
}

function common_components(selectedAnnotations, _cacheAnnotations, data, type) {

    if (!data) {
        return false;
    }

    var cacheAnnotations = $.extend(true, {}, _cacheAnnotations);

    if (typeof type == 'undefined' || !type) {
        type = "components";
    }

    var allograph_id, allograph, allographs, allograph_names = [],
        cacheAnn = [];

    var ind = 0;
    while (ind < selectedAnnotations.length) {
        if (typeof cacheAnnotations.graphs[selectedAnnotations[ind]] !== 'undefined') {
            allograph_id = cacheAnnotations.graphs[selectedAnnotations[ind]].allograph_id;
            allographs = $.extend(true, {}, cacheAnnotations.allographs[allograph_id][type]);
            cacheAnn.push(allographs);
        }
        ind++;
    }

    var copy_data = data.slice(0);
    var n = 0;
    var arrays = [];

    for (var i in cacheAnn) {
        var array = [];
        if ($.isEmptyObject(cacheAnn[i])) {
            copy_data = [];
            return copy_data;
        }

        for (var a in cacheAnn[i]) {
            all = cacheAnn[i][a].name;
            array.push(all);
        }

        arrays.push(array);
        n++;
    }

    var ints = arrays[0],
        intersection;
    for (var h = 0; h < arrays.length - 1; h++) {
        intersection = intersect(ints, arrays[h + 1]);
        ints = intersection;
    }

    for (var k = 0; k < copy_data.length; k++) {
        if (intersection.indexOf(copy_data[k].name) < 0) {
            copy_data.splice(k, 1);
            k--;
        }
    }

    return copy_data;
}

function preprocess_features(graphs, _cache, type) {
    var graph, all = [],
        features, component_id;

    var cache = $.extend(true, {}, _cache);
    if (!type) {
        type = 'features';
    }
    for (var i = 0; i < graphs.length; i++) {
        graph_id = graphs[i];
        graph = cache.graphs[graph_id];
        features = graph[type];

        obj = {
            graph: graph_id
        };

        for (var d = 0; d < features.length; d++) {
            if (type == 'features') {
                component_id = features[d].component_id;
            } else {
                component_id = features[d].id;
            }
            if (!obj.hasOwnProperty(component_id)) {
                obj[component_id] = {};
                obj[component_id][type] = [];
            }
            var f;
            if (type == 'features') {
                f = features[d].feature[0];
            } else {
                f = features[d].name;
            }
            obj[component_id][type].push(f);
        }
        all.push(obj);
    }
    return all;
}

function compute_features(graphs, checkboxes, type) {
    var iterations;

    var ticked = [],
        unticked = [],
        indeterminate = [];

    var graph, graph_next, parent;
    if (type == 'features' || !type) {
        type = 'features';
        parent = checkboxes.closest('#box_features_container').parent();
    } else {
        parent = $('#notes_tab').parent();
    }
    $.each(checkboxes, function() {
        var checkbox = $(this);
        var label = parent.find('label[for="' + checkbox.attr('id') + '"]');
        var val = label.text();
        var component = checkbox.val().split(':')[0];

        if (graphs.length > 1) {
            iterations = graphs.length - 1;
        } else {
            iterations = 1;
        }
        for (var i = 0; i < iterations; i++) {

            if (graphs.length > 1) {
                if (graphs[i].hasOwnProperty(component)) {
                    graph = graphs[i][component][type];
                } else {
                    graph = [];
                }

                if (graphs[i + 1].hasOwnProperty(component)) {
                    graph_next = graphs[i + 1][component][type];
                } else {
                    graph_next = [];
                }

                if (graph.indexOf(val) >= 0 && graph_next.indexOf(val) < 0 || graph.indexOf(val) < 0 && graph_next.indexOf(val) >= 0) {
                    indeterminate.push(checkbox.attr('id'));
                } else if (graph.indexOf(val) >= 0 && graph_next.indexOf(val) >= 0) {
                    checkbox.prop('checked', true);
                    checkbox.prop('indeterminate', false);
                    ticked.push(val);
                } else {
                    checkbox.prop('checked', false);
                    checkbox.prop('indeterminate', false);
                    unticked.push(val);
                }

            } else if (graphs.length == 1) {
                if (!graphs[0].hasOwnProperty(component) || typeof graphs[0][component][type] == 'undefined') {
                    graph = [];
                } else {
                    graph = graphs[0][component][type];
                }

                if (graph.indexOf(val) >= 0) {
                    checkbox.prop('checked', true);
                } else {
                    checkbox.prop('checked', false);
                }

                checkbox.prop('indeterminate', false);
            } else {
                return false;
            }
        }

    });

    for (ind = 0; ind < indeterminate.length; ind++) {
        parent.find('#' + indeterminate[ind]).prop('indeterminate', true);
    }

}

function detect_common_features(selectedAnnotations, checkboxes, _cache) {
    var cache = $.extend(true, {}, _cache);
    var features_preprocessed = preprocess_features(selectedAnnotations, cache);
    compute_features(features_preprocessed, checkboxes);
    var aspects_processed = preprocess_features(selectedAnnotations, cache, "aspects");
    var aspects_checkbox = $('.aspect');
    compute_features(aspects_processed, aspects_checkbox, "aspects");
    checkboxes.add(aspects_checkbox).unbind().on('change', function() {
        var state = $(this).data('state');
        if (!state) {
            state = 1;
            $(this).data('state', state);
        } else if (state < 2) {
            state += 1;
            $(this).data('state', state);
        } else if (state === 2) {
            $(this).prop('indeterminate', true);
            state = 0;
            $(this).data('state', state);
        }
    });
}

function check_features_by_default(component_id, allograph_id, cache) {
    var allograph = cache.allographs[allograph_id];
    var components = allograph.components;
    for (var component in components) {
        if (components[component].hasOwnProperty('default') && components[component].
            default.length) {
            for (var i = 0; i < components[component].
                default.length; i++) {
                var default_feature = components[component].
                default [i].component + '::' + components[component].
                default [i].feature;
                var checkbox_val = $('input[value="' + default_feature + '"]');
                if (checkbox_val.length && checkbox_val.val().split('::')[0] == component_id) {
                    checkbox_val.prop('checked', true);
                }
            }
        }
    }
}

function updateStatus(msg, status) {
    var running = running || true;

    if (typeof status == 'undefined') {
        status = 'warning';
    }

    if (running) {
        clearInterval(timeout);
        $('#status').remove();
    }

    var status_element = $('#status');

    if (!status_element.length) {
        status_element = $('<div id="status">');
        $('body').append(status_element.hide());
    }

    status_element.css('z-index', 5000);
    status_class = status ? ' alert-' + status : '';
    status_element.attr('class', 'alert' + status_class);

    status_element.html(msg).fadeIn();

    var timeout =
        setTimeout(function() {
            status_element.fadeOut();
            running = false;
        }, 5000);
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


function load_aspects(aspects, graph, _cache) {
    var aspects_list = "";
    var graph_aspects = null;

    var cache = $.extend(true, {}, _cache);
    if (cache.graphs.hasOwnProperty(graph)) {
        if (cache.graphs[graph].hasOwnProperty('aspects')) {
            graph_aspects = cache.graphs[graph].aspects;
        }
    }

    if (aspects.length) {
        for (var i = 0; i < aspects.length; i++) {
            var checked = "";
            if (typeof graph_aspects !== "undefined" && graph_aspects) {
                for (var j = 0; j < graph_aspects.length; j++) {
                    if (graph_aspects[j].id == aspects[i].id) {
                        checked = "checked";
                        break;
                    }
                }
            }
            aspects_list += "<div class='component_labels'><input " + checked + " data-checked='" + checked + "'  class='aspect' id='" + aspects[i].id + "' type='checkbox' value='" + aspects[i].id + "' /> <label for='" + aspects[i].id + "'>" + aspects[i].name + "</label></div>";
            aspects_list += "<div class='feature_containers'>";
            for (var j = 0; j < aspects[i].features.length; j++) {
                aspects_list += "<p class='feature'>- " + aspects[i].features[j].name + "</p>";
            }
            aspects_list += "</div>";
        }
    } else {
        aspects_list += "<p class='component'>No common aspects (or not defined)</p>";
    }
    return aspects_list;
}

// Intialise a div to write an note about an annotation
// The div is turned into a textarea/wysiwyg
// Any change by the user will be saved into the selected feature in the annotator
// note_key is the name of the property to be saved on the feature object
function init_note_field($field, annotator, note_key, placeholder) {

    $field = $($field);

    // set up the wysiwyg on the field
    $field.notebook({
        placeholder: placeholder || 'Type description here...'
    });
    
    // set the value from the selected feature
    if (annotator && annotator.selectedFeature) {
        $field.html(annotator.selectedFeature[note_key] || '');
    }
    
    // copy any change to the selected feature
    //$field.on('contentChange keyup', function(e) {
    $field.on('contentChange', function(e) {
        if (e.originalEvent && e.originalEvent.detail && e.originalEvent.detail.content) {
            annotator.selectedFeature[note_key] = e.originalEvent.detail.content;
            remove_url_div();
        }
    });
    
    return $field;
    
}

function remove_url_div() {
    if ($('.allograph_url_div').length) {
        $('.allograph_url_div').remove();
    }
    $('.tooltip').remove();
    $('.url_allograph').data('hidden', true);
}

function setNotes(selectedFeature, dialog) {
    var display_note = $('<div>');
    display_note.attr('id', 'id_display_note').attr('name', 'display_note').addClass('form-control');

    var internal_note = $('<div>');
    internal_note.attr('id', 'id_internal_note').attr('name', 'internal_note').addClass('form-control');

    display_note.notebook().html(selectedFeature.display_note);
    display_note.on('keyup', function() {
        selectedFeature.display_note = $(this).html();
        remove_url_div();
    }).on('contentChange', function() {
        selectedFeature.display_note = $(this).html();
        remove_url_div();
    });

    internal_note.notebook().html(selectedFeature.internal_note);
    internal_note.on('keyup', function() {
        selectedFeature.internal_note = $(this).html();
        remove_url_div();
    }).on('contentChange', function() {
        selectedFeature.internal_note = $(this).html();
        remove_url_div();
    });

    var notes = "";
    notes += "<p id='label_display_note' class='component_labels' data-id='id_display_note' data-hidden='false'><b>Public Note</b></p>";
    notes += "<p id='label_internal_note' class='component_labels' data-id='id_internal_note' data-hidden='false'><b>Internal Note</b></p>";

    dialog.html(notes);

    $('#label_display_note').after(display_note);
    $('#label_internal_note').after(internal_note);
}


function isNodeEmpty(node) {
    var self_closed = ["AREA", "BR", "COL", "EMBED", "HR", "IMG", "INPUT", "LINK", "META", "PARAM"];
    if (node) {
        var string = $.parseHTML(node);
        var emptyNodes = 0;
        var value;
        for (var i = 0; i < string.length; i++) {
            if (string[i].nodeName == '#text') {
                value = string[i].nodeValue;
            } else {
                value = string[i].innerText;
            }
            if (($.trim(value) === '' || $.trim(value) == 'Type display note here...' || $.trim(value) == 'Type internal note here...') && self_closed.indexOf(string[i].nodeName) < 0) {
                emptyNodes++;
            }
        }
        return emptyNodes === string.length;
    }
}
