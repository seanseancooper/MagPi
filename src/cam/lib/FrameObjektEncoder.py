import threading

from sklearn.preprocessing import MinMaxScaler
import numpy as np
import geohash
import cv2 as cv
import hashlib
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import pairwise_distances
from src.config import readConfig
import logging


class FrameObjektEncoder(threading.Thread):
    #     Spectral Analysis Features to Extract for Each Signal [scipy.signal, numpy.fft]:
    #     Feature                         : Description
    #
    #     Mean signal power               : Average strength
    #     Variance                        : Signal stability
    #     FFT Peak/Dominant Frequency     : Periodic behavior
    #     Auto-correlation lag            : Repetitions
    #     Coherence with other signals    : Time-dependent similarity
    #     Rolling correlation window      : Pairwise time-varying relationships [pandas.rolling().corr()]
    #     Mean signal power               : Average strength
    #
    #     PCA / UMAP | sklearn, umap-learn
    #     Clustering | sklearn.cluster
    #     Mutual Information | sklearn.metrics.mutual_info_score

    def __init__(self, frame_obj):
        super().__init__()
        self.frame_obj = frame_obj
        self.config = {}

        self.hash_histogram = True
        self.hist_nbins = 32                          # get from config and configure
        self.geohash_prec = 8                      # TOOD: geohash precision, make config

        self.mm_scaler = MinMaxScaler()
        # self.std_scaler = StandardScaler()

        self.mediapipe = False
        self._pose = None
        self._result_T = None

        # distances
        self.e_distance = float()           # euclidean distance between the current and previous frames
        self.e_cache = []                   # list of previous euclidean distance over last f_limit frames
        self.cosim = float()                # cosine similarity between the current and previous frames
        self.cosim_cache = []               # list of previous...
        self.mse = float()                  # Mean Squared Error between the current and previous frames
        self.mse_cache = []                 # list of previous...
        self.ssim = float()                 # Structural similarity between the current and previous frames
        self.ssim_cache = []                # list of previous...

    @staticmethod
    def hash_color_histogram(histogram):
        histogram_str = ','.join(map(str, histogram))
        return hashlib.sha256(histogram_str.encode()).hexdigest()

    def configure(self):
        tmp = {}
        readConfig('cam.json', tmp)
        self.config = tmp['PLUGIN']

        try:
            self.hash_histogram = self.config['encoder']['hash_histogram']
            self.hist_nbins = int(self.config['encoder']['hist_nbins'])
            self.geohash_prec = int(self.config['encoder']['geohash_prec'])
        except ValueError as v:
            print(f'{v} bad value: (should be numeric)')
            exit(1)

    def encode_lat_lon(self, latitude, longitude):
        return geohash.encode(latitude, longitude, precision=self.geohash_prec)

    def pre_mediapipe(self, f, _max_height, _max_width):

        if self.mediapipe:
            import mediapipe as mp  # only load if needed. slow...

            mp_pose = mp.solutions.pose
            self._pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            BGR_T = cv.cvtColor(f[_max_height, _max_width], cv.COLOR_RGB2BGR)  # 'BGR'
            self._result_T = self._pose.process(BGR_T)

    def post_mediapipe(self, f):
        if self.mediapipe:
            import mediapipe as mp  # already loaded, only here for refs
            mp_pose = mp.solutions.pose

        if self._result_T is not None:
            if self._result_T.pose_landmarks is not None:

                def draw_pose(fragment, result):
                    if result.pose_landmarks is not None:
                        mp_drawing = mp.solutions.drawing_utils
                        mp_drawing_styles = mp.solutions.drawing_styles
                        mp_drawing.draw_landmarks(fragment, result.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                                  landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

                draw_pose(f, self._result_T)

    def set_frame_delta(self, X, Y):
        ''' set the allowable difference between frames *fragments_* to the
        average of the paired euclidean distances between the previous 'item'
        and the current frame 'wall'.
        '''

        try:
            # return the distances between the row vectors of X and Y
            self.e_distance = np.mean(pairwise_distances(X, Y))
            self.e_cache.append(self.e_distance)

            # return the cosine similarity of X and Y
            self.cosim = np.mean(cosine_similarity(X, Y))
            self.cosim_cache.append(self.cosim)

            # def MSE(X, Y):
            #     n = X.shape[0] * Y.shape[1]
            #     return 1 / n * np.sum(np.square(X - Y))
            # self._frame_SSIM = MSE(X, Y)

            self.mse = np.sum((X - Y) ** 2)
            self.mse /= float(X.shape[0] * Y.shape[1])
            self.mse_cache.append(self.mse)

            from skimage.metrics import structural_similarity as ssim

            self.ssim = 0.0
            if X.shape[0] > self.config['tracker']['ssim_win_size'] and X.shape[1] > self.config['tracker']['ssim_win_size']:
                # skimage.metrics.structural_similarity(im1, im2, *, win_size=None, gradient=False, data_range=None, channel_axis=None, gaussian_weights=False, full=False, **kwargs)
                (self.ssim, diff) = ssim(X, Y, win_size=self.config['tracker']['ssim_win_size'], full=True)
                self.ssim_cache.append(self.ssim)

        except Exception as e:
            logging.warning(f'FrameObjektTracker error while setting deltas: {e}  {X.shape}, {Y.shape}')

    def extract_color_histogram_from_image(self, image):
        # images, channels, mask, histSize, ranges[, hist[, accumulate]]
        histogram = cv.calcHist([image], [0, 1, 2], None, [self.hist_nbins, self.hist_nbins, self.hist_nbins], [0, 256, 0, 256, 0, 256])
        histogram = cv.normalize(histogram, histogram).flatten()
        return histogram.tolist()

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

        def make_grey_data(item, rectangle):
            wx, wy, ww, wh = rectangle
            return cv.cvtColor(item[wy:wy + wh, wx:wx + ww], cv.COLOR_BGR2GRAY)

        prev_wall = self.frame_obj.prev_tag.wall
        wall = self.frame_obj.prev_tag.wall
        X = make_grey_data(prev_wall, rect_array)
        Y = make_grey_data(wall, rect_array)
        self.set_frame_delta(X, Y)

        encoded_rect = np.divide((np.asarray(self.frame_obj._rect)), rect_array)
        encoded_avg_loc = np.divide((np.asarray(self.frame_obj._avg_loc)), loc_array)

        norm_numerical_features = self.mm_scaler.fit_transform(numerical_features)
        lat_lon_features = self.encode_lat_lon(self.frame_obj.lat, self.frame_obj.lon)

        hashed_histogram = None
        histogram = self.extract_color_histogram_from_image(self.frame_obj.wall) # <-- get this from zeroMQ/imageZMQ
        normalized = cv.normalize(histogram, histogram)
        flattened = normalized.flatten()
        color_histogram = flattened.tolist()

        if self.hash_histogram:
            hashed_histogram = self.hash_color_histogram(color_histogram)

        encoded_data = list(norm_numerical_features) + list(encoded_rect) + list(encoded_avg_loc) + [lat_lon_features] + [hashed_histogram]

        # event list --> push events, labels and image refs to elastic
        # vehicle id: available in a model?
        # license plate reader: is this available in a model?

        # IDEA: MEDIAPIPE
        # person detection: use mediapipe pose to label as 'human' motion.
        # find AND magnify faces: use mediapipe face to find the head ROI, Magnify it.

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

