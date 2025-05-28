import os
from collections import defaultdict
from datetime import datetime, timedelta
import threading
import json
import logging
import time


from gpsdclient import GPSDClient

from src.config import readConfig
from src.map.gps.lib.BlackViewGPSClient import BlackViewGPSClient
from src.lib.utils import format_time
from src.net.lib.net_utils import load_module

gps_logger = logging.getLogger('gps_logger')
retrievers = {}


class GPSRetriever(threading.Thread):

    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.config = {}
        self.retriever = None
        self.retrieving = False
        self.thread = None
        self.result = defaultdict(dict)

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta
        self.polling_count = 0
        self.lat = 0.0
        self.lon = 0.0

    def get(self):
        return f"GPSRetriever: {self.result} config: {self.config}"

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def register_retriever(self):
        """ Register retriever methods """
        retrievers[self.__name__] = self
        return self

    def update(self):
        # gps_logger.debug(f'{self.result}')
        self.updated = datetime.now()
        self.elapsed = self.updated - self.created
        self.polling_count += 1
        print(self.result)

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
                        self.result = result  # use 'heading', not 'track'.
                        self.update()

            except OSError as e:  # unable to connect.
                gps_logger.error(f"GPSDClientRetriever {e}")  # unable to connect to GPS Hardware

    @register_retriever
    def BlackviewGPSRetriever(self, *, c, **retriever_args):
        # "GPS_HOST": "10.99.77.1" "GPS_PORT": 80 "GPS_CONNECT_TIMEOUT": 10
        while True:
            try:
                with BlackViewGPSClient(**retriever_args) as client:
                    for result in client.dict_stream():
                        if not result:
                            break
                        # gps_logger.debug(f'{result}')

                        self.result = {"lat": result['GPS']['LATITUDE'],
                                       "lon": result['GPS']['LONGITUDE'],
                                       "time": format_time(datetime.now(), self.config.get('DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S.%f'))
                                       }

                        self.update()
                        time.sleep(self.config.get('GPS_RETRIEVER_TIMEOUT', 1))
            except OSError as e:
                gps_logger.error(f"BlackviewGPSRetriever: {e}")  # unable to connect to Blackview

    @register_retriever
    def DummyGPSRetriever(self, *, c, **retriever_args):

        lines = [line.replace('LATITUDE', 'lat').replace('LONGITUDE', 'lon').strip() for line in open(self.config['GPS_TEST_FILE'], 'r')]
        lines = [json.loads(line.replace("\'", "\"")) for line in lines]

        while True:
            for i in range(len(lines) - 1):
                result = lines[i]
                self.result = {"lat": result['GPS']['lat'],
                               "lon": result['GPS']['lon'],
                               "heading": 0.0,
                               "track": 0.0,
                               "speed": 0.0,
                               "altitude": 0.0,
                               "climb": 0.0,
                               "time":  datetime.now().__format__(self.config.get('DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S.%f'))
                               }
                self.update()
                time.sleep(self.config.get('GPS_RETRIEVER_TIMEOUT', 1))

    @register_retriever
    def JSGPSRetriever(self, *, c, **retriever_args):

        import requests

        while True:
            time.sleep(self.config.get('GPS_RETRIEVER_TIMEOUT', 1))
            res = requests.get(f'http://{self.config.get("GPS_HOST", "localhost")}:{self.config.get("GPS_PORT", 5015)}')
            result = json.loads(res.text)

            self.result = {"lat": result['lat'],
                           "lon": result['lon'],
                           "heading": 0.0,
                           "track": 0.0,
                           "speed": 0.0,
                           "altitude": 0.0,
                           "climb": 0.0,
                           "time":  datetime.now().__format__(self.config.get('DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S.%f'))
                           }
            self.update()


    def gps_result(self):
        return self.result

    def gps_location(self):
        return {"lat": self.result['lat'], "lon": self.result['lon']}

    def gps_time(self):
        return self.result.get('time', datetime.now().strftime(self.config.get('DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S.%f')))

    def gps_altitude(self):
        return {"altitude": self.result['altitude']}

    def gps_speed(self):
        return {"speed": self.result['speed']}

    def gps_track(self):
        return {"track": self.result['heading']}  # if there is a 'track', it's a heading

    def gps_heading(self):
        return {"heading": self.result['heading']}

    def gps_climb(self):
        return {"climb": self.result['climb']}

    def stop(self):
        pass

    def run(self):

        self.retriever = load_module(self.config['GPS_MODULE_RETRIEVER'])

        self.thread = threading.Thread(
                target=self.retriever,
                kwargs=dict(self=self, c=None, host=self.config['GPS_HOST'],
                            port=self.config['GPS_PORT'],
                            timeout=self.config['GPS_CONNECT_TIMEOUT']
                            )
        ).start()


if __name__ == '__main__':
    from src.config.__init__ import CONFIG_PATH

    gpsRet = GPSRetriever()
    gpsRet.configure(os.path.join(CONFIG_PATH, 'map.json'))
    gpsRet.run()