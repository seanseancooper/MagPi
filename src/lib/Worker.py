from datetime import datetime, timedelta
import json

from src.lib.SignalPoint import SignalPoint
from src.lib.utils import format_time, format_delta
from src.wifi.lib.wifi_utils import append_to_outfile, json_logger


class Worker:
    # 🧩 Modeling Components

    # 1. Signal Sources as Agents
    # Each emitter can be modeled as an agent with:
    #

    #     Repetition, pattern, schedule: Worker() could support 'period' data via EAV tables of events; need event 'types'? & tests
    #     Signal fingerprint (modulation, bandwidth, power, etc.)

    def __init__(self, id):
        self.config = {}
        self.scanner = None
        self.id = ''                    # filled if match(), marks 'SignalPoint' type.
        self.name = ''                  # Human readable name of asset.

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

    def worker_to_sgnl(self, sgnl, worker):
        """ update sgnl data map with current info from worker """
        sgnl['id'] = worker.id
        sgnl['Signal'] = worker.signal

        # this is formatting for luxon.js, but is not clean.
        sgnl['created'] = format_time(worker.created, "%Y-%m-%d %H:%M:%S")
        sgnl['updated'] = format_time(worker.updated, "%Y-%m-%d %H:%M:%S")
        sgnl['elapsed'] = format_delta(worker.elapsed, self.config.get('TIME_FORMAT', "%H:%M:%S"))

        sgnl['is_mute'] = worker.is_mute
        sgnl['tracked'] = worker.tracked
        sgnl['signal_cache'] = [sgnl.get() for sgnl in self.scanner.signal_cache[worker.id]]
        sgnl['results'] = [json.dumps(result) for result in worker.test_results]

    @staticmethod
    def worker_to_dict(worker):
        """ calculates on arxs """
        return  {
            "id"                        : worker.id,
            "name"                      : worker.name,
            "created"                   : format_time(worker.created, "%Y-%m-%d %H:%M:%S"),
            "updated"                   : format_time(worker.updated, "%Y-%m-%d %H:%M:%S"),
            "elapsed"                   : format_delta(worker.elapsed, "%H:%M:%S"),

            "is_mute"                   : worker.is_mute,
            "tracked"                   : worker.tracked,
            "text_attributes"           : worker.get_text_attributes(),
        }

    def get(self):
        return {
            "id"                    : self.id,
            "name"                  : self.name,
            "created"               : format_time(self.created, "%Y-%m-%d %H:%M:%S"),
            "updated"               : format_time(self.updated, "%Y-%m-%d %H:%M:%S"),
            "elapsed"               : format_delta(self.elapsed, "%H:%M:%S"),

            "is_mute"               : self.is_mute,
            "tracked"               : self.tracked,

            "text_attributes"       : self.get_text_attributes(),
        }

    def config_worker(self, scanner):
        self.scanner = scanner
        self.config = scanner.config
        self.created = datetime.now()
        self.cache_max = max(int(scanner.config.get('SIGNAL_CACHE_LOG_MAX', -5)), -5)
        self.DEBUG = scanner.config['DEBUG']

    def get_text_attributes(self):
        return self._text_attributes

    def get_text_attribute(self, a):
        return self._text_attributes[a]

    def set_text_attribute(self, a, v):
        self._text_attributes[a] = v

    def set_text_attributes(self, text_data):
        def aggregate(k, v):
            self._text_attributes[k] = v
        [aggregate(k, str(v)) for k, v in text_data.items()]

    def make_signalpoint(self, worker_id, id, signal):
        sgnlPt = SignalPoint(self.scanner.lon, self.scanner.lat, signal)
        self.scanner.signal_cache[id].append(sgnlPt)

        while len(self.scanner.signal_cache[id]) >= self.scanner.signal_cache_max:
            self.scanner.signal_cache[id].pop(0)

    def process_cell(self, cell):
        """ update static fields, tests"""
        self.set_text_attributes(cell)
        self.update(cell)

        def test(cell):
            # TODO: use this as an entrypoint to a discrete test in a test
            # framework that would return T or F.
            # need to identify the test...
            # provides [{testname: result}, {...}]
            try:
                tests = self.scanner.searchmap[self.id]['tests']
                # return all results or only ones that passed?
                self.return_all = self.scanner.searchmap[self.id]['return_all']

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
        self.tracked = self.id in self.scanner.tracked_signals
        self.scanner.make_signalpoint(self.id, self.id, int(sgnl.get('Signal', -99)))
        # self._signal_cache_frequency_features = self.extract_signal_cache_features(
        #         [pt.getSgnl() for pt in self.scanner.signal_cache[self.id]]
        # )

    def get_signal_cache_frequency_features(self):
        return self._signal_cache_frequency_features

    def match(self, cell):
        """ match id, derive the 'id' and set mute status """
        if self.id.upper() == cell['id'].upper():
            self.id = str(self.id).replace(':', '').lower()
            self.process_cell(cell)
            self.auto_unmute()

    def mute(self):
        from src.lib.utils import mute
        return mute(self)

    def signal_vec(self):
        yield [pt.getSgnl() for pt in self.scanner.signal_cache[self.id]][self.cache_max:]

    def auto_unmute(self):
        """ polled function to UNMUTE signals AUTOMATICALLY after the MUTE_TIME. """
        if self.config['MUTE_TIME'] > 0:
            if datetime.now() - self.updated > timedelta(seconds=self.config['MUTE_TIME']):
                self.is_mute = False

    def add(self, id):

        try:
            worker = self.scanner.get_worker(id)

            if worker:
                worker.tracked = True
                self.scanner.tracked_signals.append(id)
                if worker not in self.scanner.workers:
                    self.scanner.workers.append(worker)
                return True

            return False
        except IndexError:
            return False

    def remove(self, id):
        _copy = self.scanner.tracked_signals.copy()
        self.scanner.tracked_signals.clear()
        [self.add(remaining) for remaining in _copy if remaining != id]
        return True

    def stop(self):
        if self.tracked:

            def append_to_outfile(cls, config, cell):
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
                    "id"          : cell['id'],
                    "SSID"        : cell['SSID'],
                    "BSSID"       : cell['BSSID'],
                    "created"     : cell['created'],
                    "updated"     : cell['updated'],
                    "elapsed"     : cell['elapsed'],
                    # "text_attributes":
                    "is_mute"     : cell['is_mute'],
                    "tracked"     : cell['tracked'],
                    "signal_cache": [pt.get() for pt in cls.producer.signal_cache[cell['id']]][cls.cache_max:],
                    "tests"       : [x for x in cell['tests']]
                }

                json_logger.info({cell['id']: formatted})

            append_to_outfile(self, self.config, self.get())

    def run(self):
        """ match an ID and populate data """
        [self.match(sgnl) for sgnl in self.scanner.parsed_signals]
