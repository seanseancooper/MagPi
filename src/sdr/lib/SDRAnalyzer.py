import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import cm
from matplotlib.colors import ListedColormap
from scipy.signal import find_peaks
from src.sdr.lib.IQFileReader import IQFileReader


class SDRAnalyzer:
    def __init__(self, filename):
        self.fft_size = 4096
        self.num_rows = 100
        self.sample_rate = 2.048e6
        self.center_freq = 100e6

        self.reader = IQFileReader(filename, block_size=self.fft_size)
        self.image_buffer = -100 * np.ones((self.num_rows, self.fft_size))  # dB scale

        self.fig, self.ax = plt.subplots()
        self.cmap = self.create_custom_colormap()
        self.image = self.ax.imshow(
                self.image_buffer,
                aspect='auto',
                interpolation='nearest',
                vmin=-30,
                vmax=40,
                cmap=self.cmap,
                extent=self.compute_extent(),
                origin='lower'
        )

        self.ax.set_xlabel("MHz")
        self.ax.set_ylabel("Time")
        self.anim = FuncAnimation(self.fig, self.update, interval=100, blit=False)

        self.seen_frequencies = set()
        self.filter_peaks = False

    def create_custom_colormap(self):
        base = cm.get_cmap('viridis', 256)
        colors = base(np.linspace(0, 1, 256))
        red = np.array([1, 0, 0, 1])  # RGBA for red
        extended = np.vstack([colors, red])
        return ListedColormap(extended)

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

    def compute_extent(self):
        freq_min = (self.center_freq - self.sample_rate / 2) / 1e6
        freq_max = (self.center_freq + self.sample_rate / 2) / 1e6
        return [freq_min, freq_max, self.num_rows, 0]

    def generate_spectrogram_row(self, data):
        fft = np.fft.fftshift(np.fft.fft(data, n=self.fft_size))
        magnitude_db = 10 * np.log10(np.abs(fft)**2 + 1e-12)  # Avoid log(0)
        return magnitude_db

    def update(self, frame):
        data = self.reader.read_block()
        if data is None:
            return [self.image]

        row = self.generate_spectrogram_row(data)

        # Update image buffer
        self.image_buffer = np.roll(self.image_buffer, -1, axis=0)
        self.image_buffer[-1, :] = row
        self.image.set_data(self.image_buffer)

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

        freq_min, freq_max, _, _ = self.compute_extent()
        for bin_idx in peaks:
            freq = freq_min + (freq_max - freq_min) * bin_idx / self.fft_size
            line = self.ax.axvline(freq, color='red', linestyle='-', linewidth=0.8)
            self.highlight_lines.append(line)

        return [self.image] + self.highlight_lines

    def run(self):
        plt.show()
        self.reader.close()


if __name__ == '__main__':
    import glob

    iq_files = glob.glob('.' + './*.iq')
    if not iq_files:
        raise FileNotFoundError("No .iq file found in the current directory.")
    analyzer = SDRAnalyzer(iq_files[-1])
    analyzer.run()
