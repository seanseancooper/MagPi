from datetime import datetime, timedelta
import logging
from src.lib.utils import format_time, format_delta
from src.wifi.lib.wifi_utils import append_to_outfile

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')


class WifiWorker:
    """ WifiWorker: match a BSSID in the scanner; provide data back to the scanner. """

    def __init__(self, bssid):
        self.config = {}
        self.scanner = None
        self.id = ''                    # filled if match(), based on BSSID; marks 'SignalPoint'.
        self.bssid = bssid              # MAC ADDRESS. used in object lookups and coloring UI
        self.ssid = ''                  # Human readable name of Wifi access point.

        self.vendor = ''
        self.channel = ''
        self.frequency = ''
        self.quality = ''
        self.signal = ''
        self.is_encrypted = False

        self.created = datetime.now()   # when signal was found
        self.updated = datetime.now()   # when signal was last reported
        self.elapsed = timedelta()      # time signal has been tracked.

        self.is_mute = False            # is BSSID muted
        self.tracked = False            # is BSSID in scanner.tracked_signals

        self.results = []               # a list of test results (this should be local to method)
        self.return_all = False         # return all/any
        self.test_results = {}          # mapping of results
        self.cache_max = 0              # maximum number of SignalPoints displayed in logs
        self._frequency_features = None

        self.DEBUG = False

    def get(self):
        return {"id"            : self.id,
                "SSID"          : self.ssid,
                "BSSID"         : self.bssid,
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
                "signal_cache"  : [pt.get() for pt in self.scanner.signal_cache[self.bssid]][self.cache_max:],
                "frequency_features"  : self._frequency_features,
                "tests"         : [x for x in self.test_results]
        }

    # IDEA: probability that signal is mobile as
    #  opposed to stationary; features may be
    #  location, signal_cache, Vendor, Quality?

    @staticmethod
    def extract_signal_strength_features(past_signals, sampling_rate=1):

        import numpy as np
        from scipy.fftpack import fft
        from python_speech_features import mfcc

        MIN_LEN = 50

        if len(past_signals) < 2:
            return {
                "dominant_freq": None,
                "spectral_entropy": None,
                "fft_magnitude": [0.0] * MIN_LEN,
                "mfcc"         : [0.0] * 13
            }

        signal_values = np.array(past_signals)
        N = len(signal_values)

        if N < MIN_LEN:
            signal_values = np.pad(signal_values, (0, MIN_LEN - N), 'constant')
            N = MIN_LEN

        fft_vals_full = np.abs(fft(signal_values))
        fft_vals = fft_vals_full[:N // 2]

        fft_vals_50 = np.zeros(MIN_LEN)
        fft_clip = fft_vals[:MIN_LEN] if len(fft_vals) >= MIN_LEN else fft_vals
        fft_vals_50[:len(fft_clip)] = fft_clip

        freqs = np.fft.fftfreq(N, d=1 / sampling_rate)[:N // 2]
        dominant_freq = freqs[np.argmax(fft_vals)]
        normalized_fft = fft_vals / np.sum(fft_vals) if np.sum(fft_vals) > 0 else np.ones_like(fft_vals) / len(fft_vals)
        spectral_entropy = -np.sum(normalized_fft * np.log2(normalized_fft + 1e-12))

        try:
            mfcc_features = mfcc(signal_values.reshape(-1, 1), samplerate=sampling_rate, numcep=13)
            mfcc_mean = mfcc_features.mean(axis=0).tolist()
        except Exception:
            mfcc_mean = [0.0] * 13

        # AUDIO FREQUENCY FEATURES:
        # // ENOB: Effective number of bits

        # DB (_sgnl): decibels
        # SNR: Signal-to-noise ratio
        # THD: Total harmonic distortion
        # THD + N: Total harmonic distortion plus noise

        # SFDR: Spurious free dynamic range
        # SINAD: Signal-to-noise-and-distortion ratio

        return {
            "dominant_freq"   : float(dominant_freq),
            "spectral_entropy": float(spectral_entropy),
            "fft_magnitude"   : fft_vals_50.tolist(),
            "mfcc"            : mfcc_mean
        }

    def process_cell(self, cell):
        """ update static fields, tests"""

        if cell['SSID'] == '' or None:
            cell['SSID'] = "*HIDDEN SSID*"

        self.ssid = cell['SSID']
        self.vendor = cell['Vendor']
        self.channel = cell['Channel']
        self.frequency = cell['Frequency']
        self.quality = cell['Quality']
        self.is_encrypted = cell['Encryption']
        self.signal = cell['Signal']
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
        self.elapsed = self.updated - self.created
        self.tracked = self.bssid in self.scanner.tracked_signals
        self.scanner.make_signalpoint(self.id, self.bssid, int(sgnl.get('Signal', -99)))
        self._frequency_features = self.extract_signal_strength_features(
                [pt.getSgnl() for pt in self.scanner.signal_cache[self.bssid]]
        )

    def match(self, cell):
        """ match BSSID, derive the 'id' and set mute status """
        if self.bssid.upper() == cell['BSSID'].upper():
            self.id = str(self.bssid).replace(':', '').lower()
            self.process_cell(cell)
            self.auto_unmute()

    def mute(self):
        from src.lib.utils import mute
        # SIGNAL: MUTE/UNMUTE
        return mute(self)

    def signal_vec(self):
        yield [pt.getSgnl() for pt in self.scanner.signal_cache[self.bssid]][self.cache_max:]

    def auto_unmute(self):
        """ polled function to UNMUTE signals AUTOMATICALLY after the MUTE_TIME. """
        if self.config['MUTE_TIME'] > 0:
            if datetime.now() - self.updated > timedelta(seconds=self.config['MUTE_TIME']):
                self.is_mute = False
                # SIGNAL: AUTO UNMUTE

    def add(self, bssid):

        try:
            worker = self.scanner.get_worker(bssid)

            if worker:
                worker.tracked = True
                self.scanner.tracked_signals.append(bssid)
                if worker not in self.scanner.workers:
                    self.scanner.workers.append(worker)
                # SIGNAL: ADDED ITEM
                return True

            return False
        except IndexError:
            return False

    def remove(self, bssid):
        _copy = self.scanner.tracked_signals.copy()
        self.scanner.tracked_signals.clear()
        [self.add(remaining) for remaining in _copy if remaining != bssid]
        # SIGNAL: REMOVED ITEM
        return True

    def stop(self):
        if self.tracked:
            append_to_outfile(self, self.config, self.get())

    def run(self):
        """ match a BSSID and populate data """
        [self.match(sgnl) for sgnl in self.scanner.parsed_signals]

