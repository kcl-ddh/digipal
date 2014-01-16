/**
 * Every element that match the css selector '.imageDatabase a.droppable_image'
 * will become draggable to a basket. The element must have an data-id attribute
 * which contains the ID of the digipal image record to add to the basket.     
 * 
 * Requires a <div id="basket_collector"> that will serves as a drop target
 * which is made visible as soon as we start dragging an item.
 * 
 * Dependency: add_to_lightbox.js
 */
$(document).ready(function(){
    $('select').chosen();

    var basket_collector = $('#basket_collector');
        basket_collector.droppable({
            accept: "a.droppable_image",
            hoverClass: "ui-state-active",
            drop: function(event, ui){

                var element = $(ui.helper[0]);
                if(add_to_lightbox(element, 'image', element.data('id'), false)){

                    var s = '<p>Image added to Lightbox!</p>';
                    s += '<p><img src="/static/digipal/images/success-icon.png" /></p>';
                    $(this).html(s);

                    element.animate({
                        width: 0,
                        height: 0
                    }, 650).remove();

                }

                var interval = setTimeout(function(){
                    s = '<p>Add image to Basket</p>';
                    s += '<p><img src="/static/digipal/images/shopping-cart-icon.png" /></p>';
                    basket_collector.html(s);

                    basket_collector.animate({
                        bottom: '-28%'
                    }, 350);

                }, 3000);

                $('html, body').css('cursor', 'initial');

            },
            out: function(){
                $(this).css('background', 'rgba(0, 0, 0, 0.7)');
            },
            over:function(){
                $(this).css('background', 'rgba(100, 100, 100, 0.7)');
            }
        });

        var images = $('a.droppable_image');
        images.draggable({
            containment: false,
            stack: '*',
            cursor: 'move',
            revert: true,
            scroll: true,
            zIndex: 6000,
            start: function(){
                basket_collector.animate({
                    bottom: '0'
                }, 350);
            },
            stop: function(){

                setTimeout(function(){

                    basket_collector.animate({
                        bottom: '-28%'
                    }, 350);

                }, 1000);
            }
        });

        $('.imageDatabase').on('mouseenter', function(event){
            $(this).find('.drag_caption').slideDown();
            event.stopPropagation();
            return false;
        }).on('mouseleave', function(event){
            $(this).find('.drag_caption').slideUp();
            event.stopPropagation();
            return false;
        });

});
