from datetime import datetime, timedelta
import random
import uuid
import logging

json_logger = logging.getLogger('json_logger')

def write_to_scanlist(config, searchmap):
    """Write current searchmap out as JSON"""
    make_path(config.get('OUTFILE_PATH', "out"))
    _time = datetime.now().strftime(config.get('DATETIME_FORMAT', "%Y%m%d_%H%M%S"))
    if len(searchmap) > 0:  # don't write nothing; write something.
        # todo: process this as above....
        return write_file(config['OUTFILE_PATH'], "scanlist_" + _time + ".json", json.dumps(searchmap, indent=1), "x")

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