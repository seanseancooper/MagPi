import numpy as np

from src.lib.utils import format_time
from src.lib.SignalPoint import SignalPoint
from src.lib.Signal import Signal
from src.arx.lib.ARXEncoder import ARXEncoder
from src.arx.lib.ARXMQConsumer import ARXMQConsumer

class ARXSignalPoint(SignalPoint):
    """
    Class to encapsulate ARXRecorder recordings. This class holds a single audio data
    recording as a Signal() with a default sampling rate of 48Khz.

    The clas computes frequency features using ARXEncoder.
    """
    def __init__(self, worker_id, lon, lat, sgnl, audio_data=None, sr=48000):
        super().__init__(lon, lat, sgnl)
        self._worker_id = worker_id or 'ARXRecorder'
        self._signal_type = 'continuous'
        
        self._audio_data = audio_data                   # potentially an array, a Signal() or LIST of type
        self._sr = sr
        self._audio_frequency_features = None                 # a mapping of features, or LIST of mappings

        self._text_attributes = {}
        self._text_attributes.update({
            # map of signal attributes (Who, What, When, Where, How, Why).
            # defaults:
            "source"            : None,           # who: source component, plugin or process
            "signal_type"       : None,           # who: ???
            "name"              : None,           # what: a human readable identifier
            "d_type"            : type(self._audio_data),# what: 32bit, 64bit, complex, list?
            "id"                : self._id,       # when: derived from creator SignalPoint type.
            "fs_path"           : None,           # where: could be on filesystem
            "channels"          : None,           # how: documentation of created value.
            "shape"             : self._audio_data.shape(),           # how: documentation of created value.
            "sr"                : self._sr,       # how: documentation of created value.
            "tags"              : [None]          # why: a list of ad hoc tags for this Signal
        })

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

    def get_sampling_rate(self):
        return self._sr

    def get_audio_data(self):
        return self._audio_data

    def set_audio_data(self, audio_data):
        def process_features(_data):
            self._audio_data = Signal(_data, self._id, sr=self._sr)
            yield self.compute_audio_frequency_features()

        if type(audio_data) is np.ndarray:
            process_features(audio_data)

        if type(audio_data) is list:
            self._audio_frequency_features = []
            [self._audio_frequency_features.append(process_features(_data)) for _data in audio_data]

    @staticmethod
    def arxs_to_dict(arxs):
        """ calculates on arxs """
        audio_data = arxs.get_audio_data()
        return  {
            "worker_id"                 : arxs.worker_id,
            "lon"                       : arxs.lon,
            "lat"                       : arxs.lat,
            "sgnl"                      : arxs.sgnl,
            "audio_data"                : audio_data,
            "sr"                        : arxs.get_sampling_rate(),
            "signal_type"               : arxs.get_signal_type(),
            "frequency_features"        : arxs.get_audio_frequency_features(),
            "text_attributes"           : arxs.get_text_attributes(),
        }

    def get(self):
        """ return arxs *as is* """
        return {
            "created"           : format_time(self._created, "%Y-%m-%d %H:%M:%S.%f"),
            "id"                : self._id,
            "worker_id"         : self._worker_id,
            "signal_type"       : self._signal_type,
            "lon"               : self._lon,
            "lat"               : self._lat,
            "audio_data"        : self._audio_data.tolist() if self._audio_data is not None else None,
            "sr"                : self._sr,
            "frequency_features": self._audio_frequency_features,
            "text_attributes"   : self._text_attributes
        }

    @staticmethod
    def dict_to_arxs(d):
        provider = ARXMQConsumer()
        _metadata = provider.zmq.get_metadata() # potentially array, a Signal() or LIST of type
        _audio_data = provider.zmq.get_data()   # potentially array, a Signal() or LIST of type

        sgnlpt  = ARXSignalPoint(d['worker_id'],
                                 d['lon'],
                                 d['lat'],
                                 d['sgnl'],
                                 audio_data=_audio_data,
                                 sr=d.sr)

        sgnlpt._worker_id = d.worker_id
        sgnlpt._signal_type = d['signal_type']
        sgnlpt._sampling_rate = d['sr']
        sgnlpt._audio_frequency_features = d['audio_frequency_features']  # a mapping of features, or LIST of mappings
        sgnlpt._text_attributes = {k: v for k, v in d['_text_attributes'].items()},

        return sgnlpt

    def compute_audio_frequency_features(self):
        # Compute frequency features for the audio data
        enc = ARXEncoder(self._audio_data, self._sr) # <-- now needs to  process multiple
        self._audio_frequency_features = enc.compute_audio_frequency_features()
        yield self._audio_frequency_features
