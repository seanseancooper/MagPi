import uuid
from decimal import Decimal

import cv2 as cv
import numpy as np
from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from sklearn.metrics import euclidean_distances, pairwise_distances, pairwise_kernels
from sklearn.metrics.pairwise import paired_distances, cosine_similarity

from src.cam.Showxating.lib.utils import is_in_range, is_inside, getAggregatedRect, getRectsFromContours
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
            f"\to.avg_loc: {str(o.avg_loc)}"
            f"\to.rect:{str(o.rect).ljust(10, ' ')}"
            
            f"\to.fd_in_range: {o.distance}"
            f"\to.inside_rect: {o.inside_rect}"
            
            f"\to.lat: {o.lat}"
            f"\to.lon: {o.lon}"
            f"\to.close: {o.close}"
            f"\to.SIM_pass: {o.SIM_pass}"
            f"\to.WALL_pass: {o.WALL_pass}"
            
            f"\tcurr_dist: {str(o.curr_dist.__format__('.4f')).ljust(3, ' ')}"
            f"\tdist_mean: {str(o.dist_mean.__format__('.4f')).ljust(3, ' ')}"
            
            f"\tf_EUCs_mean: {str(o.distances_mean.__format__('.4f')).ljust(10, ' ')}"

    )


class FrameObjektTracker:

    def __init__(self):
        super().__init__()
        self.f_id = 0                       # current frame id
        self.config = {}

        self.f_limit = 2                    # max age of frames in o_cache_map.
        self.f_delta_pcnt = 0.50            # 0..1 percentage of delta between current/previous f over all pixels
        self.l_delta_pcnt = 0.50            # 0..1 percentage of delta between the current/previous mean locations

        self.contour_limit = None           # number of contours evaluated by plugin in each pass
        self.contour_id = None              # ????

        self.tracked = {}                   # mapping of FrameObjekts over last 'f_limit' frames.
        self.ml = []                        # list of (x,y) location of contour in self.contours


        # deltas: distance between the current and previous frames
        self.frame_EUC = float()            # euclidean distance between the current and previous frames
        self.frame_EUCs = []                # list of previous euclidean distance over last f_limit frames

        self.frame_COS = float()            # cosine similarity between the current and previous frames
        self.frame_COSs = []                # list of previous...

        self.frame_MSE = float()            # Mean Squared Error between the current and previous frames
        self.frame_MSEs = []                # list of previous...

        self.frame_SSIM = float()           # Structural similarity between the current and previous frames
        self.frame_SSIMs = []               # list of previous...

        self.fd_mean = float()              # InCORRECT!: mean of ALL differences between ALL SEEN frames -- no f_limit.
        self.d_range = 90.00                # offset +/- allowed difference; frm_delta_pcnt * fd_mean

        self.latitude = 0.0                 # current latitude
        self.longitude = 0.0                # current longitude

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
            self.d_range = float(self.config['tracker']['d_range'])

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
            self.frame_EUC = np.mean(pairwise_distances(X, Y))
            self.frame_EUCs.append(self.frame_EUC)

            # return the cosine similarity of X and Y
            self.frame_COS = np.mean(cosine_similarity(X, Y))
            self.frame_COSs.append(self.frame_COS)

            # def MSE(X, Y):
            #     n = X.shape[0] * Y.shape[1]
            #     return 1 / n * np.sum(np.square(X - Y))
            # self._frame_SSIM = MSE(X, Y)

            self.frame_MSE = np.sum((X - Y) ** 2)
            self.frame_MSE /= float(X.shape[0] * Y.shape[1])
            self.frame_MSEs.append(self.frame_MSE)

            from skimage.metrics import structural_similarity as ssim

            self.frame_SSIM = 0.0
            if X.shape[0] > self.config['tracker']['ssim_win_size'] and X.shape[1] > self.config['tracker']['ssim_win_size']:
                # skimage.metrics.structural_similarity(im1, im2, *, win_size=None, gradient=False, data_range=None, channel_axis=None, gaussian_weights=False, full=False, **kwargs)
                (self.frame_SSIM, diff) = ssim(X, Y, win_size=self.config['tracker']['ssim_win_size'], full=True)
                self.frame_SSIMs.append(self.frame_SSIM)

        except Exception as e:
            cam_logger.warning(f'FrameObjektTracker error while setting deltas: {e}  {X.shape}, {Y.shape}')

    def init_o(self, wall, rectangle):
        o = FrameObjekt.create(self.f_id)
        o.rect = rectangle
        # save the wall to the filesystem
        # put the location of the wall in o.wall
        o.wall = wall
        o.f_shape = wall.shape

        get_location(self)
        o.lat = self.latitude
        o.lon = self.longitude

        # oN.contour_id = self.contour_id
        o.avg_loc = self.ml

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

        o.distance = self.frame_EUC  # delta of wall image to current f
        o.distances_mean = np.mean(self.frame_EUCs)

        # is the current distance within a range of the
        # median of distances for the last thing with a tag?
        o.close = is_in_range(o.curr_dist, max(o.rect[2], o.rect[3]), self.l_delta_pcnt * max(o.rect[1], o.rect[2]))

        o.inside_rect = is_inside(o.avg_loc, o.rect)                            # is the ml inside rect?
        o.delta_range = self.f_delta_pcnt * o.distances_mean                    # percentage of px difference

        o.WALL_pass = is_in_range(o.distance, o.distances_mean, self.d_range)
        o.MSE_pass = self.frame_MSE > 0.0
        o.COS_pass = self.frame_COS > 0.0

        o.SIM_pass = self.frame_SSIM > 0.1

    # IDEA: Use a Regression Tree to discern the object's actual label based on frame MSE or SSIM:

    # Scikit-learn provides a linear regression solver, which is demonstrated below.
    #
    # from sklearn.linear_model import LinearRegression
    #
    # # Set parameter to False since intercept is already included in X (constant dim)
    # clf = LinearRegression(fit_intercept=False)
    # clf.fit(X, y)
    # w_sklearn = clf.coef_

    # Scikit-learn also provides an implementation of Regression Trees (and Decision Tree Classifiers).
    # The usage is pretty straight-forward: define the regression tree with the impurity function
    # (and other settings), fit to the training set, and evaluate on any dataset.
    #
    # from sklearn.tree import DecisionTreeRegressor, plot_tree
    #
    # t0 = time.time()
    # tree = DecisionTreeRegressor(
    #         criterion='mse',  # Impurity function = Mean Squared Error (squared loss)
    #         splitter='best',  # Take the best split
    #         max_depth=None,  # Expand the tree to the maximum depth possible
    # )
    # tree.fit(xTrSpiral, yTrSpiral)
    # t1 = time.time()
    #
    # tr_err = np.mean((tree.predict(xTrSpiral) - yTrSpiral) ** 2)
    # te_err = np.mean((tree.predict(xTeSpiral) - yTeSpiral) ** 2)
    #
    # print("Elapsed time: %.2f seconds" % (t1 - t0))
    # print("Training RMSE : %.2f" % tr_err)
    # print("Testing  RMSE : %.2f \n" % te_err)

    # Scikit-learn also provides a tree plotting function, which is again quite simple to use.
    # This is extremely useful while debugging a decision tree.
    # fig, ax = plt.subplots(figsize=(20, 20))
    # _ = plot_tree(tree, ax=ax, precision=2, feature_names=[f'$[\mathbf{{x}}]_{i + 1}$' for i in range(2)], filled=True)

    def label_locations(self, frame, wall, rectangle):
        """ find elements 'tag' by euclidean distance """

        labeled = []
        # get all previous mean_locations (if they exist)
        p_ml = [self.tracked.get(o_tag).avg_loc for o_tag in list(self.tracked.keys())]

        if len(p_ml) == 1:
            # NEW TAG for a different thing; there is only one
            o1 = self.init_o(wall, rectangle)

            o1.distances = euclidean_distances(
                    np.array([self.ml], dtype=int),
                    np.array([p_ml[0]], dtype=int).reshape(1, -1)
            )

            o1.dist_mean = np.mean(o1.distances)

            o1.curr_dist = int(o1.distances[0])
            o1.prev_tag = str(list(self.tracked.keys())[0])

            o1.tag = o1.create_tag(self.f_id)
            self.get_stats(o1, wall, rectangle)

            if o1.inside_rect and o1.SIM_pass:
                # item following f0 item.

                # back reference and merge the rects (n largest) and
                # take a pic of the merged area (use frame)
                # largest area wins.

                o1.tag = f"{self.f_id}_{o1.prev_tag.split('_')[1]}"
                print_frame(o1, "N1:")

            if not o1.close and not o1.SIM_pass and not o1.WALL_pass:
                # NEW 'interstitial' item
                o1.tag = o1.create_tag(self.f_id)
                print_frame(o1, "!N:")

            labeled.append(o1)

        if len(p_ml) > 1:
            # CONTINUATION or NEW?
            oN = self.init_o(wall, rectangle)

            # get the mean location of the distances identified in the previous frame
            oN.distances = [euclidean_distances(
                    np.array([self.ml], dtype=int),
                    np.array([p_ml[j]], dtype=int).reshape(1, -1))
                for j in np.arange(len(p_ml)) if p_ml[j] is not None]

            oN.dist_mean = np.mean(oN.distances)

            # the item in the array representing
            # the minimum euclidean distance to
            # the current location
            idx = np.argmin(oN.distances)

            oN.curr_dist = float(oN.distances[idx])                       # distance from last location
            oN.prev_tag = str(list(self.tracked.keys())[idx])             # 'target' tag; may not be the right tag

            oN.tag = f"{self.f_id}_{oN.prev_tag.split('_')[1]}"
            self.get_stats(oN, wall, rectangle)

            if oN.inside_rect and oN.SIM_pass:
                # continuation of motion
                # back reference and merge the rects (n largest) and take a pic of the merged area
                # largest area wins.

                print_frame(oN, "   ")

            if not oN.close and not oN.SIM_pass:
                # NEW 'interstitial' item
                oN.tag = oN.create_tag(self.f_id)
                print_frame(oN, "XN:")

            labeled.append(oN)

        if not labeled:
            # f 0
            o = self.init_o(wall, rectangle)
            o.close = is_in_range(o.curr_dist, o.dist_mean, self.l_delta_pcnt * o.dist_mean)
            o.inside_rect = is_inside(o.avg_loc, o.rect)
            o.tag = o.create_tag(self.f_id)
            print_frame(o, "N0:")
            labeled.append(o)

        return labeled

    def track_objects(self, f_id, frame, contour, hierarchy, wall, rectangle):
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

        self.ml = get_mean_location(contour)

        for o in self.label_locations(frame, wall, rectangle):

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

