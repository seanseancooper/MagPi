#!/usr/bin/python3

import RPi.GPIO as GPIO
from aiy.board import Board, Led
import psutil
import time

TEMP_MAX = 64.0

###########################

FAN_GPIO = 22
LASER_GPIO = 4 

_ON = 'ON'
_OFF = 'OFF'


GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_GPIO, GPIO.IN)
GPIO.setup(LASER_GPIO, GPIO.IN)


def getState(pin):
    return GPIO.input(pin)

def getTemp():
	temps = psutil.sensors_temperatures()
	temp = None
	
	for name, entries in temps.items():
		for entry in entries:
			temp = entry.current
			print("CPU TEMP: {0:.0f}".format(temp))
			return temp
            
def updateLight(board):
    # look at the state of the laser, fan and temp:
    # OFF ON BLINK BLINK_3 BEACON BEACON_DARK DECAY PULSE_SLOW PULSE_QUICK

    temp = None
    temp = getTemp()
    
    
    if temp < float(TEMP_MAX):
        
        # laser off, fan off
        if getState(LASER_GPIO) == 0 and getState(FAN_GPIO) == 0:
            board.led.state = Led.OFF
        
        # laser off, fan on
        if getState(LASER_GPIO) == 0 and getState(FAN_GPIO) == 1:
            board.led.state = Led.BEACON_DARK
        
        # laser on, fan off
        if getState(LASER_GPIO) == 0 and getState(FAN_GPIO) == 0:
            board.led.state = Led.BEACON
        
        # laser on, fan on
        if getState(LASER_GPIO) == 1 and getState(FAN_GPIO) == 1:
            board.led.state = Led.ON
    
    elif temp > float(TEMP_MAX):
        
        # laser off, fan off
        if getState(LASER_GPIO) == 0 and getState(FAN_GPIO) == 0:
            board.led.state = Led.BLINK
        
        # laser off, fan on
        if getState(LASER_GPIO) == 0 and getState(FAN_GPIO) == 1:
            board.led.state = Led.BLINK_3
        
        # laser on, fan off
        if getState(LASER_GPIO) == 0 and getState(FAN_GPIO) == 0:
            board.led.state = Led.PULSE_QUICK
        
        # laser on, fan on
        if getState(LASER_GPIO) == 1 and getState(FAN_GPIO) == 1:
            board.led.state = Led.PULSE_SLOW

    elif temp == None:
        print('getting temperature failed')
        pass

def main():
    with Board() as board:
        while True:
            updateLight(board)
            time.sleep(1)

if __name__ == '__main__':
    main()
