import os
import platform
import threading
import random
from collections import defaultdict

import usb.core
import usb.backend.libusb1

import time
from datetime import datetime, timedelta

from src.config import readConfig

from src.lib.utils import get_location
from src.trx.lib.TRXSignalPoint import TRXSignalPoint
os.environ['PYUSB_DEBUG'] = 'debug'  # uncomment for verbose pyusb output

# notes
#  see  https://kampi.gitbook.io/avr/lets-use-usb/a-brief-introduction-to-the-usb-protocol




class TRXUSBRetriever(threading.Thread):

    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.config = {}

        self.latitude = 0.0
        self.longitude = 0.0

        self.out = None
        self.signal_cache = []

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()
        self.polling_count = 0
        self.latitude = 0.0
        self.longitude = 0.0

        self.tracked_signals = defaultdict(dict)

        self.retrieving = False
        self.thread = None

    def __str__(self):
        return f"TRXRetriever: "

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
        return [sgnl.get() for sgnl in self.signal_cache]

    def get_tracked(self):
        return [sgnl for sgnl in self.tracked_signals]

    @staticmethod
    def write_to_adu(dev, endpoint, msg_str):
        print("Writing command: {}".format(msg_str))

        # return the string representing the character i
        # byte_str = chr(0x02) + msg_str + chr(0x03)

        num_bytes_written = 0

        try:
            num_bytes_written = dev.write(endpoint, msg_str)
        except usb.core.USBError as e:
            print(e.args)

        return num_bytes_written

    @staticmethod
    def read_from_adu(dev, endpoint, timeout):
        try:
            data = dev.read(endpoint, 64, timeout)
        except usb.core.USBError as e:
            print("Error reading response: {}".format(e.args))
            return None

        byte_str = ''.join(
                chr(n) for n in data[1:])  # construct a string out of the read values, starting from the 2nd byte
        result_str = byte_str.split('\x00', 1)[0]  # remove the trailing null '\x00' characters

        if len(result_str) == 0:
            return None

        return result_str

    def mute(self, uniqId):
        from src.lib.utils import mute

        def find(f):
            return [sgnl for sgnl in self.signal_cache if str(sgnl._id) == f][0]

        sgnl = find(uniqId)
        # SIGNAL: MUTE/UNMUTE
        return mute(sgnl)

    def auto_unmute(self, sgnl):
        ''' this is the polled function to UNMUTE signals AUTOMATICALLY after the MUTE_TIME. '''
        if self.config['MUTE_TIME'] > 0:
            if datetime.now() - sgnl.updated > timedelta(seconds=self.config['MUTE_TIME']):
                sgnl.is_mute = False
                # SIGNAL: AUTO UNMUTE

    def add(self, uniqId):

        try:

            def find(f):
                return [sgnl for sgnl in self.signal_cache if str(sgnl._id) == f][0]

            sgnl = find(uniqId)
            sgnl.tracked = True
            self.tracked_signals.update({uniqId: sgnl})

            # SIGNAL: ADDED ITEM
            return True
        except IndexError:
            return False  # not in tracked_signals

    def remove(self, uniqId):
        _copy = self.tracked_signals.copy()
        self.tracked_signals.clear()

        def find(f):
            return [sgnl for sgnl in self.signal_cache if str(sgnl._id) == f][0]

        sgnl = find(uniqId)
        sgnl.tracked = False

        [self.add(remaining) for remaining in _copy if remaining != uniqId]
        # SIGNAL: REMOVED ITEM
        return True

    def stop(self):
        pass
        # if self.sgnl.tracked:
        #     append_to_outfile(self.config, self.__str__())

    def run(self):

        self.configure('trx.json')

        try:
            if self.config['TEST_FILE']:

                lines = [line.strip().replace('"', '').replace('<', '').replace('  ', '') for line in
                         open(self.config['TEST_FILE'], 'r')]
                keys = lines[0].split(',')

                FIX_TIME = True

                while True:
                    for line in lines[1:-1]:
                        vals = line.split(',')
                        self.out = dict([(keys[i], vals[i]) for i in range(len(keys))])
                        if FIX_TIME:
                            # self.out['COMP_DATE'] = format(datetime.now(), self.config['DATE_FORMAT'])
                            # self.out['COMP_TIME'] = format(datetime.now(), self.config['TIME_FORMAT'])
                            self.out['SCAN_DATE'] = format(datetime.now(), self.config['DATE_FORMAT'])
                            self.out['SCAN_TIME'] = format(datetime.now(), self.config['TIME_FORMAT'])
                        time.sleep(random.randint(1, self.config['TEST_FILE_TIME_MAX']))

                        self.makeSignalPoint()

                        print(self.out)
                        # TODO: this needs to update more regularly than
                        #  the current implementation allows
                        self.updated = datetime.now()
                        self.elapsed = self.updated - self.created
                        self.polling_count += 1

                        [sgnl.update(sgnl.tracked) for sgnl in self.signal_cache]
            else:
                try:

                    VENDOR_ID = 10841
                    PRODUCT_ID = 16

                    was_kernel_driver_active = False

                    if platform.system() == 'Windows':
                        backend = None
                        # required for Windows only
                        # libusb DLLs from: https://sourcefore.net/projects/libusb/
                        arch = platform.architecture()
                        if arch[0] == '32bit':
                            backend = usb.backend.libusb1.get_backend(find_library=lambda
                                x: "libusb/x86/libusb-1.0.dll")  # 32-bit DLL, select the appropriate one based on your Python installation
                        elif arch[0] == '64bit':
                            backend = usb.backend.libusb1.get_backend(
                                    find_library=lambda x: "libusb/x64/libusb-1.0.dll")  # 64-bit DLL

                        device = usb.core.find(backend=backend, idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
                    elif platform.system() == 'Linux':
                        device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

                        # if the OS kernel already claimed the device
                        if device.is_kernel_driver_active(0) is True:
                            # tell the kernel to detach
                            device.detach_kernel_driver(0)
                            was_kernel_driver_active = True
                    else:
                        device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

                    if device is None:
                        raise ValueError('Device not found. Please ensure it is connected.')

                    # for cfg in device:
                    #     print(f'cfg : {cfg.bConfigurationValue}')
                    #     for i in cfg:
                    #         print(f'interface number: {i.bInterfaceNumber}')
                    #         for e in i:
                    #             print(f'endpoint address: {e.bEndpointAddress}')

                    # interface number: 0
                        # endpoint address: 129
                        # endpoint address: 1
                    # interface number: 1
                        # endpoint address: 130
                        # endpoint address: 3
                        # endpoint address: 131

                    device.reset()


                    # Set the active configuration to 1
                    # 0 == USB Mass Storage
                    # 1 == CDC Communication.
                    device.set_configuration(1)
                    trx_config = device.get_active_configuration()[(1, 0)]

                    EP_OUT = usb.util.find_descriptor(trx_config,
                                                      custom_match=lambda e: \
                                                          usb.util.endpoint_direction(e.bEndpointAddress) == \
                                                          usb.util.ENDPOINT_OUT)
                    EP_IN = usb.util.find_descriptor(trx_config,
                                                     custom_match=lambda e: \
                                                         usb.util.endpoint_direction(e.bEndpointAddress) == \
                                                         usb.util.ENDPOINT_IN)



                    # # Claim interface
                    # usb.util.claim_interface(device, 0)

                    # Write commands
                    # message = chr(0x02) + 'A' + chr(0x03)
                    message = 'A'
                    chksum = sum(bytes(message, encoding='utf-8')) and 0xFF

                    bytes_written = self.write_to_adu(device, EP_OUT, message)  # send STX A ETX
                    bytes_written = self.write_to_adu(device, EP_OUT, chksum)  # send SUM

                    # Read data back
                    data = self.read_from_adu(device, EP_IN, 200)  # read from EP_IN device with a 200 millisecond timeout

                    if data is not None:
                        print("Received string: {}".format(data))
                        print("Received data as int: {}".format(int(data)))

                    # usb.util.release_interface(device, 1)

                    # This applies to Linux only - reattach the kernel driver if we previously detached it
                    if was_kernel_driver_active:
                        device.attach_kernel_driver(0)

                except Exception as e:
                    print(f'USB Exception {e}')
                finally:
                    pass


        except Exception as e:
            print(f'General Exception {e}')


if __name__ == '__main__':
    print(TRXUSBRetriever().run())
