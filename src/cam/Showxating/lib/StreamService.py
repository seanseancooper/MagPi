import socketserver
import threading
from http import server
from typing import Tuple

import numpy as np
import logging

cam_logger = logging.getLogger('cam_logger')


class StreamingHandler(server.BaseHTTPRequestHandler):

    def __init__(self, request: bytes, client_address: Tuple[str, int], srvr: socketserver.BaseServer):
        super().__init__(request, client_address, srvr)
        self.src = None
        self.config_path = None
        self.majic_color = None
        cam_logger.debug(f"{threading.current_thread().name} created StreamingHandler for request.")

    def do_GET(self):

        if self.path == self.config_path:

            # am I still sending the correct headers
            # in the right order at the right time?
            # Consider reloading vs. new connection
            # vs. broken connection.
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.send_header('Cache-Control',
                             'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
            self.end_headers()

            if type(self.src) is str:  # a new URL
                cam_logger.debug(f"{threading.current_thread().name} StreamService received {self.src} URL")
                self.finish()  # explicitly finish the request
                return

            if type(self.src) is np.ndarray:  # a plugin frame

                while self.src is not None:

                    def process_frame(my, f):

                        try:
                            import cv2 as cv
                            params = (cv.IMWRITE_JPEG_QUALITY, 100)
                            img_str = cv.imencode('.jpeg', f, params)[1].tobytes()

                            my.wfile.write(b"\r\n--jpgboundary\r\n")
                            my.send_header('Content-type', 'image/jpeg')
                            my.send_header('Content-length', str(len(img_str)))
                            my.send_header('Access-Control-Expose-Headers', 'majic-color')
                            my.send_header('majic-color', my.majic_color)
                            my.end_headers()

                            my.wfile.write(img_str)
                        except ConnectionResetError:
                            pass
                        except BrokenPipeError:
                            pass

                    process_frame(self, self.src)
                    self.finish()

        else:
            self.send_error(404)
            # self.end_headers()
            self.finish()


class StreamService(server.ThreadingHTTPServer):

    def __init__(self, addr, ctx, hndlr):
        super().__init__(addr, hndlr)
        self.config_path = ctx
        self.RequestHandlerClass.config_path = ctx
        self.is_stopped = False
        self.t = None

        self.allow_reuse_address = True

    def get_status(self):
        return {
            "addr": self.server_address,
            "config_path": self.config_path,
            "is_stopped": self.is_stopped
        }

    def serve_forever(self, poll_interval: float = ...) -> None:
        while not self.is_stopped:
            self.handle_request()

    def force_stop(self):
        self.server_close()
        self.is_stopped = True
        self.t.join(0.1)
        self.t = None

    def stream(self):

        try:
            threading.Thread(target=self.serve_forever, name='StreamService').start()
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


