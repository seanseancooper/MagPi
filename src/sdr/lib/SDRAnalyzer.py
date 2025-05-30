import threading

import numpy as np
import matplotlib.pyplot as plt

class SDRAnalyzer(threading.Thread):

    #  Fast Fourier Transform (FFT): FFT converts a time-series signal into a set of frequency components.
    #     We use it to extract dominant frequencies, spectral power, and energy concentration.
    # compute_fft_features(signal_values, sampling_rate=1)
    #
    #
    #     Spectral Analysis Features to Extract for Each Signal [scipy.signal, numpy.fft]:
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


    def __init__(self, data, sr=2.048e6, center_freq=100e6, fft_size=4096, num_rows=500):
        super().__init__()
        self._data = data
        self._sr = sr
        self.center_freq = center_freq
        self.fft_size = fft_size
        self.num_rows = num_rows

    def set_data(self, data):
        self._data = data

    def read_file(self, f):
        self._data = np.fromfile(f, np.complex64)  # Read in file

    def get_data(self):
        return self._data

    def generate_spectrogram(self, data):
        spectrogram = np.zeros((self.num_rows, self.fft_size))
        for i in range(self.num_rows):
            spectrogram[i, :] = 10 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(data[i * self.fft_size:(i + 1) * self.fft_size]))) ** 2)

        extent = [(self.center_freq + self._sr / -2) / 1e6,
                  (self.center_freq + self._sr / 2) / 1e6,
                  len(data) / self._sr, 0]

        plt.imshow(spectrogram, aspect='auto', extent=extent)
        plt.xlabel("Frequency [MHz]")
        plt.ylabel("Time [s]")
        plt.show()

    def plot_psd(self, x):
        """Plot the Power Spectral Density (PSD) using matplotlib."""
        plt.psd(x, NFFT=1024, Fs=self._sr / 1e6, Fc=self.center_freq / 1e6)
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Relative power (dB)')
        plt.show()

    def plot_iq_data(self, x):
        """Plot I/Q data from the SDR samples."""
        plt.plot(x.real)
        plt.plot(x.imag)
        plt.legend(["I", "Q"])
        plt.savefig("./rtlsdr-gain.svg", bbox_inches='tight')
        plt.show()

if __name__ == '__main__':

    a = SDRAnalyzer([])
    a.read_file('/Users/scooper/PycharmProjects/MagPi/_out/bandwidth_block.raw')

    a.generate_spectrogram(a.get_data())
    a.plot_psd(a.get_data())
    a.plot_iq_data(a.get_data())


