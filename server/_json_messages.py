from _spec import *

# converts Midi message to a json message for the client
def create_json_message(message):
    # map for client:
    func = None
    context= None
    group = None
    chan = message.channel

    if message.type == MIDI_CC:

        # Volume for tracks 1-16:
        for i in range(0, len(MIDI_CC_TRACK_GROUPS)):
            grp = MIDI_CC_TRACK_GROUPS[i]
            if message.control == grp:
                func="volume"
                context="track"
                group=i
                break

        # Volume for stereo tracks 17-20:
        for i in range(0, len(MIDI_CC_TRACK_ST_GROUPS)):
            grp = MIDI_CC_TRACK_ST_GROUPS[i]
            if message.control == grp:
                func="volume"
                context="track"
                group=i
                chan=16+message.channel
                break

        # track mute:
        if message.control == MIDI_CC_TRACK_MUTE:
            func="mute"
            context="track"
        # track mute: (stereo tracks)
        elif message.control == MIDI_CC_TRACK_MUTE2:
            chan+=16;
            func="mute"
            context="track"
        # track solo
        elif message.control == MIDI_CC_TRACK_SOLO:
            func="solo"
            context="track"
        # track solo (stereo tracks)
        elif message.control == MIDI_CC_TRACK_SOLO2:
            chan += 16
            func="solo"
            context="track"
        # track rec/play
        elif message.control == MIDI_CC_TRACK_REC:
            func="rec"
            context="track"
        # track rec/play (stereo tracks)
        elif message.control == MIDI_CC_TRACK_REC2:
            chan += 16
            func="rec"
            context="track"

        # master volume:
        elif message.control == MIDI_CC_MASTER_VOLUME and message.channel == MIDI_CHAN_MASTER_VOLUME:
            func="volume"
            context="main"
        # master mute:
        elif message.control == MIDI_CC_MASTER_MUTE and message.channel == MIDI_CHAN_MASTER_MUTE:
            func="mute"
            context="main"
        elif message.control == MIDI_CC_MASTER_REC:
            func="rec"
            context="main"
        
        # FX channels
         # Volume for tracks 1-16:
        for c in range(0, len(MIDI_CC_FX_GROUPS)):
            grp = MIDI_CC_FX_GROUPS[c]
            ch = MIDI_CHAN_FX_GROUPS[c]
            ch2=ch+1
            if message.control == grp and (message.channel == ch or message.channel == ch2): 
                func="volume"
                context="FXtrack"
                group=c
                chan = chan - ch # client wants channel 0/1
                break
        if message.control == MIDI_CC_FX:
            context="FXtrack"
            if message.channel == MIDI_CHAN_FX1_MUTE:
                func="mute"
                chan=0
            elif message.channel == MIDI_CHAN_FX2_MUTE:
                func="mute"
                chan=1
            elif message.channel == MIDI_CHAN_FX1_SOLO:
                func="solo"
                chan=0
            elif message.channel == MIDI_CHAN_FX2_SOLO:
                func="solo"
                chan=1
        elif message.control == MIDI_CC_FX_EFFECT:
            context="FX"

        # monitor volume:
        elif message.control == MIDI_CC_MONITOR:
            func="volume"
            context="monitor"

    return { "command": { "type": message.type, "channel": chan, "control": message.control, "value": message.value, "function": func, "context": context, "group": group } }
