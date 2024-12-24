from datetime import datetime
import os
import cv2 as cv
from src.config import CONFIG_PATH, readConfig


class ImageWriter:

    def __init__(self, writer_name: str):
        self.writer_name = writer_name
        self.IMAGE_OUT = None
        self.OUTFILE_NAME = None
        self.config = {}

    def write(self, writer_name: str, frame):
        readConfig('cam.json', self.config)
        self.IMAGE_OUT = self.config['PLUGIN'].get('outfile_path', '../_out')
        if writer_name:
            PATH = os.path.join(os.getcwd(), self.IMAGE_OUT, self.writer_name)
            if not os.path.exists(PATH):
                os.makedirs(PATH)

            NOW = datetime.now().strftime(self.config['DATETIME_FORMAT'])
            self.OUTFILE_NAME = os.path.join(PATH, NOW + '_' + self.config['PLUGIN'].get('outfile_name', 'cam_snap') + '.jpg')

            cv.imwrite(self.OUTFILE_NAME, frame)

        return True

    def release(self):
        pass
