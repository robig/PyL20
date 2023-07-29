function Binding(b) {
    const _this = this
    this.elementBindings = []
	const prop = b.property;
	if(!this.values) this.values={};
    this.value = b.object[b.property]
    this.valueGetter = function(){
        return _this.value;
    }
    this.callbacks=[];
    this.redrawCalback=null;
    this.identifier=null;
    this.blocked=false;
    this.trigger=null;
    this.valueSetter = function(val){
        _this.value = val;
        
        var ta = null;
        for (var i = 0; i < _this.elementBindings.length; i++) {
            var binding=_this.elementBindings[i]
            if(binding) {
                ta = binding.element;
                var v = val;
                if(binding.mapper) v = binding.mapper(val, binding.element[binding.attribute]);
                binding.element[binding.attribute] = v;
            }
            if(_this.trigger) {
                //console.log("TRIGGER: "+_this.trigger+" on ", binding.element);
                $(binding.element).trigger(_this.trigger);
            }
        }
        if(_this.redrawCalback) {
            _this.redrawCalback({"value": val, "ident": _this.identifier});
        }
        if(_this.blocked && _this.callbacks.length>0) {
            //console.log("callback blocked", _this.callbacks);
            return;
        }
        _this.callbacks.forEach(cb=> cb({"value": val, "ident":_this.identifier, "target": ta }));
    }
    this.addBinding = function(element, attribute, event){
        if(!element) return _this;
        var binding = {
            element: element,
            attribute: attribute
        };
        if (event){
            $(element).on(event, function(evt){
                //console.log("bingding.js event: "+event, evt)
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

    this.addClassBinding = function(element, attribute, className){
        if(!element) return _this;
        var binding = {
            element: element,
            attribute: attribute,
            mapper: function(val, oldVal) {
                //console.log("toggle "+className);
                $(element).removeClass(className + oldVal);
                $(element).addClass(className + val);
                return val;
            }
        };
        _this.elementBindings.push(binding);
        element[attribute] = _this.value;
        return _this;
    }

    this.addMappedBinding = function(element, attribute, mapper){
        if(!element) return _this;
        var binding = {
            element: element,
            attribute: attribute,
            mapper: mapper
        };

        _this.elementBindings.push(binding);
        element[attribute] = _this.value;
        return _this;
    }

    this.addCallback = function(cb) {
        _this.callbacks.push(cb)
    };

    this.setIdentifier = function(val) {
        _this.identifier = val;
    }

    this.setTrigger = function(val) {
        _this.trigger = val;
    }

    this.setRedrawCallback = function(val) {
        _this.redrawCalback = val;
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
