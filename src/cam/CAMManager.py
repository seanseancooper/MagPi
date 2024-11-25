import threading
import logging
from flask import json

from src.cam.Showxating.ShowxatingBlackviewPlugin import ShowxatingBlackviewPlugin
from src.config.__init__ import readConfig

cam_logger = logging.getLogger('cam_logger')


class CAMManager(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}

        self.plugin = None

        self.plugin_args_capture_src = None
        self.plugin_args_capture_frame_rate = None
        self.plugin_args_capture_width = None
        self.plugin_args_capture_height = None

        self.multibutton = {}
        self.statistics = {}                    # not used!

    def __str__(self):
        return {"CAMManager": str(self.config)}

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.multibutton = {
            "OFF": self.config['MULTIBUTTON_OFF'],
            "SYM": self.config['MULTIBUTTON_SYM'],
            "ANA": self.config['MULTIBUTTON_ANA'],
            "ALL": self.config['MULTIBUTTON_ALL']
        }

    def init_plugin(self, plugin, direction):

        self.plugin = plugin()

        # configure ShowxatingPlugin
        self.plugin.plugin_name = self.config['PLUGIN_NAME']
        self.plugin.plugin_args_capture_src = self.cam_direction(direction)
        self.plugin.get_config()
        self.plugin.config_tracker()

    def cam_direction(self, direction):
        if not self.config['FORWARD_TEST_URL'] > "":
            return self.config[direction.upper() + '_VIDEO_URL']
        return self.config['FORWARD_TEST_URL']

    def cam_reload(self, direction):

        self.plugin.plugin_args_capture_src = self.cam_direction(direction)

        for frame in self.plugin.plugin_capture.run():
            self.plugin.tracker.flush_cache()

            def noop(f):
                return f

            noop(frame)
            break

        self.plugin.streamservice.reload(self.cam_direction(direction))

    def cam_multibutton(self, mode):
        """ set mode of ShowxatingBlackviewPlugin """
        try:
            self.plugin.has_symbols, self.plugin.has_analysis = self.multibutton[mode]
        except KeyError:
            pass

    def cam_twiddle(self, field, value):
        # TODO: FIX BRITTLE CODE!

        plugin_value_types = {
            "self.plugin.krnl"          : "int",
            "self.plugin.threshold"     : "float",
            "self.plugin.threshold_hold": "bool",
            "self.plugin.mediapipe"     : "bool",
        }

        if field == 'crop':
            json_value = json.loads(value)
            self.plugin._max_height = slice(int(json_value['y']), int(json_value['h']), None)
            self.plugin._max_width = slice(int(json_value['x']), int(json_value['w']), None)

        if field == 'krnl':
            self.plugin.krnl = int(value)
            self.plugin.show_krnl_grid = True

        if field == 'threshold':
            self.plugin.threshold = float(value)
            self.plugin.show_threshold = True

        if field == 'threshold_hold':
            self.plugin.threshold_hold = (value == 'true')

        if field == 'mediapipe':
            self.plugin.mediapipe = (value == 'true')

        if field == 'f_limit':
            self.plugin.tracker.f_limit = int(value)

        if field == 'frame_delta':
            self.plugin.tracker.frame_delta = float(value)

        if field == 'frm_delta_pcnt':
            self.plugin.tracker.frm_delta_pcnt = float(value)

        return True

    def tracker_twiddle(self, field, value):
        pass

    def stop(self):
        pass

    def run(self):
        self.init_plugin(ShowxatingBlackviewPlugin, "FORE")
        self.plugin.run()

