import os
import queue
import threading
import time
from collections import defaultdict
from datetime import datetime

import numpy as np
import sounddevice as sd
import soundfile as sf

from src.config import readConfig


class ARXRecorder(threading.Thread):
    ''' Passthrough recording '''

    @staticmethod
    def file_writing_thread(*, q, **soundfile_args):
        with sf.SoundFile(**soundfile_args) as f:
            while True:
                data = q.get()
                if data is None:
                    break
                f.write(data)

    def __init__(self):
        super().__init__()
        self.config = {}

        self._input_overflows = 0
        self._OUTFILE = None

        self.is_mute = False
        self.updated = None

        self._stream = None
        self.thread = None
        self.audioq = queue.Queue()
        self.metering_q = queue.Queue(maxsize=1)
        self.peak = 0.0
        self.meter = {'max': 1.0, 'peak_percentage': 0}
        self.signal_cache = []   # a lists of audio SignalPoint.


    def configure(self, config_file):

        if not config_file:
            exit(1)

        readConfig(config_file, self.config)

        self.create_stream()

        if not os.path.exists(self.config['OUTFILE_PATH']):
            os.mkdir(self.config['OUTFILE_PATH'])

        self._OUTFILE = os.path.join(self.config['OUTFILE_PATH'],
                                     datetime.now().strftime(self.config['DATETIME_FORMAT']) +
                                     "_" +
                                     self.config['OUTFILE_NAME'] + self.config['OUTFILE_EXTENSION'])

    def create_stream(self):

        if self._stream is not None:
            self._stream.close()

        INPUT_DEVICE = self.config.get('INPUT_DEVICE', 0)
        OUTPUT_DEVICE = self.config.get('OUTPUT_DEVICE', 1)
        SR = self.config.get('SR', 44100)
        BLOCKSIZE = self.config.get('BLOCKSIZE', 1000)
        DTYPE = self.config.get('DTYPE', 'float32')
        LATENCY = self.config.get('LATENCY', 0.1)
        CHANNELS = self.config.get('CHANNELS', 2)

        self._stream = sd.Stream(device=(INPUT_DEVICE,
                                         OUTPUT_DEVICE),
                                 samplerate=SR,
                                 blocksize=BLOCKSIZE,
                                 dtype=DTYPE,
                                 latency=LATENCY,
                                 channels=CHANNELS,
                                 callback=self.streamCallback)

        self._stream.start()

    def streamCallback(self, indata, outdata, frames, time, status):
        if status.input_overflow:
            self._input_overflows += 1

        if not self.thread:
            if self.is_mute:
                self.audioq.put(None)
        elif self.thread.is_alive():
            if self.is_mute is False:
                self.audioq.put(indata.copy())
            else:
                # fill with silence..
                self.audioq.put(np.zeros(np.shape(indata.copy())))

        c_level = max(self.peak, np.max(np.abs(indata)))

        try:
            self.peak = min(c_level, 100.00)
            self.signal_cache.append(self.peak)
            self.metering_q.put_nowait(self.peak)
        except queue.Full:
            pass
        else:
            self.peak = 0.0

        self.update_meter()

    def update_meter(self):

        try:
            self.meter['peak_percentage'] = float(self.metering_q.get_nowait())
        except queue.Empty:
            pass

        return self.meter

    def after(self, ms, func=None, *args):
        """Call function once after given time.

        MS specifies the time in milliseconds. FUNC gives the
        function which shall be called. Additional parameters
        are given as parameters to the function call.  Return
        identifier to cancel scheduling with after_cancel."""
        if not func:
            time.sleep(ms * 0.1)
            return None
        else:
            try:
                time.sleep(ms * 0.1)
                return self._wait_for_thread()
            except KeyboardInterrupt:
                pass

    def wait_for_thread(self):
        self.after(10, self._wait_for_thread)

    def _wait_for_thread(self):
        if self.thread.is_alive():
            self.wait_for_thread()
            return
        self.thread.join()

    def stop(self):
        self.wait_for_thread()

    def run(self):
        self.thread = threading.Thread(
                target=self.file_writing_thread,
                kwargs=dict(
                        file=self._OUTFILE,
                        mode='w',
                        samplerate=int(self._stream.samplerate),
                        channels=self.config['CHANNELS'],
                        q=self.audioq,
                ),
        )
        self.thread.start()


if __name__ == '__main__':
    from src.config import CONFIG_PATH

    arxRec = ARXRecorder()
    arxRec.configure(os.path.join(CONFIG_PATH, 'arx.json'))
    arxRec.run()
