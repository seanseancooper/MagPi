import math
from datetime import datetime, timedelta

from scipy.optimize import minimize

from src.lib.utils import format_time, format_delta
from src.config import readConfig

class Trilaterator():
    # based on
    # www.alanzucconi.com/2017/03/13/understanding-geographical-coordinates/
    # https://www.kaggle.com/code/johnbacksund/rssi-trilateration-of-ap-location

    def __init__(self):
        super().__init__()

        self.config = {}

        self.created = datetime.now()   # when signal was found
        self.updated = datetime.now()   # when signal was last reported
        self.elapsed = timedelta()      # time signal has been tracked.

        self.a = None
        self.b = None


    def __str__(self):
        return {

            "created"       : format_time(self.created, self.config.get('TIMER_FORMAT', "%H:%M:%S")),
            "updated"       : format_time(self.updated, self.config.get('TIMER_FORMAT', "%H:%M:%S")),
            "elapsed"       : format_delta(self.elapsed, self.config.get('TIMER_FORMAT', "%H:%M:%S")),

        }

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def mse(self, x, locations, distances):
        # Mean Square Error
        # locations: [ (lat1, long1), ... ]
        # distances: [ distance1, ... ]
        mse = 0.0
        for location, distance in zip(locations, distances):
            distance_calculated = self.great_circle_distance(x[0], x[1], location[0], location[1])
            mse += math.pow(distance_calculated - distance, 2.0)
        return mse / len(distances)

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

    def trilaterate(self, initial_location, locations, distances):

        # initial_location: (lat, long)
        # locations: [ (lat1, long1), ... ]
        # distances: [ distance1,     ... ]
        result = minimize(
                self.mse,  # The error function
                initial_location,  # The initial guess
                args=(locations, distances),  # Additional parameters for mse
                method='L-BFGS-B',  # The optimisation algorithm
                options={
                    'ftol'   : 1e-5,  # Tolerance
                    'maxiter': 1e+7  # Maximum iterations
                })
        location = result.x

        return location
