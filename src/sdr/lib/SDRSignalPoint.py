import numpy as np
from src.lib.utils import format_time
from src.lib.SignalPoint import SignalPoint
from src.lib.Signal import Signal
import librosa
from librosa import feature


class SDRSignalPoint(SignalPoint):
    """
    Class to handle SDR signals. This class is designed to hold raw numpy array data and/or 'audible'
    audio data from an SDR, and compute audio frequency features.
    """
    def __init__(self, worker_id, lon, lat, sgnl, audio_data=None, array_data=None, sampling_rate=None):
        super().__init__(lon, lat, sgnl)
        self._worker_id = worker_id

        self._audio_data = audio_data
        self._sampling_rate = sampling_rate
        self._array_data = array_data

        self._audio_frequency_features = None

        if audio_data is not None and sampling_rate is not None:
            self._audio_frequency_features = self.compute_audio_frequency_features(audio_data, sampling_rate)

        if array_data is not None:
            self._array_frequency_features = self.compute_array_features(array_data)

    def get(self):
        data = {
            "created": format_time(self._created, "%Y-%m-%d %H:%M:%S.%f"),
            "id": str(self._id),
            "worker_id": self._worker_id,
            "lon": self._lon,
            "lat": self._lat,
            "sgnl": self._sgnl,
        }
        if self._audio_data is not None:
            data["audio_sampling_rate"] = self._sampling_rate
            data["audio_data"] = self._audio_data.tolist()  # Assuming audio data is a numpy array
        if self._array_data is not None:
            data["array_data"] = self._array_data.tolist()  # Assuming array data is a numpy array
        if self._frequency_features is not None:
            data["frequency_features"] = self._frequency_features
        return data

    def set_audio_data(self, audio_data):
        self._audio_data = Signal(self._sampling_rate, audio_data)
        signal = Signal(self._sampling_rate, self._audio_data)
        self._frequency_features = self.compute_audio_frequency_features(signal._data, signal._sr)

    def get_audio_data(self):
        return self._audio_data

    def set_array_data(self, array_data):
        """Set the array data."""
        self._array_data = array_data

    def get_array_data(self):
        """Get the array data."""
        return self._array_data

    def get_sampling_rate(self):
        """Get the sampling rate."""
        return self._sampling_rate

    def get_frequency_features(self):
        """Get the computed frequency features."""
        return self._frequency_features

    def compute_audio_frequency_features(self, audio_data, sampling_rate):
        """Compute frequency features for the given audio data."""
        return self.extract_audio_features(audio_data, sampling_rate)

    def compute_array_features(self, array_data):
        """Compute fft features for the given audio data."""
        return self.compute_fft_features((self.normalize_signal(s) for s in array_data))

    @staticmethod
    def extract_audio_features(audio_data, sampling_rate):
        if len(audio_data) < 2:
            return {}

        zcr = float(np.mean(librosa.feature.zero_crossing_rate(audio_data)))
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=sampling_rate)))
        bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=audio_data, sr=sampling_rate)))
        flatness = float(np.mean(librosa.feature.spectral_flatness(y=audio_data)))
        contrast = float(np.mean(librosa.feature.spectral_contrast(y=audio_data, sr=sampling_rate)))
        rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=audio_data, sr=sampling_rate)))
        tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sampling_rate)
        mfccs = librosa.feature.mfcc(y=audio_data, sr=sampling_rate, n_mfcc=13).mean(axis=1).tolist()
        chroma = float(np.mean(librosa.feature.chroma_stft(y=audio_data, sr=sampling_rate)))

        return {
            "zero_crossing_rate": zcr,
            "spectral_centroid": centroid,
            "spectral_bandwidth": bandwidth,
            "spectral_flatness": flatness,
            "spectral_contrast": contrast,
            "spectral_rolloff": rolloff,
            "tempo": float(tempo),
            "mfcc": mfccs,
            "chroma": chroma
        }
