var basket = localStorage.getItem('lightbox_basket');
var basket_elements = JSON.parse(basket);
var length_basket_elements = function(elements) {
	var n = 0;
	if (elements) {
		$.each(elements, function() {
			n += this.length;
		});
	}
	return n;
};

var length_basket = length_basket_elements(basket_elements);
var basket_element = $('#lightbox_button');
if (length_basket == 1) {
	basket_element.html("Collection (" + length_basket + " image)");
} else {
	basket_element.html("Collection (" + length_basket + " images)");
}