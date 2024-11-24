import socketserver
import threading
from http import server
from typing import Tuple

import cv2 as cv
import numpy as np
import logging

cam_logger = logging.getLogger('cam_logger')


def highlight(arr, x, y):
    """sample a pixel position; use combinatorial 'inversion'
    of the color to produce a new color that is always visible."""
    from PIL import Image
    img = Image.fromarray(arr, "RGB")
    pix = img.load()
    R, G, B = pix[x, y]
    return (R + 128) % 255, (G + 128) % 255, (B + 128) % 255


class StreamingHandler(server.BaseHTTPRequestHandler):

    def __init__(self, request: bytes, client_address: Tuple[str, int], srvr: socketserver.BaseServer):
        super().__init__(request, client_address, srvr)
        self.src = None
        self.context = None
        self.highlight = ()

    def do_GET(self):

        if self.path == self.context:

            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.send_header('Cache-Control',
                             'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
            self.end_headers()

            if type(self.src) is str:  # a new URL
                return

            if type(self.src) is np.ndarray:  # a plugin frame

                while self.src is not None:

                    self.highlight = highlight(self.src, 10, 110)

                    def process_frame(sh, f):

                        if type(f) is str:
                            return  # a new URL

                        try:
                            p = (cv.IMWRITE_JPEG_QUALITY, 100)
                            img_str = cv.imencode('.jpeg', f, p)[1].tobytes()

                            sh.wfile.write(b"\r\n--jpgboundary\r\n")
                            sh.send_header('Content-type', 'image/jpeg')
                            sh.send_header('Content-length', str(len(img_str)))
                            sh.send_header('Access-Control-Expose-Headers', 'majic-color')
                            sh.send_header('majic-color', str(self.highlight))
                            sh.end_headers()

                            sh.wfile.write(img_str)
                        except ConnectionResetError:
                            pass
                        except BrokenPipeError:
                            pass

                    process_frame(self, self.src)

        else:
            self.send_error(404)
            self.end_headers()


class StreamService(server.ThreadingHTTPServer):

    def __init__(self, address, context, handler):
        super(StreamService, self).__init__(address, handler)

        self.address = address
        self.context = context
        self.handler = handler

        self.allow_reuse_address = True     # will server will allow the reuse of an address
        self.daemon_threads = True          # True not wait until threads complete.

        self.src = None

    def reload(self, new_src):
        """ change direction """
        self.shutdown()

        h = StreamingHandler      # make a NEW instance of handler.
        h.src = new_src           # set the handlers' 'source' to the new_src.
        self.handler = h

        self.src = new_src
        self.stream()

    def stream(self):

        self.handler.context = self.context

        try:
            threading.Thread(target=self.serve_forever, name="streamservice").start()
            cam_logger.info(f"{threading.current_thread().name} streaming on http://{self.address[0]}:{self.address[1]}{self.context}")
        except Exception as e:
            cam_logger.error(f"streaming error on http://{self.address[0]}:{self.address[1]}{self.context}! " + str(e))


if __name__ == "__main__":
    import os
    from src.config.__init__ import readConfig, CONFIG_PATH

    # myconfig = {}
    # readConfig(os.path.join(CONFIG_PATH, 'cam.json'), myconfig)
    #
    # handler = StreamingHandler  # choose the handler.
    # handler.src = myconfig.get('FORWARD_TEST_URL', myconfig['FORE_VIDEO_URL'])  # set the handlers' 'source'.
    # host, port = myconfig.get('SERVER_NAME').split(':')
    # svc = StreamService((host, int(port)), '/stream', handler)
    # svc.src = handler.src
    # svc.stream()


