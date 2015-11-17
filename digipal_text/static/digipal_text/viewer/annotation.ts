/// <reference path="../dts/jquery.d.ts"/>

class Greeter {
    message: string;
   
    constructor(message: string) {
        this.message = message;
    }
    
    greet() {
       alert(this.message);
    }
}

$(function() {
    var greeter = new Greeter('Yo2!');
    greeter.greet();
});
