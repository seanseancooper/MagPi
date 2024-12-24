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
        self._kz = (3,3)
        self.library = ''
        self.bins = 32
        self.rectangle = []
        self.greyscale_frame = None
        self.out_data = {}

    def get_config(self):
        super().get_config()
        # self._kz = self.plugin_config('krnl')
        self.bins = self.plugin_config.get('bins', 32)
        self.library = self.plugin_config.get('library', 'cv')

    def make_histogram(self, item, rect):

        x, y, w, h = self.rectangle = rect
        f = item[y:y + h, x:x + w]
        self.out_data = {'b': [],'g': [],'r': []}

        _ = self.process_frame(f).T
        return self.out_data

    def compare_hist(self, a, b, metric):

        if self.plugin_config['color_histograms']:
            colors = ['b', 'g', 'r']
            for i in range(len(a)):
                if metric == 'euclidean':
                    return euclidean_distances(a[colors[i]], b[colors[i]])
                elif metric == 'paired':
                    return paired_distances(a[colors[i]], b[colors[i]])
        else:
            if metric == 'euclidean':
                return euclidean_distances(a, b)
            elif metric == 'paired':
                return paired_distances(a, b)

    def process_frame(self, f):
        """This method takes as frame, analyzes it and returns the analyzed frame"""

        if self.plugin_process_frames:

            def get_hist(f):
                if self.library == 'cv':
                    # images, channels, mask, histSize, ranges[, hist[, accumulate]]
                    return cv.calcHist([f], [0], None, [self.bins], [0, 256], accumulate=False)
                else:
                    # If channel_axis is not set, the histogram is computed on the flattened image.
                    return exposure.histogram(f, nbins=self.bins, channel_axis=0)

            # kernel size from plugin UI
            f = cv.GaussianBlur(f, self._kz, 0)

            if self.plugin_config['color_histograms']:
                colors = ['b', 'g', 'r']
                _, _, ch = f.shape
                for i in range(ch):
                    try:
                        self.out_data[colors[i]] = np.zeros(shape=(self.bins, 1))
                        self.out_data[colors[i]] = get_hist(f[i])
                    except Exception: pass
            else:
                # get a slice
                br_x, br_y, br_w, br_h = self.rectangle
                greyscale_f = self.greyscale_frame[br_y:br_y + br_h, br_x:br_x + br_w]
                self.out_data['greyscale'] = get_hist(greyscale_f)

        return f

