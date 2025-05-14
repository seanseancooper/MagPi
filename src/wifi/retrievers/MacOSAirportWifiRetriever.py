import subprocess
import threading

import xml
import xml.etree.ElementTree as ET
import xml.parsers.expat
from xml.parsers.expat import ExpatError

from src.config import readConfig
import logging

logger_root = logging.getLogger('root')
wifi_logger = logging.getLogger('wifi_logger')


class MacOSAirportWifiRetriever(threading.Thread):
    """ Apple MacOS specific Wifi Retriever class """
    def __init__(self):
        super().__init__()

        self.config = {}

        self.stats = {}                         # new, not yet used
        self.parsed_cells = []                  # incomplete labels: cells represented as a list of dictionaries.
        self.parsed_signals = []                # complete signals represented as a list of dictionaries.

        self.SIGNAL_DEBUG = False
        self.DATA_DEBUG = False
        self.PARSE_DEBUG = False
        self.ROOT_DEBUG = False
        self.APPEND_DEBUG = False

        self.DEBUG = False

    @staticmethod
    def scan():
        """ scan using airport """
        # this is an I/O bound process; decouple it from callers
        try:
            # airport is being deprecated! This is only for development if available.
            process = subprocess.Popen(
                    ['/usr/local/bin/airport', '-s', '-x'],
                    stdout=subprocess.PIPE)
            while process.stdout:
                return str(b''.join(process.stdout.readlines()).decode(encoding='latin-1'))

        except Exception as e:
            wifi_logger.error(f"[{__name__}]: Exception: {e}")

    def configure(self, config_file): # this should only ever read 'wifi'
        readConfig(config_file, self.config)

        self.SIGNAL_DEBUG = self.config.get('XML_SIGNAL_DEBUG')
        self.DATA_DEBUG = self.config.get('XML_DATA_DEBUG')
        self.PARSE_DEBUG = self.config.get('XML_PARSE_DEBUG')
        self.ROOT_DEBUG = self.config.get('XML_ROOT_DEBUG')
        self.APPEND_DEBUG = self.config.get('XML_APPEND_DEBUG')

        self.DEBUG = self.config.get('DEBUG')

    def get_quality(self, cell):
        """ Gets the quality of a network / cell.
        @param cell
            A network / cell from iwlist scan.

        @return string
            The quality of the network.
        """

        def matching_line(lines, keyword):
            """ Returns the first matching line in a list of lines.
            @see match()
            """
            for line in lines:
                matching = match(line, keyword)
                if matching is not None:
                    return matching
            return None

        def match(line, keyword):
            """ If the first part of line (modulo blanks) matches keyword,
            returns the end of that line. Otherwise checks if keyword is
            anywhere in the line and returns that section, else returns None"""

            line = line.lstrip()
            length = len(keyword)
            if line[:length] == keyword:
                return line[length:]
            else:
                if keyword in line:
                    return line[line.index(keyword):]
                else:
                    return None

        signal = matching_line(cell, "Signal level=")
        if signal is None:
            if self.SIGNAL_DEBUG:
                wifi_logger.debug(f"[{__name__}]: no signal...")
                return ""
        signal = signal.split("=")[1].split("/")
        if len(signal) == 2:
            return str(int(round(float(signal[0]) / float(signal[1]) * 100)))
        elif len(signal) == 1:
            return signal[0].split(' ')[0]
        else:
            return ""

    @staticmethod
    def get_parsed_cells(airport_data):
        """ Parses MacOS airport output into a list of networks
            @return list
                properties:
        """

        cells = [{}]
        parsed_cells = []

        if not airport_data:
            return parsed_cells

        DOCTYPE = "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\t\t\t\t<plist version=\"1.0\">\t\t<array></array>\t\t</plist>"

        def process_xml(xml_data, DOCTYPE):
            _elements = {}

            def start_element(name, attr):
                _elements[parser.CurrentByteIndex] = name

            def end_element(name):
                if name:
                    _elements.popitem()

            def close_element(d, errorByteIndex):

                if d is not None:
                    if len(d) > 0:
                        data = d[0:errorByteIndex]
                        # [data += str(f"</{v}>") for v in reversed(_elements.values())]
                        for v in reversed(_elements.values()):
                            data = data + str(f"</{v}>")
                        return data
                else:
                    return DOCTYPE

            parser = xml.parsers.expat.ParserCreate(encoding='latin-1')
            parser.StartElementHandler = start_element
            parser.EndElementHandler = end_element

            try:
                parser.Parse(xml_data, True)
                root = ET.fromstring(xml_data)
            except ExpatError:
                root = ET.fromstring(close_element(xml_data, parser.ErrorByteIndex))
            except TypeError:
                root = ET.fromstring(close_element(xml_data, parser.ErrorByteIndex))

            return root

        root = process_xml(airport_data, DOCTYPE)

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
                    # wifi_logger.debug(f"[{__name__}]:("
                    #                   f"element_key: {element_key}, "
                    #                   f"element.tag: {element.tag}, "
                    #                   f"element.text: {element.text}"
                    #                   )

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
                QUALITY = None
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
                    from src.wifi.lib.WifiVendors import vendors
                    VENDOR = vendors[BSSID[0:8]]
                except KeyError:
                    VENDOR = f"UNKNOWN"

                cell = {
                    'SSID'      : SSID,
                    'BSSID'     : BSSID,
                    'Signal'    : RSSI,
                    'Channel'   : CHANNEL,
                    'Frequency' : FREQUENCY,
                    'Quality'   : QUALITY,
                    'Encryption': SECURITY,
                    'Vendor'    : VENDOR,
                }

                cells.append(cell)

                # wifi_logger.debug(f"[{__name__}]: FOUND CELL: >> {cell}")

        [parse_item(record) for record in root.iter('dict')]
        [parsed_cells.append(cell) for cell in cells[2:]]

        # wifi_logger.debug(f"[{__name__}]: PARSED_CELLS: >> {parsed_cells}")

        return parsed_cells
