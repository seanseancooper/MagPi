from datetime import datetime


class Signal:
    """
    Generic class to encapsulate a signal and  ad hoc map of attributes
    """
    def __init__(self, data, s_id, sr=1):
        self._created = datetime.now()  # when signal was created (differs from SignalPoint.created)
        self._id = s_id                 # id of associated SignalPoint object
        self.__sr = sr                  # sampling rate of signal (immutable, see 'attributes')
        self.__data = data              # [ndarray: container] data of T (immutable)

        self.attributes = {}            # ad hoc map of signal attributes

        self.attributes.update({

            # map of signal attributes (Who, What, When, Where, How, Why).
            # defaults:

            "source": None,             # who: source component, plugin or process
            "signal_type": None,        # who: ???

            "name": None,               # what: a human readable identifier
            "d_type": type(self.__data),# what: 32bit, 64bit, complex, list?

            "id": self._id,             # when: derived from creator SignalPoint type.

            "fs_path": None,            # where: could be on filesystem

            "channels": None,           # how: documentation of created value.
            "sr": self.__sr,            # how: documentation of created value.

            "tags": [None]              # why: a list of ad hoc tags for this Signal
        })

    def get_id(self):
        return self._id

    def get_sr(self):
        return self.__sr

    def get_data(self):
        return self.__data

    def get_attributes(self):
        return self.attributes

    def get_attribute(self, a):
        return self.attributes[a]

    def set_attribute(self, a, v):
        self.attributes[a] = v
