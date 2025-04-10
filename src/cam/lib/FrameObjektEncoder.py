import threading

from sklearn.preprocessing import MinMaxScaler, StandardScaler
import numpy as np
import geohash
import cv2 as cv
import hashlib
from src.cam.Showxating.ShowxatingHistogramPlugin import ShowxatingHistogramPlugin

class FrameObjektEncoder(threading.Thread):

    def __init__(self, frame_obj):
        super().__init__()
        self.frame_obj = frame_obj
        self.hash_histogram = True
        self.bins = 32                          # get from config and configure
        self.precision = 8                      # TOOD: geohash precision, make config
        self.mm_scaler = MinMaxScaler()
        self.std_scaler = StandardScaler()

    def encode_lat_lon(self, latitude, longitude):
        return geohash.encode(latitude, longitude, precision=self.precision)

    def get_histogram(self, wall, rectangle):

        hist_plugin = ShowxatingHistogramPlugin()
        hist_plugin.plugin_name = 'histogramPlugin'
        hist_plugin.get_config()
        hist_plugin.f_id = self.frame_obj.f_id
        hist_plugin._kz = (3, 3)                            # self.kernel_sz
        hist_plugin.library = 'cv'                          # TODO: add to configurable
        hist_plugin.compare_method = cv.HISTCMP_CORREL
        hist_plugin.norm_type = cv.NORM_MINMAX

        histogram = hist_plugin.get_histogram(wall, rectangle)
        histogram = cv.normalize(histogram, histogram)
        flattened = histogram.flatten()
        return flattened.tolist()

    def extract_color_histogram_from_image(self, image):
        # images, channels, mask, histSize, ranges[, hist[, accumulate]]
        histogram = cv.calcHist([image], [0, 1, 2], None, [self.bins, self.bins, self.bins], [0, 256, 0, 256, 0, 256])
        histogram = cv.normalize(histogram, histogram).flatten()
        return histogram.tolist()

    def hash_color_histogram(self, histogram):
        histogram_str = ','.join(map(str, histogram))
        return hashlib.sha256(histogram_str.encode()).hexdigest()

    def run(self):

        numerical_features = np.array([
            [
                float(self.frame_obj.distance),
                float(self.frame_obj.distances_mean),
                float(self.frame_obj.hist_delta),
            ]
        ])

        _s = self.frame_obj.frame_shape
        rect_array = np.asarray([int(_s[1]), int(_s[0]), int(_s[1]), int(_s[0])])
        loc_array = np.asarray([int(_s[1]), int(_s[0])])

        encoded_rect = np.divide((np.asarray(self.frame_obj.rect)), rect_array)
        encoded_avg_loc = np.divide((np.asarray(self.frame_obj.avg_loc)), loc_array)
        norm_numerical_features = self.mm_scaler.fit_transform(numerical_features)
        lat_lon_features = self.encode_lat_lon(self.frame_obj.lat, self.frame_obj.lon)

        hashed_histogram = None
        if self.frame_obj.w_hist:

            # histogram = self.get_histogram(self.frame_obj.wall, self.frame_obj.rect)
            histogram = self.extract_color_histogram_from_image(self.frame_obj.wall)
            normalized = cv.normalize(histogram, histogram)
            flattened = normalized.flatten()
            color_histogram = flattened.tolist()

            if self.hash_histogram:
                hashed_histogram = self.hash_color_histogram(color_histogram)

        encoded_data = list(norm_numerical_features) + list(encoded_rect) + list(encoded_avg_loc) + [lat_lon_features] + [hashed_histogram]

        # do something with encoded_data...
        # OFFLINE PROCESSING FEATURES
        # event list --> push events, labels and image refs to elastic
        # vehicle id: available in a model?
        # license plate reader: is this available in a model?
        print(f'encoded data {self.frame_obj.f_id}: {encoded_data}')
        exit(0)
        # return encoded_data

if __name__ == "__main__":

    from src.cam.lib.FrameObjekt import FrameObjekt

    frame_objects = [
        FrameObjekt.create(1),
        FrameObjekt.create(2),
        FrameObjekt.create(3)
    ]

    for f in frame_objects:
        encoder = FrameObjektEncoder(f)
        encoder.run()

