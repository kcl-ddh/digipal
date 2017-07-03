/* Adds an edit icon next to each foreign key field to edit the related object in a new window */
jQuery(function($){
	// add the icon nect to each related object drop down
    $("select ~ a.add-another").each(function(){
        $(this).after("&nbsp;\x3Ca class='changelink' href='#'\x3E\x3C/a\x3E");
        $(this).next().click(function(){
            // get the value of the first selected option in the preceding select element
            //value = $(this).parent().children('select:first').attr('value');
            // better selector that will work with both a single select element or a dual 'pour-over' select widget.
            var value = $(this).parent().find('select :selected:last').val();
            if (value) {
                // /admin/digipal/itempart/add/?_to_field=id
                var link = $(this).prev().attr('href');
                link = link.replace(/\/add\/.*/, '/'+value+'/');
                //console.log(link + '?_popup=1', link, 'height=600,width=1000,resizable=yes,scrollbars=yes');
                var win = window.open(link + '?_popup=1', link, 'height=600,width=1000,resizable=yes,scrollbars=yes');
                win.focus();
            }
            return false;
        });
    });

    // this is for one to many inlines
    // TODO: make it work with new version of Django
    $("span.delete").each(function(){
        var inputFK = $(this).parent().nextAll('input').filter(function(index){return ($(this).attr("id").match(/-id$/) );}).eq(0);
        if (inputFK != null) {
            var recId = inputFK.val();
            var recTable = inputFK.attr('name').match(/^(.*)_set-/);
            if (recTable != null) {
            	recTable = recTable[1];
            	$(this).before("&nbsp;\x3Ca class='changelink' href='#'\x3E\x3C/a\x3E");
                var link = '../../'+recTable+'/'+recId+'/';
                $(this).prev().click(function(){
	                var win = window.open(link + '?_popup=1', link, 'height=600,width=1000,resizable=yes,scrollbars=yes');
    	            win.focus();
    	            return false;
                });
            }
        }
    });
});
