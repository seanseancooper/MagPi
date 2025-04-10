from datetime import datetime
import numpy as np
import uuid


class FrameObjekt:

    def __init__(self, f_id):

        # features
        self.f_id = f_id                                                # frame id when created.
        self.created = datetime.now()                                   # not used yet
        self.tag = None                                                 # [deprecate this in favor of using the f_id, portable] string unique identifier for this frame
        self.prev_tag = None                                            # [string: object tracking] tag of nearest FrameObjekt from the previous frame

        self.avg_loc = np.array([0, 0], dtype=np.int32)                 # [tuple {x,y}: object segmentation] mean x, y location of *this* contour
        self.rect = None                                                # [tuple {x, y, w, h}: object segmentation] bounding rects of contours in this frame
        self.lat = 0.0                                                  # latitude
        self.lon = 0.0                                                  # longitude

        self.frame_rate = 0.0
        self.frame_period = 0.0
        self.frame_shape = None                                             # [ndarray: container] shape of current frame

        # "unused" features
        self.contours = None                                            # [tuple of ndarray(n, 1, 2): object tracking] ALL contours in this frame

        self.distance = 0.0                                             # [0.0: reporting] euclidean_distance wrt previous frame analysis area
        self.distances = np.zeros(shape=[1, 1], dtype=np.float64)       # [list([1,1]): object location] of previous euclidean_distances wrt previous mean x, y locations.
        self.distances_mean = 0.0
        self.delta_range = 0.0
        self.hist_delta = 0.0                                           # [0.0: reporting] histogram distance wrt previous frame analysis area

        self.f_hist = None                                              # histogram of frame
        self.w_hist = None                                              # histogram of wall, filled in by FrameObjectTracker
        self.wall = None                                                # [ndarray: container] image of processed area in this frame

        # 'deprecated' booleans
        self.close = None                                               # [boolean: reporting] is this mean location with the bounds of the contour?
        self.inside_rect = None
        self.hist_pass = None                                           # filled during offline processing

        self.ssim_pass = None
        self.wall_pass = None
        self.mse_pass = None
        self.cosim_pass = None

    @staticmethod
    def create(f_id):
        return FrameObjekt(f_id)

    @staticmethod
    def create_tag(f_id):
        tag = f"{f_id}_{str(uuid.uuid4())}"
        return tag

    def get(self):
        return {'f_id'              : self.f_id,
                'tag'               : str(self.tag),
                'avg_loc'           : str(self.avg_loc),    # self.avg_loc.tolist()
                'rect'              : str(self.rect),       # a string???
                'lat'               : self.lat,
                'lon'               : self.lon,
                'frame_rate'        : self.frame_rate,
                'frame_period'      : self.frame_period,

                'distance'      : self.distance,
                'distances_mean': self.distances_mean,
                'close'         : self.close,
                'inside_rect'   : self.inside_rect is True,
                'hist_pass'     : self.hist_pass,
                'wall_pass'     : self.wall_pass,
        }
