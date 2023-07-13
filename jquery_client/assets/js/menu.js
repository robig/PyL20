$("#menu .channel").on("click", e => {
    $("#channel_settings").toggle();
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
