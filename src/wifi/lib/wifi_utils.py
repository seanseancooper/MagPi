import os
import xml.etree.ElementTree as ET
from datetime import datetime

from .iw_parse import matching_line
from src.config import CONFIG_PATH, readConfig

import logging
logger_root = logging.getLogger('root')

config = {}
readConfig(os.path.join(CONFIG_PATH, 'wifi.json'), config)

vendors = {}
vendorsMacs_XML = ET.parse(os.path.join(CONFIG_PATH, config['VENDORMACS_FILE']))


def proc_vendors(vendor):
    mac_prefix = vendor.attrib["mac_prefix"]
    vendor_name = vendor.attrib["vendor_name"]
    vendors[mac_prefix] = vendor_name


[proc_vendors(vendor) for vendor in vendorsMacs_XML.getroot()]


def get_vendor(cell):
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
        logger_root.error(f"[{__name__}]:get_vendor got no cell!!")
        return "no cell!"


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


def write_foundLIST(config, found_cell, stats):
    """Append found cells to a rolling list"""
    from src.lib.utils import make_path, write_file

    make_path(config.get('OUTFILE_PATH', "out"))
    _time = datetime.now().strftime(config.get('DATETIME_FORMAT', "%Y-%m-%d %H:%M:%S.%f"))
    write_file(config['OUTFILE_PATH'], config['OUT_FILE'] + ".out", f"{_time}: {found_cell} {stats}", "a")


def write_trackedJSON(config, searchmap):
    """Write current SEARCHMAP out as JSON"""
    from src.lib.utils import make_path, write_file
    import json

    make_path(config.get('OUTFILE_PATH', "out"))
    _time = datetime.now().strftime(config.get('DATETIME_FORMAT', "%Y-%m-%d %H:%M:%S.%f"))
    write_file(config['OUTFILE_PATH'], "scanlist_" + _time + ".json", json.dumps(searchmap, indent=1), "x")

    return True
