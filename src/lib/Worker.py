import uuid
from datetime import datetime, timedelta

from collections import defaultdict

from src.lib.utils import format_time, format_delta

import logging

wifi_logger = logging.getLogger('wifi_logger')
json_logger = logging.getLogger('json_logger')

class Worker:
    # 🧩 Modeling Components

    # 1. Signal Sources as Agents
    # Each emitter can be modeled as an agent with:
    #     Repetition, pattern, schedule: Worker() could support 'period' data via EAV tables of events; need event 'types'? & tests
    #     Signal fingerprint (modulation, bandwidth, power, etc.)

    def __init__(self, ident):
        self.config = {}
        self.tracker = None
        self.id = None                  # filled if match(), 'marks' SignalPoint type.
        self.ident = ident              # used in object lookups and coloring UI, value of 'self.tracker.CELL_IDENT_FIELD'

        self.created = datetime.now()   # when signal was found
        self.updated = datetime.now()   # when signal was last reported
        self.elapsed = timedelta()      # time signal has been tracked.

        self.is_mute = False            # is muted
        self.tracked = False            # is in scanner.tracked_signals

        self._text_attributes = {}       # mapping of worker attributes

        self.results = []               # a list of test results (this should be local to method)
        self.return_all = False         # return all/any
        self.test_results = {}          # mapping of results
        self.cache_max = 0              # maximum number of SignalPoints displayed in logs
        self._signal_cache_frequency_features = None

        self.DEBUG = False
        self.TYPE = None

    def get_sgnl(self, sgnl=None):
        """ update sgnl (a map) with the following fields in the
        current worker (an object created from a 'cell') note
        this doesn't RETURN a signal type, it populates one """

        if sgnl is None:
            sgnl = defaultdict()

        sgnl['id'] = self.id
        sgnl['type'] = self.TYPE
        sgnl['ident'] = self.ident

        # this is formatting for luxon.js, but is not clean.
        sgnl['created'] = format_time(self.created, "%Y-%m-%d %H:%M:%S")
        sgnl['updated'] = format_time(self.updated, "%Y-%m-%d %H:%M:%S")
        sgnl['elapsed'] = format_delta(self.elapsed, self.config.get('TIME_FORMAT', "%H:%M:%S"))

        sgnl['is_mute'] = self.is_mute
        sgnl['tracked'] = self.tracked

        # sgnl['signal_cache'] = [x.get() for x in self.tracker.signal_cache[self.ident]]
        sgnl['text_attributes'] = self.get_text_attributes()

        # put text attributes into worker representation
        sgnl.update(self.get_text_attributes())

        return sgnl

    def get_type(self):
        return self.TYPE

    def set_type(self, TYPE):
        self.TYPE = TYPE

    def config_worker(self, tracker):
        """ worker append itself, pulls config when created. """
        self.tracker = tracker
        self.config = tracker.config
        self.created = datetime.now()
        self.cache_max = max(int(tracker.config.get('SIGNAL_CACHE_LOG_MAX', -5)), -5)
        self.DEBUG = tracker.config['DEBUG']

    def get_text_attributes(self):
        return self._text_attributes

    def get_text_attribute(self, a):
        try:
            return self._text_attributes[a] or None
        except KeyError:
            return None

    def set_text_attribute(self, a, v):
        self._text_attributes[a] = v

    def set_text_attributes(self, text_data):
        def aggregate(k, v):
            self._text_attributes[k] = v
            if k not in [self.tracker.CELL_IDENT_FIELD, self.tracker.CELL_NAME_FIELD, self.tracker.CELL_STRENGTH_FIELD]:
                text_data.pop(k)
        [aggregate(k, str(v)) for k, v in text_data.copy().items()]

    def make_signalpoint(self, worker_id, ident, sgnl):
        kwargs = {}
        sgnlPt = None

        # SignalPoint       (self, lon, lat, sgnl)
        if self.TYPE == 'generic':
            from src.lib.SignalPoint import SignalPoint
            sgnlPt = SignalPoint(lon=self.tracker.lon, lat=self.tracker.lat, sgnl=sgnl)

        # ARXSignalPoint    (self, worker_id, lon, lat, sgnl)
        if self.TYPE == 'arx':
            from src.arx.lib.ARXSignalPoint import ARXSignalPoint
            sgnlPt = ARXSignalPoint(worker_id=worker_id, lon=self.tracker.lon, lat=self.tracker.lat, sgnl=sgnl)

        # WifiSignalPoint   (self, worker_id, lon, lat, sgnl, bssid=None)
        if self.TYPE == 'wifi':
            kwargs["bssid"] =  self.get_text_attribute(self.tracker.CELL_IDENT_FIELD)
            from src.wifi.lib.WifiSignalPoint import WifiSignalPoint
            sgnlPt = WifiSignalPoint(worker_id=worker_id, lon=self.tracker.lon, lat=self.tracker.lat, sgnl=sgnl, **kwargs)

        # SDRSignalPoint    (self, worker_id, lon, lat, sgnl, array_data=None, audio_data=None, sr=48000)
        if self.TYPE == 'sdr':
            kwargs["array_data"] =  self.get_text_attribute('array_data'),
            kwargs["audio_data"] =  self.get_text_attribute('audio_data'),
            kwargs["sr"] =  self.get_text_attribute('sr'),
            from src.sdr.lib.SDRSignalPoint import SDRSignalPoint
            sgnlPt = SDRSignalPoint(worker_id=worker_id, lon=self.tracker.lon, lat=self.tracker.lat, sgnl=sgnl, **kwargs)

        # TRXSignalPoint    (self, worker_id, lon, lat, sgnl, text_data={}, audio_data=None, signal_type="object", sr=48000)
        if self.TYPE == 'trx':
            kwargs["text_data"] = {} # self._text_attributes,
            kwargs["signal_type"] =  self.get_text_attribute('type'),
            from src.trx.lib.TRXSignalPoint import TRXSignalPoint
            sgnlPt = TRXSignalPoint(worker_id=worker_id, lon=self.tracker.lon, lat=self.tracker.lat, sgnl=sgnl, **kwargs)
            sgnlPt.get() # stop & look

        self.tracker.signal_cache[ident].append(sgnlPt)

        while len(self.tracker.signal_cache[ident]) >= self.tracker.signal_cache_max:
            self.tracker.signal_cache[ident].pop(0)

    def process_cell(self, cell):
        """ update static fields, tests"""

        self.update(cell)

        def test(cell):
            # TODO: use this as an entrypoint to a discrete test in a test
            # framework that would return T or F.
            # need to identify the test...
            # provides [{testname: result}, {...}]
            try:
                tests = self.tracker.searchmap[self.ident]['tests']
                # return all results or only ones that passed?
                self.return_all = self.tracker.searchmap[self.ident]['RETURN_ALL']

                [[self.results.append(eval(str(v.strip() + t_v.strip()))) for t_k, t_v in tests.items() if k == t_k] for k, v in cell.items()]

                while len(self.results) > len(tests):
                    self.results.pop(0)

                self.test_results = zip(tests, self.results)

                # if self.return_all:
                #     return all(self.results)
                # else:
                #     return any(self.results)
            except KeyError:
                return True  # no test, np

            return True

        return cell if test(cell) else None

    def update(self, sgnl):
        """ updates *dynamic* fields"""
        self.updated = datetime.now()
        self.elapsed = self.updated - self.created
        self.tracked = self.ident in self.tracker.tracked_signals
        self.make_signalpoint(self.id, self.ident, int(sgnl.get(self.tracker.CELL_STRENGTH_FIELD, -99)))
        # self._signal_cache_frequency_features = self.extract_signal_cache_features(
        #         [pt.getSgnl() for pt in self.tracker.signal_cache[self.id]]
        # )

    def get_signal_cache_frequency_features(self):
        return self._signal_cache_frequency_features

    def match(self, cell):
        """ match id, derive the 'id' and set mute status """
        if self.ident.upper() == cell[f'{self.tracker.CELL_IDENT_FIELD}'].upper():
            if not self.id:
                # self.id = str(self.ident).replace(':', '').lower()
                self.id = str(uuid.uuid1()).lower()
                self.set_type(cell['type'])
                self.set_text_attributes(cell)
            self.process_cell(cell)
            self.auto_unmute()

    def mute(self):
        from src.lib.utils import mute
        return mute(self)

    def auto_unmute(self):
        """ polled function to UNMUTE signals AUTOMATICALLY after the MUTE_TIME. """
        if self.config['MUTE_TIME'] > 0:
            if datetime.now() - self.updated > timedelta(seconds=self.config['MUTE_TIME']):
                self.is_mute = False

    def add(self, ident):

        try:
            worker = self.tracker.get_worker(ident)

            if worker:
                worker.tracked = True
                self.tracker.tracked_signals.append(ident)
                if worker not in self.tracker.workers:
                    self.tracker.workers.append(worker)
                return True

            return False
        except IndexError:
            return False

    def remove(self, ident):
        _copy = self.tracker.tracked_signals.copy()
        self.tracker.tracked_signals.clear()
        [self.add(remaining) for remaining in _copy if remaining != ident]
        return True

    def stop(self):

        if self.tracked:

            def append_to_outfile(sgnl):
                """Append found cells to a rolling JSON list"""

                formatted = {
                    "id"                : sgnl['id'],
                    "type"              : sgnl['type'],
                    "ident"             : sgnl['ident'],
                    f"{self.tracker.CELL_IDENT_FIELD}"  : sgnl[self.tracker.CELL_IDENT_FIELD],
                    f"{self.tracker.CELL_NAME_FIELD}"   : sgnl[self.tracker.CELL_NAME_FIELD],

                    "created"           : sgnl['created'],
                    "updated"           : sgnl['updated'],
                    "elapsed"           : sgnl['elapsed'],

                    "is_mute"           : sgnl['is_mute'],
                    "tracked"           : sgnl['tracked'],
                    "signal_cache"      : sgnl['signal_cache'],
                    "text_attributes"   : sgnl['text_attributes'],

                }

                json_logger.info({sgnl['BSSID']: formatted})

            append_to_outfile(self.get_sgnl())




    def run(self):
        """ match an ID and populate data """
        [self.match(cell) for cell in self.tracker.parsed_cells]
