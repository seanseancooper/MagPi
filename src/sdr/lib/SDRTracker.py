from datetime import datetime, timezone, timedelta
from collections import defaultdict

from src.config import readConfig
from src.map.gps import get_location

from src.lib.Worker import Worker # specialize the worker to the signal

import logging

logger_root = logging.getLogger('root')
speech_logger = logging.getLogger('speech_logger')


class SDRTracker(object):
    """ Generic Tracker class """

    def __init__(self):
        super().__init__()

        self.config = {}

        self.searchmap = {}

        self.parsed_cells = [defaultdict()]                  # parsed cells from retirever...
        self.parsed_signals = [defaultdict()]                # product of scanning
        self.polling_count = 0

        ''' all items represented as a list of dictionaries.  '''
        self.workers = []                           # list of workers assigned to monitor a discrete signal.
        self.tracked_signals = []                   # parsed_cells currently being tracked.
        self.ghost_signals = []                     # signals no longer received, but tracked -- 'ghost' signals
        self.signal_cache = defaultdict(list)       # a mapping of lists of SignalPoint for all signals received.
        self.signal_cache_max = 160                 # max size of these lists of SignalPoint. overridden via config

        self.blacklist = {}                     # ignored signals
        self.sort_order = None                  # sort order for printed output; consider not support printing.
        self.reverse = False                    # reverse the sort...
        self.tz = None

        self.lat = 0.0  # this lat; used in SignalPoint creation
        self.lon = 0.0  # this lon; used in SignalPoint creation

        self._OUTFILE = None
        self.DEBUG = False

        self.CELL_IDENT_FIELD = None
        self.CELL_NAME_FIELD = None
        self.CELL_STRENGTH_FIELD = None

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.DEBUG = self.config['DEBUG']
        self.blacklist = self.config['BLACKLIST']
        self.signal_cache_max = self.config.get('SIGNAL_CACHE_MAX', self.signal_cache_max)

        self.CELL_IDENT_FIELD = self.config['CELL_IDENT_FIELD']
        self.CELL_NAME_FIELD = self.config['CELL_NAME_FIELD']
        self.CELL_STRENGTH_FIELD = self.config['CELL_STRENGTH_FIELD']

        self.sort_order = self.config['CELL_SORT_FIELD']
        self.tz = timezone(timedelta(hours=self.config['INDEX_TIMEDELTA']), name=self.config['INDEX_TZ'])

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

    def process_cells(self):
        """ retrieve, classify, filter, sort and find missing signals in parsed_cells"""

        for cell in self.parsed_cells:
            try:  # not maintainable; see 'multibutton'
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

    def process_signals(self):
        """ workers match their cells, add attributes, and make signalpoint """
        [worker.run() for worker in self.workers]

    def track(self, parsed_cells):

        self.parsed_cells = parsed_cells
        get_location(self)

        if len(self.parsed_cells) > 0:
            self.process_signals()
            return self.parsed_signals
