import os
import glob
import numpy as np
import time

class IQFileReader:

    def __init__(self, outfile_path, block_size):

        self.block_size = block_size
        self.outfile_path = outfile_path

        iq_files = glob.glob('../' + '*.iq')
        if not iq_files:
            raise FileNotFoundError("No .iq file found in the parent directory.")
        f = sorted(iq_files)[-1]
        print(f'Reading: {f}')

        self.file = open(f, 'rb')  # read as bytes
        self.path = f

    def read_block(self):
        while True:
            data = np.fromfile(self.file, dtype=np.complex64, count=self.block_size)
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
