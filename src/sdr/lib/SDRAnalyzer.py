import numpy as np
import pylab as pyl
from matplotlib.mlab import psd

NFFT = 4096
NUM_ROWS = 500  # Number of spectrogram rows to show in the waterfall
SAMPLE_RATE = 2.048e6  # 2.048 MHz sample rate
CENTER_FREQ = 100e6    # 900 MHz center frequency

class IQFileReader:
    def __init__(self, filename, block_size=4096):
        self.filename = filename
        self.block_size = block_size
        self.file = open(filename, "rb")

    def __iter__(self):
        return self

    def __next__(self):
        data = np.fromfile(self.file, dtype=np.complex64, count=self.block_size)
        if data.size == 0:
            self.file.close()
            raise StopIteration
        return data

    def close(self):
        self.file.close()

class SDRAnalyzer:
    def __init__(self, filename):
        self.reader = IQFileReader(filename, block_size=NFFT)
        self.fft_size = NFFT
        self.num_rows = NUM_ROWS
        self.sample_rate = SAMPLE_RATE
        self.center_freq = CENTER_FREQ

        self.image_buffer = -100 * np.ones((self.num_rows, self.fft_size))  # dB scale
        self.fig, self.ax = pyl.subplots()
        self.image = self.ax.imshow(
            self.image_buffer,
            aspect='auto',
            interpolation='nearest',
            vmin=-50,
            vmax=35,
            extent=self.compute_extent(),
            origin='lower'
        )

    def compute_extent(self):
        freq_min = (self.center_freq - self.sample_rate / 2) / 1e6
        freq_max = (self.center_freq + self.sample_rate / 2) / 1e6
        return [freq_min, freq_max, 0, self.num_rows]

    def generate_spectrogram_row(self, data):
        fft = np.fft.fftshift(np.fft.fft(data, n=self.fft_size))
        magnitude_db = 10 * np.log10(np.abs(fft)**2 + 1e-12)  # Avoid log(0)
        return magnitude_db

    def run(self):
        pyl.ion()  # Turn on interactive mode

        for block in self.reader:
            row = self.generate_spectrogram_row(block)
            print(f"Min: {np.min(row):.2f} dB, Max: {np.max(row):.2f} dB, Mean: {np.mean(row):.2f} dB")

            self.image_buffer = np.vstack([self.image_buffer[1:], row[None, :]])  # Add new row to bottom

            self.image.set_data(self.image_buffer)
            self.image.set_extent(self.compute_extent())
            self.ax.set_xlabel("Frequency (MHz)")
            self.ax.set_ylabel("Time (scrolling)")

            pyl.pause(0.01)  # Small delay to update plot

        self.reader.close()
        pyl.ioff()
        pyl.show()


if __name__ == '__main__':
    filename = "/Users/scooper/PycharmProjects/MagPi/src/sdr/rtlsdr_20250602_172353_4100654000_2048000.0.iq"
    analyzer = SDRAnalyzer(filename)
    analyzer.run()
