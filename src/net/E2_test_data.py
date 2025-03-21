import random
import uuid
import string
from datetime import datetime, timedelta

CARTOON_NAMES = ["Mickey", "Donald", "Goofy", "Bugs", "Daffy", "Popeye", "Scooby", "Shaggy", "Tom", "Jerry"]
VENDORS = ["ACME", "BETA", "CHARLIE", "UNknOwN"]


def random_hex_octet():
    return ':'.join(f'{random.randint(0, 255):02x}' for _ in range(6))


def generate_worker():
    bssid = random_hex_octet()
    created = datetime.utcnow() - timedelta(seconds=random.randint(0, 300))  # Last 5 minutes
    updated = created + timedelta(seconds=random.randint(1, 300))
    elapsed = updated - created

    worker = {
        "id"          : bssid.replace(":", "").lower(),
        "SSID"        : random.choice(CARTOON_NAMES),
        "BSSID"       : bssid,
        "created"     : created.strftime("%Y-%m-%d %H:%M:%S"),
        "updated"     : updated.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed"     : str(elapsed),
        "Vendor"      : random.choice(VENDORS),
        "Channel"     : random.randint(1, 165),
        "Frequency"   : random.randint(-32768, 32767),
        "Signal"      : random.randint(-99, 0),
        "Quality"     : random.randint(0, 100),
        "Encryption"  : random.choice([True, False]),
        "is_mute"     : random.choice([True, False]),
        "tracked"     : random.choice([True, False]),
        "tests"       : [],
        "signal_cache": generate_signal_cache(created)
    }

    return worker


def generate_signal_cache(worker_created):
    num_signals = random.randint(1, 5)  # Generate between 1 to 5 signals per worker
    signals = []
    for _ in range(num_signals):
        created = worker_created + timedelta(seconds=random.randint(1, 600))  # After worker creation
        signal = {
            "created"  : created.strftime("%Y-%m-%d %H:%M:%S"),
            "id"       : str(uuid.uuid4()),
            "worker_id": "",  # Will be filled later based on parent worker
            "lon"      : round(random.uniform(-180.0, 180.0), 6),
            "lat"      : round(random.uniform(-90.0, 90.0), 6),
            "sgnl"     : random.randint(-99, 0)
        }
        signals.append(signal)

    return signals


def generate_dataset(num_workers=10):
    dataset = []
    for _ in range(num_workers):
        worker = generate_worker()
        worker_id = worker["id"]

        # Attach worker_id to signals
        for signal in worker["signal_cache"]:
            signal["worker_id"] = worker_id

        dataset.append(worker)

    return dataset


if __name__ == "__main__":
    num_workers = 10
    data = generate_dataset(num_workers)

    import json

    with open("sample_dataset.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"Generated {num_workers} workers and saved to 'sample_dataset.json'")
