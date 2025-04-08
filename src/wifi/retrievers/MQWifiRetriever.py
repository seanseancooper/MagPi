import threading

from src.wifi.MQWifiScanner import MQWifiScanner
import xml
import xml.etree.ElementTree as ET
import xml.parsers.expat
from xml.parsers.expat import ExpatError

from src.config import readConfig
from src.net.RabbitMQAsyncConsumer import RabbitMQAsyncConsumer

import logging

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')


class MQWifiRetriever(threading.Thread):
    """ MQ Wifi Retriever class """
    def __init__(self):
        super().__init__()

        self.config = {}
        self.interface = None

        self.consumer = RabbitMQAsyncConsumer('wifi_queue')

        self.stats = {}                         # new, not yet used
        self.parsed_signals = []                # signals represented as a list of dictionaries.

        self.SIGNAL_DEBUG = False
        self.DATA_DEBUG = False
        self.PARSE_DEBUG = False
        self.ROOT_DEBUG = False
        self.ELEMENT_DEBUG = False
        self.FOUNDCELL_DEBUG = False
        self.APPEND_DEBUG = False
        self.PARSEDCELL_DEBUG = False

        self.DEBUG = False

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.SIGNAL_DEBUG = self.config.get('XML_SIGNAL_DEBUG')
        self.DATA_DEBUG = self.config.get('XML_DATA_DEBUG')
        self.PARSE_DEBUG = self.config.get('XML_PARSE_DEBUG')
        self.ROOT_DEBUG = self.config.get('XML_ROOT_DEBUG')
        self.ELEMENT_DEBUG = self.config.get('XML_ELEMENT_DEBUG')
        self.FOUNDCELL_DEBUG = self.config.get('XML_FOUNDCELL_DEBUG')
        self.APPEND_DEBUG = self.config.get('XML_APPEND_DEBUG')
        self.PARSEDCELL_DEBUG = self.config.get('XML_PARSEDCELL_DEBUG')
        self.DEBUG = self.config.get('DEBUG')

        self.start_scanner()
        self.start_consumer()

    @staticmethod
    def start_scanner():
        scanner = MQWifiScanner()
        scanner.configure('net.json')
        t = threading.Thread(target=scanner.run, daemon=True)
        t.start()

    def start_consumer(self):
        t = threading.Thread(target=self.consumer.run, daemon=True)
        t.start()

    def scan_wifi(self):
        """ scan configured wifi interface using iwlist """
        try:
            return self.consumer.data or []
        except Exception as e:
            wifi_logger.error(f"[{__name__}]: Exception: {e}")

    def parse_signals(self, readlines):
        """ parse signals from iwlist """

        self.parsed_signals = self.get_parsed_cells(readlines)

    def process_xml(self, xml_data):
        _elements = {}

        def start_element(name, attr):
            _elements[parser.CurrentByteIndex] = name

        def end_element(name):
            if name:
                _elements.popitem()

        def close_element(d, errorByteIndex):
            # move me
            DOCTYPE = self.config['DOCTYPE']

            if d is not None:
                if len(d) > 0:
                    data = d[0:errorByteIndex]
                    # [data += str(f"</{v}>") for v in reversed(_elements.values())]
                    for v in reversed(_elements.values()):
                        data = data + str(f"</{v}>")
                        if self.DATA_DEBUG:
                            wifi_logger.debug(f"[{__name__}]: >> {data}")
                    return data
            else:
                return DOCTYPE

        parser = xml.parsers.expat.ParserCreate(encoding='latin-1')
        parser.StartElementHandler = start_element
        parser.EndElementHandler = end_element

        try:
            if self.PARSE_DEBUG:
                wifi_logger.debug(f"[{__name__}]: PARSE: >> {xml_data}")
            parser.Parse(xml_data, True)
            root = ET.fromstring(xml_data)
        except ExpatError:
            root = ET.fromstring(close_element(xml_data, parser.ErrorByteIndex))
        except TypeError:
            root = ET.fromstring(close_element(xml_data, parser.ErrorByteIndex))

        if self.ROOT_DEBUG:
            wifi_logger.debug(f"[{__name__}]: ROOT: >> {root}")
        return root

    def get_parsed_cells(self, airport_data):
        """ Parses MacOS airport output into a list of networks
            @return list
                properties:
        """

        cells = [{}]
        parsed_cells = []

        if not airport_data:
            return parsed_cells

        root = self.process_xml(airport_data)

        def unwrap(record):
            u_record = {}
            element_key = None
            element_val = None

            for element in record:
                if element.tag == 'key':
                    element_key = element.text
                    continue
                if element.tag == 'array':
                    u_record.update(unwrap(element))
                if element.tag == 'dict':
                    u_record.update(unwrap(element))
                elif element.tag == 'string' or element.tag == 'integer' or element.tag == 'data':
                    element_val = element.text

                if element_key and element_val:
                    u_record[element_key] = element_val
                    if self.ELEMENT_DEBUG:
                        wifi_logger.debug(f"[{__name__}]:(element_key: {element_key}, "
                                          f"element.tag: {element.tag}, element.text: {element.text}")

            return u_record

        def clean_bssid(elided):
            _bssid = []

            def parse_o(o):
                if len(o) == 1:
                    o = "0" + o
                _bssid.append(o)

            [parse_o(o) for o in elided.split(":")]

            return ":".join(_bssid).upper()

        def parse_item(record):

            item = unwrap(record)

            if 'BSSID' in item:

                SSID = item.get('SSID_STR', '*HIDDEN*').strip()
                BSSID = clean_bssid(item.get('BSSID', '00:00:00:00:00:00').strip())
                RSSI = int(item.get('RSSI', 0))
                CHANNEL = int(item.get('CHANNEL', -1))

                # convert to Ghz band
                FREQUENCY = int(item.get('CAPABILITIES', -1))

                try:
                    QUALITY = abs(RSSI + 100) or 0
                except Exception as e:
                    wifi_logger.debug(f"[{__name__}]:Exception: calculating quality {e}")

                SECURITY = False

                # don't really care about details... is or is it not secured.
                try:

                    IE_KEY_RSN_MCIPHER = int(item.get('IE_KEY_RSN_MCIPHER', 0).strip())
                    IE_KEY_RSN_UCIPHERS = int(item.get('IE_KEY_RSN_UCIPHERS', 0).strip())

                    if IE_KEY_RSN_MCIPHER > 0 or IE_KEY_RSN_UCIPHERS > 0:
                        SECURITY = True
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass

                try:
                    from src.wifi.lib.wifi_utils import vendors
                    VENDOR = vendors[BSSID[0:8]]
                except KeyError:
                    VENDOR = f"UNKNOWN"

                cell = {
                    'SSID'      : SSID,
                    'BSSID'     : BSSID,
                    'Signal'    : RSSI,
                    'Channel'   : CHANNEL,
                    "Frequency" : FREQUENCY,
                    'Quality'   : QUALITY,
                    'Encryption': SECURITY,
                    'Vendor'    : VENDOR,
                }

                cells.append(cell)

                if self.FOUNDCELL_DEBUG:
                    wifi_logger.debug(f"[{__name__}]: FOUND CELL: >> {cell}")

        [parse_item(record) for record in root.iter('dict')]
        [parsed_cells.append(cell) for cell in cells[2:]]

        if self.PARSEDCELL_DEBUG:
            wifi_logger.debug(f"[{__name__}]: PARSED_CELLS: >> {parsed_cells}")

        return parsed_cells
