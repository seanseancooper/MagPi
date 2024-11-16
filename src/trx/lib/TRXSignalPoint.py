import uuid
from collections import defaultdict
from datetime import datetime


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

        self.attributes = defaultdict(dict)
        #   ALPHATAG: name of system broadcasting
        # COMP_DATE: ??
        # COMP_TIME: ??
        #   FREQ1: responding frequency?
        #   FREQ2: initial freq?
        # INFO
        #   OBJECT_ID: system object broadcasting
        # OTHER_TEXT
        # RID1
        # RID2
        # SCAN_DATE: replaced date
        # SCAN_TIME: replaced time
        #   SITE: broadcast site
        # SQ_MODE
        # SQ_VALUE
        #   SYSTEM: Broadcaster
        # TGID1
        # TGID2
        # TSYS_ID
        # TSYS_TYPE: broadcast system TYPE
        # TYPE: broadcast type

        def aggregate(k,v):
            self.attributes[k] = v
        [aggregate(k, str(v)) for k, v in attributes.items()]


    def getLatLon(self):
        return self._lat, self._lon

    def get(self):
        config = {}

        for k, v in self.attributes.items():
            config[k] = v

        return {
            "datetime": str(self._dt),
            "id": str(self._id),
            "lon": self._lon,
            "lat": self._lat,
            "attributes": dict(config.items())
        }


    def __str__(self):
        return {
            "datetime": str(self._dt),
            "id": str(self._id),
            "lon": self._lon,
            "lat": self._lat,
        }
