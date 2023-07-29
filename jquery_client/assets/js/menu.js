$("#menu .channel").on("click", e => {
    $("#channel_settings").toggle();
    $("#effect_settings").hide();
    activateMenu("channel");
});

$("#menu .effects").on("click", e => {
    $("#channel_settings").hide();
    $("#effect_settings").toggle();
    activateMenu("effects");
});

function activateMenu(name) {
    $("#menu li").removeClass("active");
    $("#menu li."+name).addClass("active");
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

    var html='<select name="efx1" id="efx0-select">';
    for(var i=0;i<efx1_selection.length;i++) {
        html+='<option value="'+i+'">'+efx1_selection[i]+'</option>';
    }
    html+='</select>';

    html+='<input type="text" value="0" max="60" class="knob fx1_param1">';
    html+='<input type="text" value="0" max="60" class="knob fx1_param2">';

    fx1.html(html)

    html='<select name="efx2" id="efx1-select">';
    for(var i=0;i<efx2_selection.length;i++) {
        html+='<option value="'+i+'">'+efx2_selection[i]+'</option>';
    }
    html+='</select>';
    fx2.html(html)
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