$("#menu .channel").on("click", e => {
    activateMenu("channel");
});

$("#menu .effect").on("click", e => {
    activateMenu("effect");
});

function activateMenu(name) {
    var all=["channel", "effect"];
    var isActive=$("#menu li."+name).hasClass("active");

    $("#menu li").removeClass("active");
    all.forEach(n=>{
        $("#"+n+"_settings").hide();    
    })
    
    if(!isActive) {
        $("#menu li."+name).addClass("active");  
        $("#"+name+"_settings").show();
    }
}


function showModal(id) {
    $("#"+id).show();
}

$(".close").on("click", evt=>{
    $(evt.target).parent().hide();
})

$("#colorpicker li").on("click", e=> {
    var val=$(e.target).attr("x-value");
    var trk = $(e.target).parent().parent().attr("x-track");
    if(val && trk) {
        console.log("Choosen color: track="+trk+" color="+val);
        sendToServer({"context": "track-settings", "color": val, "channel": trk});
        $("#colorpicker").hide();
    }
});


var efx1_selection=["Hall 1","Hall 2","Room 1","Plate","Church","DrumAmb","GateRev","Vocal 1","Vocal 2","Vocal 3"];
var efx2_selection=["Hall 3","Room 2","Spring","Delay","Analog","P-P Delay","Vocal 4","Chorus 1","Chorus 2","Chorus+Delay"];
$("document").ready(function() {
    var effect_settings = $('#effect_settings');
    var fx1=$("#effect_settings .fx1");
    var fx2=$("#effect_settings .fx2");

    var html='<div class="name">EFX1</div>';
    html+='<select name="efx1" id="efx0-select">';
    for(var i=0;i<efx1_selection.length;i++) {
        html+='<option value="'+i+'">'+efx1_selection[i]+'</option>';
    }
    html+='</select>';

    html+='<input type="text" value="0" max="100" class="knob fx1_param1">';
    html+='<input type="text" value="0" max="100" class="knob fx1_param2">';

    fx1.html(html)

    html='<div class="name">EFX2</div>';
    html+='<select name="efx2" id="efx1-select">';
    for(var i=0;i<efx2_selection.length;i++) {
        html+='<option value="'+i+'">'+efx2_selection[i]+'</option>';
    }
    html+='</select>';

    html+='<input type="text" value="0" max="100" class="knob fx2_param1">';
    html+='<input type="text" value="0" max="100" class="knob fx2_param2">';

    fx2.html(html)

    var b = new Binding({
        object: effect_data[0],
        property: "effect"
    });
    b.addBinding($("#efx0-select")[0], "value");
    $("#efx0-select").on("change", e=>{
        var val=$(e.target).val();
        sendToServer({"context":"FX", "function":"effect", "value": val, "channel":0});
    });

    b = new Binding({
        object: effect_data[1],
        property: "effect"
    });
    b.addBinding($("#efx1-select")[0], "value");
    $("#efx1-select").on("change", e=>{
        var val=$(e.target).val();
        sendToServer({"context":"FX", "function":"effect", "value": val, "channel":1});
    });

    b = new Binding({
        object: effect_data[0],
        property: "param1"
    });
    b.addBinding($(".fx1_param1")[0], "value");
    b.setTrigger("update");

    b = new Binding({
        object: effect_data[0],
        property: "param2"
    });
    b.addBinding($(".fx1_param2")[0], "value");
    b.setTrigger("update");

    b = new Binding({
        object: effect_data[1],
        property: "param1"
    });
    b.addBinding($(".fx2_param1")[0], "value");
    b.setTrigger("update");

    b = new Binding({
        object: effect_data[1],
        property: "param2"
    });
    b.addBinding($(".fx2_param2")[0], "value");
    b.setTrigger("update");
	b.setIdentifier($(".fx2_param2")[0]);
});


$(function() {
    setTimeout(function() {
        console.log("init knobs");
        $(".knob").knob({
            'displayInput': true,
            'width': 50,
            'height': 50,
            'class': 'cknob',
            'knobColor': '#6c6c6c',
            'knobRadius': 23,

            'change': function(j,v){
                /*data.eq.eq_mid=v;
                var svg=$('.eq').svg('get');
                svg.clear(); drawEq(svg);*/
                //console.log("Knob change: "+v,j);
                return true;
            }
        });
    }, 100);
});