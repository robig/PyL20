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
        # track solo
        elif message.control == MIDI_CC_TRACK_SOLO:
            func="solo"
            context="track"
        # track rec/play
        elif message.control == MIDI_CC_TRACK_REC:
            func="rec"
            context="track"

        # master volume:
        elif message.control == MIDI_CC_MASTER_VOLUME and message.channel == MIDI_CHAN_MASTER_VOLUME:
            func="volume"
            context="main"

    return { "command": { "type": message.type, "channel": chan, "control": message.control, "value": message.value, "function": func, "context": context, "group": group } }
