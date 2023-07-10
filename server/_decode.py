from _spec import *


# convert json dict to bytearray (without DATA_PREFIX)
def convert_to_bytes(data):
    channel = int(data["channel"])
    control = get_CC_from_track_data(data)
    value = get_Value_from_track_data(control, data)
    print("control=", control)
    return bytearray([channel + MIDI_CC_BASE, control, value])

# convert json dict to control value
def get_CC_from_track_data(data):
    if "mute" in data:
        return MIDI_CC_TRACK_MUTE
    if "solo" in data:
        return MIDI_CC_TRACK_SOLO
    if "rec" in data:
        return MIDI_CC_TRACK_REC
    
    group = int(data["group"])
    if group >= 0 and group < len(MIDI_CC_TRACK_GROUPS):
        return MIDI_CC_TRACK_GROUPS[group]
    return 0

# convert json dict (and control value) to value value
def get_Value_from_track_data(cc, data):
    value = int(data.get("value", "0"))
    if "mute" in data:
        value = int(data["mute"])
    if "solo" in data:
        value = int(data["solo"])
    if "rec" in data:
        value = int(data["rec"])
    return value

# converts Midi message to json for the client
def message2obj(message):
    # map for client:
    func = None
    context= None
    group = None
    if message.type == MIDI_CC and message.control == MIDI_CC_TRACK_VOLUME:
        func="volume"
        context="track"
        group=0
    elif message.type == MIDI_CC and message.control == MIDI_CC_TRACK_VOLUME_A:
        func="volume"
        context="track"
        group=1
    elif message.type == MIDI_CC and message.control == MIDI_CC_MASTER_VOLUME and message.channel == MIDI_CHAN_MASTER_VOLUME:
        func="volume"
        context="main"
    return { "command": { "type": message.type, "channel": message.channel, "control": message.control, "value": message.value, "function": func, "context": context, "group": group } }


def decode_sysex_message(sysex_data : bytearray):
    num_tracks=18
    fx_tracks=2
    offset=9
    line_len=9
    i = offset

    command = {"function":"track-info", "tracks": []}

    buffer=bytearray()
    while i < len(sysex_data):
        #print(sysex_data[i])
        buffer.append(sysex_data[i])
        if (i - offset) % line_len == 0:
            print(buffer)
            #d = " ".join(hex(n) for n in buffer)
            #print(d)
            buffer.clear()
        i += 1

    # track names:
    for i in range(0, num_tracks):
        f=offset + i*line_len
        t=f+line_len
        d=sysex_data[f:t]
        command["tracks"].append({"number": i, "name": d.decode().replace("\x00",""), "color": 0, "mute": 0, "solo": 0})

    # two FX
    command["tracks"].append({"number":19, "name": "FX1", "color": 0, "mute": 0, "solo": 0})
    command["tracks"].append({"number":20 "name": "FX2", "color": 0, "mute": 0, "solo": 0})

    # track colors:
    offset += num_tracks*line_len #18 namedd tracks
    for i in range(0, num_tracks-1):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["color"]=int(d)

    # yet unknown:
    offset += num_tracks

    # mute
    offset += num_tracks+fx_tracks #18 tracks + 2 fx - MASTER?
    for i in range(0, num_tracks+fx_tracks-1):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["mute"]=int(d)

    # solo
    offset += num_tracks+fx_tracks
    for i in range(0, num_tracks+fx_tracks-1):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["solo"]=int(d)

    return { "command": command }