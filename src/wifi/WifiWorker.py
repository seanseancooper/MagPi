from datetime import datetime, timedelta
import logging
from src.wifi.lib.wifi_utils import write_foundLIST

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
        self.elapsed = datetime.now()   # time signal has been tracked.

        self.is_mute = False            # is BSSID muted
        self.tracked = False            # is BSSID in scanner.tracked_signals

        self.stats = {}                 # statisics on this signal

        self.results = []               # a list of test results (this should be local to method)
        self.return_all = False         # return all/any
        self.test_results = {}          # mapping of results

        self.DEBUG = False

    def __str__(self):
        return {"SSID"          : self.ssid,
                "BSSID"         : self.bssid,

                "vendor"        : self.vendor,
                "channel"       : self.channel,
                "frequency"     : self.frequency,
                "quality"       : self.quality,
                "encryption"    : self.is_encrypted,

                "created"       : str(self.created),
                "updated"       : str(self.updated),
                "elapsed"       : str(self.elapsed),
                "is_mute"       : str(self.is_mute),

                "tracked"       : str(self.tracked),
                "signal_cache"  : self.stats['signal_cache'],
                "test_results"  : [item for item in self.test_results],
                }

    def populate_stats(self):

        self.stats['created'] = self.created
        self.stats['updated'] = self.updated = datetime.now()
        self.stats['elapsed'] = self.elapsed = datetime.now() - self.created
        self.stats['is_mute'] = self.is_mute

        self.stats['tracked'] = self.tracked = self.bssid in self.scanner.tracked_signals.keys()
        self.stats['signal_cache'] = [pt.get() for pt in self.scanner.signal_cache[self.bssid]]
        self.stats['results'] = self.test_results

    def get_MFCC(self):
        # TODO
        pass

    def process_cell(self, cell):

        if cell['SSID'] == '' or None:
            cell['SSID'] = "*HIDDEN SSID*"

        self.vendor = cell['Vendor']
        self.channel = cell['Channel']
        self.frequency = cell['Frequency']
        self.quality = cell['Quality']
        self.is_encrypted = cell['Encryption']

        self.scanner.makeSignalPoint(self.bssid, int(cell.get('Signal', -99)))  # fails on missing signals

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

    def match_sgnl(self, cell):
        """ process the matching BSSID and return data in it as a 'cell' """
        if self.bssid.upper() == cell['BSSID'].upper():
            self.process_cell(cell)
            self.auto_unmute()
            self.populate_stats()

    def mute(self):
        from src.lib.utils import mute
        # SIGNAL: MUTE/UNMUTE
        return mute(self)

    def auto_unmute(self):
        ''' this is the polled function to UNMUTE signals AUTOMATICALLY after the MUTE_TIME. '''
        if self.config['MUTE_TIME'] > 0:
            elapsed = datetime.now() - self.updated
            if elapsed > timedelta(seconds=self.config['MUTE_TIME']):
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

    def run(self):
        ''' match a BSSID and populate data '''

        [self.match_sgnl(sgnl) for sgnl in self.scanner.parsed_signals]
        [self.match_sgnl(sgnl) for sgnl in self.scanner.get_missing_signals()]

        if self.tracked:
            write_foundLIST(self.config, self.__str__(), self.stats)

