import os
from collections import defaultdict
from datetime import datetime
import threading
import logging
import time
from gpsdclient import GPSDClient

from src.config import readConfig
from src.gps.lib.BlackViewGPSClient import BlackViewGPSClient
from src.gps.lib.JavaScriptGPSClient import JavaScriptGPSClient


gps_logger = logging.getLogger('gps_logger')
retrievers = {}


def format_time(_, fmt):
    return f'{_.strftime(fmt)}'


class GPSRetriever(threading.Thread):

    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.config = {}
        self.lat = None
        self.lon = None
        self.time = None
        self.heading = None
        self.track = None
        self.speed = None
        self.altitude = None
        self.climb = None

        self.retriever_method = None
        self.retrieving = False
        self.thread = None
        self.result = defaultdict(dict)

    def __str__(self):
        return {f"GPSRetriever: time: {self.gps_time()} position: {self.gps_position()} config: {self.config}"}

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def register_retriever(self):
        """ Register retriever methods """
        retrievers[self.__name__] = self
        return self

    def get_retriever(self):
        try:
            retriever_plugin = eval("GPSRetriever." + self.config['RETRIEVER_METHOD'])
            return retriever_plugin
        except AttributeError as e:
            gps_logger.fatal(f'no retriever found {e}')


    @register_retriever
    def GPSDClientRetriever(self, *, c, **retriever_args):
        # "GPS_HOST": "192.168.1.2" "GPS_PORT": 2947 "GPS_CONNECT_TIMEOUT": 10
        while True:
            try:
                with GPSDClient(**retriever_args) as client:
                    # for result in client.json_stream():
                    for result in client.dict_stream(convert_datetime=True, filter=["TPV"]):
                        if not result:
                            break
                        self.result = result

            except OSError as e:  # unable to connect.
                gps_logger.error(f"GPSDClientRetriever {e}")  # unable to connect to GPS Hardware

    @register_retriever
    def BlackviewGPSRetriever(self, *, c, **retriever_args):
        while True:
            try:
                with BlackViewGPSClient(**retriever_args) as client:
                    for result in client.dict_stream():
                        if not result:
                            break
                        # send: b'GET http://10.99.77.1/blackvue_livedata.cgi HTTP/1.1\r\n
                        # Host: 10.99.77.1\r\n
                        # Accept-Encoding: identity\r\n\r\n'
                        # reply: 'HTTP/1.1 200 OK\r\n'
                        # header: Date: Tue, 12 Nov 2024 20:33:24 GMT
                        # header: Server: DR750S-2CH
                        # header: Accept-Ranges: bytes
                        # header: Connection: close
                        # header: Content-Type: application/json; boundary=--ptaboundary
                        # {'GPS': {'LATITUDE': 39.917143, 'LONGITUDE': -105.068342, 'UPDATED': '2024-11-12 13:33:22'}}
                        # {'lat': 39.917143, 'lon': -105.068342, 'time': '2024-11-12 13:33:22'}
                        # {'lat': 39.917143, 'lon': -105.068342, 'time': '2024-11-12 13:33:22'}
                        # {'GPS': {'LATITUDE': 39.917144, 'LONGITUDE': -105.068342, 'UPDATED': '2024-11-12 13:33:22'}}
                        # {'lat': 39.917144, 'lon': -105.068342, 'time': '2024-11-12 13:33:22'}
                        # {'lat': 39.917144, 'lon': -105.068342, 'time': '2024-11-12 13:33:22'}
                        # {'GPS': {'LATITUDE': 39.917145, 'LONGITUDE': -105.068343, 'UPDATED': '2024-11-12 13:33:22'}}
                        # {'lat': 39.917145, 'lon': -105.068343, 'time': '2024-11-12 13:33:22'}
                        # {'lat': 39.917145, 'lon': -105.068343, 'time': '2024-11-12 13:33:22'}
                        # {'GPS': {'LATITUDE': 39.917145, 'LONGITUDE': -105.068343, 'UPDATED': '2024-11-12 13:33:22'}}
                        # {'lat': 39.917145, 'lon': -105.068343, 'time': '2024-11-12 13:33:22'}
                        # {'lat': 39.917145, 'lon': -105.068343, 'time': '2024-11-12 13:33:22'}
                        # {'GPS': {'LATITUDE': 39.917146, 'LONGITUDE': -105.068344, 'UPDATED': '2024-11-12 13:33:25'}}
                        # {'lat': 39.917146, 'lon': -105.068344, 'time': '2024-11-12 13:33:25'}
                        # {'lat': 39.917146, 'lon': -105.068344, 'time': '2024-11-12 13:33:25'}
                        gps_logger.debug(f'{result}')
                        lat = result['GPS']['LATITUDE']
                        lon = result['GPS']['LONGITUDE']
                        updt = result['GPS']['UPDATED']
                        self.result = {"lat": lat, "lon": lon, "time": updt}
                        gps_logger.debug(f'{self.result}')
                        time.sleep(self.config.get('BLACKVIEWGPSRETRIEVER_TIMEOUT', 1))
            except OSError as e:
                gps_logger.error(f"BlackviewGPSRetriever: {e}")  # unable to connect to Blackview

    @register_retriever
    def DummyGPSRetriever(self, *, c, **retriever_args):

        import json
        lines = [line.replace('LATITUDE', 'lat').replace('LONGITUDE', 'lon').strip() for line in open(self.config['TEST_FILE'], 'r')]
        lines = [json.loads(line.replace("\'","\"")) for line in lines]

        while True:
            for i in range(len(lines) - 1):
                result = lines[i]
                lat = result['GPS']['lat']
                lon = result['GPS']['lon']
                self.result = {"lat": lat, "lon": lon, "time": datetime.now().__format__("%Y-%m-%d %H:%M:%S")}
                time.sleep(self.config.get('DUMMYRETRIEVER_TIMEOUT', 1))

    @register_retriever
    def JavaScriptGPSRetriever(self, *, c, **retriever_args):
        while True:
            try:
                with JavaScriptGPSClient(**retriever_args) as client:
                    for result in client.dict_stream():
                        if not result:
                            break
                        self.result = result

            except Exception as e:
                gps_logger.error(f"JavaScriptGPSRetriever: {e}")  # unable to connect to Blackview

    def gps_time(self):
        return str(self.time)  # needs a format

    def gps_position(self):
        return self.result

    def gps_location(self):
        return {"lat": self.result['lat'], "lon": self.result['lon']}

    def gps_altitude(self):
        return {"altitude": self.result['altitude']}

    def gps_speed(self):
        return {"speed": self.result['speed']}

    def gps_track(self):
        return {"heading": self.result['heading']}

    def gps_climb(self):
        return {"climb": self.result['climb']}

    def stop(self):
        pass

    def run(self):

        retriever = self.get_retriever()

        self.thread = threading.Thread(
                target=retriever,
                kwargs=dict(self=self, c=None, host=self.config['GPS_HOST'],
                            port=self.config['GPS_PORT'],
                            timeout=self.config['GPS_CONNECT_TIMEOUT']
                            )
        ).start()


if __name__ == '__main__':
    from src.config.__init__ import CONFIG_PATH

    gpsRet = GPSRetriever()
    gpsRet.configure(os.path.join(CONFIG_PATH, 'gps.json'))
    gpsRet.run()