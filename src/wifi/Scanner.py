import threading
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from src.config import readConfig
from src.lib.instrumentation import timer
from src.net.lib.net_utils import get_retriever
from src.lib.utils import get_location, format_time, format_delta
from src.lib.utils import write_to_scanlist
from src.lib.Worker import Worker

import logging

logger_root = logging.getLogger('root')
speech_logger = logging.getLogger('speech_logger')


class Scanner(threading.Thread):
    """Scanner class; poll, match ID and report as 'parsed_cells'. """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.module_retriever = None

        self.searchmap = {}
        self.stats =  {}

        self.parsed_cells = [defaultdict()]                  # parsed cells from retirever...
        self.parsed_signals = [defaultdict()]                # product of scanning

        ''' all items represented as a list of dictionaries.  '''

        self.workers = []                       # list of workers assigned to monitor a discrete signal.
        self.tracked_signals = []               # parsed_cells currently being tracked.
        self.ghost_signals = []                 # signals no longer received, but tracked -- 'ghost' signals
        self.signal_cache = defaultdict(list)   # a mapping of lists of SignalPoint for all signals received.
        self.signal_cache_max = 160             # max size of these lists of SignalPoint. overridden via config

        self.blacklist = {}                     # ignored signals
        self.sort_order = None                  # sort order for printed output; consider not support printing.
        self.reverse = False                    # reverse the sort...

        self.tz = None                          # NEW: timezone
        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()              # elapsed time since created
        self.polling_count = 0                  # iterations in this run.

        self.lat = 0.0                          # this lat; used in SignalPoint creation
        self.lon = 0.0                          # this lon; used in SignalPoint creation

        self._OUTFILE = None
        self.OUTDIR = None
        self.DEBUG = False

        self.CELL_IDENT_FIELD = None
        self.CELL_STRENGTH_FIELD = None

        self.scanned = None

    def configure(self, config_file):
        readConfig(config_file, self.config)
        MQ_AVAILABLE = True

        if MQ_AVAILABLE:
            golden_retriever = get_retriever(self.config['MQ_MODULE_RETRIEVER'])
            self.module_retriever = golden_retriever()
        else:
            golden_retriever = get_retriever(self.config['MODULE_RETRIEVER'])
            self.module_retriever = golden_retriever()

        self.module_retriever.configure(config_file) # use the module config for the retriever

        self.searchmap = self.config['SEARCHMAP']
        self.blacklist = self.config['BLACKLIST']
        self.DEBUG = self.config['DEBUG']
        self.OUTDIR = self.config['OUTFILE_PATH']
        self.signal_cache_max = self.config.get('SIGNAL_CACHE_MAX', self.signal_cache_max)
        self.tz = timezone(timedelta(hours=self.config['INDEX_TIMEDELTA']), name=self.config['INDEX_TZ'])

        self.CELL_IDENT_FIELD = self.config['CELL_IDENT_FIELD']
        self.CELL_STRENGTH_FIELD = self.config['CELL_STRENGTH_FIELD']

        self.sort_order = self.config['CELL_SORT_FIELD']

        [self.workers.append(Worker(ID)) for ID in self.searchmap.keys()]
        [worker.config_worker(self) for worker in self.workers]

    def get_worker(self, ident):
        worker = None
        try:
            worker = [worker for worker in self.workers if worker.ident == ident.upper()][0]
            if worker:
                return worker
        except IndexError:
            worker = Worker(ident)
            worker.config_worker(self)
            self.workers.append(worker)
            worker.run()
        finally:
            return worker

    def load_ghosts(self):
        """ find 'ghost' signals (handle tracked signals not detected
        during parsing), and make a signalpoint for them """
        tracked = frozenset([x for x in self.tracked_signals])
        parsed = frozenset([key[f'{self.CELL_IDENT_FIELD}'] for key in self.parsed_cells])
        self.ghost_signals = tracked.difference(parsed)

        def _ghost(item):
            w = self.get_worker(item)
            w.signal = -99
            w.updated = datetime.now()
            w.make_signalpoint(w.id, w.ident, w.signal)

        [_ghost(item) for item in self.ghost_signals]
    
    def process_cells(self):
        """ retrieve, classify, filter, sort and find missing signals in parsed_cells"""

        for cell in self.parsed_cells:
            try: # not maintainable; see 'multibutton'
                if cell['BSSID']:
                    cell['type'] = 'wifi'
                elif cell['ARX_TYPE']:
                    cell['type'] = 'arx'
                elif cell['SDR_TYPE']:
                    cell['type'] = 'sdr'
                elif cell['ALPHATAG']:
                    cell['type'] = 'trx'
                else:
                    cell['type'] = 'generic'
            except KeyError:
                pass

        def _blacklist(sgnl):
            ''' removes items from *parsed_cells* so they are never evaluated in further processing. '''
            if sgnl[f'{self.CELL_IDENT_FIELD}'] in self.blacklist.keys():
                try:
                    self.parsed_cells.remove(sgnl)
                except Exception: pass

        [_blacklist(sgnl) for sgnl in self.parsed_cells.copy()]  # remove BLACKLIST cells
        
        if self.sort_order:  # sort by CELL_SORT_FIELD for printing. See PRINT_CELLS
            self.parsed_cells.sort(key=lambda el: el[self.sort_order], reverse=self.reverse)

        self.load_ghosts()

        """ 
        process cells to include 'worker' fields making them signals 
        to fill parsed_signals
        """
        self.parsed_signals.clear()
        for sgnl in self.parsed_cells:
            wrkr = self.get_worker(sgnl[f'{self.CELL_IDENT_FIELD}'])
            self.parsed_signals.append(wrkr.get_sgnl())

    def update(self, ident, _signals):
        wrkr = self.get_worker(ident)       # should be current fields of worker
        _signals.append(wrkr.get_sgnl())

    def get_parsed_signals(self):
        return self.parsed_signals or []

    def get_tracked_signals(self):
        """ update, transform and return a list of 'rehydrated' tracked signals """
        _signals = []
        [self.update(ident, _signals) for ident in self.tracked_signals]
        return _signals

    def get_ghost_signals(self):
        """ update, transform and return a list of 'rehydrated' ghost signals """
        _signals = []
        [self.update(ident, _signals) for ident in self.ghost_signals]
        return _signals

    def process_signals(self):
        """ workers match their cells, add attributes, and make signalpoint """
        [worker.run() for worker in self.workers]

    def stop(self):
        write_to_scanlist(self.config, self.get_tracked_signals()) # make into signals....
        [worker.stop() for worker in self.workers]
        self.tracked_signals.clear()
        logger_root.info(f"[{__name__}]: Scanner stopped. {self.polling_count} iterations.")

    def report(self, flag=None):

        # if self.polling_count % 10 == 0:
        #     speech_logger.info(
        #         f'{len(self.parsed_cells)} scanned, {len(self.tracked_signals)} tracked, {len(self.ghost_signals)} ghosts.')

        if not flag:
            print(f"Scanner [{self.polling_count}] "
                f"{format_time(datetime.now(), self.config.get('TIME_FORMAT', '%H:%M:%S'))} "
                f"{self.stats['elapsed']} "
                f"[{self.stats['lat']}, {self.stats['lon']}] "
                f"{self.stats['signals']} signals, "
                f"{self.stats['workers']} workers, "
                f"{self.stats['tracked']} tracked, "
                f"{self.stats['ghosts']} ghosts")

            if self.polling_count > 0 and self.polling_count % 10 == 0:
                speech_logger.info(
                        f'{len(self.parsed_cells)} signals, {len(self.tracked_signals)} tracked, {len(self.ghost_signals)} ghosts.')

        else:
            print(f"looking for data [{self.polling_count}] {format_time(datetime.now(), self.config.get('TIME_FORMAT', '%H:%M:%S'))}...")

    def run(self):

        self.created = datetime.now()
        speech_logger.info('scanner started')

        while True:

            get_location(self)

            self.stats = {
                'created'      : format_time(self.created, self.config['TIME_FORMAT']),
                'updated'      : format_time(self.updated, self.config['TIME_FORMAT']),
                'elapsed'      : format_delta(self.elapsed, self.config['TIME_FORMAT']),
                'polling_count': self.polling_count,
                'lat'          : self.lat,
                'lon'          : self.lon,
                'signals'      : len(self.parsed_signals),
                'workers'      : len(self.workers),
                'tracked'      : len(self.tracked_signals),
                'ghosts'       : len(self.ghost_signals),
            }

            self.scanned = self.module_retriever.scan()

            if len(self.scanned) > 0:

                self.parsed_cells = self.module_retriever.get_parsed_cells(self.scanned)

                self.process_cells()
                self.process_signals()

                self.updated = datetime.now()
                self.elapsed = self.updated - self.created
                
                self.report()
                self.polling_count += 1

            else:
                self.report(True)
                speech_logger.info(f'looking for data {self.polling_count} ...')

            # throttle MQ requests vs. further delay an I/O bound process that blocks....
            time.sleep(self.config.get('SCAN_TIMEOUT', 5))
