import cv2 as cv
import numpy as np

from src.lib.utils import generate_uuid


def getRectsFromContours(contours):
    rects = np.empty(shape=(1, 4), dtype=np.int32)

    if contours:
        rects = np.append(rects, [np.array(cv.boundingRect(cnt), dtype=np.int32) for cnt in contours], axis=0)
        return rects


def sortedContours(contours):
    # key=cv.isContourConvex, reverse=True)
    # key=cv.boundingRect, reverse=True)
    # key=cv.fitEllipse, reverse=True)
    a = sorted(contours, key=cv.contourArea, reverse=True)
    # a = sorted(contours, key=cv.minAreaRect, reverse=True)
    # a = sorted(contours, key=cv.minEnclosingCircle, reverse=True)
    return a


def getLargestRect(rects):
    return np.sort(rects, axis=1)


def getAggregatedRect(rects):
    """ the region of interest """
    xs = []
    ys = []
    ws = []
    hs = []

    [(xs.append(d[0]), ys.append(d[1]), ws.append(d[2]), hs.append(d[3])) for d in [r for r in rects]]
    aggregated = np.min(xs), np.min(ys), np.max(ws), np.max(hs)

    return aggregated


def draw_circle(frag, x, y, rad, clr, fill):
    if x > 0 and y > 0:
        cv.circle(frag, (x, y), rad, clr, fill)


def draw_rects(frag, rects, clr, fill):
    if np.any(rects):
        [cv.rectangle(frag, (x, y), (x+w, y+h), clr, fill) for x, y, w, h in rects]


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


def is_inside(pt, rect):
    x, y = pt
    rx, ry, rw, rh = rect
    return rx < x < rx+rw and ry < y < ry+rh


def is_in_range(val, initial, offset):
    lwr = initial - offset
    upp = initial + offset

    return bool(lwr < val < upp)


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

def get_mean_locations(contours):  # contours are sorted.
    _locs = []
    _cnts = []
    for cnt in contours:
        _x = []
        _y = []
        [(_x.append(a), _y.append(b)) for [[a, b]] in cnt]

        _cnts.append({id: generate_uuid()})
        _locs.append({id: np.mean(np.array([_x, _y]), axis=1, dtype=int)})

    return _locs, _cnts

# c_grps_locs, c_grps_cnts = get_mean_locations(contours)  # contourGroups


def getAggregatedRects(rects):
    """ the region of interest """
    xs = []
    ys = []
    ws = []
    hs = []

    [(xs.append(d[0]), ys.append(d[1]), ws.append(d[2]), hs.append(d[3])) for d in [r for r in rects]]
    aggregated = [np.min(xs), np.min(ys), np.max(ws), np.max(hs)]

    return aggregated


def wall_images(frame, conts):
    canvas = np.zeros(frame.shape, np.uint8)
    wall = np.zeros(frame.shape, np.uint8)
    rectangle = None
    dists = []

    # https://stackoverflow.com/questions/48979219/opencv-composting-2-images-of-differing-size
    def combine_images(paint, canvas, anchor_y, anchor_x):
        fg, c = paint, canvas  # no refs

        # Check if the foreground is inbound with the new coordinates
        # and raise an error if out of bounds
        bg_height = c.shape[0]
        bg_width = c.shape[1]
        fg_height = fg.shape[0]
        fg_width = fg.shape[1]

        if fg_height + anchor_y > bg_height or fg_width + anchor_x > bg_width:
            raise ValueError("The foreground image exceeds the background boundaries at this location")

        anchor_y_end = anchor_y + fg_height
        anchor_x_end = anchor_x + fg_width

        alpha = 1.0
        c[anchor_y:anchor_y_end, anchor_x:anchor_x_end, :] = cv.addWeighted(fg,
                 alpha,
                 c[anchor_y:anchor_y + fg_height, anchor_x:anchor_x + fg_width:],
                 1-alpha,
                 0,
                 c)

        return c

    if conts.any() or conts:

        # this will be a 'contourGroup', get 'bounds' of members
        rectangle = br_x, br_y, br_w, br_h = cv.boundingRect(conts)
        cnt_img = frame[br_y:br_y + br_h, br_x:br_x + br_w]  # as numpy rows, cols...
        wall = combine_images(cnt_img, canvas, br_y, br_x)

    # rectangle is bounds of contourGroup
    return wall, rectangle


def calculate_contour_distance(contour1, contour2):
    x1, y1, w1, h1 = cv.boundingRect(contour1)
    c_x1 = x1 + w1/2
    c_y1 = y1 + h1/2

    x2, y2, w2, h2 = cv.boundingRect(contour2)
    c_x2 = x2 + w2/2
    c_y2 = y2 + h2/2

    return max(abs(c_x1 - c_x2) - (w1 + w2)/2, abs(c_y1 - c_y2) - (h1 + h2)/2)


def merge_contours(contour1, contour2):
    return np.concatenate((contour1, contour2), axis=0)


def agglomerative_cluster(contours, threshold_distance=40.0):
    current_contours = contours
    while len(current_contours) > 1:
        min_distance = None
        min_coordinate = None

        for x in range(len(current_contours)-1):
            for y in range(x+1, len(current_contours)):
                distance = calculate_contour_distance(current_contours[x], current_contours[y])
                if min_distance is None:
                    min_distance = distance
                    min_coordinate = (x, y)
                elif distance < min_distance:
                    min_distance = distance
                    min_coordinate = (x, y)

        if min_distance < threshold_distance:
            index1, index2 = min_coordinate
            current_contours[index1] = merge_contours(current_contours[index1], current_contours[index2])
            del current_contours[index2]
        else:
            break

    return current_contours

