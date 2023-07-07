import argparse
import asyncio

from bleak import BleakScanner
from bleak import BleakClient
from bleak import BleakGATTCharacteristic

MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
BLE_MIDI_UUID  = "7772E5DB-3868-4112-A1A9-F2669D106BF3"

DATA_PREFIX=b"\x80\x80"

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

def received_data(sender: BleakGATTCharacteristic, data: bytearray):
    print(f"Received: {sender}: {data}")

async def main(args: argparse.Namespace):
    print("Searching for 5 seconds, please wait...")

    devices = await BleakScanner.discover(
        return_adv=False, cb=dict(use_bdaddr=True) #args.macos_use_bdaddr)
    )

    found = None

    for dev in devices:
        f=" "
        if dev.name and dev.name.startswith("L-20"):
            found = dev
            f="*"    
        print("%s %s - %s" % (f, dev.address, dev.name)) 


    if found:
        async with BleakClient(found) as client:
            print(f"Connected: {client.is_connected}")
            model_number = await client.read_gatt_char(MODEL_NBR_UUID)
            print("Model Number: {0}".format("".join(map(chr, model_number))))

            # pairing not needed in MacOS:
            #paired = await client.pair(protection_level=2)
            #print(f"Paired: {paired}")

            await client.start_notify(BLE_MIDI_UUID, received_data)

            await testme(client)

            print("Waiting 10s")
            await asyncio.sleep(10.0)
    else:
        print("Device not found :(")
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--macos-use-bdaddr",
        action="store_true",
        help="when true use Bluetooth address instead of UUID on macOS",
    )

    args = parser.parse_args()

    asyncio.run(main(args))
