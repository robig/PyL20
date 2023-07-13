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
var monitorNames = ["A","B","C","D","E","F"];
var main_data = {"master": {"value": 0, "mute": 0, "solo": 0}, "monitor": [{"value":0},{"value":0},{"value":0},{"value":0},{"value":0},{"value":0}]};
var message_callbacks = [];
var mouseDown=false;
var track_selected = {"group": 0, "track": null};

//////////// for debugging/decoding ////////////////
function showDebug(data) {
	console.log(data);
	if(data) $("#debug textarea").val(data);
	$("#debug").show();
}
$("#debug .close").on("click", function() {$(this).parent().hide();});
function printDiff(o1, o2) {
	arr1=o1.split('\n')
	arr2=o2.split('\n')
	ret=[]
	diffLines=[]
	for(var i=0;i<arr1.length && i<arr2.length;i++) {
		var lineNumber = ("00" + i).slice (-3)
		var d = "=";
		if(arr1[i] != arr2[i]) {
			d="+";
			diffLines.push(lineNumber);
			var oldline=lineNumber+" -"+arr1[i];
			ret.push(oldline+"\n");
		}
		var line = lineNumber+" "+d + arr2[i];
		ret.push(line+"\n");
	}
	//$("#debug").html(ret);
	showDebug(ret);
	console.log("lines that are different: "+diffLines.length, diffLines);
	return ret;
}
lastMessage=null;
debugEnabled=false;
message_callbacks.push(
	{
		"filter": function(cmd) {
			return cmd.raw && cmd.raw!= null;
		},
		"action": function(cmd) {
			console.log("got RAW Response");
			if(debugEnabled && lastMessage!=null) {
				printDiff(lastMessage, cmd.raw);
			}

			lastMessage = cmd.raw;
		}
	}
);

////////////////////////////////////////////////////
message_callbacks.push(
	{ // Track Volume chages
		"filter": function(cmd) {
			return cmd.context=="track" && cmd.function == "volume" && !mouseDown;
		},
		"action": function(cmd) {
			if(cmd.group >= 0 && cmd.group < 8) {
				var g = cmd.group;
				var trk = cmd.channel;
				// the two stereo tracks are on channel 16 and 18
				if(trk==18){
					trk=17 // translate chan 18 to index 17
				}
				track_data[trk].groups[g].value=cmd.value;
			}
		}
	}
);
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
				if(track_data[i]) {
					track_data[i].name = t.name;
					track_data[i].color = t.color;
					track_data[i].mute = t.mute;
					track_data[i].solo = t.solo;
					
					if(t.values)
						t.values.forEach((v,num) => {
							//console.log("channel "+num+"="+v);
							track_data[i].groups[num].value = v;
						});
					
				}
			});
		}
		if(cmd.master) {
			main_data.master.value=cmd.master.value;
			main_data.master.mute=cmd.master.mute;
		}
		if(cmd.monitor) {
			for(var i=0; i<main_data.monitor.length && i<cmd.monitor.length;i++) {
				main_data.monitor[i].value = cmd.monitor[i];
			}
		}
	}
});
message_callbacks.push({ // Track MUTE
	"filter": function(cmd) {
		return cmd.context=="track" && cmd.function=="mute";
	},
	"action": function(cmd) {
		var trk=cmd.channel;
		if(trk==18){
			trk=17 // translate chan 18 to index 17
		}
		console.log("MUTE for track #"+trk);
		track_data[trk].mute = cmd.value;
	}
});
message_callbacks.push({ // Track SOLO
	"filter": function(cmd) {
		return cmd.context=="track" && cmd.function=="solo";
	},
	"action": function(cmd) {
		var trk=cmd.channel;
		if(trk==18){
			trk=17 // translate chan 18 to index 17
		}
		console.log("SOLO for track #"+trk);
		track_data[trk].solo = cmd.value;
	}
});
message_callbacks.push({ // Track REC
	"filter": function(cmd) {
		return cmd.context=="track" && cmd.function=="rec";
	},
	"action": function(cmd) {
		var trk=cmd.channel;
		if(trk==18){
			trk=17 // translate chan 18 to index 17
		}
		console.log("REC for track #"+trk);
		track_data[trk].rec = cmd.value;
	}
});
message_callbacks.push({ // MASTER mute
	"filter": function(cmd) {
		return cmd.context=="main" && cmd.function=="mute";
	},
	"action": function(cmd) {
		console.log("MUTE for master track");
		main_data.master.mute=cmd.value;
	}
});
message_callbacks.push({ // MASTER rec
	"filter": function(cmd) {
		return cmd.context=="main" && cmd.function=="rec";
	},
	"action": function(cmd) {
		console.log("REC for master track");
		main_data.master.rec=cmd.value;
	}
});
message_callbacks.push({ // Monitor volume
	"filter": function(cmd) {
		return cmd.context=="monitor" && cmd.function=="volume";
	},
	"action": function(cmd) {
		var mon = monitorNames[cmd.channel];
		console.log("monitor volume received: "+mon);
		main_data.monitor[cmd.channel].value=cmd.value;
	}
});



function onLoad(config) {
	var monoTrackCount = config.tracks.mono.count;
	var stereoTrackCount = config.tracks.stereo.count;
	var fxTrackCount = config.tracks.fx.count;
	var trackCount = monoTrackCount + stereoTrackCount;
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
			$("#channel_settings .tab").removeClass("active");
			$("#channel_settings .tab[x-track="+trk+"]").addClass("active");
		});
		t.find(".number").text(i+1);
		if(i>=monoTrackCount) {
			var tc = 1+monoTrackCount+(i-monoTrackCount)*2;
			t.find(".number").text(tc+"/"+(tc+1));
		}

		track_data[i] = {"name": "CH"+(i+1), "color": 0, "value": 0, "channel": i, "group": g, "mute": 0, "solo": 0, "rec": 0, "groups":[]};

		var elName = t.find(".name")[0];
		var nameBind = new Binding({
			object: track_data[i],
			property: "name"
		});
		nameBind.addBinding(elName, "innerHTML");

		var colorBind = new Binding({
			object: track_data[i],
			property: "color"
		});
		colorBind.addClassBinding(elName, "x-value", "color");

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
				if(g==config.groups.startup) {
					grp.addClass("active");
				}
			}
	
			var tab = $(trkGroupsTemplate);
			tab.addClass("group"+g);
			if(g==config.groups.startup) {
				$("body").addClass("activeGroup"+g);
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
			$(elSlider).bind('mousewheel DOMMouseScroll', function(e) {
				//console.log(e.originalEvent);
				console.log(e.originalEvent.detail);
				var gid = $(this).attr("x-group");
				var trk = $(this).attr("x-track");
				var val=parseInt($(this).val()) - e.originalEvent.detail;
				sendToServer({"context": "track", "value": val, "group": gid, "channel": track_data[trk].channel});
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
			track.rec = (track.rec == 2 ? 0 : 2 );
			sendToServer({"context": "track", "rec": track_data[trk].rec, "channel": track_data[trk].channel});
		});
		

		////////////// CHANNEL SETTINGS ////////////
		var channel_settings = $('#channel_settings');
		var chanSettingsTemplate = $('template#chan_settings_tpl').html();
		var settings = $(chanSettingsTemplate);
		settings.attr("x-track", i);
		settings.appendTo(channel_settings);
		if(i==0) settings.addClass("active");
		var nameRead = settings.find("div.name");
		var nameWrite = settings.find("input.name");
		nameBind.addBinding(nameRead[0], "innerHTML");
		nameBind.addBinding(nameWrite[0], "value");
		colorBind.addClassBinding(settings.find(".color")[0], "x-value", "color");
		nameRead.on("click", e=>{
			$(e.target).hide();
			var nameWrite = $(e.target).parent().find("input.name");
			nameWrite.show();
			nameWrite.focus();
		});
		nameWrite.on("input", e=>{
			var trk = $(e.target).parent().attr("x-track");
			console.log("hide input. trk="+trk);
			track_data[trk].name=e.target.value;
			
			sendToServer({"context": "track", "name": track_data[trk].name, "channel": track_data[trk].channel});
		});
		nameWrite.on('keypress',function(e) {
			if(e.which == 13) {
				var nameWrite=$(e.target);
				var nameRead =nameWrite.parent().find("div.name");
				nameRead.show();
				nameWrite.hide();
			}
		});

	}

	/////////////// MASTER track ///////////////
	var t = $(".master.track");
	var b = new Binding({
		object: main_data.master,
		property: "value"
	});
	var elSlider = t.find(".slider")[0];
	b.addBinding(elSlider, "value", "input");
	var elValue= t.find(".value")[0];
	b.addBinding(elValue, "innerHTML");
	elSlider.addEventListener("input", function() {
		const now = Date.now();
		if((now - lastChange) > 100 ) { //DEbounce
			lastChange = Date.now();
			sendToServer({"context": "main", "value": main_data.master.value, "channel": 10});
		}
	});
	// MUTE button
	var el = t.find(".mute");
	b = new Binding({
		object: main_data.master,
		property: "mute"
	});
	b.addClassBinding(el[0], "x-value", "value");
	el.on("click", function(event) {
		var track = main_data.master;
		track.mute = (track.mute == 0 ? 1 : 0);
		console.log("mute MASTER: "+track.mute);
		sendToServer({"context": "main", "mute": track.mute, "channel": 10});
	});

	////////// MONITOR section ///////////
	
	for(var m=0; m<monitorNames.length;m++) {
		var mon=monitorNames[m];
		var monTemplate=$("#monitor_tpl").html();
		var moni=$(monTemplate);
		moni.appendTo($("#main .monitor"));
		moni.addClass("monitor"+mon);

		var b = new Binding({
			object: main_data.monitor[m],
			property: "value"
		});
		b.addBinding(moni[0], "value", "input");
		b.setIdentifier(mon);
		b.addCallback((val,mon)=>{
			$(".monitor .monitor"+mon).trigger("change"); // required to update UI
			console.log("would sendToServer: "+val);
		});
	}
	$(".knob").fancyknob();

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


var b = new Binding({
	object: track_selected,
	property: "track"
});
b.addCallback(trk=>{
	$(".track").removeClass("selected");
	$(".track.track"+trk).addClass("selected");
	$("#channel_settings .tab").removeClass("active");
	$("#channel_settings .tab[x-track="+trk+"]").addClass("active");
});
$(window).keydown(function (e) {
	console.log("Keydown: '"+e.keyCode+"'");
	if(e.keyCode==39){ // right arrow ->
		if(!track_selected.track) {
			track_selected.track = 0;
		}else{
			track_selected.track ++;
			$('.track_container').scrollTo($("track.track"+track_selected.track)[0], 0.5);
		}
		e.preventDefault();
	}
	if(e.keyCode==37){ // left arrow ->
		if(!track_selected.track) {
			track_selected.track = 0;
		}else{
			track_selected.track --;
			if(track_selected.track<0){
				track_selected.track=track_data.length-1;
			}
		}
		e.preventDefault();
	}
});
$(window).keypress(function (e) {
	console.log("Keypress: '"+e.key+"'");
	if (e.key === ' ' || e.key === 'Spacebar') {
		// ' ' is standard, 'Spacebar' was used by IE9 and Firefox < 37
		e.preventDefault();
		console.log('Space pressed');
	}
});

function ok_message(txt) {
	$('#ok_message').innerText=txt;
}
function error_message(txt) {
	$('#error_message').innerText=txt;
}
