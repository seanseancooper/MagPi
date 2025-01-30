#!/usr/bin/python3

import gpiozero
import psutil
import time
import numpy

LED_GPIO = 25
FAN_GPIO = 17 
LASER_GPIO = 4 

led = gpiozero.PWMLED(LED_GPIO)
laser = gpiozero.LED(LASER_GPIO)
fan = gpiozero.LED(FAN_GPIO)

led.value = 0.0

def updateLight():
    # v.01: look at the state of fan and laser, control light
    # v.2 move fan status tio LCD and use light ONKY for laser.
    # need to keep LCD usable by all, so periodic updates

    if fan.value == 0.0:
        if laser.value == 0.0:
            led.value = 0.0
        elif laser.value > 0.0:
            blink()
    elif fan.value > 0.0:
        if laser.value == 0.0:
            biPulse()
        elif laser.value > 0.0:
            led.value = 1.0

def blink3():
    led.value = 1.0
    time.sleep(.1)
    led.value = 0.0
    time.sleep(.1)

    led.value = 1.0
    time.sleep(.1)
    led.value = 0.0
    time.sleep(.1)
    
    led.value = 1.0
    time.sleep(.1)
    led.value = 0.0
    time.sleep(.1)

def blink():
    led.value = 1.0
    time.sleep(.1)
    led.value = 0.0
    time.sleep(.1)
    
def pulse():
    for i in numpy.arange(0.0,1.0,.1):
        led.value = i
        time.sleep(.05)

def biPulse():
    for i in numpy.arange(0.0,1.0,.1):
        led.value = i
        time.sleep(.05)
    for i in numpy.arange(1.0,0.0,-.1):
        led.value = i
        time.sleep(.05)
    led.value = 0.0

def main():
    while True:
        updateLight()
        time.sleep(1)

if __name__ == '__main__':
    main()
