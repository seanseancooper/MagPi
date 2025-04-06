import usb.core
import usb.util
import usb.backend.libusb1
import platform


def find_device(vendor_id, product_id):
    backend = None
    if platform.system() == 'Windows':
        arch = platform.architecture()[0]
        dll_path = "libusb/x86/libusb-1.0.dll" if arch == '32bit' else "libusb/x64/libusb-1.0.dll"
        backend = usb.backend.libusb1.get_backend(find_library=lambda x: dll_path)

    device = usb.core.find(idVendor=vendor_id, idProduct=product_id, backend=backend)

    if device is None:
        raise ValueError("Device not found.")

    if platform.system() == 'Linux' and device.is_kernel_driver_active(0):
        device.detach_kernel_driver(0)

    device.set_configuration(1)
    return device


def get_endpoints(device, interface_idx):
    cfg = device.get_active_configuration()[(interface_idx, 0)]
    ep_out = usb.util.find_descriptor(cfg, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
    ep_in = usb.util.find_descriptor(cfg, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
    return ep_in, ep_out


def wrap_command(cmd: bytes) -> bytes:
    return b'\x02' + cmd + b'\x03'


def send_command(dev, endpoint_out, cmd: bytes):
    data = wrap_command(cmd)
    return dev.write(endpoint_out.bEndpointAddress, data)


def read_response(dev, endpoint_in, timeout=200):
    try:
        data = dev.read(endpoint_in.bEndpointAddress, 64, timeout)
        if data:
            result = ''.join(chr(x) for x in data[1:]).split('\x00', 1)[0]
            return result if result else None
    except usb.core.USBError as e:
        print(f"Read error: {e}")
    return None
