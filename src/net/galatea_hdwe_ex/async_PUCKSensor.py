#!/usr/bin/python3

import board
import busio
import configparser

import time
from time import strftime
import json

import asyncio
import array

#  pip install bleak
from bleak import discover
from bleak import BleakClient

# how stable is this and should it be discovered of in config? customized?
#address = "db:d1:d8:ad:89:bd"
address = "EB:67:99:CC:3C:9B"

# should these be hardcoded/device?
UUID_NORDIC_TX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UUID_NORDIC_RX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

'''
pi@galatea:~/boxapp/hdwe_test $ bluetoothctl
Agent registered
[bluetooth]# scan on
Discovery started
[CHG] Controller DC:A6:32:13:28:5B Discovering: yes
[CHG] Device EB:67:99:CC:3C:9B RSSI: -52
[CHG] Device EB:67:99:CC:3C:9B RSSI: -32
[CHG] Device 53:69:52:9C:A9:7C RSSI: -85
[CHG] Device 53:69:52:9C:A9:7C TxPower: 12
[DEL] Device EB:67:99:CC:3C:9B Puck.js 3c9b
[DEL] Device 53:69:52:9C:A9:7C 53-69-52-9C-A9-7C
[NEW] Device EB:67:99:CC:3C:9B Puck.js 3c9b
[bluetooth]# pair EB:67:99:CC:3C:9B
Attempting to pair with EB:67:99:CC:3C:9B
[CHG] Device EB:67:99:CC:3C:9B Connected: yes
[NEW] Primary Service
    /org/bluez/hci0/dev_EB_67_99_CC_3C_9B/service000a
    00001801-0000-1000-8000-00805f9b34fb
    Generic Attribute Profile
[NEW] Primary Service
    /org/bluez/hci0/dev_EB_67_99_CC_3C_9B/service000b
    6e400001-b5a3-f393-e0a9-e50e24dcca9e
    Nordic UART Service
[NEW] Characteristic
    /org/bluez/hci0/dev_EB_67_99_CC_3C_9B/service000b/char000c
    6e400003-b5a3-f393-e0a9-e50e24dcca9e
    Nordic UART RX
[NEW] Descriptor
    /org/bluez/hci0/dev_EB_67_99_CC_3C_9B/service000b/char000c/desc000e
    00002902-0000-1000-8000-00805f9b34fb
    Client Characteristic Configuration
[NEW] Characteristic
    /org/bluez/hci0/dev_EB_67_99_CC_3C_9B/service000b/char000f
    6e400002-b5a3-f393-e0a9-e50e24dcca9e
    Nordic UART TX
[CHG] Device EB:67:99:CC:3C:9B UUIDs: 00001800-0000-1000-8000-00805f9b34fb
[CHG] Device EB:67:99:CC:3C:9B UUIDs: 00001801-0000-1000-8000-00805f9b34fb
[CHG] Device EB:67:99:CC:3C:9B UUIDs: 6e400001-b5a3-f393-e0a9-e50e24dcca9e
[CHG] Device EB:67:99:CC:3C:9B ServicesResolved: yes
[Puck.js 3c9b]# connect EB:67:99:CC:3C:9B
Attempting to connect to EB:67:99:CC:3C:9B
Connection successful
Failed to pair: org.bluez.Error.AuthenticationCanceled
[Puck.js 3c9b]#
'''


# this needs to be refactored and configurable

# \x03 -> Ctrl-C clears line
# \x10 -> Echo off for line so don't try and send any text back
# command = "\x03\x10reset()\nLED.toggle()\n"

#command = b"\x03\x10clearInterval()\n\x10setInterval(function() {JSON.stringify({Date.now(), E.getTemperature(),-63, 7, 45,35,15,-102,BTN.read(),Puck.light(),Puck.capSense(),Puck.getBatteryPercentage()}, 10)};\n"
command = b"\x03\x10clearInterval()\n\x10setInterval(function() {Bluetooth.println(JSON.stringify({u:Date.now(),c:E.getTemperature(),x_axis:-63, y_axis:7, z_axis:45,x_ori:35, y_ori:15, z_ori:-102,btn:BTN.read(),l:Puck.light(),k:Puck.capSense(),b:Puck.getBatteryPercentage()}));}, 100); NRF.on('disconnect', function() {reset()});\n"


'''
byte_test_command = "\n"
my_test_command_bytes = bytearray(byte_test_command, 'utf-8')
'''


puck_json = dict()


# get the config

# these functions require time, consider disabling it
puck_TILT_ENABLED = False
puck_STEP_ENABLED = False
puck_MOVEMENT_ENABLED = False
puck_SIGNIFICANT_MOVEMENT_ENABLED = False

if puck_TILT_ENABLED:
    pucksensor.enable_tap_detection()
    '''
    Send this javascript:
        /*
        require("puckjsv2-accel-tilt").on();
        Puck.on('accel',function(a) {
          digitalPulse(LED1,1,100);
        });
        // turn off with require("puckjsv2-accel-tilt").off();
        */
    '''

# You can scan for devices with:
#async def run():
#    devices = await discover()
#    for d in devices:
#        print(d)

async def send_puck_request(address):

    client = BleakClient(address)

    try:
        while await client.connect():
            await client.start_notify(UUID_NORDIC_RX, get_puck_response)

            c = command

            while len(c)>0:
                await client.write_gatt_char(UUID_NORDIC_TX, bytearray(c[0:20]), True)
                c = c[20:]

            #await asyncio.sleep(.5, loop=get_puck_response)

    except Exception as e:
        print(e)
    finally:
        await client.disconnect()

def get_puck_response(sender, data):
    print(data.decode())
    puck_json.update({"sender": "{0}".format(sender), "data": "{0}".format(data.decode())})

async def startup():
    # get the logfile location
    '''
    [Puck.js 89bd]# version
        Version 5.50

    [Puck.js 89bd]# list
        Controller DC:A6:32:13:28:5B galatea [default]

    [Puck.js 89bd]# show DC:A6:32:13:28:5B
        Controller DC:A6:32:13:28:5B (public)
        Name: galatea
        Alias: galatea
        Class: 0x00480000
        Powered: yes
        Discoverable: no
        Pairable: yes
        UUID: Headset AG                (00001112-0000-1000-8000-00805f9b34fb)
        UUID: Generic Attribute Profile (00001801-0000-1000-8000-00805f9b34fb)
        UUID: A/V Remote Control        (0000110e-0000-1000-8000-00805f9b34fb)
        UUID: SIM Access                (0000112d-0000-1000-8000-00805f9b34fb)
        UUID: Generic Access Profile    (00001800-0000-1000-8000-00805f9b34fb)
        UUID: PnP Information           (00001200-0000-1000-8000-00805f9b34fb)
        UUID: A/V Remote Control Target (0000110c-0000-1000-8000-00805f9b34fb)
        UUID: Audio Source              (0000110a-0000-1000-8000-00805f9b34fb)
        UUID: Handsfree Audio Gateway   (0000111f-0000-1000-8000-00805f9b34fb)
        Modalias: usb:v1D6Bp0246d0532
        Discovering: yes

    [Puck.js 89bd]# info DB:D1:D8:AD:89:BD
        Device DB:D1:D8:AD:89:BD (random)
        Name: Puck.js 89bd
        Alias: Puck.js 89bd
        Paired: yes
        Trusted: yes
        Blocked: no
        Connected: yes
        LegacyPairing: no
        UUID: Generic Access Profile    (00001800-0000-1000-8000-00805f9b34fb)
        UUID: Generic Attribute Profile (00001801-0000-1000-8000-00805f9b34fb)
        UUID: Nordic UART Service       (6e400001-b5a3-f393-e0a9-e50e24dcca9e)
        RSSI: -52
        AdvertisingFlags:
        05

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
        handle: 0x000e, uuid: 00002902-0000-1000-8000-00805f9b34fb
        handle: 0x000f, uuid: 00002803-0000-1000-8000-00805f9b34fb
        handle: 0x0010, uuid: 6e400002-b5a3-f393-e0a9-e50e24dcca9e

    [NEW] Device 64:B0:B7:18:E8:10 64-B0-B7-18-E8-10
    [NEW] Device DC:A9:04:75:0A:D6 MACBOOK
    '''

    # log the component has started
    print("component PUCK started")

async def shutdown():
    # log the component has stopped
    # do disconnections and cleanups
    pass





async def getData(puck):
    return json.dumps(puck, indent=4)

async def main():
    await startup()
    evt_id = 0

    while True:
        evt_id +=1
        puck = {}

        puck.update({"id": evt_id})

        t0 = strftime("%Y-%m-%d %H:%M:%S")
        puck.update({"t0": t0})

        t1 = time.perf_counter()
        puck.update({"t1": "{0:.4f}".format(t1)})

        # connect and get data from the puck over serial.
        await send_puck_request(address)

        '''
        # pull NEW data from incoming JSON (puck_json)
        # puck_json should have new values for every iteration

        puck.update({"btty": puck_json.b})
        puck.update({"uptime": puck_json.u})
        puck.update({"button": puck_json.btn})
        puck.update({"led": puck_json.l})

        if puck_ACCELERATION_ENABLED:
            # acceleration - 3-tuple of X, Y, Z axis accelerometer
            # values in meters per second squared.
            # "a:Puck.accel() <-- contains accel & gyro tuples

            accl = {}

            accl.update({"x": puck_json.x_axis})
            accl.update({"y": puck_json.y_axis})
            accl.update({"z": puck_json.z_axis})
            puck.update({"accl" : accl})

            # gyro - 3-tuple of X, Y, Z axis gyroscope values in degrees
            # per second.

            gyro = {}

            gyro.update({"x": puck_json.x_ori})
            gyro.update({"y": puck_json.y_ori})
            gyro.update({"z": puck_json.z_ori})
            puck.update({"gyro" : gyro})

        if puck_MAGNET_ENABLED:
            # magnetic - 3-tuple of X, Y, Z axis magnetometer values
            # Puck.mag()
            mag = {}

            mag.update({"x": puck_json.x_mag})
            mag.update({"y": puck_json.y_mag})
            mag.update({"z": puck_json.z_mag})
            puck.update({"mag" : mag})

        if puck_TEMPERATURE_ENABLED:
            # temperature - temperature in degrees Celsius.
            # E.getTemperature()
            temp = {}
            temp.update({"c": puck_json.c})
            puck.update({"temp" : temp})

        if puck_LUX_ENABLED:
            # light sensing between 0 ... 1.0
            # Puck.light()
            lux = {}
            lux.update({"lux": puck_json.l})
            puck.update({"lux" : lux})

        if puck_CAPSENSE_ENABLED:
            # capacitive sensing integer value that rises as the capacitance attached to D11 increases
            # Puck.capSense()
            cap = {}
            cap.update({"cap": puck_json.k})
            puck.update({"cap" : cap})

        t = []
        if puck_TILT_ENABLED:
            t.append("tilt") if puck.events["tilt"] else None

        if puck_STEP_ENABLED:
            t.append("step") if puck.events["tilt"] else None

        if puck_MOVEMENT_ENABLED:
            t.append("move") if puck.events["tilt"] else None

        if puck_SIGNIFICANT_MOVEMENT_ENABLED:
            t.append("bigmove") if puck.events["tilt"] else None

        puck.update({"t": t})
        '''

        t2 = time.perf_counter()
        puck.update({"d": "{0:.4f}".format(t2 - t1)})

        # add current data to the dictionary
        puck.update({"data": puck_json})

        print(await getData(puck))

if __name__ == "__main__":
    asyncio.run(main())
