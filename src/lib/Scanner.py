import threading
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from src.net.lib.net_utils import check_zmq_available
from src.config import readConfig
from src.net.lib.net_utils import load_module
from src.lib.utils import format_time, format_delta
from src.map.gps import get_location
from src.wifi.lib.wifi_utils import write_to_scanlist

import logging

logger_root = logging.getLogger('root')
speech_logger = logging.getLogger('speech_logger')


class Scanner(threading.Thread):
    """Scanner class; poll, match ID and report as 'parsed_cells'. """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.module_retriever = None
        self.module_tracker = None

        self.scanned = None
        self.parsed_signals = []
        self.signal_cache = defaultdict(list)   # mapping of lists of SignalPoint for all signals received.
        self.signal_cache_max = 160             # max size of lists of SignalPoint. overridden via config

        self.stats =  {}
        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()              # elapsed time since created
        self.polling_count = 0                  # iterations in this run.
        self.tz = None

        self.lat = 0.0                          # this lat; used in SignalPoint creation
        self.lon = 0.0                          # this lon; used in SignalPoint creation

        self.DEBUG = False
        self.CELL_IDENT_FIELD = None
        self.CELL_NAME_FIELD = None
        self.CELL_STRENGTH_FIELD = None

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.DEBUG = self.config['DEBUG']
        self.tz = timezone(timedelta(hours=self.config['INDEX_TIMEDELTA']), name=self.config['INDEX_TZ'])
        self.CELL_IDENT_FIELD = self.config['CELL_IDENT_FIELD']
        self.CELL_NAME_FIELD = self.config['CELL_NAME_FIELD']
        self.CELL_STRENGTH_FIELD = self.config['CELL_STRENGTH_FIELD']

        _, ZMQ_OK = check_zmq_available()  # self.config['MODULE'].lower()

        if ZMQ_OK:
            golden_retriever = load_module(self.config['MQ_MODULE_RETRIEVER'])
        else:
            golden_retriever = load_module(self.config['MODULE_RETRIEVER'])

        self.module_retriever = golden_retriever()
        self.module_retriever.configure(config_file)

        # I could import Tracker now...
        module_tracker = load_module(self.config['MODULE_TRACKER'])
        self.module_tracker = module_tracker()
        self.module_tracker.configure(config_file)

        self.signal_cache_max = self.config.get('SIGNAL_CACHE_MAX', self.signal_cache_max)

    def get_parsed_signals(self):
        return self.parsed_signals or []

    def get_workers(self):
        return [worker.to_map() for worker in self.module_tracker.workers]

    def update(self, ident, _signals):
        worker = self.module_tracker.get_worker(ident)                   # should be current fields of worker
        _signals.append(worker.to_map())

    def get_tracked_signals(self):
        """ update, transform and return a list of 'rehydrated' tracked signals """
        _signals = []
        [self.update(ident, _signals) for ident in self.module_tracker.tracked_signals]
        return _signals

    def get_ghost_signals(self):
        """ update, transform and return a list of 'rehydrated' ghost signals """
        _signals = []
        [self.update(ident, _signals) for ident in self.module_tracker.ghost_signals]
        return _signals

    def stop(self):
        write_to_scanlist(self.config, self.get_tracked_signals()) # make into signals....
        [worker.stop() for worker in self.module_tracker.workers]
        self.module_tracker.tracked_signals.clear()
        logger_root.info(f"[{__name__}]: Scanner stopped. {self.polling_count} iterations.")

    def report(self, flag=None):

        if not flag:
            print(f"{self.config['MODULE']}Scanner [{self.polling_count}] "
                f"{format_time(datetime.now(), self.config.get('TIME_FORMAT', '%H:%M:%S'))} "
                f"{self.stats['elapsed']} "
                f"[{self.stats['lat']}, {self.stats['lon']}] "
                f"{self.stats['signals']} signals, "
                f"{self.stats['workers']} workers, "
                f"{self.stats.get('cached', 0)} cached, "
                f"{self.stats['tracked']} tracked, "
                f"{self.stats['ghosts']} ghosts")

            if self.polling_count > 0 and self.polling_count % 10 == 0 and self.config['SPEECH_ENABLED']:
                speech_logger.info(
                        f'{len(self.module_tracker.parsed_cells)} signals, {len(self.module_tracker.tracked_signals)} tracked, {len(self.module_tracker.ghost_signals)} ghosts.')

        else:
            if self.config['SCAN_GHOSTS'] is True:
                print(f"looking for data [{self.polling_count}] {format_time(datetime.now(), self.config.get('TIME_FORMAT', '%H:%M:%S'))}...")

    def run(self):

        self.created = datetime.now()

        while True:

            get_location(self)

            self.stats = {
                'created'      : format_time(self.created, self.config['TIME_FORMAT']),
                'updated'      : format_time(self.updated, self.config['TIME_FORMAT']),
                'elapsed'      : format_delta(self.elapsed, self.config['TIME_FORMAT']),
                'polling_count': self.polling_count,
                'lat'          : self.lat,
                'lon'          : self.lon,
            }

            self.scanned = self.module_retriever.scan()

            if self.scanned:

                parsed_cells = self.module_retriever.get_parsed_cells(self.scanned)

                # pick apart, assign workers (~signalpoints), and track the cells.
                self.parsed_signals = self.module_tracker.track(parsed_cells)

            if self.config['SCAN_GHOSTS'] is True:
                self.stats.update({
                    'signals': len(self.parsed_signals),
                    'workers': len(self.module_tracker.workers),
                    'tracked': len(self.module_tracker.tracked_signals),
                    'ghosts' : len(self.module_tracker.ghost_signals),
                })
            else:
                self.stats.update({
                    'signals': len(self.module_retriever.signal_cache),
                    'workers': len(self.module_tracker.workers),
                    'cached': len(self.module_retriever.tracked_signals),
                    'tracked': len(self.module_tracker.tracked_signals),
                    'ghosts' : 0,
                })

            self.updated = datetime.now()
            self.elapsed = self.updated - self.created

            self.report()
            self.polling_count += 1

            # if self.scanned is None:
            #     self.report(True)
            #     if self.config['SPEECH_ENABLED']:
            #         speech_logger.info(f'looking for data {self.polling_count} ...')

            # throttle MQ requests vs. further delay an I/O bound process that blocks....
            time.sleep(self.config.get('SCAN_TIMEOUT', 5))


if __name__ == '__main__':
    scanner = Scanner()
    scanner.configure('scanner.json')
    t = threading.Thread(target=scanner.run)
    t.start()
