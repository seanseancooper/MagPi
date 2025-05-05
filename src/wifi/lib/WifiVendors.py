
import os
import xml.etree.ElementTree as ET
from src.config import CONFIG_PATH, readConfig

config = {}
readConfig('wifi.json', config)

vendors = {}
vendorsMacs_XML = ET.parse(os.path.join(CONFIG_PATH, config['VENDORMACS_FILE']))


def matching_line(lines, keyword):
    """ Returns the first matching line in a list of lines.
    @see match()
    """
    for line in lines:
        matching = match(line, keyword)
        if matching != None:
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


def proc_vendors(vendor, vendors):
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
        return f"[{__name__}]:get_vendor got no cell!!"


[proc_vendors(vendor, vendors) for vendor in vendorsMacs_XML.getroot()]

