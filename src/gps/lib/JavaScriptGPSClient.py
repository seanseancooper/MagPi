"""
A simple and lightweight JavaScript client based on GPSD client.
"""
import requests
import json
from datetime import datetime
from typing import Union, Iterable, Dict, Any


class JavaScriptGPSClient:
    def __init__(
            self,
            host: str = "http://localhost:5173",
            port: Union[str, int] = "5173",
            timeout: Union[float, int, None] = 1,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.conn = None
        self.resp = None

    def javascript_lines(self):
        # TODO: don't hardcode the URL
        # asbytes  = b'<!DOCTYPE html>\n<html lang="en">\n<head>\n  <script type="module" src="/@vite/client"></script>\n\n    <meta charset="UTF-8">\n    <meta name="viewport" content="initial-scale=1.0" />\n    <title>Open Layers</title>\n    <link rel="stylesheet" href="./node_modules/ol/ol.css">\n    <style>\n\n    .rotate-north {\n      top: 65px;\n      left: 8px;\n    }\n\n    .track {\n      top: 92px;\n      left: 8px;\n    }\n\n    .map .ol-custom-overviewmap,\n    .map .ol-custom-overviewmap.ol-uncollapsible {\n        bottom: auto;\n        left: auto;\n        right: 0;\n        top: 0;\n    }\n\n    .map .ol-custom-overviewmap:not(.ol-collapsed)  {\n        border: 1px solid black;\n    }\n\n    .map .ol-custom-overviewmap .ol-overviewmap-map {\n        border: 1px solid black;\n        width: 300px;\n    }\n\n    .map .ol-custom-overviewmap .ol-overviewmap-box {\n        border: 2px solid red;\n    }\n\n    .map .ol-custom-overviewmap:not(.ol-collapsed) button{\n        bottom: auto;\n        left: auto;\n        right: 1px;\n        top: 1px;\n    }\n\n    .map .ol-rotate {\n        top: 170px;\n        right: 0;\n    }\n\n    #info {\n        position: absolute;\n        font-family: Helvetica;\n        font-size: 10px;\n        display: inline-block;\n        height: auto;\n        width: 120px;\n        z-index: 100;\n        background-color: #333;\n        color: #fff;\n        text-align: left;\n        border-radius: 2px;\n        padding: 5px;\n        left: 50%;\n        transform: translateX(3%);\n        visibility: hidden;\n        pointer-events: none;\n    }\n\n    </style>\n</head>\n<body>\n    <div id="map" class="map" style="position:absolute;top:0px;left:0px;width:707px;height:443px;"></div>\n    <div id="heatmap_ctrl" style="position:absolute;top:125px;left:8px;width:25px;height:300px;text-align:center;">\n        <input id="radius" type="range" min="1" max="50" step="1" value="5" orient="vertical" style="height:130px;" /><br>\n        <label for="radius">\xc3\x98</label>\n        <br>\n        <input id="blur" type="range" min="1" max="50" step="1" value="15" orient="vertical" style="height:130px;" /><br>\n        <label for="blur">\xc3\x9f</label>\n    </div>\n    <div style="position:absolute;top:424px;left:80px;" id="featuresList"></div>\n    <div style="position:absolute;top:95px;left:35px;">\n        <div id="tracking_ind" style=""></div>\n    </div>\n    <div style="position:absolute;top:95px;left:40px;">\n        <div>\n            <div id="info" style=""></div>\n            <div id="output" style=""></div>\n        </div>\n    </div>\n    <script type="module" src="main.js"></script>\n</body>\n</html>'
        # return asbytes
        self.resp = requests.get("http://localhost:5183/")
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
