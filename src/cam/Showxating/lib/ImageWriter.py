from datetime import datetime
import os
import cv2 as cv
from src.config.__init__ import CONFIG_PATH, readConfig


class ImageWriter:

    def __init__(self, writer_name: str):
        self.writer_name = writer_name
        self.IMAGE_OUT = None
        self.OUTFILE_NAME = None
        self.config = {}

    def write(self, writer_name: str, frame):
        readConfig(os.path.join(CONFIG_PATH, 'cam.json'), self.config)
        self.IMAGE_OUT = self.config['OUTFILE_PATH']
        if writer_name:
            PATH = os.path.join(os.getcwd(), self.IMAGE_OUT, self.writer_name)
            if not os.path.exists(PATH):
                os.makedirs(PATH)

            NOW = datetime.now().strftime(self.config['DATETIME_FORMAT'])
            self.OUTFILE_NAME = os.path.join(PATH, NOW + '_' + self.config['OUTFILE_NAME'] + '.jpg')

            cv.imwrite(self.OUTFILE_NAME, frame)

    def release(self):
        pass
