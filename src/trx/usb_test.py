import usb.core
import usb.util
import usb.backend.libusb1

def main():
    backend = usb.backend.libusb1.get_backend()
    if not backend:
        print("libusb backend not found. Make sure it's installed (brew install libusb).")
        return

    print("Scanning for USB devices...\n")

    devices = usb.core.find(find_all=True, backend=backend)
    if devices is None:
        print("No USB devices found.")
        return

    for i, dev in enumerate(devices, start=1):
        print(f"Device {i}:")
        print(f"  Vendor ID : {hex(dev.idVendor)}")
        print(f"  Product ID: {hex(dev.idProduct)}")
        try:
            print(f"  Manufacturer: {usb.util.get_string(dev, dev.iManufacturer)}")
            print(f"  Product     : {usb.util.get_string(dev, dev.iProduct)}")
        except Exception as e:
            print(f"  Could not read strings: {e}")
        print("-" * 40)

if __name__ == "__main__":
    main()
