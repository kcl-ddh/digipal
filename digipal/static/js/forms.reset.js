 $(document).ready( function() {
	var originals = [];

	$("#reset").click(function(){
		$('#filtersform select').each(function(){
			originals.push(this[0].firstChild.nodeValue)
		})	
		$(".chzn-results").val("");
		var f = ($("ul .chzn-single span"))
		for(var i = 0; i < f.length; i++){
			f[i].firstChild.nodeValue = originals[i]
		}
	});
});