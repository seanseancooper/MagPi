import os
os.environ['PYUSB_DEBUG'] = 'debug' # uncomment for verbose pyusb output
import platform
import usb.core
import usb.backend.libusb1

VENDOR_ID = 10841
PRODUCT_ID = 16


def write_to_adu(dev, msg_str):
    print("Writing command: {}".format(msg_str))

    # return the string representing the character i
    # byte_str = chr(0x02) + msg_str + chr(0x03)

    num_bytes_written = 0

    try:
        num_bytes_written = dev.write(1, msg_str)
    except usb.core.USBError as e:
        print(e.args)

    return num_bytes_written


def read_from_adu(dev, timeout):
    try:
        data = dev.read(0x83, 64, timeout)
    except usb.core.USBError as e:
        print ("Error reading response: {}".format(e.args))
        return None

    byte_str = ''.join(chr(n) for n in data[1:]) # construct a string out of the read values, starting from the 2nd byte
    result_str = byte_str.split('\x00',1)[0] # remove the trailing null '\x00' characters

    if len(result_str) == 0:
        return None

    return result_str

was_kernel_driver_active = False
device = None

if platform.system() == 'Windows':
    backend = None
    # required for Windows only
    # libusb DLLs from: https://sourcefore.net/projects/libusb/
    arch = platform.architecture()
    if arch[0] == '32bit':
        backend = usb.backend.libusb1.get_backend(find_library=lambda x: "libusb/x86/libusb-1.0.dll") # 32-bit DLL, select the appropriate one based on your Python installation
    elif arch[0] == '64bit':
        backend = usb.backend.libusb1.get_backend(find_library=lambda x: "libusb/x64/libusb-1.0.dll") # 64-bit DLL

    device = usb.core.find(backend=backend, idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
elif platform.system() == 'Linux':
    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

    # if the OS kernel already claimed the device
    if device.is_kernel_driver_active(0) is True:
        # tell the kernel to detach
        device.detach_kernel_driver(0)
        was_kernel_driver_active = True
else:
    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if device is None:
    raise ValueError('Device not found. Please ensure it is connected.')

for cfg in device:
    print(f'cfg : {cfg.bConfigurationValue}')
    for i in cfg:
        print(f'interface number: {i.bInterfaceNumber}')
        for e in i:
            print(f'endpoint address: {e.bEndpointAddress}')
# interface number: 0
# endpoint address: 129
# endpoint address: 1

# interface number: 1
# endpoint address: 130
# endpoint address: 3
# endpoint address: 131

device.reset()

# Set the active configuration. With no arguments, the first configuration will be the active one
device.set_configuration()

# Claim interface

for cfg in device:
    [print(device, i.iInterface) for i in cfg]

# usb.util.claim_interface(device, 1)

# Write commands
message = chr(0x02) + 'A' + chr(0x03)
chksum = sum(bytes(message, encoding='utf-8')) and 0xFF

bytes_written = write_to_adu(device, message)  # send STX A ETX
bytes_written = write_to_adu(device, chksum)  # send SUM

# Read data back
data = read_from_adu(device, 10)  # read from device with a 200 millisecond timeout

if data != None:
    print("Received string: {}".format(data))
    print("Received data as int: {}".format(int(data)))

usb.util.release_interface(device, 0)

# This applies to Linux only - reattach the kernel driver if we previously detached it
if was_kernel_driver_active == True:
    device.attach_kernel_driver(0)
