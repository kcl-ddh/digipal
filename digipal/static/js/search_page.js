/**
 * Code used on the various search pages
 * (main search, record pages, graph search, browse images)
 */

function init_suggestions() {
    // Autocomplete for the search input box
    // Everywhere on the site + the search page
    var suggestions_limit = 8;

    // return true if the scope of the quick search is the database
    function is_searching_database() {
        return !$('[name=scp]').val();
    }

    function get_suggestions(query, cb) {
        // returns suggestions only if we are searching the database
        // so no suggestion for blog/news
        // Works for both typeahead and jqueryui
        if (is_searching_database()) {
            $.getJSON('/digipal/search/suggestions.json', {
                q: query.term || query,
                l: suggestions_limit
            }, function(data) {
                var ret = [];
                $.each(data, function(i, str) {
                    ret.push({
                        value: str.replace(/<\/?strong>/g, ''),
                        label: str
                    });
                });
                cb(ret);
            });
        } else {
            cb([]);
        }
    }

    // JQuery UI
    if (1) {
        $(function() {
            var cache = {};
            var $ac = $("#search-terms.autocomplete");
            if ($ac.length) {
                $ac.autocomplete({
                  minLength: 1,
                  source: get_suggestions,
                })
                .data('autocomplete')._renderItem = function( ul, item ) {
                    //return $('<li style="white-space: normal;>'+item.label+'</li>').appendTo(ul);
                    return $('<li>').append($('<a>').html(item.label)).appendTo(ul);
                };
            }
        });
    }

    // Old Typeahead version
    // No longer used as it messes up the styles of the text box
    // We already include JQueryUI anyway
    if (0 && $.fn.typeahead) {
        $("#search-terms").typeahead({
            minlength: 1,
            limit: suggestions_limit
        }, {
            name: 'dbrecords',
            source: get_suggestions,
            displayKey: 'value',
            templates: {
                suggestion: function(suggestion) {
                    return '<p style="white-space: normal;">' + suggestion.label + '</p>';
                }
            }
        });
    }
}

$(document).ready(function() {

    init_suggestions();

    // use bootstrap select to render the scope dropdown on the quick search
    var $select = $('select[name="scp"]');
    if ($.fn.bootstrapSelect && $select.length) {
        $select.bootstrapSelect(
            {
                // surround BS dropdown with input-group-btn span
                input_group: true,
                // need to be first so we get round corners on the left
                parent: {
                    selector: '#quick-search form .input-group:first',
                    placement: 'prepend'
                }
            },
            function() {
                $select.parent().hide();
                $select.on('change', function() {
                    $('#search-terms').focus();
            });
        });
    }

    // Scrolls directly to the results on second or later pages.
    // Scrolls to an element with id="auto-scroll"
    var page = window.dputils.get_query_string_param('page');
    if (page && (page != '1')) {
        var auto_scroll = $('#auto-scroll');
        if (auto_scroll.length) {
            // scroll to the results
            $("html, body").scrollTop(auto_scroll.offset().top);
        }
    }

    // clear-all button is clicked, we reset the form and empty the breadcrumb.
    // JIRA 484
    $('.breadcrumb .clear-all').on('click', function() {
        // remove the filters in the breadcrumb
        $('.breadcrumb a').remove();
        $('.breadcrumb').append('All');
        // remove the ',' between the filters we have removed.
        $('.breadcrumb').html($('.breadcrumb').html().replace(',', ''));

        // reset the selects in the form
        $('#searchform select').val('');
        $('#searchform select').trigger("liszt:updated");
        // clear the query text
        $('#searchform input[type=text]').val('');
        return false;
    });

    // prevent the page from jumping each time we expand/collapse a panel
    $('[data-toggle=collapse]').on('click', function() {
        return true;
    });

    if ($.fn.sortable) {
        $('.sortable').sortable();
    }
});


/*
 * This function is called by the main search page to:
 *  do some initialisations
 *  make the page work without reload
 */
function init_search_page(options) {

    window.sp_options = options;

    /*
        Example:

        init_search_page({
            advanced_search_expanded: {{ advanced_search_expanded }},
            filters: [
                {
                    html: '{{ filterHands.as_ul|escapejs }}',
                    label: 'Hands',
                },
                {
                    html: '{{ filterManuscripts.as_ul|escapejs }}',
                    label: 'Manuscripts',
                },
                {
                    html: '{{ filterScribes.as_ul|escapejs }}',
                    label: 'Scribes',
                }
            },
            linked_fields: [
                    {
                        'fields': ['chartype', 'character'],
                        'values': {
                                    u'abbreviation': [u'7', u'th\xe6t'],
                                    u'ligature': [u'&', u'ligature'],
                                    u'accent': [u'accent'],
                                    u'punctuation': [u'.', u'?', u'./', u';', u'abbrev. stroke'],
                    }
                ]
        });
    */

    function set_focus_search_box() {
        // Set focus on the search box. Place the cursor at the end.
        // Add a whitespace after the last search term.
        var search_box = $('#search-terms');
        if (search_box.length > 0) {
            var search_terms = $('#search-terms').val().replace(/^\s+|\s+$/g, '') + ' ';
            if (search_terms == ' ') search_terms = '';

            var page = dputils.get_query_string_param('page');
            if (!page || (page == '1')) {
                // GN: 2015/08/19: disabled focus on page load
                // because on small screens the text box is below the result
                // and the user, when they arrive to the search page for the
                // first time will be disoriented.
                //search_box.val(search_terms).focus();
            }
        }
    }

    function init_sliders() {
        $("div.slider").each(function() {
            $slider = $(this);
            $slider.slider({
                range: true,
                min: $slider.data('min'),
                max: $slider.data('max'),
                values: [$slider.data('min-value'), $slider.data('max-value')],
                slide: function(event, ui) {
                    $($slider.data('label-selector')).val("" + ui.values[0] + "x" + ui.values[1]);
                }
            });
        });
    }

    function set_up() {
        // update the advanced search hidden field
        $('#filter-toggler').on('click', function(e) {
            $('#advanced').val(!$('#advancedSearch').is(':visible'));
            // show/hide the advanced search panel
            $('#advancedSearch').slideToggle();
        });

        // Update the list of dropdowns in the advanced search panel
        // each time a tab is selected.
        $('#searchform a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
            var container = $('#containerFilters ul');

            var content = '';
            var label = '';
            for (var i in window.sp_options.filters) {
                var filter = window.sp_options.filters[i];
                if ($(this).data('filter-key') == filter.key) {
                    $('#basic_search_type').val(filter.key);
                    content += filter.html;
                    break;
                }
            }
            container.html(content);

            $('select').chosen();
        });

        set_focus_search_box();

        // Clicking a tab displays its content
        // and we set the selected tab in a hidden form field
        $('#result-types-switch a[data-target]').click(function(e) {
            e.preventDefault();
            $('#searchform input[name=result_type]').val($(this).attr('data-target').replace('#', ''));
        });

        // Update the result_type param in the query string when user
        // clicks the link to go to faceted search from advanced search.
        $('#link-faceted-search').click(function(e) {
            var result_type = $('#searchform input[name=result_type]').val();
            $(this).attr('href', $(this).attr('href') + '&result_type=' + result_type);
        });

        if (options && options.linked_fields) {
            set_up_linked_fields(options.linked_fields);
        }

        // convert div.slider into jquery UI slider widget
        init_sliders();

        // this is to force a reload of the search page after pressing back button
        // see http://stackoverflow.com/a/21507994
        window.onpopstate = function(event) {
            if(event && event.state) {
                location.reload();
            }
        };

        // Ajaxify the faceted search request
        // Any click on a link is intercepted and sent as an ajax request
        // the html fragment returned is re-injected into the page.
        // TODO: error management
        $('body').on('click', '#search-ajax-fragment a:not([data-target]):not([data-toggle]), #search-ajax-fragment form button:not([data-target]):not([data-toggle])', function(ev) {
            var $element = $(this);

            var page_url = dputils.get_page_url($(location).attr('href'));
            // ! we use this.href instead of $element.attr('href') as the first one returns the absolute URL
            var $form = $element.parents('form');
            //var url = this.hasAttribute('href') ? this.href : page_url + '?' + $form.serialize();
            var url = this.hasAttribute('href') ? this.href : page_url;
            var $focus_selector = $element.data('focus');

            // leave if the href points to another page
            if (page_url !== dputils.get_page_url(url)) return true;
            // leave if control-click (reload in new tab)
            if (ev.ctrlKey) return true;

            window.dputils.fragment_refreshing("#search-ajax-fragment");

            var url_on_success = this.href ? url : page_url + '?' + $form.serialize().replace(/[^?&]+=(&|$)/g, '');

            // See http://stackoverflow.com/questions/9956255.
            // This tricks prevents caching of the fragment by the browser.
            // Without this if you move away from the page and then click back
            // it will show only the last Ajax response instead of the full HTML page.
            var url_ajax = url + ((url.indexOf('?') === -1) ? '?' : '&') + 'jx=1';
            var is_post = ($form.attr('method') === 'POST');
            $.ajax({
                url: url_ajax,
                type: is_post ? 'post' : 'get',
                async: true,
                data: this.href ? {} : $form.serializeArray().reduce(function(obj, item) {obj[item.name] = item.value; return obj;}, {})
            })
            .success(function(data) {
                var $data = $(data);
                var $fragment = $('#search-ajax-fragment');

                // get rid of opened tooltip to avoid ghosts
                if ($.fn.tooltip) {
                    $fragment.find('[data-toggle="tooltip"]').tooltip('destroy');
                }

                // insert the new HTML content
                $fragment.html($data.html());

                if (!is_post) dputils.update_address_bar(url_on_success, false, true);
                // if (!is_post) dputils.update_address_bar(url, false, true);

                $fragment.stop().animate({
                    'background-color': 'white',
                    opacity: 1,
                    'border': 'none'
                }, 50);

                // TODO: find a way to pass title via the pushState/update_address_bar?
                var new_title = $('#search_page_title').val();
                if (document.title != new_title) {
                    document.title = $('#search_page_title').val();
                    // scroll to top of the search div
                    var $search_top = $('#search-top');
                    if ($search_top.length) {
                        $('html, body').animate({
                            scrollTop: $search_top.offset().top
                        }, 500);
                    }
                }

                // make sure visible thumbnails are loaded
                document.load_lazy_images();
                init_sliders();
                init_suggestions();
                if ($.fn.tooltip) {
                    $fragment.find('[data-toggle="tooltip"]').tooltip();
                }
                if ($.fn.sortable) {
                    $fragment.find('.sortable').sortable();
                }
                if ($focus_selector) {
                    var v = $($focus_selector).val();
                    $($focus_selector).val('').val(v).focus();
                }
                // enable the collection stars on the images
                if (window.collection_star) {
                    window.collection_star.init();
                }

                $(window).trigger('dploaded');
            })
            .fail(function(data) {
                $("#search-ajax-fragment").stop().css({
                    'opacity': 1
                }).animate({
                    'background-color': '#FFA0A0'
                }, 250, function() {
                    $("#search-ajax-fragment").animate({
                        'background-color': 'white'
                    }, 250);
                });
            });
            return false;
        });

        //		$('.facets a[data-toggle=collapse]').on('click', function() {
        //		    var $target = $($(this).data('target'));
        //		    $target.toggle();
        //		    return false;
        //		});
    }

    $(document).ready(function() {
        set_up();
    });
}

/* Browse Images, Search Graph pages and Record page */
$(function() {
    // Browse or Search Graph pages
    // When the user switches to a view, that view is stored in a hidden input field.
    // This allows the page to preserve the view across searches.
    $('#view-switch a[data-target]').on('click', function() {
        $('#searchform input[name=view]').attr('value', $(this).attr('href').replace(/.*view=([^&#]*).*/, '$1'));
    });

    // Annotation mode should be persistent across page loads
    $('#toggle-annotations-mode').on('change', function() {
        // So any change in the toggle widget should be reflected in the hidden field in the main form
        $('#searchform input[name=am]').attr('value', $(this).is(':checked') ? '1' : '0');
    });

    // Browse image
    // When the user clicks the pagination, we set the view and annotation mode
    // in the query string before following the link.
    $('.pagination a, .pagination-group a').on('click', function() {
        var $clicked = $(this);
        var href = $clicked.attr('href');
        $('form input[type=hidden][class=sticky]').each(function() {
            var name = $(this).attr('name');
            var replace = name + '=' + $(this).attr('value');
            if (replace) {
                href = (href.indexOf(name + '=') == -1) ? href + '&' + replace : href.replace(new RegExp(name + '=[^&#]*', 'g'), replace);
            }
        });
        $clicked.attr('href', href);
    });

    // Record page
    // When the user clicks the previous/next pagination, we set the tab in the
    // query string before following the link.
    // This way the same tabs remains open on the next record we visit.
    $('.record-view .previous a, .record-view .next a').on('click', function() {
        // extract the webpath (tab) after the record id from the current URL
        // e.g. '/hands/'
        // we get the current tab from the currently active tab rather than the
        // current document URL because of cases like:
        // http://127.0.0.1:8000/digipal/manuscripts/1464/descriptions/?s=1&result_type=manuscripts
        // where it's more difficult to extract the right number.
        //var tab = document.location.href.replace(/.*?\d+([^?]+).*/, '$1');
        var tab = $('#record-tab-switch li.active a').attr('href');
        if (tab) {
            tab = tab.replace(/.*?\d+([^?]+).*/, '$1');
        }
        var href = $(this).attr('href');
        if (tab && href) {
            // overwrite that path in the previous/next links
            $(this).attr('href', href.replace(/(\/\d+)[^?]+/, '$1' + tab));
        }
    });

    window.set_open_layer_on_faceted_results = function() {
        $('.result-ol').each(function() {
            set_open_layer_on_target($(this));
        });
    };

    var set_open_layer_on_target = function($target) {
        var map = window.dputils.add_open_layer({
            $target: $target,
            image_url: $target.data('url'),
            image_height: $target.data('height'),
            image_width: $target.data('width'),
            zoom: 1,
            can_rotate: true,
            can_fullscreen: true,
        });

        window.dputils.elastic_element($target, function() { map.updateSize(); }, 100, 10);
    };

    window.set_open_layer_on_faceted_results();
});
