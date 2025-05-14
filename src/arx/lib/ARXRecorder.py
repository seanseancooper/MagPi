import os
import queue
import threading
import time
from datetime import datetime, timedelta

import numpy as np
import sounddevice as sd
import soundfile as sf

from src.arx.lib.ARXSignalPoint import ARXSignalPoint
from src.lib.utils import get_location, format_time
from src.config import readConfig

import logging

arx_logger = logging.getLogger('arx_logger')

def file_writing_thread(*, q, **soundfile_args):
    """
    Thread function to continuously write audio data from queue to a file.
    Stops when it gets a `None` item.
    """
    with sf.SoundFile(**soundfile_args) as f:
        while True:
            data = q.get()
            if data is None:
                break
            f.write(data)

class ARXRecorder(threading.Thread):
    """
    Audio recorder class that records audio input to a file,
    monitors peak levels, and handles threading.
    """

    def __init__(self):
        super().__init__()
        self.config = {}

        self._input_overflows = 0
        self._OUTFILE = None

        self.is_mute = False
        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()  # elapsed time since creation

        self._worker_id = 'ARXRecorder'
        self._signal_type = None                    # Emission type (radar, voice, data)

        self._stream = None
        self.thread = None
        self.recording = self.previously_recording = False
        self.audioq = queue.Queue()                 # Unbounded queue for audio frames
        self.metering_q = queue.Queue(maxsize=1)    # Small queue for metering
        self.peak = 0.0
        self.meter = {'max': 1.0, 'peak_percentage': 0}
        self.signal_cache = []  # Cache of peaks (unbounded)

        self.lon = 0.0
        self.lat = 0.0

    def configure(self, config_file):
        """
        Loads configuration from file and sets location.
        """
        if not config_file:
            exit(1)

        readConfig(config_file, self.config)
        get_location(self)
        self._signal_type = ARXSignalPoint.get_signal_type(self)

    def create_stream(self):
        """
        Creates and starts the audio input/output stream.
        """
        if self._stream is not None:
            self._stream.close()

        INPUT_DEVICE = self.config.get('INPUT_DEVICE', 0)
        OUTPUT_DEVICE = self.config.get('OUTPUT_DEVICE', 1)
        SR = self.config.get('SR', 44100)
        BLOCKSIZE = self.config.get('BLOCKSIZE', 1000)
        DTYPE = self.config.get('DTYPE', 'float32')
        LATENCY = self.config.get('LATENCY', 0.1)
        CHANNELS = self.config.get('CHANNELS', 2)

        self._stream = sd.Stream(device=(INPUT_DEVICE, OUTPUT_DEVICE),
                                 samplerate=SR,
                                 blocksize=BLOCKSIZE,
                                 dtype=DTYPE,
                                 latency=LATENCY,
                                 channels=CHANNELS,
                                 callback=self.streamCallback)

        self._stream.start()

    def streamCallback(self, indata, outdata, frames, time, status):
        """
        Callback executed for every audio block.
        Pushes audio to queue for writing and updates peak metering.
        """
        if status.input_overflow:
            self._input_overflows += 1

        if self.recording:
            if not self.is_mute:
                self.audioq.put(indata.copy())
            else:
                # Push silence if muted
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
        """
        Updates the meter readings for audio peak levels.
        """
        self.updated = datetime.now()
        self.elapsed = self.updated - self.created

        try:
            self.meter['peak_percentage'] = float(self.metering_q.get_nowait())
        except queue.Empty:
            pass

        return self.meter

    def after(self, ms, func=None, *args):
        """
        Delayed call to a function after specified milliseconds.
        """
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
        """
        Waits until the file writing thread completes.
        """
        self.after(10, self._wait_for_thread)

    def _wait_for_thread(self):
        """
        Helper method to join the writing thread.
        """
        if self.thread.is_alive():
            self.wait_for_thread()
            return
        self.thread.join()

    def get_worker_id(self):
        """
        Returns the worker identifier.
        """
        return self._worker_id

    def stop(self):
        """
        Stops recording and waits for thread completion.
        """
        self.recording = False
        self.wait_for_thread()

        arxs = ARXSignalPoint(self.get_worker_id(),
                              self.lon,
                              self.lat,
                              self.signal_cache[:-1])  # remove signal_cache

        data, sr   = sf.read(self._OUTFILE)

        arxs.set_audio_data(data)
        arxs.set_sampling_rate(sr)

        arxs.set_text_attribute('signal_type', self._signal_type)
        arxs.set_text_attribute('sent', format_time(datetime.now(), "%Y-%m-%d %H:%M:%S.%f"))
        arxs.set_text_attribute('fs_path', self._OUTFILE)
        arxs.set_text_attribute('channels', data.shape[1])
        arxs.set_text_attribute('sr', sr)
        arxs.set_text_attribute('frame_shape', data.shape)
        arxs.set_text_attribute('dtype', str(data.dtype))

        return arxs

    def run(self):
        """
        Main method that starts recording audio to a file.
        """
        self.recording = True

        if not os.path.exists(self.config['OUTFILE_PATH']):
            os.mkdir(self.config['OUTFILE_PATH'])

        self._OUTFILE = os.path.join(
            self.config['OUTFILE_PATH'],
            datetime.now().strftime(self.config['DATETIME_FORMAT']) +
            "_" +
            self.config['OUTFILE_NAME'] +
            self.config['OUTFILE_EXTENSION']
        )
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
            daemon=False,  # Important: non-daemon to finalize files correctly
        )
        self.thread.start()

if __name__ == '__main__':
    # Entry point when run as a standalone script
    arxRec = ARXRecorder()
    arxRec.configure('arx.json')

    def run() -> None:
        import atexit
        def stop():
            arxRec.stop()  # required cleanup
        atexit.register(stop)

        arxRec.run()

    run()
