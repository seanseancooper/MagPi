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
        self.compare_method = None
        self.norm_type = None
        self.out_data = {}

    def get_config(self):
        super().get_config()
        # self._kz = self.plugin_config('krnl')
        self.bins = self.plugin_config.get('bins', 32)
        self.library = self.plugin_config.get('library', 'cv')

    def get_histogram(self, item, rect):

        x, y, w, h = self.rectangle = rect
        f = item[y:y + h, x:x + w]
        self.out_data = {'b': [], 'g': [], 'r': []}

        return self.process_frame(f).T

    def normalize_channels(self, hist):
        if True:
            colors = ['b', 'g', 'r']
            for i in range(len(colors)):
                try:
                    cv.normalize(hist[colors[i]], hist[colors[i]], alpha=0, beta=1, norm_type=self.norm_type)
                except Exception:
                    pass

    def compare_hist(self, a, b):
        return cv.compareHist(a, b, self.compare_method)


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

            return get_hist(f)

        return f

