import argparse
import asyncio
import logging
import websockets
import json
from bleak import BleakScanner
from bleak import BleakClient
from bleak import BleakGATTCharacteristic
from mido import Message

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
BLE_MIDI_UUID  = "7772E5DB-3868-4112-A1A9-F2669D106BF3"

DATA_PREFIX=b"\x80\x80"

MIDI_CC_BASE=176
MIDI_CC="control_change"
MIDI_CC_TRACK_VOLUME=60 #master
MIDI_CC_TRACK_VOLUME_A=62
MIDI_CC_TRACK_VOLUME_B=64
MIDI_CC_TRACK_VOLUME_C=66
MIDI_CC_TRACK_VOLUME_D=68
MIDI_CC_TRACK_VOLUME_E=70
MIDI_CC_TRACK_VOLUME_F=72
MIDI_CC_TRACK_REC=54
MIDI_CC_TRACK_SOLO=50
MIDI_CC_TRACK_MUTE=48

MIDI_CC_MASTER_VOLUME=84
MIDI_CHAN_MASTER_VOLUME=10

MIDI_CC_TRACK_GROUPS=[MIDI_CC_TRACK_VOLUME, MIDI_CC_TRACK_VOLUME_A, MIDI_CC_TRACK_VOLUME_B, MIDI_CC_TRACK_VOLUME_C, MIDI_CC_TRACK_VOLUME_D, MIDI_CC_TRACK_VOLUME_E, MIDI_CC_TRACK_VOLUME_F]

CMD_TRACK_INFO=b"\xf0\x52\x00\x00\x2b\x80\xf7" #F052 0000 2B80 F7
MIDI_SYSEX_END=b"\xf7"
MIDI_SYSEX_START=b"\xf0"

# list of connected sockets:
clients=[]

connected_to_device = False
message_queue = asyncio.Queue()
response_queue = asyncio.Queue()
sysex_mode = False

## sysEx message to set channel name:
async def testme2(client):
    print("Set Channel2")
    data = b"\x80\x80\xf0\x52\x00\x00\x31\x02\x02\x09\x00" + b"\x45\x45\x45\x65\x63\x74\x73\x00\x00\xf7"
    print("sending: ", data)
    await client.write_gatt_char(BLE_MIDI_UUID, data)
	#00000000: 5212 0080 80F0 5200 0031 0202 0900 4566  R.....R..1....Ef
	#00000010: 6665 6374 7300 00                        fects..

async def testme(client):
    print("Set Channel1")
    await client.write_gatt_char(BLE_MIDI_UUID, b"\x80\x80\xB0\x3C\x10")
    await asyncio.sleep(1.0)
    await client.write_gatt_char(BLE_MIDI_UUID, b"\x80\x80\xB0\x3C\x21")
    await asyncio.sleep(1.0)
    await client.write_gatt_char(BLE_MIDI_UUID, b"\x80\x80\xB0\x3C\x31")
    await asyncio.sleep(1.0)
    await client.write_gatt_char(BLE_MIDI_UUID, b"\x80\x80\xB0\x3C\x41")
    await asyncio.sleep(1.0)
    await client.write_gatt_char(BLE_MIDI_UUID, b"\x80\x80\xB0\x3C\x51")
    await asyncio.sleep(1.0)
#//  Value: b"\x80\x80\xB0\x3C \x12\x3C\x13"
#// channel for B0

async def send_midi_message_to_mixer(client, message):
    if message.get("raw"):
        await send_raw_message(client, message)
        return
    logger.info("Sending message to mixer: %s", str(message))
    if not client or not client.is_connected:
        logger.info("send_midi_message_to_mixer: Not connected")
        return
    data = bytearray(DATA_PREFIX) + convert_to_bytes(message)
    print("send_midi_message_to_mixer:", data)
    
    #print(message.bytes())
    #print("MIDI value:")
    #print(" ".join(hex(n) for n in data))
    #print(int(data[4]))
    await client.write_gatt_char(BLE_MIDI_UUID, data)
    d = " ".join(hex(n) for n in data)
    logger.info("Sent: %s", d)

async def send_raw_message(client, message):
    d = " ".join(hex(n) for n in message.get("raw"))
    logger.info("Sending raw message: %s", d)
    data = bytearray(DATA_PREFIX) + message.get("raw")
    print("send_raw_message:", data)
    await client.write_gatt_char(BLE_MIDI_UUID, data)
    #if message.get("event"):
    #    message.get("event").set() #notify
    #if message.get("callback"):
    #    await message["callback"]()

def convert_to_bytes(data):
    channel = int(data["channel"])
    control = get_CC_from_track_data(data)
    value = get_Value_from_track_data(control, data)
    print("control=", control)
    return bytearray([channel + MIDI_CC_BASE, control, value])

# control
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

# value
def get_Value_from_track_data(cc, data):
    value = int(data.get("value", "0"))
    if "mute" in data:
        value = int(data["mute"])
    if "solo" in data:
        value = int(data["solo"])
    if "rec" in data:
        value = int(data["rec"])
    return value

async def on_connected_to_device(client):
    connected_to_device = True
    await ws_send_to_clients({"status": "ready"})


async def ws_handler(websocket, path):
    clients.append(websocket)
    
    status = "ready"
    if not connected_to_device:
        status = "no device"
    await websocket.send(f"{{\"status\": \"{status}\"}}")
    while websocket.open:
        try:
            data = await websocket.recv()
            logger.info(f"Data received: {data}")
            try:
                json_data = json.loads(data)
                await ws_process_request(json_data)
            except ValueError:
                logger.info("Ignoring invalid request (invalid json)")
            #reply = f"{{\"message\": \"Data recieved: {data}!\"}}"
            #await websocket.send(reply)
        except websockets.exceptions.ConnectionClosed:
            logger.debug("Client disconnected.  Do cleanup")
            break             

    clients.remove(websocket)

async def ws_process_request(data):
    if data.get("cmd"):
        if data.get("cmd") == "track_info":
            await cmd_track_info()
        return
    if data["context"] == "track":
        message_queue.put_nowait(data)
    True

async def cmd_track_info():
    event = asyncio.Event()
    await message_queue.put({"raw": CMD_TRACK_INFO, "callback": cmd_track_info_join, "event": event})
    #async with sysex_mode:
    #    await sysex_mode.wait()
    #print("waiting...")
    #await event.wait()

async def cmd_track_info_join():
    buffer = b""
    while not response_queue.empty():
        msg = response_queue.get_nowait()
        buffer = buffer + msg
        await asyncio.sleep(0)
    print("Data received: ", buffer)

async def cmd_track_info_raw():
    buffer = b""
    while not response_queue.empty():
        msg = response_queue.get_nowait()
        buffer = buffer + msg
        await asyncio.sleep(0)
    print("Data received: ",buffer)

async def received_data(sender: BleakGATTCharacteristic, data: bytearray):
    logger.info(f"Received: {sender}: {data}")
    
    try:
        msg=Message.from_bytes(data[2:])
        
        logger.info("decoded incoming message: %s" % msg)
        await ws_send_to_clients(message2obj(msg))
        return
    except Exception as e:
        logger.error("No MIDI message or parse error: "+ str(e))
    
    print("data2:",data[2]);
    if data[2] == MIDI_SYSEX_START:
        print("SysEx START")
    await response_queue.put(data[1:]) #skip 1st byte

    if data[-1:] == MIDI_SYSEX_END:
        print("SysEx END")
        await cmd_track_info_join();
    


async def ws_send_to_clients(obj):
    msg = json.dumps(obj, indent=2)
    for c in clients:
        print("sending to client: ", msg)
        try:
            await c.send(msg)
        except websockets.exceptions.ConnectionClosed:
            logger.error("Cannot send to client - connection closed")

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

async def ble_main(): #args: argparse.Namespace):
    while True:
        logger.info("Searching for 5 seconds, please wait...")
        await ws_send_to_clients({"status": "searching"})
        devices = await BleakScanner.discover(
            return_adv=False, cb=dict(use_bdaddr=True) #args.macos_use_bdaddr)
        )

        found = None
        connected_to_device = False

        for dev in devices:
            f=" "
            if dev.name and dev.name.startswith("L-20"):
                found = dev
                f="*"    
            logger.info("%s %s - %s" % (f, dev.address, dev.name)) 

        if found:
            await ws_send_to_clients({"status": "found"})
            async with BleakClient(found) as client:
                logger.info(f"Connected: {client.is_connected}")
                model_number = await client.read_gatt_char(MODEL_NBR_UUID)
                logger.info("Model Number: {0}".format("".join(map(chr, model_number))))

                # pairing not needed in MacOS:
                #paired = await client.pair(protection_level=2)
                #print(f"Paired: {paired}")

                await client.start_notify(BLE_MIDI_UUID, received_data)
                logger.info("start_notify for BLE MIDI done")

                #await testme(client)
                #await testme2(client)
                connected_to_device = True
                await on_connected_to_device(client)

                #print("cmd_track_info:")
                #await cmd_track_info_raw()

                while client.is_connected:
                    #msg = await message_queue.get()
                    #await send_midi_message_to_mixer(client, msg)
                    #message_queue.task_done()
                    while not message_queue.empty():
                        msg = message_queue.get_nowait()
                        await send_midi_message_to_mixer(client, msg)
                    await asyncio.sleep(0.1)

                connected_to_device = False
                await ws_send_to_clients({"status": "disconnected"})
        else:
            logger.info("Device not found :( waiting...")
            await asyncio.sleep(5.0)


async def ws_main(args: argparse.Namespace):
    async with websockets.serve(ws_handler, "", int(args.port)):
        await asyncio.Future()  # run forever

async def main(args: argparse.Namespace):
    task1 = asyncio.create_task(ws_main(args))
    task2 = asyncio.create_task(ble_main())
    #task3 = asyncio.create_task(func3()) todo webserver

    await asyncio.wait([task1, task2])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--macos-use-bdaddr",
        action="store_true",
        help="when true use Bluetooth address instead of UUID on macOS",
    )
    parser.add_argument('--port', required=False, default="5885")

    args = parser.parse_args()

    asyncio.run(main(args))
    
