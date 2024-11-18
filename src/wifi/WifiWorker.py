from datetime import datetime, timedelta
import logging
from src.wifi.lib.wifi_utils import append_to_outfile

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')


class WifiWorker:
    """ WifiWorker: match a BSSID in the scanner; provide data back to the scanner. """

    def __init__(self, bssid):
        self.config = {}
        self.scanner = None

        self.bssid = bssid
        self.ssid = ''

        self.vendor = ''
        self.channel = ''
        self.frequency = ''
        self.quality = ''
        self.is_encrypted = ''

        self.created = datetime.now()   # when signal was found
        self.updated = datetime.now()   # when signal was last reported
        self.elapsed = timedelta()      # time signal has been tracked.

        self.is_mute = False            # is BSSID muted
        self.tracked = False            # is BSSID in scanner.tracked_signals

        self.results = []               # a list of test results (this should be local to method)
        self.return_all = False         # return all/any
        self.test_results = {}          # mapping of results

        self.DEBUG = False

    def __str__(self):
        cache_max = max(int(self.config.get('SIGNAL_CACHE_LOG_MAX', -5)), -(self.config.get('SIGNAL_CACHE_MAX')))
        return {"SSID"          : self.ssid,
                "BSSID"         : self.bssid,
                "created"       : str(self.created),
                "updated"       : str(self.updated),
                "elapsed"       : str(self.elapsed),
                "vendor"        : self.vendor,
                "channel"       : self.channel,
                "frequency"     : self.frequency,
                "quality"       : self.quality,
                "encryption"    : self.is_encrypted,
                "is_mute"       : self.is_mute,
                "tracked"       : self.tracked,
                "signal_cache"  : [pt for pt in self.scanner.signal_cache[self.bssid]][cache_max:],
                "tests"         : [x for x in self.test_results]
        }

    def get_MFCC(self):
        # TODO
        pass

    def process_cell(self, cell):
        """ update static fields, tests"""

        if cell['SSID'] == '' or None:
            cell['SSID'] = "*HIDDEN SSID*"

        self.vendor = cell['Vendor']
        self.channel = cell['Channel']
        self.frequency = cell['Frequency']
        self.quality = cell['Quality']
        self.is_encrypted = cell['Encryption']
        self.update(cell)

        def test(cell):
            # TODO: use this as an entrypoint to a discrete test in a test
            # framework that would return T or F.
            # need to identify the test...
            # provides [{testname: result}, {...}]
            try:
                tests = self.scanner.searchmap[self.bssid]['tests']
                # return all results or only ones that passed?
                self.return_all = self.scanner.searchmap[self.bssid]['return_all']

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
        self.elapsed = datetime.now() - self.created
        self.tracked = self.bssid in self.scanner.tracked_signals.keys()
        self.scanner.makeSignalPoint(self.bssid, int(sgnl.get('Signal', -99)))

    def match(self, cell):
        """ process the matching BSSID and return data in it as a 'cell' """
        if self.bssid.upper() == cell['BSSID'].upper():
            self.process_cell(cell)
            self.auto_unmute()

    def mute(self):
        from src.lib.utils import mute
        # SIGNAL: MUTE/UNMUTE
        return mute(self)

    def auto_unmute(self):
        ''' this is the polled function to UNMUTE signals AUTOMATICALLY after the MUTE_TIME. '''
        if self.config['MUTE_TIME'] > 0:
            if datetime.now() - self.updated > timedelta(seconds=self.config['MUTE_TIME']):
                self.is_mute = False
                # SIGNAL: AUTO UNMUTE

    def add(self, bssid):

        worker = self.scanner.get_worker(bssid)

        try:
            cell = [cell for cell in self.scanner.parsed_signals if cell['BSSID'] == bssid][0]
            if cell:
                worker.ssid = cell['SSID']
                self.scanner.tracked_signals.update(
                    {
                        worker.bssid: {
                            "ssid"      : worker.ssid,
                            "tests"     : {},
                            "return_all": True
                        }
                    }
                )

                if worker not in self.scanner.workers:
                    self.scanner.workers.append(worker)

                # SIGNAL: ADDED ITEM
                return True
            return False  # no cell
        except IndexError:
            return False  # not in parsed_signals

    def remove(self, bssid):
        _copy = self.scanner.tracked_signals.copy()
        self.scanner.tracked_signals.clear()
        [self.add(remaining) for remaining in _copy if remaining != bssid]
        # SIGNAL: REMOVED ITEM
        return True

    def stop(self):
        if self.tracked:
            append_to_outfile(self.config, self.__str__())

    def run(self):
        ''' match a BSSID and populate data '''
        [self.match(sgnl) for sgnl in self.scanner.parsed_signals]

