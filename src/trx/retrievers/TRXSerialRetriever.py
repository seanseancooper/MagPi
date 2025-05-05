import threading
import random
import serial
import time
from datetime import datetime, timedelta

from src.config import readConfig
from src.lib.utils import get_location
from src.trx.lib.TRXWorker import TRXWorker
from src.trx.lib.TRXSignalPoint import TRXSignalPoint


class TRXSerialRetriever(threading.Thread):
    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.config = {}
        self.worker_id = 'TRXSerialRetriever'
        self.signal_cache = []
        self.workers = []
        self.tracked_signals = {}
        self.out = None

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()

        self.device = None
        self.rate = 115200
        self.parity = None
        self.bytesize = 8
        self.stopbits = 1

        self.polling_count = 0
        self.lat = 0.0
        self.lon = 0.0

    def __str__(self):
        return f"TRXRetriever: {self.worker_id}"

    def config_worker(self, worker):
        worker.retriever = self
        worker.config = self.config
        worker.created = datetime.now()
        worker.DEBUG = self.config.get('DEBUG', False)
        worker.cache_max = max(
            int(self.config.get('SIGNAL_CACHE_LOG_MAX', -5)),
            -self.config.get('SIGNAL_CACHE_MAX', 150)
        )

    def get_worker(self, freq):
        for worker in self.workers:
            if worker.freq == freq:
                return worker
        new_worker = TRXWorker(freq)
        self.config_worker(new_worker)
        self.workers.append(new_worker)
        new_worker.run()
        return new_worker

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.device = self.config['DEVICE']
        self.rate = self.config['RATE']
        self.parity = self.config['PARITY']
        self.bytesize = self.config['BYTESIZE']
        self.stopbits = self.config['STOPBITS']

        for freq in self.tracked_signals.keys():
            worker = TRXWorker(freq)
            self.config_worker(worker)
            self.workers.append(worker)

    def make_signal_point(self):
        get_location(self)
        sgnl = TRXSignalPoint(
            self.worker_id, self.lon, self.lat, 0.0, self.out
        )

        while len(self.signal_cache) >= self.config.get('SIGNAL_CACHE_MAX', 150):
            self.signal_cache.pop(0)

        try:
            freq1 = float(self.out.get('FREQ1', 0))
            freq2 = float(self.out.get('FREQ2', 0))
            self.get_worker(max(freq1, freq2))
        except (ValueError, TypeError):
            pass

        self.signal_cache.append(sgnl)

    def get_scanned(self):
        return [sgnl.get() for sgnl in self.signal_cache]

    def get_tracked(self):
        return [sgnl for sgnl in self.tracked_signals]

    def scan(self):
        return self.out

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

    def run(self):
        self.configure('trx.json')

        try:
            if self.config.get('TEST_FILE'):
                self._run_test_mode()
            else:
                self._run_serial_mode()
        except Exception as e:
            print(f'[ERROR] General Exception: {e}')

    def _run_test_mode(self):
        with open(self.config['TEST_FILE'], 'r') as f:
            lines = [line.strip().replace('"', '').replace('<', '').replace('  ', '')
                     for line in f if line.strip()]
        keys = lines[0].split(',')
        fix_time = self.config.get('FIX_TIME', False)

        while True:
            for line in lines[1:]:
                vals = line.split(',')
                self.out = {keys[i]: vals[i] for i in range(len(keys))}

                if fix_time:
                    now = datetime.now()
                    self.out.update({
                        'COMP_DATE': now.strftime(self.config['DATE_FORMAT']),
                        'COMP_TIME': now.strftime(self.config['TIME_FORMAT']),
                        'SCAN_DATE': now.strftime(self.config['DATE_FORMAT']),
                        'SCAN_TIME': now.strftime(self.config['TIME_FORMAT']),
                    })

                self.make_signal_point()
                self.updated = datetime.now()
                self.elapsed = self.updated - self.created
                self.polling_count += 1

                for worker in self.workers:
                    self.config_worker(worker)
                    worker.run()

                if self.DEBUG:
                    print(self.out)

                time.sleep(random.randint(1, self.config['TEST_FILE_TIME_MAX']))

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
                            self.make_signal_point()
                            self.updated = datetime.now()
                            self.elapsed = self.updated - self.created
                            self.polling_count += 1
                            if True:
                                print(f'[SERIAL] {line}')

        except serial.SerialException as e:
            print(f'[ERROR] Serial communication failed: {e}')

    def stop(self):
        print("[USB] Retriever stopping...")

if __name__ == '__main__':
    retriever = TRXSerialRetriever()
    try:
        retriever.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        exit(1)
        # retriever.stop()
        # retriever.join()
