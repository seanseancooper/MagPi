"""
A simple and lightweight Blackview client based on GPSD client.
"""
import json
from datetime import datetime
from typing import Union, Iterable, Dict, Any

from src.config import readConfig


class BlackViewGPSClient:
    def __init__(
            self,
            host: str,
            port: Union[str, int],
            timeout: Union[float, int, None],
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.config = {}
        self.conn = None
        self.resp = None

    def blackview_lines(self):
        from http import client

        self.conn = client.HTTPConnection(self.host)  # TODO: port?
        self.conn.set_debuglevel(1)
        self.conn.timeout = self.timeout
        self.conn.request("GET", "http://" + self.host + "/blackvue_livedata.cgi")
        self.resp = self.conn.getresponse()
        self.conn.close()

        return self.resp

    def configure(self):
        readConfig('map.json', self.config)

    def json_stream(self):
        for line in self.blackview_lines():
            answ = line.decode('utf-8').strip()
            # print(f'answ: {answ}')  # this also contains IMS readings.
            if answ.startswith('{"GPS"'):
                yield json.loads(answ)
            else:
                self.close()

    def dict_stream(self) -> Iterable[Dict[str, Any]]:
        if self.json_stream():
            for line in self.json_stream():
                yield line

    def close(self):
        if self.conn:
            self.conn.close()
        self.conn = None

    def __str__(self):
        return "<BlackViewClient(host=%s, port=%s)>" % (self.host, self.port)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def __del__(self):
        self.close()
