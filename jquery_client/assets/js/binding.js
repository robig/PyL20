function Binding(b) {
    const _this = this
    this.elementBindings = []
	const prop = b.property;
	if(!this.values) this.values={};
    this.value = b.object[b.property]
    this.valueGetter = function(){
        return _this.value;
    }
    this.blocked=false;
    this.valueSetter = function(val){
        _this.value = val;
        for (var i = 0; i < _this.elementBindings.length; i++) {
            var binding=_this.elementBindings[i]
            if(binding) {
                binding.element[binding.attribute] = val
            }
        }
    }
    this.addBinding = function(element, attribute, event){
        if(!element) return _this;
        var binding = {
            element: element,
            attribute: attribute
        };
        if (event){
            element.addEventListener(event, function(event){
                _this.valueSetter(element[attribute]);
            });
            //needed? 
            //binding.event = event

            
            element.addEventListener("mousedown", function(event){
                _this.blocked = true;
            });
            element.addEventListener("mouseup", function(event){
                _this.blocked = false;
            });
        }
        _this.elementBindings.push(binding);
        element[attribute] = _this.value;
        return _this;
    }

    Object.defineProperty(b.object, b.property, {
        get: this.valueGetter,
        set: this.valueSetter
    }); 

    b.object[b.property] = this.value;
}

/*
 example:

 var obj = {a:123}
var myInputElement1 = document.getElementById("myText1")
var myInputElement2 = document.getElementById("myText2")
var myDOMElement = document.getElementById("myDomElement")

new Binding({
	object: obj,
	property: "a"
})
.addBinding(myInputElement1, "value", "keyup")
.addBinding(myInputElement2, "value", "keyup")
.addBinding(myDOMElement, "innerHTML")

obj.a = 456;
*/
