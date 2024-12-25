from datetime import datetime
import numpy as np
import uuid

class FrameObjekt:


    def __init__(self, f_id):

        # metadata
        self.f_id = f_id                                    # frame id when created.
        self.timestamp = datetime.now()                     # not used yet
        self.tag = None                                     # [deprecate this in favor of using the f_id, portable] string unique identifier for this frame
        self.isNew = True                                   # boolean is the id a NEW id or derived from f[-1]
        self.skip = False                                   # [is this logical to have, useful or relevant?] should this frame be skipped in tagging f[+1]

        # frame data: features [remove unused things, decide when things are used]
        self.contours = None                                            # [tuple of ndarray(n, 1, 2): object tracking] ALL contours in this frame
        self.hierarchy = None                                           # [ndarray  1, n, 4: unused] ordering of the contours in this frame  (UNUSED)
        self.prev_tag = ''                                              # [string: object tracking] tag of nearest FrameObjekt from the previous frame
        self.contour_id = None                                            # [string: object tracking] id of source contour
        self.curr_dist = 0                                              # [int32: object tracking] euclidean_distance wrt previous mean x, y location
        self.distances = np.zeros(shape=[1, 1], dtype=np.float64)     # [list([1,1]): object location] of previous euclidean_distances wrt previous mean x, y locations.
        self.fd = float()                                               # [float: reporting] euclidean_distance wrt previous frame analysis area
        self.hist_delta = float()                                       # [float: reporting] histogram distance wrt previous frame analysis area
        self.rect = None                                                # [tuple {x, y, w, h}: object segmentation] bounding rects of contours in this frame
        self.ml = np.ndarray(shape=[2,], dtype=np.int32)                # [tuple {x,y}: object segmentation] mean x, y location of *this* contour
        self.md = float()                                               # mean of self.distances
        self.wall = None                                                # [ndarray: container] image of processed area in this frame
        self.close = None                                               # [boolean: reporting] is this mean location with the bounds of the contour?
        self.is_inside = None
        self.is_negative = None
        self.in_range = None


    @staticmethod
    def create(f_id):
        o = FrameObjekt(f_id)
        return o

    def get(self):
        return {'f_id' : self.f_id,
                'tag'      : self.tag,
                'isNew'    : self.isNew,
                'ml'       : self.ml,
                'rect'     : self.rect,
                'skip'     : self.skip,
                'is_inside': self.is_inside,
                }

    @staticmethod
    def create_tag(f_id):
        tag = f"{f_id}_{str(uuid.uuid4())}"
        return tag
