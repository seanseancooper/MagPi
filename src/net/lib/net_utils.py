from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from datetime import datetime
import numpy as np


def frameobjekt_to_dict(f_obj):
    """Convert FrameObjekt to a serializable dictionary."""
    return {
        'f_id'              : f_obj.f_id,
        'created'           : f_obj.created.isoformat(),
        'tag'               : f_obj.tag,

        # 'contours'        : f_obj.contours.tolist() if f_obj.contours is not None else None,
        # 'hierarchy'       : f_obj.hierarchy.tolist() if f_obj.hierarchy is not None else None,
        # 'prev_tag'        : f_obj.prev_tag,
        # 'contour_id'      : f_obj.contour_id,
        'curr_dist'         : f_obj.curr_dist,
        # 'distances'       : f_obj.distances.tolist(),
        'fd'                : f_obj.fd,
        'fd_mean'           : f_obj.fd_mean,
        # 'delta_range'     : f_obj.delta_range,
        'hist_delta'        : f_obj.hist_delta,
        # 'f_hist'          : f_obj.f_hist,
        'w_hist'            : f_obj.w_hist.tolist() if f_obj.w_hist is not None else [],  # DBUG this needs to be an array, so this isn't the right way to process this
        'rect'              : f_obj.rect,
        'avg_loc'           : f_obj.avg_loc.tolist(),
        'dist_mean'         : f_obj.dist_mean,
        # 'wall'            : f_obj.wall.tolist() if f_obj.wall is not None else None,
        'lat'               : f_obj.lat,
        'lon'               : f_obj.lon,
        'close'             : str(f_obj.close),
        'inside_rect'       : str(f_obj.inside_rect),
        'hist_pass'         : str(f_obj.hist_pass),
        'wall_pass'         : str(f_obj.wall_pass)
    }


def dict_to_frameobjekt(data):
    """Convert dictionary back to FrameObjekt."""
    frame_obj = FrameObjekt.create(data['f_id'])
    frame_obj.f_id = data['f_id']
    frame_obj.created = datetime.fromisoformat(data['created'])
    frame_obj.tag = data['tag']

    # frame_obj.contours = np.array(data['contours']) if data['contours'] is not None else None
    # frame_obj.hierarchy = np.array(data['hierarchy']) if data['hierarchy'] is not None else None
    # frame_obj.prev_tag = data['prev_tag']
    # frame_obj.contour_id = data['contour_id']
    frame_obj.curr_dist = data['curr_dist']
    # frame_obj.distances = np.array(data['distances'])
    frame_obj.fd = data['fd']
    frame_obj.fd_mean = data['fd_mean']
    # frame_obj.delta_range = data['delta_range']
    frame_obj.hist_delta = data['hist_delta']
    # frame_obj.f_hist = data['f_hist']
    frame_obj.w_hist = data['w_hist']  # DBUG this needed to be an array, so this isn't the right way to process this
    frame_obj.rect = tuple(data['rect']) if data['rect'] else None
    frame_obj.avg_loc = np.array(data['avg_loc'])
    frame_obj.dist_mean = data['dist_mean']
    # frame_obj.wall = np.array(data['wall']) if data['wall'] is not None else None
    frame_obj.lat = data['lat']
    frame_obj.lon = data['lon']
    frame_obj.close = data['close']
    frame_obj.inside_rect = data['inside_rect']
    frame_obj.hist_pass = data['hist_pass']
    frame_obj.wall_pass = data['wall_pass']
    return frame_obj


class WifiWorkerParser:

    def __init__(self, data):
        self.data = data
        self.worker_data = {}
        self.signal_data = {}
        self.signal_test = {}
        self._parse()

    def _parse(self):
        self.worker_data = self.data
        self.signal_data = self.worker_data['signal_cache']
        self.signal_test = self.worker_data['results']

        self.worker_data.pop('signal_cache')    # remove the signal cache
        self.worker_data.pop('results')         # remove the tests

    def get_worker_data(self):
        return self.worker_data

    def get_signal_data(self):
        return self.signal_data

    def get_test_data(self):
        return self.signal_test

