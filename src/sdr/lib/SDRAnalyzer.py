import threading
import numpy as np
from scipy.signal import find_peaks

from src.config import readConfig
from src.sdr.lib.IQFileReader import IQFileReader

class SDRAnalyzer:

    def __init__(self):
        self.config = {}
        self.peaks = []
        self.reader = None
        self.image_buffer = None

        self.sample_rate = None
        self.center_freq = None
        self.fft_size = 4096
        self.fft_rows = None

        self.filter_peaks = False
        self.lock = threading.Lock()

    def configure(self, config_file):

        readConfig(config_file, self.config)

        self.sample_rate = self.config['DEFAULT_SAMPLE_RATE']
        self.center_freq = self.config['DEFAULT_CENTER_FREQ']
        self.fft_size = self.config['FFT_SIZE']
        self.fft_rows = self.config['FFT_ROWS']
        outfile_path = self.config['OUTFILE_PATH']

        self.filter_peaks = False

        self.reader = IQFileReader(outfile_path, block_size=self.fft_size)
        self.image_buffer = -100 * np.ones((self.fft_rows, self.fft_size))

    def detect_peak_bins(self, magnitude_db):

        mean = np.mean(magnitude_db)
        std = np.std(magnitude_db)

        peak_options = {
            'height'    : mean + 2 * std,               # Filters out background noise and low-level fluctuations.
            'prominence': 0.1 * np.max(magnitude_db),   # Rejects peaks that don't stand out from surrounding spectrum.
            'width'     : (3, 30),                      # Rejects sharp spikes (impulsive noise) and overly broad hills (clutter or poor resolution). Bin range; depends on your resolution
            'rel_height': 0.5                           # Ensures peak width is measured at a consistent threshold (half-max)
        }

        self.peaks, properties = find_peaks(magnitude_db, **peak_options)

        if self.filter_peaks: # filter by further criteria post-hoc
            filtered_peaks = []
            for i, peak in enumerate(self.peaks):
                w = properties['widths'][i] if 'widths' in properties else None
                p = properties['prominences'][i] if 'prominences' in properties else None
                if w and p and w > 20 and p > 1:
                    filtered_peaks.append(peak)
            self.peaks = np.array(filtered_peaks)

        return self.peaks

    def get_magnitudes(self, data):
        fft = np.fft.fftshift(np.fft.fft(data, n=self.fft_size))
        magnitude_db = 10 * np.log10(np.abs(fft)**2 + 1e-12)        # verify this
        self.detect_peak_bins(magnitude_db)
        return magnitude_db

    def compute_extent(self):
        freq_min = (self.center_freq - self.sample_rate / 2) / 1e6  # verify this
        freq_max = (self.center_freq + self.sample_rate / 2) / 1e6
        return [freq_min, freq_max, self.fft_rows, 0]

    def extract_signal(self, center_freq, bandwidth, start_time, end_time):
        offset = center_freq - self.center_freq
        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)
        num_samples = end_sample - start_sample

        self.reader.seek_time(start_time, self.sample_rate)
        data = self.reader.read_range(num_samples)

        # Frequency shift
        t = np.arange(len(data)) / self.sample_rate
        data_shifted = data * np.exp(-2j * np.pi * offset * t)

        # Band-pass filter placeholder (you can add scipy.signal.butter here)
        return data_shifted
