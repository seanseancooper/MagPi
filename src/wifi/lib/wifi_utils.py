import os
import xml.etree.ElementTree as ET
from datetime import datetime
import json

from src.config import CONFIG_PATH, readConfig
from src.lib.utils import make_path, write_file
from src.wifi.lib.iw_parse import matching_line

import logging

json_logger = logging.getLogger('json_logger')

config = {}
readConfig('wifi.json', config)

vendors = {}
vendorsMacs_XML = ET.parse(os.path.join(CONFIG_PATH, config['VENDORMACS_FILE']))


def proc_vendors(vendor, vendors):
    vendors[vendor.attrib["mac_prefix"]] = vendor.attrib["vendor_name"]


def get_vendor(cell):
    wifi_logger = logging.getLogger('wifi_logger')
    if cell:
        vendor_mac = matching_line(cell, "Address: ")[0:8]
        if vendor_mac is None:
            return "no mac!"
        else:
            try:
                return vendors[vendor_mac]
            except KeyError:
                return f"UNKNOWN"
    else:
        wifi_logger.error(f"[{__name__}]:get_vendor got no cell!!")
        return "no cell!"


[proc_vendors(vendor, vendors) for vendor in vendorsMacs_XML.getroot()]


def get_timing(cell):
    """ Gets the mode of a network / cell.
    @param string cell
        A network / cell from iwlist scan.

    @return string
        Last updated timestamp
    """

    time = matching_line(cell, "Extra: Last beacon:")
    if time is None:
        return ""
    return time


def print_table(table):
    # Functional black magic.
    widths = list(map(max, map(lambda l: map(len, l), zip(*table))))

    justified_table = []
    for line in table:
        justified_line = []
        for i, el in enumerate(line):
            try:
                if isinstance(el, str):
                    justified_line.append(el.ljust(widths[i] + 2))
                if isinstance(el, list):
                    pass  # don't deal with lists of signal_cache
            except AttributeError:
                pass  # I got an 'el' that doesn't 'justify'

        justified_table.append(justified_line)

    for line in justified_table:
        print("\t".join(line))


def print_signals(sgnls, columns):
    table = [columns]

    def print_signal(sgnl):
        sgnl_properties = []

        def make_cols(column):
            try:
                # make boolean a str to print (needs 'width').
                if isinstance(sgnl[column], bool):
                    sgnl_properties.append(str(sgnl[column]))
                else:
                    sgnl_properties.append(sgnl[column])
            except KeyError as e:
                print(f"KeyError getting column for {e}")

        [make_cols(column) for column in columns]
        table.append(sgnl_properties)

    [print_signal(sgnl) for sgnl in sgnls]
    print_table(table)

def compare_MFCC():
    # TODO: compare_MFCC(), Was in Scanner
    pass


def analyze_periodicity():
    # TODO: analyze_periodicity(), Was in Scanner
    pass


def get_MFCC():
    # TODO: get_MFCC(), Was in Worker
    pass


def append_to_outfile(cls, config, cell):
    """Append found cells to a rolling JSON list"""
    from src.lib.utils import format_time, format_delta
    # unwrap the cell and format the dates, guids and whatnot.
    # {'EE:55:A8:24:B1:0A':
    #   {
    #   'id': 'ee55a824b10a',
    #   'SSID': 'Goodtimes Entertainment Inc.',
    #   'BSSID': 'EE:55:A8:24:B1:0A',
    #   'created': '2025-03-12 00:36:07',
    #   'updated': '2025-03-12 00:36:10',
    #   'elapsed': '00:00:03',
    #   'Vendor': 'UNKNOWN',
    #   'Channel': 11,
    #   'Frequency': 5169,
    #   'Signal': -89,
    #   'Quality': 11,
    #   'Encryption': True,
    #   'is_mute': False,
    #   'tracked': True,
    #   'signal_cache': [
    #       {
    #       'created': '2025-03-12 00:36:07.511398',
    #       'id': '6fb74555-e1f5-440a-9c42-f5649a536279',
    #       'worker_id': 'ee55a824b10a',
    #       'lon': -105.068195,
    #       'lat': 39.9168,
    #       'sgnl': -89
    #       },
    #       {'created': '2025-03-12 00:36:10.641924',
    #       'id': '18967444-39bf-4082-9aa4-d833fbb9ed28',
    #       'worker_id': 'ee55a824b10a',
    #       'lon': -105.068021,
    #       'lat': 39.916915,
    #       'sgnl': -89
    #       }
    #   ],
    #   'tests': []
    #   }
    # }
    #
    # config.get('CREATED_FORMATTER', '%Y-%m-%d %H:%M:%S')
    # config.get(UPDATED_FORMATTER', '%Y-%m-%d %H:%M:%S')
    # config.get(ELAPSED_FORMATTER', '%H:%M:%S')

    # format created timestamp in signals
    # SGNL_CREATED_FORMAT: "%Y-%m-%d %H:%M:%S.%f"
    formatted = {
                "id"          : cell['id'],
                "SSID"        : cell['SSID'],
                "BSSID"       : cell['BSSID'],
                "created"     : cell['created'],
                "updated"     : cell['updated'],
                "elapsed"     : cell['elapsed'],
                "Vendor"      : cell['Vendor'],
                "Channel"     : cell['Channel'],
                "Frequency"   : cell['Frequency'],
                "Signal"      : cell['Signal'],
                "Quality"     : cell['Quality'],
                "Encryption"  : cell['Encryption'],
                "is_mute"     : cell['is_mute'],
                "tracked"     : cell['tracked'],
                "signal_cache": [pt.get() for pt in cls.scanner.signal_cache[cell['BSSID']]] [cls.cache_max:],
                "tests"       : [x for x in cell['tests']]
    }

    json_logger.info({cell['BSSID']: formatted})


def write_to_scanlist(config, searchmap):
    """Write current SEARCHMAP out as JSON"""
    make_path(config.get('OUTFILE_PATH', "out"))
    _time = datetime.now().strftime(config.get('DATETIME_FORMAT', "%Y%m%d_%H%M%S"))
    if len(searchmap) > 0:  # don't write nothing; write something.
        # todo: process this as above....
        return write_file(config['OUTFILE_PATH'], "scanlist_" + _time + ".json", json.dumps(searchmap, indent=1), "x")


def commit_mapping(config, mapping):
    """ commit data to a git repo, use GIT API """
    # get_credentials(config.get('OUTFILE_PATH', "out"))
    # _time = datetime.now().strftime(config.get('DATETIME_FORMAT', "%Y%m%d_%H%M%S"))
    # return commit_file(config['OUTFILE_PATH'], "scanlist_" + _time + ".json", json.dumps(mapping, indent=1), "x")
    pass