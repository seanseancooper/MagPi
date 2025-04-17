import datetime
import random
import uuid


class FAKETRXUSBRetriever:

    def __init__(self):
        self.freq = None

    def set_freq(self, f):
        self.freq = f

    def get_freq(self):
        return self.freq

    def scan(self):

        # Example values for generating random data
        SSIDs = ["Larry", "Moe", "Curly", "Shemp", "Stooges_Office_WiFi"]
        vendors = ["UNKNOWN", "Extreme Networks", "Cisco", "Netgear", "TP-Link"]
        channels = list(range(1, 12))
        frequencies = list(range(2400, 2500))
        signals = list(range(-99, -30))
        qualities = list(range(0, 100))
        encryption = [True, False]
        is_mute = [True, False]
        tracked = [True, False]

        # Function to generate a random signal cache entry
        def generate_signal_cache(worker_id):
            return {
                "datetime" : (datetime.datetime.utcnow() - datetime.timedelta(minutes=random.randint(1, 1000))).isoformat(),
                "id"       : str(uuid.uuid4()),
                "worker_id": worker_id,
                "lon"      : round(random.uniform(-105.068000, -105.060000), 6),
                "lat"      : round(random.uniform(39.910000, 39.920000), 6),
                "sgnl"     : random.choice(signals)
            }

        # Function to generate a random worker record
        def generate_worker():
            worker_id = str(uuid.uuid4())
            data = {
                "id"        : worker_id,
                "SSID"      : random.choice(SSIDs),
                "BSSID"     : ":".join(["{:02X}".format(random.randint(0, 255)) for _ in range(6)]),
                "created"   : (datetime.datetime.utcnow() - datetime.timedelta(minutes=random.randint(1, 1000))).strftime('%H:%M:%S'),
                "updated"   : datetime.datetime.utcnow().strftime('%H:%M:%S'),
                "elapsed"   : "00:{:02}:{:02}".format(random.randint(0, 59), random.randint(0, 59)),
                "Vendor"    : random.choice(vendors),
                "Channel"   : random.choice(channels),
                "Frequency" : random.choice(frequencies),
                "Signal"    : random.choice(signals),
                "Quality"   : random.choice(qualities),
                "Encryption": random.choice(encryption),
                "is_mute"   : random.choice(is_mute),
                "tracked"   : random.choice(tracked),
                "signal_cache": [generate_signal_cache(worker_id) for _ in range(160)]
            }

            return data

        # Generate 30 worker records
        print(f'scanning on frequency: {self.freq}')
        return [generate_worker() for _ in range(30)]

