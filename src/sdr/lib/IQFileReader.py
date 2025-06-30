import os
import glob
import numpy as np
import time

class IQFileReader:

    def __init__(self, outfile_path, block_size):

        self.block_size = block_size
        self.outfile_path = outfile_path

        self.iq_files  = None
        self.file = None
        self.path = None
        self.load_file()

    def set_path(self, path):
        self.path = path

    def get_path(self):
        return self.path

    def load_file(self, target=None):
        """ set self.file to either latest or target """
        self.iq_files = sorted(glob.glob(self.outfile_path + '/*.iq'))
        if not self.iq_files:
            raise FileNotFoundError("No .iq file found in the parent directory.")

        self.path = target if target else self.iq_files[-1] # target or current file.
        self.file = open(self.path, 'rb')  # read as bytes
        print(f'Reading: {self.path}')

    def read_block(self):
        while True:

            def test_signal(num_samples):
                import numpy as np

                samplerate = 2.048e6
                samples = np.arange(num_samples) / samplerate

                amplitude = 1.0
                base_signal = amplitude * np.sin(2 * np.pi * 97e6 * samples)
                complex_signal = np.exp(1j * base_signal)

                noise = (np.random.randn(num_samples) + 1j * np.random.randn(num_samples)) / np.sqrt(2)  # complex noise with unity power
                noise_power = 2
                noisy_complex_signal = complex_signal + noise * np.sqrt(noise_power)

                # return base_signal.astype(np.complex64)
                # return noise.astype(np.complex64)
                return complex_signal.astype(np.complex64)
                # return noisy_complex_signal.astype(np.complex64)

            data = np.fromfile(self.file, dtype=np.complex64, count=self.block_size)
            # data = test_signal(self.block_size)
            if data.size == 0:
                time.sleep(0.01)
                continue
            return data

    def seek_time(self, start_time, sample_rate):
        byte_offset = int(start_time * sample_rate) * np.dtype(np.complex64).itemsize
        self.file.seek(byte_offset, os.SEEK_SET)

    def read_range(self, sample_count):
        return np.fromfile(self.file, dtype=np.complex64, count=sample_count)

    def close(self):
        self.file.close()
