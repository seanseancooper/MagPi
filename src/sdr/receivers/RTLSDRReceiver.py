from __future__ import division

import queue
import threading
from datetime import datetime

from rtlsdr import RtlSdr
from scipy.signal import find_peaks, welch
from matplotlib.mlab import psd
import numpy as np


from src.config import readConfig
from src.lib.utils import format_time, generate_uuid


def file_writing_thread(*, q, **blockfile_args):
    """
    Thread function to continuously write audio data from queue to a file.
    Stops when it gets a `None` item.
    """
    with open(**blockfile_args) as f:
        while True:
            data = q.get()
            if data is None:
                break
            data = data.astype(np.complex64)
            data.tofile(f)


class RTLSDRReceiver(threading.Thread):

    def __init__(self):
        """Initialize the SDR hardware with provided parameters.
        Received energy on a particular frequency may start a recorder, and alert a human
        to listen to the signals if they are intelligible (i.e., COMINT). If the frequency
        is not known, the operators may look for power on primary or sideband frequencies
        using a spectrum analyzer. Information from the spectrum analyzer is then used to
        tune receivers to signals of interest.
        """
        super().__init__()
        self.sdr = None
        self.thread = None
        self.config = {}

        self.fft_size = 4096                # a default
        self.block = None                   # data read from hardware and analyzed.
        self.iq_queue = queue.Queue()       # Unbounded queue for I/Q data
        self.iq_outfile = None              # a file for IQFileReader

        self.seen_frequencies = set()
        self.freq_match_tolerance = 2000  # 2 kHz
        self.filter_peaks = False

        self.filter_peaks = False           # 'Scanner' peaks are filtered
        self.parsed_cells = None            # what 'Scanner' needs for tracking


    def configure(self, config_file):

        readConfig(config_file, self.config)

        self.sdr = RtlSdr()
        self.sdr.sample_rate = self.config['DEFAULT_SAMPLE_RATE']
        self.sdr.center_freq = self.config['DEFAULT_CENTER_FREQ']
        self.sdr.freq_correction = self.config['DEFAULT_FREQ_CORRECTION']
        self.sdr.gain = self.config['DEFAULT_GAIN']

        self.fft_size = self.config['FFT_SIZE']

    def get_sample_rate(self):
        return self.sdr.sample_rate

    def get_center_freq(self):
        return self.sdr.center_freq

    def set_center_freq(self, freq):
        self.sdr.center_freq  = freq

    def get_freq_correction(self):
        return self.sdr.freq_correction

    def get_gain(self):
        return self.sdr.gain

    def set_gain(self, gain_value):
        self.sdr.gain = gain_value

    def set_block(self, scanned):
        if type(scanned) is list:
            self.block = scanned[0]
        if type(scanned) is np.array:
            self.block = scanned

        self.iq_queue.put(self.block.copy())

    def get_block(self, scanned):
        self.set_block(scanned)
        return self.block # yield?

    def get_psd_for_block(self):

        from matplotlib.mlab import psd
        psd, frequencies = psd(self.block, NFFT=self.fft_size)

        # from scipy.signal import welch
        # frequencies, psd = welch(self.block, fs=self.sdr.sample_rate, nperseg=self.fft_size)

        return psd, frequencies

    def get_peaks(self):
        psd_scan, f = self.get_psd_for_block()

        mean = np.mean(psd_scan)
        std = np.std(psd_scan)

        # | Feature              | Indicator of Signal | Indicator of Noise          |
        # | -------------------- | ------------------- | --------------------------- |
        # | Height               | High above mean     | Barely above noise floor    |
        # | Prominence           | High                | Low / embedded in clutter   |
        # | Width                | Moderate            | Too narrow or too wide      |
        # | Shape                | Smooth/consistent   | Jagged or asymmetrical      |
        # | Temporal Consistency | Stable over time    | Appears/disappears randomly |

        peak_options = {
            'height'    : mean + 2 * std,           # Filters out background noise and low-level fluctuations.
            'prominence': 0.1 * np.max(psd_scan),   # Rejects peaks that don't stand out from surrounding spectrum.
            'width'     : (3, 30),                  # Rejects sharp spikes (impulsive noise) and overly broad hills (clutter or poor resolution). Bin range; depends on your resolution
            'rel_height': 0.5                       # Ensures peak width is measured at a consistent threshold (half-max)
        }

        peaks, properties = find_peaks(psd_scan, **peak_options)

        if self.filter_peaks: # filter by further criteria post-hoc
            filtered_peaks = []
            for i, peak in enumerate(peaks):
                w = properties['widths'][i] if 'widths' in properties else None
                p = properties['prominences'][i] if 'prominences' in properties else None
                if w and p and w > 5 and p > 0.1:
                    filtered_peaks.append(peak)
            return np.array(filtered_peaks), properties

        return peaks, properties

    def get_peak_freq(self, peak):
        psd_scan, f = self.get_psd_for_block()
        return f[peak]  + self.config['DEFAULT_CENTER_FREQ']

    def get_peak_db(self, peak):
        psd_scan, _ = self.get_psd_for_block()

        power = psd_scan[peak]
        if power <= 0:
            return -np.inf
        return 10 * np.log10(power)

    def get_parsed_cells(self, scanned):

        if not scanned:
            return []

        self.get_block(scanned)

        peaks, peak_properties = self.get_peaks()
        # print(peaks)

        self.parsed_cells = []
        for peak in peaks:

            text_attributes = {
                # 'sample_rate' : self.sdr.sample_rate,
                # 'center_freq' : self.sdr.center_freq,            # CELL_NAME_FIELD
                # 'freq_corr'   : self.sdr.freq_correction,
                # 'gain'        : self.sdr.gain,
            }

            peak_freq = self.get_peak_freq(peak)

            worker_id = ''

            cell = {
                'peak_freq'      : peak_freq,                                           # CELL_IDENT_FIELD
                "created"        : format_time(datetime.now(), "%Y-%m-%d %H:%M:%S.%f"),
                "id"             : str(generate_uuid()),
                "worker_id"      : worker_id,
                "lon"            : 0.0,
                "lat"            : 0.0,
                "sgnl"           : self.get_peak_db(peak),                              # CELL_STRENGTH_FIELD

                # "text_attributes": text_attributes, # this is being done 2x?
                'sample_rate'   : self.sdr.sample_rate,
                'center_freq'   : self.sdr.center_freq,                                    # CELL_NAME_FIELD
                'freq_corr'     : self.sdr.freq_correction,
                'gain'          : self.sdr.gain,

                "audio_data"     : None,
                'cell_type'      : 'sdr',
                'is_mute'        : False,
                'tracked'        : False,
            }

            # Skip if frequency is already tracked (within tolerance)
            # if any(abs(peak_freq - f) < self.freq_match_tolerance for f in self.seen_frequencies):
            #     continue
            #
            # self.seen_frequencies.add(peak_freq)

            self.parsed_cells.append(cell)

        [print(cell) for cell in self.parsed_cells]

        return self.parsed_cells

    def run(self):

        name = (self.config['OUT_FILE'] +
                format_time(datetime.now(), "%Y%m%d_%H%M%S") + '_' +
                str(self.sdr.center_freq) + '_' +
                str(int(self.sdr.sample_rate)) +
                self.config['OUT_FILE_EXT']
                )

        self.outfile = self.config['OUTFILE_PATH'] + '/' + name

        self.thread = threading.Thread(
                target=file_writing_thread,
                kwargs=dict(
                        file=self.outfile,
                        mode='w',
                        q=self.iqq,
                ),
                daemon=True,
        )

        self.thread.start()

    def scan(self):

        def get_data(nfft_size):
            if not self.sdr.device_opened:
                self.sdr.open()

            if not self.thread:
                self.run()

            s = self.read_samples(nfft_size)    # get rid of initial empty samples
            if s.any():
                return s                        # no contract
            return None

        scanned = get_data(self.nfft_size)

        return [scanned]  # contract is list of T

    def read_samples(self, num_samples=4096):
        """Read samples from the SDR."""
        return self.sdr.read_samples(num_samples)

    def print_device_info(self):
        """Print the length of samples and valid gains for the SDR."""
        print(len(self.read_samples(num_samples=self.nfft_size)))
        print(self.sdr.valid_gains_db)

if __name__ == '__main__':
    sdr = RTLSDRReceiver()

    sdr.configure('sdr.json')
    sdr.set_gain(49.6)

    fft_size=512
    num_rows=500

    data = sdr.scan()


