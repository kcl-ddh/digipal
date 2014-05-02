function DropdownSelect() {

    var init = function() {
        main();
    };

    var main = function() {

        var parameters = getParameters();
        var value;
        for (var i = 0; i < parameters.length; i++) {
            $.each(parameters[i], function(index, value) {
                switch (index) {
                    case "index":
                        $('#index-select').val(value);
                        break;
                    case "repository":
                        $('#repository-select').val(value);
                        break;
                    case "date":
                        $('#date-select').val(value);
                        break;
                    case "scribes":
                        $('#scribes-select').val(value);
                        break;
                    case "place":
                        $('#place-select').val(value);
                        $('#scriptorium-select').val(value);
                        break;
                    case "name":
                        a = value;
                        $('#name-select').val(value);
                        break;
                    case "character":
                        $('#character-select').add('#character').val(value.replace('Æ', 'æ'));
                        break;
                    case "component":
                        $('#component-select').add('#component').val(value);
                        break;
                    case "feature":
                        $('#feature-select').add('#feature').val(value);
                        break;
                    case "script":
                        $('#script').val(value);
                        break;
                    case "allograph":
                        $('#allograph').val(value);
                        break;
                }
            });
        }


        $('select').trigger('liszt:updated');

    };

    var getParameters = function() {

        var searchString = window.location.search.substring(1),
            i, val, params = searchString.split("&");

        var parameters = [],
            param, value, key;

        for (i = 0; i < params.length; i++) {

            val = {};
            param = params[i].split("=");
            key = param[0];
            value = unescape(param[1]).replace(/\+/gi, ' ')
                .replace('Ã', 'Æ')
                .replace('Ã', 'æ')
                .replace(/[^\(\)\[\]a-zA-Z 0-9 Æ æ\'.,:-]+/g, '');

            if (value) {
                val[key] = value;
                parameters.push(val);
            }

        }

        return parameters;

    };

    return {
        'init': init
    };

}


$(document).ready(function() {
    var dropdowns = DropdownSelect();
    dropdowns.init();
});