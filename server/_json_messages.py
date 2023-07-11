from _spec import *

# converts Midi message to a json message for the client
def create_json_message(message):
    # map for client:
    func = None
    context= None
    group = None

    if message.type == MIDI_CC:

        # Volume for all tracks:
        for i in range(0, len(MIDI_CC_TRACK_GROUPS)):
            grp = MIDI_CC_TRACK_GROUPS[i]
            if message.control == grp:
                func="volume"
                context="track"
                group=i

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

    return { "command": { "type": message.type, "channel": message.channel, "control": message.control, "value": message.value, "function": func, "context": context, "group": group } }
