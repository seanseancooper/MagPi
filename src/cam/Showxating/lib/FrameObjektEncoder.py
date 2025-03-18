import threading

from sklearn.preprocessing import MinMaxScaler
import numpy as np
import geohash
import cv2
import hashlib


class ObjektEncoder(threading.Thread):

    def __init__(self, frame_obj):
        super().__init__()
        self.frame_obj = frame_obj
        self.hash_histogram = True
        self.precision = 8
        self.bins = 12
        self.scaler = MinMaxScaler()

    def encode_lat_lon(self, latitude, longitude):
        return geohash.encode(latitude, longitude, precision=self.precision)

    def extract_color_histogram_from_image(self, image):
        # images, channels, mask, histSize, ranges[, hist[, accumulate]]
        histogram = cv2.calcHist([image], [0, 1, 2], None, [self.bins, self.bins, self.bins], [0, 256, 0, 256, 0, 256])
        histogram = cv2.normalize(histogram, histogram).flatten()
        return histogram.tolist()

    def hash_color_histogram(self, histogram):
        histogram_str = ','.join(map(str, histogram))
        return hashlib.sha256(histogram_str.encode()).hexdigest()

    def run(self):

        numerical_features = np.array([
            [
                self.frame_obj.fd,
                self.frame_obj.fd_mean,
                # self.frame_obj.delta_range,
                self.frame_obj.hist_delta,
                self.frame_obj.rect[0],
                self.frame_obj.rect[1],
                self.frame_obj.rect[2],
                self.frame_obj.rect[3],
                self.frame_obj.avg_loc[0],
                self.frame_obj.avg_loc[1],
                self.frame_obj.dist_mean,
            ]
        ])

        normalized_features = self.scaler.fit_transform(numerical_features)
        lat_lon_features = self.encode_lat_lon(self.frame_obj.lat, self.frame_obj.lon)

        # encoded_data = []
        # for features, obj, lat_lon in zip(normalized_features, self.frame_obj, lat_lon_features):
        #     color_histogram = None
        #     hashed_histogram = None
        #
        #     if obj.wall is not None:
        #         color_histogram = self.extract_color_histogram_from_image(obj.wall)
        #         if self.hash_histogram:
        #             hashed_histogram = self.hash_color_histogram(color_histogram)
        #
        #     combined = list(features) + (color_histogram if color_histogram else []) + [hashed_histogram] + [lat_lon]
        #     encoded_data.append(combined)
        #
        # return encoded_data

        color_histogram = self.frame_obj.w_hist
        hashed_histogram = None

        if self.frame_obj.w_hist is not None:
            if self.hash_histogram:
                hashed_histogram = self.hash_color_histogram(color_histogram)

        encoded_data = list(normalized_features) + (color_histogram if color_histogram else []) + [hashed_histogram] + [lat_lon_features]

        print(encoded_data)
        return encoded_data


