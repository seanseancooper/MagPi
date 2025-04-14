from src.lib.utils import format_time
from src.lib.SignalPoint import SignalPoint


class WifiSignalPoint(SignalPoint):
    """
    Class to encapsulate a Wifi signal captured at a point.
    The 'id' field uniquely represents a specific point.
    The 'worker_id' is derived from the BSSID of the AP that produced it.
    """
    def __init__(self, worker_id, bssid, lon, lat, sgnl):
        super().__init__(lon, lat, sgnl)
        self._bssid = bssid
        self._worker_id = worker_id
        self._signal_type = 'continuous'

    def get(self):
        return {
            "created"           : format_time(self._created, "%Y-%m-%d %H:%M:%S.%f"),
            "id"                : str(self._id),
            "worker_id"         : self._worker_id,
            "bssid"             : self._bssid,
            "lon"               : self._lon,
            "lat"               : self._lat,
            "sgnl"              : self._sgnl
        }
