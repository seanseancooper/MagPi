import json
import glob
import uuid
from src.lib.utils import format_time
from src.wifi.lib.wifi_utils import vendorsMacs_XML, proc_vendors
from datetime import datetime, timedelta
from src.config import readConfig
from src.lib.utils import get_location
import random

import numpy as np

# Example values for generating random data
SSIDs = ["DIRECT-a1-HP M477 LaserJet", "CCOB_Library", "Home_Network", "Guest_WiFi", "Office_WiFi"]
vendors = ["UNKNOWN", "Extreme Networks Headquarters", "Cisco", "Netgear", "TP-Link"]
channels = list(range(1, 12))
frequencies = list(range(2400, 2500))
signals = list(range(-100, 0))
qualities = list(range(0, 100))
encryption = [True, False]
is_mute = [True, False]
tracked = [True, False]


class cat_scanlists:

    def __init__(self, scanlist_archive, output_file):

        self.scanlist_archive = scanlist_archive
        self.output_file = output_file
        self.data = []
        self.vendors = {}
        self.mapped_workers = {}
        self.skipped = []
        self.total = 0
        self.scanlist_total = 0
        self.config = {}
        self.lat = 0.0
        self.lon = 0.0
        self.configure()

    def configure(self):
        readConfig('net.json', self.config)
        get_location(self)
        [proc_vendors(vendor, self.vendors) for vendor in vendorsMacs_XML.getroot()]

    def _get_vendor(self, bssid):
        """ a custom implementation get_vendor() for this class that takes a bssid.
            note it's '_'; not intended to be used elsewhere, and it initializes
            inside this class """
        try:
            return self.vendors[bssid[0:8]]
        except KeyError:
            return f"UNKNOWN"

    def read(self):
        for scanlist in sorted(glob.glob(self.scanlist_archive + "/*.json")):
            with open(scanlist, "r") as f:
                try:
                    self.data.append(json.load(f))
                    for scanned in self.data:

                        # for worker in scanned:
                        #     # GOING FORWARD:
                        #     self.mapped_workers[worker['BSSID']] = worker

                        for worker in scanned:
                            try:
                                # LIST OF MAPS: w/ current SignalPoint:
                                self.mapped_workers[worker['BSSID']] = worker
                            except Exception:
                                try:
                                    # early 'signalpoint' array; a MAP of MAPS
                                    worker_bssid = [k for k in worker][0]
                                    worker_data = worker[worker_bssid]
                                    self.mapped_workers[worker_bssid] = worker_data
                                except Exception:
                                    # naked JSON map. 'BSSID': {[{}]}
                                    try:
                                        key = [k for k in worker][0]
                                        value = worker_data
                                        # no created, updated; handled on write()
                                        self.mapped_workers[key] = value
                                    except Exception as e:
                                        print(f'skipped worker {e}')
                                        self.skipped.append(worker)
                    self.scanlist_total += 1
                    print(f'ingested list {self.scanlist_total} {scanlist}')
                except Exception as e:
                    print(f'skipped scanlist {scanlist} {e}')
        print(f'{datetime.now().isoformat()} @ [{self.lon}, {self.lat}]: processed {self.scanlist_total} scanlists, ', end='')

    def write(self, add_signals=False, generate_signalpoints=False):
        with open(self.output_file, 'w') as f:
            f.write('[\n')

            for _id in sorted(self.mapped_workers):
                try:
                    record = self.mapped_workers[_id]

                    from dateutil.parser import parse
                    c_created = parse(record.get('created') or format_time(datetime.now(), "%Y-%m-%d %H:%M:%S")).strftime("%Y-%m-%d %H:%M:%S")
                    c_updated = parse(record.get('updated') or format_time(datetime.now(), "%Y-%m-%d %H:%M:%S")).strftime("%Y-%m-%d %H:%M:%S")

                    record['id'] = _id.replace(':', '').lower()
                    record['SSID'] = record.get('SSID', record.get('ssid'))
                    record['BSSID'] = _id

                    record['created'] = c_created
                    record['updated'] = c_updated
                    record['elapsed'] = datetime.strptime(record.get('elapsed', "00:00:00").split('.')[0], "%H:%M:%S").time().strftime("%H:%M:%S")

                    record['Channel'] = record.get('Channel') or 0
                    record['Frequency'] = record.get('Frequency') or 0
                    record['Signal'] = record.get('Signal') or -99
                    record['Quality'] = record.get('Quality') or 0

                    def process_sgnl(sgnl):
                        return {
                            "created": sgnl.get('created', record['created']),   # this should match the created date of the record
                            "id": sgnl.get('id', str(uuid.uuid4())),
                            "worker_id": record['id'],
                            "lon": sgnl.get('lon', self.lon),
                            "lat": sgnl.get('lat', self.lat),
                            "sgnl": sgnl.get('sgnl', -99)
                        }

                    def generate_signal():
                        base_lat = 39.915
                        base_lon = -105.065
                        spread = 0.003

                        offset_lat = random.uniform(-spread, spread)
                        offset_lon = random.uniform(-spread, spread)

                        return {
                            "created"  : (datetime.utcnow() - timedelta(minutes=random.randint(1, 1000))).isoformat(),
                            "id"       : str(uuid.uuid4()),
                            "worker_id": record['id'],
                            "lat"      : round(base_lat + offset_lat, 6),
                            "lon"      : round(base_lon + offset_lon, 6),
                            "sgnl"     : random.choice(signals)
                        }

                    if generate_signalpoints:
                        cache = [generate_signal() for _ in range(10)]
                    else:
                        cache = [process_sgnl(x) for x in record.get('signal_cache')] if add_signals is True else []

                    out = {
                         "id"           : record['id'],
                         "SSID"         : record['SSID'],
                         "BSSID"        : record['BSSID'],
                         "created"      : record.get('created', format_time(datetime.now(), '%Y-%m-%d %H:%M:%S')),
                         "updated"      : record.get('updated', format_time(datetime.now(), '%Y-%m-%d %H:%M:%S')),
                         "elapsed"      : record.get('elapsed'),

                         "Vendor"       : record.get('Vendor', self._get_vendor(_id)),
                         "Channel"      : int(record['Channel']),
                         "Frequency"    : int(record['Frequency']),
                         "Signal"       : int(record['Signal']),
                         "Quality"      : int(record['Quality']),

                         "Encryption"   : bool(record.get('Encryption', True)),
                         "is_mute"      : False,
                         "tracked"      : True,
                         "signal_cache" : cache,
                         "tests"        : [x for x in record.get('tests', [x for x in record.get('results', [])])]  if add_signals is True else []
                    }

                    f.write(json.dumps(out, indent=2))
                    self.total += 1

                    if self.total < len(self.mapped_workers):
                        f.write(',\n')
                    else:
                        f.write('\n')

                except AttributeError as a:
                    print(f'omitted {record} {a}')
            f.write(']\n')

        print(f'mapped {self.total} signals {add_signals} for {len(self.mapped_workers)} records.')


if __name__ == "__main__":
    archive = '/Users/scooper/PycharmProjects/MagPiDev/wifi/scanlist_archive/'
    output =  '/Users/scooper/PycharmProjects/MagPiDev/wifi/training_data/scanlists_out.json'
    # archive = '_out'
    # output = 'dev/wifi/training_data/scanlists_out.json'
    cat = cat_scanlists(archive, output)

    cat.read()
    cat.write(add_signals=True, generate_signalpoints=True)

