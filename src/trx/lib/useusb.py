import usb

# Find all connected USB devices
devices = usb.core.find(find_all=True)

# Print information about each device
for device in devices:
    print(f"Device: {device.idVendor}:{device.idProduct}")

# Find the USB device
# device = usb.core.find(idVendor=0x1234, idProduct=0x5678)

# Set the device configuration
# device.set_configuration()

# Read data from the device
# endpoint = device[0][(0,0)][0]
# data = device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
# print(f"Received data: {data}")