from datetime import datetime, timedelta
import json
from src.lib.utils import format_time, format_delta


class Worker:

    def __init__(self, id):
        self.config = {}
        self.scanner = None
        self.id = ''                    # filled if match(), marks 'SignalPoint'.
        self.name = ''                  # Human readable name of Wifi access point.

        self.vendor = ''
        self.channel = ''
        self.frequency = ''
        self.quality = ''
        self.signal = ''
        self.is_encrypted = False

        self.created = datetime.now()   # when signal was found
        self.updated = datetime.now()   # when signal was last reported
        self.elapsed = timedelta()      # time signal has been tracked.

        self.is_mute = False            # is muted
        self.tracked = False            # is in scanner.tracked_signals

        self.results = []               # a list of test results (this should be local to method)
        self.return_all = False         # return all/any
        self.test_results = {}          # mapping of results
        self.cache_max = 0              # maximum number of SignalPoints displayed in logs
        self._signal_cache_frequency_features = None

        self.DEBUG = False

    def get(self):
        return {"id"            : self.id,
                "SSID"          : self.name,
                "created"       : format_time(self.created, "%Y-%m-%d %H:%M:%S"),
                "updated"       : format_time(self.updated, "%Y-%m-%d %H:%M:%S"),
                "elapsed"       : format_delta(self.elapsed, "%H:%M:%S"),
                "Vendor"        : self.vendor,
                "Channel"       : self.channel,
                "Frequency"     : self.frequency,
                "Signal"        : self.signal,
                "Quality"       : self.quality,
                "Encryption"    : self.is_encrypted,
                "is_mute"       : self.is_mute,
                "tracked"       : self.tracked,
                "signal_cache"  : [pt.get() for pt in self.scanner.signal_cache[self.id]][self.cache_max:],
                "frequency_features"  : self._signal_cache_frequency_features,
                "tests"         : [x for x in self.test_results]
        }

    def config_worker(self, scanner):
        self.scanner = scanner
        self.config = scanner.config
        self.created = datetime.now()
        self.cache_max = max(int(scanner.config.get('SIGNAL_CACHE_LOG_MAX', -5)), -(scanner.config.get('SIGNAL_CACHE_MAX')))
        self.DEBUG = scanner.config['DEBUG']

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
