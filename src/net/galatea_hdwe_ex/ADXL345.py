#!/usr/bin/python3

import board
import busio

import time
from time import strftime
import json

import adafruit_adxl34x

i2c = busio.I2C(board.SCL, board.SDA)
adxl345 = adafruit_adxl34x.ADXL345(i2c)

config = json.load(open("config.json", "r"))
adx_config = config['adxl345']

TAP_ENABLED = adx_config['TAP_ENABLED']
DROP_ENABLED = adx_config['DROP_ENABLED']
MOTION_ENABLED = adx_config['MOTION_ENABLED']

if TAP_ENABLED:
    adxl345.enable_tap_detection()
    TAP_COUNT = adx_config['TAP_COUNT']
    TAP_THRESHOLD = adx_config['TAP_THRESHOLD']
    TAP_DURATION = adx_config['TAP_DURATION']
    TAP_LATENCY = adx_config['TAP_LATENCY']
    TAP_WINDOW = adx_config['TAP_WINDOW']

if DROP_ENABLED:
    adxl345.enable_freefall_detection()
    DROP_THRESHOLD = adx_config['DROP_THRESHOLD']
    DROP_TIME = adx_config['DROP_TIME']

if MOTION_ENABLED:
    adxl345.enable_motion_detection()
    MOTION_THRESHOLD = adx_config['MOTION_THRESHOLD']

# may add this
adafruit_adxl34x.DataRate.RATE_100_HZ
adafruit_adxl34x.Range.RANGE_2_G

def startup():
    # get the logfile location
    print(getData(adx_config))

def shutdown():
    # do disconnections and cleanups
    print(getData(adx_config))

def getData(adxl):
    return json.dumps(adxl, indent=4)

def main():
    startup()
    evt_id = 0

    while True:
        evt_id +=1
        adxl = {}
        adxl.update({"id": evt_id})

        t0 = strftime("%Y-%m-%d %H:%M:%S")
        adxl.update({"t0": t0})

        t1 = time.perf_counter()
        adxl.update({"t1": "{0:.4f}".format(t1)})

        accl = {}

        # formatting takes time, may consider moving it upstream along
        # with 'averaging'
        accl.update({"x": "{0:.4f}".format(adxl345.acceleration[0])})
        accl.update({"y": "{0:.4f}".format(adxl345.acceleration[1])})
        accl.update({"z": "{0:.4f}".format(adxl345.acceleration[2])})

        t = []
        if TAP_ENABLED:
            t.append("tap") if adxl345.events["tap"] else None

        if DROP_ENABLED:
            t.append("drop") if adxl345.events["freefall"] else None

        if MOTION_ENABLED:
            t.append("motion") if adxl345.events["motion"] else None

        accl.update({"t": t})

        t2 = time.perf_counter()
        adxl.update({"d": "{0:.4f}".format(t2 - t1)})

        adxl.update({"accl" : accl})

        print(getData(adxl))

if __name__ == "__main__":
    main()
