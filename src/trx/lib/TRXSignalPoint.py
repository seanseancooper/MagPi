from datetime import datetime, timedelta
import numpy as np
import librosa
from librosa import feature

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
    def __init__(self, worker_id, lon, lat, sgnl, text_data, signal_data=None, audio_data=None, signal_type="object", sr=44100):
        super().__init__(lon, lat, sgnl)
        self._worker_id = worker_id
        self._signal_type = signal_type         # continuous || intermittent

        self.updated = datetime.now()           # when signal was last reported
        self.elapsed = timedelta()              # time signal has been tracked.
        self.tracked = False
        self.is_mute = False

        self.text_attributes = {}               # object (default): text from hardware, see aggregate(k, v)
        self._signal_data = signal_data         # discrete: signal data (vector)
        self._audio_data = audio_data           # continuous: audio data (numpy array)
        self._sr = sr                           # need config, and ability to ad hoc change

        self._frequency_features = None

        if text_data is not None:
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
            def aggregate(k, v):
                self.text_attributes[k] = v
            [aggregate(k, str(v)) for k, v in text_data.items()]

        elif self._signal_type == "discrete" and self._signal_data is not None:
            # an array of discrete floats or int; extract_signal_strength_features
            self._frequency_features = self.extract_signal_strength_features(self._signal_data)

        elif self._signal_type == "continuous" and self._audio_data is not None:
            # set sr, make Signal. use audio data and extract_audio_features
            signal = Signal(audio_data, self._id, sr=self._sr)
            self._frequency_features = self.extract_audio_features(signal.get_data(), signal.get_sr())

    def get_audio_data(self):
        """
        Accessor method for raw audio data.
        """
        return self._audio_data

    def set_audio_data(self, audio_data):
        """
        Mutator method for raw audio data.
        """
        self._audio_data = Signal(audio_data, self._id, sr=self._sr)
        self._frequency_features = self.extract_audio_features(audio_data, self._sr)

    def update(self, tracked):
        self.updated = datetime.now()
        self.elapsed = self.updated - self._created
        self.tracked = tracked

    def get(self):
        return {
            "created"           : format_time(self._created, "%Y-%m-%d %H:%M:%S.%f"),
            "id"                : str(self._id),
            "lon"               : self._lon,
            "lat"               : self._lat,
            "sgnl"              : self._sgnl,
            "updated"           : str(self.updated),
            "elapsed"           : str(self.elapsed),
            "is_mute"           : self.is_mute,
            "tracked"           : self.tracked,

            "signal_type"       : self._signal_type,

            "signal_data"       : [_ for _ in self._signal_data] if self._signal_data is not None else None,
            "audio_data"        : self._audio_data.tolist() if self._audio_data is not None else None,
            "text_data"         : {k: v for k, v in self.text_attributes.items()},

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
