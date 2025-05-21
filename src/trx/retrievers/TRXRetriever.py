import platform
import threading
import time
from datetime import datetime, timedelta
import random

import serial

import usb.core
import usb.util
import usb.backend.libusb1

from src.config import readConfig
from src.map.gps import get_location
from src.lib.Worker import Worker
from src.trx.lib.TRXSignalPoint import TRXSignalPoint


def find_device(vendor_id, product_id):
    if platform.system() == 'Windows':
        arch = platform.architecture()[0]
        dll_path = "libusb/x86/libusb-1.0.dll" if arch == '32bit' else "libusb/x64/libusb-1.0.dll"
        backend = usb.backend.libusb1.get_backend(find_library=lambda x: dll_path)
        dev = usb.core.find(backend=backend, idVendor=vendor_id, idProduct=product_id)
    else:
        dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if dev and dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)  # permission denied

    if dev is None:
        raise ValueError("Device not found. Ensure it's connected.")

    dev.set_configuration(1)
    return dev

def get_endpoints(device, interface_idx=1):
    cfg = device.get_active_configuration()
    intf = cfg[(interface_idx, 0)]

    ep_out = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(
        e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
    ep_in = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(
        e.bEndpointAddress) == usb.util.ENDPOINT_IN)

    return ep_in, ep_out

def send_command(device, endpoint, cmd_bytes):
    try:
        print(f"[USB] Sending: {cmd_bytes}")
        endpoint.write(cmd_bytes)
    except usb.core.USBError as e:
        print(f"[USB] Write error: {e}")

def read_response(device, endpoint, timeout=200):
    try:
        data = endpoint.read(64, timeout)
        response = ''.join(chr(n) for n in data).split('\x00', 1)[0]
        return response
    except usb.core.USBError as e:
        print(f"[USB] Read error: {e}")
        return None

class TRXRetriever(threading.Thread):

    def __init__(self, mode='serial'):
        super().__init__()
        self.DEBUG = False
        self.config = {}
        self.worker_id = 'TRXRetriever'
        self.signal_cache = []
        self.workers = []
        self.tracked_signals = {}
        self.out = None

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()

        self.mode = mode

        self.device = None
        self.rate = 115200
        self.parity = None
        self.bytesize = 8
        self.stopbits = 1

        self.device = None

        self.polling_count = 0
        self.lat = 0.0
        self.lon = 0.0

        self.configure('trx.json')
        self.daemon = True # required to exit thread
        self.start()

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.mode = self.config['USB_SERIAL_MODE']

        self.device = self.config['DEVICE']
        self.rate = self.config['RATE']
        self.parity = self.config['PARITY']
        self.bytesize = self.config['BYTESIZE']
        self.stopbits = self.config['STOPBITS']

    # def config_worker(self, worker):
    #     worker.tracker = self
    #     worker.config = self.config
    #     worker.created = datetime.now()
    #     worker.id = worker.get_text_attribute['id']
    #     worker.ident = worker.get_text_attribute['ident']
    #     worker.DEBUG = self.config.get('DEBUG', False)
    #     worker.cache_max = max(
    #         int(self.config.get('SIGNAL_CACHE_LOG_MAX', -5)),
    #         -self.config.get('SIGNAL_CACHE_MAX', 150)
    #     )
    #
    # def get_worker(self, ident):
    #     for worker in self.workers:
    #         if worker.ident == ident:
    #             return worker
    #     new_worker = Worker(ident)
    #     self.config_worker(new_worker)
    #     self.
    #     .append(new_worker)
    #     new_worker.run()
    #     return new_worker

    def get_scanned(self):
        return [sgnl.get() for sgnl in self.signal_cache]

    def get_tracked(self):
        return [sgnl for sgnl in self.tracked_signals]

    def scan(self):
        return self.out or ''

    def get_parsed_cells(self, scanned):

        # use TRXRetriever fields to store data.
        # internally track broadcasts on frequencies

        scanned.update({'type': 'trx'})
        fix_time = self.config.get('FIX_TIME', False)

        if fix_time:
            now = datetime.now()
            scanned.update({
                'COMP_DATE': now.strftime(self.config['DATE_FORMAT']),
                'COMP_TIME': now.strftime(self.config['TIME_FORMAT']),
                'SCAN_DATE': now.strftime(self.config['DATE_FORMAT']),
                'SCAN_TIME': now.strftime(self.config['TIME_FORMAT']),
            })

        if scanned not in self.signal_cache:
            self.signal_cache.append(scanned)

            # return what Scanner can use and expects to have.
        return self.signal_cache

    def find(self, uniqId):
        return [(self.signal_cache.index(sgnl), sgnl) for sgnl in self.signal_cache if str(sgnl['id']) == uniqId][0]

    def update_cache(self, cache_id, cache_key, cache_value):
        cached = self.signal_cache[cache_id]
        cached.update({cache_key: cache_value})

    def mute(self, uniqId):
        cache_id, sgnl = self.find(uniqId)

        sgnl['is_mute'] = not sgnl['is_mute']
        self.tracked_signals.update({uniqId: sgnl})
        self.update_cache(cache_id, 'is_mute', sgnl['is_mute'])
        print(f"muted {uniqId}")
        return sgnl['is_mute']

    def auto_unmute(self, sgnl):
        ''' this is the polled function to UNMUTE signals AUTOMATICALLY after the MUTE_TIME. '''
        if self.config['MUTE_TIME'] > 0:
            if datetime.now() - sgnl.updated > timedelta(seconds=self.config['MUTE_TIME']):
                sgnl.is_mute = False

    def add(self, uniqId):

        try:

            def find(f):
                return [sgnl for sgnl in self.signal_cache if str(sgnl['id']) == f][0]

            sgnl = find(uniqId)
            sgnl['tracked'] = True
            self.tracked_signals.update({uniqId: sgnl})

            return True
        except IndexError:

            return False  # not in tracked_signals

    def remove(self, uniqId):
        _copy = self.tracked_signals.copy()
        self.tracked_signals.clear()

        def find(f):
            return [sgnl for sgnl in self.signal_cache if str(sgnl['id']) == f][0]

        sgnl = find(uniqId)
        sgnl.tracked = False

        [self.add(remaining) for remaining in _copy if remaining != uniqId]
        return True

    def _run_test_mode(self):
        with open(self.config['TEST_FILE'], 'r') as f:
            lines = [line.strip().replace('"', '').replace('<', '').replace('  ', '')
                     for line in f if line.strip()]
        keys = lines[0].split(',')

        while True:
            # simulate a random amount of radio silence ...
            time.sleep(random.randint(1, self.config['TEST_FILE_TIME_MAX']))

            line = lines[random.randint(1,len(lines)-1)]  # choose a random line

            vals = line.split(',')
            self.out = {keys[i]: vals[i] for i in range(len(keys))}

            from src.lib.utils import generate_uuid
            self.out.update({'id': str(generate_uuid())})
            self.out.update({'ident': self.out['id'].upper().replace('-', '')[0:12]})

            self.updated = datetime.now()
            self.elapsed = self.updated - self.created
            self.polling_count += 1

            if self.DEBUG:
                print(self.out)

            # simulate broadcasting for a random amount of time
            time.sleep(random.randint(1, self.config['TEST_FILE_TIME_MAX']))
            self.out = None # silence again ...

    def _run_serial_mode(self):
        SPACE = b'\x32'
        STX = b'\x02' + SPACE
        msgCode = b'A' + SPACE
        msgData = b'' + SPACE
        ETX = b'\x03'
        checksum = ((sum(msgCode + msgData + ETX)) & 0xFF).to_bytes(1, 'little')

        try:
            with serial.Serial(
                    self.device,
                    self.rate,
                    parity=self.parity,
                    bytesize=self.bytesize,
                    stopbits=self.stopbits,
                    rtscts=True,
                    dsrdtr=True,
                    timeout=self.config.get('SERIAL_TIMEOUT', 5)
            ) as ser:
                ser.write(STX + msgCode + msgData + ETX + checksum)
                print('[INFO] Serial communication started...')

                while True:
                    if ser.in_waiting:
                        line = ser.readline().decode(errors='ignore').strip()
                        if line:
                            self.out = {'RAW': line}
                            # self.make_signal_point()
                            self.updated = datetime.now()
                            self.elapsed = self.updated - self.created
                            self.polling_count += 1
                            if True:
                                print(f'[SERIAL] {line}')

        except serial.SerialException as e:
            print(f'[ERROR] Serial communication failed: {e}')

    def _usb_command_loop(self):
        try:
            device = find_device(10841, 16)
            # device = find_device(self.config.get('SIGNAL_CACHE_MAX', 10841), self.config.get('SIGNAL_CACHE_MAX', 16))
            ep_in, ep_out = get_endpoints(device)
            interval = self.config.get('USB_POLL_INTERVAL', 1)

            while True:
                command = b'A'  # Could rotate more commands here
                send_command(device, ep_out, command)
                response = read_response(device, ep_in)

                if response:
                    print(f"[USB] Got: {response}")
                    self.out = {"RAW": response}
                    # self.make_signal_point()

                self.updated = datetime.now()
                self.elapsed = self.updated - self.created

                time.sleep(interval)

        except Exception as e:
            print(f"[USB] Loop Error: {e}")

    def run(self):
        self.configure('trx.json')

        try:
            if self.config.get('TEST_FILE'):
                self._run_test_mode()
            elif self.mode.lower() == 'usb':
                self._usb_command_loop()
            elif self.mode.lower() == 'serial':     # default
                self._run_serial_mode()
        except Exception as e:
            print(f'[ERROR] General Exception: {e}')

    def stop(self):
        print("TRX Retriever stopping...")
        exit(0) # required to exit thread

if __name__ == '__main__':
    retriever = TRXRetriever()
    retriever.configure('trx.json')
    try:
        while True:
            scanned = retriever.scan()
            if len(scanned) > 0:
                # print(f'scanned: {scanned}')
                # use *current retriever* method to parse what it returned.
                # return objects [cells] that tracker can
                parsed_cells = retriever.get_parsed_cells(scanned)
                import json
                print(f'parsed: {json.dumps(retriever.get_parsed_cells(retriever.scan()))}')

            time.sleep(1)
    except KeyboardInterrupt:
        retriever.stop()
        retriever.join()
