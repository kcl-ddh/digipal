jQuery(document).ready(function($) {
    function enable(jqe, enabled) {
        if (enabled) {
            jqe.removeAttr('disabled');
        } else {
            jqe.attr('disabled', 'disabled');
        }
    }
    
    $('#itempart_shelfmark_id').change(function() {
        // disable item part and locus drop down when shelfmark selected
        var checked = $(this).is(':checked');
        enable($('select[name=manuscript]'), !checked);
        enable($('#itempart_locus_id'), !checked);
        $('#itempart_shelfmark_text_id').toggle(checked);
        $('#itempart_repo_id').toggle(checked);
        $('#itempart_locus_text_id').toggle(checked);
        if (checked) {
            $('#itempart_shelfmark_text_id input').focus();
        }
    });

    $('#itempart_locus_id').change(function() {
        // disable item part and locus drop down when shelfmark selected
        var checked = $(this).is(':checked');
        //enable($('select[name=manuscript]'), !checked);
        enable($('#itempart_shelfmark_id'), !checked);
        $('#itempart_shelfmark_text_id').toggle(false);
        $('#itempart_locus_text_id').toggle(checked);
        if (checked) {
            $('#itempart_locus_text_id input').focus();
        }
    });
    
    $('#hand_set_id').change(function () {
        var checked = $(this).is(':checked');
        enable($('#manuscript_set_id'), !checked);
    });

    $('#manuscript_set_id').change(function () {
        var checked = $(this).is(':checked');
        enable($('#hand_set_id'), !checked);
    });

    function refresh_links() {
        $('#manuscript-link').attr('href', '/admin/digipal/itempart/'+$('select[name=manuscript]').val());
        $('#hand-link').attr('href', '/admin/digipal/hand/'+$('select[name=hand]').val());
    }
    
    $('select[name=manuscript], select[name=hand]').change(refresh_links);
    
    function show_image_replace_info(data) {
        var image_id = data['image1'];
        $replace_row = $('tr.replace-image-' + image_id);
        
        if (data['annotations'] && data['annotations'].length) {
            $replace_row.find('.message').html('Below you can see an annotation from this image and the same annotation after replacing with the new image. If they don\'t match revert to the original image by undoing your change in the drop down. <a class="try-another-graph" href="#">Try another graph</a>');
            var $samples = $replace_row.find('.samples');
            $samples.html('');
            for (var i = 0; i < data['annotations'].length; i++) {
                var $sp = $('<div class="img"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==" /></div>');
                $sp.find('img').attr('src', data['annotations'][i]);
                $samples.append($sp);
            }
            $samples.show();
            $replace_row.find('.try-another-graph').click(function() { 
               $('select[name=replace-image-' + image_id + ']').change(); 
               return false;
            });
        } else {
            $replace_row.find('.message').html('This image record has no annotation. Only the image file will be replaced.');
        }
    }
    
    $('select.replace-image').change(function () {
        var $select = $(this);
        var image_id = $select.attr('name').match(/\d+/)[0];
        var new_image_id = $select.val();
        
        var different_image = (image_id != new_image_id);
        $select.toggleClass('changed', different_image);
        
        $replace_row = $('tr.replace-image-' + image_id);
        $replace_row.toggle(different_image);
        $replace_row.find('.message').html('Please wait while the crop offsets are being calculated...');
        $replace_row.find('.samples').hide();
        //$replace_row.find('.samples img').attr('src', 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==');
        $replace_row.find('.samples').html('&nbsp;');
        if (different_image) {
            $.getJSON('', {action: 'test_replace_image', image1: image_id, image2: new_image_id}, show_image_replace_info);
        }
        
    });
    
    $('input[name=locus_regex], input[name=locus_result], select[name=locus_example]').on('change keyup', function() {
        var regexp = $('input[name=locus_regex]').val();
        var result = $('input[name=locus_result]').val();
        var example = $('select[name=locus_example] option:checked').text();
        var message = 'WARNING: No match found.';
        
        try {
            regexp = RegExp(regexp, 'i');
            
            var matches = regexp.exec(example);
            
            if (matches) {
                for (var i in matches) {
                    result = result.replace('\\'+i, matches[i]);
                }
                message = result;
            }
            
        } catch (err) {
            if (err.name === 'SyntaxError') {
                message = 'WARNING: ' + err.message;
            }
        }
        
        $('#locus-example-result').html(message.replace('<', '&lt;').replace('>', '&gt;'));
    });
    
    refresh_links();    
});
