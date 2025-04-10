import uuid
from datetime import datetime
import hashlib
import geohash


class SignalPoint(object):
    """
    Base class to handle spatio-temporal properties and frequency feature extraction of a Signal.
    """
    def __init__(self, lon, lat, sgnl):
        self._created = datetime.now()
        self._id = uuid.uuid4()
        self._lon = lon
        self._lat = lat
        self._sgnl = sgnl               # a discrete value

    def getId(self):
        return self._id

    def getLatLon(self):
        return self._lat, self._lon

    def getSgnl(self):
        return self._sgnl

    def generate_signal_hash(self, worker_id):
        data = f"{worker_id}-{self._lon}-{self._lat}-{self._sgnl}".encode()
        return hashlib.sha256(data).hexdigest()

    def get_geohash(self, precision=7):
        return geohash.encode(self._lat, self._lon, precision=precision)

    def normalize_signal(self, sgnl):
        return [(sgnl + 100) / 100.0]  # Normalizing from [-100, 0] → [0, 1]
