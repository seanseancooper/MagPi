import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict

from src.config import readConfig
from src.lib.utils import get_location, format_time, format_delta
from src.lib.utils import write_to_scanlist, print_signals
from src.lib.Worker import Worker

import logging

logger_root = logging.getLogger('root')
speech_logger = logging.getLogger('speech_logger')


class Scanner(threading.Thread):
    """Scanner class; poll, match ID and report as 'parsed_signals'. """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.retriever = None

        self.searchmap = {}
        self.stats =  {}

        self.parsed_signals = []
        ''' all items represented as a list of dictionaries.  '''
        self.workers = []                       # list of workers assigned to monitor a discrete signal.
        self.tracked_signals = []               # parsed_signals currently being tracked.
        self.ghost_signals = []                 # signals no longer received, but tracked -- 'ghost' signals

        self.signal_cache = defaultdict(list)   # a mapping of lists of SignalPoint for all signals received.
        self.signal_cache_max = 160             # max size of these lists of SignalPoint. overridden via config

        self.blacklist = {}                     # ignored signals
        self.sort_order = None                  # sort order for printed output; consider not support printing.
        self.reverse = False                    # reverse the sort...

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()              # elapsed time since created
        self.polling_count = 0                  # iterations in this run.

        self.lat = 0.0                          # this lat; used in SignalPoint creation
        self.lon = 0.0                          # this lon; used in SignalPoint creation

        self._OUTFILE = None
        self.OUTDIR = None
        self.DEBUG = False
        self.SIGNAL_IDENT_FIELD = None
        self.SIGNAL_STRENGTH_FIELD = None

    @staticmethod
    def get_retriever(name):

        try:
            components = name.split('.')
            mod = __import__(components[0])
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod
        except AttributeError as e:
            logger_root.fatal(f'no retriever found {e}')
            exit(1)

    def configure(self, config_file):
        readConfig(config_file, self.config)

        golden_retriever = self.get_retriever("retrievers." + self.config['SCANNER_RETRIEVER'])
        self.retriever = golden_retriever()
        self.retriever.configure(config_file)

        self.searchmap = self.config['SEARCHMAP']
        self.blacklist = self.config['BLACKLIST']
        self.DEBUG = self.config['DEBUG']
        self.OUTDIR = self.config['OUTFILE_PATH']
        self.signal_cache_max = self.config.get('SIGNAL_CACHE_MAX', self.signal_cache_max)

        self.SIGNAL_IDENT_FIELD = 'BSSID'
        self.SIGNAL_STRENGTH_FIELD = 'Signal'
        self.sort_order = self.SIGNAL_STRENGTH_FIELD

        [self.workers.append(Worker(ID)) for ID in self.searchmap.keys()]
        [worker.config_worker(self) for worker in self.workers]

    def get_worker(self, id):
        worker = None
        try:
            worker = [worker for worker in self.workers if worker.id == id.upper()][0]
            if worker:
                return worker
        except IndexError:
            worker = Worker(id)
            worker.config_worker(self)
            self.workers.append(worker)
            worker.run()
        finally:
            return worker

    def get_cell(self, id):
        cell = [_ for _ in self.parsed_signals if _['ID'] == id][0]
        return cell

    def update(self, id):
        _signals = []
        """ put id associated signal data into a map as an element in a list of _signals """
        self.get_worker(id).worker_to_sgnl(self.get_worker(id), self.get_worker(id).get())
        _signals.append(self.get_worker(id).get())

    def update_ghosts(self):
        """ find, load and update ghosts """
        tracked = frozenset([x for x in self.tracked_signals])
        parsed = frozenset([key[f'{self.SIGNAL_IDENT_FIELD}'] for key in self.parsed_signals])
        self.ghost_signals = tracked.difference(parsed)

        def update_ghost(item):
            self.get_worker(item).signal = -99
            self.get_worker(item).updated = datetime.now()
            self.get_worker(item).make_signalpoint(self.get_worker(item).id, self.get_worker(item).id, self.get_worker(item).signal)

        [update_ghost(item) for item in self.ghost_signals]

    def parse_signals(self, readlines):
        self.parsed_signals = self.retriever.get_parsed_cells(readlines)

    def get_parsed_signals(self):
        """ updates and returns ALL parsed SIGNALS """
        self.updated = datetime.now()
        self.elapsed = self.updated - self.created

        [self.get_worker(sgnl[f'{self.SIGNAL_IDENT_FIELD}']).worker_to_sgnl(sgnl, self.get_worker(sgnl[f'{self.SIGNAL_IDENT_FIELD}'])) for sgnl in self.parsed_signals]
        return self.parsed_signals

    def get_tracked_signals(self):
        """ update, transform and return a list of 'rehydrated' tracked signals """
        return [self.update(id) for id in self.tracked_signals]

    def get_ghost_signals(self):
        """ update, transform and return a list of 'rehydrated' ghost signals """
        return [self.update(item) for item in self.ghost_signals]

    def stop(self):
        write_to_scanlist(self.config, self.get_tracked_signals())
        [worker.stop() for worker in self.workers]
        self.parsed_signals.clear()
        self.tracked_signals.clear()
        logger_root.info(f"[{__name__}]: Scanner stopped. {self.polling_count} iterations.")

    def report(self):
        # get from stats....
        print(f"Scanner [{self.polling_count}] "
              f"{format_time(datetime.now(), self.config.get('TIME_FORMAT', '%H:%M:%S'))} "
              f"{format_delta(self.elapsed, self.config.get('TIME_FORMAT', '%H:%M:%S'))} "
              f"{len(self.parsed_signals)} scanned, "
              f"{len(self.tracked_signals)} tracked, "
              f"{len(self.ghost_signals)} ghosts")

    def run(self):

        self.created = datetime.now()
        speech_logger.info('scanner started')

        self.stats = {
            'created'      : format_time(self.created, self.config['TIME_FORMAT']),
            'updated'      : format_time(self.updated, self.config['TIME_FORMAT']),
            'elapsed'      : format_delta(self.elapsed, self.config['TIME_FORMAT']),
            'polling_count': self.polling_count,
            'lat'          : self.lat,
            'lon'          : self.lon,
            'workers'      : len(self.workers),
            'tracked'      : len(self.tracked_signals),
            'ghosts'       : len(self.ghost_signals),
        }

        while True:
            scanned = self.retriever.scan()

            if len(scanned) > 0:
                self.parse_signals(scanned)
                self.update_ghosts()
                get_location(self)

                def blacklist(sgnl):
                    if sgnl[f'{self.SIGNAL_IDENT_FIELD}'] in self.blacklist.keys():
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
                self.updated = datetime.now()
                self.elapsed = self.updated - self.created

                if self.polling_count % 10 == 0:
                    speech_logger.info(f'{len(self.parsed_signals)} scanned, {len(self.tracked_signals)} tracked, {len(self.ghost_signals)} ghosts.')

                self.report()
                self.polling_count += 1
            else:
                speech_logger.info(f'looking for data {self.polling_count} ...')
                print(f"looking for data [{self.polling_count}] {format_time(datetime.now(), self.config.get('TIME_FORMAT', '%H:%M:%S'))}...")

            time.sleep(self.config.get('SCAN_TIMEOUT', 5))
