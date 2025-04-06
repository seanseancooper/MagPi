import os
import platform
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta

import usb.core
import usb.util
import usb.backend.libusb1

from src.config import readConfig
from src.lib.utils import get_location
from src.trx.lib.TRXSignalPoint import TRXSignalPoint

def find_device(vendor_id, product_id):
    if platform.system() == 'Windows':
        arch = platform.architecture()[0]
        dll_path = "libusb/x86/libusb-1.0.dll" if arch == '32bit' else "libusb/x64/libusb-1.0.dll"
        backend = usb.backend.libusb1.get_backend(find_library=lambda x: dll_path)
        dev = usb.core.find(backend=backend, idVendor=vendor_id, idProduct=product_id)
    else:
        dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if dev and dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)  # permission denied

    if dev is None:
        raise ValueError("Device not found. Ensure it's connected.")

    dev.set_configuration(1)
    return dev

def get_endpoints(device, interface_idx=1):
    cfg = device.get_active_configuration()
    intf = cfg[(interface_idx, 0)]

    ep_out = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(
        e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
    ep_in = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(
        e.bEndpointAddress) == usb.util.ENDPOINT_IN)

    return ep_in, ep_out

def send_command(device, endpoint, cmd_bytes):
    try:
        print(f"[USB] Sending: {cmd_bytes}")
        endpoint.write(cmd_bytes)
    except usb.core.USBError as e:
        print(f"[USB] Write error: {e}")

def read_response(device, endpoint, timeout=200):
    try:
        data = endpoint.read(64, timeout)
        response = ''.join(chr(n) for n in data).split('\x00', 1)[0]
        return response
    except usb.core.USBError as e:
        print(f"[USB] Read error: {e}")
        return None


class TRXUSBRetriever(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.worker_id = 'TRXUSBRetriever'

        self.out = None
        self.signal_cache = []
        self.tracked_signals = defaultdict(dict)

        self.created = datetime.now()
        self.updated = datetime.now()
        self.elapsed = timedelta()

        self.latitude = 0.0
        self.longitude = 0.0

        self.retrieving = False

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def make_signalpoint(self):
        get_location(self)
        sgnl = TRXSignalPoint(self.worker_id, self.longitude, self.latitude, 0.0, self.out)

        while len(self.signal_cache) >= self.config.get('SIGNAL_CACHE_MAX', 150):
            self.signal_cache.pop(0)

        self.signal_cache.append(sgnl)

    def _usb_command_loop(self):
        try:
            device = find_device(10841, 16)
            # device = find_device(self.config.get('SIGNAL_CACHE_MAX', 10841), self.config.get('SIGNAL_CACHE_MAX', 16))
            ep_in, ep_out = get_endpoints(device)
            interval = self.config.get('USB_POLL_INTERVAL', 1)

            while self.retrieving:
                command = b'A'  # Could rotate more commands here
                send_command(device, ep_out, command)
                response = read_response(device, ep_in)

                if response:
                    print(f"[USB] Got: {response}")
                    self.out = {"RAW": response}
                    self.make_signalpoint()

                self.updated = datetime.now()
                self.elapsed = self.updated - self.created

                time.sleep(interval)

        except Exception as e:
            print(f"[USB] Loop Error: {e}")

    def run(self):
        self.configure('trx.json')
        self.retrieving = True
        self._usb_command_loop()

    def stop(self):
        self.retrieving = False
        print("[USB] Retriever stopping...")


if __name__ == '__main__':
    retriever = TRXUSBRetriever()
    try:
        retriever.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        retriever.stop()
        retriever.join()
