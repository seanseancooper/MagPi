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

    def write(self, writer_name: str, frame, f_id=None):
        readConfig('cam.json', self.config)
        self.IMAGE_OUT = self.config['PLUGIN'].get('outfile_path', '../_out')
        if writer_name:
            PATH = os.path.join(os.getcwd(), self.IMAGE_OUT, self.writer_name)
            if not os.path.exists(PATH):
                os.makedirs(PATH)

            NOW = datetime.now().strftime(self.config['DATETIME_FORMAT'])
            filename = f"{NOW}_{self.config['PLUGIN'].get('outfile_name', 'cam_snap')}.jpg"

            if f_id is not None:
                filename = f"{str(f_id)}_{filename}"

            self.OUTFILE_NAME = os.path.join(PATH, filename)
            cv.imwrite(self.OUTFILE_NAME, frame)

        return True

    def release(self):
        pass
