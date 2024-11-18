import os
import threading
import random

import hid

import time
from datetime import datetime

from src.config import CONFIG_PATH, readConfig

from src.lib.utils import get_location
from src.trx.lib.TRXSignalPoint import TRXSignalPoint


class TRXUSBRetriever(threading.Thread):

    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.config = {}

        self.latitude = 0.0
        self.longitude = 0.0

        self.out = None
        self.signal_cache = []

        self.retrieving = False
        self.thread = None

    def __str__(self):
        return {f"TRXRetriever: "}

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def get_scan(self):
        return self.out

    def makeSignalPoint(self):
        get_location(self)
        sgnl = TRXSignalPoint(self.longitude, self.latitude, self.out)

        def manage_signal_cache():
            while len(self.signal_cache) >= self.config.get('SIGNAL_CACHE_MAX', 150):
                self.signal_cache.pop(0)

        manage_signal_cache()
        self.signal_cache.append(sgnl)

    def get_scanned(self):
        return [x.get() for x in self.signal_cache]

    @staticmethod
    def write_to_adu(dev, msg_str):
        print('Writing command: {}'.format(msg_str))

        # message structure:
        #   message is an ASCII string containing the command
        #   8 bytes in length
        #   0th byte must always be 0x01 (decimal 1)
        #   bytes 1 to 7 are ASCII character values representing the command
        #   remainder of message is padded to 8 bytes with character code 0

        byte_str = chr(0x01) + msg_str + chr(0) * max(7 - len(msg_str), 0)

        try:
            num_bytes_written = dev.write(byte_str.encode())
        except IOError as e:
            print('Error writing command: {}'.format(e))
            return None

        return num_bytes_written

    @staticmethod
    def read_from_adu(dev, timeout):
        try:
            # read a maximum of 8 bytes from the device, with a user specified timeout
            data = dev.read(8, timeout)
        except IOError as e:
            print('Error reading response: {}'.format(e))
            return None

        byte_str = ''.join(
                chr(n) for n in data[1:])  # construct a string out of the read values, starting from the 2nd byte

        result_str = byte_str.split('\x00', 1)[0]  # remove the trailing null '\x00' characters

        if len(result_str) == 0:
            return None

        return result_str


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

                        self.makeSignalPoint()

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

                    # find our device
                    idVendor = 10841
                    idProduct = 16
                    kUSBProductString  = "Whistler TRX-1 Scanner"

                    print('Connected devices:')
                    #     The fields of dict are:
                    #
                    #      - 'path'
                    #      - 'vendor_id'
                    #      - 'product_id'
                    #      - 'serial_number'
                    #      - 'release_number'
                    #      - 'manufacturer_string'
                    #      - 'product_string'
                    #      - 'usage_page'
                    #      - 'usage'
                    #      - 'interface_number'
                    for d in hid.enumerate():
                        print('    ADU: {} {} {} {}'.format(d['vendor_id'],
                                                      d['product_id'],
                                                      d['manufacturer_string'],
                                                      d['interface_number'],
                                                      ))
                    print('')

                    # https://www.ontrak.net/pythonhidapi.htm
                    dev = hid.device()
                    dev.open(idVendor, idProduct)

                    # was it found?
                    if dev is None:
                        raise ValueError('Device not found')


                    # clear the read buffer of any unread values
                    # this is important so that we don't read old values from previous requests sent to the device
                    while True:
                        if self.read_from_adu(dev, 200) is None:
                            break

                    bytes_written = self.write_to_adu(dev, 'RPA')  # request the status of PORT A in binary format

                    data = self.read_from_adu(dev, 200)  # read the response from above PA request
                    if data:
                        print('Received string: {}'.format(data))
                    # data_int = int(data) # if you wish to work with the data in integer format
                    # print( 'Received int: {}'.format(data_int))

                    dev.close()
                except Exception as e:
                    print(f'USB Exception {e}')
                finally:
                    pass


        except Exception as e:
            print(f'General Exception {e}')


if __name__ == '__main__':
    print(TRXUSBRetriever().run())
