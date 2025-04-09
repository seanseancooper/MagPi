from collections import defaultdict
from datetime import datetime, timedelta
import logging

from src.lib.utils import format_time, format_delta
from src.wifi.lib.wifi_utils import append_to_outfile

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')


class TRXWorker:
    """
    TRXWorker: match a radio frequency from the TRX-1 when it
    broadcasts. This is different than wifi, because it
    is an 'intermittant' signal, not continous.
    """

    def __init__(self, freq):
        self.config = {}
        self.retriever = None

        self.freq = freq
        self.ALPHATAG = None

        self.attributes = defaultdict(dict)


        self.created = datetime.now()   # when signal was found
        self.updated = datetime.now()   # when signal was last reported
        self.elapsed = timedelta()      # time signal has been tracked.

        self.is_mute = False            # is freq muted
        self.tracked = False            # is freq in retriever.tracked_signals

        self.results = []               # a list of test results (this should be local to method)
        self.return_all = False         # return all/any
        self.test_results = {}          # mapping of results
        self.cache_max = 0              # used in worker model

        self.DEBUG = False

    def get(self):
        return {"ALPHATAG"      : self.ALPHATAG,
                "freq"          : self.freq,

                "created"       : format_time(self.created, self.config.get('TIMER_FORMAT', "%H:%M:%S")),
                "updated"       : format_time(self.updated, self.config.get('TIMER_FORMAT', "%H:%M:%S")),
                "elapsed"       : format_delta(self.elapsed, self.config.get('TIMER_FORMAT', "%H:%M:%S")),

                "is_mute"       : str(self.is_mute),
                "tracked"       : str(self.tracked),
                "signal_cache"  : [pt for pt in self.retriever.signal_cache[self.freq]][self.cache_max:],
                "tests"         : [x for x in self.test_results]
        }

    def process_cell(self, sgnl):
        """ update static fields, tests"""

        if sgnl.text_attributes['ALPHATAG'] == '' or None:
            sgnl.text_attributes['ALPHATAG'] = "*MISSING ALPHATAG*"

        self.attributes = sgnl.text_attributes.copy()
        self.ALPHATAG = self.attributes['ALPHATAG']

        def test(cell):
            # IDEA: use this as an entrypoint to a discrete test in a test
            # framework that would return T or F.
            # worker emits [test] & [result] separately, these should be together [{test:result}].
            try:
                tests = self.retriever.tracked_signals[self.freq]['tests']
                # return all results or only ones that passed?
                self.return_all = self.retriever.tracked_signals[self.freq]['return_all']

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

        return sgnl if test(sgnl) else None

    def update(self):
        """ updates *dynamic* fields"""
        self.updated = datetime.now()
        self.elapsed = self.updated - self.created
        self.tracked = self.freq in self.retriever.tracked_signals.keys()

    def match(self, sgnl):
        """ process the matching freq and return data in it as a 'cell' """
        if self.freq == float(sgnl.text_attributes['FREQ1']):
            self.process_cell(sgnl)
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

    def add(self, freq):

        worker = self.retriever.get_worker(freq)

        try:
            cell = [cell for cell in self.retriever.tracked_signals if cell['freq'] == freq][0]
            if cell:
                worker.ALPHATAG = cell['ALPHATAG']
                self.retriever.tracked_signals.update(
                    {
                        worker.freq: {
                            "ALPHATAG"      : worker.ALPHATAG,
                            "tests"     : {},
                            "return_all": True
                        }
                    }
                )

                if worker not in self.retriever.workers:
                    self.retriever.workers.append(worker)

                # SIGNAL: ADDED ITEM
                return True
            return False  # no cell
        except IndexError:
            return False  # not in tracked_signals

    def remove(self, freq):
        _copy = self.retriever.tracked_signals.copy()
        self.retriever.tracked_signals.clear()
        [self.add(remaining) for remaining in _copy if remaining != freq]
        # SIGNAL: REMOVED ITEM
        return True

    def stop(self):
        if self.tracked:
            append_to_outfile(self.config, self.get())

    def run(self):
        ''' match a freq and populate data '''
        [self.match(sgnl) for sgnl in self.retriever.signal_cache]

