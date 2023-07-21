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
    elif data["context"] == "FXtrack":
        control = get_CC_from_FXtrack_data(data)
        value = get_Value_from_track_data(control, data)
        channel = int(data["channel"])
    elif data["context"] == "main":
        control = get_CC_from_main_data(data)
        channel = int(data["channel"])
        print("main: channel=",channel, "cc=",control)
        value = int(data["value"])
    elif data["context"] == "monitor":
        control = get_CC_from_monitor_data(data)
        channel = int(data["channel"])
        value = int(data["value"])
    elif data["context"] == "track-settings":
        return create_sysex_track_settings(data)

    print("MIDI message built: ", [channel, control, value])
    if channel == 0 and control == 0:
        raise Exception("Invalid MIDI")
    return bytearray([channel + MIDI_CC_BASE, control, value])

def need_sysex_end_message(data):
    if data["context"] == "track-settings" and data.get("name"):
        return True

    return False

# convert json dict to control value
def get_CC_from_track_data(data):
    if "mute" in data:
        if data["channel"]>15:
            data["channel"]-=16
            return MIDI_CC_TRACK_MUTE2
        return MIDI_CC_TRACK_MUTE
    if "solo" in data:
        if data["channel"]>15:
            data["channel"]-=16
            return MIDI_CC_TRACK_SOLO2
        return MIDI_CC_TRACK_SOLO
    if "rec" in data:
        if data["channel"]>15:
            data["channel"]-=16
            return MIDI_CC_TRACK_REC2
        return MIDI_CC_TRACK_REC
    if "function" in data:
        func = data["function"]
        if data["channel"] > 15:
            data["channel"]-=16
            if func in WS_FUNCTION_TO_TRACK_CC2:
                return WS_FUNCTION_TO_TRACK_CC2[func]
                
        if func in WS_FUNCTION_TO_TRACK_CC:
            return WS_FUNCTION_TO_TRACK_CC[func]
    
    group = int(data["group"])
    if data["channel"]>15: #there can only be 16 channels (0..15)
        #print("channel16", data["channel"])
        data["channel"]=data["channel"]-16
        #print("channel now", data["channel"])
        if group >= 0 and group < len(MIDI_CC_TRACK_ST_GROUPS):
            return MIDI_CC_TRACK_ST_GROUPS[group]
    else:
        if group >= 0 and group < len(MIDI_CC_TRACK_GROUPS):
            return MIDI_CC_TRACK_GROUPS[group]
    return 0

# convert json dict to control value
def get_CC_from_FXtrack_data(data):
    # all channel data use the same CC:
    cc=MIDI_CC_FX
    if "mute" in data:
        data["channel"] = data["channel"] + MIDI_CHAN_FX1_MUTE
        return cc
    if "solo" in data:
        data["channel"] = data["channel"] + MIDI_CHAN_FX1_SOLO
        return cc
    
    if "effect" in data:
        #keep channel 0/1
        return MIDI_CC_FX_EFFECT
    
    # channel volume
    group = int(data["group"])
    if group >= 0 and group < len(MIDI_CHAN_FX_GROUPS):
        data["channel"] = data["channel"] + MIDI_CHAN_FX_GROUPS[group]
    if group >= 0 and group < len(MIDI_CC_FX_GROUPS):
        return  MIDI_CC_FX_GROUPS[group]

    # master channel
    data["channel"] = data["channel"] + MIDI_CHAN_FX1 # channel 0/1 -> 12/13
    return cc

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
    if "mute" in data:
        data["value"] = data.get("mute")
        return MIDI_CC_MASTER_MUTE
    if "rec" in data:
        data["value"] = data.get("rec")
        return MIDI_CC_MASTER_REC

    return MIDI_CC_MASTER_VOLUME #fallback

# convert json dict to control value (for monitor section)
def get_CC_from_monitor_data(data):
    return MIDI_CC_MONITOR

def print_hex_line(data : bytearray):
    res = ' '.join(format(x, '02x') for x in data)
    print("%s %s" % (res, data))

def get_hex_line(line: int, data : bytearray):
    res = ' '.join(format(x, '02x') for x in data)
    return f"{line:03d} {res} {data}"

def raw_decode_sysex_message(sysex_data : bytearray):
    offset=9
    line_len=9
    i = 0
    ret=""
    buffer=bytearray()
    while i < len(sysex_data):
        buffer.append(sysex_data[i])
        if i>0 and (i) % line_len == 0:
            ret += get_hex_line(i, buffer) + "\n"
            buffer.clear()
        i += 1
    return ret


def decode_sysex_message(sysex_data : bytearray):
    sysex_type=sysex_data[1:5]
    if sysex_type == MIDI_SYSEX_TRACK_INFO:
        return decode_sysex_track_info(sysex_data)
    sysex_type=sysex_data[1:6]
    if sysex_type == MIDI_SYSEX_TRACK_COLOR:
        return decode_sysex_track_color(sysex_data)
    if sysex_type == MIDI_SYSEX_TRACK_RENAME:
        return decode_sysex_track_rename(sysex_data)
    print("Unknown SysEx message type: "+str(sysex_type))
    return None

def decode_sysex_track_color(sysex_data : bytearray):
    offset=6
    chan = int(sysex_data[offset]) -1
    color = int(sysex_data[offset + 1])
    print(f"Received track color change: #{chan}: color={color}")
    return { "command": {"function": "color", "channel": chan, "value": color} }

def decode_sysex_track_rename(sysex_data : bytearray):
    offset=6
    chan = int(sysex_data[offset]) -1
    offset+=1
    end=offset+9
    d = sysex_data[offset:end]
    newname=d.decode('ascii', errors='ignore').replace("\x00","")
    print(f"Received track rename: #{chan}: name={newname}")
    return { "command": {"function": "rename", "channel": chan, "name": newname} }

def decode_sysex_track_info(sysex_data : bytearray):
    num_tracks=18
    num_groups=7
    fx_tracks=2
    offset=9
    line_len=9
    i = offset

    command = {"function":"track-info", "tracks": [], "master": {"value": 0, "mute": 0}, "monitor": []}

    buffer=bytearray()
    while i < len(sysex_data):
        #print(sysex_data[i])
        buffer.append(sysex_data[i])
        if i>offset and (i - offset) % line_len == 0:
            print(get_hex_line(i, buffer) )
            buffer.clear()
        i += 1

    # track names:
    for i in range(0, num_tracks):
        f=offset + i*line_len
        t=f+line_len
        d=sysex_data[f:t]
        command["tracks"].append({"number": i, "name": d.decode('ascii', errors='ignore').replace("\x00",""), "color": 0, "mute": 0, "solo": 0, "values":[], "eq": {}})

    # two FX
    command["tracks"].append({"number":18, "name": "FX1", "mute": 0, "solo": 0, "values":[]})
    command["tracks"].append({"number":19, "name": "FX2", "mute": 0, "solo": 0, "values":[]})

    # track colors:
    offset += num_tracks*line_len #18 namedd tracks
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["color"]=int(d)

    # yet unknown:
    offset += num_tracks

    # mute
    offset += num_tracks #18 tracks
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["mute"]=int(d)

    # solo
    offset += num_tracks
    for i in range(0, num_tracks+fx_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["solo"]=int(d)

    # REC
    offset = 21 * line_len
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["rec"]=int(d)

    # EQ: phase
    offset = 27 * line_len
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["eq"]["phase"]=int(d)
    # EQ: PAN
    offset = 29 * line_len
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["eq"]["pan"]=int(d)

    # EQ: Off
    offset = 31 * line_len
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["eq"]["eq_off"]=int(d)
    # EQ: High
    offset = 33 * line_len
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["eq"]["eq_high"]=int(d)
    # EQ: MidFrq
    offset = 35 * line_len
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["eq"]["eq_mid_frq"]=int(d)
    # EQ: MidGain
    offset = 37 * line_len
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["eq"]["eq_mid"]=int(d)
    # EQ: Low
    offset = 39 * line_len
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["eq"]["eq_low"]=int(d)
    # EQ: LowCut
    offset = 41 * line_len
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["eq"]["eq_lowcut"]=int(d)
    # EQ: EFX1
    offset = 43 * line_len
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["eq"]["fx1"]=int(d)
    # EQ: EFX2
    offset = 45 * line_len
    for i in range(0, num_tracks):
        f=offset + i
        d=sysex_data[f]
        command["tracks"][i]["eq"]["fx2"]=int(d)

    # track volumes start on line 47
    offset=47*line_len
    for g in range(0, num_groups):
        for i in range(0, num_tracks):
            f=offset + i
            d=sysex_data[f]
            #print("track g=",g," i=", i, " d=", int(d))
            command["tracks"][i]["values"].append(int(d))
        offset+=num_tracks

    # FX mute
    offset = 62*line_len+1
    for i in range(2):
        ti=num_tracks+i
        f=offset + i
        d=sysex_data[f]
        command["tracks"][ti]["mute"]= int(d)
    # FX solo
    offset = 62*line_len+3
    for i in range(2):
        ti=num_tracks+i
        f=offset + i
        d=sysex_data[f]
        command["tracks"][ti]["solo"]= int(d)
    # FX levels on line 62
    offset = 62*line_len + 5
    for g in range(0, num_groups):
        for i in range(2):
            ti=num_tracks+i
            f=offset + 2*g + i
            d=sysex_data[f]
            #print("FX",ti, "g=",g," i=", i, " d=", int(d), " offsets", 2*g+i, " offset=",f)
            command["tracks"][ti]["values"].append(int(d))

    # master mute
    offset = 64*line_len + 2
    d=sysex_data[offset]
    command['master']['mute']=int(d)

    # master volume (at line 64) followed by monitor volumes
    offset = 64*line_len + 3
    d=sysex_data[offset]
    command['master']['value']=int(d)
    for i in range(1, num_groups):
        f=offset + i
        d=sysex_data[f]
        command['monitor'].append(int(d))

    return { "command": command }

def create_sysex_track_settings(data):
    if data.get("name"):
        value = bytes(data["name"], 'ascii')
        chan = int(data["channel"]) + 1
        if chan>16: chan+=1 # stereo channel 17/18 occupies index 16/17
        color = 0
        if "color" in data:
            color = int(data["color"])
        sysex = bytearray(b"\xF0\x52\x00\x00\x31\x02\x02\x09\x00" + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00")

        print("Building sysex message... from", sysex)
        sysex[6] = chan
        print("+channel                      ", sysex)
        sysex[8] = color
        print("+color                        ", sysex)
        for i in range(9, 18):
            if len(value) > i-9:
                sysex[i] = value[i-9]

        print("sysex:                        ", sysex)
        return sysex
    if data.get("color"):
        sysex = bytearray(b"\xF0\x52\x00\x00\x31\x03\x02\x06\x80\xF7")
        chan = int(data["channel"])+1
        color= int(data["color"])
        sysex[6] = chan
        sysex[7] = color 

    return sysex

