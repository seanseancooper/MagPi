from datetime import datetime, timedelta
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
    def __init__(self, worker_id, lon, lat, sgnl, array_data=None, audio_data=None, sr=48000):
        super().__init__(lon, lat, sgnl)
        self._worker_id = worker_id
        self._signal_type = None                # 'array' | 'audio' | 'both' ??

        self._audio_data = audio_data
        self._sr = sr
        self._array_data = array_data

        self._audio_frequency_features = None
        self._array_frequency_features = None

        self.updated = datetime.now()           # when signal was last reported
        self.elapsed = timedelta()              # time signal has been tracked.
        self.tracked = False
        self.is_mute = False

        self._ctrl_record = False
        self._ctrl_analyze = False
        self._ctrl_demux = False
        self._ctrl_decode = False
        self._ctrl_filter = False
        self._ctrl_block = False
        self._ctrl_label = False
        self._ctrl_test = False
        self._control_fields = [f for f in dir(self) if f.startswith("_ctrl_")]

        self._text_attributes = {}

        if audio_data is not None and sr is not None:
            self._audio_frequency_features = self.compute_audio_frequency_features(audio_data, sr)

        if array_data is not None:
            self._array_frequency_features = self.compute_array_frequency_features(array_data)

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
            data["sr"] = self._sr
            data["audio_data"] = self._audio_data.tolist()  # Assuming audio data is a numpy array
        if self._array_data is not None:
            data["array_data"] = self._array_data.tolist()  # Assuming array data is a numpy array
        if self._audio_frequency_features is not None:
            data["frequency_features"] = self._audio_frequency_features
        return data

    def get_signal_type(self):
        return self._signal_type

    def set_signal_type(self, signal_type):
        self._signal_type = signal_type

    def set_audio_data(self, audio_data):
        self._audio_data = audio_data
        signal = Signal(audio_data, self._id, sr=self._sr)
        self._audio_frequency_features = self.compute_audio_frequency_features(signal.get_data(), signal.get_sr())

    def get_audio_data(self):
        return self._audio_data

    def set_array_data(self, array_data):
        """Set the array data."""
        self._array_data = array_data

    def get_array_data(self):
        """Get the array data."""
        return self._array_data

    def set_attributes(self, attributes):
        if attributes is not None:
            def aggregate(k, v):
                self._text_attributes[k] = v
            [aggregate(k, str(v)) for k, v in attributes.items()]

    def set_attribute(self, attr_key, attr_value):
        self._text_attributes[attr_key] = attr_value

    def get_attribute(self, attr_key):
        return self._text_attributes[attr_key]

    def set_control_field(self, attr_field, attr_field_value):
        if attr_field in self._control_fields:
            self.__setattr__(attr_field, attr_field_value)

    def get_control_field(self, attr_field):
        if attr_field in self._control_fields:
            return self.__getattribute__(attr_field)

    def get_sampling_rate(self):
        """Get the sampling rate."""
        return self._sr

    def get_audio_frequency_features(self):
        """Get the audio frequency features."""
        return self._audio_frequency_features

    def get_array_frequency_features(self):
        """Get the array frequency features."""
        return self._array_frequency_features

    def compute_audio_frequency_features(self, audio_data, sampling_rate):
        """Compute frequency features for the given audio data."""
        return self.extract_audio_features(audio_data, sampling_rate)

    def compute_array_frequency_features(self, array_data):
        """Compute fft features for the given audio data."""
        return self.compute_fft_frequency_features([self.normalize_signal(s) for s in array_data])

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

    @staticmethod
    def compute_fft_frequency_features(norm_array_data, sampling_rate=1):

        # Since sgnl is a single value at a point in time, we need to collect multiple signals over
        # a time window (e.g., the last 100 signal points) and analyze their frequency spectrum.
        # Fast Fourier Transform (FFT)
        #
        # FFT converts a time-series signal into a set of frequency components.
        #  We use it to extract dominant frequencies, spectral power, and energy concentration.

        """
        Compute FFT features from a list of signal values.
        :param norm_array_data: Normalized list of past signal strengths.
        :param sampling_rate: Number of samples per second (adjust as needed).
        :return: Dictionary of frequency domain features.
        """
        from scipy.fftpack import fft

        N = len(norm_array_data)
        fft_vals = np.abs(fft(norm_array_data))[:N // 2]  # One-sided FFT
        freqs = np.fft.fftfreq(N, d=1 / sampling_rate)[:N // 2]  # Corresponding frequencies

        # Extract dominant frequency and spectral features
        dominant_freq = freqs[np.argmax(fft_vals)]
        spectral_entropy = -np.sum((fft_vals / np.sum(fft_vals)) * np.log2(fft_vals / np.sum(fft_vals)))

        return {
            "dominant_freq": dominant_freq,
            "spectral_entropy": spectral_entropy,
            "fft_magnitude": fft_vals.tolist()
        }
