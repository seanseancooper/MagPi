import threading
from datetime import datetime

import cv2 as cv
import numpy as np
from sklearn.metrics.pairwise import euclidean_distances, paired_distances
import logging

from src.lib.instrumentation import timer

cam_logger = logging.getLogger('cam_logger')


class FrameObjektTracker(threading.Thread):

    def __init__(self):
        super().__init__()
        self.f_id = 0               # current frame id

        # hyper parameters
        self.f_limit = 8            # max age of frames in o_cache_map.
        self.frame_delta = 0.0      # euclidean distance between the current and previous frames
        self.frm_delta_pcnt = 1.0   # percentage of delta between the current and previous frames over all pixels in frame

        self.o_cache_map = {}       # map of FrameObjekts data over last f_limit frames.

        #  todo numpy arrays here
        self.tags = []              # previous processed tags
        self.data = []              # FrameObjekt data for tags
        self.c_ml = []              # list of (x,y) location of contour in contours
        self.frame_deltas = []      # list of previous distances over last f_limit frames

    def config(self, f_limit, frame_delta, frm_delta_pcnt):
        self.f_limit = f_limit
        self.frame_delta = frame_delta
        self.frm_delta_pcnt = frm_delta_pcnt

    @staticmethod
    def diff_areas(a, b):
        return a - b

    @staticmethod
    def getLargestRect(rectangleList):
        """ the region of interest """

        def largest_rect(rectangles):
            xs = []
            ys = []
            ws = []
            hs = []
            [(xs.append(d[0]), ys.append(d[1]), ws.append(d[2]), hs.append(d[3])) for d in [r for r in rectangles]]
            return np.min(xs), np.min(ys), np.max(xs) + ws[xs.index(np.max(xs))], np.max(ys) + hs[ys.index(np.max(ys))]

        return largest_rect(rectangleList)

    @staticmethod
    def getLargestArea(areasList):
        """ the *actual* area of what is being analyzed """

        def largest_area(areas):
            # TODO numpy arrays
            ws = []
            hs = []
            ds = []
            [(ws.append(a[0]), hs.append(a[1]), ds.append(a[2])) for a in areas]
            return np.max(ws), np.max(hs), np.max(ds)

        return largest_area(areasList)

    def set_frame_delta(self, item, wall, wall_rectangleList):
        wx, wy, ww, wh = self.getLargestRect(wall_rectangleList)
        self.frame_deltas = [float(o.fd) for o in self.data]

        try:
            distances = paired_distances(cv.cvtColor(wall[wy:wy + wh, wx:wx + ww], cv.COLOR_BGR2GRAY), cv.cvtColor(item[wy:wy + wh, wx:wx + ww], cv.COLOR_BGR2GRAY))
            self.frame_delta = np.mean(distances)
        except Exception as e:
            cam_logger.error(f"Problem setting frame delta: {e}")
        cam_logger.debug(f"frame_delta [fd]: {self.frame_delta}")

    def get_mean_locations(self, contours, cache_map):

        self.tags = [t for t in cache_map.keys()]
        self.data = [d for d in cache_map.values()]

        mean_locs = [c for c in [np.mean(pt, axis=0, dtype=int) for pt in [cnt for cnt in contours]]]
        self.c_ml = [(int(x), int(y)) for [x, y] in [t for [t] in mean_locs]]


    def label_frame_objekts(self, contours, cache_map, aw):
        """ find closest elements 'tag' by location"""

        located_o = []

        for i in np.arange(len(contours)):

            o = FrameObjekt(self.f_id)
            o.contours = contours
            o.ml = self.c_ml[i]  # mean location of *this* contour
            o.tags = list(cache_map.keys())
            p_ml = [cache_map.get(o_key).ml for o_key in o.tags]

            if len(p_ml) > 1:
                # compare to other mean locations

                # for j in np.arange(len(p_ml)):
                #     if p_ml[j] is not None:
                #         o.distances.append(euclidean_distances(np.array([o.ml], dtype=int),
                #                                                np.array([p_ml[j]], dtype=int).reshape(1, -1)))
                #         cam_logger.debug(f"a:{o.ml} to b:{p_ml[j]} distance:{o.distances[-1]} tag:{o.tags[j]}")
                # as list comprehension
                [o.distances.append(euclidean_distances(np.array([o.ml], dtype=int), np.array([p_ml[j]], dtype=int).reshape(1, -1))) for j in np.arange(len(p_ml)) if p_ml[j] is not None]
                # cam_logger.debug(f"a:{o.ml} to b:{p_ml[j]} distance:{o.distances[-1]} tag:{o.tags[j]}")

                try:
                    if len(o.distances) > 0:
                        idx = np.argmin([x for x in o.distances])
                        o.prev_tag = o.tags[idx]
                        o.prev_dist = o.distances[idx][0][0]
                        cam_logger.debug(f"mean location: {o.ml} aw: {aw} dist: {o.prev_dist} found tag: {o.prev_tag}")
                        located_o.append(o)
                except ValueError: pass
                except AttributeError: pass

        # IDEA: 'compress' located_o; remove duplicated tags

        if len(located_o) > 0:

            # TODO list comprehension
            for o in located_o:

                # Comparing distance to width: 'aw' uses
                # gravity & the fixed lens to it's advantage.

                # Mean Squared Error -- already have 'deltas':
                dist_mean = np.mean(o.distances)

                if o.prev_dist < dist_mean:
                    o.tag = f"{self.f_id}_{o.prev_tag.split('_')[1]}"
                else:
                    o.tag = o.create_tag(self.f_id)
                    o.isNew = True

                cam_logger.debug(f"mean of distances for {o.tag}: {dist_mean}")

        else:
            # TRANSIENT
            if o.tag is None:
                o.skip = True
                located_o.append(o)

        return located_o

    def flush_cache(self):
        self.o_cache_map.clear()

    def preen_cache(self, f_id, frame_limit):

        aged_o = [o for o in self.o_cache_map if self.o_cache_map.get(o).frame_id < (int(f_id) - frame_limit)]
        [self.o_cache_map.pop(o) for o in aged_o]

        # delete TRANSIENT (skip = True)
        skips = [o for o in self.o_cache_map if self.o_cache_map.get(o).skip is True]
        [self.o_cache_map.pop(o) for o in skips]

    def track_objects(self, f_id, contours, hierarchy, wall, rectangleList, areaList):
        """
        LEARNINGS:
        Not all moving things should be tracked; this is very sensitive to minute changes in light, and not all movement is relevant.
        Not all tracked things move; Consider flashing lights or any localized, repetitive change. Tracking seizes!
        Objects can suddenly appear or appear to change *size* if the frame drags due to network latency. Back referencing frames needs a cache.

        :param f_id:
        :param contours:
        :param hierarchy:
        :param wall:
        :param rectangleList:
        :param areaList:
        :return:
        """

        self.f_id = f_id
        # current, as of this iteration, view!
        c_cache_map = self.o_cache_map.copy()
        items = list(c_cache_map.keys())

        rx, ry, rw, rh = self.getLargestRect(rectangleList)
        ra = rw * rh

        (aw, ah, ad) = self.getLargestArea(areaList)
        aa = aw * ah

        self.get_mean_locations(contours, c_cache_map)

        if len(items) > 0:

            for o in self.label_frame_objekts(contours, c_cache_map, aw):

                o.wall = wall
                o.ra = ra
                o.aa = aa
                o.hierarchy = hierarchy
                o.rs = rectangleList

                if o.prev_tag is not None:

                    mode_wall = c_cache_map.get(o.prev_tag).wall
                    # cv.imshow(f"mode_wall", mode_wall)
                    # cv.putText(wall, o.tag, o.ml, cv.FONT_HERSHEY_DUPLEX, .45, (255, 255, 255), stroke)

                    self.set_frame_delta(mode_wall, wall, rectangleList)
                    o.fd = self.frame_delta

                    # the mean of all the previous frame deltas
                    d_mean = int(np.mean(self.frame_deltas[-self.f_limit:]))

                    # allowed percentage of changed pixels: width * height * depth / 100 * n
                    d_range = int(((((ry + rh) * (rx + rw)) * mode_wall.shape[2]) / 100) * self.frm_delta_pcnt)

                    if int(self.frame_delta) not in np.arange(d_mean - d_range, d_mean + d_range):
                        # IDEA: perhaps try a different previous 'o' here?
                        #  read tags & distances from 'o' internally.

                        # [cam_logger.info(f"o: {o} {c_cache_map.get(o).ml}") for o in c_cache_map.keys()]

                        o.tag = o.create_tag(self.f_id)
                        cam_logger.info(f"{o.prev_tag} FAILED: {self.frame_delta} rng:{d_range} tag: {o.tag}")

                else:
                    o.tag = o.create_tag(self.f_id)  # NEW

                self.o_cache_map[o.tag] = o
                # cam_logger.info(f"TAGGED: {o.tag} NEW: {o.isNew} SKIP: {o.skip} prev: {o.prev_tag} [{o.prev_dist}]:{o.fd}")

        else:
            # initial entries
            # TODO list comp
            for i in np.arange(len(contours)):
                o = FrameObjekt(self.f_id)
                o.isNew = True
                o.contours = contours
                o.hierarchy = hierarchy
                o.fd = self.frame_delta
                o.aa = aa
                o.ra = ra
                o.rs = rectangleList
                o.ml = self.c_ml[i]
                o.wall = wall

                o.tag = o.create_tag(self.f_id)
                self.o_cache_map[o.tag] = o

        self.preen_cache(self.f_id, self.f_limit)

        return self.o_cache_map


class FrameObjekt:

    def __init__(self, f_id):

        # metadata
        self.frame_id = f_id
        self.timestamp = datetime.now()  # not used yet
        self.tag = None
        self.isNew = False
        self.skip = False

        # frame data: features
        self.contours = None   # ALL contours in this frame
        self.hierarchy = None  # ordering of the contours in this frame
        self.prev_tag = None   # tag of nearest FrameObjekt from the previous frame
        self.prev_dist = 0.0   # euclidean_distance wrt previous mean x, y location
        self.tags = []         # list of previous tags wrt distances
        self.distances = []    # list of previous euclidean_distance wrt previous mean x, y locations.
        self.fd = 0.0          # euclidean_distance wrt previous frame analysis area
        self.aa = 0.0          # analysis area of this frame
        self.ra = 0.0          # largest rectangle area in this frame
        self.rs = None         # bounding rects of contours in this frame
        self.ml = None         # mean x, y location of *this* contour
        self.wall = None       # image of processed area in this frame

    def __str__(self):
        return {'f_id' : self.frame_id,
                'timestamp': self.timestamp,
                'tag'      : self.tag,
                'isNew'    : self.isNew,
                'skip'     : self.skip,
                }

    @staticmethod
    def create_tag(f_id):
        import uuid
        tag = f"{f_id}_{str(uuid.uuid4())}"
        return tag
