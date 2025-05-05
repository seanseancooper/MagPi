import cv2 as cv
import numpy as np
import json

# from src.net.imageZMQ.ImageZMQAsyncProducer import ImageZMQAsyncProducer

from src.cam.mq.CAMMQProvider import CAMMQProvider
from src.cam.Showxating.plugin import ShowxatingPlugin
from src.cam.lib.ImageWriter import ImageWriter
from src.cam.lib.FrameObjektTracker import FrameObjektTracker
from src.cam.lib.utils import draw_contours, wall_images, sortedContours
from src.ebs.lib.TokenBucket import TokenBucket
from src.lib.utils import format_time, format_delta
from src.net.lib.net_utils import check_imq_available


import logging

cam_logger = logging.getLogger('cam_logger')
speech_logger = logging.getLogger('speech_logger')


class ShowxatingBlackviewPlugin(ShowxatingPlugin):

    def __init__(self):
        super().__init__()
        self._area = tuple[0:345, 0:704]    # the work area.
        self._max_height = slice(125, 345)  # work are height is 220px
        self._max_width = slice(0, 704)     # view width, not 'step'

        self.has_symbols = True
        self.has_analysis = False

        self.has_motion = False
        self.had_motion = False
        self.throttle = None
        self.trap_motion = False

        self.cropped_frame = None                       #
        self.cropped_reference = None                   #
        self.greyscale_frame = None                     #
        self.greyscale_refer = None                     #

        self.krnl = 17                                  # controls size of items considered relevant
        self._kSz = (int(self.krnl), int(self.krnl))
        self.threshold = 15.0                           # pixels additional to the mean during thresholding

        self.show_threshold = False
        self.hold_threshold = 0                         # number of frames threshold mask is displayed if displayed

        self._pose = None
        self._result_T = None  # medipipe result

        self.tracker = FrameObjektTracker()
        self.mq_provider = None

        self.tracked = {}

    @staticmethod
    def print_symbology(p, f, rect):

        _height, _width, ch = f.shape
        _start = int(0.25 * _height)

        if p.has_symbols:
            if p.has_motion:
                cv.putText(f, "MOTION DETECTED!", (5, _start - 5), cv.FONT_HERSHEY_PLAIN, 1.0, p.majic_color, 2)

            # yellow rect: items that are moving
            try:
                def print_rect(r):
                    x, y, w, h = r
                    item = f'({x},{y})'
                    cv.putText(f, item, (x - 15, y - 10), cv.FONT_HERSHEY_PLAIN, .75, (0, 255, 255), 1)
                    cv.rectangle(f, (x, y), (x + w, y + h), (0, 255, 255), 2)

                if np.any(rect):
                    print_rect(rect)

            except TypeError:
                pass  # 'NoneType' object is not subscriptable

    @staticmethod
    def print_analytics(p, f, contours, hierarchy):
        if p.has_analysis:
            draw_contours(f, contours, hierarchy, (64, 255, 64), 1)  # green contours
            # draw_centroid(f, contours, 5, (127, 0, 255), 1)  # purple centroid

    @staticmethod
    def print_tracked(p, f):
        _height, _width, ch = f.shape
        _end = int(0.70 * _height)
        _font_size = 0.75

        if p.has_symbols:

            for i, _ in enumerate(p.tracked):
                o = p.tracked.get(_)
                x = o._avg_loc[0]
                y = o._avg_loc[1]
                item = f'{o.tag[-12:]} [{x},{y}]'
                pt = x, y
                # yellow dot: items being tracked
                cv.putText(f, item, (x, (y + (i * 10))), cv.FONT_HERSHEY_PLAIN, .75, (0, 255, 255), 1)
                cv.rectangle(f, (x, y), (x + 5, y + 5), (0, 255, 255), -1)

        if p.has_analysis:
            for w, _ in enumerate([x for x in p.tracked][:p.tracker.contour_limit], 1):
                o = p.tracked.get(_)
                try:
                    cv.putText(f, o.tag, (385, _end + (w * 20)), cv.FONT_HERSHEY_PLAIN, _font_size, (255, 255, 255), 1)
                except AttributeError as a:
                    pass

    def get_config(self):
        super().get_config()
        self.tracker.configure()
        self.throttle = TokenBucket(self.plugin_config['tokenbucket'].get('tokens', 1),
                                    self.plugin_config['tokenbucket'].get('interval', 60)
                                    )
        self.krnl = self.plugin_config.get('krnl', 10.0)
        self.threshold = self.plugin_config.get('threshold', 10.0)

        if check_imq_available():
            self.mq_provider = CAMMQProvider()
            self.mq_provider.configure('cam.json')


    def get(self):
        return {
            "has_symbols": self.has_symbols,
            "has_analysis": self.has_analysis,
            "has_motion": self.has_motion,

            "kSz": str(self._kSz),
            "threshold": self.threshold,

            "f_id": self.frame_id,
            "majic_color": self.majic_color,
            "frame_shape": self.frame_shape,
            "show_threshold": self.show_threshold,
            "hold_threshold": self.hold_threshold,

            "created": format_time(self.created, "%H:%M:%S"),
            "updated": format_time(self.updated, "%H:%M:%S"),
            "elapsed": format_delta(self.elapsed, "%H:%M:%S")
        }

    def sets_hold_threshold(self, value):
        if value is True:
            self.hold_threshold = self.plugin_config.get('hold_threshold_max', 5)
        elif value is False:
            self.hold_threshold = 0

    def set_field(self, field, value):
        if field == 'hold_threshold':
            self.show_threshold = (value == 'true')

        if field == 'krnl':
            self.krnl = value
        if field == 'threshold':
            self.sets_hold_threshold(True)
            self.threshold = float(value)
        if field == 'frm_delta_pcnt':
            self.tracker.f_delta_pcnt = float(value)
        if field == 'f_limit':
            self.tracker.f_limit = int(value)

        if field == 'crop':
            json_value = json.loads(value)
            print(f'cropper json: {json_value}')
            self._max_height = slice(int(json_value['y']), int(json_value['y'] + json_value['h']), None)
            self._max_width = slice(int(json_value['x']), int(json_value['x'] + json_value['w']), None)

    def threshold_ops(self, f, t):
        # displayed when self.threshold is changing or threshold_hold is enabled
        if self.show_threshold or self.hold_threshold > 0:
            # transform the greyscale threshold into the color f
            f[self._max_height, self._max_width] = cv.cvtColor(t, cv.COLOR_GRAY2BGR)
            self.hold_threshold -= 1

    def trap(self, f, reset):
        """ crop area, with symbology & labels """

        if self.trap_motion:
            if self.has_motion:

                def _snap(plugin, f):

                    writer = ImageWriter("CAMManager")
                    writer.write_trapped("CAM_TRAP", self.plugin_config.get('outfile_path', '../_out'), f)

                    # if self.tracked get the label and either log
                    # the trapped thing to an event list, or mark
                    # it as trapped in an event list. We want to be
                    # able to read a running list of past events as
                    # relates to motion and image captures
                    # AT MINIMUM THIS SHOULD HAVE THE LABEL ON THE IMAGE

                _snap(self, f[self._max_height, self._max_width])

                self.trap_motion = False      # unset trap_motion
                if reset:
                    self.trap_motion = True   # reset trap_motion

    def cam_snap(self):
        """ unaltered frame, no processing or symbology """

        def _snap(f):
            if f is not None:
                writer = ImageWriter("CAMManager")
                writer.write("CAM_SNAP", f, f_id=None)

        _, f = self.plugin_capture.capture.retrieve()
        _snap(f)

        return "OK"

    def print_frame(self, frame, f_id):
        """ FOR ITEMS TRACKED/MOVING.
            unaltered frame, no processing or symbology
            associated to a 'label' for future reference.
            BEST?? IMAGE....
            get histogram here ...
            seen_things[hist] = labeled_image_ref -> filesystem location of this image
        """

        def _snap(f):
            if f is not None:
                writer = ImageWriter("CAMManager")
                writer.write("CAM_PRNT", f, f_id)

        _snap(frame)

        return "OK"

    def process_contours(self, frame, contours, hier):

        if contours:

            self.has_motion = True
            conts = sortedContours(contours)

            for cnt in conts[:self.tracker.contour_limit]:

                wall, rect = wall_images(frame.copy(), cnt)

                if self.has_analysis or self.has_symbols:

                    stats = {
                        "capture_frame_rate": self.frame_rate,
                        "capture_frame_period": self.frame_period,
                        "capture_frame_shape": self.frame_shape,
                        "max_height": self._max_height,
                        "max_width": self._max_width
                    }

                    self.tracked = self.tracker.track_objects(self.frame_id, frame, cnt, wall, rect, stats)

                    if self.tracked:
                        if self.mq_provider:
                            [self.mq_provider.send_frameobjekt(o) for o in self.tracked.values() if o.f_id > 0]

                        self.print_tracked(self, frame)
                        self.print_symbology(self, frame, rect)
                    self.print_analytics(self, frame, cnt, hier)

                    if self.plugin_config['write_all_frames']:
                         self.print_frame(frame, self.frame_id)  # <-- memorize moving things

            self.trap(frame, False)

            if self.had_motion != self.has_motion is True:
                if self.throttle.handle('motion'):
                    pass
                    # speech_logger.info('motion detected!')
                self.had_motion = True

        else:
            self.has_motion = False
            self.had_motion = False
            self.tracker.clear_cache(self.frame_id)

    def process_frame(self, frame):

        if self.plugin_process_frames:

            # ensure capture is open and if so, get a reference.
            # failing that (not open?), try *again* to read
            # the capture to get the reference frame.
            if self.plugin_capture.capture.grab():
                ret, reference = self.plugin_capture.capture.retrieve()
            else:
                ret, reference = self.plugin_capture.capture.read()

            if ret:

                self.cropped_frame = frame[self._max_height, self._max_width]
                self.cropped_reference = reference[self._max_height, self._max_width]

                self.greyscale_frame = cv.cvtColor(self.cropped_frame, cv.COLOR_BGR2GRAY)
                self.greyscale_refer = cv.cvtColor(self.cropped_reference, cv.COLOR_BGR2GRAY)

                DELTA = cv.absdiff(self.greyscale_frame, self.greyscale_refer)

                BLURRED = cv.GaussianBlur(DELTA, (int(self.krnl), int(self.krnl)), 0)
                _, THRESHOLD = cv.threshold(BLURRED, int(np.mean(BLURRED)) + self.threshold, 255, cv.THRESH_BINARY)

                contours, hier = cv.findContours(THRESHOLD, cv.RETR_TREE, cv.CHAIN_APPROX_NONE,
                                              offset=[self._max_width.start, self._max_height.start])

                self.threshold_ops(frame, THRESHOLD)
                self.process_contours(frame, contours, hier)

            return frame

        return frame
