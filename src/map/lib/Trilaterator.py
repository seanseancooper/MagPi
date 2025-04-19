import math
import threading
from datetime import datetime, timedelta

import numpy as np
from scipy.optimize import minimize

from src.lib.utils import get_location, format_time, format_delta
from src.config import readConfig
import requests
import json

from src.lib import SignalPoint


class Trilaterator(threading.Thread):
    # based on
    # www.alanzucconi.com/2017/03/13/understanding-geographical-coordinates/
    # https://www.kaggle.com/code/johnbacksund/rssi-trilateration-of-ap-location

    def __init__(self):
        super().__init__()

        self.config = {}

        self.created = datetime.now()   # when signal was found
        self.updated = datetime.now()   # when signal was last reported
        self.elapsed = timedelta()      # time signal has been tracked.

        self.locations = []             #
        self.distances = []

        self.target = None              # id to trilaterate

        self.lat = 39.916895                    # uses the context GPSRetriever...
        self.lon = -105.068699                  # uses the context GPSRetriever...
        self.result = None

    def get(self):
        return {
            "created"       : format_time(self.created, self.config.get('TIMER_FORMAT', "%H:%M:%S")),
            "updated"       : format_time(self.updated, self.config.get('TIMER_FORMAT', "%H:%M:%S")),
            "elapsed"       : format_delta(self.elapsed, self.config.get('TIMER_FORMAT', "%H:%M:%S")),
        }

    def configure(self, config_file):
        readConfig(config_file, self.config)

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

    def set_target(self, target):
        self.target = target

    def getSignalPointsForBSSID(self, BSSID):
        # resp = requests.get(f'http://wifi.localhost:5006/scan/{BSSID}')
        # resp = requests.get(f'http://map.localhost:5006/data/wifi')
        # cache = json.dumps(resp)

        with open('/Users/scooper/PycharmProjects/MagPiDev/wifi/training_data/scanlists_out.json', 'r') as f:
            cache = json.load(f)
        signals = []

        for signal in cache:
            if BSSID.lower() == signal['BSSID'].lower():
                signals.append({signal['BSSID']: signal['signal_cache']})
        return BSSID, signals[0][BSSID]

    def getSignalPointsForUniqId(self, UniqId, scanner):
        # TRXSignalPoint, et, al.
        return scanner.signal_cache.get(UniqId)

    def getLocationsForSignalPoints(self, pts: list):
        return [[pt.get('lat'), pt.get('lon')] for pt in pts]

    def getDistancesForSignalPoints(self, initial_location, pts):
        # list of distances per SignalPoint to initial_location
        pt_locs = [[pt.get('lat'), pt.get('lon')] for pt in pts]
        return [self.get_LatLonDistance(initial_location, pt) for pt in pt_locs]

    def get_LatLonDistance(self, LatLon1, LatLon2):
        [lat1, lon1] = LatLon1
        [lat2, lon2] = LatLon2
        return self.geographical_distance(lat1, lon1, lat2, lon2)

    def getSignalPointDistance(self, s1: SignalPoint, s2: SignalPoint):
        [lat1, lon1] = s1.get_lat_lon()
        [lat2, lon2] = s2.get_lat_lon()
        return self.geographical_distance(lat1, lon1, lat2, lon2)

    def mse(self, x, locations, distances):
        # x: (lat, lon) tuple, list
        # locations: [ (lat1, long1), ... ]
        # distances: [ distance1, ... ]
        mse = 0.0
        for location, distance in zip(locations, distances):
            distance_calculated = self.great_circle_distance(x[0], x[1], location[0], location[1])
            mse += math.pow(distance_calculated - distance, 2.0)
            # mse += np.sum((distance_calculated - distance) ** 2)
        print(f"Evaluating at {x}: MSE={mse / len(distances)}")
        return mse / len(distances)

    def trilaterate(self, initial_location, locations, distances):

        # initial_location: (lat, lon)          <-- the current location
        # locations: [ (lat1, long1), ... ]     <-- list of SignalPoints
        # distances: [ distance1,     ... ]     <-- list of distances per SignalPoint to initial_location
        result = minimize(
                self.mse,                                   # The function to be minimized
                initial_location,                           # initial guess
                args=(locations, distances),                # parameters for self.mse

                method='Nelder-Mead',
                options={
                    'xatol'  : 1e-8,
                    'fatol'  : 1e-8,
                    'maxiter': 10000
                }

                # method='L-BFGS-b',                          # The minimization method
                # options={
                #     'ftol'   : 1e-5,                        # Tolerance
                #     'maxiter': 1e+7                         # Maximum iterations
                # }
        )

        location = result.x
        print(result.pop('message'))
        return location

    def run(self):
        # not sure how I plan to use this. trilat only one
        # seems not as useful as a group, so perhaps this
        # should be a list if items? Also, what to do about
        # symbology? How does this fit into other things
        # geolocated? this might be threaded, might not;
        # ...what's happening?

        # get_location(self)
        BSSID, sgnlPts = self.getSignalPointsForBSSID(self.target)

        self.locations = self.getLocationsForSignalPoints(sgnlPts)
        self.distances = self.getDistancesForSignalPoints([self.lat, self.lon], sgnlPts)

        self.result = self.trilaterate([self.lat, self.lon], self.locations, self.distances)
        print(f'{[self.lat, self.lon]} target:{self.target}  result: {self.result} \nlocations:{self.locations}\ndistances:{self.distances}\n')
        exit(0)

if __name__ == '__main__':
    trilaterator = Trilaterator()
    trilaterator.configure('gps.json')

    # Example:
    # Let's say you have the following coordinates:
    # Point A: 37.7749° N, 122.4194° W (San Francisco)
    # Point B: 40.7128° N, 74.0060° W (New York)
    locations = [
        [40.7128, -74.0060]
    ]

    distances = trilaterator.getDistancesForSignalPoints([37.7749, -122.4194], [{"lat": l[0], "lon": l[1]} for l in locations])

    result = trilaterator.trilaterate([37.7749, -122.4194], locations, distances)
    print(" position:", [trilaterator.lat, trilaterator.lon])
    print("locations:", locations)

    # Using an online calculator or a programming script with the Haversine formula,
    # the great circle distance between San Francisco and New York would be approximately 3,396 kilometers.
    print("distances:", distances)
    print("Estimated location:", result)
