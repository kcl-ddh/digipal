/**
 * StoredInputs:
 * 	Store the value of HTML inputs across page loads. 
 * 
 * Usage:
 * 
 * 	<input type="text" id="i1"/>
 *  <select id="i2">[...]</select>
 * 
 *  <script>
 * 		si = new StoredInputs('digipal_settings');
 * 		si.registerInput('#i1');
 * 		si.registerInput('#i2');
 *  <script>
 * 
 * Requirements:
 * 
 * 	jquery
 * 
**/
function StoredInputs(name) {
	this.name = name;
	this.duration = 10;
};

StoredInputs.prototype.registerInput = function(jqsInput) {
	// read value from cookie
	
	var c_name = this.name + '_' + $(jqsInput).attr('id');
	var c_value = document.cookie;
	var c_start = c_value.indexOf(" " + c_name + "=");
	if (c_start == -1) {
		c_start = c_value.indexOf(c_name + "=");
	}
	if (c_start !== -1) {
		c_start = c_value.indexOf("=", c_start) + 1;
		var c_end = c_value.indexOf(";", c_start);
		if (c_end == -1) {
			c_end = c_value.length;
		}
		c_value = unescape(c_value.substring(c_start,c_end));
		$(jqsInput).val(c_value);
	}
	
	// update cookie on change
	var self = this;
	$(jqsInput).change(function (event) {self.onChangeInput(event)});
}

StoredInputs.prototype.onChangeInput = function(event) {
	var exdate = new Date();
	exdate.setDate(exdate.getDate() + this.duration);
	
	var value=escape($(event.target).val()) + ((exdate==null) ? "" : "; expires="+exdate.toUTCString());
	
	document.cookie = this.name + "_" + event.target.id + "=" + value;
	
	return true;
}
