from datetime import datetime
import cv2 as cv
import numpy as np

from src.cam.Showxating.plugin import ShowxatingPlugin
from src.cam.Showxating.lib.ImageWriter import ImageWriter
from src.cam.Showxating.lib.FrameObjektTracker import FrameObjektTracker
from src.cam.Showxating.lib.StreamService import StreamService, StreamingHandler, highlight
import logging

from .lib.utils import getRectsFromContours, draw_rects, draw_contours, \
    draw_centroid, getLargestRect, wall_images, draw_grid

cam_logger = logging.getLogger('cam_logger')


class ShowxatingBlackviewPlugin(ShowxatingPlugin):

    def __init__(self):
        super().__init__()
        self._area = tuple[0:345, 0:704]
        self._max_height = slice(125, 345)              # view height is 220px
        self._max_width = slice(0, 704)                 # view width, not 'step'

        self._has_symbols = True
        self.ssid_key = "SSID"
        self.signal_key = "Signal"

        # hyper parameters
        self.krnl = 17                                  # controls size of items considered relevant
        self.show_krnl_grid = False
        self._kz = (int(self.krnl), int(self.krnl))
        self.threshold = 15.0                           # value of pixels additional to the mean, during thresholding

        self.show_threshold = False
        self.threshold_hold = False

        self.mediapipe = False                          # slow!
        self._pose = None
        self._result_T = None                           # medipipe result

        self._has_analysis = False
        self._motion = False

        self.tracker = FrameObjektTracker()
        self.events = []                                # list of events. deprecate
        self.tracked = {}

        self.streamservice = None
        self.processed = None

    def get_config(self):
        super().get_config()

        self.tracker.config(self.plugin_config['f_limit'],
                            self.plugin_config['frame_delta'],
                            self.plugin_config['frm_delta_pcnt']
        )

        return

    def sets_threshold_hold(self, value):
        self.threshold_hold = value

    def sets_mediapipe(self, value):
        self.mediapipe = value

    def getMaxHeight(self):
        return self._max_height

    def getMaxWidth(self):
        return self._max_width

    def start_streamservice(self):

        if self.streamservice is not None:
            self.streamservice.shutdown()
            self.streamservice = None
        handler = StreamingHandler
        handler.src = self.processed
        self.streamservice = StreamService(('localhost', self.plugin_config['streaming_port']),
                                           self.plugin_config['streaming_path'], handler)
        self.streamservice.stream()

    def stream(self, frame):
        if self.plugin_config['streams'] is True:
            if self.streamservice is not None:
                self.streamservice.requesthandler.src = frame

    def cam_snap(self):

        # IDEA: It may be more efficient to
        #  write frames via delegation than by force ('we've got that "B" roll!').

        #TODO: write to imagecache, or create a vector that can later be compared.

        def _snap(frame):
            if frame is not None:
                writer = ImageWriter("CAMManager")
                writer.write("CAM_SNAP", frame)

        for frame in self.plugin_capture.run():
            _snap(frame)
            break

    def pre_mediapipe(self, frame, max_height, max_width):
        import mediapipe as mp  # slow...

        mp_pose = mp.solutions.pose
        self._pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        BGR_T = cv.cvtColor(frame[max_height, max_width], cv.COLOR_RGB2BGR)
        self._result_T = self._pose.process(BGR_T)

    def draw_mediapipe(self, f):
        import mediapipe as mp  # slow...
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

    @staticmethod
    def print_symbology(f, contours, m, c, t):

        # delimit the work area
        cv.line(f, (0, 125), (704, 125), c, 1)
        cv.line(f, (0, 345), (704, 345), c, 1)

        if m :
            cv.putText(f, "MOTION DETECTED!", (5, 110), cv.FONT_HERSHEY_PLAIN, 1.0, c, 2)

        # green dot: items being tracked
        for _ in t:
            o = t.get(_)
            cv.rectangle(f, o.ml, (o.ml[0] - 5, o.ml[1] - 5), (0, 255, 0), -1)

        # yellow contour rect: items that are moving
        try:
            draw_rects(f, [getRectsFromContours(contours)[1]], (0, 255, 255), 2)
        except TypeError:
            pass  # 'NoneType' object is not subscriptable


    @staticmethod
    def print_analytics(f, contours, hierarchy, rectangles):

        mean = np.mean([[rx, ry, rx + rw, ry + rh] for [rx, ry, rw, rh] in rectangles], axis=0, dtype=int)

        draw_rects(f, [mean], (255, 0, 0), 1)                               # 'blue meany' (average) rect
        draw_contours(f, contours, hierarchy, (64, 255, 64), 1)             # green contours
        draw_rects(f, [getLargestRect(rectangles)], (255, 255, 255), 2)     # white bounding rect
        draw_centroid(f, contours, 5, (127, 0, 255), 1)                     # purple centroid


    def process_frame(self, frame):

        self._motion = False
        self.show_krnl_grid = False
        self.show_threshold = False

        max_height = self.getMaxHeight()
        max_width = self.getMaxWidth()

        if self.plugin_process_frames:

            frame_events = []
            # IDEA: can the timing of this be adjusted? Async code to 'grab()' might
            #  be possible.
            if self.plugin_capture.capture.grab():
                ret, reference = self.plugin_capture.capture.retrieve()
            else:
                ret, reference = self.plugin_capture.capture.read()

            if self.mediapipe is True:
                self.pre_mediapipe(frame, max_height, max_width)

            if ret:
                # sliced references...
                cropped_frame = frame[max_height, max_width]
                cropped_reference = reference[max_height, max_width]
                # cv.imshow(f'cropped_frame {cropped_frame.shape}', cropped_frame)
                # cv.imshow(f'cropped_reference {cropped_reference.shape}', cropped_reference)

                greyscale_frame = cv.cvtColor(cropped_frame, cv.COLOR_BGR2GRAY)
                greyscale_refer = cv.cvtColor(cropped_reference, cv.COLOR_BGR2GRAY)
                # cv.imshow(f'greyscale_frame {greyscale_frame.shape}', greyscale_frame)
                # cv.imshow(f'greyscale_refer {greyscale_refer.shape}', greyscale_refer)

                DELTA = cv.absdiff(greyscale_frame, greyscale_refer)
                # cv.imshow(f'DELTA {DELTA.shape}', DELTA)

                BLURRED = cv.GaussianBlur(DELTA, (int(self.krnl), int(self.krnl)), 0)
                # cv.imshow(f'BLURRED {BLURRED.shape}', BLURRED)

                _, THRESHOLD = cv.threshold(BLURRED, int(np.mean(BLURRED)) + self.threshold, 255, cv.THRESH_BINARY)
                # cv.imshow(f'THRESHOLD {THRESHOLD.shape}', THRESHOLD)

                # then add text *here* so it doesn't blink and isn't analyzed.
                '''
                if self.has_symbology:
                    cv.putText(frame, "SYM", (103, 52), cv.FONT_HERSHEY_PLAIN, .80, self.majic_color, 2)

                if not self.has_symbology and not self.has_analysis:
                    cv.putText(frame, "OFF", (134, 52), cv.FONT_HERSHEY_PLAIN, .80, self.majic_color, 2)

                if self.has_analysis:
                    cv.putText(frame, "ANA", (165, 52), cv.FONT_HERSHEY_PLAIN, .80, self.majic_color, 2)
                '''
                self.processed = frame
                # cv.imshow(f'processed {self.processed.shape}', self.processed)
                # cv.imshow(f'frame {frame.shape}', frame)

                contours, hierarchy = cv.findContours(THRESHOLD, cv.RETR_TREE, cv.CHAIN_APPROX_NONE,
                                                      offset=[max_width.start, max_height.start])

                if self.show_threshold or self.threshold_hold:
                    frame[max_height, max_width] = cv.cvtColor(THRESHOLD, cv.COLOR_GRAY2BGR)

                if len(contours) > 0:

                    # TODO: change this to filter for 'volume' of contour
                    self._motion = True

                    wall, rectangles, areas = wall_images(frame, contours)  # ONLY frame.

                    self.tracked = self.tracker.track_objects(self.frame_id, contours, hierarchy, wall, rectangles, areas)

                    # TODO: log this to a file instead of saving it in memory?
                    self.events.append({
                        'f_id'           : self.frame_id,
                        'timestamp'      : datetime.now(),
                        'motion_detected': self._motion,
                        'frame_data'     : [{'tag'  : self.tracked.get(o).tag,
                                             'isNew': self.tracked.get(o).isNew,
                                             'skip' : self.tracked.get(o).skip
                                             } for o in self.tracked]
                                        })

                    # ANALYSIS
                    if self._has_analysis:
                        self.print_analytics(self.processed, contours, hierarchy, rectangles)
                else:
                    self.events.append({'f_id': self.frame_id,'timestamp': datetime.now()})

            # so it doesn't blink
            # overlay a grid based on 'kernel size' when self.krnl is being adjusted...
            if self.show_krnl_grid:

                draw_grid(self.processed, (int(self.krnl), int(self.krnl)),
                          highlight(self.processed, int(self.krnl), int(self.krnl)), 1)

            if self._has_analysis:
                for w, _ in enumerate([x for x in self.tracked][:5], 1):
                    o = self.tracked.get(_)
                    try:
                        cv.putText(self.processed, o.tag, (385, 345 + (w * 20)), cv.FONT_HERSHEY_PLAIN, .75,
                                   (255, 255, 255), 1)
                    except AttributeError as a:
                        pass

            # # SYMBOLOGY
            if self._has_symbols:
                try:

                    if self.mediapipe is True:
                        self.draw_mediapipe(self.processed)

                    self.print_symbology(self.processed, contours, self._motion, self.majic_color, self.tracked)
                except UnboundLocalError:
                    pass  # no contours? no problem.

            if self.frame_id == 0:
                self.start_streamservice()

            self.stream(self.processed)

            return self.processed

        return frame  # this will not stream if not processing!


if __name__ == "__main__":
    import atexit

    def plugin_stops():
        cam_logger.info(f"plugin stopped")

    atexit.register(plugin_stops)

    #TODO make this use the config
    thread = ShowxatingBlackviewPlugin()
    thread.plugin_name = 'blackview_test_vis'

    thread.plugin_args_capture_src = 'http://10.99.77.1/blackvue_live.cgi'
    thread.plugin_args_capture_frame_rate = 10  # see also hardcoded in CAMManager.
    thread.plugin_args_capture_width = 704
    thread.plugin_args_capture_height = 480
    thread.run()
