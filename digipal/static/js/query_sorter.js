/**
 * Automatically update the Character and Allograph dropdowns on the Graph 
 * filters/search page each time one of them is changed.
 */

function set_up_linked_fields(linked_fields_list) {
    // update dependent drop downs
    // e.g. user selects chartype = accent 
    //  => we highlight all the accents chars in character drop down
    // and move them to the top
    for (var i in linked_fields_list) {
        set_up_linked_field(linked_fields_list[i]);
    }
};

function set_up_linked_field(linked_fields) {
    // select option in source -> only show related options in target
    $('form').on('change', 'select[name='+linked_fields.fields[0]+']', function () {
        // get all the related values
        var target_vals = linked_fields.values[$(this).val()];

        // if the current selection in target is not in target_vals we select the default one
        var target = $('select[name='+linked_fields.fields[1]+']');
        var target_selection_is_valid = (!$(this).val() || (target_vals && (target_vals.indexOf(target.val()) > -1))) || select_alternative_option(target, target_vals);
        if (!target_selection_is_valid) {
            target.val('');
        }
        
        // refresh the target drop down (to clear previous highlights)
        target.trigger("liszt:updated");
        
        // move related values to the top and highlight them
        if (target_vals) {
            
            $(target.next().find('li').get().reverse()).each(function() {
                // if related value then move it to the top
                if (target_vals.indexOf($(this).text()) > -1) {
                    $(this).parent().prepend($(this).addClass('added').detach());
                }
            });
        }

        // scroll to the top so highlighted options are visible
        if (!target_selection_is_valid) {
            target.next().find('ul').scrollTop(0);
        }
    });

    // if the user selects an option in the target that is not allowed by the source
    // we reset the source.
    // e.g. char = a and chartype = accent
    // we also remove the highlighting.
    $('form').on('change', 'select[name='+linked_fields.fields[1]+']', function () {
        var $source = $('select[name='+linked_fields.fields[0]+']');
        if ($source.length) {
            var target_val = $(this).val();
            if (target_val) {
                target_val = $(this).find('option:selected').text();
                var target_vals = linked_fields.values[$source.val()] || [];
                if (target_vals.indexOf(target_val) == -1) {

                    // update the source selection (e.g. a, insular -> a) 
                    var source_val = '';
                    if (linked_fields.update_source) {
                        for (var val in linked_fields.values) {
                            if (linked_fields.values[val].indexOf(target_val) > -1) {
                                source_val = val;
                                break;
                            }
                        }
                    }
                    
                    $source.val(source_val);
                    
                    $source.trigger('liszt:updated');
                    $(this).trigger('liszt:updated');
                }
            }
        }
    });
    
    // run this once on page load to initialise the highlights
    for (var i in linked_fields.fields) {
        $('select[name='+linked_fields.fields[i]+']').trigger('change');
    }
};

function select_alternative_option(target, valid_vals) {
    // Special case for the clunky allograph dropdown.
    // Allograph drop down has options like these: 
    // <option value="insular">a, insular</option>
    // <option value="insular">r, insular</option>
    // So when the user selects 'r, insular', the page reloads with:
    // ?character=a&allograph=insular
    // and 'a, insular' gets selected in the allograph drop down.
    //
    // This function will select the 'r, insular' option
    // by combining the current value (insular) and the value of
    // the source dropdown (character = r)
    //
    var ret = false;
    
    // get the value of the target
    var target_val = $(target).val();
    if (target_val) {
        // get all valid targets
        // TODO: escape the value (e.g. ']' would cause an error)
        $(target).find('option[value='+target_val+']').each(function() {
            if (valid_vals.indexOf($(this).text()) > -1) {
                // note: we can't do $(target).val(...) because values are not unique
                $(this).prop('selected', true);
                ret = true;
            }
        });
    }
    
    return ret;    
};

