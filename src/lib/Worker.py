from datetime import datetime, timedelta
from collections import defaultdict
from src.lib.utils import format_time, format_delta, generate_uuid

import logging

wifi_logger = logging.getLogger('wifi_logger')
json_logger = logging.getLogger('json_logger')

class Worker:

    def __init__(self, ident):
        self.config = {}
        self.tracker = None
        self.id = None                  # filled if match(), 'marks' SignalPoint cell_type.
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
        self.cell_type = None

    def config_worker(self, tracker):
        """ worker append itself, pulls config when created. """
        self.tracker = tracker
        self.config = tracker.config
        self.created = datetime.now()
        self.cache_max = max(int(tracker.config.get('SIGNAL_CACHE_LOG_MAX', -5)), -5)
        self.DEBUG = tracker.config['DEBUG']

    def to_map(self):
        """ return the Worker fields as a mapping """

        w = defaultdict()

        w['id'] = self.id
        w['cell_type'] = self.cell_type
        w['ident'] = self.ident

        # this is formatting for luxon.js, but is not clean.
        w['created'] = format_time(self.created, "%Y-%m-%d %H:%M:%S")
        w['updated'] = format_time(self.updated, "%Y-%m-%d %H:%M:%S")
        w['elapsed'] = format_delta(self.elapsed, self.config.get('TIME_FORMAT', "%H:%M:%S"))

        w['is_mute'] = self.is_mute
        w['tracked'] = self.tracked

        w['signal_cache'] = [x.get() for x in self.tracker.signal_cache[self.ident] if x is not None]
        w['text_attributes'] = self.get_text_attributes()

        # wifi: put 'cell' level data (text_attributes) into Worker object (read by UI)
        if w['cell_type'] == 'wifi':
            w.update(self.get_text_attributes())

        return w

    def get_type(self):
        return self.cell_type

    def set_type(self, c_type):
        self.cell_type = c_type

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
            # if k not in [self.tracker.CELL_IDENT_FIELD, self.tracker.CELL_NAME_FIELD, self.tracker.CELL_STRENGTH_FIELD]:
            #     text_data.pop(k)
        [aggregate(k, v) for k, v in text_data.copy().items()]

    def get_signal_cache_frequency_features(self):
        return self._signal_cache_frequency_features

    def make_signalpoint(self, worker_id, ident, sgnl):
        kwargs = {}
        sgnlPt = None

        # SignalPoint       (self, lon, lat, sgnl)
        # if self.cell_type == 'generic':
        #     from src.lib.SignalPoint import SignalPoint
        #     sgnlPt = SignalPoint(lon=self.tracker.lon, lat=self.tracker.lat, sgnl=sgnl)

        # ARXSignalPoint    (self, worker_id, lon, lat, sgnl)
        if self.cell_type == 'arx':
            from src.arx.lib.ARXSignalPoint import ARXSignalPoint
            sgnlPt = ARXSignalPoint(worker_id=worker_id, lon=self.tracker.lon, lat=self.tracker.lat, sgnl=sgnl)

        # WifiSignalPoint   (self, worker_id, lon, lat, sgnl, bssid=None)
        if self.cell_type == 'wifi':
            kwargs["bssid"] =  self.get_text_attribute(self.tracker.CELL_IDENT_FIELD)
            from src.wifi.lib.WifiSignalPoint import WifiSignalPoint
            sgnlPt = WifiSignalPoint(worker_id=worker_id, lon=self.tracker.lon, lat=self.tracker.lat, sgnl=sgnl, **kwargs)

        # SDRSignalPoint    (self, worker_id, lon, lat, sgnl, array_data=None, audio_data=None, sr=48000)
        if self.cell_type == 'sdr':
            kwargs["array_data"] =  self.get_text_attribute('array_data'),
            kwargs["audio_data"] =  self.get_text_attribute('audio_data'),
            kwargs["sr"] =  self.get_text_attribute('sr'),
            from src.sdr.lib.SDRSignalPoint import SDRSignalPoint
            sgnlPt = SDRSignalPoint(worker_id=worker_id, lon=self.tracker.lon, lat=self.tracker.lat, sgnl=sgnl, **kwargs)

        # TRXSignalPoint    (self, worker_id, lon, lat, sgnl, text_data={}, audio_data=None, signal_type="object", sr=48000)
        if self.cell_type == 'trx':
            kwargs["text_data"] = self._text_attributes,
            kwargs["signal_type"] =  'object',
            from src.trx.lib.TRXSignalPoint import TRXSignalPoint
            sgnlPt = TRXSignalPoint(worker_id=worker_id, lon=self.tracker.lon, lat=self.tracker.lat, sgnl=sgnl, **kwargs)
            sgnlPt.get() # stop & look

        self.tracker.signal_cache[ident].append(sgnlPt)

        while len(self.tracker.signal_cache[ident]) >= self.tracker.signal_cache_max:
            self.tracker.signal_cache[ident].pop(0)

    def process_cell(self, cell):
        """ set static fields """
        if self.ident.upper() == cell[f'{self.tracker.CELL_IDENT_FIELD}'].upper():
            if not self.id:
                try:
                    self.id = cell['id']                    # fail on items w/o id
                except KeyError:
                    self.id = str(generate_uuid()).lower()  # sets id for new items
                self.set_type(cell['cell_type'])
                self.set_text_attributes(cell)

            if self.config['MUTE_TIME'] > 0:                # auto unmute??
                if datetime.now() - self.updated > timedelta(seconds=self.config['MUTE_TIME']):
                    self.is_mute = False

            """ update *dynamic* fields"""
            self.updated = datetime.now()
            self.elapsed = self.updated - self.created
            self.tracked = self.ident in self.tracker.tracked_signals
            self.make_signalpoint(self.id, self.ident, int(cell.get(self.tracker.CELL_STRENGTH_FIELD, -99)))

        return cell # look @ SDR; I don't think this is needed

    def add(self, ident):

        try:
            worker = self.tracker.get_worker(ident)

            if worker:
                worker.tracked = True
                self.tracker.tracked_signals.append(ident)
                if worker not in self.tracker.workers:
                    self.tracker.workers.append(worker)
                print(f"added to cached  {ident}")
                return True

            return False
        except IndexError:
            return False

    def remove(self, ident):
        _copy = self.tracker.tracked_signals.copy()
        self.tracker.tracked_signals.clear()
        [self.add(remaining) for remaining in _copy if remaining != ident]
        print(f"removed from cached  {ident}")
        return True

    def mute(self):
        from src.lib.utils import mute
        return mute(self)

    def stop(self):

        if self.tracked:

            # move me
            def append_to_outfile(sgnl):

                formatted = {

                    "id"                                : sgnl['id'],
                    "type"                              : sgnl['type'],
                    "ident"                             : sgnl['ident'],
                    f"{self.tracker.CELL_IDENT_FIELD}"  : sgnl[self.tracker.CELL_IDENT_FIELD],
                    f"{self.tracker.CELL_NAME_FIELD}"   : sgnl[self.tracker.CELL_NAME_FIELD],

                    "created"                           : sgnl['created'],
                    "updated"                           : sgnl['updated'],
                    "elapsed"                           : sgnl['elapsed'],

                    "is_mute"                           : sgnl['is_mute'],
                    "tracked"                           : sgnl['tracked'],
                    "signal_cache"                      : sgnl['signal_cache'],
                    "text_attributes"                   : sgnl['text_attributes'],

                }

                json_logger.info({sgnl[f"{self.tracker.CELL_IDENT_FIELD}"]: formatted})

            append_to_outfile(self.to_map())

    def run(self):
        # this is long-standing ugly; I should not be brute-forcing matches
        # across parsed_cells to know what cell to operate on.

        [self.process_cell(cell) for cell in self.tracker.parsed_cells]
