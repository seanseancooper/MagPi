import os
import threading
import logging.handlers
from datetime import datetime, timedelta

from src.cam.Showxating.capture import ShowxatingCapture
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

        self.frame = None
        self.frame_id = None
        self.frame_rate = None
        self.frame_period = None
        self.frame_shape = None

        self.streamservice = None  # from CAMManager now
        self.plugin_thread = None
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

        self.plugin_config = global_config['PLUGIN']
        self.plugin_process_frames = self.plugin_config['plugin_process_frames']

    def stream(self, frame):
        if self.plugin_config['streams'] is True:
            if not self.streamservice.stopped and self.is_alive:
                self.streamservice.RequestHandlerClass.src = frame
                self.streamservice.RequestHandlerClass.majic_color = self.majic_color

    # def process_frame(self, frame):
    #     return frame

    @staticmethod
    def process_frame(frame):
        """"method that processes frames from the capture."""
        raise RuntimeError('Must be implemented by subclasses.')

    def stream_direct(self):
        """Video streaming generator function."""
        yield b'--jpgboundary\r\n'
        while self.is_alive:
            f = self.plugin_capture.get_frame()

            import cv2 as cv
            params = (cv.IMWRITE_JPEG_QUALITY, 100)
            img_str = cv.imencode('.jpeg', f, params)[1].tobytes()

            yield b'Content-Type: image/jpeg\r\n\r\n' + img_str + b'\r\n--jpgboundary\r\n'

    def stop(self):
        """set a flag to stop threads"""
        self.is_alive = False
        self.plugin_process_frames = False

    # def join(self):
    #     if not self.is_alive:
    #         self.streamservice_thread.join()

    def _plugin(self):
        self.get_config()
        self.set_capture()
        try:
            frame_iterator = self.plugin_capture.run()
            for frame in frame_iterator:

                self.created = self.plugin_capture.statistics['capture_start_time']
                self.frame_id = self.plugin_capture.statistics['capture_frame_id']
                self.frame_rate = self.plugin_capture.statistics['capture_frame_rate']
                self.frame_period = self.plugin_capture.statistics['capture_frame_period']
                self.frame_shape = self.plugin_capture.statistics['capture_frame_shape']
                self.majic_color = self.plugin_capture.statistics['capture_majic_color']

                self.updated = datetime.now()
                self.elapsed = self.updated - self.created

                self.frame = self.process_frame(frame)
                self.stream(self.frame)

        except ValueError:
            print(f"no frame!!")
        except KeyboardInterrupt:
            pass

    def start(self):

        self.is_alive = True

        self.plugin_thread = threading.Thread(target=self._plugin, name='BVPlugin')
        # self.plugin_thread.daemon = True
        self.plugin_thread.start()

