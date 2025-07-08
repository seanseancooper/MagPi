import json
from datetime import datetime
import logging
from src.lib.utils import make_path, write_file

json_logger = logging.getLogger('json_logger')

def write_to_scanlist(config, searchmap):
    """Write current searchmap out as JSON"""
    out_path = make_path(config.get('OUTFILE_PATH', "out"))
    fmt = config.get('DATETIME_FORMAT', "%Y%m%d_%H%M%S")
    t = datetime.now().strftime(fmt)
    outfile = "scanlist_" + t.replace('-', '').replace(':', '').replace(' ', '_') + ".json"

    if len(searchmap) > 0:
        return write_file(out_path, outfile, json.dumps(searchmap, indent=1), "x")

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


def append_to_outfile(cls, config, cell):
    """Append found cells to a rolling JSON list"""
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