import os.path
import cv2 as cv
import numpy as np
from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from sklearn.metrics.pairwise import euclidean_distances, paired_distances

from src.cam.Showxating.lib.utils import in_range, is_inside
from src.config import CONFIG_PATH, readConfig

import logging


cam_logger = logging.getLogger('cam_logger')


class FrameObjektTracker:

    def __init__(self):
        super().__init__()
        self.f_id = 0               # current frame id
        self.config = {}

        # hyper parameters
        self.f_limit = 2            # hyperparameter: max age of frames in o_cache_map.
        self.frm_delta_pcnt = 0.95  # hyperparameter: percentage of delta between the current and previous frames over all pixels in frame

        self.tracked = {}           # mapping of FrameObjekts over last 'f_limit' frames.

        self._ml = []               # DO NOT CHANGE: list of (x,y) location of contour in contours
        self._frame_delta = 0.0     # DO NOT CHANGE: euclidean distance between the current and previous frames
        self._frame_deltas = []     # DO NOT CHANGE: list of previous distances over last f_limit frames

    def configure(self):
        readConfig(os.path.join(CONFIG_PATH, 'cam.json'), self.config)

        self.f_limit = self.config['TRACKER']['f_limit']
        self.frm_delta_pcnt = self.config['TRACKER']['frm_delta_pcnt']

    def set_frame_delta(self, item, wall, rectangle):
        ''' set the allowable difference between frames *fragments_* to the
        average of the paired euclidean distances between the previous 'item'
        and the current frame 'wall'
        '''

        wx, wy, ww, wh = rectangle

        try:
            # TODO: try out metric = "euclidean", "manhattan", or "cosine"
            distances = paired_distances(cv.cvtColor(wall[wy:wy + wh, wx:wx + ww], cv.COLOR_BGR2GRAY), cv.cvtColor(item[wy:wy + wh, wx:wx + ww], cv.COLOR_BGR2GRAY))
            self._frame_delta = np.mean(distances)
            self._frame_deltas.append(self._frame_delta)
        except Exception as e:
            cam_logger.error(f"Problem setting frame delta: {e}")

    def get_mean_location(self, contours):
        ''' aka 'basically where it is' get the average location of all the contours in the frame '''

        # break the contours into 'nearest neighbors'
        # so we can process each group separately as
        # independent things.

        x = []
        y = []

        for cnt in contours:
            [(x.append(a), y.append(b)) for [[a, b]] in cnt]

        # this will become a list of [x, y]!!!
        return np.mean(np.array([x, y]), axis=1, dtype=int)

        # res = np.mean([np.array(cnt).mean(axis=0) for cnt in np.array(contours, dtype=object)], axis=0)
        # res2 = np.mean([np.mean([[np.mean(pt, axis=0, dtype=int)] for pt in cnt], axis=0).reshape(-1, 1) for cnt in np.array(contours, dtype=object)], axis=0)
        # not_c_ml = np.mean([np.mean([np.mean([np.mean([pt], axis=0, dtype=int) for [pt] in pt], axis=0) for pt in cnt], axis=0) for cnt in [np.array(contours, dtype=object)]], axis=0)

    def label_locations(self):
        """ find elements 'tag' by euclidean distance """

        labeled = []
        distances = []  # this will be a mapping... need to id the contour 'group'

        p_ml = [self.tracked.get(o_key).ml for o_key in list(self.tracked.keys())]  # get the previous (self.f_limit) detected and located mean_location from the cache_map

        if len(p_ml) > 1:

            o = FrameObjekt.create(self.f_id)
            o.ml = self._ml  # will be a list...
            # compare this NEW o location to previous mean locations
            # for j in np.arange(len(p_ml)):
            #     distances.append(euclidean_distances(np.array([o.ml], dtype=int),
            #                                            np.array([p_ml[j]], dtype=int).reshape(1, -1)))
            #     print(f"a:{o.ml} to b:{p_ml[j]} distance:{distances[-1]}")
            [distances.append(euclidean_distances(np.array([self._ml], dtype=int), np.array([p_ml[j]], dtype=int).reshape(1, -1))) for j in np.arange(len(p_ml)) if p_ml[j] is not None]

            o.distances = distances
            idx = np.argmin(distances)                      # which one is closer to the current location? first or second?
            o.prev_tag = str(list(self.tracked.keys())[idx])     # tag closest to the current location
            o.prev_dist = np.float64(distances[idx])        # the distance from the current location

            # if in_range(o.prev_dist, np.mean(distances), .10 * np.mean(distances)):
            if o.prev_dist <= np.mean(distances) or o.prev_dist == 0.0:     # if the lower of the 2 distances is less than the mean...
                o.tag = f"{self.f_id}_{o.prev_tag.split('_')[1]}"           # close enough to be the same thing, use the previous tag.
                o.close = True
            else:
                o.isNew = True
                o.close = False

            labeled.append(o)

        if not labeled:
            o = FrameObjekt.create(self.f_id)
            o.ml = self._ml
            o.skip = True
            labeled.append(o)

        return labeled

    def preen_cache(self):
        aged_o = [o for o in self.tracked if self.tracked.get(o).f_id < (self.f_id - self.f_limit)]
        [self.tracked.pop(o) for o in aged_o]

    def track_objects(self, f_id, contours, hierarchy, wall, rectangle):
        """
        LEARNINGS:
        Not all moving things should be tracked; this is very sensitive to minute changes in light, and not all movement is relevant.
        Not all tracked things move; Consider flashing lights or any localized, repetitive change. Tracking seizes!
        Objects can suddenly appear or appear to change *size* if the frame drags due to network latency. Back referencing frames needs a cache.
        """

        self.f_id = f_id
        self._ml = self.get_mean_location(contours)

        for o in self.label_locations():

            o.wall = wall
            o.contours = contours
            o.hierarchy = hierarchy
            o.rect = rectangle
            o.is_inside = is_inside(o.ml, o.rect)

            if o.prev_tag:
                prev_wall = self.tracked.get(o.prev_tag).wall
                self.set_frame_delta(prev_wall, wall, rectangle)
                o.fd = self._frame_delta                                # delta of walls
            else:
                # is the current delta outside the ALLOWED mean of all the previous frame deltas?
                # how different is this wrt that which preceded it?
                if not o.is_inside:
                    fd_mean = np.mean(self._frame_deltas[:-self.f_limit])   # a float,
                    d_range = self.frm_delta_pcnt * fd_mean                 # percentage of px difference

                    if in_range(self._frame_delta, fd_mean, d_range):
                        o.tag = self.tracked[list(self.tracked)[0]].tag     # not -- > f'{self.f_id}_{tag.split("_")[1]}'
                        o.isNew = False                                     # use the previous tag; SAME THING IN THE SAME PLACE
                else:
                    o.tag = o.create_tag(self.f_id)         # NEW TAG FOR A NEW THING IN A NEW PLACE
                    print(f"{self.f_id} NEW: {o.tag}\t{o.is_inside}\t[{o.prev_dist.__format__('.4f')}]\tml: {o.ml}:{o.rect}")

            self.tracked[o.tag] = o
            print(f"{self.f_id}      {o.tag}\t{o.is_inside}\t[{o.prev_dist.__format__('.4f')}]\tml: {o.ml}:{o.rect}")

        self.preen_cache()

        return self.tracked

