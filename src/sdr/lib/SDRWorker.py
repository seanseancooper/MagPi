import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np

from src.lib.utils import format_time, format_delta, generate_uuid
import logging

from src.sdr.sset.core.signal_model import SignalFrame
from src.sdr.sset.core.time_frequency_frame import TimeFrequencyFrame
from src.sdr.sset.core.signal_collections import TimeFrequencyFrameList, SignalFrameList

sdr_logger = logging.getLogger('sdr_logger')


class SDRWorker(threading.Thread):

    def __init__(self, ident):
        super().__init__()
        self.config = {}
        self.tracker = None
        self.id = None                  # filled if match(), 'marks' SignalPoint cell_type.
        self.sdr_ident = ident          # used in object lookups and coloring UI, value of 'self.tracker.CELL_IDENT_FIELD'

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

        self._ctrl_record = False
        self._ctrl_play = False
        self._ctrl_mute = False
        self._ctrl_solo = False
        self._ctrl_analyze = False
        self._ctrl_demux = False
        self._ctrl_decode = False
        self._ctrl_encode = False
        self._ctrl_filter = False
        self._ctrl_block = False
        self._ctrl_label = False
        self._ctrl_test = False

        self._control_fields = [f for f in dir(self) if f.startswith("_ctrl_")]

        self.signal_frame_list = SignalFrameList([])
        self.tff_frame_list = TimeFrequencyFrameList([])

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
        w['ident'] = self.sdr_ident

        # this is formatting for luxon.js, but is not clean.
        w['created'] = format_time(self.created, "%Y-%m-%d %H:%M:%S")
        w['updated'] = format_time(self.updated, "%Y-%m-%d %H:%M:%S")
        w['elapsed'] = format_delta(self.elapsed, self.config.get('TIME_FORMAT', "%H:%M:%S"))

        w['is_mute'] = self.is_mute
        w['tracked'] = self.tracked

        w['signal_cache'] = [x.get() for x in self.tracker.signal_cache[self.sdr_ident] if x is not None]
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

    def set_control_field(self, attr_field, attr_field_value):
        if attr_field in self._control_fields:
            self.__setattr__(attr_field, attr_field_value)

    def get_control_field(self, attr_field):
        if attr_field in self._control_fields:
            return self.__getattribute__(attr_field)

    def get_signal_cache_frequency_features(self):
        return self._signal_cache_frequency_features

    def make_signalpoint(self, worker_id, ident, sgnl):
        kwargs = {}

        # SDRSignalPoint    (self, worker_id, lon, lat, sgnl, array_data=None, audio_data=None, sr=48000)
        kwargs["array_data"] =  self.get_text_attribute('array_data'),
        kwargs["audio_data"] =  self.get_text_attribute('audio_data'),
        kwargs["sr"] =  self.get_text_attribute('sr'),

        # use SDRSignalPoint for tracking/displays
        from src.sdr.lib.SDRSignalPoint import SDRSignalPoint
        sgnlPt = SDRSignalPoint(worker_id=worker_id, lon=self.tracker.lon, lat=self.tracker.lat, sgnl=sgnl, **kwargs)
        self.tracker.signal_cache[ident].append(sgnlPt)

        # use sset SignalFrame, TimeFrequencyFrame for processing
        start_time = timestamp = time.monotonic()
        duration = 0
        carrier_freq = self.get_text_attribute('frequency')
        bandwidth = self.get_text_attribute('bandwidth')

        freq_min = carrier_freq - bandwidth/2
        freq_max = carrier_freq + bandwidth/2

        tf_matrix = data = np.zeros((4096,))

        domain = 'frequency'
        metadata = self.get_text_attributes()

        sgnlFrm = SignalFrame(timestamp, duration, carrier_freq, bandwidth, data, domain, metadata)
        tfFrm = TimeFrequencyFrame(start_time, duration, freq_min, freq_max, tf_matrix, metadata)

        # add sgnlFrm & tfFrm to sset.collections
        self.signal_frame_list.append(sgnlFrm)
        self.tff_frame_list.append(tfFrm)

        while len(self.tracker.signal_cache[ident]) >= self.tracker.signal_cache_max:
            self.tracker.signal_cache[ident].pop(0)

    def process_cell(self, cell):
        """ set static fields """
        if self.sdr_ident == cell[f'{self.tracker.CELL_IDENT_FIELD}']:
            if not self.id:
                try:
                    self.id = cell['id']                    # fail on items w/o id
                except KeyError:
                    self.id = str(generate_uuid()).lower()     # sets id for new items
                self.set_type(cell['cell_type'])
                self.set_text_attributes(cell)

            if self.config['MUTE_TIME'] > 0:                # auto unmute??
                if datetime.now() - self.updated > timedelta(seconds=self.config['MUTE_TIME']):
                    self.is_mute = False

            """ update *dynamic* fields"""
            self.updated = datetime.now()
            self.elapsed = self.updated - self.created
            self.tracked = self.sdr_ident in self.tracker.tracked_signals
            self.make_signalpoint(self.id, self.sdr_ident, int(cell.get(self.tracker.CELL_STRENGTH_FIELD, -99)))

        return cell

    def add(self, ident):

        try:
            worker = self.tracker.get_worker(ident)

            if worker:
                worker.tracked = True
                self.tracker.tracked_signals.append(ident)
                if worker not in self.tracker.workers:  # why would it not be?
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
    
    def ctrl_record(self):
        print(f'{__name__} executed')
        pass
    
    def ctrl_play(self):
        print(f'{__name__} executed')
        pass

    def ctrl_mute(self):
        print(f'{__name__} executed')
        pass

    def ctrl_solo(self):
        print(f'{__name__} executed')
        pass

    def ctrl_analyze(self):
        print(f'{__name__} executed')
        pass

    def ctrl_demux(self):
        print(f'{__name__} executed')
        pass

    def ctrl_decode(self):
        print(f'{__name__} executed')
        pass

    def ctrl_encode(self):
        print(f'{__name__} executed')
        pass

    def ctrl_filter(self):
        print(f'{__name__} executed')
        pass

    def ctrl_block(self):
        print(f'{__name__} executed')
        pass

    def ctrl_label(self):
        print(f'{__name__} executed')
        pass

    def ctrl_test(self):
        print(f'{__name__} executed')
        pass

    def stop(self):

        if self.tracked:
            pass
            # move me
            # def append_to_outfile(sgnl):
            #
            #     formatted = {
            #
            #         "id"                                : sgnl['id'],
            #         "type"                              : sgnl['type'],
            #         "ident"                             : sgnl['ident'],
            #         f"{self.tracker.CELL_IDENT_FIELD}"  : sgnl[self.tracker.CELL_IDENT_FIELD],
            #         f"{self.tracker.CELL_NAME_FIELD}"   : sgnl[self.tracker.CELL_NAME_FIELD],
            #
            #         "created"                           : sgnl['created'],
            #         "updated"                           : sgnl['updated'],
            #         "elapsed"                           : sgnl['elapsed'],
            #
            #         "is_mute"                           : sgnl['is_mute'],
            #         "tracked"                           : sgnl['tracked'],
            #         "signal_cache"                      : sgnl['signal_cache'],
            #         "text_attributes"                   : sgnl['text_attributes'],
            #
            #     }
            #
            #     json_logger.info({sgnl[f"{self.tracker.CELL_IDENT_FIELD}"]: formatted})
            #
            # append_to_outfile(self.to_map())

    def run(self):
        # this is long-standing ugly; I should not be brute-forcing matches
        # across parsed_cells to know what cell to operate on.

        [self.process_cell(cell) for cell in self.tracker.parsed_cells]
