//webkitURL is deprecated but nevertheless

// load config
jQuery.getJSON( "config.json", function( data ) {
	console.log(data);
	
	onLoad(data);
}
);

function onLoad(config) {
	var channelCount = config.channels.count;

	var mixer = $('#mixer');
	var trackTemplate = $('template#track_tpl').html();
	for(var i=0; i<channelCount; i++) {
		var t = mixer.append(trackTemplate);
		t.addClass("track"+(i+1));
	}

	connect();
}

var socket = null;
function connect() {
	socket = new WebSocket('ws://localhost:5000');
	socket.addEventListener('open', function (event) {
	    socket.send('Hi!');
	});
	 
	socket.addEventListener('message', function (event) {
	    console.log(event.data);
		var json = JSON.parse(event.data)
		if(json.command) {
			parseIncomingCommand(json.command);
		}
	});
	 
	socket.onclose = function(e) {
		console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
		setTimeout(function() {
			connect();
		}, 1000);
	};
	socket.onerror = function(err) {
		console.error('Socket encountered error: ', err.message, 'Closing socket');
		socket.close();
	};
}

function parseIncomingCommand(cmd) {
	if(cmd.function == "volume") console.log("Volume: "+cmd.value);
}

$(window).keypress(function (e) {
  if (e.key === ' ' || e.key === 'Spacebar') {
    // ' ' is standard, 'Spacebar' was used by IE9 and Firefox < 37
    e.preventDefault()
    console.log('Space pressed');
	socket.send("SPACE");
  }
})
function startRecording() {
	console.log("recordButton clicked");
	playTake();
 	/*
    	Disable the record button until we get a success or fail from getUserMedia() 
	*/

	recording=true;
	recordButton.disabled = true;
	stopButton.disabled = true;
	pauseButton.disabled = true
	playButton.disabled = true;
            
	vocals = null;
	module.sync('record', backingInstance, null, function(ret) {
		console.log("Sync recording started:", ret);
		document.getElementById("formats").innerHTML="Recording: 1 channel pcm @ "+ret.sampleRate/1000+"kHz"
		recordButton.disabled = true;
		stopButton.disabled = false;
		//pauseButton.disabled = false
		playButton.disabled = true;
	});

}

function pauseRecording(){
	console.log("pauseButton clicked rec.recording=",rec.recording );
	if (rec.recording){
		//pause
		if(rec && recording) rec.stop();
		sample.pause();
		pauseButton.innerHTML="Resume";
	}else{
		//resume
		if(rec && recording) rec.record()
		sample.play();
		pauseButton.innerHTML="Pause";
	}
}

function stopRecording() {
	console.log("stopButton clicked");
    module.stop(backingInstance);
	playing=false;

	//disable the stop button, enable the record too allow for new recordings
	stopButton.disabled = true;
	recordButton.disabled = false;
	pauseButton.disabled = true;
	playButton.disabled = false;
	playSyncButton.disabled=false;

	//reset button just in case the recording is stopped while paused
	pauseButton.innerHTML="Pause";

	if(!recording) return;
	//tell the recorder to stop the recording
	recording=false;
	module.recordStop(function(buffers) {
		// calculate filled version for looping playback
		vocalsBuffers = buffers;
		vocalsRecording = module.createBuffer(vocalsBuffers, 2);
		vocalsOffset = module.getOffset(vocalsRecording, backingOriginal, offset);
		vocals = module.offsetBuffer(vocalsBuffers, vocalsOffset.before, vocalsOffset.after);

		document.getElementById("formats").innerHTML="Recording stopped. "+vocals.duration;
		module.recorder.exportWAV(createDownloadLink);
	});

	//stop microphone access
	//gumStream.getAudioTracks()[0].stop();

	//create the wav blob and pass it on to createDownloadLink
	//rec.exportWAV(createDownloadLink);
	
}

function playTake() {
	playing=true;
	backingInstance = module.play(backing);
	backingOriginal = backingInstance;

	stopButton.disabled=false;
	playButton.disabled=true;
	recordButton.disabled=true;
}

function playSync() {
	playingSync=true;	
	module.sync('play', backingInstance, vocals, function (data) {
		vocalsInstance = data;
	});
}

var debug=null;
function createDownloadLink(blob) {
	
	var url = URL.createObjectURL(blob);
	var au = document.createElement('audio');
	var li = document.createElement('li');
	var link = document.createElement('a');

	//name of .wav file to use during upload and download (without extendion)
	var filename = new Date().toISOString()+"_"+recorderName+".wav";

	//add controls to the <audio> element
	au.controls = true;
	au.src = url;

	//save to disk link
	link.href = url;
	link.download = filename; //download forces the browser to donwload the file using the  filename
	link.innerHTML = "Download";

	//add the new audio element to li
	li.appendChild(au);
	
	//add the filename to the li
	li.appendChild(document.createTextNode(filename))

	//add the save to disk link to li
	li.appendChild(link);
	
	//upload link
	var upload = document.createElement('a');
	upload.href="#";
	upload.innerHTML = "Upload";
	upload.addEventListener("click", function(event){
		upload(blob, filename);
	});
	if(uploadDirectly)
		upload(blob, filename);
	else {
		li.appendChild(document.createTextNode (" "))//add a space in between
		li.appendChild(upload)//add the upload link to li
	}
	

	var del = document.createElement("a");
	del.href="#";
	del.innerHTML="Löschen";
	del.addEventListener("click", function(event){
		$(event.srcElement).closest('li').remove();
	});
	li.appendChild(document.createTextNode (" "))//add a space in between
	li.appendChild(del);

	var play = document.createElement("a");
	play.href="#";
	play.innerHTML="Play L/R";
	play.addEventListener("click", function(event){
		if(recording || playing) stopRecording();
		merge(); return;
		var li=$(event.srcElement).closest('li');
		var pl=$(li).find('audio')[0];
		//merge(pl); return;
		console.log(pl);
		sample.currentTime=0;
		pl.currentTime=0;
		sample.play();
		pl.volume=0;
		pl.play();
		stopButton.disabled=false;
    	recordButton.disabled = true;
		playButton.disabled=true;
		setTimeout(function() {
			pl.currentTime=sample.currentTime;
			pl.volume=1;
		},250);
	});
	li.appendChild(document.createTextNode (" "))//add a space in between
	li.appendChild(play);

	//add the li element to the ol
	recordingsList.appendChild(li);
}

function upload(blob, filename) {
	var xhr=new XMLHttpRequest();
	xhr.onload=function(e) {
	  console.log("Server returned: ",e.target.responseText);
	  if(this.statue!== 200) {
		  error_message("Upload Fehler! Server returned: ",e.target.responseText);
	  }
	  else {
		  $(upload).hide();
		ok_message("Upload erfolgreich");
	  }
	};
	var fd=new FormData();
	fd.append("audio_data",blob, filename);
	xhr.open("POST","upload.php",true);
	xhr.send(fd);
}

function changeVolume(el) {
  var volume = element.value;
  var fraction = parseInt(element.value) / parseInt(element.max);
  // Let's use an x*x curve (x-squared) since simple linear (x) does not
  // sound as good.
  module.gainNode.gain.value = fraction * fraction;
}

function ok_message(txt) {
	$('#formats').innerText=txt;
}
function error_message(txt) {
	$('#formats').innerText=txt;
}
