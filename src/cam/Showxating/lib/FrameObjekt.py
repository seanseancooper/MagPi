from datetime import datetime
import numpy as np

class FrameObjekt:

    def __init__(self, f_id):

        # metadata
        self.f_id = f_id                                # frame id when created.
        self.timestamp = datetime.now()                 # not used yet
        self.tag = None                                 # [deprecate this in favor of using the f_id, portable]   string unique identifier for this frame
        self.isNew = True                               # boolean is the id a NEW id or derived from f[-1]
        self.skip = False                               # [is this logical to have, useful or relevant?] should this frame be skipped in tagging f[+1]

        # frame data: features [remove unused things, deccide when things are used]
        self.contours = None                            # [list: object tracking] ALL contours in this frame
        self.hierarchy = None                           # [list: unused] ordering of the contours in this frame
        self.prev_tag = None                            # [string: object tracking] tag of nearest FrameObjekt from the previous frame
        self.prev_dist = 0.0                            # [float: object tracking] euclidean_distance wrt previous mean x, y location
        self.distances = np.array([], dtype=np.float64) # [list: object location] of previous euclidean_distances wrt previous mean x, y locations.
        self.fd = 0.0                                   # [float: reporting] euclidean_distance wrt previous frame analysis area
        self.rect = None                                # [list: object segmentation] bounding rects of contours in this frame
        self.ml = None                                  # [list: object segmentation] mean x, y location of *this* contour
        self.wall = None                                # [ndarray: container] image of processed area in this frame
        self.close = False                              # [boolean: reporting] is this mean location with the bounds of the contour?

    @staticmethod
    def create(f_id):
        return FrameObjekt(f_id)

    def initial(self, conts, heir, rect, ml, wall):
        self.contours = conts
        self.hierarchy = heir
        self.rect = rect
        self.ml = ml
        self.wall = wall

    def __str__(self):
        return {'f_id' : self.f_id,
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
