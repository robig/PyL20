from mido import Message
import re

while True:
    val = input("Paste data: ")
    val = re.sub(".*Value: ", "", val)
    val = val.replace(" ", "")
    data = bytearray.fromhex(val)

    message = None
    if len(data) > 3:
        message = Message.from_bytes(data[2:])
    print(val, " -> ", message)