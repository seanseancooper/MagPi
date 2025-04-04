import numpy as np
from src.lib.utils import format_time
from src.lib.SignalPoint import SignalPoint
from python_speech_features import mfcc


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
            self._frequency_features = self.compute_audio_frequency_features(audio_data, self._sampling_rate)

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
        self._frequency_features = self.compute_audio_frequency_features(audio_data, self._sampling_rate)

    def compute_audio_frequency_features(self, audio_data, sampling_rate):
        """
        Compute continuous audio-specific frequency features (e.g., MFCC) from raw audio data.
        """
        mfcc_features = mfcc(audio_data, samplerate=sampling_rate, numcep=13)

        # Add these frequency features for continuous audio:
        # Spectral Flatness
        # Spectral Contrast
        # chromanance
        # tempo
        # rhythm
        # zero-crossings
        # chromagram = librosa.feature.chroma_stft(y=x, sr=sr, hop_length=hop_length)

        # oenv = librosa.onset.onset_strength(y=x, sr=sr, hop_length=hop_length)
        # times = librosa.times_like(oenv, sr=sr, hop_length=hop_length)
        # tempogram = librosa.feature.tempogram(onset_envelope=oenv, sr=sr,
        #                                       hop_length=hop_length)# Estimate the global tempo for display purposes
        # tempo = librosa.feature.rhythm.tempo(onset_envelope=oenv, sr=sr, hop_length=hop_length)[0]

        # rhythm,
        # zero crossings.

        audio_features = {
            "mfcc"            : mfcc_features.mean(axis=0).tolist(),
            "dominant_freq"   : float(np.argmax(np.abs(np.fft.fft(audio_data)))),
            "spectral_entropy": float(
                -np.sum((np.abs(np.fft.fft(audio_data)) / np.sum(np.abs(np.fft.fft(audio_data)))) *
                        np.log2(np.abs(np.fft.fft(audio_data)) / np.sum(np.abs(np.fft.fft(audio_data))))))
        }
        return audio_features

    def get(self):
        """
        Return a dictionary of the ARX signal data, including frequency features and audio analysis.
        """
        return {
            "created"           : format_time(self._created, "%Y-%m-%d %H:%M:%S.%f"),
            "lon"               : self._lon,
            "lat"               : self._lat,
            "sgnl"              : self._sgnl,
            "audio_data"        : self._audio_data.tolist() if self._audio_data is not None else None,
            "frequency_features": self._frequency_features
        }


