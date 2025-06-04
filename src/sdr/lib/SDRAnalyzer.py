import io
import threading
import time
import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from src.sdr.lib.IQFileReader import IQFileReader

class SDRAnalyzer:

    def __init__(self):
        self.fft_size = 4096
        self.num_rows = 100
        self.sample_rate = 2.048e6
        self.center_freq = 100e6

        self.filter_peaks = False
        self.peaks = []

        self.reader = IQFileReader(block_size=self.fft_size)
        self.image_buffer = -100 * np.ones((self.num_rows, self.fft_size))
        self.lock = threading.Lock()

        self.streaming = True
        self.thread = threading.Thread(target=self.update_loop)
        self.thread.daemon = True
        self.thread.start()

    def detect_peak_bins(self, magnitude_db):

        mean = np.mean(magnitude_db)
        std = np.std(magnitude_db)

        peak_options = {
            'height'    : mean + 2 * std,               # Filters out background noise and low-level fluctuations.
            'prominence': 0.1 * np.max(magnitude_db),   # Rejects peaks that don't stand out from surrounding spectrum.
            'width'     : (3, 30),                      # Rejects sharp spikes (impulsive noise) and overly broad hills (clutter or poor resolution). Bin range; depends on your resolution
            'rel_height': 0.5                           # Ensures peak width is measured at a consistent threshold (half-max)
        }

        peaks, properties = find_peaks(magnitude_db, **peak_options)

        if self.filter_peaks: # filter by further criteria post-hoc
            filtered_peaks = []
            for i, peak in enumerate(peaks):
                w = properties['widths'][i] if 'widths' in properties else None
                p = properties['prominences'][i] if 'prominences' in properties else None
                if w and p and w > 20 and p > 1:
                    filtered_peaks.append(peak)
            return np.array(filtered_peaks)

        return peaks

    def generate_spectrogram_row(self, data):
        fft = np.fft.fftshift(np.fft.fft(data, n=self.fft_size))
        magnitude_db = 10 * np.log10(np.abs(fft)**2 + 1e-12)
        return magnitude_db

    def update_loop(self):
        while self.streaming:
            data = self.reader.read_block()
            row = self.generate_spectrogram_row(data)
            self.peaks = self.detect_peak_bins(row)
            with self.lock:
                self.image_buffer = np.roll(self.image_buffer, -1, axis=0)
                self.image_buffer[-1, :] = row
            time.sleep(0.1)

    def compute_extent(self):
        freq_min = (self.center_freq - self.sample_rate / 2) / 1e6
        freq_max = (self.center_freq + self.sample_rate / 2) / 1e6
        return [freq_min, freq_max, self.num_rows, 0]

    def render_spectrogram_png(self):
        with self.lock:
            fig, ax = plt.subplots()
            extent = self.compute_extent()

            freq_min, freq_max, _, _ = self.compute_extent()
            for bin_idx in self.peaks:

                # Skip if frequency is already tracked (within tolerance)
                # if any(abs(peak_freq - f) < 2000 for f in self.seen_frequencies):
                #     continue
                #
                # self.seen_frequencies.add(peak_freq)

                freq = freq_min + (freq_max - freq_min) * bin_idx / self.fft_size
                line = ax.axvline(freq, color='red', linestyle='-', linewidth=0.8)

            ax.imshow(self.image_buffer, aspect='auto', origin='lower', extent=extent, cmap='viridis', vmin=-30, vmax=30)
            ax.set_xlabel("Frequency (MHz)")
            ax.set_ylabel("Time")
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close(fig)
            buf.seek(0)
            return buf

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
