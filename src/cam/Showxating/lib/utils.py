import os
import cv2 as cv
import numpy as np


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


def write_imagecache(self, o, frame):

    if o.prev_tag is not None:

        if len(o.contours) > 2:
            cv.imwrite(os.path.join(self.imagecache, o.tag + '.jpeg'), frame)

        if o.aa < self.o_cache_map.get(o.prev_tag).aa:
            cv.imwrite(os.path.join(self.imagecache, o.tag + '.jpeg'), frame)

    if np.all(o.hierarchy == np.array([[[-1, -1, -1, -1]]])):
        cv.imwrite(os.path.join(self.imagecache, o.tag + '.jpeg'), o.wall)


def diff_areas(a, b):
    return a - b


def getLargestRect(rectangleList):
    """ the region of interest """

    def largest_rect(rectangles):
        xs = []
        ys = []
        ws = []
        hs = []
        [(xs.append(d[0]), ys.append(d[1]), ws.append(d[2]), hs.append(d[3])) for d in [r for r in rectangles]]
        return np.min(xs), np.min(ys), np.max(xs) + ws[xs.index(np.max(xs))], np.max(ys) + hs[ys.index(np.max(ys))]

    return largest_rect(rectangleList)


def getLargestArea(areasList):
    """ the *actual* area of what is being analyzed """

    def largest_area(areas):
        # TODO numpy arrays
        ws = []
        hs = []
        ds = []
        [(ws.append(a[0]), hs.append(a[1]), ds.append(a[2])) for a in areas]
        return np.max(ws), np.max(hs), np.max(ds)

    return largest_area(areasList)

