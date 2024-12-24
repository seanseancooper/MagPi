import uuid

import cv2 as cv
import numpy as np
from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from sklearn.metrics import euclidean_distances, pairwise_distances
from sklearn.metrics.pairwise import paired_distances

from src.cam.Showxating.lib.utils import in_range, is_inside, getAggregatedRect, getRectsFromContours
from src.config import readConfig

import logging
cam_logger = logging.getLogger('cam_logger')


class FrameObjektTracker:

    def __init__(self):
        super().__init__()
        self.f_id = 0                       # current frame id
        self.config = {}

        self.f_limit = 2                    # hyperparameter: max age of frames in o_cache_map.
        self.f_delta_pcnt = 0.50            # hyperparameter: 0..1 percentage of delta between the current and previous frames over all pixels in frame
        self.l_delta_pcnt = 0.50            # hyperparameter: 0..1 percentage of delta between the current and previous mean locations
        self.contour_limit = None           # number of contours evaluated by plugin in each pass
        self.contours = None                # ????
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
        readConfig('cam.json', self.config)

        try:
            self.f_limit = int(self.config['TRACKER'].get('f_limit', 1))
            if self.f_limit < 1:
                self.f_limit = 1

            self.f_delta_pcnt = float(self.config['TRACKER']['f_delta_pcnt'])
            if self.f_delta_pcnt > 1.0:
                print(f'bad f_delta_pcnt: (should be <= 1.0)')
                exit(1)

            self.l_delta_pcnt = float(self.config['TRACKER']['l_delta_pcnt'])
            if self.l_delta_pcnt > 1.0:
                print(f'bad l_delta_pcnt: (should be <= 1.0)')
                exit(1)

            self.contour_limit = int(self.config['TRACKER'].get('contour_limit', None))
            if self.contour_limit == 0:
                print(f'contour_limit warning: (contour_limit should be > 0 or "None" for all contours)')

        except ValueError:
            print(f'bad value: (should be numeric)')
            exit(1)

    def preen_cache(self):
        aged_o = [o for o in self.tracked if self.tracked.get(o).f_id < (self.f_id - self.f_limit)]
        [self.tracked.pop(o) for o in aged_o]

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

            self._frame_MSE = np.sum((X.astype("float") - Y.astype("float")) ** 2)
            self._frame_MSE /= float(X.shape[0] * Y.shape[1])

            from skimage.metrics import structural_similarity as ssim
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
        print(f"{str(self.f_id)}\t{origin}{str(o.tag)}\t"
              # f"INSIDE: {str(o.is_inside).ljust(2, ' ')}\t"
              f"CLOSE: {str(o.close).ljust(1, ' ')}\t"
              f"dist: {str(o.curr_dist.__format__('.4f')).ljust(3, ' ')}\t"
              f"md: {str(o.md.__format__('.4f')).ljust(3, ' ')}\t"
              # f"ML: {str(o.ml)}\trect:{str(o.rect).ljust(10, ' ')}\t"
              # f"fd: {str(self.fd_mean.__format__('.4f')).ljust(10, ' ')}\tmse: {str(self._frame_MSE.__format__('.4f')).ljust(10, ' ')}\tssim: {str(self._frame_SSIM.__format__('.4f')).ljust(10, ' ')}"
        )

    def get_mean_location(self, contours):
        ''' aka 'basically where it is' get the average location of all the contours in the frame '''
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

            o1.ml = self._ml
            o1.isNew = True

            o1.contour_id = self.contour_id
            # contours are sorted, first p_ml is 'largest' contour
            o1.distances = euclidean_distances(np.array([self._ml], dtype=int), np.array([p_ml[0]], dtype=int).reshape(1, -1))
            o1.md = np.mean(o1.distances)
            # popitem removes; is that really what we want?
            o1.prev_tag = str(list(self.tracked.keys())[0])                 # find the last thing with a tag, if not expired already ("when?", f_limit)
            o1.curr_dist = int(o1.distances[0])

            o1.rect = self.tracked.get(o1.prev_tag).rect                    # "where?" was the last thing with a tag? (p_ml)
            o1.is_inside = is_inside(o1.ml, o1.rect)                        # is the current ml inside the bounding rect of the last thing with a tag?

            off = self.l_delta_pcnt * o1.md                                 # did o1 suddenly appear?
            o1.close = in_range(o1.curr_dist, o1.md, off)                   # is the current distance within a range of the median of distances for the last thing with a tag?


            o1.tag = o1.create_tag(self.f_id)  # NEW TAG

            self.print_frame(o1, "N1:")
            labeled.append(o1)

        if len(p_ml) > 1:
            o = FrameObjekt.create(self.f_id)

            o.contour_id = self.contour_id

            o.ml = self._ml
            o.isNew = False  # could be reset!
            # get the mean location of the distances identified in the previous frame
            o.distances = [euclidean_distances(np.array([self._ml], dtype=int), np.array([p_ml[j]], dtype=int).reshape(1, -1)) for j in np.arange(len(p_ml)) if p_ml[j] is not None]
            o.md = np.mean(o.distances)

            idx = np.argmin(o.distances)                              # the item in the array representing the minimum euclidean distance to the current location
            o.prev_tag = str(list(self.tracked.keys())[idx])          # its' tag
            o.curr_dist = float(o.distances[idx])                     # distance from last location

            o.rect = self.tracked.get(o.prev_tag).rect

            o.is_inside = is_inside(o.ml, o.rect)                     # *MIGHT* BE TRUE
            off = self.l_delta_pcnt * o.md
            o.close = in_range(o.curr_dist, o.md, off)

            o.tag = f"{self.f_id}_{o.prev_tag.split('_')[1]}"

            # self.print_frame(o, "   ")
            labeled.append(o)

        if not labeled:
            # f 0
            o = FrameObjekt.create(self.f_id)
            o.ml = self._ml
            o.skip = True
            self.print_frame(o, "N0:")
            labeled.append(o)

        return labeled

    def get_histograms(self, frame, wall, rectangle, metric):
        from src.cam.Showxating.ShowxatingHistogramPlugin import ShowxatingHistogramPlugin

        hist_plugin = ShowxatingHistogramPlugin()
        hist_plugin.plugin_name = 'histogramPlugin'
        hist_plugin.get_config()
        hist_plugin.f_id = self.f_id
        hist_plugin._kz = (3,3) # self.kernel_sz
        hist_plugin.library = 'cv'  # TODO: add to configurable
        hist_plugin.greyscale_frame = self.greyscale_frame
        hist_plugin.rectangle = rectangle

        # gaussian kernel pre processing
        f_hist = hist_plugin.make_histogram(frame, rectangle)
        w_hist = hist_plugin.make_histogram(wall, rectangle)

        if self.config['PLUGIN'].get('color_histograms', False):
            dists = hist_plugin.compare_hist(f_hist, w_hist, metric=metric)
        else:
            dists = hist_plugin.compare_hist(f_hist['greyscale'], w_hist['greyscale'], metric=metric)

        return dists

    def track_objects(self, f_id, frame, contour, hierarchy, wall, rectangle):
        """
        LEARNINGS:
        Not all moving things should be tracked; this is very sensitive to minute changes in light, and not all movement is relevant.
        Not all tracked things move; Consider flashing lights or any localized, repetitive change. Tracking seizes!
        Objects can suddenly appear or appear to change *size* if the frame drags due to network latency. Back referencing frames needs a cache.
        """
        self.f_id = f_id
        self.contours = contour
        self.contour_id = str(uuid.uuid4()).split('-')[0]
        distances = self.get_histograms(frame, wall, rectangle, 'euclidean')

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
                X = self.make_grey_data(prev_wall, rectangle)
                Y = self.make_grey_data(wall, rectangle)
                self.set_frame_delta(X, Y)                                  # compare to current wall

                o.fd = self._frame_delta                                    # delta of wall image to current f
                self.fd_mean = np.mean(self._frame_deltas)                  # a float,
                self.d_range = self.f_delta_pcnt * self.fd_mean             # percentage of px difference

                # does this f match the previous f
                # and thus the previous tag? make an
                # evaluation based on delta between frames.
                # if not in_range(o.fd, self.fd_mean, self.d_range):
                #     # o.tag = f"{self.f_id}_{o.prev_tag.split('_')[1]}"
                #     o.tag = o.create_tag(self.f_id)

            else:
                o.tag = o.create_tag(self.f_id)

            self.tracked[o.tag] = o

        self.preen_cache()

        return self.tracked

