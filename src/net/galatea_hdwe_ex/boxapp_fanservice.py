#!/usr/bin/python3

import sys
import gpiozero
import psutil
import time

TEMP_MAX = 52.0
SLEEP_TIME = 60
###########################

FAN_GPIO = 17

fan = gpiozero.LED(FAN_GPIO) # is this PWM?

# turn off the fan
fan.off()

def updateFan():
    temps = psutil.sensors_temperatures()
    
    temp = None

    for name, entries in temps.items():
        for entry in entries:
            temp = entry.current
    
    if temp < TEMP_MAX:
        print("CPU temperature: {0:.0f}".format(temp))
        sys.stdout.flush()
        fan.off()
    elif temp >= TEMP_MAX:
        if (fan.value == 0.0):
            print("CPU above threshold. Starting FAN: {0:.0f}".format(temp))
            sys.stdout.flush()
        elif fan.value > 0.0:
            print("CPU still above threshold: {0:.0f}".format(temp))
            sys.stdout.flush()

        fan.on()

def main():
    while True:
        updateFan()
        time.sleep(SLEEP_TIME)

if __name__ == '__main__':
    main()
