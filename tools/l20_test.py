import sys
import argparse
import asyncio
import logging
import re
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

message_queue = asyncio.Queue()
connected_to_device = False

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
    await client.write_gatt_char(BLE_MIDI_UUID, b"\x80\x80\xB0\x3C\x10") # 8080 b03c 10
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

async def on_connected_to_device(client):
    connected_to_device = True

async def received_data(sender: BleakGATTCharacteristic, data: bytearray):
    logger.info(f"Received: {sender}: {data}")
    d = " ".join(hex(n) for n in data)
    #print(d)
    logger.info("  hex: %s", d.replace("0x0 ", "0x00 ").replace("0x",""))
    # first 2 bytes is a prefix
    try:
        command=Message.from_bytes(data[2:])
        logger.info("decoded MIDI message: %s" % command)
    except:
        logger.debug(sys.exc_info()[0])


async def ble_main(started_event, args: argparse.Namespace):
    while True:
        logger.info("Searching for 5 seconds, please wait...")
        devices = await BleakScanner.discover(
            return_adv=False, cb=dict(use_bdaddr=True) #args.macos_use_bdaddr)
        )

        found = None
        connected_to_device = False

        for dev in devices:
            f=" "
            if dev.name and dev.name.startswith(args.name):
                found = dev
                f="*"    
            logger.info("%s %s - %s" % (f, dev.address, dev.name)) 

        if found:
            async with BleakClient(found) as client:
                logger.info(f"Connected: {client.is_connected}")
                model_number = await client.read_gatt_char(MODEL_NBR_UUID)
                logger.info("Model Number: {0}".format("".join(map(chr, model_number))))

                # pairing not needed in MacOS:
                #paired = await client.pair(protection_level=2)
                #print(f"Paired: {paired}")

                # list services:
                if args.list:
                    await list_bt_services(client)

                await client.start_notify(BLE_MIDI_UUID, received_data)
                #print("notify registerd")

                #await testme(client)
                #await testme2(client)
                connected_to_device = True
                await on_connected_to_device(client)

                #print("setting event")
                started_event.set()
                #print("set")

                while True: #client.is_connected:
                    #print("Waiting for message queue...")
                    while not message_queue.empty():
                        msg = message_queue.get_nowait()
                        
                        print("Sending message: ", msg)
                        await client.write_gatt_char(BLE_MIDI_UUID, msg)
                    await asyncio.sleep(1)

        else:
            logger.info("Device not found :( waiting...")
            await asyncio.sleep(5.0)

async def list_bt_services(client):
    for service in client.services:
        logger.info("[Service] %s", service)

        for char in service.characteristics:
            if "read" in char.properties:
                try:
                    value = await client.read_gatt_char(char.uuid)
                    logger.info(
                        "  [Characteristic] %s (%s), Value: %r",
                        char,
                        ",".join(char.properties),
                        value,
                    )
                except Exception as e:
                    logger.error(
                        "  [Characteristic] %s (%s), Error: %s",
                        char,
                        ",".join(char.properties),
                        e,
                    )
            else:
                logger.info(
                    "  [Characteristic] %s (%s)", char, ",".join(char.properties)
                )

            for descriptor in char.descriptors:
                try:
                    value = await client.read_gatt_descriptor(descriptor.handle)
                    logger.info("    [Descriptor] %s, Value: %r", descriptor, value)
                except Exception as e:
                    logger.error("    [Descriptor] %s, Error: %s", descriptor, e)


async def ainput(string: str) -> str:
    await asyncio.get_event_loop().run_in_executor(
            None, lambda s=string: sys.stdout.write(s+' '))
    return await asyncio.get_event_loop().run_in_executor(
            None, sys.stdin.readline)

async def user_main(started_event):
    print("Waiting for BLE to be ready...")
    await started_event.wait()
    while True:
        print("Paste data (hex): ")
        val = await ainput("Paste data (hex): ")
        if val == "exit" or val == "quit":
            sys.exit(0)
        val = re.sub(".*Value: ", "", val)
        val = val.replace(" ", "").replace("\\x","")
        data = bytearray.fromhex(val)
        if len(data)>0:
            print(" <- ", data)
            await message_queue.put(data)
            #print("waiting...")
        await asyncio.sleep(1)

async def main(args: argparse.Namespace):
    started_event = asyncio.Event()
    task1 = asyncio.create_task(user_main(started_event))
    task2 = asyncio.create_task(ble_main(started_event, args))

    await asyncio.wait([task2, task1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--macos-use-bdaddr",
        action="store_true",
        help="when true use Bluetooth address instead of UUID on macOS",
    )
    parser.add_argument("name", default="L-20")
    parser.add_argument("--list", action="store_true")

    args = parser.parse_args()

    #asyncio.run(ble_main(args))
    asyncio.run(main(args))
    
