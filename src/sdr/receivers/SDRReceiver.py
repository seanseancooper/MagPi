from rtlsdr import RtlSdr
from src.sdr.lib.SDRSignalPoint import SDRSignalPoint

class SDRReceiver:

    def __init__(self, sr=2.048e6, center_freq=100e6, freq_correction=60, gain='auto'):
        """Initialize the SDR hardware with provided parameters.
        Received energy on a particular frequency may start a recorder, and alert a human
        to listen to the signals if they are intelligible (i.e., COMINT). If the frequency
        is not known, the operators may look for power on primary or sideband frequencies
        using a spectrum analyzer. Information from the spectrum analyzer is then used to
        tune receivers to signals of interest.
        """
        self.sdr = RtlSdr()
        self.sdr.sample_rate = sr
        self.sdr.center_freq = center_freq
        self.sdr.freq_correction = freq_correction
        self.sdr.gain = gain
        self.data = None
        self.signalpoint = None

    def get_sample_rate(self):
        return self.sdr.sample_rate

    def get_center_freq(self):
        return self.sdr.center_freq

    def get_freq_correction(self):
        return self.sdr.freq_correction

    def get_gain(self):
        return self.sdr.gain

    def set_gain(self, gain_value):
        self.sdr.gain = gain_value

    # needs to be renamed: self.module_retriever.get_parsed_cells()
    def get_parsed_cells(self):
        return [self.signalpoint]

    # needs to be renamed: self.module_retriever.scan()
    def scan(self):
        print(f'scannin....{self.signalpoint}')
        # return self.get_data()

    def get_data(self, fft_size=512, num_rows=500):
        x = self.read_samples(2048)  # get rid of initial empty samples
        x = self.read_samples(fft_size * num_rows)  # get all the samples we need for the spectrogram
        self.sdr.close()

        # test SDRSignalPoint
        self.signalpoint = SDRSignalPoint(
                'worker_id',
                0.0,  # lat
                0.0,  # lon
                0.0,  # sgnl
                array_data=x,
                audio_data=None,
                sr=self.sdr.sample_rate)

        print(self.signalpoint.get_audio_frequency_features())

        return x

    def read_samples(self, num_samples=2048):
        """Read samples from the SDR."""
        return self.sdr.read_samples(num_samples)

    def print_device_info(self):
        """Print the length of samples and valid gains for the SDR."""
        print(len(self.read_samples(1024)))
        print(self.sdr.valid_gains_db)

if __name__ == '__main__':
    sdr_analyzer = SDRReceiver()
    sdr_analyzer.set_gain(49.6)

    fft_size=512
    num_rows=500

    sdr_analyzer.print_device_info()

    data = sdr_analyzer.get_data(
            fft_size=fft_size,
            num_rows=num_rows
    )
    print(data)


