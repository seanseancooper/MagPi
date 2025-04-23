from src.lib.utils import format_time
from src.lib.SignalPoint import SignalPoint


class WifiSignalPoint(SignalPoint):
    """
    Class to encapsulate a Wifi signal captured at a point.
    The 'id' field uniquely represents a specific point and is filled in the super when created.
    The 'worker_id' is derived from the BSSID of the AP that produced the signal.
    The 'bssid' is the BSSID of the AP that produced the signal.
    """
    def __init__(self, worker_id, lon, lat, sgnl, bssid=None):
        super().__init__(lon, lat, sgnl)
        self._bssid = bssid
        self._worker_id = worker_id
        self._signal_type = 'continuous' # Emission type (radar, voice, 'data')

    def set_bssid(self, bssid):
        self._bssid = bssid

    def get(self):
        return {
            "created"           : format_time(self._created, "%Y-%m-%d %H:%M:%S"),
            "id"                : str(self._id),
            "worker_id"         : self._worker_id,
            "bssid"             : self._bssid,
            "lon"               : self._lon,
            "lat"               : self._lat,
            "sgnl"              : self._sgnl,
            "signal_type"       : self._signal_type
        }
