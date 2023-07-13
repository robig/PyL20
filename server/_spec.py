MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
BLE_MIDI_UUID  = "7772E5DB-3868-4112-A1A9-F2669D106BF3"

DATA_PREFIX=b"\x80\x80"

MIDI_CC_BASE=176
MIDI_CC="control_change"
MIDI_CC_TRACK_VOLUME=60     # master for track1-16 value 0-120
MIDI_CC_TRACK_VOLUME_A=62   # value 0-120
MIDI_CC_TRACK_VOLUME_B=64   # value 0-120
MIDI_CC_TRACK_VOLUME_C=66   # value 0-120
MIDI_CC_TRACK_VOLUME_D=68   # value 0-120
MIDI_CC_TRACK_VOLUME_E=70   # value 0-120
MIDI_CC_TRACK_VOLUME_F=72   # value 0-120
MIDI_CC_TRACK_ST_VOLUME=61   # for stereo tracks 17/18 and 19/20
MIDI_CC_TRACK_ST_VOLUME_A=63 # for stereo tracks 17/18 and 19/20
MIDI_CC_TRACK_ST_VOLUME_B=65 # for stereo tracks 17/18 and 19/20
MIDI_CC_TRACK_ST_VOLUME_C=67 # for stereo tracks 17/18 and 19/20
MIDI_CC_TRACK_ST_VOLUME_D=69 # for stereo tracks 17/18 and 19/20
MIDI_CC_TRACK_ST_VOLUME_E=71 # for stereo tracks 17/18 and 19/20
MIDI_CC_TRACK_ST_VOLUME_F=73 # for stereo tracks 17/18 and 19/20
MIDI_CC_TRACK_REC=8         # value 0,1,2
MIDI_CC_TRACK_REC2=9        # for stereo tracks
MIDI_CC_TRACK_SOLO=50       # value 0/1
MIDI_CC_TRACK_SOLO2=51      # for stereo tracks
MIDI_CC_TRACK_MUTE=48       # value 0/1
MIDI_CC_TRACK_MUTE2=49      # for stereo tracks 17-20
MIDI_CC_TRACK_EQ_OFF=14     # value 0/1
MIDI_CC_TRACK_EQ_PHASE=10   # value 0/1
MIDI_CC_TRACK_EQ_LOWCUT=46  # value 0-56
MIDI_CC_TRACK_EQ_MID_FRQ=24 # value 0-96
MIDI_CC_TRACK_EQ_MID=26     # value 0-60
MIDI_CC_TRACK_EQ_HIGH=20    # value 0-60
MIDI_CC_TRACK_PAN=12        # value 0-100
MIDI_CC_TRACK_FX1=52        # value 0-60
MIDI_CC_TRACK_FX2=54        # value 0-60
MIDI_CC_MONITOR=83          # value 0-118

MIDI_CC_FX=80 # channel 12 + 13, value 0-120
MIDI_CHAN_FX1=12
MIDI_CHAN_FX2=13
MIDI_CHAN_FX1_MUTE=4 # mute FX1: CC=80 channel=4 value=0/1
MIDI_CHAN_FX2_MUTE=5 # mute FX2: CC=80 channel=5 value=0/1
MIDI_CHAN_FX1_SOLO=8 # solo FX1: CC=80 channel=8 value=0/1
MIDI_CHAN_FX2_SOLO=9 # solo FX2: CC=80 channel=9 value=0/1             
MIDI_CC_FX_EFFECT=78 # FX1: channel=0
                     # FX2: channel=1

MIDI_CC_MASTER_VOLUME  =84
MIDI_CHAN_MASTER_VOLUME=10
MIDI_CC_MASTER_MUTE    =84
MIDI_CHAN_MASTER_MUTE  =9
MIDI_CC_MASTER_REC     =8

MIDI_CC_TRACK_GROUPS=[MIDI_CC_TRACK_VOLUME, MIDI_CC_TRACK_VOLUME_A, MIDI_CC_TRACK_VOLUME_B, MIDI_CC_TRACK_VOLUME_C, MIDI_CC_TRACK_VOLUME_D, MIDI_CC_TRACK_VOLUME_E, MIDI_CC_TRACK_VOLUME_F]
MIDI_CC_TRACK_ST_GROUPS=[MIDI_CC_TRACK_ST_VOLUME, MIDI_CC_TRACK_ST_VOLUME_A, MIDI_CC_TRACK_ST_VOLUME_B, MIDI_CC_TRACK_ST_VOLUME_C, MIDI_CC_TRACK_ST_VOLUME_D, MIDI_CC_TRACK_ST_VOLUME_E, MIDI_CC_TRACK_ST_VOLUME_F]


MIDI_SYSEX_TRACK_INFO=82 # b"\x52" # == 82 dec
MIDI_SYSEX_TRACK_INFO=bytearray(b"\x52\x00\x00\x2a")
MIDI_SYSEX_TRACK_COLOR=bytearray(b"\x52\x00\x00\x31")
CMD_TRACK_INFO=b"\xf0\x52\x00\x00\x2b\x80\xf7" #F052 0000 2B80 F7
MIDI_SYSEX_END=b"\xf7"
MIDI_SYSEX_START=b"\xf0"