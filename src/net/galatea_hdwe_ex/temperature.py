#!/usr/bin/python3

import board
import busio
import configparser

import time
from time import strftime
import json

import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

ads = ADS.ADS1015(busio.I2C(board.SCL, board.SDA))

ads_CHAN_0 = True
ads_CHAN_1 = True
ads_CHAN_2 = True
ads_CHAN_3 = True

if ads_CHAN_0:
    chan0 = AnalogIn(ads, ADS.P0)

if ads_CHAN_1:
    chan1 = AnalogIn(ads, ADS.P1)

if ads_CHAN_2:
    chan2 = AnalogIn(ads, ADS.P2)

if ads_CHAN_3:
    chan3 = AnalogIn(ads, ADS.P3)

def startup():
    # get the logfile location
    # log the component has started
    # initialize for stats
    pass

def shutdown():
    # log the component has stopped
    # do disconnections and cleanups
    pass

def getData(ads):
    return json.dumps(ads, indent=4)

def main():
        evt_id = 0

        while True:
            evt_id +=1
            ads = {}
            ads.update({"id": evt_id})

            t0 = strftime("%Y-%m-%d %H:%M:%S")
            ads.update({"t0": t0})

            t1 = time.perf_counter()
            ads.update({"t1": "{0:.4f}".format(t1)})

            analog = {}

            # formatting takes time, may consider moving it upstream along
            # with 'averaging'
            if ads_CHAN_0:
                    analog.update({"chan0value": "{0:.4f}".format(chan0.value)})
                    analog.update({"chan0voltage": "{0:.4f}".format(chan0.voltage)})

            if ads_CHAN_1:
                    analog.update({"chan1value": "{0:.4f}".format(chan1.value)})
                    analog.update({"chan1voltage": "{0:.4f}".format(chan1.voltage)})

            if ads_CHAN_2:
                    analog.update({"chan2value": "{0:.4f}".format(chan2.value)})
                    analog.update({"chan2voltage": "{0:.4f}".format(chan2.voltage)})

            if ads_CHAN_3:
                    analog.update({"chan3value": "{0:.4f}".format(chan3.value)})
                    analog.update({"chan3voltage": "{0:.4f}".format(chan3.voltage)})

            t2 = time.perf_counter()
            ads.update({"d": "{0:.4f}".format(t2 - t1)})

            ads.update({"analog" : analog})

            print(getData(ads))

if __name__ == "__main__":
    main()
