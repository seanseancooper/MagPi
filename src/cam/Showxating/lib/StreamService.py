import socketserver
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Tuple

import numpy as np
import logging

cam_logger = logging.getLogger('cam_logger')


class StreamingHandler(BaseHTTPRequestHandler):

    def __init__(self, request: bytes, client_address: Tuple[str, int], srvr: socketserver.BaseServer):
        super().__init__(request, client_address, srvr)
        self.config_path = None
        self.src = None
        self.majic_color = None

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'http://cam.localhost:5002')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Headers', 'Access-Control-Allow-Headers')
        self.send_header('Access-Control-Allow-Headers', 'Access-Control-Allow-Methods')
        self.send_header('Access-Control-Allow-Headers', 'Access-Control-Allow-Origin')
        self.end_headers()

    def do_GET(self):

        if self.path == self.config_path:

            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', 'http://cam.localhost:5002')
            self.send_header('Access-Control-Allow-Headers', 'MAJIC-COLOR')

            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.send_header('Cache-Control',
                             'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
            self.end_headers()

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
                            my.send_header('Access-Control-Expose-Headers', 'MAJIC-COLOR')
                            my.send_header('MAJIC-COLOR', my.majic_color)
                            my.end_headers()

                            my.wfile.write(img_str)
                        except ConnectionResetError as c:
                            pass  # print(f'{c}')
                        except BrokenPipeError as b:
                            pass  # print(f'{b}')
                        except ValueError as v:
                            print(f'{v}')

                    process_frame(self, self.src)

        else:
            self.send_error(404)


class StreamService(ThreadingHTTPServer):

    def __init__(self, addr, ctx, hndlr):
        super().__init__(addr, hndlr)
        self.config_path = ctx
        self.RequestHandlerClass.config_path = ctx
        self.is_stopped = False
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

    def stream(self):

        try:
            threading.Thread(target=self.serve_forever, name='StreamService').start()
            cam_logger.info(f"streaming on http://{self.server_address[0]}:{self.server_address[1]}{self.config_path}")

        except Exception as e:
            cam_logger.error(f"streaming error on http://{self.server_address[0]}:{self.server_address[1]} {self.config_path}! " + str(e))


