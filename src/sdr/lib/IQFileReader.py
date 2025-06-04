import numpy as np
import time

class IQFileReader:

    def __init__(self, block_size=4096):

        self.block_size = block_size

        import glob
        iq_files = glob.glob('../' + '*.iq')
        if not iq_files:
            raise FileNotFoundError("No .iq file found in the current directory.")
        f = sorted(iq_files)[-1]
        print(f'reading: {f}')
        self.file = open(f, 'r')

    def read_block(self):
        while True:
            data = np.fromfile(self.file, dtype=np.complex64, count=self.block_size)
            if data.size == 0:
                time.sleep(0.01)
                continue
            return data

    def close(self):
        self.file.close()
