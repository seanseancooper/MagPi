#!/usr/bin/python3

import board
import busio
import configparser
import time
from time import strftime
import json
import asyncio
import array
from bleak import discover
from bleak import BleakClient

address = "EB:67:99:CC:3C:9B"
UUID_NORDIC_TX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UUID_NORDIC_RX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

command = b"\x03\x10var cmds=['Math.round(Date.now()*100)/100','E.getTemperature()','Puck.getBatteryPercentage()','BTN.read()','','','Math.round(Puck.light()*100)/100','Puck.capSense()',''];setInterval(function(){for (i=0;i<cmds.length;i++){out = i+':'+eval(cmds[i]); Bluetooth.println(out.toString());}},250);\n"
data_lines = ['0:11225.982666015   ','1:100 24.75 false   ','2:-10.00-10.00-10.00','3:-10.00-10.00-10.00','4:0.5608215332      ','5:3359              ','6:\r                ']

databuffer = {}

def uart_data_received(sender, data):
    # incoming data SHOULD BE 20 bytes wide
    data_line = data.decode()
    print("data_line:'" + data_line + "'")

    flag =  data_line[0:2]
    print("flag:" + flag)

    if flag == '0:':
        databuffer['u'] = data_line[2:20].strip()
        print("got:" + databuffer['u'])

    if flag == '1:':
        databuffer['c'] = data_line[2:20].strip()
        print("got:" + databuffer['c'])

    if flag == '2:':
        databuffer['b'] = data_line[2:20].strip()
        print("got:" + databuffer['b'])

    if flag == '3:':
        databuffer['btn'] = data_line[2:20].strip()
        print("got:" + databuffer['btn'])
    '''
    if flag == '4:':
        databuffer['x_accl'] = data_line[2:8].strip()
        databuffer['y_accl'] = data_line[8:14].strip()
        databuffer['z_accl'] = data_line[14:20].strip()
        print("got:" + str(databuffer['x_accl']), str(databuffer['y_accl']), str(databuffer['z_accl']))

    if flag == '5:':
        databuffer['x_gyro'] = data_line[2:8].strip()
        databuffer['y_gyro'] = data_line[8:14].strip()
        databuffer['z_gyro'] = data_line[14:20].strip()
        print("got:" + str(databuffer['x_gyro']), str(databuffer['y_gyro']), str(databuffer['z_gyro']))
    '''
    if flag == '6:':
        databuffer['l'] = data_line[2:20].strip()
        print("got:" + databuffer['l'])

    if flag == '7:':
        databuffer['k'] = data_line[2:20].strip()
        print("got:" + databuffer['k'])

    if flag == '8:': # not implemented yet
        print("RESULT: {0}".format(json.dumps(databuffer, indent=4)))
        databuffer.clear()

print("Connecting...")
async def run(address, loop):

    SENT = False # send command once
    i = 0

    try:
        async with BleakClient(address, loop=loop) as client:
            print("loading client")

            try:
                while await client.is_connected():
                    print("connected")
                    await client.start_notify(UUID_NORDIC_RX, uart_data_received)

                    i += 1
                    if SENT is False:
                        c=command
                        while len(c)>0:
                          await client.write_gatt_char(UUID_NORDIC_TX, bytearray(c[0:20]), True)
                          c = c[20:]

                          SENT = True

                    print("waiting..." + str(i))
                    await asyncio.sleep(.1) # wait for a response

                if not await client.is_connected():
                    print("disconnected.")

            except KeyboardInterrupt:
                await client.disconnect()
                print("disconnected.")
    except RuntimeError:
        pass
    finally:
        pass

loop = asyncio.get_event_loop()
try:
    asyncio.ensure_future(run(address, loop))
    loop.run_forever()
except RuntimeError:
    pass
finally:
    print("Closing Loop")
    loop.close()

