from collections import defaultdict

import cv2 as cv
import numpy as np
from skimage import exposure
from sklearn.metrics.pairwise import euclidean_distances, paired_distances
from src.cam.Showxating.plugin import ShowxatingPlugin

import logging.handlers
plugin_logger = logging.getLogger('pluginManager')


class ShowxatingHistogramPlugin(ShowxatingPlugin):
    """template class for cv2 based 'plug-ins' to be
    inserted into RTSP video feed processing chains"""

    def __init__(self):
        super().__init__()
        self.f_id = 0
        self.rectangle = []
        self.greyscale_frame = None
        self.bins = 32          # TODO: make configurable
        self.out_data = {}

        self.library = ''

    def get_config(self):
        return super().get_config()

    def make_histogram(self, item, rect):

        x, y, w, h = self.rectangle = rect
        f = item[y:y + h, x:x + w]
        self.out_data = {'b': [],'g': [],'r': []}

        _ = self.process_frame(f).T
        return self.out_data

    @staticmethod
    def compare_hist(a, b, metric):
        distances = []
        # use our MSE here, add to if
        if metric == 'euclidean':
            distances = euclidean_distances(a, b)
        elif metric == 'paired':
            distances = paired_distances(a, b)
        return distances

    @staticmethod
    def compare_color_hist(a, b, metric):
        distances = []
        # use our MSE here
        if metric == 'euclidean':
            distances = [euclidean_distances(a[i], b[i]) for i in ['b', 'g', 'r']]
        elif metric == 'paired':
            distances = [paired_distances(a[i], b[i]) for i in ['b', 'g', 'r']]
        return distances

    def process_frame(self, f):
        """This method takes as frame, analyzes it and returns the analyzed frame"""

        if self.plugin_process_frames:

            # TODO: resize & kernel trick. these don't need to be so big.
            f = cv.GaussianBlur(f,(5,5),0)

            def get_hist(f):
                if self.library == 'cv':
                    # images, channels, mask, histSize, ranges[, hist[, accumulate]]
                    return cv.calcHist([f], [0], None, [self.bins], [0, 256], accumulate=False)
                else:
                    return exposure.histogram(f, nbins=self.bins, channel_axis=0)

            if self.plugin_config['color_histograms']:
                colors = ['b', 'g', 'r']
                _, _, ch = f.shape
                for i in range(ch):
                    try:
                        self.out_data[colors[i]] = np.zeros(shape=(32,1))
                        self.out_data[colors[i]] = get_hist(f[i])
                    except Exception: pass
            else:
                # get a slice
                br_x, br_y, br_w, br_h = self.rectangle
                greyscale_f = self.greyscale_frame[br_y:br_y + br_h, br_x:br_x + br_w]
                self.out_data['greyscale'] = get_hist(greyscale_f)

        return f

