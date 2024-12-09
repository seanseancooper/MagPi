import math
import threading
from datetime import datetime, timedelta

from scipy.optimize import minimize

from src.lib.utils import format_time, format_delta
from src.config import readConfig

# start w/this & app context... use MAPAggregator
from src.wifi import WifiScanner
from src.wifi.lib import WifiSignalPoint
from src.trx.lib import TRXSignalPoint


from src.gps.GPSRetriever import GPSRetriever

class Trilaterator(threading.Thread):
    # based on
    # www.alanzucconi.com/2017/03/13/understanding-geographical-coordinates/
    # https://www.kaggle.com/code/johnbacksund/rssi-trilateration-of-ap-location

    def __init__(self, target: str):
        super().__init__()

        self.config = {}

        self.created = datetime.now()   # when signal was found
        self.updated = datetime.now()   # when signal was last reported
        self.elapsed = timedelta()      # time signal has been tracked.

        self.initial_location = []      # from current GPS or injected
        self.locations = []             #
        self.distances = []

        self.target = target
        self.retriever = GPSRetriever()  # no, use the context GPSRetriever...
        self.scanner = None  # no, use the context WifiScanner...

    def __str__(self):
        return {
            "created"       : format_time(self.created, self.config.get('TIMER_FORMAT', "%H:%M:%S")),
            "updated"       : format_time(self.updated, self.config.get('TIMER_FORMAT', "%H:%M:%S")),
            "elapsed"       : format_delta(self.elapsed, self.config.get('TIMER_FORMAT', "%H:%M:%S")),
        }

    def configure(self, config_file):
        readConfig(config_file, self.config)
        self.retriever.configure(config_file)

    @staticmethod
    def geographical_distance(latitudeA, longitudeA, latitudeB, longitudeB):
        # Degrees to radians
        delta_latitude = math.radians(latitudeB - latitudeA)
        delta_longitude = math.radians(longitudeB - longitudeA)
        mean_latitude = math.radians((latitudeA + latitudeB) / 2.0)

        R = 6371.009  # Km

        # Spherical Earth projected to a plane
        return R * math.sqrt(math.pow(delta_latitude, 2) + math.pow(math.cos(mean_latitude) * delta_longitude, 2))

    @staticmethod
    def great_circle_distance(latitudeA, longitudeA, latitudeB, longitudeB):

        # Degrees to radians
        phi1 = math.radians(latitudeA)
        lambda1 = math.radians(longitudeA)

        phi2 = math.radians(latitudeB)
        lambda2 = math.radians(longitudeB)

        delta_lambda = math.fabs(lambda2 - lambda1)

        central_angle = math.atan2(
                            math.sqrt(
                                math.pow(math.cos(phi2) *
                                math.sin(delta_lambda), 2.0) +
                                math.pow(math.cos(phi1) *
                                         math.sin(phi2) - math.sin(phi1) *
                                         math.cos(phi2) *
                                         math.cos(delta_lambda), 2.0)
                            ), (
                                math.sin(phi1) * math.sin(phi2) +
                                math.cos(phi1) * math.cos(phi2) * math.cos(delta_lambda)
                            )
                        )

        R = 6371.009  # Km
        return R * central_angle

    def get_initial_location(self):
        # get from app.GPSRetriever..
        # {'GPS': {'LATITUDE': 39.916891, 'LONGITUDE': -105.06867, 'UPDATED': '2024-10-25 17:55:48'}}.
        lat = -105.06867
        lon = 39.916891
        self.initial_location = (lat, lon)

    def getSignalPointsForBSSID(self, BSSID, scanner: WifiScanner):
        # WifiSignalPoint
        return scanner.signal_cache.get(BSSID)

    def getSignalPointsForUniqId(self, UniqId, scanner):
        # TRXSignalPoint, et, al.
        return scanner.signal_cache.get(UniqId)

    def getLocationsForsSignalPoints(self, SignalPoints: list):
        return [pt.getLatLon() for pt in SignalPoints]

    def getDistancesForSignalPoints(self, initial_location, SignalPointList):
        # list of distances per SignalPoint to initial_location
        pt_locs = [sp.getLatLon() for sp in SignalPointList]
        return [self.get_LatLonDistance(initial_location, pt) for pt in pt_locs]

    def get_LatLonDistance(self, LatLon1, LatLon2):
        [lat1, lon1] = LatLon1
        [lat2, lon2] = LatLon2
        return self.geographical_distance(lat1, lon1, lat2, lon2)

    def getSignalPointDistance(self, s1: WifiSignalPoint, s2: WifiSignalPoint):
        # I think this should work for both, but do we really want a superclass 'SignalPoint'?
        [lat1, lon1] = s1.getLatLon()
        [lat2, lon2] = s2.getLatLon()
        return self.geographical_distance(lat1, lon1, lat2, lon2)

    def mse(self, x, locations, distances):
        # x: (lat, lon) tuple, list
        # locations: [ (lat1, long1), ... ]
        # distances: [ distance1, ... ]
        mse = 0.0
        for location, distance in zip(locations, distances):
            distance_calculated = self.great_circle_distance(x[0], x[1], location[0], location[1])
            mse += math.pow(distance_calculated - distance, 2.0)
        return mse / len(distances)

    def trilaterate(self, initial_location, locations, distances):

        # initial_location: (lat, lon)         <-- the current location
        # locations: [ (lat1, long1), ... ]     <-- list of SignalPoints
        # distances: [ distance1,     ... ]     <-- list of distances per SignalPoint to initial_location
        result = minimize(
                self.mse,                                   # The error function reference
                initial_location,                           # The initial guess
                args=(locations, distances),                # Additional parameters for mse
                method='L-BFGS-B',                          # The optimisation algorithm
                options={
                    'ftol'   : 1e-5,                        # Tolerance
                    'maxiter': 1e+7                         # Maximum iterations
                })
        location = result.x

        return location

    def run(self) -> None:
        t = Trilaterator('BSSID_TARGeT')

        t.get_initial_location()
        t.locations = []  # get the list of sp for BSSID_TARGeT
        t.distances = []  # getDistancesForSignalPoints

        print(f'result: {t.trilaterate(t.initial_location, t.locations, t.distances)}')