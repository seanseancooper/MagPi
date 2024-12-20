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


class ShowxatingPlugin(threading.Thread):
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

        self.streamservice = None
        self.streamservice_thread = None

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
        if frame is not None:
            cv.imshow(self.plugin_name, frame)
        else:
            cam_logger.warning("display got no frame!!!")

    def render(self, frame):
        if self.plugin_config['plugin_displays']:
            self.display(frame)

    def stop_streamservice(self):
        self.plugin_process_frames = False
        self.streamservice.force_stop()
        self.streamservice_thread = None
        self.streamservice = None

    def start_streamservice(self, processed):
        handler = StreamingHandler
        handler.src = processed
        handler.majic_color = self.majic_color
        self.streamservice = StreamService((self.plugin_config['streaming_host'], self.plugin_config['streaming_port']),
                                           self.plugin_config['streaming_path'], handler)
        self.streamservice.stream()
        self.streamservice_thread = self.streamservice.t

    def stream(self, frame):
        if self.plugin_config['streams'] is True:
            if self.streamservice is not None:
                self.streamservice.RequestHandlerClass.src = frame

    def process_frame(self, frame):
        return frame

    def stop(self):
        if self.streamservice_thread:
            self.stop_streamservice()

    def run(self):
        """ event loop for generic plugin """

        try:

            self.get_config()
            self.set_capture()

            for frame in self.plugin_capture.run():
                self.start_time = self.plugin_capture.statistics['capture_start_time']
                self.frame_rate = self.plugin_capture.statistics['capture_frame_rate']
                self.frame_delta = self.plugin_capture.statistics['capture_frame_period'] #  rename
                self.frame_id = self.plugin_capture.statistics['capture_frame_id']
                self.frame_shape = self.plugin_capture.statistics['capture_frame_shape']
                self.majic_color = self.plugin_capture.statistics['capture_majic_color']
                processed = self.process_frame(frame)
                self.render(processed)

                if cv.waitKey(1) & 0xFF == ord('x'):
                    break
        except ValueError:
            print(f"no frame!!")
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":

    plugin = ShowxatingPlugin()

    def plugin_stops():
        cam_logger.info(f"{plugin.plugin_name} plugin stopped.")

    import atexit
    atexit.register(plugin_stops)
    plugin.run()
