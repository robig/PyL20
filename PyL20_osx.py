import argparse
import asyncio
import logging
import websockets
import json
from bleak import BleakScanner
from bleak import BleakClient
from bleak import BleakGATTCharacteristic
from mido import Message

logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)

MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
BLE_MIDI_UUID  = "7772E5DB-3868-4112-A1A9-F2669D106BF3"

DATA_PREFIX=b"\x80\x80"

MIDI_CC="control_change"
MIDI_CC_TRACK_VOLUME=60
MIDI_CC_TRACK_SOLO=50
MIDI_CC_TRACK_MUTE=48

# list of connected sockets:
clients=[]

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


async def ws_handler(websocket, path):
    clients.append(websocket)
    while websocket.open:
        try:
            data = await websocket.recv()
            reply = f"{{\"message\": \"Data recieved: {data}!\"}}"
            await websocket.send(reply)
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected.  Do cleanup")
            break             
        await asyncio.sleep(1.0)
    clients.remove(websocket)

async def received_data(sender: BleakGATTCharacteristic, data: bytearray):
    logging.debug(f"Received: {sender}: {data}")
    # first 2 bytes is a prefix
    command=Message.from_bytes(data[2:])
    logging.info("decoded incoming message: %s" % command)
    for c in clients:
        msg = "{\"command\": "+json.dumps(message2obj(command), indent=2)+"}"
        print("sending to client: ", msg)
        await c.send(msg)

def message2obj(message):
    # map for client:
    func = None
    context= None
    if message.type == MIDI_CC and message.control == MIDI_CC_TRACK_VOLUME:
        func="volume"
        context="track"
    return { "type": message.type, "channel": message.channel, "control": message.control, "value": message.value, "function": func, "context": context }

async def ble_main(): #args: argparse.Namespace):
    while True:
        logging.info("Searching for 5 seconds, please wait...")
        devices = await BleakScanner.discover(
            return_adv=False, cb=dict(use_bdaddr=True) #args.macos_use_bdaddr)
        )

        found = None

        for dev in devices:
            f=" "
            if dev.name and dev.name.startswith("L-20"):
                found = dev
                f="*"    
            logging.info("%s %s - %s" % (f, dev.address, dev.name)) 


        if found:
            async with BleakClient(found) as client:
                logging.info(f"Connected: {client.is_connected}")
                model_number = await client.read_gatt_char(MODEL_NBR_UUID)
                logging.info("Model Number: {0}".format("".join(map(chr, model_number))))

                # pairing not needed in MacOS:
                #paired = await client.pair(protection_level=2)
                #print(f"Paired: {paired}")

                await client.start_notify(BLE_MIDI_UUID, received_data)

                await testme(client)

                while True:
                    await asyncio.sleep(1)
        else:
            logging.info("Device not found :( waiting...")
            await asyncio.sleep(10.0)
        
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
    
