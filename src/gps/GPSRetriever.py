import os
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
        self.result = dict()

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

    def gone_offline(self):
        ''' emit *something* when offline '''
        self.result['lat'] = self.lat = "0.0"
        self.result['lon'] = self.lon = "0.0"
        self.result['time'] = self.time = datetime.now().__format__(self.config['DATETIME_FORMAT'])
        self.result['track'] = self.track = "0.0"
        self.result['speed'] = self.speed = "0.0"
        self.result['altitude'] = self.altitude = "0.0"
        self.result['climb'] = self.climb = "0.0"

        time.sleep(1)

    def tx_result(self):

        self.time = self.result.get('time')

        self.lat = self.result.get('lat')
        self.lon = self.result.get('lon')

        self.heading = self.result.get('track')
        self.speed = self.result.get('speed')
        self.altitude = self.result.get('altitude')
        self.climb = self.result.get('climb')

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
                        self.result = result

            except OSError as e:  # unable to connect.
                gps_logger.error(f"GPSDClientRetriever {e}")  # unable to connect to Blackview
                self.gone_offline()
            finally:
                self.tx_result()

    @register_retriever
    def BlackviewGPSRetriever(self, *, c, **retriever_args):
        # "GPS_HOST": "10.99.77.1" "GPS_PORT": 80 "GPS_CONNECT_TIMEOUT": 10
        while True:
            try:
                with BlackViewGPSClient(**retriever_args) as client:
                    for result in client.dict_stream():
                        if not result:
                            break
                        # {'GPS': {'LATITUDE': 39.915162, 'LONGITUDE': -105.069197, 'UPDATED': '2024-10-31 21:00:55'}}
                        self.result = result
                        # print(f'{self.result}')
                        self.tx_result()
            except OSError as e:
                gps_logger.error(f"BlackviewGPSRetriever: {e}")  # unable to connect to Blackview
                self.gone_offline()
            # finally:
            #     client.close()
            #     self.tx_result()

    @register_retriever
    def DummyGPSRetriever(self, *, c, **retriever_args):

        import json
        lines = [line.replace('LATITUDE', 'lat').replace('LONGITUDE', 'lon').strip() for line in open(self.config['TEST_FILE'], 'r')]
        lines = [json.loads(line) for line in lines]

        while True:
            for i in range(len(lines) - 1):
                self.result = lines[i]
                self.result['time'] = datetime.now().__format__("%Y-%m-%d %H:%M:%S")
                self.tx_result()
                time.sleep(1)

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
                self.gone_offline()
            finally:
                self.tx_result()

    def gps_time(self):
        return str(self.time) # needs a format

    def gps_position(self):
        return self.result

    def gps_location(self):
        return str(self.lat, self.lon)

    def gps_altitude(self):
        return str(self.altitude)

    def gps_speed(self):
        return str(self.speed)

    def gps_track(self):
        return str(self.heading)  # TPV class refers to 'track' as 'heading'

    def gps_climb(self):
        return str(self.climb)

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