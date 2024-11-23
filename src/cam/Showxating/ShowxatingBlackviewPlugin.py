from datetime import datetime
import os
import cv2 as cv
import numpy as np

from src.cam.Showxating.plugin import ShowxatingPlugin
from src.cam.Showxating.lib.ImageWriter import ImageWriter
from src.cam.Showxating.lib.FrameObjektTracker import FrameObjektTracker
from src.cam.Showxating.lib.StreamService import StreamService, StreamingHandler, highlight
import logging

cam_logger = logging.getLogger('cam_logger')


def getRectsFromContours(contours):
    rects = np.empty(shape=(1, 4), dtype=np.int32)

    def make_rect(cnt):
        cnt_x, cnt_y, cnt_w, cnt_h = cv.boundingRect(cnt)
        return [cnt_x, cnt_y, cnt_w + cnt_x, cnt_h + cnt_y]  # note modifications

    if contours:
        rects = np.append(rects, [np.array(make_rect(cnt), dtype=np.int32) for cnt in contours], axis=0)
        return rects


def getLargestRect(rectangleList):
    def largest_rect(rectangles):
        xs = []
        ys = []
        ws = []
        hs = []
        [(xs.append(d[0]), ys.append(d[1]), ws.append(d[2]), hs.append(d[3])) for d in [r for r in rectangles]]
        return np.min(xs), np.min(ys), np.max(xs) + ws[xs.index(np.max(xs))], np.max(ys) + hs[ys.index(np.max(ys))]

    return largest_rect(rectangleList)


def wall_images(frame, cont):
    canvas = np.zeros(frame.shape, np.uint8)
    wall = np.zeros(frame.shape, np.uint8)
    rectangles = []
    areas = []

    # https://stackoverflow.com/questions/48979219/opencv-composting-2-images-of-differing-size
    def combine_images(image1, image2, anchor_y, anchor_x):
        foreground, background = image1.copy(), image2.copy()

        # Check if the foreground is inbound with the new coordinates and raise an error if out of bounds
        background_height = background.shape[0]
        background_width = background.shape[1]
        foreground_height = foreground.shape[0]
        foreground_width = foreground.shape[1]

        if foreground_height + anchor_y > background_height or foreground_width + anchor_x > background_width:
            raise ValueError("The foreground image exceeds the background boundaries at this location")

        alpha = 1.0

        # do composite at specified location
        start_y = anchor_y
        start_x = anchor_x
        end_y = anchor_y + foreground_height
        end_x = anchor_x + foreground_width

        blended_portion = cv.addWeighted(foreground,
                                         alpha,
                                         background[start_y:end_y, start_x:end_x, :],
                                         1 - alpha,
                                         0,
                                         background)

        background[start_y:end_y, start_x:end_x, :] = blended_portion
        # cv.imshow('background', background)
        # cv.imshow('blended_portion', blended_portion)
        areas.append(blended_portion.shape)
        return background

    # TODO: do list comps here
    # if contours:
    #     fragments = [(frame[br_y:br_y + br_h, br_x:br_x + br_w], br_y, br_x) for br_x, br_y, br_w, br_h in self.getRectsFromContours(contours)]
    #     walls = [combine_images(fragment, canvas, br_y, br_x) for (fragment, br_y, br_x) in fragments]
    #     wall = [combine_images(_, canvas, br_y, br_x) for _ in walls]

    # wall = [combine_images(cnt_img, canvas, br_y, br_x) for cnt_img, br_x, br_y in
    #         [(frame[br_y:br_y + br_h, br_x:br_x + br_w], br_x, br_y) for br_x, br_y, br_w, br_h in
    #          self.getRectsFromContours(contours)]]

    if cont:
        # TODO: get rid of this loop
        #  "for i, cnt in np.arange(len(contours))"
        #  "
        for cnt in cont:
            br_x, br_y, br_w, br_h = cv.boundingRect(cnt)
            # convert to numpy rows, cols...
            cnt_img = frame[br_y:br_y + br_h, br_x:br_x + br_w]
            wall = combine_images(cnt_img, canvas, br_y, br_x)
            # cam_logger.debug(f"wall append rectangle: [{br_x, br_y, br_w, br_h}]")
            rectangles.append([br_x, br_y, br_w, br_h])

    return wall, rectangles, areas


def warp_perspective(frame):
    # LENS BENT: transformation on the remaining ROI
    # to improve detection ^ tracking
    # The lens is 'wide-angle'; Mediapipe frames are corrected
    # to preserve human dimensions in the image

    rows, cols, ch = frame.shape
    cntr_pt = [[352, 225]]

    left_pt = [342, 225]
    rght_pt = [362, 225]
    top_pt = [352, 214]
    bot_pt = [352, 236]

    wrp_left = [352, 211]  # sub from y
    wrp_rght = [352, 239]  # add to y
    wrp_top = [339, 225]  # sub from x
    wrp_bot = [365, 225]  # add to x

    pts1 = [top_pt, bot_pt, left_pt, rght_pt]
    pts2 = [wrp_left, wrp_rght, wrp_top, wrp_bot]

    # TODO: use draw_circle() here
    [cv.circle(frame, (x, y), 1, (0, 255, 0), -1) for x, y in pts1]
    [cv.circle(frame, (x, y), 1, (0, 0, 255), -1) for x, y in pts2]

    M = cv.getPerspectiveTransform(np.float32(pts1), np.float32(pts2))
    return cv.warpPerspective(frame[125:350, 0:704], M, (704, 350))


def draw_circle(frag, x, y, rad, clr, fill):
    if x > 0 and y > 0:
        cv.circle(frag, (x, y), rad, clr, fill)


def draw_centroid(frame, cont, rad, clr, fill):
    try:
        M = cv.moments(cont[0])
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        draw_circle(frame, cx, cy, rad, clr, fill)
        return cx, cy
    except IndexError:
        pass
    except ZeroDivisionError:
        pass


def draw_contours(frag, cont, hier, clr, strk):
    [cv.drawContours(frag, cont, contour_idx, clr, strk, cv.LINE_8, hier, 0) for contour_idx in
     range(len(cont))]


def draw_rects(frag, rects, clr, fill):
    if np.any(rects):
        [cv.rectangle(frag, (x, y), (w, h), clr, fill) for x, y, w, h in rects]


class ShowxatingBlackviewPlugin(ShowxatingPlugin):

    def __init__(self):
        super().__init__()
        self.WORK_AREA = tuple[0:345, 0:704]
        self.max_height = slice(125, 345)  # view height is 220px
        self.max_width = slice(0, 704)  # view width, not 'step'

        self.has_symbology = True
        self.ssid_key = "SSID"
        self.signal_key = "Signal"

        # hyper parameters
        self.krnl = 17  # controls size of items considered relevant
        self.show_krnl_grid = False
        self.kernel_sz = (int(self.krnl), int(self.krnl))
        self.threshold = 15.0  # value of pixels additional to the mean during thresholding

        self.show_threshold = False
        self.threshold_hold = False

        self.mediapipe = False  # mp is slow!
        self.pose = None
        self.result_T = None  # medipipe result

        self.has_analysis = False
        self.motion_detected = False

        self.tracker = FrameObjektTracker()
        self.events = []  # list of events
        self.tracked = {}

        self.speaker = None  # TODO: deprecated
        self.streamservice = None
        self.processed = None

    def get_config(self):

        super().get_config()

        # self.speaker = Enunciator('BLACKVIEW_TEST_VIS', self.plugin_config['tokens'], self.plugin_config['interval'])
        # self.speaker.config['BLACKVIEW_TEST_VIS'] = self.plugin_config
        # self.speaker.configure()

        self.tracker.config(self.plugin_config['f_limit'], self.plugin_config['frame_delta'],
                            self.plugin_config['frm_delta_pcnt'])

        return

    def write_imagecache(self, o, frame):
        # write to imagecache for KNN classifier
        # frames with aligned contour and largest rect areas

        if o.prev_tag is not None:

            if len(o.contours) > 2:
                cv.imwrite(os.path.join(self.imagecache, o.tag + '.jpeg'), frame)

            if o.aa < self.o_cache_map.get(o.prev_tag).aa:
                cv.imwrite(os.path.join(self.imagecache, o.tag + '.jpeg'), frame)

        if np.all(o.hierarchy == np.array([[[-1, -1, -1, -1]]])):
            cv.imwrite(os.path.join(self.imagecache, o.tag + '.jpeg'), o.wall)

    def stream(self, frame):
        if self.plugin_config['streams'] is True:
            if self.streamservice is not None:
                self.streamservice.requesthandler.src = frame

    def print_symbology(self, f, contours):

        # delimit the work area
        cv.line(f, (0, 125), (704, 125), self.majic_color, 1)
        cv.line(f, (0, 345), (704, 345), self.majic_color, 1)

        if self.motion_detected:
            cv.putText(f, "MOTION DETECTED!", (5, 110), cv.FONT_HERSHEY_PLAIN, 1.0, self.majic_color, 2)
            # self.speaker.broadcast("MOTION DETECTED!")

        # green dot: items being tracked
        for _ in self.tracked:
            o = self.tracked.get(_)
            cv.rectangle(f, o.ml, (o.ml[0] - 5, o.ml[1] - 5), (0, 255, 0), -1)

        # yellow contour rect: items that are moving
        try:
            draw_rects(f, [getRectsFromContours(contours)[1]], (0, 255, 255), 2)
        except TypeError:
            pass  # 'NoneType' object is not subscriptable

        # IDEA: instead of mediapipe, look at the aspect ratio of the moving
        # contour (yellow); if there are more vertical than horizontal pixels, the
        # object is *probably* human. If not, it's *probably* a car.
        # Bayesian inference could be used here since we have a binary
        # output, and based on previous estimations of aspetc ratio
        # we can make a prediction.
        # This seems like a far less expensivve way to do what I need; I don't
        # really care about 'pose' estimation here; in an 'intent driven' scenario,
        # proximity is already enough.

        # having said that, mediapipe alone takes ~5 seconds to spin
        # up -- the issue is in my code!

        if self.mediapipe is True:
            import mediapipe as mp
            mp_pose = mp.solutions.pose

            def draw_pose(fragment, result):
                if result.pose_landmarks is not None:
                    mp_drawing = mp.solutions.drawing_utils
                    mp_drawing_styles = mp.solutions.drawing_styles
                    mp_drawing.draw_landmarks(fragment, result.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                              landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

            if self.result_T is not None:
                if self.result_T.pose_landmarks is not None:
                    draw_pose(f, self.result_T)

    def print_analytics(self, f, contours, hierarchy, rectangles):

        # get cache map data; returns list of tagged & matched 'o'
        # [print(f"o created at: {tracked.get(o).timestamp}") for o in tracked.keys()]

        mean = np.mean([[rx, ry, rx + rw, ry + rh] for [rx, ry, rw, rh] in rectangles], axis=0, dtype=int)

        draw_rects(f, [mean], (255, 0, 0), 1)  # 'blue meany' (average) rect
        draw_contours(f, contours, hierarchy, (64, 255, 64), 1)  # green contours
        draw_rects(f, [getLargestRect(rectangles)], (255, 255, 255), 2)  # white bounding rect
        draw_centroid(f, contours, 5, (127, 0, 255), 1)  # purple centroid

        # pull in 'averaged' from diff_rectangles
        # [diff_rectangles(rs, rs_prev, processed) for _ in tracked]

        # pull l2 norm of current cont
        # rx, ry, rw, rh = getLargestRect(rectangles)
        # [diff_contours(cont, cont_prev, shape, rx, ry, rw, rh) for _ in tracked]

    def sets_threshold_hold(self, value):
        if value is True:
            self.threshold_hold = True;
        elif value is False:
            self.threshold_hold = False;

    def sets_mediapipe(self, value):
        if value is True:
            self.mediapipe = True;
        elif value is False:
            self.mediapipe = False;

    def start_streamservice(self):

        if self.streamservice is not None:
            self.streamservice.shutdown()
            self.streamservice = None
        handler = StreamingHandler
        handler.src = self.processed
        self.streamservice = StreamService(('localhost', self.plugin_config['streaming_port']),
                                           self.plugin_config['streaming_path'], handler)
        self.streamservice.stream()

    def cam_snap(self):

        # IDEA: It may be more efficient to
        #  write frames via delegation than by force ('we've got that "B" roll!').

        #TODO: write to imagecache, or create a vector that can later be compared.

        def _snap(frame):
            if frame is not None:
                writer = ImageWriter("CAMManager")
                writer.write("CAM_SNAP", frame)

        # NOFIX: throttle me; I can be overloaded by requests
        #  and crash the capture! [this is for stills, not movies. Not fixing it.]
        for frame in self.plugin_capture.run():
            _snap(frame)
            break

    def getMaxHeight(self):
        return self.max_height

    def getMaxWidth(self):
        return self.max_width

    # @timer
    def process_frame(self, frame):
        # 'process_frame' :0.0660 secs avg: 0.04014569751740745 < w/MediaPipe
        # 'process_frame' :0.0121 secs avg: 0.01590019583518516 < w/FrameObjektTracker
        # 'process_frame' :0.0414 secs avg: 0.05433940612135726 < KNN classifier, live data
        # 'process_frame' :0.0491 secs avg: 0.033803447738023976
        # 'process_frame' :0.0427 secs avg: 0.035632539323980666
        # 'process_frame' :0.0352 secs avg: 0.03165668891851849
        self.motion_detected = False
        self.show_krnl_grid = False
        self.show_threshold = False

        # print(f" self.start_time {self.start_time} "
        #       f"self.frame_rate {self.frame_rate} "
        #       f"self.elapsed_frames {self.elapsed_frames} "
        #       f"self.frame_delta {self.frame_delta} "
        #       f"self.frame_id {self.frame_id} "
        #       f"self.majic_color {self.majic_color}")

        # localized
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
                import mediapipe as mp
                mp_pose = mp.solutions.pose
                self.pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
                # BGR_T = cv.cvtColor(warp_perspective(frame), cv.COLOR_RGB2BGR)
                BGR_T = cv.cvtColor(frame[max_height, max_width], cv.COLOR_RGB2BGR)
                # cv.imshow('BGR_T', BGR_T)
                self.result_T = self.pose.process(BGR_T)

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

                # show the THRESHOLD when self.threshold is changing or threshold_hold ('∞') is enabled
                if self.show_threshold or self.threshold_hold:
                    frame[max_height, max_width] = cv.cvtColor(THRESHOLD, cv.COLOR_GRAY2BGR)

                cam_logger.debug(
                        f"{len(contours)} contours found in frame {self.frame_id} hierarchy: {hierarchy}".replace('\n',
                                                                                                                  ''))

                if len(contours) > 0:

                    # TODO: change this to filter for 'volume' of contour
                    self.motion_detected = True

                    wall, rectangles, areas = wall_images(frame, contours)  # ONLY frame.

                    self.tracked = self.tracker.track_objects(self.frame_id, contours, hierarchy, wall, rectangles, areas)

                    self.events.append({
                        'f_id'           : self.frame_id,
                        'timestamp'      : datetime.now(),
                        'motion_detected': self.motion_detected,
                        'frame_data'     : [{'tag'  : self.tracked.get(o).tag,
                                             'isNew': self.tracked.get(o).isNew,
                                             'skip' : self.tracked.get(o).skip
                                             } for o in self.tracked]
                                        })

                    # ANALYSIS
                    if self.has_analysis:
                        self.print_analytics(self.processed, contours, hierarchy, rectangles)
                else:
                    self.events.append({'f_id': self.frame_id,'timestamp': datetime.now()})

            # so it doesn't blink
            # overlay a grid based on 'kernel size' when self.krnl is being adjusted...
            if self.show_krnl_grid:

                def draw_grid(f, grid_shape, color, thickness):
                    h, w, _ = f.shape
                    rows, cols = grid_shape

                    # draw vertical lines
                    for x in np.arange(start=0, stop=w, step=cols):
                        x = int(round(x))
                        cv.line(f, (x, 125), (x, 345), color=color, thickness=thickness)

                    # draw horizontal lines
                    for y in np.arange(start=125, stop=345, step=rows):
                        y = int(round(y))
                        cv.line(f, (0, y), (w, y), color=color, thickness=thickness)

                    return f

                draw_grid(self.processed, (int(self.krnl), int(self.krnl)),
                          highlight(self.processed, int(self.krnl), int(self.krnl)), 1)

            if self.has_analysis:
                for w, _ in enumerate([x for x in self.tracked][:5], 1):
                    o = self.tracked.get(_)
                    try:
                        cv.putText(self.processed, o.tag, (385, 345 + (w * 20)), cv.FONT_HERSHEY_PLAIN, .75,
                                   (255, 255, 255), 1)
                    except AttributeError as a:
                        pass

            # # SYMBOLOGY
            if self.has_symbology:
                try:
                    self.print_symbology(self.processed, contours)
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
        [cam_logger.debug(f"{evt}") for evt in thread.events]
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
