#!/usr/bin/python3

import board
import busio

import time
from time import strftime
import json

import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1015(i2c)

config = json.load(open("config.json", "r"))
ads_config = config['ads1015']

ads.gain = ads_config['gain']
ads.data_rate = ads_config['data_rate']
Ro = ads_config['Ro']
To = ads_config['To']
beta = ads_config['beta']
ads_C0_ENABLED = ads_config['ads_C0_ENABLED']
ads_C1_ENABLED = ads_config['ads_C1_ENABLED']
ads_C2_ENABLED = ads_config['ads_C2_ENABLED']
ads_C3_ENABLED = ads_config['ads_C3_ENABLED']

# never change this
ads.mode = ADS.Mode.SINGLE

if ads_C0_ENABLED:
    c0 = AnalogIn(ads, ADS.P0)

if ads_C1_ENABLED:
    c1 = AnalogIn(ads, ADS.P1)

if ads_C2_ENABLED:
    c2 = AnalogIn(ads, ADS.P2)

if ads_C3_ENABLED:
    c3 = AnalogIn(ads, ADS.P3)

def startup():
    # get the logfile location
    print(getData(ads_config))

def shutdown():
    # do disconnections and cleanups
    print(getData(ads_config))

def steinhart_temperature_C(r, Ro=Ro, To=To, beta=beta):
    import math
    steinhart = math.log(r / Ro) / beta      # log(R/Ro) / beta
    steinhart += 1.0 / (To + 273.15)         # log(R/Ro) / beta + 1/To
    steinhart = (1.0 / steinhart) - 273.15   # Invert, convert K to C
    return steinhart

def getData(ads):
    return json.dumps(ads, indent=4)

def main():
    startup()
    evt_id = 0

    while True:
        ads = {}
        evt_id +=1

        ads.update({"id": evt_id})

        t0 = strftime("%Y-%m-%d %H:%M:%S")
        ads.update({"t0": t0})

        t1 = time.perf_counter()
        ads.update({"t1": "{0:.4f}".format(t1)})

        analog = {}

        # formatting and CONVERSION takes time, may consider moving it upstream along
        # with 'averaging'

        # make c0r, c1r, c2r & c3r configurable values and inset in ads object
        if ads_C0_ENABLED:
            c0r = 10000 / (65535/c0.value - 1)
            analog.update({"c0x": c0.value})
            analog.update({"c0v": "{:>3.2f}".format(c0.voltage)})
            analog.update({"c0c": "{:>3.2f}".format(steinhart_temperature_C(c0r))})

        if ads_C1_ENABLED:
            c1r = 10000 / (65535/c1.value - 1)
            analog.update({"c1x": c1.value})
            analog.update({"c1v": "{:>3.2f}".format(c1.voltage)})
            analog.update({"c1c": "{:>3.2f}".format(steinhart_temperature_C(c1r))})

        if ads_C2_ENABLED:
            c2r = 10000 / (65535/c2.value - 1)
            analog.update({"c2x": c2.value})
            analog.update({"c2v": "{:>3.2f}".format(c2.voltage)})
            analog.update({"c2c": "{:>3.2f}".format(steinhart_temperature_C(c2r))})

        if ads_C3_ENABLED:
            c3r = 10000 / (65535/c3.value - 1)
            analog.update({"c3x": c3.value})
            analog.update({"c3v": "{:>3.2f}".format(c3.voltage)})
            analog.update({"c3c": "{:>3.2f}".format(steinhart_temperature_C(c3r))})

        t2 = time.perf_counter()
        ads.update({"d": "{0:.4f}".format(t2 - t1)})
        # typically ~.212 when running c0,c1 alone

        ads.update({"analog" : analog})

        print(getData(ads))

if __name__ == "__main__":
    main()
