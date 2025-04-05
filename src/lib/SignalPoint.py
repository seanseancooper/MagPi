import uuid
from datetime import datetime

class SignalPoint(object):
    """
    Base class to handle spatio-temporal properties and frequency feature extraction.
    """
    def __init__(self, lon, lat, sgnl):
        self._created = datetime.now()
        self._id = uuid.uuid4()
        self._lon = lon
        self._lat = lat
        self._sgnl = sgnl
        self._frequency_features = None

    def getId(self):
        return self._id

    def getLatLon(self):
        return self._lat, self._lon

    def getSgnl(self):
        return self._sgnl
