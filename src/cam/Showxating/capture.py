import time
from datetime import datetime
import cv2 as cv
from PIL import Image

import logging
import http.client

cam_logger = logging.getLogger('cam_logger')
logger_root = logging.getLogger('root')


class ShowxatingCapture:

    def __init__(self, name, src, config):
        super().__init__()

        self.plugin_config = config
        self.capture = None
        self.capture_name = name
        self.capture_param_capture_src = src

        self.capture_frame_rate = 0.0
        self.capture_output_show_stats = False
        self.capture_output_log_stats = False
        self.write_mp4 = False

        self.f_id = 0
        self.statistics = {}

    def init_capture(self):

        def initialize():
            self.capture = cv.VideoCapture(self.capture_param_capture_src)
            if not self.capture.isOpened():
                cam_logger.warning(cv.getBuildInformation())

        if self.capture:
            initialize()
        else:
            while self.capture is None:
                # camera capture (0)
                if isinstance(self.capture_param_capture_src, int):
                    initialize()
                # test mp4
                elif 'http' not in self.capture_param_capture_src:
                    initialize()
                # wifi connected camera over http
                elif 'http' in self.capture_param_capture_src:
                    try:
                        elements = str(self.capture_param_capture_src).lstrip("http://").split("/")
                        try:
                            conn = http.client.HTTPConnection(elements[0])
                            conn.request("GET", "/" + elements[1])
                            r1 = conn.getresponse()
                            if r1.status == 200:
                                initialize()
                            conn.close()
                        except OSError as e:
                            cam_logger.error(
                                    f"[{__name__}] failed to connect {e}, retrying in 5 seconds...")
                            time.sleep(5)
                    except Exception as e:
                        cam_logger.warn(
                                f"[{__name__}] failed to connect to camera: {e}\n retrying in 5 seconds...")
                        time.sleep(5)
                else:
                    cam_logger.error(
                            f"[{__name__}] invalid connection string in configuration file.")
    @staticmethod
    def highlight(f, arry):
        """sample a pixel position; use combinatorial 'inversion'
        of the color to produce a new color that is always visible."""
        img = Image.fromarray(f, "RGB")
        pix = img.load()
        x, y = arry
        R, G, B = pix[x, y]
        return (R + 128) % 255, (G + 128) % 255, (B + 128) % 255

    def run(self):

        self.init_capture()

        if not self.capture.isOpened():
            cam_logger.critical("{} cannot open capture".format(self.capture_name))
            exit(1)

        frame_start = time.monotonic()
        start_time = datetime.now()

        while self.capture.isOpened():

            proc_start = time.monotonic()
            ref, frame = self.capture.read()

            if ref:

                self.capture_frame_rate = round(self.f_id / (time.monotonic() - frame_start), 2)

                self.statistics['capture_start_time'] = start_time
                self.statistics['capture_frame_rate'] = self.capture_frame_rate
                self.statistics['capture_frame_period'] = round(time.monotonic() - proc_start, 4)
                self.statistics['capture_frame_id'] = self.f_id
                self.statistics['capture_frame_shape'] = frame.shape
                self.statistics['capture_majic_color'] = self.highlight(frame, self.plugin_config.get('plugin_majic_pixel', [10, 110]))

                stats = f'{self.capture_name} | OUT: {self.capture_frame_rate:.2f} fps {datetime.now().strftime("%b %d, %Y %X")} '

                if self.plugin_config['capture_output_show_stats']:
                    cv.putText(frame, stats, (35, 445), cv.FONT_HERSHEY_DUPLEX, .50, self.statistics['capture_majic_color'], 1)

                self.statistics['capture_output_show_stats'] = stats

                if self.plugin_config['capture_output_log_stats']:
                    logger_root.debug(stats)

                self.f_id += 1
                yield frame

            else:
                cam_logger.warning(f"{self.capture_name} capture returned NO REF!")
                self.capture.release()
