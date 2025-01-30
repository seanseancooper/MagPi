#!/usr/bin/python3

import sys
import gpiozero
from aiy.board import Board

GPIO = 4
VALUE = 1.0
BUTTON_GPIO = 23
pwmled = gpiozero.PWMLED(GPIO)
button = gpiozero.Button(BUTTON_GPIO)

# turn off the laser
pwmled.off()

def updateGpio():
    if pwmled.value == 0.0:
        pwmled.value = VALUE
        print("laser ON")
        sys.stdout.flush()
    else:
        pwmled.off()
        print("laser OFF")
        sys.stdout.flush()

def main():
    with Board() as board:
        while True:
            board.button.wait_for_press()
            updateGpio()

if __name__ == '__main__':
    main()
