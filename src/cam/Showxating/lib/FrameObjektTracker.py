import uuid

import cv2 as cv
import numpy as np
from decimal import *
from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from sklearn.metrics import euclidean_distances, pairwise_distances
from sklearn.metrics.pairwise import paired_distances

from src.cam.Showxating.lib.utils import is_in_range, is_inside, getAggregatedRect, getRectsFromContours
from src.config import readConfig

import logging
cam_logger = logging.getLogger('cam_logger')
speech_logger = logging.getLogger('speech_logger')


class FrameObjektTracker:

    def __init__(self):
        super().__init__()
        self.f_id = 0                       # current frame id
        self.config = {}

        self.f_limit = 2                    # hyperparameter: max age of frames in o_cache_map.
        self.f_delta_pcnt = 0.50            # hyperparameter: 0..1 percentage of delta between the current and previous frames over all pixels in frame
        self.l_delta_pcnt = 0.50            # hyperparameter: 0..1 percentage of delta between the current and previous mean locations
        self.contour_limit = None           # number of contours evaluated by plugin in each pass
        self.contour_id = None              # ????
        self.tracked = {}                   # mapping of FrameObjekts over last 'f_limit' frames.
        self.greyscale_frame  = None
        self._ml = []                       # DO NOT CHANGE: list of (x,y) location of contour in self.contours
        self._frame_delta = float()         # DO NOT CHANGE: euclidean distance between the current and previous frames
        self._frame_deltas = []             # DO NOT CHANGE: list of previous distances over last f_limit frames

        self._frame_MSE = float()
        self._frame_MSEs = []

        self._frame_SSIM = float()

        self.fd_mean = float()              # mean of ALL differences between ALL SEEN frames -- no f_limit.
        self.d_range = float()              # offset +/- allowed difference; frm_delta_pcnt * fd_mean

    def get(self):
        return {
            "f_id": self.f_id,                      # current frame id
            "f_limit": self.f_limit,                # hyperparameter: max age of frames in o_cache_map.
            "frm_delta_pcnt": self.f_delta_pcnt,  # hyperparameter: percentage of delta between the current and previous frames over all pixels in frame
            "contour_limit": self.contour_limit,    # number of contours evaluated by plugin in each pass
            "tracked": self.tracked,                # mapping of FrameObjekts over last 'f_limit' frames.

            "_ml": self._ml,                        # DO NOT CHANGE: list of (x,y) location of contour in self.contours
            "_frame_delta": self._frame_delta,      # DO NOT CHANGE: euclidean distance between the current and previous frames
            "_frame_MSE": self._frame_MSE,
            "_frame_SSIM": self._frame_SSIM,

            "fd_mean": self.fd_mean,                # mean of ALL differences between ALL SEEN frames -- no f_limit.
            "d_range": self.d_range,                # offset +/- allowed difference; frm_delta_pcnt * fd_mean
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
            if self.f_delta_pcnt > 1.0:
                print(f'bad f_delta_pcnt: (should be <= 1.0)')
                exit(1)

            self.l_delta_pcnt = float(self.config['tracker']['l_delta_pcnt'])
            if self.l_delta_pcnt > 1.0:
                print(f'bad l_delta_pcnt: (should be <= 1.0)')
                exit(1)

           # not implmented. yet...
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
                print('cleared cache!')

    @staticmethod
    def make_grey_data(item, rectangle):
        wx, wy, ww, wh = rectangle
        return cv.cvtColor(item[wy:wy + wh, wx:wx + ww], cv.COLOR_BGR2GRAY)

    def set_frame_delta(self, X, Y):
        ''' set the allowable difference between frames *fragments_* to the
        average of the paired euclidean distances between the previous 'item'
        and the current frame 'wall'.
        '''
        self._frame_SSIM = 0.0
        try:
            # TODO: see metrics of pairwise_distances
            # return the distances between the row vectors of X and Y
            self._frame_delta = np.mean(pairwise_distances(X, Y))
            self._frame_deltas.append(self._frame_delta)

            self._frame_MSE = np.sum((X - Y) ** 2)
            self._frame_MSE /= float(X.shape[0] * Y.shape[1])

            def MSE(X, Y):
                n = X.shape[0] * Y.shape[1]
                return 1 / n * np.sum(np.square(X - Y))

            self._frame_SSIM = MSE(X, Y)

            # from skimage.metrics import structural_similarity as ssim
            # self._frame_SSIM = ssim(X, Y)
            # self._frame_MSEs.append(self._frame_MSE)

        except Exception as e:
            # ssim(X, Y) Problem setting frame delta: win_size exceeds image extent.
            # Either ensure that your images are at least 7x7; or pass win_size explicitly
            # in the function call, with an odd value less than or equal to the smaller
            # side of your images. If your images are multichannel (with color channels),
            # set channel_axis to the axis number corresponding to the channels.
            pass

    def print_frame(self, o, origin):
        # print(f"{str(self.f_id)}\t{origin}{o.contour_id}-{str(o.tag[-12:])}\t"
        print(f"{self.f_id}"
              f"\t{origin}"
              f"\t{o.tag}"
              f"\to.curr_dist: {str(o.curr_dist.__format__('.4f')).ljust(3, ' ')}"
              f"\to.md: {str(o.md.__format__('.4f')).ljust(3, ' ')}"
              f"\to.ml: {str(o.ml)}"
              f"\to.rect:{str(o.rect).ljust(10, ' ')}\t"
              f"\to.fd: {str(self.fd_mean.__format__('.4f')).ljust(10, ' ')}"
              f"\tmse: {str(self._frame_MSE.__format__('.4f')).ljust(10, ' ')}"
              f"\to.in_range: {o.in_range} "
              f"\to.is_inside: {o.is_inside} "
              f"\to.close: {o.close} "
              f"\to.hist_delta: {o.hist_delta} "
              f"\to.is_negative: {o.is_negative}"
        )

    def get_mean_location(self, contours):
        ''' aka 'basically where it is' get the average location of all the contours in the frame '''
        x = []
        y = []

        [(x.append(a), y.append(b)) for [[a, b]] in contours]
        return np.mean(np.array([x, y]), axis=1, dtype=int)

    def label_locations(self, frame, wall, rectangle):
        """ find elements 'tag' by euclidean distance """

        labeled = []

        p_ml = [self.tracked.get(o_tag).ml for o_tag in list(self.tracked.keys())]  # get all previous mean_locations (if they exist)

        if len(p_ml) == 1:
            # NEW TAG for a different thing; there is only one
            o1 = FrameObjekt.create(self.f_id)
            o1.rect = rectangle  # NOW WE GET A RECT.
            o1.wall = wall                               # the current wall is my wall.

            o1.contour_id = self.contour_id
            o1.ml = self._ml
            o1.isNew = True

            # contours are sorted, first p_ml is 'largest' contour
            o1.distances = euclidean_distances(np.array([self._ml], dtype=int), np.array([p_ml[0]], dtype=int).reshape(1, -1))
            o1.md = np.mean(o1.distances)

            o1.curr_dist = int(o1.distances[0])
            o1.prev_tag = str(list(self.tracked.keys())[0])                 # find the last thing with a tag, if not expired already ("when?", f_limit). LEAVE IT IN THERE!
            o1.tag = o1.create_tag(self.f_id)

            o1.is_inside = is_inside(o1.ml, o1.rect)
            o1.close = is_in_range(o1.curr_dist, o1.md, self.l_delta_pcnt * o1.md)


            o1.hist_delta = self.get_histogram_delta(self.tracked.get(o1.prev_tag).wall, wall, rectangle)

            o1.is_negative = False
            if Decimal.from_float(o1.hist_delta).is_signed():
                o1.is_negative = True

            # pairwise distance to the previous wall image
            X = self.make_grey_data(self.tracked.get(o1.prev_tag).wall, rectangle)
            Y = self.make_grey_data(wall, rectangle)
            self.set_frame_delta(X, Y)  # compare to current wall

            o1.fd = self._frame_delta  # delta of wall image to current f
            self.fd_mean = np.mean(self._frame_deltas)  # a float,
            self.d_range = self.f_delta_pcnt * self.fd_mean  # percentage of px difference

            o1.in_range = False
            if is_in_range(o1.fd, self.fd_mean, self.d_range):
                o1.in_range = True

            if o1.is_inside and not o1.is_negative:
                # 22 NEW item.
                self.print_frame(o1, "N1:")

            else:
                # 10 NEW item out of focus
                self.print_frame(o1, "X1:")

            if not o1.is_inside and o1.is_negative and o1.close:
                # self.print_frame(o1, "!C:")
                return labeled
            elif not o1.is_inside and o1.is_negative:
                # self.print_frame(o1, "!X:")
                return labeled

            labeled.append(o1)

        if len(p_ml) > 1:
            oN = FrameObjekt.create(self.f_id)
            oN.rect = rectangle  # NOW WE GET A RECT.
            oN.wall = wall                               # the current wall is my wall.

            # oN.contour_id = self.contour_id
            oN.ml = self._ml
            oN.isNew = False  # could be reset!

            # get the mean location of the distances identified in the previous frame
            oN.distances = [euclidean_distances(np.array([self._ml], dtype=int), np.array([p_ml[j]], dtype=int).reshape(1, -1)) for j in np.arange(len(p_ml)) if p_ml[j] is not None]
            oN.md = np.mean(oN.distances)

            # I think this is wrong; criteria should add:
            # if distance from the closest is > the bounds of the current rect, it is new.
            # this should choose the closest item within the bounds of it's rect.
            idx = np.argmin(oN.distances)                                 # the item in the array representing the minimum euclidean distance to the current location

            oN.curr_dist = float(oN.distances[idx])                       # distance from last location
            oN.prev_tag = str(list(self.tracked.keys())[idx])             # target tag; may not be the right tag
            oN.tag = f"{self.f_id}_{oN.prev_tag.split('_')[1]}"           # THIS IS A GUESS

            # did o suddenly appear?
            # is the current ml inside the current rect? THIS SHOULD ALWAYS BE TRUE
            # if so -- this is MY RECTANGLE, otherwise ths  is indicative of some other contour.
            oN.is_inside = is_inside(oN.ml, oN.rect)
            # is the current distance within a range of the
            # median of distances for the last thing with a tag?
            # if NOT, then this is the wrong rect, use the tag of the previous
            # is the current distance larger than the width of the thing??
            oN.close = is_in_range(oN.curr_dist, oN.md, self.l_delta_pcnt * oN.md)
            # euclidean distance of the wall histograms
            # observation: this goes negative periodically, apparently
            # on tags that might be in the set of things
            # we don't want. it *often* precedes a tag that has
            # a 'higher' percentage.




            oN.hist_delta = self.get_histogram_delta(self.tracked.get(oN.prev_tag).wall, wall, rectangle)

            oN.is_negative = False
            if Decimal.from_float(oN.hist_delta).is_signed():
                oN.is_negative = True


            # pairwise distance to the previous wall image
            X = self.make_grey_data(self.tracked.get(oN.prev_tag).wall, rectangle)
            Y = self.make_grey_data(wall, rectangle)
            self.set_frame_delta(X, Y)  # compare to current wall

            oN.fd = self._frame_delta  # delta of wall image to current f
            self.fd_mean = np.mean(self._frame_deltas)  # a float,
            self.d_range = self.f_delta_pcnt * self.fd_mean  # percentage of px difference

            oN.in_range = False
            if is_in_range(oN.fd, self.fd_mean, self.d_range):
                oN.in_range = True




            if is_in_range(oN.curr_dist, oN.md, .10 * oN.md):
                # 352 momentary change in focus
                self.print_frame(oN, "!N:")

            if oN.is_inside and not oN.is_negative:
                # 1171 continuations
                self.print_frame(oN, "   ")

            # ARE THESE 'SHADOWS'? PAUSE PLAYBACK
            if not is_in_range(oN.curr_dist, oN.md, .10 * oN.md) and not oN.is_inside:
                # 17, RANDOM GLINTS AND SHADOWS:
                # MAY OR MAY NOT
                # FOLLOW X1, !N
                # DUPLICATE X1, !N
                # not inside rect and doesn't match, but close
                # -- must label
                self.print_frame(oN, "CN:")
            elif not is_in_range(oN.curr_dist, oN.md, .10 * oN.md) and oN.is_negative:
                # 21, RANDOM not inside rect and doesn't match
                # SHADOW, GLINTS AND *NEW* ITEMS
                # change conditional to see range in
                # relation to prev_item.
                # -- must label
                self.print_frame(oN, "XN:")

            labeled.append(oN)

        if not labeled:                                             # nothing in cache.
            # f 0
            o = FrameObjekt.create(self.f_id)
            o.rect = rectangle          # the current rectangle is my rect.
            o.wall = wall               # the current wall is my wall.
            o.ml = self._ml
            o.is_inside = is_inside(o.ml, o.rect)
            o.close = is_in_range(o.curr_dist, o.md, self.l_delta_pcnt * o.md)
            o.hist_delta = None
            o.skip = True
            o.tag = o.create_tag(self.f_id)
            self.print_frame(o, "N0:")
            labeled.append(o)

        return labeled

    def get_histogram_delta(self, frame, wall, rectangle):
        from src.cam.Showxating.ShowxatingHistogramPlugin import ShowxatingHistogramPlugin

        hist_plugin = ShowxatingHistogramPlugin()
        hist_plugin.plugin_name = 'histogramPlugin'
        hist_plugin.get_config()
        hist_plugin.f_id = self.f_id
        hist_plugin._kz = (3, 3)  # self.kernel_sz
        hist_plugin.library = 'cv'  # TODO: add to configurable
        hist_plugin.rectangle = rectangle
        hist_plugin.compare_method = cv.HISTCMP_CORREL
        hist_plugin.norm_type = cv.NORM_MINMAX

        f_hist = hist_plugin.get_histogram(frame, rectangle)
        w_hist = hist_plugin.get_histogram(wall, rectangle)

        hist_plugin.normalize_channels(f_hist)
        hist_plugin.normalize_channels(w_hist)

        return hist_plugin.compare_hist(f_hist, w_hist)

    def track_objects(self, f_id, frame, contour, hierarchy, wall, rectangle):
        """
        LEARNINGS:
        Not all moving things should be tracked; this is very sensitive to minute changes in light, and not all movement is relevant.
        Not all tracked things move; Consider flashing lights or any localized, repetitive change. Tracking seizes!
        Objects can suddenly appear or appear to change *size* if the frame drags due to network latency. Back referencing frames needs a cache.
        """

        self.f_id = f_id
        self.contour_id = str(uuid.uuid4()).split('-')[0]

        self._ml = self.get_mean_location(contour)       # find the mean location of this target

        for o in self.label_locations(frame, wall, rectangle):  # go label this location as either NEW, PREV or INITIAL.

            o.contour = contour                          # this is one of a group of sorted contours; it could be the first or the smallest. first is largest.
            o.hierarchy = hierarchy                      # unused for now, will be i of an enumeration

            if not o.prev_tag:
                o.prev_tag = o.tag

            self.tracked[o.tag] = o

        self.preen_cache()

        return self.tracked

