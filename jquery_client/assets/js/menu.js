$("#menu .channel").on("click", e => {
    $("#channel_settings").toggle();
    $("#effect_settings").hide();
});

$("#menu .effects").on("click", e => {
    
    $("#channel_settings").hide();
    $("#effect_settings").toggle();
});


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


var efx1_selection=["Hall1","Hall2","Room1","Plate","Church","DrumAmb","GateRev","Vocal 1","Vocal 2","Vocal 3"];
$("document").ready(function() {
    var effect_settings = $('#effect_settings');
    var fx1=$("#effect_settings .fx1");
    var fx2=$("#effect_settings .fx2");

    var html='<select name="efx1" id="efx0-select">';
    for(var i=0;i<efx1_selection.length;i++) {
        html+='<option value="'+i+'">'+efx1_selection[i]+'</option>';
    }
    html+='</select>';
    fx1.html(html)
});
