from rtlsdr import RtlSdr
import numpy as np
import matplotlib.pyplot as plt

class SDRAnalyzer:
    def __init__(self, sample_rate=2.048e6, center_freq=100e6, freq_correction=60, gain='auto'):
        """Initialize the SDR with provided parameters."""
        self.sdr = RtlSdr()
        self.sdr.sample_rate = sample_rate
        self.sdr.center_freq = center_freq
        self.sdr.freq_correction = freq_correction
        self.sdr.gain = gain

    def read_samples(self, num_samples=2048):
        """Read samples from the SDR."""
        return self.sdr.read_samples(num_samples)

    def print_device_info(self):
        """Print the length of samples and valid gains for the SDR."""
        print(len(self.read_samples(1024)))
        print(self.sdr.valid_gains_db)

    def set_gain(self, gain_value):
        """Set the manual gain for the SDR."""
        self.sdr.gain = gain_value
        print(self.sdr.gain)

    def generate_data(self, fft_size=512, num_rows=500):
        """Generate and display a spectrogram from the SDR data."""
        x = self.read_samples(2048)  # get rid of initial empty samples
        x = self.read_samples(fft_size * num_rows)  # get all the samples we need for the spectrogram
        self.sdr.close()
        return x

    def generate_spectrogram(self, x, fft_size=512, num_rows=500):

        spectrogram = np.zeros((num_rows, fft_size))
        for i in range(num_rows):
            spectrogram[i, :] = 10 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(x[i * fft_size:(i + 1) * fft_size]))) ** 2)

        extent = [(self.sdr.center_freq + self.sdr.sample_rate / -2) / 1e6,
                  (self.sdr.center_freq + self.sdr.sample_rate / 2) / 1e6,
                  len(x) / self.sdr.sample_rate, 0]

        plt.imshow(spectrogram, aspect='auto', extent=extent)
        plt.xlabel("Frequency [MHz]")
        plt.ylabel("Time [s]")
        plt.show()

    def plot_psd(self, x):
        """Plot the Power Spectral Density (PSD) using matplotlib."""
        plt.psd(x, NFFT=1024, Fs=self.sdr.sample_rate / 1e6, Fc=self.sdr.center_freq / 1e6)
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
    sdr_analyzer = SDRAnalyzer()
    sdr_analyzer.set_gain(49.6)

    fft_size=512
    num_rows=500
    sdr_analyzer.print_device_info()
    x = sdr_analyzer.generate_data(
            fft_size=fft_size,
            num_rows=num_rows
    )

    sdr_analyzer.generate_spectrogram(x, fft_size=fft_size, num_rows=num_rows)
    sdr_analyzer.plot_psd(x)
    # sdr_analyzer.plot_iq_data(x)  # Pass your signal data here


