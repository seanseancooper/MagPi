from collections import defaultdict
from datetime import datetime, timedelta
from src.lib.SignalPoint import SignalPoint
from src.lib.utils import format_time

# class TRXSignalPoint(SignalPoint):
#     """ discrete class to encapsulate a signal captured at a point.
#         A list of this type are assumed to be attributed to a specific bssid.
#         The id field serves to provide a unique representation of a specific
#         point.
#      """
#
#     def __init__(self, lon, lat, attributes):
#         self._dt = datetime.now()
#         self._id = uuid.uuid4()
#         self._lon = lon
#         self._lat = lat
#
#         self.created = datetime.now()   # when signal was found
#         self.updated = datetime.now()   # when signal was last reported
#         self.elapsed = timedelta()      # time signal has been tracked.
#
#         self.tracked = False
#         self.is_mute = False
#
#         self.attributes = defaultdict(dict)
#         #   ALPHATAG: name of system broadcasting
#         #   COMP_DATE: ??
#         #   COMP_TIME: ??
#         #   FREQ1: responding frequency?
#         #   FREQ2: initial freq?
#         # INFO
#         #   OBJECT_ID: system object broadcasting
#         # OTHER_TEXT
#         #   RID1
#         #   RID2
#         #   SCAN_DATE: replaced date
#         #   SCAN_TIME: replaced time
#         #   SITE: broadcast site
#         # SQ_MODE
#         # SQ_VALUE
#         #   SYSTEM: Broadcaster
#         #   TGID1
#         #   TGID2
#         #   TSYS_ID
#         #   TSYS_TYPE: broadcast system TYPE
#         #   TYPE: broadcast type
#
#         def aggregate(k,v):
#             self.attributes[k] = v
#         [aggregate(k, str(v)) for k, v in attributes.items()]
#
#     def getLatLon(self):
#         return self._lat, self._lon
#
#     def update(self, tracked):
#         self.updated = datetime.now()
#         self.elapsed = self.updated - self.created
#         self.tracked = tracked
#
#     def get(self):
#         return {
#             "datetime": str(self._dt),
#             "id": str(self._id),
#             "lon": self._lon,
#             "lat": self._lat,
#             "created": format_time(self.created, "%H:%M:%S"),
#             "updated": format_time(self.updated, "%H:%M:%S"),
#             "elapsed": format_delta(self.elapsed, "%H:%M:%S"),
#             "is_mute": self.is_mute,
#             "tracked": self.tracked,
#             "attributes": self.attributes
#         }

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
        self.attributes = defaultdict(dict)     # see aggregate
        self._signal_data = signal_data         # Raw signal data (could be radio data or audio data)
        self._audio_data = audio_data           # Raw audio data (if present)
        self._sr = sr
        self._frequency_features = None

        def aggregate(k,v):
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
            self.attributes[k] = v
        [aggregate(k, str(v)) for k, v in attributes.items()]

        # If the signal is intermittent, set sr and process as intermittent
        if self._signal_type == "intermittent" and signal_data is not None:
            from src.arx.lib.ARXAudioencoder import compute_frequency_features
            self._frequency_features = compute_frequency_features(signal_data, self._sr)
        # add  'interstitial' signals? hmmm....
        elif self._signal_type == "continuous" and audio_data is not None:
            # If continuous, set sr and use audio data and compute frequency features (similar to ARXSignalPoint)
            from src.arx.lib.ARXAudioencoder import compute_audio_frequency_features
            self._frequency_features = compute_audio_frequency_features(audio_data, self._sr)

    def set_audio_data(self, audio_data, sampling_rate):
        self._audio_data = audio_data  # Set audio data dynamically
        self._sr = sampling_rate  # Set the sampling rate dynamically

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
            "frequency_features": self._frequency_features,
            "audio_data"        : self._audio_data.tolist() if self._audio_data is not None else None
        }
