import os.path
import threading
import cv2 as cv
import numpy as np
from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from src.cam.Showxating.lib.utils import getLargestRect, getLargestArea
from sklearn.metrics.pairwise import euclidean_distances, paired_distances
from src.config import CONFIG_PATH, readConfig

import logging


cam_logger = logging.getLogger('cam_logger')


class FrameObjektTracker:

    def __init__(self):
        super().__init__()
        self.f_id = 0               # current frame id

        self.config ={}

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

    def configure(self):
        readConfig(os.path.join(CONFIG_PATH, 'cam.json'), self.config)

        self.f_limit = self.config['TRACKER']['f_limit']
        self.frame_delta = self.config['TRACKER']['frame_delta']
        self.frm_delta_pcnt = self.config['TRACKER']['frm_delta_pcnt']

    def set_frame_delta(self, item, wall, rectangleList):
        wx, wy, ww, wh = getLargestRect(rectangleList)
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

            o = FrameObjekt.create(self.f_id)
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
                    if len(o.distances):
                        idx = np.argmin([x for x in o.distances])
                        o.prev_tag = o.tags[idx]
                        o.prev_dist = o.distances[idx][0][0]
                        cam_logger.debug(f"mean location: {o.ml} aw: {aw} dist: {o.prev_dist} found tag: {o.prev_tag}")
                        located_o.append(o)
                except ValueError: pass
                except AttributeError: pass

        # IDEA: 'compress' located_o; remove duplicated tags

        if len(located_o):

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

        aged_o = [o for o in self.o_cache_map if self.o_cache_map.get(o).frame_id < (f_id - frame_limit)]
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
        """

        self.f_id = f_id
        # current, as of this iteration, view!
        c_cache_map = self.o_cache_map.copy()
        items = list(c_cache_map.keys())

        rx, ry, rw, rh = getLargestRect(rectangleList)
        ra = rw * rh

        (aw, ah, ad) = getLargestArea(areaList)
        aa = aw * ah

        self.get_mean_locations(contours, c_cache_map)

        if len(items):

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
                    d_mean = float(np.mean(self.frame_deltas[-self.f_limit:]))

                    # allowed percentage of changed pixels: width * height * depth / 100 * n
                    d_range = float(((((ry + rh) * (rx + rw)) * mode_wall.shape[2]) / 100) * self.frm_delta_pcnt)
                    lwr = d_mean - d_range
                    upp = d_mean + d_range

                    if not min(lwr, upp) < float(self.frame_delta) < max(lwr, upp):
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

