import cv2 as cv
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
        self.out_data = {}

        self.library = ''

    def get_config(self):
        return super().get_config()

    def make_histogram(self, f, rect):

        x, y, w, h = rect
        f_region = f[y:y + h, x:x + w]

        _ = self.process_frame(f_region).T
        return self.out_data

    @staticmethod
    def compare_hist(a, b, metric):
        distances = []
        if metric == 'euclidean':
            distances = [euclidean_distances(a[i], b[i]) for i in ['b', 'g', 'r']]
        elif metric == 'paired':
            distances = [paired_distances(a[i], b[i]) for i in ['b', 'g', 'r']]
        return distances

    def process_frame(self, f):
        """This method takes as frame, analyzes it and returns the analyzed frame"""
        cv.imshow('f', f)  # broken??

        if self.plugin_process_frames:

            # TODO: resize & kernel trick. these don't need to be so big.

            if self.plugin_config['color_histograms']:

                # https://docs.opencv.org/4.x/d1/db7/tutorial_py_histogram_begins.html

                color = ('b', 'g', 'r')

                for i, col in enumerate(color):
                    # 2 different ways to do it....

                    if self.library == 'cv':
                        # images, channels, mask, histSize, ranges[, hist[, accumulate]]
                        hist = cv.calcHist([f], [i], None, [32], [0, 256], accumulate=False)
                    else:
                        hist = exposure.histogram(f, channel_axis=i)

                    self.out_data[col] = hist
                    print("color: {}, hist: {}".format(col, ",".join(str(x) for x in self.out_data[col])))

            else:
                # IDEA: use the greyscale_frame from the plugin.
                greyscale_f = cv.cvtColor(f, cv.COLOR_BGR2GRAY)
                if self.library == 'cv':
                    # images, channels, mask, histSize, ranges[, hist[, accumulate]]
                    hist = cv.calcHist([greyscale_f], [0], None, [32], [0, 256], accumulate=False)
                else:
                    hist = exposure.histogram(greyscale_f, channel_axis=0)

                self.out_data['greyscale'] = hist
                print(f"hist: {hist}")

        return f


if __name__ == "__main__":
    thread = ShowxatingHistogramPlugin()
    thread.run()
