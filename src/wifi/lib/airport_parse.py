import os
import subprocess

import xml
import xml.etree.ElementTree as ET
import xml.parsers.expat
from xml.parsers.expat import ExpatError

from .iw_parse import matching_line
from .wifi_utils import vendors
from src.config import readConfig, CONFIG_PATH

import logging.handlers

wifi_logger = logging.getLogger('wifi_logger')

config = {}
config_file = os.path.join(CONFIG_PATH, 'wifi.json')
readConfig(config_file, config)

SIGNAL_DEBUG = config.get('XML_SIGNAL_DEBUG', False)
DATA_DEBUG = config.get('XML_DATA_DEBUG', False)
PARSE_DEBUG = config.get('XML_PARSE_DEBUG', False)
ROOT_DEBUG = config.get('XML_ROOT_DEBUG', False)
ELEMENT_DEBUG = config.get('XML_ELEMENT_DEBUG', False)
FOUNDCELL_DEBUG = config.get('XML_FOUNDCELL_DEBUG', False)
APPEND_DEBUG = config.get('XML_APPEND_DEBUG', False)
PARSEDCELL_DEBUG = config.get('XML_PARSEDCELL_DEBUG', False)


def scan_macos_wifi():
    try:
        # airport is being deprecated! This is only for development if available.
        process = subprocess.Popen(
                ['/usr/local/bin/airport', '-s', '-x'],
                stdout=subprocess.PIPE)
        while process.stdout:
            return str(b''.join(process.stdout.readlines()).decode(encoding='latin-1'))

    except Exception as e:
        wifi_logger.error(f"[{__name__}]: Exception: {e}")


def get_quality(cell):
    """ Gets the quality of a network / cell.
    @param cell
        A network / cell from iwlist scan.

    @return string
        The quality of the network.
    """

    signal = matching_line(cell, "Signal level=")
    if signal is None:
        if SIGNAL_DEBUG:
            wifi_logger.debug(f"[{__name__}]: no signal...")
            return ""
    signal = signal.split("=")[1].split("/")
    if len(signal) == 2:
        return str(int(round(float(signal[0]) / float(signal[1]) * 100)))
    elif len(signal) == 1:
        return signal[0].split(' ')[0]
    else:
        return ""


def process_xml(xml_data):
    _elements = {}

    def start_element(name, attr):
        _elements[parser.CurrentByteIndex] = name

    def end_element(name):
        if name:
            _elements.popitem()

    def close_element(d, errorByteIndex):

        DOCTYPE = config['DOCTYPE']

        if d is not None:
            if len(d) > 0:
                data = d[0:errorByteIndex]
                # [data += str(f"</{v}>") for v in reversed(_elements.values())]
                for v in reversed(_elements.values()):
                    data = data + str(f"</{v}>")
                    if DATA_DEBUG:
                        wifi_logger.debug(f"[{__name__}]: >> {data}")
                return data
        else:
            return DOCTYPE

    parser = xml.parsers.expat.ParserCreate(encoding='latin-1')
    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element

    try:
        if PARSE_DEBUG:
            wifi_logger.debug(f"[{__name__}]: PARSE: >> {xml_data}")
        parser.Parse(xml_data, True)
        root = ET.fromstring(xml_data)
    except ExpatError:
        root = ET.fromstring(close_element(xml_data, parser.ErrorByteIndex))
    except TypeError:
        root = ET.fromstring(close_element(xml_data, parser.ErrorByteIndex))

    if ROOT_DEBUG:
        wifi_logger.debug(f"[{__name__}]: ROOT: >> {root}")
    return root


def get_macos_parsed_cells(airport_data):
    """ Parses airport output into a list of networks on MacOS.

        @return list
            properties:
    """

    cells = [[]]
    parsed_cells = []

    if not airport_data:
        return parsed_cells

    root = process_xml(airport_data)

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
                if ELEMENT_DEBUG:
                    wifi_logger.debug(f"[{__name__}]:(element_key: {element_key}, "
                                      f"element.tag: {element.tag}, element.text: {element.text}")

        # def parse_element(element):
        #
        #     element_key = None
        #     element_val = None
        #
        #     if element.tag == 'key':
        #         element_key = element.text
        #         return
        #     if element.tag == 'dict':
        #         pass
        #         # element_key = unwrap(element)
        #     elif element.tag == 'string' or element.tag == 'integer' or element.tag == 'data':
        #         element_val = element.text
        #
        #     if element_key and element_val:
        #         u_record[element_key] = element_val
        #         if ELEMENT_DEBUG:
        #             wifi_logger.debug(f"[{__name__}]:(element_key: {element_key}, "
        #                               f"element.tag: {element.tag}, element.text: {element.text}")
        #
        # [parse_element(element) for element in record]

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
            RSSI = str(item.get('RSSI', 0).strip())
            CHANNEL = str(item.get('CHANNEL', '?').strip())

            # convert to Ghz band
            FREQUENCY = str(item.get('CAPABILITIES', '?').strip())

            try:
                QUALITY = str(abs(int(RSSI) + 100) or 0)
            except Exception as e:
                wifi_logger.debug(f"[{__name__}]:Exception: calculating quality {e}")

            SECURITY = 'False'

            # don't really care about details... is or is it not secured.
            try:

                IE_KEY_RSN_MCIPHER = int(item.get('IE_KEY_RSN_MCIPHER', 0).strip())
                IE_KEY_RSN_UCIPHERS = int(item.get('IE_KEY_RSN_UCIPHERS', 0).strip())

                if IE_KEY_RSN_MCIPHER > 0 or IE_KEY_RSN_UCIPHERS > 0:
                    SECURITY = 'True'
            except AttributeError: pass
            except UnboundLocalError: pass

            # wifi_logger.debug(f"[{__name__}]:(SECURITY:{SECURITY})")

            IS_MUTE = False

            try:
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
                # 'is_mute'   : "False",  # later, this is replaced with the current value.
                'Vendor'    : VENDOR,
            }

            cells.append(cell)

            if FOUNDCELL_DEBUG:
                wifi_logger.debug(f"[{__name__}]: FOUND CELL: >> {cell}")

    [parse_item(record) for record in root.iter('dict')]
    [parsed_cells.append(cell) for cell in cells[2:]]

    if PARSEDCELL_DEBUG:
        wifi_logger.debug(f"[{__name__}]: PARSED_CELLS: >> {parsed_cells}")

    return parsed_cells
