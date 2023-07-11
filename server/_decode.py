from _spec import *


# convert json dict message to bytearray (without DATA_PREFIX)
def convert_to_bytes(data):
    channel = 0
    control = 0
    value = 0
    if data["context"] == "track":
        control = get_CC_from_track_data(data)
        value = get_Value_from_track_data(control, data)
        channel = int(data["channel"])
    elif data["context"] == "main":
        print("main")
        control = get_CC_from_main_data(data)
        channel = int(data["channel"])
        value = int(data["value"])

    print("MIDI message built: ", [channel, control, value])
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
    if data["channel"]>15: #ther can only be 16 channels (0..15)
        print("channel16", data["channel"])
        data["channel"]=data["channel"]-16
        print("channel now", data["channel"])
        if group >= 0 and group < len(MIDI_CC_TRACK_ST_GROUPS):
            return MIDI_CC_TRACK_ST_GROUPS[group]
    else:
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

# convert json dict to control value (for main/master section)
def get_CC_from_main_data(data):
    if data["channel"] == 0: #master
        channel = MIDI_CHAN_MASTER_VOLUME # main channel starts at 10
        return MIDI_CC_MASTER_VOLUME
    

    return MIDI_CC_MASTER_VOLUME #fallback

def print_hex_line(data : bytearray):
    res = ' '.join(format(x, '02x') for x in data)
    print("%s %s" % (res, data))

def get_hex_line(data : bytearray):
    res = ' '.join(format(x, '02x') for x in data)
    return f"{res} {data}"

def raw_decode_sysex_message(sysex_data : bytearray):
    offset=9
    line_len=9
    i = 0
    ret=""
    buffer=bytearray()
    while i < len(sysex_data):
        buffer.append(sysex_data[i])
        if i>0 and (i) % line_len == 0:
            ret += get_hex_line(buffer) + "\n"
            buffer.clear()
        i += 1
    return ret


def decode_sysex_message(sysex_data : bytearray):
    sysex_type=sysex_data[1]
    if sysex_type == MIDI_SYSEX_TRACK_INFO:
        return decode_sysex_track_info(sysex_data)
    print("Unknown SysEx message type: "+str(sysex_type))
    return {"info": "unknown sysex message received"}

def decode_sysex_track_info(sysex_data : bytearray):
    num_tracks=18
    num_groups=7
    fx_tracks=2
    offset=9
    line_len=9
    i = offset

    command = {"function":"track-info", "tracks": [], "master": {"value": 0}}

    buffer=bytearray()
    while i < len(sysex_data):
        #print(sysex_data[i])
        buffer.append(sysex_data[i])
        if i>offset and (i - offset) % line_len == 0:
            print("%d %s" % (i,get_hex_line(buffer) ))
            buffer.clear()
        i += 1

    # track names:
    for i in range(0, num_tracks):
        f=offset + i*line_len
        t=f+line_len
        d=sysex_data[f:t]
        command["tracks"].append({"number": i, "name": d.decode('utf8', errors='ignore').replace("\x00",""), "color": 0, "mute": 0, "solo": 0, "values":[]})

    # two FX
    command["tracks"].append({"number":19, "name": "FX1", "mute": 0, "solo": 0, "value":0})
    command["tracks"].append({"number":20, "name": "FX2", "mute": 0, "solo": 0, "value":0})

    # track colors:
    offset += num_tracks*line_len #18 namedd tracks
    for i in range(0, num_tracks-1):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["color"]=int(d)

    # yet unknown:
    offset += num_tracks

    # mute
    offset += num_tracks #18 tracks
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

    # track volumes start on line 47
    offset=47*line_len + 4
    for g in range(0, num_groups):
        for i in range(0, num_tracks-1):
            f=offset + i
            d=sysex_data[f]
            command["tracks"][i]["values"].append(int(d))
        offset+=num_tracks

    # master volume (at line 64 + 4byte)
    offset = 47*line_len
    d=sysex_data[offset]
    command['master']['value']=int(d)

    return { "command": command }