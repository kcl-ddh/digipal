/*

    Config.js: main javascript file

*/

$(document).ready( function() {

    /* modules */

    /* link behaviours */
    $("a.ctrl.tooltip").tooltip({
        position: "bottom right",
        predelay: 30,
        delay: 50,
        effect: "fade",
        fadeInSpeed: 400,
        fadeOutSpeed: 400,
        tipClass: "tooltipBox"
    });

    if ( $.fancybox ) {
        $(".ctrl.overlayTrigger").fancybox();
    }

    /* tabs */
    $(".mod.tabs ul.tabControls").tabs(".tabPanes > section");

    // jQuery("#breadCrumb1").jBreadCrumb();

     /* Tipsy tool tips */
    try {
        $(".tip").tipsy({
            delayIn: 500,
            delayOut: 500,
            fade: true
        });
    } catch(e) {
        // pass
        }
    // Idiograph / Component / Feature expansion
    $('.expand').on('click', function(ev){
        $(this).next('ul').toggleClass('showing');
    });
    // add a "faceted" class to active faceting dropdowns
    $("option.active").parent().addClass("faceted");
    // reset dropdown
    $("span.remove").on('click', function(){
        var prev = $(this).prev();
        prev.val("");
        prev.removeClass("faceted");
        $(this).remove();
        // resubmit form
        $("#filter_btn").click();
    });
    // reset dropdown using active facet buttons
    $(".clear_facet").on('click', function(){
        var to_remove = $(this).attr('id');
        $("option." + to_remove).removeAttr("selected");
        $(this).parent().remove();
        $("#filter_btn").click();
    });
});
