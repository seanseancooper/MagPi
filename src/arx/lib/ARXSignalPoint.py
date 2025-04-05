from src.lib.SignalPoint import SignalPoint
from src.arx.lib.ARXAudioEncoder import ARXEncoder


class ARXSignalPoint(SignalPoint):
    """
    Class to handle continuous audio signals. This class encapsulates both the raw audio data and its frequency features.
    """
    def __init__(self, worker_id, lon, lat, sgnl, audio_data=None, sampling_rate=44100):
        super().__init__(lon, lat, sgnl)
        self._worker_id = worker_id
        self._signal_type = 'continuous'
        self._audio_data = audio_data                   # Raw audio data as numpy array
        self._sampling_rate = sampling_rate
        self._frequency_features = None

        if audio_data is not None:
            # Compute frequency features for the audio data
            arx  = ARXEncoder(audio_data, self._sampling_rate)
            self._frequency_features = arx.compute_audio_frequency_features()

    def get_signal_type(self):
        return self._signal_type

    def get_audio_data(self):
        """
        Accessor method for raw audio data.
        """
        return self._audio_data

    def set_audio_data(self, audio_data):
        """
        Mutator method for raw audio data.
        """
        self._audio_data = audio_data
        arx = ARXEncoder(self._audio_data, self._sampling_rate)
        self._frequency_features = arx.compute_audio_frequency_features()
