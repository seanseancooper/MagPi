from src.lib.SignalPoint import SignalPoint
from src.lib.Signal import Signal
from src.arx.lib.ARXAudioEncoder import ARXEncoder


class ARXSignalPoint(SignalPoint):
    """
    Class to handle ARXRecorder recordings. This class encapsulates the raw audio data as a Signal()
    and computes the frequency features using ARXEncoder.
    """
    def __init__(self, worker_id, lon, lat, sgnl, audio_data=None):
        super().__init__(lon, lat, sgnl)

        self._worker_id = worker_id
        self._signal_type = 'continuous'
        self._audio_data = audio_data                   # Raw numpy array, not a Signal?
        self._sr = 44100
        self._frequency_features = None

        if audio_data is not None:
            # Compute frequency features for the audio data
            arx  = ARXEncoder(audio_data, self._sr) # assumes numpy array...
            self._frequency_features = arx.compute_audio_frequency_features()

    def get_signal_type(self):
        return self._signal_type

    def get_sampling_rate(self):
        return self._sr

    def get_audio_data(self):
        return self._audio_data

    def set_audio_data(self, audio_data):
        self._audio_data = Signal(audio_data, self._id, sr=self._sr) # was a raw numpy array, now a Signal?
        arx = ARXEncoder(self._audio_data, self._sr)
        self._frequency_features = arx.compute_audio_frequency_features()
