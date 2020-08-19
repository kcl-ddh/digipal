(function() {
    var csrftoken = window.getCookie('csrftoken');
    $.ajaxSetup({
        headers: {
            "X-CSRFToken": csrftoken
        }
    });

    $('#sort-select').bootstrapSelect({
        label: "Group By"
    });


    var cache = {};

    var selectedItems = [];

    var editorialCache = {};

    var collection;

    var sum_images_collection = function(basket) {
        var n = 0;
        if (basket.annotations) {
            n += basket.annotations.length;
        }

        if (basket.images) {
            n += basket.images.length;
        }
        return n;
    };

    var selectedAnnotations = function() {
        var checkboxes = $('.checkbox_image');
        var graphs = {};
        var n = 0;
        $.each(checkboxes, function() {
            if ($(this).is(':checked')) {
                graphs[$(this).data('graph')] = $(this).data('type');
                n++;
            }
        });
        return {
            'graphs': graphs,
            'graphs_number': n
        };
    };

    function update_counter() {
        $.each(window.collection_types, function(type, info) {
            var check_all = $('#check_'+info.group+'_all');

            var count = $('.checkbox_image[data-type='+ type +']:checked').length;

            $('#counter-'+info.group).html(count);

            if (count < 1) {
                check_all.prop('checked', false).prop('indeterminate', false);
            } else if ($('#table-'+ info.group +' .table-row').length == count) {
                check_all.prop('checked', true).prop('indeterminate', false);
            } else {
                check_all.prop('indeterminate', true);
            }

            $('#to_lightbox,#remove_from_collection').attr('disabled', !selectedItems.length);

            $("#header_"+info.group).add($("#"+info.group+"-grid h2")).html(info.label+"s (" + $('#table-'+info.group).find('tr[data-graph]').length + ")");
        });
    }

    var changeNumbers = function() {
        var tbody = $("tbody");
        tbody.find('tr').each(function() {
            $(this).find('.num_row').text('#' + $(this).index());
        });
    };

    function main(callback) {

        var element_basket = $('#collection_link');
        var container_basket = $('#container_basket');
        var collection_name, data = {};
        var isExternal = false;

        if (!getParameter('collection').length) {
            var collections = JSON.parse(localStorage.getItem('collections'));
            var url = location.href;
            var collection_name_from_url = decodeURIComponent(url.split('/')[url.split('/').length - 2]);
            var selectedCollection = localStorage.getItem('selectedCollection');

            $.each(collections, function(index, value) {
                if (index.replace(/\s+/gi, '').toLowerCase() == collection_name_from_url.toLowerCase()) {
                    collection = value;
                    collection_name = index;
                }
            });

            if (!collection) {
                location.href = "../";
            }

            $.each(window.collection_types, function(k, type_info) {
                var tname = type_info.group;
                if (typeof collection[tname] !== 'undefined' && collection[tname].length) {
                    data[tname] = [];
                    for (d = 0; d < collection[tname].length; d++) {
                        var v = collection[tname][d];
                        if (tname == 'images') {
                            if (typeof v != 'number') v = v.id;
                            v = parseInt(collection.images[d], 10);
                        }
                        data[tname].push(v);
                    }
                }
            });

        } else {
            /*
        var external_collection = JSON.parse(getParameter('collection'));
        data = external_collection;
        collection_name = data['name'];
        collection = data;
        isExternal = true;
        */

            // GN: hack here to unescape the param, although it should already have been unescaped in GetParam
            // so I imagine the param has been escaped twice before...
            var collection_param = getParameter('collection');
            if (collection_param.length) {
                collection_param = collection_param[0];
                if (collection_param.lastIndexOf('%', 0) === 0) {
                    collection_param = unescape(collection_param);
                }
                var external_collection = JSON.parse(collection_param);

                data = external_collection;
                collection_name = data['name'];
                collection = data;
                isExternal = true;
            }

        }

        var header = $('.page-header');
        header.find('.collection-title').html(collection_name);
        $('#breadcrumb-current-collection').html(collection_name);
        var length_basket = length_basket_elements(collection) || 0;
        $('#delete-collection').attr('data-original-title', 'Delete ' + collection_name);
        $('#share-collection').attr('data-original-title', 'Share ' + collection_name);
        
        if (!window.digipal_settings.ARCHETYPE_GOOGLE_SHORTENER_CLIENTID) {
            $('#share-collection').hide();
        }
        
        var url_request = '/digipal/collection/' + collection_name.replace(/\s*/gi, '') + '/images/';
        if (!$.isEmptyObject(data)) {

            var request = $.ajax({
                type: 'GET',
                url: url_request,
                contentType: 'application/json',
                data: {
                    'data': JSON.stringify(data)
                },
                success: function(data) {
                    var attrs = {
                        "isExternal": isExternal,
                        "reverse": true
                    };
                    displayTable(data, attrs);

                    displayGrid(data, {
                        'sorting': "no-group"
                    });

                    makeSortable();

                    if (callback) {
                        callback();
                    }

                },

                complete: function(data) {
                    var loading_div = $(".loading-div");
                    if (loading_div.length) {
                        loading_div.fadeOut().remove();
                    }


                    $('#save-collection').unbind().click(function() {
                        var id = save_collection(collection);
                        history.pushState(null, null, '../' + encodeURIComponent(collection.name));
                        $('#alert-save-collection').fadeOut().remove();
                        notify('Collection saved', 'success');
                        localStorage.setItem('selectedCollection', id);
                        update_collection_counter();
                    });
                },

                error: function() {

                    var s = '<div class="container alert alert-warning">Something has gone wrong. Please refresh the page and try again.</div>';
                    container_basket.html(s);

                    var loading_div = $(".loading-div");
                    if (loading_div.length) {
                        loading_div.fadeOut().remove();
                    }
                }
            });

        } else {
            s = '<div class="container alert alert-warning"><p>The collection is empty.</p>';
            s += '<p>Start adding images from <a href="/digipal/page/">Browse Images</a> or using the <a href="/digipal/search/facets/?&result_type=images&img_is_public=1&view=grid">search page</a></div>';

            container_basket.html(s);

            var loading_div = $(".loading-div");
            if (loading_div.length) {
                loading_div.fadeOut().remove();
            }
        }

        $('[data-toggle="tooltip"]').tooltip();

        header.find('.collection-title').on('blur', function() {
            if (!$(this).data('active')) {
                $(this).data('active', true);
                var collections = JSON.parse(localStorage.getItem('collections'));
                var name = $.trim($(this).text()),
                    flag = false;

                $.each(collections, function(index, value) {
                    if (name == index) {
                        flag = false;
                        return false;
                    } else {
                        if (value.id == selectedCollection) {
                            //name = name.replace(/\s+/gi, '');
                            if (name) {
                                collections[name] = collections[index];
                                delete collections[index];
                                basket = value;
                                history.pushState(null, null, '../../' + encodeURIComponent(name));
                                flag = true;
                                return false;
                            } else {
                                notify("Please provide a valid name", 'danger');
                                $('.collection-title').html(index);
                                return false;
                            }
                        }
                    }
                });

                if (flag) {
                    localStorage.setItem('collections', JSON.stringify(collections));
                    element_basket.html(name + ' (' + sum_images_collection(basket) + ' <i class="fa fa-picture-o"></i> )');
                    element_basket.attr('href', '/digipal/collection/' + name.replace(/\s+/gi), '');
                    $('#breadcrumb-current-collection').html(name);
                    notify("Collection renamed as " + name, 'success');
                } else {
                    return false;
                }
            }
        }).on('focus', function(event) {
            $(this).on('keyup', function(event) {
                var code = (event.keyCode ? event.keyCode : event.which);
                if (code == 13) {
                    $(this).blur();
                    event.preventDefault();
                    return false;
                }
            }).on('keydown', function(event) {
                var code = (event.keyCode ? event.keyCode : event.which);
                if (code == 13) {
                    $(this).blur();
                    event.preventDefault();
                    return false;
                }
            }).data('active', false);
        });

        $('#share-collection').on('click', function() {
            share([collection['id']]);
        });

        $('#delete-collection').on('click', function() {
            delete_collections([collection['id']], false, true);
        });
    }

    function sort(property, reverse, type) {
        property = parseInt(property, 10);
        var copy_cache = $.extend({}, cache);

        copy_cache[type].sort(function(x, y) {
            return x[property] == y[property] ? 0 : (x[property] < y[property] ? -1 : 1);
        });

        if (reverse) {
            copy_cache[type].reverse();
        }

        var attrs = {
            "isExternal": false,
            "reverse": reverse
        };

        displayTable(copy_cache, attrs);
    }

    function displayTable(data, attrs) {
        var container_basket = $('#container_basket');
        var isExternal = attrs.isExternal;
        var reverse = attrs.reverse;
        var s = '';

        if (data.annotations && data.annotations.length) {
            if (cache && !cache.annotations) {
                cache.annotations = data.annotations;
            }
            s += "<h3 id='header_annotations'>Graphs (" + data.annotations.length + ")</h3>";
            s += "<table id='table-annotations' class='table'>";
            s += '<th><input data-toggle="tooltip" title="Toggle all" type="checkbox" id="check_annotations_all" /> <label id="counter-annotations" for="check_annotations_all"></label></th><th>Graph</th><th data-sort="14" data-reverse="' + reverse + '">Manuscript</th><th data-sort="11" data-reverse="' + reverse + '">Allograph</td><th data-sort="3" data-reverse="' + reverse + '">Hand</th><th data-sort="4" data-reverse="' + reverse + '">Scribe</th><th data-sort="5" data-reverse="' + reverse + '">Place</th>';
            for (var i = 0; i < data.annotations.length; i++) {
                var annotation = data.annotations[i];
                s += "<tr class='table-row' data-graph = '" + annotation[1] + "'><td class='col-md-1'><input data-toggle='tooltip' title='Toggle item' data-graph = '" + annotation[1] + "' type='checkbox' data-type='annotation' class='checkbox_image' aria-label='Graph #"+(i+1)+"' /> <span class='num_row'># " + (i + 1) + "</span>  </td><td data-graph = '" + annotation[1] + "'><a title='View graph in the manuscript viewer' href='/digipal/page/" + annotation[8] + "/?graph=" + annotation[1] + "'>" + annotation[0] + "</a>";
                s += "</td>";

                s += "<td data-graph = '" + annotation[1] + "'><a data-toggle='tooltip' title='Go to manuscript page' href='/digipal/page/" + annotation[8] + "'>" + annotation[14] + "</a>";
                s += "</td>";

                s += "<td><a data-toggle='tooltip' title='Go to " + annotation[11] + "' href='/digipal/search/graph/?character_select=" + annotation[13] + "&allograph_select=" + annotation[12] + "'>" + annotation[11] + "</a></td>";

                if (annotation[3] !== null && annotation[3] != 'Unknown') {
                    s += "<td><a data-toggle='tooltip' title='Go to Hand' href='/digipal/hands/" + annotation[9] + "'>" + annotation[3] + "</a></td>";
                } else {
                    s += "<td>Unknown</td>";
                }


                if (annotation[4] !== null && annotation[4] != 'Unknown') {
                    s += "<td><a data-toggle='tooltip' title = 'Go to Scribe' href='/digipal/scribes/" + annotation[10] + "'>" + annotation[4] + "</a></td>";
                } else {
                    s += "<td>Unknown</td>";
                }

                if (annotation[5] !== null && annotation[5] != 'Unknown') {
                    s += "<td><a data-toggle='tooltip' title = 'Explore manuscripts in " + annotation[5] + "' href='/digipal/page/?town_or_city=" + annotation[5] + "'>" + annotation[5] + "</a></td>";
                } else {
                    s += "<td>Unknown</td>";
                }

                /*if (annotation[6] !== null && annotation[6] != 'Unknown') {
                            s += "<td><a title = 'Explore manuscripts written in " + annotation[6] + "' href='/digipal/page/?date=" + annotation[6] + "'>" + annotation[6] + "</a></td>";
                        } else {
                            s += "<td>Unknown</td>";
                        }*/

                s += '</tr>'
            }

            s += "</table>";
        }

        if (data.textunits && data.textunits.length) {
            if (cache && !cache.textunits) {
                cache.textunits = data.textunits;
            }
            s += "<h3 id ='header_textunits'>Text Units (" + data.textunits.length + ")</h3>";
            s += "<table id='table-textunits' class='table'>";
            s += '<th><input data-toggle="tooltip" title="Toggle all" type="checkbox" id="check_textunits_all" /> <label id="counter-textunits" for="check_textunits_all"></label></th><th>Annotation</th><th data-sort="0" data-reverse="' + reverse + '">Unit</td><th data-sort="1" data-reverse="' + reverse + '">Item Part</td>  </th>';
            for (i = 0; i < data['textunits'].length; i++) {
                var image = data['textunits'][i];
                s += "<tr data- class='table-row' data-graph = '" + image[1] + "'>";
                s += "<td class='col-md-1'><input data-toggle='tooltip' title='Toggle item' data-annotation='"+image[4]+"' data-graph = '" + image[1] + "' type='checkbox' aria-label='Text annotation #"+(i+1)+"' data-type='textunit' class='checkbox_image' /> <span class='num_row'># " + (i + 1) + "</span></td>";
                s += "<td data-graph = '" + image[1] + "'>" + image[0] + "</td>";
                s += "<td>" + image[2] + "</td>";
                s += "<td>" + image[3] + "</td>";
                s += '</tr>'
            }
            s += "</table>";
        }

        if (data.images && data.images.length) {
            if (cache && !cache.images) {
                cache.images = data.images;
            }
            s += "<h3 id ='header_images'>Manuscript Images (" + data.images.length + ")</h3>";
            s += "<table id='table-images' class='table'>";
            s += '<th><input data-toggle="tooltip" title="Toggle all" type="checkbox" id="check_images_all" /> <label id="counter-images" for="check_images_all"></label></th><th>Page</th><th data-sort="0" data-reverse="' + reverse + '">Label</td><th data-sort="3" data-reverse="' + reverse + '">Hand</th>';
            for (i = 0; i < data['images'].length; i++) {
                var image = data['images'][i];
                s += "<tr data- class='table-row' data-graph = '" + image[1] + "'><td class='col-md-1'><input aria-label='Manuscript image #"+(i+1)+"' data-toggle='tooltip' title='Toggle item' data-graph = '" + image[1] + "' type='checkbox' data-type='image' class='checkbox_image' /> <span class='num_row'># " + (i + 1) + "</span>  <td data-graph = '" + image[1] + "'><a data-toggle='tooltip' title ='View page in the manuscript viewer' href='/digipal/page/" + image[1] + "'>" + image[0] + "</a></td>";
                s += "<td data-graph = '" + image[1] + "'><a data-toggle='tooltip' title ='View page in the manuscript viewer' href='/digipal/page/" + image[1] + "'>" + image[2] + "</a></td>";
                s += "<td>" + image[3] + "</td>";
                s += '</tr>'
            }
            s += "</table>";
        }

        if (data.editorial && data.editorial.length) {
            s += "<h3 id='header_editorial'>Editorial Annotations (" + data.editorial.length + ")</h3>";
            s += "<table id='table-editorial' class='table'>";
            s += '<th><input data-toggle="tooltip" title="Toggle all" type="checkbox" id="check_editorial_all" /> <label id="counter-editorial" for="check_editorial_all"></label></th><th>Annotation</th><th data-sort="3" data-reverse="' + reverse + '">Page</th><th>Public Note</th>';
            if (cache && !cache.editorial) {
                cache.editorial = data.editorial;
            }

            for (i = 0; i < data['editorial'].length; i++) {

                var editorial_annotation = data['editorial'][i];
                s += "<tr class='table-row' data-graph = '" + editorial_annotation[2] + "'><td class='col-md-1'><input aria-label='Editorial annotation #"+(i+1)+"' data-toggle='tooltip' title='Toggle item' data-graph = '" + editorial_annotation[2] + "' type='checkbox' data-type='editorial' class='checkbox_image' /> <span class='num_row'># " + (i + 1) + "</span>  </td><td data-graph = '" + editorial_annotation[2] + "'><a title='View graph in the manuscript viewer' href='/digipal/page/" + editorial_annotation[1] + "/?vector_id=" + editorial_annotation[2] + "'>" + editorial_annotation[0] + "</a>";
                s += "</td>";

                s += "<td data-graph = '" + editorial_annotation[2] + "'><a data-toggle='tooltip' title='Go to manuscript page' href='/digipal/page/" + editorial_annotation[2] + "'>" + editorial_annotation[3] + "</a>";
                s += "</td>";

                if (typeof isAdmin !== 'undefined' && isAdmin) {
                    s += "<td data-graph = '" + editorial_annotation[2] + "'><div class='public-note'>" + editorial_annotation[4].substring(0, 50) + " ... </div> <button class='btn-link read-more' data-image='" + editorial_annotation[1] + "' data-id = '" + editorial_annotation[2] + "'>Read and Edit</button>";
                } else {
                    if (editorial_annotation[4].length > 50) {
                        s += "<td data-graph = '" + editorial_annotation[2] + "'><div class='public-note'>" + editorial_annotation[4].substring(0, 50) + " ... </div><button class='btn-link read-more' data-image='" + editorial_annotation[1] + "' data-id = '" + editorial_annotation[2] + "'>Read more</button>";
                    } else {
                        s += "<td data-graph = '" + editorial_annotation[2] + "'><div class='public-note'>" + editorial_annotation[4] + "</div>";
                    }
                }
                s += "</td>";
                s += '</tr>'
            }
            s += "</table>";
        }

        if (isExternal) {
            var alert_string = "<div id='alert-save-collection' class='alert alert-success'>This is an external collection. Do you want to save it? <div class='pull-right'><input type='button' id='save-collection' class='btn btn-xs btn-success' value='Save' /></div></div>";
            s = alert_string + s;
        }

        container_basket.html(s);

        update();

        launchEvents(isExternal);
    }

    function groupManuscripts(annotations) {
        var manuscripts = {};
        var n = 0;
        if (annotations && annotations.length) {
            for (var i = 0; i < annotations.length; i++) {
                if (!manuscripts[annotations[i][14]]) {
                    n++;
                    manuscripts[annotations[i][14]] = n;
                }
            }
        }
        return manuscripts;
    }

    function displayGrid(data, attrs) {
        var manuscripts = groupManuscripts(data.annotations);
        var container = $('#grid');
        var s = '';

        if (data.annotations) {
            data.annotations = data.annotations.sort(function(x, y) {
                return x[attrs.sorting] == y[attrs.sorting] ? 0 : (x[attrs.sorting] < y[attrs.sorting] ? -1 : 1);
            });

            s += "<div id='manuscripts-index'>";
            if (data.annotations && data.annotations.length) {
                for (var manuscript in manuscripts) {
                    s += "<p class='manuscript-index'>" + manuscripts[manuscript] + ") " + manuscript + "</p>";
                }
            }
            s += "</div>";
        }
        if (data.annotations && data.annotations.length) {
            s += "<div id='annotations-grid' class='panel col-md-12-no'>";
            s += "<h2>Graphs (" + data.annotations.length + ")</h2>";
            for (var i = 0; i < data.annotations.length; i++) {

                if (!i || (data.annotations[i][attrs.sorting] !== data.annotations[i - 1][attrs.sorting])) {
                    if (attrs.sorting !== 'no-group') {
                        s += "<h3>" + data.annotations[i][attrs.sorting] + "</h3>";
                    }
                    s += "<div class='grid-images row'>";
                }

                //s += "<div data-toggle='tooltip' title='" + data.annotations[i][11] + "' class='grid-image col-md-1' data-graph='" + data.annotations[i][1] + "'><span class='manuscript-number'>" + manuscripts[data.annotations[i][14]] + "</span>" + data.annotations[i][0] + "</div>";
                s += "<div data-toggle='tooltip' title='" + data.annotations[i][11] + "' class='grid-image' data-graph='" + data.annotations[i][1] + "'><span class='manuscript-number'>" + manuscripts[data.annotations[i][14]] + "</span>" + data.annotations[i][0] + "</div>";

                if (!data.annotations[i + 1] || (data.annotations[i][attrs.sorting] !== data.annotations[i + 1][attrs.sorting])) {
                    s += "</div>";
                }
            }
            s += "</div>";
        }

        var data_items = data.textunits;
        if (data_items && data_items.length) {
            s += "<div id='textunits-grid' class='panel col-md-12-no'>";
            s += "<h2>Text Units (" + data_items.length + ")</h2>";

            for (var i = 0; i < data_items.length; i++) {

                if (!i || (data_items[i][2] !== data_items[i - 1][2]) && (!attrs.sorting == 'no-group')) {
                    if (!attrs.sorting == 'no-group') {
                        s += "<h3>" + data_items[i][2] + "</h3>";
                    }
                    s += "<div class='grid-images row'>";
                }

                s += "<div data-toggle='tooltip' title='" + data_items[i][3] + ", " + data_items[i][2] + "' data-placement='right' class='grid-image' data-annotation='"+data_items[i][4]+"' data-graph='" + data_items[i][1] + "'>" + data_items[i][0] + "</div>";

                if (!data_items[i + 1] || (data_items[i][2] !== data_items[i + 1][2]) && (!attrs.sorting == 'no-group')) {
                    s += "</div>";
                }
            }
            s += "</div>";
        }

        if (data.images && data.images.length) {
            s += "<div id='images-grid' class='panel col-md-12-no'>";
            s += "<h2>Manuscript Images (" + data.images.length + ")</h2>";
            for (var i = 0; i < data.images.length; i++) {

                if (!i || (data.images[i][2] !== data.images[i - 1][2]) && (!attrs.sorting == 'no-group')) {
                    if (!attrs.sorting == 'no-group') {
                        s += "<h3>" + data.images[i][2] + "</h3>";
                    }
                    s += "<div class='grid-images row'>";
                }

                //s += "<div data-toggle='tooltip' title='" + data.images[i][3] + "' data-placement='right' class='grid-image col-md-1' data-graph='" + data.images[i][1] + "'>" + data.images[i][0] + "</div>";
                s += "<div data-toggle='tooltip' title='" + data.images[i][3] + "' data-placement='right' class='grid-image' data-graph='" + data.images[i][1] + "'>" + data.images[i][0] + "</div>";

                if (!data.images[i + 1] || (data.images[i][2] !== data.images[i + 1][2]) && (!attrs.sorting == 'no-group')) {
                    s += "</div>";
                }
            }
            s += "</div>";
        }

        if (data.editorial && data.editorial.length) {
            s += "<div id='editorial-grid' class='panel col-md-12-no'>";
            s += "<h2>Editorial Annotations (" + data.editorial.length + ")</h2>";
            for (var i = 0; i < data.editorial.length; i++) {
                editorialCache[data.editorial[i][2]] = data.editorial[i][4];
                if (!i || (data.editorial[i][3] !== data.editorial[i - 1][3]) && (!attrs.sorting == 'no-group')) {
                    if (!attrs.sorting == 'no-group') {
                        s += "<h3>" + data.editorial[i][3] + "</h3>";
                    }
                    s += "<div class='grid-images row col-md-12-no'>";
                }

                //s += "<div class='grid-image col-md-1' data-graph='" + data.editorial[i][2] + "'>" + data.editorial[i][0] + "</div>";
                s += "<div class='grid-image' data-graph='" + data.editorial[i][2] + "'>" + data.editorial[i][0] + "</div>";

                if (!data.editorial[i + 1] || (data.editorial[i][3] !== data.editorial[i + 1][3]) && (!attrs.sorting == 'no-group')) {
                    s += "</div>";
                }
            }
            s += "</div>";
        }

        container.html(s);

        $('.grid-image').on('click', function() {
            var graph = $(this).data('graph');
            if ($(this).find('img').hasClass('selected') && selectedItems.indexOf(graph) >= 0) {
                selectedItems.splice(selectedItems.indexOf(graph), 1);
                $(this).find('img').removeClass('selected');
            } else {
                if (selectedItems.indexOf(graph) < 0) {
                    selectedItems.push(graph);
                }
                $(this).find('img').addClass('selected');
            }
            update_counter();
        });

        //$('.grid-images').sortable();
        $('[data-toggle="tooltip"]').tooltip();
        update_counter();
        update();
    }

    var editCollection = function(el) {
        // Update the collection in localstorage after the order of the
        // items has be changed by the user.
        var _collections = JSON.parse(localStorage.getItem('collections')),
            _basket;

        var selectedCollection = localStorage.getItem('selectedCollection');
        var list, type, new_list = [];

        // GN: why not defining ONCE in the code getCUrrentCOllection()
        // and calling it, instead of re-implementing the same things so
        // many times!
        // DRY, DRY, DRY, DRY....
        $.each(_collections, function(index, value) {
            if (value.id == selectedCollection) {
                _basket = value;
                _basket.name = index;
                _basket.id = value.id;
            }
        });

        var $table = el.closest('table, .panel');
        $table.find('tr[data-graph], div[data-graph].grid-image').each(function() {
            new_list.push($(this).data('graph'));
        });

        var group_name = ($table.attr('id')).replace('table-', '').replace('-grid', '');
        $.each(collection_types, function(type, info) {
            if (info.group == group_name) _basket[info.group] = new_list;
        });

        localStorage.setItem('collections', JSON.stringify(_collections));
        // force rendering of the other view (grid/table)
        $(window).trigger('storage');
    };

    var makeSortable = function() {
        var item_index, target_index;
        $("tbody, .grid-images").sortable({
            items: "tr[data-graph], div[data-graph].grid-image",
            update: function(event, ui) {
                changeNumbers();
                editCollection(ui.item);
            }
        });
    };

    function launchEvents(isExternal) {
        update_counter();
        $('#check_images_all').unbind().on('change', function() {
            if ($(this).is(':checked')) {
                $('#table-images').find('input[type="checkbox"]').prop('checked', true);
                $('#table-images').find('.table-row').addClass('selected').each(function() {
                    if (selectedItems.indexOf($(this).data('graph')) < 0) {
                        selectedItems.push($(this).data('graph'));
                    }
                });
            } else {
                $('#table-images').find('input[type="checkbox"]').prop('checked', false);
                $('#table-images').find('.table-row').removeClass('selected').each(function() {
                    selectedItems.splice(selectedItems.indexOf($(this).data('graph')), 1);
                });
            }
            update_counter();
        });

        $('#check_textunits_all').unbind().on('change', function() {
            if ($(this).is(':checked')) {
                $('#table-textunits').find('input[type="checkbox"]').prop('checked', true);
                $('#table-textunits').find('.table-row').addClass('selected').each(function() {
                    if (selectedItems.indexOf($(this).data('graph')) < 0) {
                        selectedItems.push($(this).data('graph'));
                    }
                });
            } else {
                $('#table-textunits').find('input[type="checkbox"]').prop('checked', false);
                $('#table-textunits').find('.table-row').removeClass('selected').each(function() {
                    selectedItems.splice(selectedItems.indexOf($(this).data('graph')), 1);
                });
            }
            update_counter();
        });

        $('#check_annotations_all').unbind().on('change', function() {
            if ($(this).is(':checked')) {
                $('#table-annotations').find('input[type="checkbox"]').prop('checked', true);
                $('#table-annotations').find('.table-row').each(function() {
                    if (selectedItems.indexOf($(this).data('graph')) < 0) {
                        selectedItems.push($(this).data('graph'));
                    }
                });
                $('#table-annotations').find('.table-row').addClass('selected');
            } else {
                $('#table-annotations').find('input[type="checkbox"]').prop('checked', false);
                $('#table-annotations').find('.table-row').each(function() {
                    selectedItems.splice(selectedItems.indexOf($(this).data('graph')), 1);
                });
                $('#table-annotations').find('.table-row').removeClass('selected');
            }
            update_counter();
        });

        $('#check_editorial_all').unbind().on('change', function() {
            if ($(this).is(':checked')) {
                $('#table-editorial').find('input[type="checkbox"]').prop('checked', true);
                $('#table-editorial').find('.table-row').addClass('selected').each(function() {
                    if (selectedItems.indexOf($(this).data('graph')) < 0) {
                        selectedItems.push($(this).data('graph'));
                    }
                });
            } else {
                $('#table-editorial').find('input[type="checkbox"]').prop('checked', false);
                $('#table-editorial').find('.table-row').removeClass('selected').each(function() {
                    selectedItems.splice(selectedItems.indexOf($(this).data('graph')), 1);
                });
            }
            update_counter();
        });

        $('th[data-sort]').unbind().on('click', function() {
            var reverse = !$(this).data('reverse');
            var html = $(this).text();
            $(this).data('reverse', reverse);
            sort($(this).data('sort'), $(this).data('reverse'), $(this).closest('table').attr('id').split('-')[1]);
            var th = $('th[data-sort="' + $(this).data('sort') + '"]');
            th.html('<span class="glyphicon glyphicon-sort-by-attributes-alt small"></span> ' + html);
            if (reverse) {
                th.find('.glyphicon').addClass('reverse');
            }
        });

        $('#remove_from_collection').on('click', function() {

            var basket;
            var selectedCollection = localStorage.getItem('selectedCollection');
            var collections = JSON.parse(localStorage.getItem('collections'));
            var loading_div = $("<div class='loading-div'>");
            var background = $("<div class='dialog-background'>");
            if (!isExternal) {
                $.each(collections, function(index, value) {
                    if (value.id == selectedCollection) {
                        basket = value;
                        basket.name = index;
                        basket.id = value.id;
                    }
                });
            } else {
                basket = collection;
            }

            if (!$(".loading-div").length) {
                var images = selectedItems.length == 1 ? "image" : "images";
                loading_div.html('<h2>Removing images</h2>');
                loading_div.append("<p>You are about to remove " + selectedItems.length + " " + images + ". Continue?");
                loading_div.append("<p><button class='btn btn-success btn-sm' id='remove_images_from_collection'>Remove</button> <button class='btn btn-danger btn-sm' id='cancel'>Cancel</button></p>");
                background.append(loading_div);
                $('body').append(background);
            }

            $('#remove_images_from_collection').unbind().on('click', function() {
                for (var j = 0; j < selectedItems.length; j++) {

                    // remove selected items from collection in localStorage
                    // GN: note that selectedItems contains only a list of item id
                    // No indication of the item type the id refers to
                    // So if you remove image 1, graph 1 and text unit one 1
                    // will also be removed from the collection!!
                    for (var i in basket) {
                        if (basket[i] instanceof Array) {
                            var itemid = selectedItems[j];
                            if (basket[i].indexOf(itemid) >= 0) {
                                if (i == "editorial") {
                                    itemid = itemid.toString();
                                }
                                basket[i].splice(basket[i].indexOf(itemid), 1);
                                $('[data-graph="' + itemid + '"]').fadeOut().remove();
                                selectedItems.splice(j, 1);
                                j--;
                            }
                        }
                    }

                    // remove from cache
                    for (var c in cache) {
                        for (var f = 0; f < cache[c].length; f++) {
                            if (cache[c] && cache.length) {
                                if (selectedItems[j] == cache[c][f][collection_types[c].idindex]) {
                                    cache[c].splice(f, 1);
                                }
                            }
                        }
                    }
                }
                //cache = basket;

                update_counter();

                if (!sum_images_collection(basket) && !isExternal) {
                    var container_basket = $('#container_basket');
                    var s = '<div class="container alert alert-warning"><p>The collection is empty.</p>';
                    s += '<p>Start adding images from <a href="/digipal/page">Browse Images</a> or using the DigiPal <a href="/digipal/search/?from_link=true">search engine</a></div>';
                    container_basket.html(s);
                }

                localStorage.setItem('collections', JSON.stringify(collections));
                $('.dialog-background').fadeOut().remove();
                update_collection_counter();
                changeNumbers();
            });

            $('#cancel').unbind().on('click', function() {
                $('.dialog-background').fadeOut().remove();
            });

        });


        var print = $('#print');
        print.unbind('click').on('click', function() {
            var tab = $('.tab-pane.active').attr('id');
            var grouping = $('#sort-select').val();
            window.open(location.href + '?view=print&tab=' + tab + '&grouping=' + grouping);
        });

        $('#to_lightbox').unbind().on('click', function() {
            var graphs = [],
                images = [],
                editorial_annotations = [],
                element,
                basket;

            var selectedCollection = localStorage.getItem('selectedCollection');
            var collections = JSON.parse(localStorage.getItem('collections'));
            var view = $('.tab-pane.active').attr('id');
            $.each(collections, function(index, value) {
                if (value.id == selectedCollection) {
                    basket = value;
                }
            });

            if (basket && basket.annotations && basket.annotations.length) {
                for (i = 0; i < basket.annotations.length; i++) {
                    if (basket.annotations[i].hasOwnProperty('graph')) {
                        element = basket.annotations[i].graph;
                    } else {
                        element = basket.annotations[i];
                    }
                    if (view == 'table') {
                        if ($('input[type="checkbox"][data-graph="' + element + '"]').is(':checked')) {
                            graphs.push(element);
                        }
                    } else if (view == 'grid') {
                        if ($('.grid-image[data-graph="' + element + '"]').find('img').hasClass('selected')) {
                            graphs.push(element);
                        }
                    }
                }
            }
            if (basket && basket.images && basket.images.length) {
                for (i = 0; i < basket.images.length; i++) {
                    element = basket.images[i];
                    if (view == 'table') {
                        if ($('input[type="checkbox"][data-graph="' + element + '"]').is(':checked')) {
                            images.push(element);
                        }
                    } else if (view == 'grid') {
                        if ($('.grid-image[data-graph="' + element + '"]').find('img').hasClass('selected')) {
                            images.push(element);
                        }
                    }
                }
            }
            if (basket && basket.editorial && basket.editorial.length) {
                for (i = 0; i < basket.editorial.length; i++) {
                    element = basket.editorial[i].toString();
                    if (view == 'table') {
                        if ($('input[type="checkbox"][data-graph="' + basket.editorial[i][0] + '"]').is(':checked')) {
                            editorial_annotations.push(element);
                        }
                    } else if (view == 'grid') {
                        if ($('.grid-image[data-graph="' + element + '"]').find('img').hasClass('selected')) {
                            editorial_annotations.push(element);
                        }
                    }
                }
            }

            $('#table-textunits input[type="checkbox"][data-graph]:checked').each(function() {
                editorial_annotations.push($(this).data('annotation'));
            });

            window.open('/lightbox/?annotations=[' + graphs.toString() + ']&images=[' + images.toString() + ']&editorial=[' + editorial_annotations + ']&from=' + encodeURIComponent(location.pathname));
        });

        $('tr.table-row').unbind().on('click', function(event) {

            var checkbox = $(this).find('.checkbox_image');

            if ($(this).hasClass('selected') && selectedItems.indexOf($(this).data('graph')) >= 0) {
                $(this).removeClass('selected');
                checkbox.prop('checked', false);
                selectedItems.splice(selectedItems.indexOf($(this).data('graph')), 1);
            } else {
                $(this).addClass('selected');
                checkbox.prop('checked', true);
                if (selectedItems.indexOf($(this).data('graph')) < 0) {
                    selectedItems.push($(this).data('graph'));
                }
            }
            update_counter();
            event.stopPropagation();
            event.stopImmediatePropagation();
        });

        $('.read-more').unbind().on('click', function(event) {

            if ($('.dialog-background').length) {
                $('.dialog-background').remove();
            }
            var image = $(this).data('image');
            var id = $(this).data('id');
            var background = $("<div class='dialog-background'>");
            var windowGraph = $("<div class='editorial-annotation-div'>");
            var title = $("<p class='editorial-annotation-title'>Editorial Annotation <span class='pull-right'><span style='cursor:pointer' class='fa fa-times' title='Close' data-toggle='tooltip'></span></span></p>");
            windowGraph.append(title);
            if (typeof isAdmin !== 'undefined' && isAdmin) {
                title.find('.pull-right').prepend("<span title='Edit' data-toggle='tooltip' style='cursor:pointer' class='fa fa-pencil-square-o'></span> <span title='Save' data-toggle='tooltip' style='cursor:pointer' class='fa fa-check-square'></span> ");
            }
            var content = $("<p class='editorial-annotation-content'>");
            var value = editorialCache[id];
            content.append(value);
            windowGraph.append(content);
            background.append(windowGraph);
            $('body').append(background);

            windowGraph.on('click', function(event) {
                event.stopPropagation();
            });

            background.on('click', function(event) {
                $(this).remove();
                event.stopPropagation();
            });

            title.find('.fa-times').on('click', function() {
                background.remove();
                event.stopPropagation();
            });

            title.find('.fa-pencil-square-o').on('click', function() {
                content.attr('contenteditable', true).focus();
                event.stopPropagation();
            });

            title.find('.fa-check-square').on('click', function() {

                var data = {
                    'display_note': content.html()
                };

                var url_data = {};
                url_data.image = image;
                url_data.id = id.toString();

                $.ajax({
                    type: 'POST',
                    url: '/digipal/api/graph/save_editorial/' + JSON.stringify([url_data]) + '/',
                    data: data,
                    success: function(data) {
                        if (data.success) {
                            notify("Annotation successfully saved", "success");
                            var value = data.graphs[0].display_note;
                            if (value.length > 50) {
                                value = value.substring(0, 50) + '...';
                            }
                            $('td[data-graph="' + id + '"]').find('.public-note').html(value);
                            editorialCache[id] = data.graphs[0].display_note;
                        } else {
                            if (data.errors.length) {
                                notify("Annotation not saved", "danger");
                            }
                        }
                    },
                    error: function(data) {
                        console.warn(data);
                    }
                });
                event.stopPropagation();
            });

            $('[data-toggle="tooltip"]').tooltip();
            event.stopPropagation();
        });

        update();

        $('[data-toggle="tooltip"]').tooltip();
    }

    $(document).ready(function() {

        $('a[data-toggle="pill"]').on('shown.bs.tab', function(e) {
            if (e.target.getAttribute('data-target') == "#table") {
                $('#select-sort-select').addClass('hidden');
            } else {
                $('#select-sort-select').removeClass('hidden');
            }
            update();
        });
        $('#select-sort-select').addClass('hidden');
        $('#sort-select').on('change', function() {
            displayGrid(cache, {
                'sorting': $(this).val()
            });
        });

        main(function() {

            var print_view = getParameter('view');
            var tab = getParameter('tab');
            var grouping = getParameter('grouping')[0] || "no-group";
            if (print_view.length && print_view[0] == 'print') {
                if (tab[0]) {
                    $('[data-target="#' + tab[0] + '"]').tab('show');
                }
                $('[media="print"]').attr('media', 'screen, print');
                $('*').unbind();
            }
            if (grouping.length && tab == 'grid') {
                displayGrid(cache, {
                    'sorting': grouping
                });
            }
        });

        $(window).bind('storage', function(e) {
            window.dputils.fragment_refreshing('#main_body_container');
            cache = {};
            main(function() {
                update_counter();
                update_collection_counter();
                window.dputils.fragment_refreshing('#main_body_container', true);
            });
        });

    });


    function update() {
        $("tr[data-graph]").each(function() {
            var graph = $(this).data('graph');
            if (selectedItems.indexOf(graph) >= 0) {
                $(this).addClass('selected');
                $(this).find('.checkbox_image').prop('checked', true);
            } else {
                $(this).removeClass('selected');
                $(this).find('.checkbox_image').prop('checked', false);
            }
        });

        $(".grid-image").each(function() {
            var graph = $(this).data('graph');
            if (selectedItems.indexOf(graph) >= 0) {
                $(this).find('img').addClass('selected');
            } else {
                $(this).find('img').removeClass('selected');
            }
        });

        update_counter();
    }

})();
