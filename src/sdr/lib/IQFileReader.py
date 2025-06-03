import numpy as np
import time

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

