#!/usr/bin/python3

import asyncio
import array
from bleak import discover
from bleak import BleakClient

address = "DB:D1:D8:AD:89:BD"
'''
    [DB:D1:D8:AD:89:BD][LE]> char-desc
        handle: 0x0001, uuid: 00002800-0000-1000-8000-00805f9b34fb
        handle: 0x0002, uuid: 00002803-0000-1000-8000-00805f9b34fb
        handle: 0x0003, uuid: 00002a00-0000-1000-8000-00805f9b34fb
        handle: 0x0004, uuid: 00002803-0000-1000-8000-00805f9b34fb
        handle: 0x0005, uuid: 00002a01-0000-1000-8000-00805f9b34fb
        handle: 0x0006, uuid: 00002803-0000-1000-8000-00805f9b34fb
        handle: 0x0007, uuid: 00002a04-0000-1000-8000-00805f9b34fb
        handle: 0x0008, uuid: 00002803-0000-1000-8000-00805f9b34fb
        handle: 0x0009, uuid: 00002aa6-0000-1000-8000-00805f9b34fb
        handle: 0x000a, uuid: 00002800-0000-1000-8000-00805f9b34fb
        handle: 0x000b, uuid: 00002800-0000-1000-8000-00805f9b34fb
        handle: 0x000c, uuid: 00002803-0000-1000-8000-00805f9b34fb

        handle: 0x000d, uuid: 6e400003-b5a3-f393-e0a9-e50e24dcca9e
The RX characteristic (UUID 6e400003-b5a3-f393-e0a9-e50e24dcca9e) lets
you get data back from Puck.js. It can't be read, but you can subscribe
to notify, and so can receive any characters as they get sent.

        handle: 0x000e, uuid: 00002902-0000-1000-8000-00805f9b34fb
        handle: 0x000f, uuid: 00002803-0000-1000-8000-00805f9b34fb
        handle: 0x0010, uuid: 6e400002-b5a3-f393-e0a9-e50e24dcca9e

The TX characteristic (UUID 6e400002-b5a3-f393-e0a9-e50e24dcca9e) lets
you send data to Puck.js. You can write up to 20 bytes of data to it,
and each time you write, the characters you send go straight to the
JS interpreter.
'''

UUID_NORDIC_RX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
UUID_NORDIC_TX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
command = b"\x03\x10clearInterval()\n\x10setInterval(function() {LED.toggle()}, 500);\n\x10print('Hello World')\n"

def uart_data_received(sender, data):
    print("RX> {0}".format(data))

# You can scan for devices with:
#async def run():
#    devices = await discover()
#    for d in devices:
#        print(d)

print("Connecting...")
async def run(address, loop):
    async with BleakClient(address, loop=loop) as client:
        print("Connected")
        await client.start_notify(UUID_NORDIC_RX, uart_data_received)
        print("Writing command")
        c=command
        while len(c)>0:
          await client.write_gatt_char(UUID_NORDIC_TX, bytearray(c[0:20]), True)
          c = c[20:]
        print("Waiting for data")
        await asyncio.sleep(1.0, loop=loop) # wait for a response
        print("Done!")


loop = asyncio.get_event_loop()
loop.run_until_complete(run(address, loop))
