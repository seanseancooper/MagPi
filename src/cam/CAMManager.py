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

        self.plugin_capture = None
        self.statistics = {}

        self.plugin_name = None
        self.plugin_args_capture_src = None
        self.plugin_args_capture_frame_rate = None
        self.plugin_args_capture_width = None
        self.plugin_args_capture_height = None

        self.plugin = None

        self.multibutton = {}

    def __str__(self):
        return {"CAMManager": str(self.config)}

    def configure(self, config_file):
        readConfig(config_file, self.config)

        # configure the multibutton
        self.multibutton = {
            "OFF": self.config['MULTIBUTTON_OFF'],
            "SYM": self.config['MULTIBUTTON_SYM'],
            "ANA": self.config['MULTIBUTTON_ANA'],
            "ALL": self.config['MULTIBUTTON_ALL']
        }

    def init_camera(self, direction):

        # import atexit
        #
        # def plugin_stops():
        #     cam_logger.info(f"{self.plugin_name} plugin stopped")
        #
        # atexit.register(plugin_stops)
        self.plugin = ShowxatingBlackviewPlugin()
        self.plugin.plugin_name = self.config['PLUGIN_NAME']

        self.plugin.plugin_args_capture_src = self.cam_direction(direction)
        # TODO: For webcams and many other connected cameras,
        #  you have to calculate the frames per second manually.
        #  You can read a certain number of frames from the video and see how much
        #  time has elapsed to calculate frames per second. I do this in the capture!

        self.plugin.plugin_args_capture_frame_rate = 10
        self.plugin.plugin_args_capture_width = 702
        self.plugin.plugin_args_capture_height = 480

    def cam_direction(self, direction):
        return self.config.get('FORWARD_TEST_URL', [direction.upper() + '_VIDEO_URL'])

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
        """ set mode of ShowxatingBlackviewPlugin """
        try:
            self.plugin._has_symbols, self.plugin._has_analysis = self.multibutton[mode]
        except KeyError:
            pass

    def cam_twiddle(self, field, value):
        # TODO: FIX BRITTLE CODE!
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

        return True

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

        resp = makeRequest(f"{self.config['CAM']['IRCAM_HOST']}/cgi-bin/ptzBase.cgi" \
              f"?action=moveDirectly" \
              f"&channel=0" \
              f"&startPoint[0]={command['S_0']}" \
              f"&startPoint[1]={command['S_1']}" \
              f"&endPoint[0]={command['E_0']}" \
              f"&endPoint[1]={command['E_1']}"
        )

        if resp:
            return resp
        else:
            return "IRCAM ircam_move error []"

    def stop(self):
        pass

    def run(self):
        self.init_camera("FORE")
        self.plugin.run()
