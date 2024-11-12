"""
A simple and lightweight Blackview client based on GPSD client.
"""
import json
from datetime import datetime
from typing import Union, Iterable, Dict, Any


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
        self.conn = None
        self.resp = None

    def blackview_lines(self):
        from http import client

        self.conn = client.HTTPConnection(self.host)
        self.conn.set_debuglevel(1)
        self.conn.timeout = self.timeout
        self.conn.request("GET", "http://" + self.host + "/blackvue_livedata.cgi")
        self.resp = self.conn.getresponse()
        self.conn.close()
        '''
        This should  work, but is blocking??
        '''
        # import requests
        # self.resp = requests.get("http://" + self.host + "/blackvue_livedata.cgi")

        return self.resp

    def json_stream(self):
        for line in self.blackview_lines():
            answ = line.decode('utf-8').strip()
            # print(f'answ: {answ}')
            if answ.startswith('{"GPS"'):
                yield json.loads(answ)
            else:
                self.close()

    def dict_stream(self) -> Iterable[Dict[str, Any]]:
        if self.json_stream():
            for line in self.json_stream():
                line["GPS"]["UPDATED"] = datetime.now().__format__("%Y-%m-%d %H:%M:%S")
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
