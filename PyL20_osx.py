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

MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
BLE_MIDI_UUID  = "7772E5DB-3868-4112-A1A9-F2669D106BF3"

DATA_PREFIX=b"\x80\x80"

MIDI_CC="control_change"
MIDI_CC_TRACK_VOLUME=60 #master
MIDI_CC_TRACK_VOLUME_A=62
MIDI_CC_TRACK_VOLUME_B=64
MIDI_CC_TRACK_VOLUME_C=66
MIDI_CC_TRACK_VOLUME_D=68
MIDI_CC_TRACK_VOLUME_E=70
MIDI_CC_TRACK_VOLUME_F=72
MIDI_CC_TRACK_SOLO=50
MIDI_CC_TRACK_MUTE=48

MIDI_CC_MASTER_VOLUME=84
MIDI_CHAN_MASTER_VOLUME=10

MIDI_CC_TRACK_GROUPS=[MIDI_CC_TRACK_VOLUME, MIDI_CC_TRACK_VOLUME_A, MIDI_CC_TRACK_VOLUME_B, MIDI_CC_TRACK_VOLUME_C, MIDI_CC_TRACK_VOLUME_D, MIDI_CC_TRACK_VOLUME_E, MIDI_CC_TRACK_VOLUME_F]

# list of connected sockets:
clients=[]

connected_to_device = False
message_queue = asyncio.Queue()

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
    logging.info("Sending message: %s", str(message))
    if not client or not client.is_connected:
        logging.info("send_midi_message_to_mixer: Not connected")
        return
    print("bytearray:")
    data = bytearray(DATA_PREFIX) + convert_to_bytes(message)
    print("data:", data)
    
    #print(message.bytes())
    print("MIDI value:")
    #print(" ".join(hex(n) for n in data))
    print(int(data[4]))
    await client.write_gatt_char(BLE_MIDI_UUID, data)
    d = " ".join(hex(n) for n in data)
    logging.info("Sent: %s", d)

def convert_to_bytes(data):
    channel = int(data["channel"])
    value = int(data["value"])
    control = get_CC_from_track_data(data)
    print("CC", control)
    return bytearray([channel + 176, control, value])

async def on_connected_to_device(client):
    connected_to_device = True
    await send_to_clients({"status": "ready"})


async def ws_handler(websocket, path):
    clients.append(websocket)
    
    status = "ready"
    if not connected_to_device:
        status = "no device"
    await websocket.send(f"{{\"status\": \"{status}\"}}")
    while websocket.open:
        try:
            data = await websocket.recv()
            logging.info(f"Data received: {data}")
            try:
                json_data = json.loads(data)
                await process_request(json_data)
            except ValueError:
                logging.info("Ignoring invalid request (invalid json)")
            #reply = f"{{\"message\": \"Data recieved: {data}!\"}}"
            #await websocket.send(reply)
        except websockets.exceptions.ConnectionClosed:
            logging.debug("Client disconnected.  Do cleanup")
            break             

    clients.remove(websocket)

async def process_request(data):
    #print(data)
    if data["context"] == "track":
        channel = data["channel"]
        value = data["value"]
        control = get_CC_from_track_data(data)
        #msg = Message(MIDI_CC, control = control, channel = channel, value = int(value) )
        #print(msg)
        message_queue.put_nowait(data)
    True

def get_CC_from_track_data(data):
    group = int(data["group"])
    #print(group)
    #print(len(MIDI_CC_TRACK_GROUPS))
    #print(MIDI_CC_TRACK_GROUPS)
    if group >= 0 and group < len(MIDI_CC_TRACK_GROUPS):
        return MIDI_CC_TRACK_GROUPS[group]
    return 0

async def received_data(sender: BleakGATTCharacteristic, data: bytearray):
    logging.debug(f"Received: {sender}: {data}")
    # first 2 bytes is a prefix
    command=Message.from_bytes(data[2:])
    logging.info("decoded incoming message: %s" % command)
    await send_to_clients(message2obj(command))

async def send_to_clients(obj):
    msg = json.dumps(obj, indent=2)
    for c in clients:
        print("sending to client: ", msg)
        try:
            await c.send(msg)
        except websockets.exceptions.ConnectionClosed:
            logging.error("Cannot send to client - connection closed")

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
        logging.info("Searching for 5 seconds, please wait...")
        await send_to_clients({"status": "searching"})
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
            logging.info("%s %s - %s" % (f, dev.address, dev.name)) 

        if found:
            await send_to_clients({"status": "found"})
            async with BleakClient(found) as client:
                logging.info(f"Connected: {client.is_connected}")
                model_number = await client.read_gatt_char(MODEL_NBR_UUID)
                logging.info("Model Number: {0}".format("".join(map(chr, model_number))))

                # pairing not needed in MacOS:
                #paired = await client.pair(protection_level=2)
                #print(f"Paired: {paired}")

                await client.start_notify(BLE_MIDI_UUID, received_data)

                #await testme(client)
                connected_to_device = True
                await on_connected_to_device(client)

                while client.is_connected:
                    #msg = await message_queue.get()
                    #await send_midi_message_to_mixer(client, msg)
                    #message_queue.task_done()
                    while not message_queue.empty():
                        msg = message_queue.get_nowait()
                        await send_midi_message_to_mixer(client, msg)
                    await asyncio.sleep(0.1)

                connected_to_device = False
                await send_to_clients({"status": "disconnected"})
        else:
            logging.info("Device not found :( waiting...")
            await asyncio.sleep(5.0)

        
async def ws_main():
    async with websockets.serve(ws_handler, "localhost", 5000):
        await asyncio.Future()  # run forever

async def main():
    task1 = asyncio.create_task(ws_main())
    task2 = asyncio.create_task(ble_main())
    #task3 = asyncio.create_task(func3())

    await asyncio.wait([task1, task2])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--macos-use-bdaddr",
        action="store_true",
        help="when true use Bluetooth address instead of UUID on macOS",
    )

    args = parser.parse_args()

    asyncio.run(main())
    
