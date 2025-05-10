import numpy as np

from src.lib.utils import format_time
from src.lib.SignalPoint import SignalPoint


class ARXSignalPoint(SignalPoint):
    """
    Class to encapsulate ARXRecorder recordings. This class holds a single audio data
    recording as a Signal() with a default sampling rate of 48Khz.
    """
    def __init__(self, worker_id, lon, lat, sgnl):
        super().__init__(lon, lat, sgnl)
        self._worker_id = worker_id
        self._signal_type = 'continuous'                    # Emission type (radar, voice, data)
        
        self._audio_data = None                             # potentially an array, a Signal() or LIST of type
        self._sr = None
        self._audio_frequency_features = None               # a mapping of features, or LIST of mappings

        self._text_attributes = {}
        self._text_attributes.update({
            # map of signal attributes (Who, What, When, Where, How, Why).
            # defaults:
            "source"            : None,                     # who: source component, plugin or process
            "signal_type"       : None,                     # who: ???
            "name"              : None,                     # what: a human readable identifier
            "id"                : str(self._id),            # when: derived from creator SignalPoint type.
            "fs_path"           : None,                     # where: could be on filesystem
            "channels"          : None,                     # how: documentation of created value.
            "shape"             : None,                     # how: documentation of created value.
            "sr"                : self._sr,                 # how: documentation of created value.
            "tags"              : [None]                    # why: a list of ad hoc tags for this Signal
        })

    def get_worker_id(self):
        return self._worker_id

    def get_signal_type(self):
        return self._signal_type

    def get_text_attributes(self):
        return self._text_attributes

    def get_text_attribute(self, a):
        return self._text_attributes[a]

    def set_text_attribute(self, a, v):
        self._text_attributes[a] = v
        
    def set_text_attributes(self, text_data):
        def aggregate(k, v):
            self._text_attributes[k] = v
        [aggregate(k, str(v)) for k, v in text_data.items()]

    def get_signal_type(self):
        return self._signal_type

    def set_sampling_rate(self, sr):
        self._sr = sr

    def get_sampling_rate(self):
        return self._sr

    def get_audio_data(self):
        return self._audio_data

    def get_frequency_features(self):
        return self._audio_frequency_features

    def set_audio_data(self, audio_data):

        self._audio_data = audio_data

    def get(self):
        """ return arxs *as is*. It may or may not have computed
        frequency_features dependent on having audio_data """
        return {
            "created"           : format_time(self.get_created(), "%Y-%m-%d %H:%M:%S.%f"),
            "id"                : str(self.get_id()),
            "worker_id"         : self.get_worker_id(),
            "signal_type"       : self.get_signal_type(),
            "lon"               : self.get_lon_lat()[0],
            "lat"               : self.get_lon_lat()[1],
            "sr"                : self.get_sampling_rate(),
            "text_attributes"   : self.get_text_attributes(),
        }
