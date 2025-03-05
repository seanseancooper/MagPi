import uuid
from datetime import datetime
from src.lib.utils import format_time, format_delta

class WifiSignalPoint:
    """ discrete class to encapsulate a signal captured at a point.
        A list of this type are assumed to be attributed to a specific bssid.
        The id field serves to provide a unique representation of a specific
        point.
     """

    def __init__(self, bssid, lon, lat, sgnl):
        self._dt = datetime.now()
        self._bssid = bssid
        self._id = uuid.uuid4()
        self._lon = lon
        self._lat = lat
        self._sgnl = sgnl

    # def __repr__(self):
    #     return "<Point x:{0},y:{1}>".format(self.x, self.y)
    #
    # implement addition (Adding 'Points' isn't natively supported)
    # def __add__(self, other):
    #     return Point(self.x + other.x, self.y + other.y)
    #
    # implement subtraction (Subtracting 'Points' isn't natively supported)
    # def __sub__(self, other):
    #     return Point(self.x - other.x, self.y - other.y)
    #
    # implement in-place addition  (in-place adding 'Points' isn't natively supported)
    # def __iadd__(self, other):
    #     self.x += other.x
    #     self.y += other.y
    #     return self

    def getLatLon(self):
        return self._lat, self._lon

    def getSgnl(self):
        return self._sgnl

    def get(self):
        return {
            "datetime": format_time(self._dt, "%Y-%m-%d %H:%M:%S.%f"),
            "id": str(self._id),
            "lon": self._lon,
            "lat": self._lat,
            "sgnl": self._sgnl
        }
