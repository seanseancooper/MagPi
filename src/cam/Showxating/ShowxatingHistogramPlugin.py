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
    def compare_hist(self, a, b):

        if self.library == 'cv':
            distances = [euclidean_distances(a[i], b[i]) for i in ['b', 'g', 'r']]
        else:
            distances = [paired_distances(a[i], b[i]) for i in ['b', 'g', 'r']]

        return distances

    def process_frame(self, frame):
        """This method takes as frame, analyzes it and returns the analyzed frame"""

        if self.plugin_process_frames:

            # https://docs.opencv.org/4.x/d1/db7/tutorial_py_histogram_begins.html

            color = ('b', 'g', 'r')

            for i, col in enumerate(color):
                # 2 different ways to do it....

                if self.library == 'cv':
                    # images, channels, mask, histSize, ranges[, hist[, accumulate]]
                    hist = cv.calcHist([frame], [i], None,  [256], [0, 256], accumulate=False)
                else:
                    hist = exposure.histogram(frame, channel_axis=i)

                self.out_data[col] = hist
                print("color: {}, hist: {}".format(col, ",".join(str(x) for x in self.out_data[col])))

        return frame


if __name__ == "__main__":
    thread = ShowxatingHistogramPlugin()
    thread.run()
