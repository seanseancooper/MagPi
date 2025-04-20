from datetime import datetime, timedelta
import os
import random
import uuid
import xml.etree.ElementTree as ET

from src.config import CONFIG_PATH, readConfig
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


def generate_signal(worker_id):
    base_lat = 39.915
    base_lon = -105.065
    spread = 0.003
    signals = list(range(-100, 0))

    offset_lat = random.uniform(-spread, spread)
    offset_lon = random.uniform(-spread, spread)

    return {
        "created"  : (datetime.now() - timedelta(minutes=random.randint(1, 1000))).isoformat(),
        "id"       : str(uuid.uuid4()),
        "worker_id": worker_id,
        "lat"      : round(base_lat + offset_lat, 6),
        "lon"      : round(base_lon + offset_lon, 6),
        "sgnl"     : random.choice(signals)
    }


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
                "signal_cache": [pt.get() for pt in cls.producer.signal_cache[cell['BSSID']]] [cls.cache_max:],
                "tests"       : [x for x in cell['tests']]
    }

    json_logger.info({cell['BSSID']: formatted})


def commit_mapping(config, mapping):
    """ commit data to a git repo, use GIT API """
    # get_credentials(config.get('OUTFILE_PATH', "out"))
    # _time = datetime.now().strftime(config.get('DATETIME_FORMAT', "%Y%m%d_%H%M%S"))
    # return commit_file(config['OUTFILE_PATH'], "scanlist_" + _time + ".json", json.dumps(mapping, indent=1), "x")
    pass