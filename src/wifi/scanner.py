import threading
import time
import json
from datetime import datetime
from collections import defaultdict
import requests
from flask.signals import Namespace
from contextlib import contextmanager

from src.config.__init__ import readConfig

from src.wifi.lib.wifi_utils import write_trackedJSON
from src.wifi.lib.iw_parse import print_table

from src.wifi.lib.SignalPoint import SignalPoint
from src.wifi.WifiWorker import WifiWorker

import logging

wifi_signals = Namespace()
wifi_started = wifi_signals.signal('WIFI START')
wifi_updated = wifi_signals.signal('WIFI UPDATED')
wifi_failed = wifi_signals.signal('WIFI FAILED')
wifi_stopped = wifi_signals.signal('WIFI STOP')

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')

wifi_retrievers = {}


def format_time(_, fmt):
    return f'{_.strftime(fmt)}'


class WifiScanner(threading.Thread):
    """ Wifi Scanner class; poll the wifi, match BSSID and report as parsed_signals. """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.retriever = None

        self.searchmap = {}
        self.stats = {}                         # new, not yet used.

        self.parsed_signals = []                # signals represented as a list of dictionaries.
        self.workers = []                       # units assigned to monitor a discrete signal
        self.tracked_signals = {}               # parsed_signals is a list, this is a map?!
        self.signal_cache = defaultdict(list)   # a mapping of lists of SignalPoint

        self.blacklist = {}
        self.sort_order = "Signal"
        self.reverse = False

        # TODO: timekeeping
        self.start_time = datetime.now()
        self.elapsed = None
        self.polling_count = 0

        self.latitude = 0.0
        self.longitude = 0.0

        self._OUTFILE = None
        self._OUTDIR = None
        self.DEBUG = False

    def config_worker(self, worker):
        worker.scanner = self
        worker.config = self.config
        worker.created = datetime.now()
        worker.DEBUG = self.config['DEBUG']

    def get_worker(self, bssid):
        worker = None
        try:
            worker = [worker for worker in self.workers if worker.bssid == bssid.upper()][0]
            if worker:
                return worker
        except IndexError:
            worker = WifiWorker(bssid)
            self.config_worker(worker)
            self.workers.append(worker)
            worker.run()
        finally:
            return worker

    @staticmethod
    def get_retriever(name):

        try:
            components = name.split('.')
            mod = __import__(components[0])
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod
        except AttributeError as e:
            wifi_logger.fatal(f'no retriever found {e}')
            exit(1)

    def configure(self, config_file):
        readConfig(config_file, self.config)

        golden_retriever = self.get_retriever("retrievers." + self.config['RETRIEVER'])
        self.retriever = golden_retriever()
        self.retriever.configure(config_file)
        self.searchmap = self.config['SEARCHMAP']
        self.blacklist = self.config['BLACKLIST']
        self.DEBUG = self.config['DEBUG']
        self._OUTDIR = self.config['OUTFILE_PATH']

        [self.workers.append(WifiWorker(BSSID)) for BSSID in self.searchmap.keys()]
        [self.config_worker(worker) for worker in self.workers]

    def print_signals(self, sgnls, columns):
        table = [columns]

        def print_signal(sgnl):
            sgnl_properties = []

            def make_cols(column):
                try:
                    # make boolean a str to print (needs 'width').
                    if isinstance(sgnl[column], bool):
                        sgnl_properties.append(str(sgnl[column]))
                    else:
                        sgnl_properties.append(sgnl[column])
                except KeyError as e:
                    print(f"KeyError getting column for {e}")

            [make_cols(column) for column in columns]
            table.append(sgnl_properties)

        [print_signal(sgnl) for sgnl in sgnls]
        print_table(table)

    def get_location(self):
        """ gets location from GPS endpoint"""
        try:
            resp = requests.get(self.config.get('GPS_ENDPOINT', 'http://gps.localhost:5004/position'))
            GPS = json.loads(resp.text)
            position = dict(GPS['GPS'])
            self.latitude = position.get('LATITUDE', position.get('lat'))
            self.longitude = position.get('LONGITUDE', position.get('lon'))
        except Exception as e:
            wifi_logger.warning(f"GPS Retrieval Error: {e}")

    def makeSignalPoint(self, bssid, signal):
        sgnlPt = SignalPoint(bssid, self.longitude, self.latitude, signal)
        self.signal_cache[bssid].append(sgnlPt)

        def manage_signal_cache(_bssid):
            while len(self.signal_cache[_bssid]) >= self.config['SIGNAL_CACHE_MAX']:
                self.signal_cache[_bssid].pop(0)

        manage_signal_cache(bssid)

        return sgnlPt

    def compare_MFCC(self):
        # TODO: just not here
        pass

    def analyze_periodicity(self):
        # TODO: just not here
        pass

    def update_signal(self, sgnl, worker, fmt):
        ''' update a signal with data from it's worker '''
        sgnl['Vendor'] = worker.vendor
        sgnl['Channel'] = worker.channel
        sgnl['Frequency'] = worker.frequency
        sgnl['Quality'] = worker.quality
        sgnl['Encryption'] = worker.is_encrypted

        sgnl['created'] = format_time(worker.created, fmt)
        sgnl['updated'] = format_time(worker.updated, fmt)
        sgnl['elapsed'] = format_time(datetime.strptime(str(worker.elapsed), "%H:%M:%S.%f"), fmt)

        sgnl['is_mute'] = worker.is_mute
        sgnl['tracked'] = worker.tracked

        sgnl['signal_cache'] = [json.dumps(sgnl.get()) for sgnl in self.signal_cache.get(worker.bssid)]
        sgnl['results'] = str(worker.stats.get('results', [result for result in worker.test_results]))

    def get_parsed_signals(self):  # rename me, easily confused w retriever impl (cells vs. signals)
        ''' updates and returns ALL signals '''
        self.elapsed = datetime.now() - self.start_time
        fmt = self.config.get('TIME_FORMAT', "%H:%M:%S")
        [self.update_signal(sgnl, self.get_worker(sgnl['BSSID']), fmt) for sgnl in self.parsed_signals]

        return self.parsed_signals

    def parse_signals(self, readlines):

        # this returns a list of dicts [{key: value},...] that key is a 'column' name.
        # So, this class needs to deal with conflicting columns names dynamically!!
        # vis å vis multiple scan sources (wifi, and bluetoooth, and sdr, and etc..)
        # Also note that this is only a single retriever dealing with wifi!

        self.parsed_signals = self.retriever.get_parsed_cells(readlines)

    def get_tracked_signals(self):
        ''' update and return ONLY tracked signals '''
        fmt = self.config.get('TIME_FORMAT', "%H:%M:%S")
        o = []

        def update(bssid):
            worker = self.get_worker(bssid)
            sgnl = {'BSSID': bssid, 'SSID': worker.ssid}
            self.update_signal(sgnl, worker, fmt)
            o.append(sgnl)

        [update(bssid) for bssid in [sgnl for sgnl in self.tracked_signals if self.get_worker(sgnl).tracked is True]]
        return o

    def get_missing_signals(self):
        ''' tracked signals MISSING from parsed_signals; 'greyed' out... '''

        parsed = frozenset([key['BSSID'] for key in self.get_parsed_signals()])
        tracked = frozenset([key['BSSID'] for key in self.get_tracked_signals()])
        fmt = self.config.get('TIME_FORMAT', "%H:%M:%S")
        o = []

        def update(bssid):
            worker = self.get_worker(bssid)
            sgnl = {'BSSID': bssid, 'SSID': worker.ssid}
            self.update_signal(sgnl, worker, fmt)
            o.append(sgnl)

        [update(str(item)) for item in tracked.difference(parsed)]
        return o

    def stop(self):
        write_trackedJSON(self.config, self.tracked_signals)
        self.parsed_signals.clear()  # ensure no data is available
        wifi_stopped.send(self)
        wifi_logger.info(f"[{__name__}]: WifiScanner stopped. {self.polling_count} iterations.")

    @contextmanager
    def run(self):

        self.start_time = datetime.now()
        # self.stats =  {}

        wifi_started.send(self)

        while True:

            scanned = self.retriever.scan_wifi()

            if len(scanned) > 0:
                self.parse_signals(scanned)
                self.get_location()

                def blacklist(sgnl):
                    if sgnl['BSSID'] in self.blacklist.keys():
                        try:
                            self.parsed_signals.remove(sgnl)
                        except Exception as e:
                            pass

                [blacklist(sgnl) for sgnl in self.parsed_signals.copy()]

                self.parsed_signals.sort(key=lambda el: el[self.sort_order], reverse=self.reverse)

                try:
                    self.print_signals(self.parsed_signals, list(self.parsed_signals[0].keys()))
                except IndexError: pass

                [worker.run() for worker in self.workers]

                self.polling_count += 1
                wifi_updated.send(self)
                time.sleep(self.config.get('SCAN_TIMEOUT', 5))
            else:
                wifi_failed.send(self)
                print(f"no signals: {self.polling_count}")
