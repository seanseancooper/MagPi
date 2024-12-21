import os
import threading
import cv2 as cv
import time

import logging.handlers
from src.cam.Showxating.capture import ShowxatingCapture
from src.cam.Showxating.lib.StreamService import StreamService, StreamingHandler
from src.config import readConfig


cam_logger = logging.getLogger('cam_logger')
logger_root = logging.getLogger('root')


class ShowxatingPlugin(object):
    """plugin implementation for OpenCV code to be inserted into a RTSP video processing chain created by a
    ShowxatingVideoCapture(). This implementation allows 'chaining' the processes by passing frames between
    named, serialized instances of the component."""

    def __init__(self):
        super().__init__()

        self.plugin_name = None

        self.plugin_elapsed_time = None
        self.plugin_current_time = None

        # encapsulated config
        self.plugin_config = {}

        # encapsulated capture
        self.plugin_capture = None

        # args on the cli
        self.plugin_args_capture_src = None

        # process_frames? The point is to be able to...
        self.plugin_process_frames = False

        # my encapsulated display(s)
        self.plugin_displays = False
        self.plugin_display = {}

        self.start_time = None
        self.frame_rate = None
        self.frame_delta = None
        self.frame_id = None
        self.frame_shape = None

        self.plugin_thread = None           # 2nd run ... tx_thread
        self.streamservice = None
        self.streamservice_thread = None    # 1st run ... rx_thread

        self.alive = False

        # magic highlight color
        self.majic_color = None

    def set_capture(self):
        self.plugin_capture = ShowxatingCapture(self.plugin_name,
                                                self.plugin_args_capture_src,
                                                self.plugin_config)
        cam_logger.debug(f"{self.plugin_name} initialized capture. src:{self.plugin_args_capture_src}")

    def get_config(self):
        global_config = {}

        readConfig('cam.json', global_config)

        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = global_config.get('OPENCV_FFMPEG_CAPTURE_OPTIONS', '')
        os.environ["OPENCV_FFMPEG_WRITER_OPTIONS"] = global_config.get('OPENCV_FFMPEG_WRITER_OPTIONS', '')

        self.plugin_config, _ = global_config['PLUGINS']
        self.plugin_process_frames = self.plugin_config['plugin_process_frames']

    def display(self, frame):
        while frame is not None:
            cv.imshow(self.plugin_name, frame)
            if cv.waitKey(1) & 0xFF == ord('x'):
                break

    def render(self, frame):
        if self.plugin_config['plugin_displays']:
            self.display(frame)

    # READING (rx_thread)....
    def _start_streamservice(self):
        handler = StreamingHandler
        handler.majic_color = self.majic_color
        self.streamservice = StreamService((self.plugin_config['streaming_host'], self.plugin_config['streaming_port']),
                                           self.plugin_config['streaming_path'], handler)
        self.streamservice.stream()

    def stream(self, frame):
        if self.plugin_config['streams'] is True:
            if not self.streamservice.is_stopped:
                self.streamservice.RequestHandlerClass.src = frame

    def process_frame(self, frame):
        return frame

    def stop(self):
        """set a flag to stop threads"""
        self.alive = False
        self.plugin_process_frames = False
        self.streamservice.force_stop()
        pass

    def join(self):
        if not self.alive:
            self.streamservice_thread.join()

    def _start_plugin(self):
        self.get_config()
        self.set_capture()
        try:
            for frame in self.plugin_capture.run():
                # WRITING ...
                self.alive = True
                self.start_time = self.plugin_capture.statistics['capture_start_time']
                self.frame_rate = self.plugin_capture.statistics['capture_frame_rate']
                self.frame_delta = self.plugin_capture.statistics['capture_frame_period']  # rename
                self.frame_id = self.plugin_capture.statistics['capture_frame_id']
                self.frame_shape = self.plugin_capture.statistics['capture_frame_shape']
                self.majic_color = self.plugin_capture.statistics['capture_majic_color']
                self.process_frame(frame)

        except ValueError:
            # consider .join()
            print(f"no frame!!")
        except KeyboardInterrupt:
            # join()
            pass

    def start(self):
        self.alive = True
        # READING...
        self._start_streamservice()
        # WRITING ...
        self.plugin_thread = threading.Thread(target=self._start_plugin, name='BVPlugin')
        self.plugin_thread.daemon = True
        self.plugin_thread.start()

