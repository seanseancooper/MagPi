from collections import defaultdict
from datetime import datetime, timedelta

from src.lib.Signal import Signal
from src.lib.SignalPoint import SignalPoint
from src.arx.lib.ARXAudioEncoder import ARXEncoder  # remove this dependency; make TRXEncoder process data locally
from src.lib.utils import format_time

class TRXSignalPoint(SignalPoint):
    """
    Class to handle intermittent or continuous radio frequency signals.
    This class encapsulates audio data for analysis and can switch between intermittent and continuous signal processing.
    """

    def __init__(self, worker_id, lon, lat, sgnl, attributes, signal_data=None, audio_data=None, signal_type="intermittent", sr=44100):
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
        if self._signal_type == "discrete" and signal_data is not None:
            arx = ARXEncoder(signal_data, self._sampling_rate)
            past_signals = []   #  wrong: this is for an array of signal strengths!
            self._frequency_features = arx.compute_frequency_features(past_signals)
        elif self._signal_type == "continuous" and audio_data is not None:
            # If continuous, set sr and use audio data and compute frequency features (similar to ARXSignalPoint)
            arx = ARXEncoder(audio_data, self._sampling_rate)
            self._frequency_features = arx.compute_audio_frequency_features()

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
        arx = ARXEncoder(self._audio_data, self._sampling_rate)
        self._frequency_features = arx.compute_audio_frequency_features()

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
