from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np
import librosa
from librosa import feature

from src.arx.lib.ARXSignalPoint import ARXSignalPoint
from src.lib.Signal import Signal
from src.lib.SignalPoint import SignalPoint
from src.lib.utils import format_time

from scipy.fftpack import fft
from python_speech_features import mfcc

class TRXSignalPoint(SignalPoint):
    """
    Class to handle intermittent or continuous radio frequency signals.
    This class encapsulates audio data for analysis and can switch between intermittent and continuous signal processing.
    """

    def __init__(self, worker_id, lon, lat, sgnl, attributes, signal_data=None, audio_data=None, signal_type="discrete", sr=44100):
        super().__init__(lon, lat, sgnl)
        self._worker_id = worker_id
        self._signal_type = signal_type         # continuous || intermittent

        self.updated = datetime.now()           # when signal was last reported
        self.elapsed = timedelta()              # time signal has been tracked.
        self.tracked = False
        self.is_mute = False

        self._signal_data = signal_data         # Raw signal data (from SDR)?
        self._audio_data = audio_data           # Raw audio data
        self._sampling_rate = sr                # need a default, a config, and ability to ad hoc change
        self._text_data = defaultdict(dict)     # see aggregate

        self._frequency_features = None

        #   ALPHATAG: name of system broadcasting
        #   COMP_DATE: ??
        #   COMP_TIME: ??
        #   FREQ1: responding frequency?
        #   FREQ2: initial freq?
        # INFO
        #   OBJECT_ID: system object broadcasting
        # OTHER_TEXT
        #   RID1
        #   RID2
        #   SCAN_DATE: replaced date
        #   SCAN_TIME: replaced time
        #   SITE: broadcast site
        # SQ_MODE
        # SQ_VALUE
        #   SYSTEM: Broadcaster
        #   TGID1
        #   TGID2
        #   TSYS_ID
        #   TSYS_TYPE: broadcast system TYPE
        #   TYPE: broadcast type

        def aggregate(k,v):
            self._text_data[k] = v

        [aggregate(k, str(v)) for k, v in attributes.items()]

        # If the signal is discrete, set sr and process as intermittent
        if self._signal_type == "discrete" and self._text_data is not None:
            self._frequency_features = self.extract_signal_strength_features(self._text_data)
        elif self._signal_type == "continuous" and audio_data is not None:
            # If continuous, set sr and use audio data and compute frequency features
            arx = ARXSignalPoint(self._worker_id, self._lon, self._lat, self._sgnl, self._audio_data)
            self._frequency_features = self.extract_audio_features(arx.get_audio_data(), arx.get_sampling_rate())

    def get_audio_data(self):
        """
        Accessor method for raw audio data.
        """
        return self._audio_data

    def set_audio_data(self, audio_data):
        """
        Mutator method for raw audio data.
        """
        self._audio_data = Signal(self._sampling_rate, audio_data)
        self._frequency_features = self.extract_audio_features(audio_data, self._sampling_rate)

    def update(self, tracked):
        self.updated = datetime.now()
        self.elapsed = self.updated - self._created
        self.tracked = tracked

    def get(self):
        """
        Return a dictionary of the TRX signal data, including frequency features, active intervals, and audio analysis.
        """
        return {
            "created"           : format_time(self._created, "%Y-%m-%d %H:%M:%S.%f"),
            "lon"               : self._lon,
            "lat"               : self._lat,
            "sgnl"              : self._sgnl,
            "signal_type"       : self._signal_type,
            "signal_data"       : self._signal_data,
            "audio_data"        : self._audio_data.tolist() if self._audio_data is not None else None,
            "text_data"         : self._text_data,
            "frequency_features": self._frequency_features,

        }


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

        # AUDIO FREQUENCY FEATURES:
        # // ENOB: Effective number of bits

        # DB (_sgnl): decibels
        # SNR: Signal-to-noise ratio
        # THD: Total harmonic distortion
        # THD + N: Total harmonic distortion plus noise

        # SFDR: Spurious free dynamic range
        # SINAD: Signal-to-noise-and-distortion ratio


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
    def extract_signal_strength_features(past_signals, sampling_rate=1):
        MIN_LEN = 50

        if len(past_signals) < 2:
            return {"dominant_freq": None, "spectral_entropy": None, "fft_magnitude": [0.0]*MIN_LEN, "mfcc": [0.0]*13}

        signal_values = np.array(past_signals)
        N = len(signal_values)

        if N < MIN_LEN:
            signal_values = np.pad(signal_values, (0, MIN_LEN - N), 'constant')
            N = MIN_LEN

        fft_vals_full = np.abs(fft(signal_values))
        fft_vals = fft_vals_full[:N // 2]

        fft_vals_50 = np.zeros(MIN_LEN)
        fft_clip = fft_vals[:MIN_LEN] if len(fft_vals) >= MIN_LEN else fft_vals
        fft_vals_50[:len(fft_clip)] = fft_clip

        freqs = np.fft.fftfreq(N, d=1 / sampling_rate)[:N // 2]
        dominant_freq = freqs[np.argmax(fft_vals)]
        normalized_fft = fft_vals / np.sum(fft_vals) if np.sum(fft_vals) > 0 else np.ones_like(fft_vals) / len(fft_vals)
        spectral_entropy = -np.sum(normalized_fft * np.log2(normalized_fft + 1e-12))

        try:
            mfcc_features = mfcc(signal_values.reshape(-1, 1), samplerate=sampling_rate, numcep=13)
            mfcc_mean = mfcc_features.mean(axis=0).tolist()
        except Exception:
            mfcc_mean = [0.0] * 13

        # AUDIO FREQUENCY FEATURES:
        # // ENOB: Effective number of bits

        # DB (_sgnl): decibels
        # SNR: Signal-to-noise ratio
        # THD: Total harmonic distortion
        # THD + N: Total harmonic distortion plus noise

        # SFDR: Spurious free dynamic range
        # SINAD: Signal-to-noise-and-distortion ratio


        return {
            "dominant_freq": float(dominant_freq),
            "spectral_entropy": float(spectral_entropy),
            "fft_magnitude": fft_vals_50.tolist(),
            "mfcc": mfcc_mean
        }
