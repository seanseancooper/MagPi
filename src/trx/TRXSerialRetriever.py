import os
import threading
import random

import serial

import time
from datetime import datetime, timedelta

from src.config import CONFIG_PATH, readConfig

from src.lib.utils import get_location
from src.trx.TRXWorker import TRXWorker
from src.trx.lib.TRXSignalPoint import TRXSignalPoint


class TRXSerialRetriever(threading.Thread):

    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.config = {}

        self.device = None  # ioreg -r -c IOUSBHostDevice -l
        self.rate = 0
        self.parity = None
        self.bytesize = None
        self.stopbits = None

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

        self.tracked_signals = {}
        self.workers = []

        self.retrieving = False
        self.thread = None

    def __str__(self):
        return f"TRXRetriever: "

    def config_worker(self, worker):
        worker.retriever = self
        worker.config = self.config
        worker.created = datetime.now()
        worker.DEBUG = self.config['DEBUG']
        worker.cache_max = max(int(self.config.get('SIGNAL_CACHE_LOG_MAX', -5)), -(self.config.get('SIGNAL_CACHE_MAX')))

    def get_worker(self, freq):
        worker = None
        try:
            worker = [worker for worker in self.workers if worker.freq == freq][0]
            if worker:
                return worker
        except IndexError:
            worker = TRXWorker(freq)
            self.config_worker(worker)
            self.workers.append(worker)
            worker.run()
        finally:
            return worker

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.device = self.config['DEVICE']
        self.rate = self.config['RATE']
        self.parity = eval(self.config['PARITY'])
        self.bytesize = eval(self.config['BYTESIZE'])
        self.stopbits = eval(self.config['STOPBITS'])

        [self.workers.append(TRXWorker(f)) for f in self.tracked_signals.keys()]
        [self.config_worker(worker) for worker in self.workers]

    def get_scan(self):
        return self.out

    def makeSignalPoint(self):
        get_location(self)
        sgnl = TRXSignalPoint(self.longitude, self.latitude, self.out)

        def manage_signal_cache():
            while len(self.signal_cache) >= self.config.get('SIGNAL_CACHE_MAX', 150):
                self.signal_cache.pop(0)

        manage_signal_cache()

        # not quite, but close
        freq1 = self.out.get('FREQ1')
        freq2 = self.out.get('FREQ2')
        self.workers.append(TRXWorker(max(freq2, freq1)))

        self.signal_cache.append(sgnl)

    def get_scanned(self):
        return [sgnl.get() for sgnl in self.signal_cache]

    def stop(self):
        pass

    def run(self):
        #  re-read config every pass.
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

                        # TODO: this needs to update more regularly than
                        #  the current implementation allows
                        self.updated = datetime.now()
                        self.elapsed = self.updated - self.created
                        self.polling_count += 1

                        [self.config_worker(worker) for worker in self.workers]
                        [worker.run() for worker in self.workers]
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
                    with serial.Serial(self.device,
                                       self.rate,
                                       parity=self.parity,
                                       bytesize=self.bytesize,
                                       stopbits=self.stopbits,
                                       timeout=None,
                                       # xonxoff=True,
                                       # rtscts=True,
                                       # dsrdtr=True
                                       ) as ser:
                        # ser.flushInput()
                        # ser.flushOutput()


                        # while True:
                        #     bytesToRead = ser.inWaiting()
                        #     ser.read(bytesToRead)
                        ALL = STX + msgCode + msgData + ETX + bytes(SUM, 'utf_8')
                        ser.write(ALL)

                        print('start:')
                        for readline in ser:
                            # self.out = ser.readline()
                            # self.out = ser.read(10)
                            print(f'read: {ser.read()}')
                            print(f'readline: {readline}')
                            print(f'line: {readline}')

                except Exception as e:
                    print(f'Serial Exception {e}')
                finally:
                    pass
                    ser.close()

        except Exception as e:
            print(f'General Exception {e}')


if __name__ == '__main__':
    print(TRXSerialRetriever().run())
