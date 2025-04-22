from datetime import datetime, timedelta

from src.lib.utils import format_time, format_delta, get_me
from src.sdr.lib.SDRSignalPoint import SDRSignalPoint
from src.trx.lib.TRXSignalPoint import TRXSignalPoint
from src.wifi.lib.WifiSignalPoint import WifiSignalPoint
from src.wifi.lib.wifi_utils import append_to_outfile, json_logger
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
        self.scanner = None
        self.id = ''                    # filled if match(), 'marks' SignalPoint type.
        self.ident = ident              # used in object lookups and coloring UI, self.scanner.SIGNAL_IDENT_FIELD

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

    def get(self):
        return get_me(self)

    def worker_to_sgnl(self, worker, sgnl): # this doesn't RETURN a signal, it populates one
        """ update sgnl data map with current info from worker """
        # sgnl['id'] = worker.id
        sgnl[f'{self.scanner.SIGNAL_IDENT_FIELD}'] = worker.ident
        sgnl[self.scanner.SIGNAL_STRENGTH_FIELD] = int(worker.get_text_attribute(self.scanner.SIGNAL_STRENGTH_FIELD))

        # this is formatting for luxon.js, but is not clean.
        sgnl['created'] = format_time(worker.created, "%Y-%m-%d %H:%M:%S")
        sgnl['updated'] = format_time(worker.updated, "%Y-%m-%d %H:%M:%S")
        sgnl['elapsed'] = format_delta(worker.elapsed, self.config.get('TIME_FORMAT', "%H:%M:%S"))

        sgnl['is_mute'] = worker.is_mute
        sgnl['tracked'] = worker.tracked

        sgnl['text_attributes'] = worker.get_text_attributes()
        sgnl['signal_cache'] = [x.get() for x in self.scanner.signal_cache[worker.ident]]

    def config_worker(self, scanner):
        self.scanner = scanner
        self.config = scanner.config
        self.created = datetime.now()
        self.cache_max = max(int(scanner.config.get('SIGNAL_CACHE_LOG_MAX', -5)), -5)
        self.DEBUG = scanner.config['DEBUG']

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
            if k not in [self.scanner.SIGNAL_IDENT_FIELD, self.scanner.SIGNAL_STRENGTH_FIELD, 'text_attributes']:
                text_data.pop(k)
        [aggregate(k, str(v)) for k, v in text_data.copy().items()]

    def make_signalpoint(self, worker_id, ident, signal):

        # import the SignalPoint type
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

        SignalPointType = get_retriever(self.scanner.config['SIGNALPOINT_TYPE'])
        kwargs = {}
        sgnlPt = None
        # SignalPoint       (self, lon, lat, sgnl)
        # ARXSignalPoint    (self, worker_id, lon, lat, sgnl)

        # WifiSignalPoint   (self, worker_id, lon, lat, sgnl, bssid=None)
        if SignalPointType.__name__ == 'src.wifi.lib.WifiSignalPoint':
            kwargs["bssid"] =  self.get_text_attribute(self.scanner.SIGNAL_IDENT_FIELD),
            # create a item of the type
            sgnlPt = WifiSignalPoint(worker_id=ident, lon=self.scanner.lon, lat=self.scanner.lat, sgnl=signal, **kwargs)

        # SDRSignalPoint    (self, worker_id, lon, lat, sgnl, array_data=None, audio_data=None, sr=48000)
        if SignalPointType.__name__ == 'src.sdr.lib.SDRSignalPoint':
            kwargs["array_data"] =  self.get_text_attribute('array_data'),
            kwargs["audio_data"] =  self.get_text_attribute('audio_data'),
            kwargs["sr"] =  self.get_text_attribute('sr'),
            # create a item of the type
            sgnlPt = SDRSignalPoint(worker_id=ident, lon=self.scanner.lon, lat=self.scanner.lat, sgnl=signal, **kwargs)

        # TRXSignalPoint    (self, worker_id, lon, lat, sgnl, text_data={}, audio_data=None, signal_type="object", sr=48000)
        if SignalPointType.__name__ == 'src.trx.lib.SDRSignalPoint':
            kwargs["text_data"] =  self.get_text_attribute('text_data'),
            kwargs["signal_type"] =  self.get_text_attribute('signal_type'),

            # create a item of the type
            sgnlPt = TRXSignalPoint(worker_id=ident, lon=self.scanner.lon, lat=self.scanner.lat, sgnl=signal, **kwargs)

        self.scanner.signal_cache[ident].append(sgnlPt)

        while len(self.scanner.signal_cache[ident]) >= self.scanner.signal_cache_max:
            self.scanner.signal_cache[ident].pop(0)

    def process_cell(self, cell):
        """ update static fields, tests"""

        self.update(cell)

        def test(cell):
            # TODO: use this as an entrypoint to a discrete test in a test
            # framework that would return T or F.
            # need to identify the test...
            # provides [{testname: result}, {...}]
            try:
                tests = self.scanner.searchmap[self.ident]['tests']
                # return all results or only ones that passed?
                self.return_all = self.scanner.searchmap[self.ident]['return_all']

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
        self.tracked = self.ident in self.scanner.tracked_signals
        self.make_signalpoint(self.id, self.ident, int(sgnl.get(self.scanner.SIGNAL_STRENGTH_FIELD, -99)))
        # self._signal_cache_frequency_features = self.extract_signal_cache_features(
        #         [pt.getSgnl() for pt in self.scanner.signal_cache[self.id]]
        # )

    def get_signal_cache_frequency_features(self):
        return self._signal_cache_frequency_features

    def match(self, cell):
        """ match id, derive the 'id' and set mute status """
        if self.ident.upper() == cell[f'{self.scanner.SIGNAL_IDENT_FIELD}'].upper():

            if not self.id:
                self.id = str(cell[f'{self.scanner.SIGNAL_IDENT_FIELD}']).replace(':', '').lower()
            self.set_text_attributes(cell)
            self.process_cell(cell)
            self.auto_unmute()

    def mute(self):
        from src.lib.utils import mute
        return mute(self)

    def signal_vec(self):
        yield [pt.getSgnl() for pt in self.scanner.signal_cache[self.ident]][self.cache_max:]

    def auto_unmute(self):
        """ polled function to UNMUTE signals AUTOMATICALLY after the MUTE_TIME. """
        if self.config['MUTE_TIME'] > 0:
            if datetime.now() - self.updated > timedelta(seconds=self.config['MUTE_TIME']):
                self.is_mute = False

    def add(self, ident):

        try:
            worker = self.scanner.get_worker(ident)

            if worker:
                worker.tracked = True
                self.scanner.tracked_signals.append(ident)
                if worker not in self.scanner.workers:
                    self.scanner.workers.append(worker)
                return True

            return False
        except IndexError:
            return False

    def remove(self, ident):
        _copy = self.scanner.tracked_signals.copy()
        self.scanner.tracked_signals.clear()
        [self.add(remaining) for remaining in _copy if remaining != ident]
        return True

    def stop(self):
        if self.tracked:

            def append_to_outfile(cls, config, cell):  # use workers instead here.
                """Append found cells to a rolling JSON list"""
                from src.lib.utils import format_time, format_delta
                # unwrap the cell and format the dates, guids and whatnot.
                # {'EE:55:A8:24:B1:0A':
                #   {
                #   'id': 'ee55a824b10a',
                #   'name': 'Goodtimes Entertainment Inc.',
                #   'created': '2025-03-12 00:36:07',
                #   'updated': '2025-03-12 00:36:10',
                #   'elapsed': '00:00:03',
                #   'Vendor': 'UNKNOWN',
                #   'Channel': 11,
                #   'Frequency': 5169,
                #   'Signal': -89,
                #   'Quality': 11,
                #   'Encryption': True,
                #   'is_mute': False,
                #   'tracked': True,
                #   'signal_cache': [
                #       {
                #       'created': '2025-03-12 00:36:07.511398',
                #       'id': '6fb74555-e1f5-440a-9c42-f5649a536279',
                #       'worker_id': 'ee55a824b10a',
                #       'lon': -105.068195,
                #       'lat': 39.9168,
                #       'sgnl': -89
                #       },
                #       {'created': '2025-03-12 00:36:10.641924',
                #       'id': '18967444-39bf-4082-9aa4-d833fbb9ed28',
                #       'worker_id': 'ee55a824b10a',
                #       'lon': -105.068021,
                #       'lat': 39.916915,
                #       'sgnl': -89
                #       }
                #   ],
                #   'tests': []
                #   }
                # }
                #
                # config.get('CREATED_FORMATTER', '%Y-%m-%d %H:%M:%S')
                # config.get(UPDATED_FORMATTER', '%Y-%m-%d %H:%M:%S')
                # config.get(ELAPSED_FORMATTER', '%H:%M:%S')

                # format created timestamp in signals
                # SGNL_CREATED_FORMAT: "%Y-%m-%d %H:%M:%S.%f"
                formatted = {
                    f"{self.scanner.SIGNAL_IDENT_FIELD}"                : cell[f'{self.scanner.SIGNAL_IDENT_FIELD}'],

                    "created"                                           : cell['created'],
                    "updated"                                           : cell['updated'],
                    "elapsed"                                           : cell['elapsed'],

                    "is_mute"                                           : cell['is_mute'],
                    "tracked"                                           : cell['tracked'],
                }

                json_logger.info({cell['id']: formatted})

            append_to_outfile(self, self.config, self.get())

    def run(self):
        """ match an ID and populate data """
        [self.match(sgnl) for sgnl in self.scanner.parsed_signals]
