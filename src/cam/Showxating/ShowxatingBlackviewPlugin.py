import cv2 as cv
import numpy as np
import json

from src.cam.Showxating.plugin import ShowxatingPlugin
from src.cam.Showxating.lib.ImageWriter import ImageWriter
from src.cam.Showxating.lib.FrameObjektTracker import FrameObjektTracker
from src.cam.Showxating.lib.utils import draw_grid, draw_contours, wall_images, sortedContours, is_inside

import logging

from src.ebs.lib.TokenBucket import TokenBucket

cam_logger = logging.getLogger('cam_logger')
speech_logger = logging.getLogger('speech_logger')


def print_symbology(has_symbols, f, rect, m, c):

    _height, _width, ch = f.shape
    _start = int(0.25 * _height)

    if has_symbols:
        if m:
            # TODO: needs to move dynamically w/ size
            cv.putText(f, "MOTION DETECTED!", (5, _start - 5), cv.FONT_HERSHEY_PLAIN, 1.0, c, 2)

        # yellow rect: items that are moving
        try:
            def print_rect(r):
                x, y, w, h = r
                item = f'({x},{y})'
                cv.putText(f, item, (x - 15, y - 10), cv.FONT_HERSHEY_PLAIN, .75, (0, 255, 255), 1)
                cv.rectangle(f, (x, y), (x + w, y + h), (0, 255, 255), 2)
            if np.any(rect):
                print_rect(rect)

        except TypeError: pass  # 'NoneType' object is not subscriptable


def print_analytics(has_analysis, f, contours, hierarchy):
    if has_analysis:
        draw_contours(f, contours, hierarchy, (64, 255, 64), 1)  # green contours
        # draw_centroid(f, contours, 5, (127, 0, 255), 1)  # purple centroid


def print_tracked(has_analysis, has_symbols, f, t, rect):
    _height, _width, ch = f.shape
    _end = int(0.70 * _height)
    _font_size = 0.75

    if has_symbols:

        for i, _ in enumerate(t):
            o = t.get(_)
            x = o.ml[0]
            y = o.ml[1]
            item = f'{o.contour_id}-{o.tag[-12:]} [{x},{y}]'
            pt = x, y
            if rect and is_inside(pt, rect):
                # yellow dot: items being tracked
                cv.putText(f, item, (x, (y + (i * 10))), cv.FONT_HERSHEY_PLAIN, .75, (0, 255, 255), 1)
                cv.rectangle(f, (x, y), (x+5, y+5), (0, 255, 255), -1)
            else:
                # red dot: mean location fails...
                cv.putText(f, item, (x, (y + (i * 10))), cv.FONT_HERSHEY_PLAIN, .75, (0, 0, 255), 1)
                cv.rectangle(f, (x, y), (x+5, y+5), (0, 0, 255), -1)

    if has_analysis:
        for w, _ in enumerate([x for x in t][:1], 1):
            o = t.get(_)
            try:
                cv.putText(f, o.tag, (385, _end + (w * 20)), cv.FONT_HERSHEY_PLAIN, _font_size, (255, 255, 255), 1)
            except AttributeError as a:
                pass


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

        self.krnl = 17                                  # controls size of items considered relevant
        self._kz = (int(self.krnl), int(self.krnl))
        self.threshold = 15.0                           # pixels additional to the mean during thresholding

        self.show_krnl_grid = False
        self.show_threshold = False
        self.hold_threshold = 0                         # number of frames threshold mask is displayed if displayed

        self.mediapipe = False  # slow!
        self._pose = None
        self._result_T = None  # medipipe result

        self.tracker = FrameObjektTracker()
        self.tracked = {}

    def get(self):
        return {
            "_area": self._area,
            "_max_height": self._max_height,
            "_max_width": self._max_width,

            "has_symbols": self.has_symbols,
            "has_analysis": self.has_analysis,
            "has_motion": self.has_motion,

            "_kz": self._kz,
            "threshold": self.threshold,

            "show_threshold": self.show_threshold,
            "mediapipe": self.mediapipe,

            "tracked": [_ for _ in self.tracked],
        }

    def get_config(self):
        super().get_config()
        self.tracker.configure()
        self.throttle = TokenBucket(int(1), int(3))

    def sets_hold_threshold(self, value):
        if value is True:
            self.hold_threshold = self.plugin_config.get('hold_threshold_max', 5)
        elif value is False:
            self.hold_threshold = 0

    def set_field(self, field, value):
        if field == 'hold_threshold':
            self.show_threshold = (value == 'true')
        if field == 'mediapipe':
            self.mediapipe = (value == 'true')
        if field == 'krnl':
            self.krnl = value
            self.show_krnl_grid = True
        if field == 'threshold':
            self.sets_hold_threshold(True)
            self.threshold = float(value)
        if field == 'frm_delta_pcnt':
            self.tracker.frm_delta_pcnt = float(value)
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
            f[self._max_height, self._max_width] = cv.cvtColor(t, cv.COLOR_GRAY2BGR)
            self.hold_threshold -= 1

    def grid_ops(self, f):
        # TODO: do this in javascript instead.
        # js will need to know width, height of workarea
        if self.show_krnl_grid:
            draw_grid(f, (int(self.krnl), int(self.krnl)), self.majic_color, 1)

    def cam_snap(self):

        def _snap(frame):
            if frame is not None:
                writer = ImageWriter("CAMManager")
                writer.write("CAM_SNAP", frame)

        for frame in self.plugin_capture.run():
            _snap(frame)
            break

        return "OK"

    def pre_mediapipe(self, f):

        if self.mediapipe:
            import mediapipe as mp  # only load if needed. slow...

            mp_pose = mp.solutions.pose
            self._pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            BGR_T = cv.cvtColor(f[self._max_height, self._max_width], cv.COLOR_RGB2BGR)
            self._result_T = self._pose.process(BGR_T)

    def post_mediapipe(self, f):
        if self.mediapipe:
            import mediapipe as mp  # already loaded, only here for refs
            mp_pose = mp.solutions.pose

        if self._result_T is not None:
            if self._result_T.pose_landmarks is not None:

                def draw_pose(fragment, result):
                    if result.pose_landmarks is not None:
                        mp_drawing = mp.solutions.drawing_utils
                        mp_drawing_styles = mp.solutions.drawing_styles
                        mp_drawing.draw_landmarks(fragment, result.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                                  landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

                draw_pose(f, self._result_T)

    def process_contours(self, f, contours, hier):

        if contours:

            self.has_motion = True
            conts = sortedContours(contours)

            for cnt in conts[:self.tracker.contour_limit]:

                wall, rect, dists = wall_images(f.copy(), cnt, False, 'paired')  # TODO: add to config

                if self.has_analysis or self.has_symbols:
                    self.tracked = self.tracker.track_objects(self.frame_id, cnt, hier, wall, rect)
                    if self.tracked:
                        print_tracked(self.has_analysis, self.has_symbols, f, self.tracked, rect)
                        print_symbology(self.has_symbols, f, rect, self.has_motion, self.majic_color)
                    print_analytics(self.has_analysis, f, cnt, hier)

            self.post_mediapipe(f)

            if self.had_motion != self.has_motion is True:
                if self.throttle.handle('motion'):
                    speech_logger.info('motion detected!')
                self.had_motion = True

        else:
            self.has_motion = False
            self.had_motion = False

    def process_frame(self, frame):

        if self.plugin_process_frames:
            # IDEA: can the timing of this be adjusted? Async code to 'grab()' might
            #  be possible.
            if self.plugin_capture.capture.grab():
                ret, reference = self.plugin_capture.capture.retrieve()
            else:
                ret, reference = self.plugin_capture.capture.read()

            if ret:
                self.pre_mediapipe(frame)
                cropped_frame = frame[self._max_height, self._max_width]
                cropped_reference = reference[self._max_height, self._max_width]

                greyscale_frame = cv.cvtColor(cropped_frame, cv.COLOR_BGR2GRAY)
                greyscale_refer = cv.cvtColor(cropped_reference, cv.COLOR_BGR2GRAY)

                DELTA = cv.absdiff(greyscale_frame, greyscale_refer)
                BLURRED = cv.GaussianBlur(DELTA, (int(self.krnl), int(self.krnl)), 0)
                _, THRESHOLD = cv.threshold(BLURRED, int(np.mean(BLURRED)) + self.threshold, 255, cv.THRESH_BINARY)
                contours, hier = cv.findContours(THRESHOLD, cv.RETR_TREE, cv.CHAIN_APPROX_NONE,
                                              offset=[self._max_width.start, self._max_height.start])
                self.threshold_ops(frame, THRESHOLD)
                self.process_contours(frame, contours, hier)
                self.grid_ops(frame)

            self.stream(frame)

            return frame

        return frame
