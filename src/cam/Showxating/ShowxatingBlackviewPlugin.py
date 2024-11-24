import cv2 as cv
import numpy as np

from src.cam.Showxating.plugin import ShowxatingPlugin
from src.cam.Showxating.lib.ImageWriter import ImageWriter
from src.cam.Showxating.lib.FrameObjektTracker import FrameObjektTracker
from src.cam.Showxating.lib.utils import getRectsFromContours, draw_rects, draw_contours, draw_centroid, \
    getLargestRect, wall_images, draw_grid

import logging

cam_logger = logging.getLogger('cam_logger')


def print_symbology(has_symbols, f, contours, m, c):
    if has_symbols:

        # delimit the work area
        cv.line(f, (0, 125), (704, 125), c, 1)
        cv.line(f, (0, 345), (704, 345), c, 1)

        if m:
            cv.putText(f, "MOTION DETECTED!", (5, 110), cv.FONT_HERSHEY_PLAIN, 1.0, c, 2)

        # yellow contour rect: items that are moving
        try:
            draw_rects(f, [getRectsFromContours(contours)[1]], (0, 255, 255), 2)
        except TypeError:
            pass  # 'NoneType' object is not subscriptable


def print_analytics(has_analysis, f, contours, hierarchy, rectangles):
    if has_analysis:
        mean = np.mean([[rx, ry, rx + rw, ry + rh] for [rx, ry, rw, rh] in rectangles], axis=0, dtype=int)

        draw_rects(f, [mean], (255, 0, 0), 1)  # 'blue meany' (average) rect
        draw_contours(f, contours, hierarchy, (64, 255, 64), 1)  # green contours
        draw_rects(f, [getLargestRect(rectangles)], (255, 255, 255), 2)  # white bounding rect
        draw_centroid(f, contours, 5, (127, 0, 255), 1)  # purple centroid


def print_tracked(has_analysis, has_symbols, f, t):

    if has_symbols:
        # green dot: items being tracked
        for _ in t:
            o = t.get(_)
            cv.rectangle(f, o.ml, (o.ml[0] - 5, o.ml[1] - 5), (0, 255, 0), -1)

    if has_analysis:
        for w, _ in enumerate([x for x in t][:5], 1):
            o = t.get(_)
            try:
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
        self.has_analysis = False
        self.has_motion = False

        # hyper parameters
        self.krnl = 17                                  # controls size of items considered relevant
        self._kz = (int(self.krnl), int(self.krnl))
        self.threshold = 15.0                           # pixels additional to the mean during thresholding

        self.show_krnl_grid = False
        self.show_threshold = False
        self.threshold_hold = False

        self.mediapipe = False  # slow!
        self._pose = None
        self._result_T = None  # medipipe result

        self.tracker = FrameObjektTracker()
        self.tracked = {}

        self.processed = None

    def config_tracker(self):
        self.tracker.configure()

    def cam_snap(self):

        def _snap(frame):
            if frame is not None:
                writer = ImageWriter("CAMManager")
                writer.write("CAM_SNAP", frame)

        for frame in self.plugin_capture.run():
            _snap(frame)
            break

    def pre_mediapipe(self, frame):

        if self.mediapipe:
            import mediapipe as mp  # only load if needed. slow...

            mp_pose = mp.solutions.pose
            self._pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            BGR_T = cv.cvtColor(frame[self._max_height, self._max_width], cv.COLOR_RGB2BGR)
            self._result_T = self._pose.process(BGR_T)

    def draw_mediapipe(self, f):
        if self.mediapipe:
            import mediapipe as mp  # already loaded, only here for refs
            mp_pose = mp.solutions.pose

            def draw_pose(fragment, result):
                if result.pose_landmarks is not None:
                    mp_drawing = mp.solutions.drawing_utils
                    mp_drawing_styles = mp.solutions.drawing_styles
                    mp_drawing.draw_landmarks(fragment, result.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                              landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

        if self._result_T is not None:
            if self._result_T.pose_landmarks is not None:
                draw_pose(f, self._result_T)

    def process_contours(self, f, conts, hier):

        if len(conts):
            # TODO: change this to filter for 'volume' of contour
            self.has_motion = True

            wall, rects, areas = wall_images(f, conts)

            if self.has_analysis or self.has_symbols:
                self.tracked = self.tracker.track_objects(self.frame_id, conts, hier, wall, rects, areas)
                if self.tracked:
                    print_tracked(self.has_analysis, self.has_symbols, f, self.tracked)

            print_analytics(self.has_analysis, f, conts, hier, rects)
            print_symbology(self.has_symbols, f, conts, self.has_motion, self.majic_color)

            self.draw_mediapipe(f)

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

                conts, hier = cv.findContours(THRESHOLD, cv.RETR_TREE, cv.CHAIN_APPROX_NONE,
                                              offset=[self._max_width.start, self._max_height.start])

                if self.show_threshold or self.threshold_hold:
                    frame[self._max_height, self._max_width] = cv.cvtColor(THRESHOLD, cv.COLOR_GRAY2BGR)

                self.process_contours(frame, conts, hier)

                # TODO: do this in javascript instead.
                if self.show_krnl_grid:
                    draw_grid(frame, (int(self.krnl), int(self.krnl)), self.majic_color, 1)

            self.processed = frame

            if self.frame_id == 0:
                self.start_streamservice(frame)

            self.stream(frame)

            return self.processed

        return frame
