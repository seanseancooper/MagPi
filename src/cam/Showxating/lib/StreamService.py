import socketserver
import threading
from http import server
from typing import Tuple

import cv2 as cv
import numpy as np
import logging

cam_logger = logging.getLogger('cam_logger')


def highlight(arr, x, y):
    from PIL import Image
    # sample a pixel position and use a combinatorial 'inversion'
    # of the color value, so it's always visible.
    img = Image.fromarray(arr, "RGB")
    pix = img.load()
    R, G, B = pix[x, y]
    return (R + 128) % 255, (G + 128) % 255, (B + 128) % 255


class StreamingHandler(server.BaseHTTPRequestHandler):

    def __init__(self, request: bytes, client_address: Tuple[str, int], srvr: socketserver.BaseServer):
        super().__init__(request, client_address, srvr)

        # Class attributes
        self.src = None
        self.config_path = None

        cam_logger.debug(f"{threading.current_thread().name} created StreamingHandler for request.")

    def do_GET(self):

        if self.path == self.config_path:
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.send_header('Cache-Control',
                             'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
            self.end_headers()

            def process_frame(self, f):

                if type(f) is str:
                    # cam_logger.debug(f"{threading.current_thread().name} StreamService received {self.src} URL in process")
                    return  # we got a new URL, ignore

                try:
                    # VideoCapture yields ndarray NOT a jpeg; make a jpeg
                    params = (cv.IMWRITE_JPEG_QUALITY, 100)

                    img_str = cv.imencode('.jpeg', f, params)[1].tobytes()

                    self.wfile.write(b"\r\n--jpgboundary\r\n")
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', str(len(img_str)))
                    self.send_header('Access-Control-Expose-Headers', 'majic-color')
                    self.send_header('majic-color', str(highlight(f, 10, 110)))
                    self.end_headers()

                    self.wfile.write(img_str)
                except ConnectionResetError as e:
                    exit(0)
                except BrokenPipeError as e:
                    exit(0)

            if type(self.src) is str:
                # cam_logger.debug(f"{threading.current_thread().name} StreamService received {self.src} URL")
                return  # we got a new URL, ignore

            if type(self.src) is np.ndarray:
                # output from a plugin (an ndarray, aka 'frame').
                # let while 'do it's thing' as long as we have something...
                while self.src is not None:
                    process_frame(self, self.src)

        else:
            self.send_error(404)
            self.end_headers()


# This class is identical to HTTPServer but uses threads to handle requests by using the ThreadingMixIn. This
# is useful to handle web browsers pre-opening sockets, on which HTTPServer would wait indefinitely.
class StreamService(server.ThreadingHTTPServer):

    def __init__(self, address, config_path, requesthandler):
        super(StreamService, self).__init__(address, requesthandler)

        self.address = address
        self.requesthandler = requesthandler

        self.allow_reuse_address = True     # Whether the server will allow the reuse of an address. This defaults to False, and can be set in subclasses to change the policy.
        self.daemon_threads = True          # Use daemonic threads by setting ThreadingMixIn.daemon_threads to True to not wait until threads complete.

        self.src = None
        self.service = None

        self.config_path = config_path

    def reload(self, new_src):
        """ change direction """
        self.shutdown()

        handler = StreamingHandler  # make a NEW instance of handler.
        handler.src = new_src  # set the handlers' 'source' to the new_src.
        self.requesthandler = handler

        # BAU
        self.src = new_src
        cam_logger.debug(f"{threading.current_thread().name} StreamService set new src {new_src} and reloaded!")
        self.stream()

    def stream(self):

        self.requesthandler.config_path = self.config_path

        try:
            threading.Thread(target=self.serve_forever, name="streamservice").start()
            cam_logger.info(f"{threading.current_thread().name} streaming on http://{self.address[0]}:{self.address[1]}{self.config_path}")
        except Exception as e:
            cam_logger.error(f"streaming error on http://{self.address[0]}:{self.address[1]}{self.config_path}! " + str(e))


if __name__ == "__main__":
    import os
    from src.config.__init__ import readConfig, CONFIG_PATH

    myconfig = {}
    readConfig(os.path.join(CONFIG_PATH, 'cam.json'), myconfig)

    handler = StreamingHandler  # choose the handler.
    handler.src = myconfig.get('FORWARD_TEST_URL', myconfig['FORWARD_VIDEO_URL'])  # set the handlers' 'source'.
    svc = StreamService(('cam.localhost', 5002), '/stream', handler)
    svc.stream()


