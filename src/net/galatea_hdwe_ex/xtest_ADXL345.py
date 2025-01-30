#!/usr/bin/python3

import board
import busio
import configparser

import time
from time import strftime
import json

import adafruit_adxl34x

# i2c reference could be passed in from the upstream component
# i2c = busio.I2C(board.SCL, board.SDA)
adxl345 = adafruit_adxl34x.ADXL345(busio.I2C(board.SCL, board.SDA))

# these functions require time, consider disabling it
adxl345_TAP_ENABLED = False
adxl345_DROP_ENABLED = False
adxl345_MOTION_ENABLED = False

if adxl345_TAP_ENABLED:
    adxl345.enable_tap_detection()
    #adxl345_TAP_COUNT = 1
    #adxl345_TAP_THRESHOLD = 20
    #adxl345_TAP_DURATION = 50
    #adxl345_TAP_LATENCY = 30
    #adxl345_TAP_WINDOW = 255

if adxl345_DROP_ENABLED:
    adxl345.enable_freefall_detection()
    #adxl345_DROP_THRESHOLD = 10
    #adxl345_DROP_TIME = 25

if adxl345_MOTION_ENABLED:
    adxl345.enable_motion_detection()
    #adxl345_MOTION_THRESHOLD = 18

adafruit_adxl34x.DataRate.RATE_100_HZ
adafruit_adxl34x.Range.RANGE_2_G

def main():
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
        if adxl345_TAP_ENABLED:
            t.append("tap") if adxl345.events["tap"] else None

        if adxl345_DROP_ENABLED:
            t.append("drop") if adxl345.events["freefall"] else None

        if adxl345_MOTION_ENABLED:
            t.append("motion") if adxl345.events["motion"] else None

        accl.update({"t": t})

        t2 = time.perf_counter()
        adxl.update({"d": "{0:.4f}".format(t2 - t1)})

        adxl.update({"accl" : accl})

        print(json.dumps(adxl, indent=4))

if __name__ == "__main__":
    main()
