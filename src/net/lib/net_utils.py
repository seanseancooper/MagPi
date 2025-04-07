from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
from datetime import datetime
import numpy as np


def frameobjekt_to_dict(f_obj):
    """Convert FrameObjekt to a serializable dictionary."""
    return {
        'f_id'              : f_obj.f_id,
        'created'           : f_obj.created.isoformat(),
        'tag'               : f_obj.tag,
        'f_shape'           : f_obj.f_shape,

        # 'contours'        : f_obj.contours.tolist() if f_obj.contours is not None else None,
        # 'hierarchy'       : f_obj.hierarchy.tolist() if f_obj.hierarchy is not None else None,
        # 'prev_tag'        : f_obj.prev_tag,
        # 'contour_id'      : f_obj.contour_id,
        'curr_dist'         : f_obj.curr_dist,
        # 'distances'       : f_obj.distances.tolist(),
        'fd'                : f_obj.distance,
        'fd_mean'           : f_obj.distances_mean,
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
        'close'             : bool(f_obj.close),
        'inside_rect'       : bool(f_obj.inside_rect),

        'hist_pass'         : bool(f_obj.hist_pass),
        'ssim_pass'         : bool(f_obj.ssim_pass),

        'wall_pass'         : bool(f_obj.wall_pass),
        'mse_pass'          : bool(f_obj.mse_pass),
        'cosim_pass'        : bool(f_obj.cosim_pass),

    }


def dict_to_frameobjekt(data):
    """Convert dictionary back to FrameObjekt."""
    frame_obj = FrameObjekt.create(data['f_id'])
    frame_obj.f_id = data['f_id']
    frame_obj.f_shape = tuple(data['f_shape'])
    frame_obj.created = datetime.fromisoformat(data['created'])
    frame_obj.tag = data['tag']

    # frame_obj.contours = np.array(data['contours']) if data['contours'] is not None else None
    # frame_obj.hierarchy = np.array(data['hierarchy']) if data['hierarchy'] is not None else None
    # frame_obj.prev_tag = data['prev_tag']
    # frame_obj.contour_id = data['contour_id']
    frame_obj.curr_dist = data['curr_dist']
    # frame_obj.distances = np.array(data['distances'])
    frame_obj.distance = data['fd']
    frame_obj.distances_mean = data['fd_mean']
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
    frame_obj.close = bool(data['close'])
    frame_obj.inside_rect = bool(data['inside_rect'])
    frame_obj.hist_pass = bool(data['hist_pass'])
    frame_obj.ssim_pass = bool(data['ssim_pass'])

    frame_obj.wall_pass = bool(data['wall_pass'])
    frame_obj.mse_pass = bool(data['mse_pass'])
    frame_obj.cosim_pass = bool(data['cosim_pass'])
    return frame_obj


# class WifiWorkerParser:
#
#     def __init__(self, data):
#         self.data = data
#         self.worker_data = {}
#         self.signal_data = {}
#         self.signal_test = {}
#         self._parse()
#
#     def _parse(self):
#         self.worker_data = self.data
#
#         # transform created, updated representations to have a timezone
#         # worker_created_time = datetime.strptime(worker_data['created'], self.config['DATETIME_FORMAT'])
#         # worker_data['created'] = worker_created_time.astimezone().isoformat()
#         #
#         # worker_updated_time = datetime.strptime(worker_data['updated'], self.config['DATETIME_FORMAT'])
#         # worker_data['updated'] = worker_updated_time.astimezone().isoformat()
#
#         self.signal_data = [_ for _ in self.worker_data['signal_cache']]
#         # self.signal_test = self.worker_data['results']
#
#         # self.worker_data.pop('signal_cache')    # remove the signal cache
#         # self.worker_data.pop('results')         # remove the tests
#
#     def get_worker_data(self):
#         return self.worker_data
#
#     def get_signal_data(self):
#         return self.signal_data
#
#     def get_test_data(self):
#         return self.signal_test

class WifiWorkerParser:

    def __init__(self, data):
        self.data = data

    def get_worker_data(self):
        return {
            "id"        : self.data["id"],
            "SSID"      : self.data["SSID"],
            "BSSID"     : self.data["BSSID"],
            "created"   : self.data["created"],
            "updated"   : self.data["updated"],
            "elapsed"   : self.data["elapsed"],
            "Vendor"    : self.data["Vendor"],
            "Channel"   : self.data["Channel"],
            "Frequency" : self.data["Frequency"],
            "Signal"    : self.data["Signal"],
            "Quality"   : self.data["Quality"],
            "Encryption": self.data["Encryption"],
            "is_mute"   : self.data["is_mute"],
            "tracked"   : self.data["tracked"],
            "tests"     : self.data.get("tests", [])
        }

    def get_signal_data(self):
        return [
            {
                "created"  : signal["created"],
                "id"       : signal["id"],
                "worker_id": signal["worker_id"],
                "lat"      : signal["lat"],
                "lon"      : signal["lon"],
                "sgnl"     : signal["sgnl"]
            }
            for signal in self.data.get("signal_cache", [0])
        ]


