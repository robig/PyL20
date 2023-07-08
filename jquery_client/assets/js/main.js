//webkitURL is deprecated but nevertheless

// load config
jQuery.getJSON( "config.json", function( data ) {
	console.log(data);
	
	onLoad(data);
}
);

var track_data = [];
var main_data = {"master": {"value": 0, "mute": 0, "solo": 0}}
var ignore_incoming=[];
var mouseDown=false;

function onLoad(config) {
	var channelCount = config.channels.count;
	var groupCount = config.groups.count;
	var groupNames = config.groups.names;
	//var group=0; // todo 0=master group

	// create the track elements:
	var mixer = $('#track_container');
	var trackTemplate = $('template#track_tpl').html();

	var groups = $('#main .groups');
	var groupTemplate = $('template#group_tpl').html();
	for(var g=0; g<groupCount; g++) {
		track_data[g]=[]; 
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

		var tab = $("<div class='tab group"+g+"'></div>");
		if(g==config.groups.startup) {
			console.log("Active group: "+g);
			$("body").addClass("activeGroup"+g);
			grp.addClass("active");
			tab.addClass("active");
		}
		tab.appendTo(mixer);

		for(var i=0; i<channelCount; i++) {
			
			var t = $(trackTemplate);
			t.appendTo(tab);
			t.addClass("track"+(i+1));
			t.find(".name").text("CH"+(i+1));

			track_data[g][i] = {"name": "CH"+(i+1), "value": 0, "channel": i, "group": g, "mute": 0, "solo": 0};
			
			var b = new Binding({
				object: track_data[g][i],
				property: "value"
			});
			var elSlider = t.find(".slider")[0];
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
					sendToServer({"context": "track", "value": track_data[gid][trk].value, "group": track_data[gid][trk].group, "channel": track_data[gid][trk].channel});
					//sendToServer(track_data[gid][trk]);
				}
			});
			$(elSlider).on('mousedown', function() {mouseDown=true;});
			$(elSlider).on('mouseup', function() {
				mouseDown=false;
				var gid = $(this).attr("x-group");
				var trk = $(this).attr("x-track");
				sendToServer({"context": "track", "value": track_data[gid][trk].value, "group": track_data[gid][trk].group, "channel": track_data[gid][trk].channel});
			});

			var elValue= t.find(".value")[0];
			b.addBinding(elValue, "innerHTML");
			//console.log("Binding setup"+i);
		}
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

var sending = false;
var socket = null;
function connect() {
	socket = new WebSocket('ws://localhost:5000');
	socket.addEventListener('open', function (event) {
		$('#connection').text("connected");
		$('body').addClass("connected");
		$('body').removeClass("offline");
		$('body').removeClass("closed");
	    socket.send('Hi!');
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
