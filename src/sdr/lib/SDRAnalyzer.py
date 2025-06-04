import io
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
from src.sdr.lib.IQFileReader import IQFileReader

class SDRAnalyzer:

    def __init__(self):
        self.fft_size = 4096
        self.num_rows = 100
        self.sample_rate = 2.048e6
        self.center_freq = 100e6

        self.reader = IQFileReader(block_size=self.fft_size)
        self.image_buffer = -100 * np.ones((self.num_rows, self.fft_size))
        self.lock = threading.Lock()

        self.streaming = True
        self.thread = threading.Thread(target=self.update_loop)
        self.thread.daemon = True
        self.thread.start()

    def generate_spectrogram_row(self, data):
        fft = np.fft.fftshift(np.fft.fft(data, n=self.fft_size))
        magnitude_db = 10 * np.log10(np.abs(fft)**2 + 1e-12)
        return magnitude_db

    def update_loop(self):

        # Remove previous highlight lines
        # for line in getattr(self, 'highlight_lines', []):
        #     line.remove()

        # Detect peaks and draw vertical lines
        # self.highlight_lines = []
        # peaks = self.detect_peak_bins(row)

        # peak_freq = self.get_peak_freq(peak)
        # # Skip if frequency is already tracked (within tolerance)
        # if any(abs(peak_freq - f) < 2000 for f in self.seen_frequencies):
        #     continue
        #
        # self.seen_frequencies.add(peak_freq)

        # freq_min, freq_max, _, _ = self.compute_extent()
        # for bin_idx in peaks:
        #     freq = freq_min + (freq_max - freq_min) * bin_idx / self.fft_size
        #     line = self.ax.axvline(freq, color='red', linestyle='-', linewidth=0.8)
        #     self.highlight_lines.append(line)

        # return [self.image] + self.highlight_lines

        while self.streaming:
            data = self.reader.read_block()
            row = self.generate_spectrogram_row(data)
            with self.lock:
                self.image_buffer = np.roll(self.image_buffer, -1, axis=0)
                self.image_buffer[-1, :] = row
            time.sleep(0.1)

    def render_spectrogram_png(self):
        with self.lock:
            fig, ax = plt.subplots()
            extent = self.compute_extent()
            ax.imshow(self.image_buffer, aspect='auto', origin='lower', extent=extent, cmap='viridis', vmin=-30, vmax=30)
            ax.set_xlabel("Frequency (MHz)")
            ax.set_ylabel("Time")
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close(fig)
            buf.seek(0)
            return buf

    def compute_extent(self):
        freq_min = (self.center_freq - self.sample_rate / 2) / 1e6
        freq_max = (self.center_freq + self.sample_rate / 2) / 1e6
        return [freq_min, freq_max, 0, self.num_rows]

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

if __name__ == '__main__':
    analyzer = SDRAnalyzer()
    analyzer.run()
