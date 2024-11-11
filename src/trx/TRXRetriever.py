import os
import threading
import random

import serial

import time
from datetime import datetime

from src.config import CONFIG_PATH, readConfig

import logging


class TRXRetriever(threading.Thread):

    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.config = {}

        self.device = None
        self.rate = 0
        self.parity = None
        self.bytesize = None
        self.stopbits = None

        self.out = None

        self.retrieving = False
        self.thread = None

    def __str__(self):
        return {f"TRXRetriever: "}

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.device = self.config['DEVICE']
        self.rate = self.config['RATE']
        self.parity = eval(self.config['PARITY'])
        self.bytesize = eval(self.config['BYTESIZE'])
        self.stopbits = eval(self.config['STOPBITS'])

    def run(self):

        self.configure(os.path.join(CONFIG_PATH, 'trx.json'))

        try:
            if self.config['TEST_FILE']:

                lines = [line.strip().replace('"', '').replace('<', '').replace('  ', '') for line in open(self.config['TEST_FILE'], 'r')]
                keys = lines[0].split(',')

                FIX_TIME = False

                while True:
                    for line in lines[1:-1]:
                        vals = line.split(',')
                        self.out = dict([(keys[i], vals[i]) for i in range(len(keys))])
                        if FIX_TIME:
                            self.out['COMP_DATE'] = format(datetime.now(), self.config['DATE_FORMAT'])
                            self.out['COMP_TIME'] = format(datetime.now(), self.config['TIME_FORMAT'])
                            self.out['SCAN_DATE'] = format(datetime.now(), self.config['DATE_FORMAT'])
                            self.out['SCAN_TIME'] = format(datetime.now(), self.config['TIME_FORMAT'])
                        time.sleep(random.randint(1, self.config['TEST_FILE_TIME_MAX']))
                        print(f'{self.out}')
            else:

                # <STX>  An ASCII “Start of Text” symbol (0x02)
                STX = b'\x02'

                # <msgCode>  A single character code that represents the command
                # or response message type. Please be aware that this code is case
                # sensitive (i.e. T and t are not the same)
                msgCode = b'P'

                # <msgData>  The data that accompanies a command or a response.
                # Not all requests require this item. The length and format of
                # this data depends on the type of request being made.
                msgData = b''

                # <ETX>  An ASCII “End of Text” symbol (0x03)
                ETX = b'\x03'

                # <sum> An unsigned char type sum of all bytes starting with
                # <msgCode> up to and including <ETX> anded with the value 0xFF.
                # This value must be calculated and sent with every command
                # and response for error checking.
                SUM = sum(msgCode + ETX) and b'\xFF'
                try:

                    with serial.Serial(self.device, self.rate, parity=self.parity, bytesize=self.bytesize, stopbits=self.stopbits, timeout=1) as ser:
                        while ser.is_open:
                            ser.write(STX + msgCode + ETX + bytes(SUM))
                            self.out = ser.readline()
                            # self.out = ser.read(10)
                            print(f'{self.out}')

                except Exception as e:
                    print(f'{e}')

        except Exception as e:
            print(f'{e}')


if __name__ == '__main__':
    print(TRXRetriever().run())
