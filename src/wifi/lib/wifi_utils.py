import os
import xml.etree.ElementTree as ET
from datetime import datetime

from .iw_parse import matching_line
from src.config import CONFIG_PATH, readConfig
from src.lib.utils import make_path, write_file
import json

import logging
logger_root = logging.getLogger('root')

config = {}
readConfig(os.path.join(CONFIG_PATH, 'wifi.json'), config)

vendors = {}
vendorsMacs_XML = ET.parse(os.path.join(CONFIG_PATH, config['VENDORMACS_FILE']))


def proc_vendors(vendor):
    vendors[vendor.attrib["mac_prefix"]] = vendor.attrib["vendor_name"]


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


[proc_vendors(vendor) for vendor in vendorsMacs_XML.getroot()]


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


def append_to_outfile(config, cell):
    """Append found cells to a rolling list"""

    make_path(config.get('OUTFILE_PATH', "out"))
    _time = datetime.now().strftime(config.get('DATETIME_FORMAT', "%Y%m%d_%H%M%S"))
    write_file(config['OUTFILE_PATH'], config['OUT_FILE'] + ".out", json.dumps(cell, indent=1), "a")


def write_to_scanlist(config, searchmap):
    """Write current SEARCHMAP out as JSON"""

    make_path(config.get('OUTFILE_PATH', "out"))
    _time = datetime.now().strftime(config.get('DATETIME_FORMAT', "%Y%m%d_%H%M%S"))
    if write_file(config['OUTFILE_PATH'], "scanlist_" + _time + ".json", json.dumps(searchmap, indent=1), "x"):
        return True
