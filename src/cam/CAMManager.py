import threading
import logging
from flask import json

from src.cam.Showxating.lib.ImageWriter import ImageWriter
from src.cam.Showxating.ShowxatingBlackviewPlugin import ShowxatingBlackviewPlugin
from src.config.__init__ import readConfig

cam_logger = logging.getLogger('cam_logger')


class CAMManager(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}

        self.plugin_capture = None
        self.statistics = {}

        self.plugin_name = None
        self.plugin_args_capture_src = None
        self.plugin_args_capture_frame_rate = None
        self.plugin_args_capture_width = None
        self.plugin_args_capture_height = None

        #TODO 'snap' config needs to move to config
        #TODO create/use a namespace for "plugins"; auto-discoover them.
        self.plugin_config = {
            "asset_classes"               : {},
            "capture_is_image"            : False,
            "capture_is_null"             : False,
            "capture_output_log_stats"    : False,
            "capture_output_show_stats"   : False,
            "capture_param_capture_height": 480,
            "capture_param_capture_width" : 702,
            "display_proc_stats"          : False,
            "display_rect_stats"          : False,
            "log_proc_stats"              : False,
            "log_rect_stats"              : False,
            "next_plugin_class"           : "",
            "next_plugin_name"            : "",
            "plugin_cv_color"             : "0, 0, 0",
            "plugin_displays"             : False,
            "plugin_process_copies"       : False,
            "plugin_process_frames"       : False,
            "write_mp4"                   : False
        }

        self.plugin = None


    def __str__(self):
        return {"CAMManager": str(self.config)}

    def configure(self, config_file):

        if not config_file:
            exit(1)

        readConfig(config_file, self.config)


    def init_camera(self, direction):

        URL = self.cam_direction(direction)

        import atexit

        def plugin_stops():
            cam_logger.info(f"{self.plugin_name} plugin stopped")

        atexit.register(plugin_stops)
        self.plugin = ShowxatingBlackviewPlugin()
        self.plugin.plugin_name = self.config['PLUGIN_NAME']

        self.plugin.plugin_args_capture_src = URL
        #DBUG: this shouldn't be hardcoded
        # For webcams and many other connected cameras,
        # you have to calculate the frames per second manually.
        # You can read a certain number of frames from the video and see how much
        # time has elapsed to calculate frames per second. I do this in the capture!

        self.plugin.plugin_args_capture_frame_rate = 10
        self.plugin.plugin_args_capture_width = 702
        self.plugin.plugin_args_capture_height = 480

    def cam_direction(self, direction):
        #TODO: return self.config[direction]; note: 'FORE'/'AFT' hardcoded in the button
        if direction == "FORE":
            return self.config.get('FORWARD_TEST_URL', self.config['FORWARD_VIDEO_URL'])
        else:
            return self.config['REVERSE_VIDEO_URL']

    def cam_reload(self, direction):

        URL = self.cam_direction(direction)

        def noop(f):
            return f

        # TODO: which? this is complicated.
        self.plugin.plugin_args_capture_src = URL
        self.plugin.plugin_capture.capture_param_capture_src = URL
        self.plugin.streamservice.requesthandler.src = URL

        for frame in self.plugin.plugin_capture.run():
            self.plugin.tracker.flush_cache()
            noop(frame)
            break

        self.plugin.streamservice.reload(URL)

    def cam_multibutton(self, mode):
        #TODO: multibutton enumeration, less brittle.
        """ set mode of ShowxatingBlackviewPlugin """
        if mode == 'OFF':
            self.plugin.has_symbology = False
            self.plugin.has_analysis = False
        if mode == 'SYM':
            self.plugin.has_symbology = True
            self.plugin.has_analysis = False
        if mode == 'ANA':
            self.plugin.has_symbology = False
            self.plugin.has_analysis = True
        if mode == 'ALL':
            self.plugin.has_symbology = True
            self.plugin.has_analysis = True

    def cam_snap(self):

        # IDEA: Move to plugin. It may be more efficient to
        #  write frames via delegation than by force ('we've got that "B" roll!').

        #TODO: write to imagecache, or create a vector that can later be compared.

        def _snap(frame):
            if frame is not None:
                writer = ImageWriter("CAMManager")
                writer.write("CAM_SNAP", frame)

        # NOFIX: throttle me; I can be overloaded by requests
        #  and crash the capture! [this is for stills, not movies. Not fixing it.]
        for frame in self.plugin.plugin_capture.run():
            _snap(frame)
            break

    def cam_plugin(self, field, value):
        # TODO: FIX BRITTLE CODE!
        if field == 'crop':

            json_value = json.loads(value)
            self.plugin.max_height = slice(int(json_value['y']), int(json_value['h']), None)
            self.plugin.max_width = slice(int(json_value['x']), int(json_value['w']), None)

        if field == 'krnl':
            self.plugin.krnl = int(value)
            self.plugin.show_krnl_grid = True
        if field == 'threshold':
            self.plugin.threshold = float(value)
            self.plugin.show_threshold = True

        if field == 'threshold_hold':
            if value == "True":
                self.plugin.sets_threshold_hold(True)
            else:
                self.plugin.sets_threshold_hold(False)
        if field == 'mediapipe':
            if value == "True":
                self.plugin.sets_mediapipe(True)
            else:
                self.plugin.sets_mediapipe(False)

        if field == 'f_limit':
            self.plugin.tracker.f_limit = int(value)
        if field == 'frame_delta':
            self.plugin.tracker.frame_delta = float(value)
        if field == 'frm_delta_pcnt':
            self.plugin.tracker.frm_delta_pcnt = float(value)

        return "OK"

    def ircam_move(self, command):
        # NOFIX:  deprecated, also brittle! [removing. 'moving a camera'
        # is not a "focus" for this project. Instead, use a 'plugin']

        def makeRequest(url):
            import os
            import socket
            import requests

            try:
                headers = {'user-agent': socket.gethostname() + os.path.basename(__file__).replace('.py', '')}
                response = requests.get(url, headers)
                return response
            except Exception as e:
                cam_logger.error(f"[{__name__}]:Error sending request: {str(e)}")

        URL = f"{self.config['CAM']['IRCAM_HOST']}/cgi-bin/ptzBase.cgi" \
              f"?action=moveDirectly" \
              f"&channel=0" \
              f"&startPoint[0]={command['S_0']}" \
              f"&startPoint[1]={command['S_1']}" \
              f"&endPoint[0]={command['E_0']}" \
              f"&endPoint[1]={command['E_1']}"

        resp = makeRequest(URL)

        if resp:
            return resp
        else:
            return "IRCAM ircam_move error []"

    def stop(self):
            pass

    def run(self):
        self.init_camera("FORE")
        self.plugin.run()
