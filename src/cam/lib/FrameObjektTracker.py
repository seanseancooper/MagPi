import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeRegressor

from src.cam.lib.FrameObjekt import FrameObjekt
from sklearn.metrics import euclidean_distances

from src.cam.lib.cam_utils import is_in_range, is_inside
from src.config import readConfig
from src.map.gps import get_location

import logging
cam_logger = logging.getLogger('cam_logger')
speech_logger = logging.getLogger('speech_logger')

def print_frame(o, origin):

    print(
            f"{o.f_id}"
            f"\t{origin}"
            #  numerical distance to the previous tag
            f"\t{o.tag}"
            f"\t{o.prev_tag}"

            f"\to._avg_loc: {str(o._avg_loc)}"
            f"\to._rect:{str(o._rect).ljust(10, ' ')}"       
            f"\to.lat: {o.lat}"
            f"\to.lon: {o.lon}"
    )

class FrameObjektTracker(object):

    def __init__(self):
        super().__init__()
        self.f_id = 0                       # current frame id
        self.f_limit = 5                    # max age of frames in o_cache_map.
        self.contour_limit = None           # number of contours evaluated by plugin in each pass

        # CART features
        self.avg_loc = []                   # list of (x,y) location of contour in self.contours
        self.rectangle = None               # [tuple {x, y, w, h}: object segmentation] bounding rects of contours in this frame
        self.lat = 0.0                      # current latitude
        self.lon = 0.0                      # current longitude
        self.decision_tree = None

        self.tracked = {}                   # mapping of FrameObjekts over last 'f_limit' frames.
        self.config = {}

        # internal values use to ascertain similarity between frames
        self.f_delta_pcnt = 0.5             # 0..1 percentage of delta between current/previous f over all pixels
        self.delta_range = 90.00            # offset +/- allowed difference; frm_delta_pcnt * fd_mean
        self.l_delta_pcnt = 0.2             # 0..1 percentage of delta between the current/previous mean locations


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
        self.config['MODULE'] = "cam"  # missing from config

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

    def init_o(self, wall, rectangle, frame_stats):
        o = FrameObjekt.create(self.f_id)
        o._avg_loc = self.avg_loc
        o._rect = rectangle

        o.wall = wall        # put the wall on a temp filesystem and use the tag for the name

        get_location(self)
        o.lat = self.lat
        o.lon = self.lon

        o.frame_rate = frame_stats['capture_frame_rate']
        o.frame_period = frame_stats['capture_frame_period']
        o.frame_shape = frame_stats['capture_frame_shape']
        o.max_height = frame_stats['max_height']
        o.max_width = frame_stats['max_width']

        return o

    def get_stats(self, o):
        o.distance = int(o.distances[0])  # distance to previous mean location
        o.distances_mean = np.mean(o.distances)

        # is the current distance within a range of the
        # median of distances for the last thing with a tag?
        o.close = is_in_range(o.distance, o.distances_mean, self.l_delta_pcnt * o.distances_mean)
        o.inside = is_inside(o._avg_loc, o._rect)                                 # is the ml inside rect?
        o.delta_range = self.f_delta_pcnt * o.distances_mean                    # percentage of px difference

    def label_locations(self, frame, wall, frame_stats):
        """ find elements 'tag' by euclidean distance """

        labeled = []
        p_ml = [self.tracked.get(o_tag)._avg_loc for o_tag in list(self.tracked.keys())]

        if len(p_ml) == 1:
            o1 = self.init_o(wall, self.rectangle, frame_stats)

            o1.distances = euclidean_distances(
                    np.array([self.avg_loc], dtype=int),
                    np.array([p_ml[0]], dtype=int).reshape(1, -1)
            )

            o1.distance = int(o1.distances[0])
            o1.prev_tag = str(list(self.tracked.keys())[0])
            o1.tag = o1.create_tag(self.f_id)
            self.get_stats(o1)

            if o1.inside and None:
                o1.tag = f"{self.f_id}_{o1.prev_tag.split('_')[1]}"
                print_frame(o1, "N1:")

            if not o1.close and not None and not None:
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

            oN = self.init_o(wall, self.rectangle, frame_stats)
            loc = oN.get_avg_loc()
            rect = oN.get_rect()
            features = np.array([[rect[0], rect[1], rect[2], rect[3], loc[0], loc[1]]])

            # Collect past tracked objects for training
            if self.tracked:
                # these are not the right features. location based, deltas, distances, histgrams/hist-deltas, booleans.
                # this is a regression problem; what does the CART tree need? do normalize of data.
                # include latency [o.frame_rate, o.frame_period]

                training_data = np.array([[o._rect[0],
                                           o._rect[1],
                                           o._rect[2],
                                           o._rect[3],
                                           o._avg_loc[0],
                                           o._avg_loc[1]
                                           ] for o in self.tracked.values()])

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
                    self.get_stats(oN)

            else:
                oN.tag = oN.create_tag(self.f_id)

            print_frame(oN, "oN:")
            labeled.append(oN)

        if not labeled:
            # f 0
            o = self.init_o(wall, self.rectangle, frame_stats)
            o.close = False
            o.inside = True
            o.tag = o.create_tag(self.f_id)
            print_frame(o, "N0:")
            labeled.append(o)

        return labeled

    def track_objects(self, f_id, frame, contour, wall, rectangle, frame_stats):
        self.f_id = f_id
        self.rectangle = rectangle

        def get_mean_location(contours):
            x = []
            y = []

            [(x.append(a), y.append(b)) for [[a, b]] in contours]
            return np.mean(np.array([x, y]), axis=1, dtype=int)

        self.avg_loc = get_mean_location(contour)

        for o in self.label_locations(frame, wall, frame_stats):
            o.contour = contour

            if not o.prev_tag:
                o.prev_tag = o.tag

            self.tracked[o.tag] = o

        self.preen_cache()

        return self.tracked

