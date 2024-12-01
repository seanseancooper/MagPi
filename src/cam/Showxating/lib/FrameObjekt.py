from datetime import datetime
import numpy as np

class FrameObjekt:

    def __init__(self, f_id):

        # metadata
        self.frame_id = f_id
        self.timestamp = datetime.now()  # not used yet
        self.tag = None
        self.isNew = True
        self.skip = False

        # frame data: features
        self.contours = None   # ALL contours in this frame
        self.hierarchy = None  # ordering of the contours in this frame
        self.prev_tag = None   # tag of nearest FrameObjekt from the previous frame
        self.prev_dist = 0.0   # euclidean_distance wrt previous mean x, y location
        self.distances = np.array([], dtype=np.float64)    # list of previous euclidean_distance wrt previous mean x, y locations.
        self.fd = 0.0          # euclidean_distance wrt previous frame analysis area
        self.rect = None       # bounding rects of contours in this frame
        self.ml = None         # mean x, y location of *this* contour
        self.wall = None       # image of processed area in this frame
        self.close = False

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
