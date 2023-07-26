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
        # track pan
        elif message.control == MIDI_CC_TRACK_PAN or message.control == MIDI_CC_TRACK_PAN2:
            if message.control == MIDI_CC_TRACK_PAN2: chan += 16
            func = "pan"
            context = "track"
        # track FX sends
        elif message.control == MIDI_CC_TRACK_FX1 or message.control == MIDI_CC_TRACK_FX1_2:
            if message.control == MIDI_CC_TRACK_FX1_2: chan += 16
            func = "efx1"
            context = "track"
        elif message.control == MIDI_CC_TRACK_FX2 or message.control == MIDI_CC_TRACK_FX2_2:
            if message.control == MIDI_CC_TRACK_FX2_2: chan += 16
            func = "efx2"
            context = "track"
        # track EQ
        elif message.control == MIDI_CC_TRACK_EQ_OFF or message.control == MIDI_CC_TRACK_EQ_OFF2:
            func = "eq_off"
            context = "track"
            if message.control == MIDI_CC_TRACK_EQ_OFF2: chan += 16
        elif message.control == MIDI_CC_TRACK_EQ_LOW or message.control == MIDI_CC_TRACK_EQ_LOW2:
            func = "eq_low"
            context = "track"
            if message.control == MIDI_CC_TRACK_EQ_LOW2: chan += 16
        elif message.control == MIDI_CC_TRACK_EQ_LOWCUT or message.control == MIDI_CC_TRACK_EQ_LOWCUT2:
            func = "eq_lowcut"
            context = "track"
            if message.control == MIDI_CC_TRACK_EQ_LOWCUT2: chan+=16
        elif message.control == MIDI_CC_TRACK_EQ_MID or message.control == MIDI_CC_TRACK_EQ_MID2:
            func = "eq_mid"
            context = "track"
            if message.control == MIDI_CC_TRACK_EQ_MID2: chan+=16
        elif message.control == MIDI_CC_TRACK_EQ_MID_FRQ or message.control == MIDI_CC_TRACK_EQ_MID_FRQ2:
            func = "eq_mid_frq"
            context = "track"
            if message.control == MIDI_CC_TRACK_EQ_MID_FRQ2: chan+=16
        elif message.control == MIDI_CC_TRACK_EQ_HIGH or message.control == MIDI_CC_TRACK_EQ_HIGH2:
            func = "eq_high"
            context = "track"
            if message.control == MIDI_CC_TRACK_EQ_HIGH2: chan+=16
        elif message.control == MIDI_CC_TRACK_EQ_PHASE or message.control == MIDI_CC_TRACK_EQ_PHASE2:
            func = "phase"
            context = "track"
            if message.control == MIDI_CC_TRACK_EQ_PHASE2: chan+=16

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
            func="effect"

        # monitor volume:
        elif message.control == MIDI_CC_MONITOR:
            func="volume"
            context="monitor"

    return { "command": { "type": message.type, "channel": chan, "control": message.control, "value": message.value, "function": func, "context": context, "group": group } }
