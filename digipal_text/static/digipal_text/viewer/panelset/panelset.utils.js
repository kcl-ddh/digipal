//////////////////////////////////////////////////////////////////////
//
// Utility functions
//
//////////////////////////////////////////////////////////////////////
(function(TextViewer, $, undefined) {

    TextViewer.callApi = function(url, onSuccess, onComplete, requestData, synced) {
        // See http://stackoverflow.com/questions/9956255.
        // This tricks prevents caching of the fragment by the browser.
        // Without this if you move away from the page and then click back
        // it will show only the last Ajax response instead of the full HTML page.
        url = url ? url : '';
        var url_ajax = url + ((url.indexOf('?') === -1) ? '?' : '&') + 'jx=1';

        var getData = {
            url: url_ajax,
            data: requestData,
            async: (synced ? false : true),
            complete: onComplete,
            success: onSuccess
        };
        if (requestData && requestData.method) {
            getData.type = requestData.method;
            delete requestData.method;
        }
        var ret = $.ajax(getData);

        return ret;
    };

    TextViewer.getStrFromTime = function(date) {
        date = date || new Date();
        var parts = [date.getHours(), date.getMinutes(), date.getSeconds()];
        for (var i in parts) {
            if ((i > 0) && (parts[i] < 10)) parts[i] = '0' + parts[i];
        }
        return parts.join(':');
    };

    // These are external init steps for JSLayout
    function initLayoutAddOns() {
        //
        //  DISABLE TEXT-SELECTION WHEN DRAGGING (or even _trying_ to drag!)
        //  this functionality will be included in RC30.80
        //
        $.layout.disableTextSelection = function(){
            var $d  = $(document),
                    s   = 'textSelectionDisabled',
                    x   = 'textSelectionInitialized'
            ;
            if ($.fn.disableSelection) {
                if (!$d.data(x)) // document hasn't been initialized yet
                    $d.on('mouseup', $.layout.enableTextSelection ).data(x, true);
                if (!$d.data(s))
                    $d.disableSelection().data(s, true);
            }
        };
        $.layout.enableTextSelection = function(){
            var $d  = $(document),
                    s   = 'textSelectionDisabled';
            if ($.fn.enableSelection && $d.data(s))
                $d.enableSelection().data(s, false);
        };

        var $lrs = $(".ui-layout-resizer");

        // affects only the resizer element
        // TODO: GN - had to add this condition otherwise the function call fails.
        if ($.fn.disableSelection) {
            $lrs.disableSelection();
        }

        $lrs.on('mousedown', $.layout.disableTextSelection ); // affects entire document
    }

    // TODO: move to dputils.js

    // See https://docs.djangoproject.com/en/1.7/ref/contrib/csrf/#ajax
    // This allows us to POST with Ajax
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    TextViewer.get_sublocation_from_element = function(element) {
        // returns a sub location array from a html element
        // <span data-dpt='location' data-dpt-loctype="entry">1a1</span>
        // => [['', 'location'], ['loctype', 'entry'], ['@text', '1a1']]
        var ret = [];
        var $el = $(element).closest('[data-dpt]');
        if ($el.length) {
            // convert attributes
            ret = $.map($el[0].attributes, function(val, i) {
                var name = val.name.replace(/^data-dpt-?/, '');
                if (name != val.name && name !== 'cat') return [[name, val.value]];
            });
            // filter: we don't want ANY element (e.g. clause: ok, exp/abbr: no)
            if (ret.length > 0) {
                var accepted_tags = ['clause', 'location', 'person'];
                if (accepted_tags.indexOf(ret[0][1]) < 0) {
                    ret = [];
                }
            }
            // add slugified small text content
            if (ret.length > 0) {
                var text = TextViewer.slugify($el.text());
                if (text.length > 0 && text.length < 20) {
                    ret.push(['@text', text]);
                }
            }

            // find out the occurrence number. e.g. ['@o', '2'] for second occurrence.
            if (1) {
                var order = 0;

                var selectorInfo = TextViewer.getSelectorFromSublocation(ret);
                $el.parents('.panel-content').find(selectorInfo.selector).each(function() {
                    var $oel = $(this);
                    if (!selectorInfo.text || (TextViewer.slugify($oel.text()) == selectorInfo.text)) {
                        order += 1;
                    }
                    if ($oel[0] === $el[0]) return false;
                });

                if (order > 1) {
                    ret.push(['@o', '' + order]);
                }
            }
        }

        return ret;
    };

    TextViewer.slugify = function(s) {
        return s.toLowerCase().replace(/(^\s+|\s+$)/g, '').replace(/\W/g, '-');
    };

    TextViewer.getSelectorFromSublocation = function(sublocation) {
        // input: [["", "person"], ["type", "name"], ["@text", "bob"], ["@o", "2"]]
        // output: {"order":"2","selector":"[data-dpt=person][data-dpt-type=name]","text":"bob"}
        var ret = {order: 1, selector: '', text: ''};

        var sel = '';

        sublocation.map(function(pair) {
            if (pair[0] == '@o') {
                ret.order = pair[1];
                return;
            }
            if (pair[0] == '@text') {
                ret.text = pair[1];
                return;
            }
            var attr = 'data-dpt' + (pair[0] ? '-' : '') + pair[0];
            sel += '['+attr+'='+pair[1]+']';
        });

        ret.selector = sel;

        return ret;
    };

    // Returns $element
    // or the chosen element associated to it
    TextViewer.getCtrl = function($element) {
        var ret = $element.next('.chzn-container');
        if (ret.length < 1) ret = $element;
        return ret;
    };

    // Show the given $element if condition is 0
    // Hide if undefined or 1
    TextViewer.unhide = function($element, condition) {
        if (!$element || $element.length < 1) return;

        // use chosen element instead if any
        $element = TextViewer.getCtrl($element);

        // find parent or itself with dp(un)hidden class
        var $el = $element.closest('.dphidden, .dpunhidden');
        if (!$el.hasClass('dphidden') && !$el.hasClass('dpunhidden')) {
            console.log('NO dp(un)hidden CLASS!');
        }
        if ($el.length < 1) {
            console.log('.dp(un)hidden NOT FOUND!');
        }
        $el.toggleClass('dphidden', !condition);
        $el.toggleClass('dpunhidden', !!condition);
        if (!$el.hasClass('dphidden') && !$el.hasClass('dpunhidden')) {
            console.log('NO dp(un)hidden CLASS SET!');
        }
    };

    // Improve all the select elements under a root element
    // At the moment we are using Chosen plugin
    TextViewer.upgrade_selects = function($root) {

        $root.find('select').not('.chzn-done').each(function() {
            var classes = $(this).attr('class');
            $(this).chosen({
                disable_search: $(this).hasClass('no-search'),
                no_results_text: $(this).hasClass('can-add') ? 'Not found, select to add' : 'Location not found',
                disable_search_threshold: 6,
            });
            // transfer all the classes from the select to the chosen element
            TextViewer.getCtrl($(this)).addClass(classes);
            $(this).removeClass(classes);
        });
    };

    TextViewer.urldecode = function(str) {
        return decodeURIComponent((str+'').replace(/\+/g, '%20'));
    };

    initLayoutAddOns();

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", window.dputils.getCookie('csrftoken'));
            }
        }
    });

}( window.TextViewer = window.TextViewer || {}, jQuery ));
