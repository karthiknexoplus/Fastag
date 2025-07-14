import ctypes
import time

# Path to your .so file (update if needed)
LIB_PATH = 'fastag/rfid/libSWNetClientApi.so'

def main():
    ip = input("Enter reader IP address (e.g., 192.168.1.101): ").strip()
    port = 60000

    lib = ctypes.cdll.LoadLibrary(LIB_PATH)
    lib.SWNet_OpenDevice.argtypes = [ctypes.c_char_p, ctypes.c_int]
    lib.SWNet_OpenDevice.restype = ctypes.c_int
    lib.SWNet_ReadDeviceOneParam.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.POINTER(ctypes.c_ubyte)]
    lib.SWNet_ReadDeviceOneParam.restype = ctypes.c_int
    lib.SWNet_SetDeviceOneParam.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_ubyte]
    lib.SWNet_SetDeviceOneParam.restype = ctypes.c_int
    lib.SWNet_CloseDevice.restype = ctypes.c_int

    ip_bytes = ip.encode()

    # Open device
    if lib.SWNet_OpenDevice(ip_bytes, port) == 0:
        print("Failed to open device")
        return

    # Get RF Power
    value = ctypes.c_ubyte()
    result = lib.SWNet_ReadDeviceOneParam(0xFF, 0x05, ctypes.byref(value))
    if result == 0:
        print("Failed to read RF Power")
    else:
        print(f"Current RF Power: {value.value} dBm")

    # Set RF Power
    set_rf = input("Enter new RF Power to set (1-30, or blank to skip): ").strip()
    if set_rf:
        try:
            new_rf = int(set_rf)
            if not (1 <= new_rf <= 30):
                print("RF Power must be between 1 and 30")
            else:
                result = lib.SWNet_SetDeviceOneParam(0xFF, 0x05, new_rf)
                if result == 0:
                    print("Failed to set RF Power.")
                else:
                    print("RF Power set successfully. Confirming...")
                    for attempt in range(5):
                        time.sleep(0.5)
                        value = ctypes.c_ubyte()
                        lib.SWNet_ReadDeviceOneParam(0xFF, 0x05, ctypes.byref(value))
                        if value.value == new_rf:
                            print(f"Confirmed RF Power: {value.value} dBm")
                            break
        except ValueError:
            print("Invalid input for RF Power.")

    lib.SWNet_CloseDevice()
    print("Device closed.")

if __name__ == '__main__':
    main() 