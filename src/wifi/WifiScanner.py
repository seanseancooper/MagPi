import threading
import time
import json
from datetime import datetime
from collections import defaultdict

from flask.signals import Namespace
from contextlib import contextmanager

from src.config.__init__ import readConfig

from src.lib.utils import get_location, format_time
from src.wifi.lib.wifi_utils import write_to_scanlist, print_signals

from src.wifi.lib.WifiSignalPoint import WifiSignalPoint
from src.wifi.WifiWorker import WifiWorker

import logging

# TODO: events to flask subsystem; NET module
wifi_signals = Namespace()
wifi_started = wifi_signals.signal('WIFI START')
wifi_updated = wifi_signals.signal('WIFI UPDATED')
wifi_failed = wifi_signals.signal('WIFI FAILED')
wifi_stopped = wifi_signals.signal('WIFI STOP')

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')


class WifiScanner(threading.Thread):
    """ Wifi Scanner class; poll the wifi, match BSSID and report as parsed_signals. """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.retriever = None

        self.searchmap = {}
        self.stats = {}                         # new, not yet used.

        self.parsed_signals = []
        ''' all wifi signals represented as a list of dictionaries.  '''

        self.workers = []                       # list of workers assigned to monitor a discrete signal.
        self.tracked_signals = {}               # parsed_signals is a list, this is a map. stinky.
        self.ghost_signals = []                 # signals no longer received, but tracked -- 'ghost' signals
        self.signal_cache = defaultdict(list)   # a mapping of lists of SignalPoint for all signals received.

        self.blacklist = {}                     # ignored signals
        self.sort_order = "Signal"              # sort order for printed output; consider not support printing.
        self.reverse = False                    # reverse the sort...

        # TODO: timekeeping
        self.start_time = datetime.now()
        self.elapsed = "00:00:00"               # should be a timedelta.
        self.polling_count = 0                  # iterations in this run.

        self.latitude = 0.0                     # this lat; used in SignalPoint creation
        self.longitude = 0.0                    # this lon; used in SignalPoint creation

        self._OUTFILE = None
        self.OUTDIR = None
        self.DEBUG = False

    def compare_MFCC(self):
        # TODO: just not here
        pass

    def analyze_periodicity(self):
        # TODO: just not here
        pass

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
        self.OUTDIR = self.config['OUTFILE_PATH']

        # TODO: make the worker append itself when created.
        [self.workers.append(WifiWorker(BSSID)) for BSSID in self.searchmap.keys()]
        [self.config_worker(worker) for worker in self.workers]

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

    def makeSignalPoint(self, bssid, signal):
        sgnlPt = WifiSignalPoint(bssid, self.longitude, self.latitude, signal)
        self.signal_cache[bssid].append(sgnlPt)

        def manage_signal_cache(_bssid):
            while len(self.signal_cache[_bssid]) >= self.config['SIGNAL_CACHE_MAX']:
                self.signal_cache[_bssid].pop(0)

        manage_signal_cache(bssid)

        return sgnlPt

    def update_signal(self, sgnl, worker, fmt):
        """ update a signal with data from it's worker """

        # TODO: this is brittle, stinky code.
        sgnl['Vendor'] = worker.vendor
        sgnl['Channel'] = worker.channel
        sgnl['Frequency'] = worker.frequency
        sgnl['Quality'] = worker.quality
        sgnl['Encryption'] = worker.is_encrypted
        sgnl['Signal'] = worker.signal

        sgnl['created'] = format_time(worker.created, fmt)
        sgnl['updated'] = format_time(worker.updated, fmt)
        sgnl['elapsed'] = format_time(datetime.strptime(str(worker.elapsed), "%H:%M:%S.%f"), fmt)

        sgnl['is_mute'] = worker.is_mute
        sgnl['tracked'] = worker.tracked

        sgnl['signal_cache'] = [json.dumps(sgnl.get()) for sgnl in self.signal_cache[worker.bssid]]
        sgnl['results'] = [json.dumps(result) for result in worker.test_results]

    def update(self, bssid, o):
        worker = self.get_worker(bssid)
        sgnl = {'BSSID': bssid, 'SSID': worker.ssid}
        self.update_signal(sgnl, worker, self.config.get('TIME_FORMAT', "%H:%M:%S"))
        o.append(sgnl)

    def update_ghosts(self):
        """ find, load and update ghosts """

        # TODO: removval from either tracked or parsed removes *entire*
        #  collection of ghosts due to using frozenset.
        tracked = frozenset([key['BSSID'] for key in self.get_tracked_signals()])
        parsed = frozenset([key['BSSID'] for key in self.parsed_signals.copy()])
        self.ghost_signals = tracked.difference(parsed)

        def update_ghost(item):
            self.get_worker(item).signal = -99
            self.get_worker(item).updated = datetime.now()
            self.makeSignalPoint(str(item), self.get_worker(item).signal)

        [update_ghost(item) for item in self.ghost_signals]

    def parse_signals(self, readlines):
        self.parsed_signals = self.retriever.get_parsed_cells(readlines)

    def get_parsed_signals(self):
        """ updates and returns ALL parsed SIGNALS """
        fmt = self.config.get('TIME_FORMAT', "%H:%M:%S")
        self.elapsed = format_time(datetime.strptime(str(datetime.now() - self.start_time), "%H:%M:%S.%f"), fmt)
        [self.update_signal(sgnl, self.get_worker(sgnl['BSSID']), fmt) for sgnl in self.parsed_signals]

        return self.parsed_signals

    def get_tracked_signals(self):
        """ update and return ONLY tracked signals """
        o = []
        [self.update(bssid, o) for bssid in self.tracked_signals]
        return o

    def get_ghost_signals(self):
        """ update and return ghost signals """
        o = []
        [self.update(item, o) for item in self.ghost_signals]
        return o

    def stop(self):
        write_to_scanlist(self.config, self.tracked_signals)
        [worker.stop() for worker in self.workers]
        self.parsed_signals.clear()
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
                self.update_ghosts()
                get_location(self)

                def blacklist(sgnl):
                    if sgnl['BSSID'] in self.blacklist.keys():
                        try:
                            self.parsed_signals.remove(sgnl)
                        except Exception: pass
                [blacklist(sgnl) for sgnl in self.parsed_signals.copy()]

                if self.config['PRINT_SIGNALS']:
                    if self.config['SORT_SIGNALS']:
                        self.parsed_signals.sort(key=lambda el: el[self.sort_order], reverse=self.reverse)
                    try:
                        print_signals(self.parsed_signals, list(self.parsed_signals[0].keys()))
                    except IndexError: pass

                [worker.run() for worker in self.workers]

                self.elapsed = format_time(datetime.strptime(str(datetime.now() - self.start_time), "%H:%M:%S.%f"), self.config.get('TIME_FORMAT', "%H:%M:%S"))
                wifi_updated.send(self)

                print(f"WifiScanner [{self.polling_count}] {format_time(datetime.now(), self.config.get('TIME_FORMAT', '%H:%M:%S'))} {self.elapsed} {len(self.parsed_signals)} signals, {len(self.tracked_signals)} tracked, {len(self.ghost_signals)} ghosts")
                self.polling_count += 1
                time.sleep(self.config.get('SCAN_TIMEOUT', 5))
            else:
                wifi_failed.send(self)
                print(f"looking for data [{self.polling_count}] {format_time(datetime.now(), self.config.get('TIME_FORMAT', '%H:%M:%S'))}... is wifi available?")
                time.sleep(1)
