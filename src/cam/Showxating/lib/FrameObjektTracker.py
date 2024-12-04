import os.path

import cv2 as cv
import numpy as np
from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from sklearn.metrics import euclidean_distances, pairwise_distances
from sklearn.metrics.pairwise import paired_distances

from src.cam.Showxating.lib.utils import in_range, is_inside, getAggregatedRect, getRectsFromContours
from src.config import CONFIG_PATH, readConfig

import logging


cam_logger = logging.getLogger('cam_logger')


class FrameObjektTracker:

    def __init__(self):
        super().__init__()
        self.f_id = 0                       # current frame id
        self.config = {}

        self.f_limit = 0                    # hyperparameter: max age of frames in o_cache_map.
        self.frm_delta_pcnt = 1.00          # hyperparameter: percentage of delta between the current and previous frames over all pixels in frame

        self.contours = None                # ????
        self.tracked = {}                   # mapping of FrameObjekts over last 'f_limit' frames.

        self._ml = []                       # DO NOT CHANGE: list of (x,y) location of contour in self.contours
        self._frame_delta = float()         # DO NOT CHANGE: euclidean distance between the current and previous frames
        self._frame_deltas = []             # DO NOT CHANGE: list of previous distances over last f_limit frames

        self._frame_MSE = float()
        self._frame_MSEs = []

        self._frame_SSIM = float()

        self.fd_mean = float()              # mean of ALL differences between ALL SEEN frames -- no f_limit.
        self.d_range = float()              # offset +/- allowed difference; frm_delta_pcnt * fd_mean

    def configure(self):
        readConfig(os.path.join(CONFIG_PATH, 'cam.json'), self.config)

        self.f_limit = self.config['TRACKER']['f_limit']
        self.frm_delta_pcnt = self.config['TRACKER']['frm_delta_pcnt']

    def preen_cache(self):
        aged_o = [o for o in self.tracked if self.tracked.get(o).f_id < (self.f_id - self.f_limit)]
        [self.tracked.pop(o) for o in aged_o]

    def set_frame_delta(self, item, wall, rectangle):
        ''' set the allowable difference between frames *fragments_* to the
        average of the paired euclidean distances between the previous 'item'
        and the current frame 'wall'
        '''

        wx, wy, ww, wh = rectangle

        try:
            # TODO: see metrics of pairwise_distances
            # return the distances between the row vectors of X and Y
            X = cv.cvtColor(item[wy:wy + wh, wx:wx + ww], cv.COLOR_BGR2GRAY)
            Y = cv.cvtColor(wall[wy:wy + wh, wx:wx + ww], cv.COLOR_BGR2GRAY)
            self._frame_delta = np.mean(pairwise_distances(X, Y))
            self._frame_deltas.append(self._frame_delta)
        except Exception as e:
            cam_logger.error(f"Problem setting frame delta: {e}")

    def set_frame_MSE(self, item, wall, rectangle):

        wx, wy, ww, wh = rectangle
        self._frame_SSIM = 0.0

        try:
            X = cv.cvtColor(item[wy:wy + wh, wx:wx + ww], cv.COLOR_BGR2GRAY)
            Y = cv.cvtColor(wall[wy:wy + wh, wx:wx + ww], cv.COLOR_BGR2GRAY)

            self._frame_MSE = np.sum((X.astype("float") - Y.astype("float")) ** 2)
            self._frame_MSE /= float(X.shape[0] * Y.shape[1])

            from skimage.metrics import structural_similarity as ssim
            self._frame_SSIM = ssim(X, Y)

            self._frame_MSEs.append(self._frame_MSE)
        except Exception:
            pass

    def print_frame(self, o, origin):
        # foo = 0.0
        # try:
        #     foo = o1.curr_dist/o1.md
        # except Exception: pass
        # except RuntimeWarning: pass
        print(f"{str(self.f_id)}\t{origin}{str(o.tag[-12:])}\t"
              f"INSIDE: {str(o.is_inside).ljust(2, ' ')}\t"
              # f"CLOSE: {str(o1.close).rjust(1, ' ')}\t"
              f"dist: {str(o.curr_dist.__format__('.4f')).ljust(3, ' ')}\t"
              f"md: {str(o.md.__format__('.4f')).ljust(3, ' ')}\t"
              # f"foo: {str(foo.__format__('.4f')).ljust(3, ' ')}\t"
              f"ML: {str(o.ml)}\trect:{str(o.rect).ljust(10, ' ')}\t"
              # f"fd: {str(self.fd_mean.__format__('.4f')).ljust(10, ' ')}\tmse: {str(self._frame_MSE.__format__('.4f')).ljust(10, ' ')}\tssim: {str(self._frame_SSIM.__format__('.4f')).ljust(10, ' ')}"
        )

    def get_mean_location(self, contours):
        ''' aka 'basically where it is' get the average location of all the contours in the frame '''

        # res = np.mean([np.array(cnt).mean(axis=0) for cnt in np.array(contours, dtype=object)], axis=0)
        # res2 = np.mean([np.mean([[np.mean(pt, axis=0, dtype=int)] for pt in cnt], axis=0).reshape(-1, 1) for cnt in np.array(contours, dtype=object)], axis=0)
        # not_c_ml = np.mean([np.mean([np.mean([np.mean([pt], axis=0, dtype=int) for [pt] in pt], axis=0) for pt in cnt], axis=0) for cnt in [np.array(contours, dtype=object)]], axis=0)

        x = []
        y = []

        [(x.append(a), y.append(b)) for [[a, b]] in contours]
        return np.mean(np.array([x, y]), axis=1, dtype=int)

    def label_locations(self):
        """ find elements 'tag' by euclidean distance """

        labeled = []

        p_ml = [self.tracked.get(o_tag).ml for o_tag in list(self.tracked.keys())]  # get the previous mean_locations

        if len(p_ml) == 1:
            # NEW THING
            o1 = FrameObjekt.create(self.f_id)
            o1.tag = o1.create_tag(self.f_id)  # NEW TAG
            o1.ml = self._ml
            o1.isNew = True
            o1.distances = euclidean_distances(np.array([self._ml], dtype=int), np.array([p_ml[0]], dtype=int).reshape(1, -1))
            o1.md = np.mean(o1.distances) # before
            o1.prev_tag = str(list(self.tracked.keys())[0])
            o1.curr_dist = int(o1.distances[0])

            o1.rect = self.tracked.get(o1.prev_tag).rect
            # o1.close = None                           # WILL BE FALSE...
            o1.is_inside = is_inside(o1.ml, o1.rect)  # *SHOULD* BE TRUE

            self.print_frame(o1, "N1:")

            labeled.append(o1)

        if len(p_ml) > 1:
            o = FrameObjekt.create(self.f_id)
            o.ml = self._ml                                                         # will be a list...

            # compare this NEW o location to previous mean locations
            # for j in np.arange(len(p_ml)):
            #     distances.append(euclidean_distances(np.array([o.ml], dtype=int),
            #                                            np.array([p_ml[j]], dtype=int).reshape(1, -1)))
            #     print(f"a:{o.ml} to b:{p_ml[j]} distance:{distances[-1]}")
            o.distances = [euclidean_distances(np.array([self._ml], dtype=int), np.array([p_ml[j]], dtype=int).reshape(1, -1)) for j in np.arange(len(p_ml)) if p_ml[j] is not None]
            o.md = np.mean(o.distances)

            # not differentiating the contours as distinct to the movement in question
            # is a problem; selecting the contour closest to the current mean location
            # doesn't discount entirely foreign objects moving at random in the mean
            # location calculation.

            # need to find the k-nearest neighbors and label them.

            idx = np.argmin(o.distances)                              # minimum euclidean distance
            o.prev_tag = str(list(self.tracked.keys())[idx])          # tag closest to current location
            o.curr_dist = float(o.distances[idx])                     # distance from current location

            o.tag = f"{self.f_id}_{o.prev_tag.split('_')[1]}"

            # off = 0.10 * o.md
            # o.close = in_range(o.curr_dist, o.md, off)
            # if o.close or o.curr_dist == 0:
            #     o.tag = f"{self.f_id}_{o.prev_tag.split('_')[1]}"   # close enough, use the previous tag.
            # else:
            #     o.tag = o.create_tag(self.f_id)                      # distant, NEW tag (is this the place to create it?)
            #     # o.tag = f"{self.f_id}_{o.prev_tag.split('_')[1]}"  # close enough, use the previous tag.
            #     o.isNew = True

            self.print_frame(o, "   ")
            labeled.append(o)

        if not labeled:
            # f 0
            o = FrameObjekt.create(self.f_id)
            o.tag = o.create_tag(self.f_id)
            o.ml = self._ml
            o.skip = True
            # o.close = None
            self.print_frame(o, "N0:")
            labeled.append(o)

        return labeled

    def track_objects(self, f_id, contour, hierarchy, wall, rectangle):
        """
        LEARNINGS:
        Not all moving things should be tracked; this is very sensitive to minute changes in light, and not all movement is relevant.
        Not all tracked things move; Consider flashing lights or any localized, repetitive change. Tracking seizes!
        Objects can suddenly appear or appear to change *size* if the frame drags due to network latency. Back referencing frames needs a cache.
        """
        self.f_id = f_id
        self.contours = contour

        self._ml = self.get_mean_location(self.contours)  # = c_grps_locs[grp_ident]

        for o in self.label_locations():

            o.wall = wall
            o.contours = self.contours                  # = c_grps_cnts[id]
            o.hierarchy = hierarchy                     # unused, will be i of an enumeration
            o.rect = rectangle
            o.is_inside = is_inside(o.ml, o.rect)

            # there may not be a previous tag, frame or anything...
            if o.prev_tag:
                prev_wall = self.tracked.get(o.prev_tag).wall               # we have wall, thus a previous frame
                self.set_frame_delta(prev_wall, wall, rectangle)            # compare to current wall
                self.set_frame_MSE(prev_wall, wall, rectangle)
                o.fd = self._frame_delta                                    # delta of walls. The wall is specific to the contour group.
                self.fd_mean = np.mean(self._frame_deltas)                  # a float,
                self.d_range = self.frm_delta_pcnt * self.fd_mean           # percentage of px difference
            else:
                # area = cv.contourArea(self.contours)
                # if area < 500:
                #     continue

                # is the current delta outside the ALLOWED mean of all the previous frame deltas?
                # how different is this wrt that which preceded it?
                # don't compute this if you don't have to?

                # if not o.is_inside:
                #     if in_range(self._frame_delta, self.fd_mean, self.d_range):     # THIS IS THE PREVIOUS FRAME DELTA, MEAN & RANGE NOW!!! WE MAY NOT HAVE THIS!!
                #         # o.tag = self.tracked[list(self.tracked)[0]].tag     # not -- > f'{self.f_id}_{some_tag.split("_")[1]}'
                #         o.tag = o.create_tag(self.f_id)                       # not -- > self.tracked[list(self.tracked)[0]].tag
                #         o.isNew = True  # False                               #
                #     else:
                #         pass  # not inside, out of range?? after every iteration
                o.tag = o.create_tag(self.f_id)

            self.tracked[o.tag] = o

        self.preen_cache()

        return self.tracked

