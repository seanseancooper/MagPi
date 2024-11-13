import encodings
import os
import threading
import random
from collections import defaultdict

import serial

import time
from datetime import datetime

from src.config import CONFIG_PATH, readConfig

import logging


class TRXUSBRetriever(threading.Thread):

    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.config = {}

        self.device = None  # ioreg -r -c IOUSBHostDevice -l
        self.rate = 0
        self.parity = None
        self.bytesize = None
        self.stopbits = None

        self.out = None
        self.signal_cache = []

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

    def get_scan(self):
        return self.out

    def get_scanned(self):
        return self.signal_cache

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
                        self.out = dict( [ (keys[i], vals[i]) for i in range(len(keys)) ] )
                        if FIX_TIME:
                            self.out['COMP_DATE'] = format(datetime.now(), self.config['DATE_FORMAT'])
                            self.out['COMP_TIME'] = format(datetime.now(), self.config['TIME_FORMAT'])
                            self.out['SCAN_DATE'] = format(datetime.now(), self.config['DATE_FORMAT'])
                            self.out['SCAN_TIME'] = format(datetime.now(), self.config['TIME_FORMAT'])
                        time.sleep(random.randint(1, self.config['TEST_FILE_TIME_MAX']))
                        self.signal_cache.insert(-1, self.out)
                        print(self.out)
            else:

                SPACE = b'\x32'
                # <STX>  An ASCII “Start of Text” symbol (0x02)
                STX = b'\x02' + SPACE

                # <msgCode>  A single character code that represents the command
                # or response message type. Please be aware that this code is case
                # sensitive (i.e. T and t are not the same)
                msgCode = bytes('P', 'utf-8') + SPACE   # b'\x80'

                # <msgData>  The data that accompanies a command or a response.
                # Not all requests require this item. The length and format of
                # this data depends on the type of request being made.
                msgData = bytes('', 'utf-8') + SPACE

                # <ETX>  An ASCII “End of Text” symbol (0x03)
                ETX = b'\x03'

                # <sum> An unsigned char type sum of all bytes starting with
                # <msgCode> up to and including <ETX> anded with the value 0xFF.
                # This value must be calculated and sent with every command
                # and response for error checking.
                SUM = (msgCode + msgData + ETX) and '\xFF'


                # +-o Whistler TRX-1 Scanner@14600000  <class IOUSBHostDevice, id 0x100003a9d, registered, matched, active, busy 0 (189 ms), retain 31>
                #   | {
                #   |   "sessionID" = 49650240276763
                #   |   "USBSpeed" = 1
                #   |   "IOServiceLegacyMatchingRegistryID" = 4294982303
                #   |   "idProduct" = 16
                #   |   "iManufacturer" = 1
                #   |   "bDeviceClass" = 0
                #   |   "IOPowerManagement" = {"PowerOverrideOn"=Yes,"CapabilityFlags"=32768,"MaxPowerState"=2,"DevicePowerState"=2,"DriverPowerState"=0,"ChildrenPowerState"=2,"CurrentPowerState"=2}
                #   |   "bcdDevice" = 1
                #   |   "bMaxPacketSize0" = 8
                #   |   "iProduct" = 2
                #   |   "iSerialNumber" = 0
                #   |   "bNumConfigurations" = 1
                #   |   "USB Product Name" = "Whistler TRX_1 Scanner"
                #   |   "USB Address" = 15
                #   |   "locationID" = 341835776
                #   |   "bDeviceSubClass" = 0
                #   |   "bcdUSB" = 512
                #   |   "Built-In" = No
                #   |   "non-removable" = "no"
                #   |   "IOCFPlugInTypes" = {"9dc7b780-9ec0-11d4-a54f-000a27052861"="IOUSBHostFamily.kext/Contents/PlugIns/IOUSBLib.bundle"}
                #   |   "kUSBCurrentConfiguration" = 1
                #   |   "bDeviceProtocol" = 0
                #   |   "USBPortType" = 0
                #   |   "IOServiceDEXTEntitlements" = (("com.apple.developer.driverkit.transport.usb"))
                #   |   "USB Vendor Name" = "Whistler"
                #   |   "Device Speed" = 1
                #   |   "idVendor" = 10841
                #   |   "kUSBProductString" = "Whistler TRX-1 Scanner"
                #   |   "IOGeneralInterest" = "IOCommand is not serializable"
                #   |   "kUSBAddress" = 15
                #   |   "kUSBVendorString" = "Whistler"
                #   |   "IOClassNameOverride" = "IOUSBDevice"
                #   | }
                #   |
                #

                try:
                    import usb.core
                    import usb.util

                    # find our device
                    idVendor = 10841
                    idProduct = 16
                    dev = usb.core.find(idVendor=idVendor, idProduct=idProduct)

                    # was it found?
                    if dev is None:
                        raise ValueError('Device not found')

                    # set the active configuration. With no arguments, the first
                    # configuration will be the active one
                    dev.set_configuration()

                    # get an endpoint instance
                    cfg = dev.get_active_configuration()
                    intf = cfg[(0, 0)]

                    ep = usb.util.find_descriptor(
                            intf,
                            # match the first OUT endpoint
                            custom_match= \
                                lambda e: \
                                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                                    usb.util.ENDPOINT_OUT)

                    assert ep is not None

                    # write the data
                    ALL = STX + msgCode + msgData + ETX + bytes(SUM, 'utf_8')
                    # ep.write('STX A ETX' + SUM)

                    msg = 'STX A ETX' + SUM
                    # ep.write(msg)
                    # assert len(ep.write(1, msg, 100)) == len(msg)
                    # ret = ep.read(0x81, len(msg), 100)
                    # sret = ''.join([chr(x) for x in ret])
                    # assert sret == msg

                    print(ep.read(0))



                except Exception as e:
                    print(f'USB Exception {e}')
                finally:
                    pass
                    # ser.close()

        except Exception as e:
            print(f'General Exception {e}')


if __name__ == '__main__':
    print(TRXUSBRetriever().run())
