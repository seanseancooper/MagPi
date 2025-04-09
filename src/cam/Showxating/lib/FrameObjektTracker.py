import uuid

import cv2 as cv
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeRegressor

from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from sklearn.metrics import euclidean_distances, pairwise_distances, pairwise_kernels
from sklearn.metrics.pairwise import paired_distances, cosine_similarity

from src.cam.Showxating.lib.utils import is_in_range, is_inside
from src.config import readConfig
from src.lib.utils import get_location

import logging
cam_logger = logging.getLogger('cam_logger')
speech_logger = logging.getLogger('speech_logger')

def print_frame(o, origin):

    print(
            f"{o.f_id}"
            f"\t{origin}"
            f"\t{o.tag}"
            f"\t{o.prev_tag}"

            f"\to.avg_loc: {str(o.avg_loc)}"
            f"\to.rect:{str(o.rect).ljust(10, ' ')}"
                        
            f"\to.lat: {o.lat}"
            f"\to.lon: {o.lon}"

            # f"\to.ssim_pass: {o.ssim_pass}"
            # f"\to.wall_pass: {o.wall_pass}"
            # f"\to.mse_pass: {o.mse_pass}"
            # f"\to.cosim_pass: {o.cosim_pass}"
            
            # f"\tdistance: {str(o.distance.__format__('.4f')).ljust(3, ' ')}"
            # f"\tdistances_mean: {str(o.distances_mean.__format__('.4f')).ljust(3, ' ')}"
            

    )

class FrameObjektTracker:

    def __init__(self):
        super().__init__()
        self.f_id = 0                       # current frame id
        self.f_limit = 30                   # max age of frames in o_cache_map.
        self.f_delta_pcnt = 0.5             # 0..1 percentage of delta between current/previous f over all pixels
        self.f_delta_mean = float()         # InCORRECT!: mean of ALL differences between ALL SEEN frames -- no f_limit.
        self.delta_range = 90.00            # offset +/- allowed difference; frm_delta_pcnt * fd_mean
        self.l_delta_pcnt = 0.2             # 0..1 percentage of delta between the current/previous mean locations

        self.contour_limit = None           # number of contours evaluated by plugin in each pass
        self.contour_id = None              # ????

        self.tracked = {}                   # mapping of FrameObjekts over last 'f_limit' frames.
        self.mean_xy = []                   # list of (x,y) location of contour in self.contours

        self.e_distance = float()           # euclidean distance between the current and previous frames
        self.e_cache = []                   # list of previous euclidean distance over last f_limit frames

        self.cosim = float()                # cosine similarity between the current and previous frames
        self.cosim_cache = []               # list of previous...

        self.mse = float()                  # Mean Squared Error between the current and previous frames
        self.mse_cache = []                 # list of previous...

        self.ssim = float()                 # Structural similarity between the current and previous frames
        self.ssim_cache = []                # list of previous...

        self.lat = 0.0                      # current latitude
        self.lon = 0.0                      # current longitude

        self.decision_tree = None
        self.config = {}

    def get(self):
        return {
            # TODO: fields for deltas, SSIM, MSE, etc.
            "f_limit"       : self.f_limit,
            "frm_delta_pcnt": float(self.f_delta_pcnt),
            # "contour_limit" : self.contour_limit,
            # "tracked"       : [self.tracked.get(o).get() for o in self.tracked],

            # "_ml"           : str(self._ml),
            # "_frame_delta"  : float(self._frame_delta),
            # "_frame_MSE"    : float(self._frame_MSE),

            # "fd_mean"       : float(self.fd_mean),
            # "d_range"       : float(self.d_range),

        }

    def configure(self):
        tmp = {}
        readConfig('cam.json', tmp)
        self.config = tmp['PLUGIN']

        try:
            self.f_limit = int(self.config['tracker'].get('f_limit', 1))
            if self.f_limit < 1:
                self.f_limit = 1

            self.f_delta_pcnt = float(self.config['tracker']['f_delta_pcnt'])
            self.l_delta_pcnt = float(self.config['tracker']['l_delta_pcnt'])
            self.delta_range = float(self.config['tracker']['d_range'])

            self.contour_limit = int(self.config['tracker'].get('contour_limit', None))
            if self.contour_limit == 0:
                print(f'contour_limit warning: (contour_limit should be > 0 or "None" for all contours)')

        except ValueError:
            print(f'bad value: (should be numeric)')
            exit(1)

    def preen_cache(self):
        aged_o = [o for o in self.tracked if self.tracked.get(o).f_id < (self.f_id - self.f_limit)]
        [self.tracked.pop(o) for o in aged_o]

    def clear_cache(self, f_id):
        if self.tracked:
            last_frame = int(list(self.tracked.keys())[-1].split('_')[0])
            if (f_id - last_frame) > self.f_limit:
                self.tracked.clear()
                print('cache cleared!')

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
            cam_logger.warning(f'FrameObjektTracker error while setting deltas: {e}  {X.shape}, {Y.shape}')

    def init_o(self, wall, rectangle):
        o = FrameObjekt.create(self.f_id)
        o.rect = rectangle
        # put the wall on a temp filesystem and use the tag for the name
        o.wall = wall
        o.f_shape = wall.shape

        get_location(self)
        o.lat = self.lat
        o.lon = self.lon

        # oN.contour_id = self.contour_id
        o.avg_loc = self.mean_xy

        return o

    def get_stats(self, o, wall, rectangle):

        def make_grey_data(item, rectangle):
            wx, wy, ww, wh = rectangle
            return cv.cvtColor(item[wy:wy + wh, wx:wx + ww], cv.COLOR_BGR2GRAY)

        # does this wall match the previous one?
        # pairwise distance to the previous wall image
        X = make_grey_data(self.tracked.get(o.prev_tag).wall, rectangle)
        Y = make_grey_data(wall, rectangle)
        self.set_frame_delta(X, Y)

        o.distance = self.e_distance  # delta of wall image to current f
        o.distances_mean = np.mean(self.e_cache)

        # is the current distance within a range of the
        # median of distances for the last thing with a tag?
        o.close = is_in_range(o.distance, max(o.rect[2], o.rect[3]), self.l_delta_pcnt * max(o.rect[1], o.rect[2]))

        o.inside_rect = is_inside(o.avg_loc, o.rect)                            # is the ml inside rect?
        o.delta_range = self.f_delta_pcnt * o.distances_mean                    # percentage of px difference

        o.hist_pass = None
        o.ssim_pass = self.ssim > 0.1
        o.wall_pass = is_in_range(o.distance, o.distances_mean, self.delta_range)
        o.mse_pass = self.mse > 0.0
        o.cosim_pass = self.cosim > 0.0

    def label_locations(self, frame, wall, rectangle, stats):
        """ find elements 'tag' by euclidean distance """

        labeled = []
        # get all previous mean_locations (if they exist)
        p_ml = [self.tracked.get(o_tag).avg_loc for o_tag in list(self.tracked.keys())]

        if len(p_ml) == 1:
            # NEW TAG for a different thing; there is only one
            o1 = self.init_o(wall, rectangle)

            o1.distances = euclidean_distances(
                    np.array([self.mean_xy], dtype=int),
                    np.array([p_ml[0]], dtype=int).reshape(1, -1)
            )

            o1.distances_mean = np.mean(o1.distances)

            o1.distance = int(o1.distances[0])
            o1.prev_tag = str(list(self.tracked.keys())[0])

            o1.tag = o1.create_tag(self.f_id)
            self.get_stats(o1, wall, rectangle)

            if o1.inside_rect and o1.ssim_pass:
                # item following f0 item.

                # back reference and merge the rects (n largest) and
                # take a pic of the merged area (use frame)
                # largest area wins.

                o1.tag = f"{self.f_id}_{o1.prev_tag.split('_')[1]}"
                print_frame(o1, "N1:")

            if not o1.close and not o1.ssim_pass and not o1.wall_pass:
                # NEW 'interstitial' item
                o1.tag = o1.create_tag(self.f_id)
                print_frame(o1, "!N:")

            labeled.append(o1)

        if len(p_ml) > 1:

            # class sklearn.tree.DecisionTreeRegressor(*,
            # criterion='squared_error',
            # splitter='best',
            # max_depth=None,
            # min_samples_split=2,
            # min_samples_leaf=1,
            # min_weight_fraction_leaf=0.0,
            # max_features=None,
            # random_state=None,
            # max_leaf_nodes=None,
            # min_impurity_decrease=0.0,
            # ccp_alpha=0.0)
            self.decision_tree = DecisionTreeRegressor()
            label_encoder = LabelEncoder()

            oN = self.init_o(wall, rectangle)
            features = np.array([[    oN.rect[0], oN.rect[1], oN.rect[2], oN.rect[3], oN.avg_loc[0], oN.avg_loc[1]    ]])

            # Collect past tracked objects for training
            if self.tracked:
                # these are not the right features. location based, deltas, distances, histgrams/hist-deltas, booleans.
                # this is a regression problem; what does the CART tree need? do normalize of data.
                # include latency [o.frame_rate, o.frame_period]


                training_data = np.array([[    o.rect[0], o.rect[1], o.rect[2], o.rect[3], o.avg_loc[0], o.avg_loc[1]    ] for o in self.tracked.values()])
                training_labels = [o.tag for o in self.tracked.values()]

                numeric_labels = label_encoder.fit_transform(training_labels)
                self.decision_tree.fit(training_data, numeric_labels)

            if self.tracked:
                prediction = self.decision_tree.predict(features)[0]  # it's a continuous value
            else:
                prediction = None

            if prediction is not None:
                threshold = 7.0

                if prediction > threshold:
                    # a new tag if prediction exceeds threshold
                    oN.tag = oN.create_tag(self.f_id)
                else:
                    # reuse the predicted tag by it's index
                    predicted_tag = label_encoder.inverse_transform(self.decision_tree.predict(features).astype(int))[0]
                    oN.tag = f"{self.f_id}_{predicted_tag.split('_')[1]}"
                    oN.prev_tag = predicted_tag
                    self.get_stats(oN, wall, rectangle)

            else:
                oN.tag = oN.create_tag(self.f_id)

            print_frame(oN, "oN:")
            labeled.append(oN)

        if not labeled:
            # f 0
            o = self.init_o(wall, rectangle)
            o.close = is_in_range(o.distance, o.distances_mean, self.l_delta_pcnt * o.distances_mean)
            o.inside_rect = is_inside(o.avg_loc, o.rect)
            o.tag = o.create_tag(self.f_id)
            print_frame(o, "N0:")
            labeled.append(o)

        return labeled

    def track_objects(self, f_id, frame, contour, hierarchy, wall, rectangle, stats):
        """
        LEARNINGS:
        Not all moving things should be tracked; this is very sensitive to minute
        changes in light, and not all movement is relevant.
        Not all tracked things move; Consider flashing lights or any localized,
        repetitive change. Tracking seizes!
        Objects can suddenly appear or appear to change *size* if the frame drags
        due to network latency. Back referencing frames needs a cache.
        """
        self.f_id = f_id
        self.contour_id = str(uuid.uuid4()).split('-')[0]

        def get_mean_location(contours):
            ''' aka 'basically where it is' get the average location of all the contours in the frame '''
            x = []
            y = []

            [(x.append(a), y.append(b)) for [[a, b]] in contours]
            return np.mean(np.array([x, y]), axis=1, dtype=int)

        self.mean_xy = get_mean_location(contour)
        # pass statistics here so they can be used by CART trees
        for o in self.label_locations(frame, wall, rectangle, stats):

            # this is one of a group of sorted
            # contours; it could be the first
            # or the smallest. first is largest.
            o.contour = contour
            o.hierarchy = hierarchy                      # unused for now

            if not o.prev_tag:
                o.prev_tag = o.tag

            self.tracked[o.tag] = o

        self.preen_cache()

        return self.tracked

