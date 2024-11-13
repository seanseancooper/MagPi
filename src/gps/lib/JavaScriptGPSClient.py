"""
A simple and lightweight JavaScript client based on GPSD client.
"""
import json
from datetime import datetime
from typing import Union, Iterable, Dict, Any


class JavaScriptGPSClient:
    def __init__(
            self,
            host: str = "http://gps.localhost:5004/location",
            port: Union[str, int] = "5004",
            timeout: Union[float, int, None] = 1,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.conn = None
        self.resp = None

    def javascript_lines(self):
        import requests
        # TODO: don't hardcode the URL
        self.resp = requests.get("http://localhost:5173/JavaScriptGPSRetriever.jsx")
        return self.resp

    def json_stream(self):
        for line in self.javascript_lines():
            answ = line.decode('utf-8').strip()
            print(f'json_stream answ: {answ}')
            if answ.find('//#') > 0:
                yield answ
            else:
                self.close()

    def dict_stream(self) -> Iterable[Dict[str, Any]]:
        if self.json_stream():
            for line in self.json_stream(): pass
                # print(f'dict_stream line: {line}')
                # line["GPS"]["UPDATED"] = datetime.now().__format__("%Y-%m-%d %H:%M:%S")
                # yield line

    def close(self):
        if self.conn:
            self.conn.close()
        self.conn = None

    def __str__(self):
        return "<JavaScriptClient(host=%s, port=%s)>" % (self.host, self.port)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def __del__(self):
        self.close()
