from datetime import datetime, timezone, timedelta
from collections import defaultdict

from src.config import readConfig
from src.map.gps import get_location

from src.lib.Worker import Worker

import logging

logger_root = logging.getLogger('root')
speech_logger = logging.getLogger('speech_logger')


class Tracker(object):
    """ Generic Tracker has 3 related jobs
     Deconstructs cells: parse the information in received data [cell] into counterpart 'Worker' attributes that
     never change. This Worker is associated by it's ident and identified by worker_id.

     Assigns Workers: Instance a Worker to track the cell over its lifetime and create signalpoints for the type.

     Tracks lif of cells: keeps up with stats on when cell last seen, tracked, etc using mappings internal to Scanner
     that instanced this Tracker.
     """

    def __init__(self):
        super().__init__()

        self.config = {}

        self.searchmap = {}

        self.parsed_cells = [defaultdict()]         # parsed cells from retriever...
        self.parsed_signals = [defaultdict()]       # product of scanning
        self.polling_count = 0

        self.workers = []                           # list of workers assigned to monitor a discrete signal.
        self.tracked_signals = []                   # parsed_cells currently being tracked.
        self.ghost_signals = []                     # signals no longer received, but tracked -- 'ghost' signals
        self.signal_cache = defaultdict(list)       # a mapping of lists of SignalPoint for all signals received.
        self.signal_cache_max = 160                 # max size of these lists of SignalPoint. overridden via config

        self.blacklist = {}                         # ignored signals
        self.sort_order = None                      # sort order for printed output; consider not support printing.
        self.reverse = False                        # reverse the sort...
        self.tz = None

        self.lat = 0.0                              # this lat; used in SignalPoint creation
        self.lon = 0.0                              # this lon; used in SignalPoint creation

        self._OUTFILE = None
        self.DEBUG = False

        self.CELL_IDENT_FIELD = None
        self.CELL_NAME_FIELD = None
        self.CELL_STRENGTH_FIELD = None
        self.SCAN_GHOSTS = True

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.DEBUG = self.config['DEBUG']
        self.blacklist = self.config['BLACKLIST']
        self.signal_cache_max = self.config.get('SIGNAL_CACHE_MAX', self.signal_cache_max)

        self.CELL_IDENT_FIELD = self.config['CELL_IDENT_FIELD']
        self.CELL_NAME_FIELD = self.config['CELL_NAME_FIELD']
        self.CELL_STRENGTH_FIELD = self.config['CELL_STRENGTH_FIELD']
        self.SCAN_GHOSTS = self.config.get('SCAN_GHOSTS', True)

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

    def load_ghosts(self):
        """ find 'ghost' signals (handle tracked signals not detected
        during parsing), and make a signalpoint for them """
        if self.SCAN_GHOSTS:
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

        for cell in self.parsed_cells:  # list of dicts. TRX will not use this tracker!
            cell['cell_type'] = self.config.get('MODULE', 'generic')

        def _blacklist(cell):
            ''' removes items from *parsed_cells* so they are never evaluated in further processing. '''
            if cell[f'{self.CELL_IDENT_FIELD}'] in self.blacklist.keys():
                try:
                    self.parsed_cells.remove(cell)
                except Exception:
                    pass

        [_blacklist(cell) for cell in self.parsed_cells.copy()]  # remove BLACKLIST cells

        # if self.sort_order:  # sort by CELL_SORT_FIELD for printing. See PRINT_CELLS
        #     self.parsed_cells.sort(key=lambda el: el[self.sort_order], reverse=self.reverse)

        self.load_ghosts()

        # process cells to include 'worker' fields making them signals to fill parsed_signals
        self.parsed_signals.clear()
        for cell in self.parsed_cells:
            wrkr = self.get_worker(cell[f'{self.CELL_IDENT_FIELD}'])
            self.parsed_signals.append(wrkr.get_sgnl())

    def update(self, ident, _signals):
        wrkr = self.get_worker(ident)                   # should be current fields of worker
        _signals.append(wrkr.get_sgnl())

    def process_signals(self):
        """ workers match their cells, add attributes, and make signalpoint """
        # idea: Tracker as ZMQ Publisher and Worker as ZMQ Subscriber (Publisher-Subscriber)
        # idea: 'Tracker' as ZMQ Ventilator and 'Scanner' as ZMQ Sink with Workers as ZMQ Worker (Parallel Pipeline)
        [worker.run() for worker in self.workers]

    def track(self, parsed_cells):

        self.parsed_cells = parsed_cells
        get_location(self)

        self.process_cells()
        self.process_signals()
        return self.parsed_signals
