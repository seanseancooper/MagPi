import os
import threading

import logging.handlers
from datetime import datetime, timedelta

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

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta

        self.plugin_config = {}
        self.plugin_capture = None
        self.plugin_capture_src = None

        self.plugin_process_frames = False

        self.frame_id = None
        self.frame_rate = None
        self.frame_period = None
        self.frame_shape = None

        self.streamservice = None
        self.streamservice_thread = None    # 1st run ... rx_thread
        self.plugin_thread = None           # 2nd run ... tx_thread
        self.is_alive = False

        self.majic_color = None

    def set_capture(self):
        self.plugin_capture = ShowxatingCapture(self.plugin_name,
                                                self.plugin_capture_src,
                                                self.plugin_config)
        cam_logger.debug(f"{self.plugin_name} initialized capture. src:{self.plugin_capture_src}")

    def get_config(self):
        global_config = {}

        readConfig('cam.json', global_config)

        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = global_config.get('OPENCV_FFMPEG_CAPTURE_OPTIONS', '')
        os.environ["OPENCV_FFMPEG_WRITER_OPTIONS"] = global_config.get('OPENCV_FFMPEG_WRITER_OPTIONS', '')

        self.plugin_config, _ = global_config['PLUGINS']
        self.plugin_process_frames = self.plugin_config['plugin_process_frames']

    def start_streamservice(self):

        self.streamservice = StreamService((
                                self.plugin_config['streaming_host'],
                                self.plugin_config['streaming_port']
                            ), self.plugin_config['streaming_path'], StreamingHandler)
        self.streamservice.stream()

    def stream(self, frame):
        ''' allow a plugin to stream frames '''
        if self.plugin_config['streams'] is True:
            if not self.streamservice.is_stopped and self.is_alive:
                self.streamservice.RequestHandlerClass.src = frame
                self.streamservice.RequestHandlerClass.majic_color = self.majic_color

    def process_frame(self, frame):
        return frame

    def stop(self):
        """set a flag to stop threads"""
        self.is_alive = False
        self.plugin_process_frames = False
        self.streamservice.force_stop()

    def join(self):
        if not self.is_alive:
            self.streamservice_thread.join()

    def start_plugin(self):
        self.get_config()
        self.set_capture()
        try:
            for frame in self.plugin_capture.run():
                self.created = self.plugin_capture.statistics['capture_start_time']
                self.frame_id = self.plugin_capture.statistics['capture_frame_id']
                self.frame_rate = self.plugin_capture.statistics['capture_frame_rate']
                self.frame_period = self.plugin_capture.statistics['capture_frame_period']
                self.frame_shape = self.plugin_capture.statistics['capture_frame_shape']
                self.majic_color = self.plugin_capture.statistics['capture_majic_color']

                self.updated = datetime.now()
                self.elapsed = self.updated - self.created

                self.process_frame(frame)

        except ValueError:
            print(f"no frame!!")
        except KeyboardInterrupt:
            pass

    def start(self):

        self.is_alive = True

        # READING...
        self.start_streamservice()

        # WRITING ...
        self.plugin_thread = threading.Thread(target=self.start_plugin, name='BVPlugin')
        self.plugin_thread.daemon = True
        self.plugin_thread.start()

