import json
import requests
import logging
from src.lib.utils import speech_logger, gps_logger
from src.map.gps.GPSRetriever import GPSRetriever

logger_root = logging.getLogger('root')
speech_logger = logging.getLogger('speech_logger')
gps_logger = logging.getLogger('gps_logger')

def get_location(locator):
    """ gets location from GPS endpoint"""
    try:
        resp = requests.get(locator.config.get('GPS_ENDPOINT', 'http://map.localhost:5005/position'))
        position = json.loads(resp.text)
        locator.lat = position.get('LATITUDE', position.get('lat'))
        locator.lon = position.get('LONGITUDE', position.get('lon'))
    except Exception as e:
        if locator.config['SPEECH_ENABLED']:
            speech_logger.warning(f"GPS Error")
        gps_logger.debug(f"GPS Retrieval Error for {locator.config['MODULE']}: {e}")
