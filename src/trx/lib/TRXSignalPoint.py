from datetime import datetime, timedelta
import numpy as np
import librosa
from librosa import feature

from src.lib.Signal import Signal
from src.lib.SignalPoint import SignalPoint
from src.lib.utils import format_time


class TRXSignalPoint(SignalPoint):
    """
    Class to handle intermittent or continuous radio frequency signals.
    This class encapsulates text_data from hardware as attributes.
    This class encapsulates audio_data as a Signal with a default sampling rate of 48Khz.
    Extracts frequency features locally; there would be special processing for audio data of this type.
    """
    def __init__(self, worker_id, lon, lat, sgnl, text_data, audio_data=None, signal_type="object", sr=48000):
        super().__init__(lon, lat, sgnl)
        self._worker_id = worker_id
        self._signal_type = signal_type         # object || continuous

        self.updated = datetime.now()           # when signal was last reported
        self.elapsed = timedelta()              # time signal has been tracked.
        self.tracked = False
        self.is_mute = False

        self._text_attributes = {}              # object (default): intermittent text from hardware, see aggregate(k, v)
        self._audio_data = audio_data           # continuous: intermittent audio data as a Signal
        self._sr = sr                           # need config, and ability to ad hoc change

        self._audio_frequency_features = None

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
                self._text_attributes[k] = v
            [aggregate(k, str(v)) for k, v in text_data.items()]

        if self._signal_type == "object" and self._audio_data is None:
            self._sgnl = 0.0
        if self._signal_type == "object" and self._audio_data is not None:
            self._sgnl = 0.0 # set to peak db in audio
        elif self._signal_type == "continuous" and self._audio_data is not None:
            # set sr, make Signal. use audio data and extract_audio_features
            # Note may not have audio yet; was there some 'directive' to 'record'?.
            signal = Signal(audio_data, self._id, sr=self._sr)
            self._audio_frequency_features = self.extract_audio_frequency_features(signal.get_data(), signal.get_sr())

    def get_audio_data(self):
        return self._audio_data

    def set_audio_data(self, audio_data):
        self._audio_data = Signal(audio_data, self._id, sr=self._sr)
        self._audio_frequency_features = self.extract_audio_frequency_features(audio_data, self._sr)

    def set_sampling_rate(self, sr):
        self._sr = sr

    def get_sampling_rate(self):
        return self._sr

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

            # "signal_data"       : [_ for _ in self._signal_data] if self._signal_data is not None else None,
            "audio_data"        : self._audio_data.tolist() if self._audio_data is not None else None,
            "text_data"         : {k: v for k, v in self._text_attributes.items()},
            "sr"                : self.get_sampling_rate(),

            "frequency_features": self._audio_frequency_features,
        }

    @staticmethod
    def extract_audio_frequency_features(audio_data, sampling_rate):
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

