import uuid
from datetime import datetime


class SignalPoint:
    """ discrete class to encapsulate a signal captured at a point.
        A list of this type ae assumed to be arributed to a specific bssid.
        The id field is to provide a unique representation of
        the point to the map.
     """

    def __init__(self, bssid, lon, lat, sgnl):
        self._dt = datetime.now()
        self._bssid = bssid
        self._id = uuid.uuid4()
        self._lon = lon
        self._lat = lat
        self._sgnl = sgnl
        # TODO: MFCC here.

    def getLatLon(self):
        return self._lat, self._lon

    def getSgnl(self):
        return self._sgnl

    def get(self):
        return self.__str__()

    def __str__(self):
        return {
            "datetime": str(self._dt),
            "id": str(self._id),
            "lon": self._lon,
            "lat": self._lat,
            "sgnl": self._sgnl
        }
