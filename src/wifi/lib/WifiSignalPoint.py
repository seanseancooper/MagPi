import uuid
from datetime import datetime
from src.lib.utils import format_time, format_delta


class WifiSignalPoint:
    """ discrete class to encapsulate a signal captured at a point.
        A list of this type are assumed to be attributed to a specific bssid.
        The 'id' field serves to provide a unique representation of a specific
        point. The 'worker_id' is derived from the BSSID of the AP that
        produced it.
     """

    def __init__(self, worker_id, bssid, lon, lat, sgnl):
        self._created = datetime.now()
        self._bssid = bssid
        self._worker_id = worker_id
        self._id = uuid.uuid4()
        self._lon = lon
        self._lat = lat
        self._sgnl = sgnl

    def getLatLon(self):
        return self._lat, self._lon

    def getSgnl(self):
        return self._sgnl

    def get(self):
        return {
            "created": format_time(self._created, "%Y-%m-%d %H:%M:%S.%f"),
            "id": str(self._id),
            "worker_id": self._worker_id,
            "lon": self._lon,
            "lat": self._lat,
            "sgnl": self._sgnl
        }
