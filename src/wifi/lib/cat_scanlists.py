import os
import json
import glob
from src.config import CONFIG_PATH, readConfig
import xml.etree.ElementTree as ET
from src.lib.utils import format_time
from datetime import datetime


class cat_scanlists:

    def __init__(self, scanlist_archive, output_file):

        self.scanlist_archive = scanlist_archive
        self.output_file = output_file
        self.data = []
        self.config = {}
        self.vendors = {}
        self.mapped_workers = {}
        self.skipped = []
        self.scanlist_stats = {}
        self.total = 0
        self.scanlist_total = 0

        def proc_vendors(vendor):
            self.vendors[vendor.attrib["mac_prefix"]] = vendor.attrib["vendor_name"]

        readConfig('wifi.json', self.config)
        vendorsMacs_XML = ET.parse(os.path.join(CONFIG_PATH, self.config['VENDORMACS_FILE']))
        [proc_vendors(vendor) for vendor in vendorsMacs_XML.getroot()]

    def get_vendor(self, bssid):
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
                        for worker in scanned:
                            try:

                                # LIST OF MAPS
                                # [
                                #  {
                                #   "SSID": "DIRECT-xy2852C1-",
                                #   "BSSID": "0E:61:27:28:52:C1",
                                #   "created": "12:23:45",
                                #   "updated": "16:44:57",
                                #   "elapsed": "04:13:01",
                                #   "Vendor": "UNKNOWN",
                                #   "Channel": 165,
                                #   "Frequency": -32751,
                                #   "Signal": -99,
                                #   "Quality": 20,
                                #   "Encryption": true,
                                #   "is_mute": false,
                                #   "tracked": true,
                                #   "signal_cache": [
                                #    {
                                #     "datetime": "2024-12-13 16:31:58.285970",
                                #     "id": "73f1da2f-ba78-49cd-b9e9-24b3a1721ee7",
                                #     "lon": -105.068433,
                                #     "lat": 39.916845,
                                #     "sgnl": -99
                                #    }
                                #   ],
                                #   "tests": [],
                                #   "results": []
                                #  },

                                self.mapped_workers[worker['BSSID']] = worker
                            except Exception:

                                try:
                                    # an early 'record' A MAP OF MAPS
                                    # {
                                    #     "00:54:AF:A4:C0:F7": {
                                    #         "ssid"      : "HotspotC0F7",
                                    #         "tests"     : {},
                                    #         "return_all": true
                                    #     }
                                    # },
                                    worker_bssid = [k for k in worker][0]
                                    worker_data = worker[worker_bssid]
                                    self.mapped_workers[worker_bssid] = worker_data
                                except Exception:
                                    # another earlier structure?
                                    # '00:54:AF:8F:D9:26': {
                                    # 'ssid': 'HotspotD926',
                                    # 'tests': {},
                                    # 'return_all': True
                                    # }
                                    try:
                                        key = worker
                                        value = worker_data
                                        self.mapped_workers[key] = value
                                    except Exception as e:
                                        print(f'skipped worker {worker} : {e}')
                                        self.skipped.append(worker)


                    self.scanlist_total += 1
                    print(f'ingested list {self.scanlist_total} {scanlist}')
                except Exception as e:
                    print(f'skipped scanlist {scanlist} {e}')

        print(f'processed {self.scanlist_total} scanlists. mapped {len(self.mapped_workers)} signals ', end='')

    def write(self, add_signals=False):
        with open(self.output_file, 'w') as f:
            f.write('[\n')
            self.mapped_workers.pop('message')

            for _id in sorted(self.mapped_workers):
                try:
                    record = self.mapped_workers[_id]

                    out = {
                         "id"           : record.get('id', _id.replace(':', '').lower()),
                         "SSID"         : record.get('SSID', record.get('ssid')),
                         "BSSID"        : _id,
                         "created"      : record.get('created', format_time(datetime.now(), '%Y-%m-%d %H:%M:%S.%f')),
                         "updated"      : record.get('updated'),
                         "elapsed"      : record.get('elapsed'),
                         "Vendor"       : record.get('Vendor', self.get_vendor(_id)),
                         "Channel"      : record.get('Channel'),
                         "Frequency"    : record.get('Frequency'),
                         "Signal"       : record.get('Signal'),
                         "Quality"      : record.get('Quality'),
                         "Encryption"   : record.get('Encryption'),
                         "is_mute"      : record.get('is_mute', False),
                         "tracked"      : record.get('tracked', True),
                         "signal_cache" : [x for x in record.get('signal_cache', [])] if add_signals is True else [],
                         "tests"        : [x for x in record.get('tests', [x for x in record.get('results', [])])]  if add_signals is True else []
                    }

                    f.write(json.dumps(out, indent=2) + ',\n')
                    self.total += 1
                except AttributeError as a:
                    print(f'omitted {record} {a}')
            f.write(']\n')
        print(f'added {self.total} records.')


if __name__ == "__main__":
    archive = '/Users/scooper/PycharmProjects/MagPi/dev/wifi/scanlist_archive'
    output = '/Users/scooper/PycharmProjects/MagPi/dev/wifi/training_data/scanlists_out.json'

    cat = cat_scanlists(archive, output)

    cat.read()
    cat.write()

