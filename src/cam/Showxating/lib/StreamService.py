import socketserver
import threading
from http import server
from typing import Tuple

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
        self.config_path = None
        cam_logger.debug(f"{threading.current_thread().name} created StreamingHandler for request.")

    def do_GET(self):

        if self.path == self.config_path:

            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.send_header('Cache-Control',
                             'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
            self.end_headers()

            if type(self.src) is str:  # a new URL
                cam_logger.debug(f"{threading.current_thread().name} StreamService received {self.src} URL")
                return

            if type(self.src) is np.ndarray:  # a plugin frame

                while self.src is not None:

                    def process_frame(self, f):

                        if type(f) is str:
                            print(f"StreamService received {self.src} URL in do_GET()")
                            return  # a new URL

                        try:
                            import cv2 as cv
                            params = (cv.IMWRITE_JPEG_QUALITY, 100)
                            img_str = cv.imencode('.jpeg', f, params)[1].tobytes()

                            self.wfile.write(b"\r\n--jpgboundary\r\n")
                            self.send_header('Content-type', 'image/jpeg')
                            self.send_header('Content-length', str(len(img_str)))
                            self.send_header('Access-Control-Expose-Headers', 'majic-color')
                            self.send_header('majic-color', str(highlight(f, 10, 110)))
                            self.end_headers()

                            self.wfile.write(img_str)
                        except ConnectionResetError:
                            pass
                        except BrokenPipeError:
                            pass

                    process_frame(self, self.src)
                    self.finish()

        else:
            self.send_error(404)
            self.end_headers()
            self.finish()


class StreamService(server.ThreadingHTTPServer):

    def __init__(self, addr, ctx, hndlr):
        super().__init__(addr, hndlr)
        self.config_path = ctx
        self.RequestHandlerClass.config_path = ctx
        self.is_stopped = False
        self.t = None

        self.allow_reuse_address = True

    # def server_bind(self):
    #     import socket
    #     self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     self.socket.bind(self.server_address)

    def serve_forever(self, poll_interval: float = ...) -> None:
        while not self.is_stopped:
            self.handle_request()

    def force_stop(self):
        self.server_close()
        self.is_stopped = True
        self.t.join(1)
        self.t = None

    def stream(self):

        try:
            self.t = threading.Thread(target=self.serve_forever)
            self.t.start()
            cam_logger.info(f"NEW {self.t.name} streaming on http://{self.server_address[0]}:{self.server_address[1]}{self.config_path}")

        except Exception as e:
            cam_logger.error(f"streaming error on http://{self.server_address[0]}:{self.server_address[1]} {self.config_path}! " + str(e))


if __name__ == "__main__":
    import os
    from src.config.__init__ import readConfig, CONFIG_PATH

    myconfig = {}
    readConfig(os.path.join(CONFIG_PATH, 'cam.json'), myconfig)

    handler = StreamingHandler  # choose the handler.
    handler.src = myconfig.get('FORWARD_VIDEO_URL')  # set the handlers' 'source'.
    svc = StreamService(('cam.localhost', 5002), '/stream', handler)
    svc.stream()


