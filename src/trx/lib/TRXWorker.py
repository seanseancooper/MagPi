from collections import defaultdict
from datetime import datetime, timedelta
import logging

from src.lib.utils import format_time, format_delta
from src.wifi.lib.wifi_utils import append_to_outfile

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')


class TRXWorker:
    """
    TRXWorker: match a radio frequency from the TRX-1 when it receives.
    These are 'intermittent' signals, not continuous ones.
    """
    # idea: FEED SIGNALPOINT TEXT DATA INTO A LLM

    #     CAN I Spectral Analysis Features to Extract for Each Signal [scipy.signal, numpy.fft]:
    #     Feature                         : Description
    #
    #     Mean signal power               : Average strength
    #     Variance                        : Signal stability
    #     FFT Peak/Dominant Frequency     : Periodic behavior
    #     Auto-correlation lag            : Repetitions
    #     Coherence with other signals    : Time-dependent similarity
    #     Rolling correlation window      : Pairwise time-varying relationships [pandas.rolling().corr()]
    #     Mean signal power               : Average strength
    #
    #     PCA / UMAP | sklearn, umap-learn
    #     Clustering | sklearn.cluster
    #     Mutual Information | sklearn.metrics.mutual_info_score


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
        return {
            "ALPHATAG"      : self.ALPHATAG,
            "freq"          : self.freq,

            "created"       : format_time(self.created, self.config.get('TIME_FORMAT', "%H:%M:%S")),
            "updated"       : format_time(self.updated, self.config.get('TIME_FORMAT', "%H:%M:%S")),
            "elapsed"       : format_delta(self.elapsed, self.config.get('TIME_FORMAT', "%H:%M:%S")),

            "is_mute"       : str(self.is_mute),
            "tracked"       : str(self.tracked),
            # "signal_cache"  : [pt for pt in self.retriever.signal_cache[self.freq]][self.cache_max:],
            # "tests"         : [x for x in self.test_results]
        }

    def config_worker(self, scanner):
        self.retriever = scanner
        self.config = scanner.config
        self.created = datetime.now()
        self.DEBUG = scanner.config.get('DEBUG', False)
        self.cache_max = max(
            int(scanner.config.get('SIGNAL_CACHE_LOG_MAX', -5)),
            -scanner.config.get('SIGNAL_CACHE_MAX', 150)
        )

    def process_cell(self, sgnl):
        """ update static fields, tests"""

        if sgnl._text_attributes['ALPHATAG'] == '' or None:
            sgnl._text_attributes['ALPHATAG'] = "*MISSING ALPHATAG*"

        self.attributes = sgnl._text_attributes.copy()
        self.ALPHATAG = self.attributes['ALPHATAG']

        return sgnl

    def update(self):
        """ updates *dynamic* fields"""
        self.updated = datetime.now()
        self.elapsed = self.updated - self.created
        self.tracked = self.freq in self.retriever.tracked_signals.keys()

    def match(self, sgnl):
        """ process the matching freq and return data in it as a 'cell' """
        if self.freq == float(sgnl._text_attributes['FREQ1']):
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
                            "RETURN_ALL": True
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

