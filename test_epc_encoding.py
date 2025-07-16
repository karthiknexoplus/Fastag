#!/usr/bin/env python3
"""
CLI tool to encode/decode EPC Memory for FASTag as per IHMCL/GS1 spec.
Segments:
- CCH ID: 5 bits (fixed to 1)
- Issuer ID: 20 bits (0–1048575)
- Issuer Key Index: 8 bits (0–255)
- Serial Number: 20 bits (0–1048575)
- RFU: 5 bits (0–31, default 0)
Total: 58 bits
"""

def get_int_input(prompt, minval, maxval, default=None):
    while True:
        val = input(f"{prompt} [{minval}-{maxval}{' default '+str(default) if default is not None else ''}]: ").strip()
        if not val and default is not None:
            return default
        try:
            ival = int(val)
            if minval <= ival <= maxval:
                return ival
            else:
                print(f"Value must be between {minval} and {maxval}.")
        except ValueError:
            print("Invalid integer. Try again.")

def encode_epc(issuer_id, issuer_key_index, serial_number, rfu=0):
    cch_id = 1  # 5 bits, fixed
    # Bit layout: [CCH_ID(5)][Issuer_ID(20)][Key_Index(8)][Serial(20)][RFU(5)]
    epc = (cch_id << (20+8+20+5)) \
        | (issuer_id << (8+20+5)) \
        | (issuer_key_index << (20+5)) \
        | (serial_number << 5) \
        | (rfu & 0b11111)
    return epc

def decode_epc(epc):
    if isinstance(epc, str):
        epc = epc.strip()
        if epc.startswith('0x') or epc.startswith('0X'):
            epc = int(epc, 16)
        else:
            epc = int(epc)
    cch_id = (epc >> 53) & 0b11111
    issuer_id = (epc >> 33) & 0xFFFFF
    issuer_key_index = (epc >> 25) & 0xFF
    serial_number = (epc >> 5) & 0xFFFFF
    rfu = epc & 0b11111
    return {
        'CCH_ID': cch_id,
        'Issuer_ID': issuer_id,
        'Issuer_Key_Index': issuer_key_index,
        'Serial_Number': serial_number,
        'RFU': rfu
    }

def main():
    print("FASTag EPC Memory Encoder/Decoder (IHMCL/GS1)")
    print("Segments: CCH_ID=1 (5b), Issuer_ID (20b), Key_Index (8b), Serial (20b), RFU (5b)")
    while True:
        print("\nChoose an option:")
        print("1. Encode EPC")
        print("2. Decode EPC")
        print("3. Exit")
        choice = input("Enter 1, 2, or 3: ").strip()
        if choice == '1':
            issuer_id = get_int_input("Issuer ID", 0, 1048575)
            issuer_key_index = get_int_input("Issuer Key Index", 0, 255)
            serial_number = get_int_input("Serial Number", 0, 1048575)
            rfu = get_int_input("RFU (Reserved for future use)", 0, 31, default=0)
            epc = encode_epc(issuer_id, issuer_key_index, serial_number, rfu)
            print("\nEPC (58 bits):", format(epc, '058b'))
            print("EPC (hex, 15 digits):", format(epc, '015X'))
            print("EPC (hex, 0x prefix):", hex(epc))
        elif choice == '2':
            epc_val = input("Enter EPC value (hex or int): ").strip()
            try:
                fields = decode_epc(epc_val)
                print("\nDecoded EPC fields:")
                for k, v in fields.items():
                    print(f"{k}: {v}")
            except Exception as e:
                print("Error decoding EPC:", e)
        elif choice == '3':
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main() 