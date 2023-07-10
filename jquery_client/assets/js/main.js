//webkitURL is deprecated but nevertheless

// load config
var server_url='ws://localhost:5000';
jQuery.getJSON( "config.json", function( data ) {
	console.log(data);
	
	if(data.connection && data.connection.url)
		server_url=data.connection.url;
	onLoad(data);
}
);

var track_data = [];
var main_data = {"master": {"value": 0, "mute": 0, "solo": 0}}
var message_callbacks = [];
var mouseDown=false;
var track_selected = {"group": 0, "track": null};

message_callbacks.push({
	"filter": function(cmd) {
		return cmd.function=="track-info";
	},
	"action": function(cmd) {
		console.log("got a Track Info Response")
		if(cmd.tracks) {
			cmd.tracks.forEach(t => {
				//console.log(t);
				var i = t.number;
				track_data[i].name = t.name;
				track_data[i].color = t.color;
				track_data[i].mute = t.mute;
				track_data[i].solo = t.solo;
			});
		}
	}
})



function onLoad(config) {
	var trackCount = config.tracks.mono.count;
	var groupCount = config.groups.count;
	var groupNames = config.groups.names;
	//var group=0; // todo 0=master group

	// create the track elements:
	var mixer = $('#track_container');
	var trackTemplate = $('template#track_tpl').html();

	for(var i=0; i<trackCount; i++) {
		var t = $(trackTemplate);
		t.appendTo(mixer);
		t.addClass("track"+(i+1));
		t.find(".name").text("CH"+(i+1));
		t.attr("x-track", i);
		t.on("click", function() {
			var trk = $(this).attr("x-track");
			track_selected.track = trk;
			$(this).parent().find(".track").removeClass("selected");
			$(this).addClass("selected");
		});

		track_data[i] = {"name": "CH"+(i+1), "color": 0, "value": 0, "channel": i, "group": g, "mute": 0, "solo": 0, "rec": 0, "groups":[]};

		var groups = $('#main .groups');
		var groupTemplate = $('template#group_tpl').html();

		var trkGroups=t.find(".groups");
		var trkGroupsTemplate=$('template#trk_group').html();
		for(var g=0; g<groupCount; g++) {
			track_data[i].groups[g]={"value": 0};

			// group buttons in main section:
			if(i==0) {
				var grp = $(groupTemplate);
				grp.appendTo(groups);
				grp.text(groupNames[g]);
				grp.attr("x-group", g); // groupID on element
				grp.on("click", function() {
					var gid = $(this).attr("x-group");
					console.log("Activate group: #"+gid+" "+groupNames[gid]);
					$("#main .groups .button").removeClass("active");
					$(this).addClass("active");
					$("#mixer .tab").removeClass("active");
					$("#mixer .tab.group"+gid).addClass("active");
				});
			}
	
			var tab = $(trkGroupsTemplate);
			tab.addClass("group"+g);
			if(g==config.groups.startup) {
				$("body").addClass("activeGroup"+g);
				grp.addClass("active");
				tab.addClass("active");
			}
			tab.appendTo(trkGroups);
			

			var b = new Binding({
				object: track_data[i].groups[g],
				property: "value"
			});
			var elSlider = tab.find(".slider")[0];
			$(elSlider).attr("x-group", g);
			$(elSlider).attr("x-track", i);
			b.addBinding(elSlider, "value", "input");
			elSlider.addEventListener("input", function() {
				//console.log($(this));
				var gid = $(this).attr("x-group");
				var trk = $(this).attr("x-track");
				const now = Date.now();
				if((now - lastChange) > 100 ) { //DEbounce
					lastChange = Date.now();
					sendToServer({"context": "track", "value": track_data[trk].groups[gid].value, "group": gid, "channel": track_data[trk].channel});
				}
			});
			$(elSlider).on('mousedown', function() {mouseDown=true;});
			$(elSlider).on('mouseup', function() {
				mouseDown=false;
				var gid = $(this).attr("x-group");
				var trk = $(this).attr("x-track");
				sendToServer({"context": "track", "value": track_data[trk].groups[gid].value, "group": gid, "channel": track_data[trk].channel});
			});

			var elValue= tab.find(".value")[0];
			b.addMappedBinding(elValue, "innerHTML", function(val) {
				// max  = 120 -> 10
				//        108 -> +5
				// zero =  88 ->  0
				//         68 -> -5
				//         45 -> -10
				//         24 -> -20
				return val;
				var num = val * 10 / 120; // convert midi value to dB

				return Math.round(num * 100) / 100; // round to 2 decimals
			});
			//console.log("Binding setup"+i);
		} // for groups
	
		// MUTE button
		var el = t.find(".mute");
		b = new Binding({
			object: track_data[i],
			property: "mute"
		});
		b.addClassBinding(el[0], "x-value", "value");
		el.on("click", function(event) {
			var trk = $(this).parent().attr("x-track");
			var track = track_data[trk];
			track.mute = (track.mute == 0 ? 1 : 0);
			console.log("mute: "+track.mute);
			sendToServer({"context": "track", "mute": track_data[trk].mute, "channel": track_data[trk].channel});
		});
		message_callbacks.push({
			"filter": function(cmd) {
				return cmd.context=="track" && cmd.function=="mute";
			},
			"action": function(cmd) {
				console.log("MUTE for track #"+trk)
			}
		});

		// SOLO button
		el = t.find(".solo");
		b = new Binding({
			object: track_data[i],
			property: "solo"
		});
		b.addClassBinding(el[0], "x-solo", "solo");
		el.on("click", function(event) {
			var trk = $(this).parent().attr("x-track");
			var track = track_data[trk];
			track.solo = (track.solo == 0 ? 1 : 0);
			if(track.solo==1) {
				$(this).parent().addClass("solo");
			}else{
				$(this).parent().removeClass("solo");
			}
			sendToServer({"context": "track", "solo": track_data[trk].solo, "channel": track_data[trk].channel});
		});

		// REC/PLAY button
		el = t.find(".rec");
		b = new Binding({
			object: track_data[i],
			property: "rec"
		});
		b.addClassBinding(el[0], "x-rec", "rec");
		el.on("click", function(event) {
			var trk = $(this).parent().attr("x-track");
			var track = track_data[trk];
			track.rec = (track.rec == 2 ? 0 : track.rec + 1 );
			sendToServer({"context": "track", "rec": track_data[trk].rec, "channel": track_data[trk].channel});
		});
		
	}

	// create master track binding:
	var t = $(".master.track");
	var b = new Binding({
		object: main_data.master,
		property: "value"
	});
	var elSlider = t.find(".slider")[0];
	b.addBinding(elSlider, "value", "input");
	var elValue= t.find(".value")[0];
	b.addBinding(elValue, "innerHTML");

	// connect to ws server:
	connect();
}

var lastChange = 0;
var lastSent = null;
function sendToServer(data) {
	try {
		console.log("Send to server:", data);
		socket.send(JSON.stringify(data));
		lastSent = data;
	} catch (error) {
		console.error("Sending Failed!", error);
	}
}

function cmdTrackInfo() {
	sendToServer({"cmd": "track_info"});
}

var sending = false;
var socket = null;
function connect() {
	socket = new WebSocket(server_url);
	socket.addEventListener('open', function (event) {
		$('#connection').text("connected");
		$('body').addClass("connected");
		$('body').removeClass("offline");
		$('body').removeClass("closed");
	    //socket.send('Hi!');
		cmdTrackInfo(); // receive track states
	});
	 
	socket.addEventListener('message', function (event) {
	    console.log(event.data);
		var json = JSON.parse(event.data)
		if(json.command) {
			parseIncomingCommand(json.command);
		}else if(json.status) {
			updateStatus(json.status);
		}
	});
	 
	socket.onclose = function(e) {
		$('#connection').text("connection closed");
		$('body').addClass("closed");
		$('body').removeClass("connected");
		$('body').removeClass("offline");
		console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
		setTimeout(function() {
			connect();
		}, 1000);
	};
	socket.onerror = function(err) {
		$('#connection').text("connection failed");
		$('body').removeClass("connected");
		$('body').addClass("offline");
		$('body').removeClass("closed");
		console.error('Socket encountered error: ', err.message, 'Closing socket');
		socket.close();
	};
}

function parseIncomingCommand(cmd) {
	console.log(mouseDown);
	if(cmd.context=="track" && cmd.function == "volume" && !mouseDown) {
		console.log("TrackVolume on group:"+cmd.group);
		if(cmd.group >= 0 && cmd.group < track_data.length) {
			var g = cmd.group;
			for(var i=0; i<track_data[g].length; i++) {
				var t=track_data[g][i];
				if(t.channel == cmd.channel && t.group == cmd.group) {
					t.value = cmd.value;
					console.log("Volume: "+cmd.value);
				}
			}
		}
	}
	for(var i=0;i<message_callbacks.length; i++){
		cb=message_callbacks[i]
		if(cb.filter(cmd)) cb.action(cmd);
	}
	if(cmd.context=="main" && cmd.function == "volume") {
		main_data.master.value = cmd.value;
	}
}

function updateStatus(status) {
	$('#main .status').text(status);
}

$(window).keypress(function (e) {
  if (e.key === ' ' || e.key === 'Spacebar') {
    // ' ' is standard, 'Spacebar' was used by IE9 and Firefox < 37
    e.preventDefault()
    console.log('Space pressed');
	socket.send("SPACE");
  }
});

function ok_message(txt) {
	$('#formats').innerText=txt;
}
function error_message(txt) {
	$('#formats').innerText=txt;
}
