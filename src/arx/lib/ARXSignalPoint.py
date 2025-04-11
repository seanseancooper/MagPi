from src.lib.utils import format_time
from src.lib.SignalPoint import SignalPoint
from src.lib.Signal import Signal
from src.arx.lib.ARXAudioEncoder import ARXEncoder


class ARXSignalPoint(SignalPoint):
    """
    Class to encapsulate ARXRecorder recordings. This class holds audio data
    as a Signal() with a default sampling rate of 48Khz.
    Computes frequency features using ARXEncoder.
    """
    def __init__(self, worker_id, lon, lat, sgnl, audio_data=None, sr=48000):
        super().__init__(lon, lat, sgnl)
        self._worker_id = worker_id or 'ARXRecorder'
        self._signal_type = 'continuous'
        self._audio_data = audio_data                   # potentially a Signal or LIST of Signal
        self._sr = sr
        self._frequency_features = None                 # potentially a mapping of features


    def get_signal_type(self):
        return self._signal_type

    def get_sampling_rate(self):
        return self._sr

    def get_audio_data(self):
        return self._audio_data

    def set_audio_data(self, audio_data):
        self._audio_data = Signal(audio_data, self._id, sr=self._sr) # was a raw numpy array, now a Signal?
        self.compute_audio_frequency_features()

    def compute_audio_frequency_features(self):
        # Compute frequency features for the audio data
        arx = ARXEncoder(self._audio_data, self._sr)
        self._frequency_features = arx.compute_audio_frequency_features()
        yield self._frequency_features

    def get(self):
        return {
            "created"           : format_time(self._created, "%Y-%m-%d %H:%M:%S.%f"),
            "id"                : str(self._id),
            "worker_id"         : self._worker_id,
            "signal_type"       : self._signal_type,
            "lon"               : self._lon,
            "lat"               : self._lat,
            "audio_data"        : self._audio_data.tolist() if self._audio_data is not None else None,
            "frequency_features": self.compute_audio_frequency_features(),
        }


            # "zero_crossing_rate": zcr,
            # "spectral_centroid": centroid,
            # "spectral_bandwidth": bandwidth,
            # "spectral_flatness": flatness,
            # "spectral_contrast": contrast,
            # "spectral_rolloff": rolloff,
            # "tempo": float(tempo),
            # "mfcc": mfccs,
            # "chroma": chroma