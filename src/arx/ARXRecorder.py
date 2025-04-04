import os
import queue
import threading
import time
from datetime import datetime, timedelta

import numpy as np
import sounddevice as sd
import soundfile as sf

from src.config import readConfig


def file_writing_thread(*, q, **soundfile_args):
    with sf.SoundFile(**soundfile_args) as f:
        while True:
            data = q.get()
            if data is None:
                break
            f.write(data)


class ARXRecorder(threading.Thread):
    ''' Passthrough recording '''

    def __init__(self):
        super().__init__()
        self.config = {}

        self._input_overflows = 0
        self._OUTFILE = None

        self.is_mute = False
        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()              # elapsed time since created

        self._worker_id = 'ARXRecorder'

        self._stream = None
        self.thread = None
        self.recording = self.previously_recording = False
        self.audioq = queue.Queue()
        self.metering_q = queue.Queue(maxsize=1)
        self.peak = 0.0
        self.meter = {'max': 1.0, 'peak_percentage': 0}
        self.signal_cache = []   # a lists of audio SignalPoint.


    def configure(self, config_file):

        if not config_file:
            exit(1)

        readConfig(config_file, self.config)

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

        if self.recording:
            if not self.is_mute:
                self.audioq.put(indata.copy())
            else:
                # fill with silence..
                self.audioq.put(np.zeros(np.shape(indata.copy())))
            self.previously_recording = True
        else:
            if self.previously_recording:
                self.audioq.put(None)
                self.previously_recording = False

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

        self.updated = datetime.now()
        self.elapsed = self.updated - self.created

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
        self.recording = False
        self.wait_for_thread()

    def run(self):
        self.recording = True

        if not os.path.exists(self.config['OUTFILE_PATH']):
            os.mkdir(self.config['OUTFILE_PATH'])

        self._OUTFILE = os.path.join(self.config['OUTFILE_PATH'],
                                     datetime.now().strftime(self.config['DATETIME_FORMAT']) +
                                     "_" +
                                     self.config['OUTFILE_NAME'] + self.config['OUTFILE_EXTENSION'])
        self.create_stream()

        self.thread = threading.Thread(
                target=file_writing_thread,
                kwargs=dict(
                        file=self._OUTFILE,
                        mode='w',
                        samplerate=int(self._stream.samplerate),
                        channels=self.config['CHANNELS'],
                        q=self.audioq,
                ),
                # "Exception ignored in: <module 'threading'...":
                # This cannot be a daemon and 'cut' files correctly
                # due to the way it is being run.
                daemon=False,
        )
        self.thread.start()


if __name__ == '__main__':

    arxRec = ARXRecorder()
    arxRec.configure('arx.json')

    def run() -> None:
        import atexit

        def stop():
            arxRec.stop()  # required.
        atexit.register(stop)

        arxRec.run()

    run()
