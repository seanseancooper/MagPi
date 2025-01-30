#!/usr/bin/python3

import sys
import time
import random
import gpiozero
import logging
import logging.handlers

GPIO = 4
VALUE = 1.0
laser = gpiozero.PWMLED(GPIO)

LOG_FILE = '/var/log/motion/motion.log'
logging.basicConfig(filename=LOG_FILE, filemode='a', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S %z')
logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=20, backupCount=1)

def updateLaser():
    if laser.value == 0.0:
        # wait some random time (250-5000ms)
        _sleeptime = random.uniform(.250, 5.0)
        laser.value = VALUE
        logging.debug("ON: " + str(_sleeptime))
        sys.stdout.flush()

        time.sleep(_sleeptime)

        laser.off()
        logging.debug("OFF")
        sys.stdout.flush()

def main():
    updateLaser()

if __name__ == '__main__':
    main()
