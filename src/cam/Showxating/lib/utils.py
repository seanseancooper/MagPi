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


def draw_circle(frag, x, y, rad, clr, fill):
    if x > 0 and y > 0:
        cv.circle(frag, (x, y), rad, clr, fill)


def draw_rects(frag, rects, clr, fill):
    if np.any(rects):
        [cv.rectangle(frag, (x, y), (w, h), clr, fill) for x, y, w, h in rects]


def draw_contours(frag, conts, hier, clr, strk):
    [cv.drawContours(frag, conts, contour_idx, clr, strk, cv.LINE_8, hier, 0) for contour_idx in range(len(conts))]


def draw_centroid(f, conts, rad, clr, fill):
    try:
        M = cv.moments(conts[0])
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        draw_circle(f, cx, cy, rad, clr, fill)
        return cx, cy
    except IndexError: pass
    except ZeroDivisionError: pass


def draw_grid(f, grid_shape, color, thickness):
    # do this in javascript
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


def wall_images(frame, conts):
    canvas = np.zeros(frame.shape, np.uint8)
    wall = np.zeros(frame.shape, np.uint8)
    rectangles = []
    areas = []

    # https://stackoverflow.com/questions/48979219/opencv-composting-2-images-of-differing-size
    def combine_images(image1, image2, anchor_y, anchor_x):
        fg, bg = image1.copy(), image2.copy()

        # Check if the foreground is inbound with the new coordinates and raise an error if out of bounds
        bg_height = bg.shape[0]
        bg_width = bg.shape[1]
        fg_height = fg.shape[0]
        fg_width = fg.shape[1]

        if fg_height + anchor_y > bg_height or fg_width + anchor_x > bg_width:
            raise ValueError("The foreground image exceeds the background boundaries at this location")

        alpha = 1.0

        blended = cv.addWeighted(fg, alpha, bg[
                                         anchor_y:anchor_y + fg_height,
                                         anchor_x:anchor_x + fg_width,
                                         :], 1-alpha, 0, bg)

        anchor_y_end = anchor_y + fg_height
        anchor_x_end = anchor_x + fg_width

        bg[anchor_y:anchor_y_end, anchor_x:anchor_x_end, :] = blended
        # cv.imshow('background', bg)
        # cv.imshow('blended_portion', blended)

        areas.append(blended.shape)
        return bg

    if conts:
        # TODO: get rid of this loop

        # fragments = [(frame[br_y:br_y + br_h, br_x:br_x + br_w], br_y, br_x) for br_x, br_y, br_w, br_h in self.getRectsFromContours(contours)]
        # walls = [combine_images(fragment, canvas, br_y, br_x) for (fragment, br_y, br_x) in fragments]
        # wall = [combine_images(_, canvas, br_y, br_x) for _ in walls]

        # wall = [combine_images(cnt_img, canvas, br_y, br_x) for cnt_img, br_x, br_y in
        #         [(frame[br_y:br_y + br_h, br_x:br_x + br_w], br_x, br_y) for br_x, br_y, br_w, br_h in
        #          self.getRectsFromContours(contours)]]

        for cnt in conts:
            br_x, br_y, br_w, br_h = cv.boundingRect(cnt)

            cnt_img = frame[br_y:br_y + br_h, br_x:br_x + br_w]  # as numpy rows, cols...
            wall = combine_images(cnt_img, canvas, br_y, br_x)

            # cam_logger.debug(f"wall append rectangle: [{br_x, br_y, br_w, br_h}]")
            rectangles.append([br_x, br_y, br_w, br_h])

    return wall, rectangles, areas


# def write_imagecache(self, o, frame):
#
#     if o.prev_tag is not None:
#
#         if len(o.contours) > 2:
#             cv.imwrite(os.path.join(self.imagecache, o.tag + '.jpeg'), frame)
#
#         if o.aa < self.o_cache_map.get(o.prev_tag).aa:
#             cv.imwrite(os.path.join(self.imagecache, o.tag + '.jpeg'), frame)
#
#     if np.all(o.hierarchy == np.array([[[-1, -1, -1, -1]]])):
#         cv.imwrite(os.path.join(self.imagecache, o.tag + '.jpeg'), o.wall)
