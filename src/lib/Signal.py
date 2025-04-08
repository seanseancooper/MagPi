import uuid
from collections import defaultdict
from datetime import datetime, timedelta


class Signal:
    """
    Generic class to encapsulate a signal and  ad hoc map of attributes
    """
    def __init__(self, sr, data):

        self._created = datetime.now()   # when signal was found
        self._id = uuid.uuid4()
        self._sr = sr                   # sampling rate of signal (see also 'attribute')
        self._data = data               # [ndarray: container] data of T (is immutable)

        self.attributes = defaultdict   # ad hoc map of signal attributes

        self.attributes.update({             # ad hoc map of signal attributes
            "source": None,             # these are some ideas for defaults
            "name": None,
            "fs_path": None,
            "id": self._id,
            "type": type(data),
            "channels": None,
            "sr": self._sr,
            "tag": None
        })

    def get_id(self):
        return self._id

    def get_sr(self):
        return self._sr

    def get_data(self):
        return self._data

    def get_attributes(self):
        return self.attributes

    def get_attribute(self, a):
        return self.attributes[a]

    def set_attribute(self, a, v):
        self.attributes[a] = v
