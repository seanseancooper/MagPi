import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.colors as mcolors
from matplotlib import cm
from matplotlib.colors import ListedColormap


class IQFileReader:
    def __init__(self, filename, block_size=4096):
        self.filename = filename
        self.block_size = block_size
        self.file = open(filename, "rb")

    def read_block(self):
        while True:
            data = np.fromfile(self.file, dtype=np.complex64, count=self.block_size)
            if data.size == 0:
                time.sleep(0.01)
                continue
            return data

    def close(self):
        self.file.close()


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
                vmin=-100,
                vmax=30,
                cmap=self.cmap,
                extent=self.compute_extent(),
                origin='lower'
        )

        self.ax.set_xlabel("MHz")
        self.ax.set_ylabel("Time")
        self.anim = FuncAnimation(self.fig, self.update, interval=100, blit=False)

    def create_custom_colormap(self):
        base = cm.get_cmap('viridis', 256)
        colors = base(np.linspace(0, 1, 256))
        red = np.array([1, 0, 0, 1])  # RGBA for red
        extended = np.vstack([colors, red])
        return ListedColormap(extended)

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
        row = self.generate_spectrogram_row(data)

        # Detect strong signals (simple threshold)
        peak_threshold = -30  # dB
        peak_indices = np.where(row > peak_threshold)[0]

        # Roll buffer and insert new row
        self.image_buffer = np.roll(self.image_buffer, -1, axis=0)
        self.image_buffer[-1, :] = row

        # Optional: Apply a marker value (e.g., 999) for peaks
        # You can store that in a parallel mask or directly modify the buffer
        self.peak_mask = np.zeros_like(self.image_buffer, dtype=bool)
        self.peak_mask[-1, peak_indices] = True

        # Combine image and peak mask for display using color-mapped values
        display_image = self.image_buffer.copy()
        display_image[self.peak_mask] = 999  # Special value for "red"

        self.image.set_data(display_image)
        return [self.image]

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
