from datetime import datetime
import numpy as np
import uuid


class FrameObjekt:

    def __init__(self, f_id):

        # metadata
        self.f_id = f_id                                                # frame 'id'
        self.created = datetime.now()                                   # when created.
        self.tag = None                                                 # [deprecate this in favor of using the f_id, portable] string unique identifier for this frame
        self.prev_tag = None                                            # [string: object tracking] tag of nearest FrameObjekt from the previous frame

        # features
        self.avg_loc = np.array([0, 0], dtype=np.int32)                 # [tuple {x,y}: object segmentation] mean x, y location of *this* contour
        self.rect = None                                                # [tuple {x, y, w, h}: object segmentation] bounding rects of contours in this frame
        self.lat = 0.0                                                  # latitude
        self.lon = 0.0                                                  # longitude

        # post-processed features
        self.frame_rate = 0.0
        self.frame_period = 0.0
        self.frame_shape = None                                         # [ndarray: container] shape of current frame

        self.max_width = None
        self.max_height = None
        self.wall = None                                                # [ndarray: container] image of processed area in this frame

        self.ssim_pass = None
        self.hist_pass = None                                           # filled during offline processing
        self.wall_pass = None
        self.mse_pass = None
        self.cosim_pass = None

        # features not passed to post processing, used internally.
        self.contours = None                                            # [tuple of ndarray(n, 1, 2): object tracking] ALL contours in this frame

        self.distance = 0.0                                             # [0.0: reporting] euclidean_distance wrt previous frame analysis area
        self.distances = np.zeros(shape=[1, 1], dtype=np.float64)       # [list([1,1]): object location] of previous euclidean_distances wrt previous mean x, y locations.
        self.distances_mean = 0.0
        self.delta_range = 0.0
        self.hist_delta = 0.0                                           # [0.0: reporting] histogram distance wrt previous frame analysis area

        # internal boolean values
        self.close = None                                               # [boolean: reporting] is this mean location with the bounds of the contour?
        self.inside = None

    @staticmethod
    def frameobjekt_to_dict(f):
        """Convert FrameObjekt to a serializable dictionary for MQ/FrameObjektEncode"""
        return {
            'f_id'       : f.f_id,
            'frame_shape': f.frame_shape,
            'created'    : f.created.isoformat(),
            'tag'        : f.tag,
            'prev_tag'   : f.prev_tag,

            'rect'       : f.rect,
            'avg_loc'    : f.avg_loc.tolist(),
            'lat'        : f.lat,
            'lon'        : f.lon,
        }

    @staticmethod
    def dict_to_frameobjekt(d):
        """Convert dictionary back to FrameObjekt for MQ"""
        frame_obj = FrameObjekt.create(d['f_id'])
        frame_obj.f_id = d['f_id']
        frame_obj.frame_shape = tuple(d['frame_shape'])
        frame_obj.created = datetime.fromisoformat(d['created'])
        frame_obj.tag = d['tag']
        frame_obj.prev_tag = d['prev_tag']

        frame_obj.rect = tuple(d['rect']) if d['rect'] else None
        frame_obj.avg_loc = np.array(d['avg_loc'])
        frame_obj.lat = d['lat']
        frame_obj.lon = d['lon']

        return frame_obj

    @staticmethod
    def create(f_id):
        return FrameObjekt(f_id)

    @staticmethod
    def create_tag(f_id):
        tag = f"{f_id}_{str(uuid.uuid4())}"
        return tag

    def get(self):
        # metadata and post-processed features.
        return {
                'f_id'              : self.f_id,
                'created'           : str(self.created.isoformat()),
                'tag'               : str(self.tag),

                'avg_loc'           : str(self.avg_loc),    # self.avg_loc.tolist()
                'rect'              : str(self.rect),       # a string???
                'lat'               : self.lat,
                'lon'               : self.lon,

                'frame_rate'        : self.frame_rate,
                'frame_period'      : self.frame_period,
                'frame_shape'       : self.frame_shape,

                'ssim_pass'         : self.ssim_pass,
                'hist_pass'         : self.hist_pass,
                'wall_pass'         : self.wall_pass,
                'mse_pass'          : self.mse_pass,
                'cosim_pass'        : self.cosim_pass,
        }
