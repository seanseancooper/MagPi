import cv2 as cv
import numpy as np

from src.cam.Showxating.plugin import ShowxatingPlugin
from src.cam.Showxating.lib.ImageWriter import ImageWriter
from src.cam.Showxating.lib.FrameObjektTracker import FrameObjektTracker
from src.cam.Showxating.lib.utils import draw_rects, draw_contours, wall_images, draw_grid, sortedContours, is_inside

import logging

cam_logger = logging.getLogger('cam_logger')


def print_symbology(has_symbols, f, rect, m, c):

    if has_symbols:
        if m:    # TODO: make this JSON on an endpoint.
            cv.putText(f, "MOTION DETECTED!", (5, 110), cv.FONT_HERSHEY_PLAIN, 1.0, c, 2)

        # yellow rect: items that are moving
        try:
            draw_rects(f, [rect], (0, 255, 255), 2)
        except TypeError:
            pass  # 'NoneType' object is not subscriptable


def print_analytics(has_analysis, f, contours, hierarchy):
    if has_analysis:
        draw_contours(f, contours, hierarchy, (64, 255, 64), 1)  # green contours
        # draw_centroid(f, contours, 5, (127, 0, 255), 1)  # purple centroid


def print_tracked(has_analysis, has_symbols, f, t, rect):

    if has_symbols:

        for _ in t:
            o = t.get(_)
            x = o.ml[0]
            y = o.ml[1]
            pt = x, y
            if rect and is_inside(pt, rect):
                # yellow dot: items being tracked
                cv.rectangle(f, (x,y), (x+5, y+5), (0, 255, 255), -1)
            else:
                # red dot: mean location fails...
                cv.rectangle(f, (x, y), (x + 5, y + 5), (0, 0, 255), -1)

    if has_analysis:
        for w, _ in enumerate([x for x in t][:1], 1):
            o = t.get(_)
            try:    # TODO: make this JSON on an endpoint.
                cv.putText(f, o.tag, (385, 345 + (w * 20)), cv.FONT_HERSHEY_PLAIN, .75, (255, 255, 255), 1)
            except AttributeError as a:
                pass


class ShowxatingBlackviewPlugin(ShowxatingPlugin):

    def __init__(self):
        super().__init__()
        self._area = tuple[0:345, 0:704]  # the work area.
        self._max_height = slice(125, 345)  # view height is 220px
        self._max_width = slice(0, 704)  # view width, not 'step'

        self.has_symbols = True
        self.has_analysis = True
        self.has_motion = False

        # hyper parameters
        self.krnl = 17                                  # controls size of items considered relevant
        self._kz = (int(self.krnl), int(self.krnl))
        self.threshold = 15.0                           # pixels additional to the mean during thresholding

        self.show_krnl_grid = False
        self.show_threshold = False
        self.hold_threshold = False

        self.mediapipe = False  # slow!
        self._pose = None
        self._result_T = None  # medipipe result

        self.tracker = FrameObjektTracker()
        self.tracked = {}

        self.processed = None

    def config_tracker(self):
        self.tracker.configure()

    def sets_binary(self, field, value):
        if field == 'threshold_hold':
            self.hold_threshold = value
        if field == 'mediapipe':
            self.mediapipe = value

    def cam_snap(self):

        def _snap(frame):
            if frame is not None:
                writer = ImageWriter("CAMManager")
                writer.write("CAM_SNAP", frame)

        for frame in self.plugin_capture.run():
            _snap(frame)
            break

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

    def threshold_ops(self, f, THRESHOLD):
        if self.show_threshold or self.hold_threshold:
            f[self._max_height, self._max_width] = cv.cvtColor(THRESHOLD, cv.COLOR_GRAY2BGR)

    def grid_ops(self, f):
        # TODO: do this in javascript instead.
        if self.show_krnl_grid:
            draw_grid(f, (int(self.krnl), int(self.krnl)), self.majic_color, 1)

    def process_contours(self, f, contours, hier):

        # delimit the work area
        cv.line(f, (0, 125), (704, 125), self.majic_color, 1)
        cv.line(f, (0, 345), (704, 345), self.majic_color, 1)

        if contours:

            self.has_motion = True
            conts = sortedContours(contours)

            for cnt in conts[:1]:
                # note: histograms for every frame is slow. That's why it's set False.

                # if cv.contourArea(cnt) < 25:
                #     print(cv.contourArea(cnt))
                #     continue

                wall, rect, dists = wall_images(f.copy(), cnt, False)

                if self.has_analysis or self.has_symbols:

                    self.tracked = self.tracker.track_objects(self.frame_id, cnt, hier, wall, rect)
                    if self.tracked:
                        print_tracked(self.has_analysis, self.has_symbols, f, self.tracked, rect)
                        print_symbology(self.has_symbols, f, rect, self.has_motion, self.majic_color)

            print_analytics(self.has_analysis, f, conts, hier)

            # # note: histograms are for every frame and is slow. That's why it's False.
            # wall, rect, dists = wall_images(f, conts, False)
            #
            # if self.has_analysis or self.has_symbols:
            #     self.tracked = self.tracker.track_objects(self.frame_id, conts, hier, wall, rect)
            #     if self.tracked:
            #         print_tracked(self.has_analysis, self.has_symbols, f, self.tracked, rect)

            # print_analytics(self.has_analysis, f, conts, hier)
            # print_symbology(self.has_symbols, f, rect, self.has_motion, self.majic_color)

            self.post_mediapipe(f)

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

            self.processed = frame

            if self.frame_id == 0:
                self.start_streamservice(frame)

            self.stream(frame)

            return self.processed

        return frame
