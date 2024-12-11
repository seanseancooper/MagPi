import os
from collections import defaultdict
from datetime import datetime
import threading
import json
import logging
import time
from gpsdclient import GPSDClient

from src.config import readConfig
from src.gps.lib.BlackViewGPSClient import BlackViewGPSClient
from src.gps.lib.JavaScriptGPSClient import JavaScriptGPSClient


gps_logger = logging.getLogger('gps_logger')
retrievers = {}


class GPSRetriever(threading.Thread):

    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.config = {}
        self.retriever_method = None
        self.retrieving = False
        self.thread = None
        self.result = defaultdict(dict)

    def __str__(self):
        return f"GPSRetriever: time: {self.gps_time()} position: {self.gps_position()} config: {self.config}"

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
                        self.result = result  # use 'heading', not 'track'.

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
                        gps_logger.debug(f'{result}')

                        self.result = {"lat": result['GPS']['LATITUDE'],
                                       "lon": result['GPS']['LONGITUDE'],
                                       "time": result['GPS']['UPDATED']}

                        gps_logger.debug(f'{self.result}')
                        time.sleep(self.config.get('BLACKVIEWGPSRETRIEVER_TIMEOUT', 1))
            except OSError as e:
                gps_logger.error(f"BlackviewGPSRetriever: {e}")  # unable to connect to Blackview

    @register_retriever
    def DummyGPSRetriever(self, *, c, **retriever_args):

        lines = [line.replace('LATITUDE', 'lat').replace('LONGITUDE', 'lon').strip() for line in open(self.config['TEST_FILE'], 'r')]
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
                print(self.result)
                time.sleep(self.config.get('DUMMYRETRIEVER_TIMEOUT', 1))

    @register_retriever
    def JavaScriptGPSRetriever(self, *, c, **retriever_args):
        while True:
            try:
                with JavaScriptGPSClient(**retriever_args) as client:
                    for result in client.dict_stream():
                        if not result:
                            break
                        result = json.loads(result)
                        self.result = {"lat": result['GPS']['lat'],
                                       "lon": result['GPS']['lon'],
                                       "heading": 0.0,
                                       "track": 0.0,
                                       "speed": 0.0,
                                       "altitude": 0.0,
                                       "climb": 0.0,
                                       "time":  datetime.now().__format__(self.config.get('DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S.%f'))
                                       }
                        print(self.result)
                        time.sleep(self.config.get('JSRETRIEVER_TIMEOUT', 1))
            except Exception as e:
                gps_logger.error(f"JavaScriptGPSRetriever: {e}")  # unable to connect to Blackview

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