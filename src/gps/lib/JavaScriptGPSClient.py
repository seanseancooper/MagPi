"""
A simple and lightweight JavaScript client based on GPSD client.
"""
import requests
from typing import Union, Iterable, Dict, Any
from src.config import readConfig


class JavaScriptGPSClient:
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

    def configure(self):
        readConfig('gps.json', self.config)

    def javascript_lines(self):
        self.resp = requests.get(f'http://{self.config.get("JSRETRIEVER_HOST", "localhost:5183")}')
        return self.resp

    def json_stream(self):
        for line in self.javascript_lines():
            answ = line.decode('utf-8').strip()
            # print(f'json_stream answ: {answ}')
            if answ.find('GPS') > 0:
                # print(f'output: {answ}')
                yield answ
            else:
                self.close()

    def dict_stream(self) -> Iterable[Dict[str, Any]]:
        if self.json_stream():
            for line in self.json_stream():
                # print(f'dict_stream line: {line}')
                yield line

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
