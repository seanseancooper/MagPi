import json
import glob
import uuid
from src.lib.utils import format_time
from src.wifi.lib.wifi_utils import vendorsMacs_XML, proc_vendors
from datetime import datetime, timedelta
from src.config import readConfig
from src.lib.utils import get_location

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
        self.latitude = 0.0
        self.longitude = 0.0
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
                        for worker in scanned:
                            try:
                                # LIST OF MAPS: this is the current way a SignalPoint looks:
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
                                    # an early 'signalpoint' arrays were structured as a MAP of MAPS:
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
                                    # handle even earlier structure, a naked JSON map.
                                    # '00:54:AF:8F:D9:26': {
                                    # 'ssid': 'HotspotD926',
                                    # 'tests': {},
                                    # 'return_all': True
                                    # }
                                    try:
                                        key = [k for k in worker][0]
                                        value = worker_data
                                        self.mapped_workers[key] = value
                                    except Exception as e:
                                        print(f'skipped worker {e}')
                                        self.skipped.append(worker)

                    self.scanlist_total += 1
                    print(f'ingested list {self.scanlist_total} {scanlist}')

                except Exception as e:
                    print(f'skipped scanlist {scanlist} {e}')

        print(f'{datetime.now().isoformat()} @ [{self.longitude}, {self.latitude}]: processed {self.scanlist_total} scanlists, ', end='')

    def write(self, add_signals=False):
        with open(self.output_file, 'w') as f:
            f.write('[\n')

            for _id in sorted(self.mapped_workers):
                try:
                    record = self.mapped_workers[_id]

                    from dateutil.parser import parse
                    c_created = parse(record.get('created')).strftime("%Y-%m-%d %H:%M:%S")
                    c_updated = parse(record.get('updated')).strftime("%Y-%m-%d %H:%M:%S")

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

                    out = {
                         "id"           : record['id'],
                         "SSID"         : record['SSID'],
                         "BSSID"        : record['BSSID'],
                         "created"      : record.get('created', format_time(datetime.now(), '%Y-%m-%d %H:%M:%S')),
                         "updated"      : record.get('updated', format_time(datetime.now(), '%Y-%m-%d %H:%M:%S')),
                         "elapsed"      : record.get('elapsed'),

                         "Vendor"       : record.get('Vendor', self._get_vendor(_id)),
                         "Channel"      : record['Channel'],
                         "Frequency"    : record['Frequency'],
                         "Signal"       : record['Signal'],
                         "Quality"      : record['Quality'],

                         "Encryption"   : record.get('Encryption', True),
                         "is_mute"      : False,
                         "tracked"      : True,
                         "signal_cache" : [process_sgnl(x) for x in record.get('signal_cache', [])] if add_signals is True else [],
                         "tests"        : [x for x in record.get('tests', [x for x in record.get('results', [])])]  if add_signals is True else []
                    }

                    def process_sgnl(sgnl):

                        return {
                            "created": sgnl.get('created', record['created']),   # this should match the created date of the record
                            "id": sgnl.get('id', str(uuid.uuid4())),
                            "worker_id": record['id'],
                            "lon": sgnl.get('lon', self.longitude),
                            "lat": sgnl.get('lat', self.latitude),
                            "sgnl": sgnl.get('sgnl', -99)
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

        print(f'mapped {self.total} signals for {len(self.mapped_workers)} records.')


if __name__ == "__main__":
    archive = '/Users/scooper/PycharmProjects/MagPi/dev/wifi/scanlist_archive/'
    output = '/Users/scooper/PycharmProjects/MagPi/dev/wifi/training_data/scanlists_out.json'
    # archive = '_out'
    # output = 'dev/wifi/training_data/scanlists_out.json'
    cat = cat_scanlists(archive, output)

    cat.read()
    cat.write(add_signals=True)

