import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from src.lib.utils import format_time, format_delta


class TRXSignalPoint:
    """ discrete class to encapsulate a signal captured at a point.
        A list of this type are assumed to be attributed to a specific bssid.
        The id field serves to provide a unique representation of a specific
        point.
     """

    def __init__(self, lon, lat, attributes):
        self._dt = datetime.now()
        self._id = uuid.uuid4()
        self._lon = lon
        self._lat = lat

        self.created = datetime.now()   # when signal was found
        self.updated = datetime.now()   # when signal was last reported
        self.elapsed = timedelta()      # time signal has been tracked.

        self.tracked = False
        self.is_mute = False

        self.attributes = defaultdict(dict)
        #   ALPHATAG: name of system broadcasting
        #   COMP_DATE: ??
        #   COMP_TIME: ??
        #   FREQ1: responding frequency?
        #   FREQ2: initial freq?
        # INFO
        #   OBJECT_ID: system object broadcasting
        # OTHER_TEXT
        #   RID1
        #   RID2
        #   SCAN_DATE: replaced date
        #   SCAN_TIME: replaced time
        #   SITE: broadcast site
        # SQ_MODE
        # SQ_VALUE
        #   SYSTEM: Broadcaster
        #   TGID1
        #   TGID2
        #   TSYS_ID
        #   TSYS_TYPE: broadcast system TYPE
        #   TYPE: broadcast type

        def aggregate(k,v):
            self.attributes[k] = v
        [aggregate(k, str(v)) for k, v in attributes.items()]

    def getLatLon(self):
        return self._lat, self._lon

    def update(self, tracked):
        self.updated = datetime.now()
        self.elapsed = self.updated - self.created
        self.tracked = tracked

    def get(self):
        return {
            "datetime": str(self._dt),
            "id": str(self._id),
            "lon": self._lon,
            "lat": self._lat,
            "created": format_time(self.created, "%H:%M:%S"),
            "updated": format_time(self.updated, "%H:%M:%S"),
            "elapsed": format_delta(self.elapsed, "%H:%M:%S"),
            "is_mute": self.is_mute,
            "tracked": self.tracked,
            "attributes": self.attributes
        }
