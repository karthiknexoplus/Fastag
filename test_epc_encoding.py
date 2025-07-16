#!/usr/bin/env python3
"""
CLI tool to encode EPC Memory for FASTag as per IHMCL/GS1 spec.
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

def main():
    print("FASTag EPC Memory Encoder (IHMCL/GS1)")
    print("Segments: CCH_ID=1 (5b), Issuer_ID (20b), Key_Index (8b), Serial (20b), RFU (5b)")
    while True:
        issuer_id = get_int_input("Issuer ID", 0, 1048575)
        issuer_key_index = get_int_input("Issuer Key Index", 0, 255)
        serial_number = get_int_input("Serial Number", 0, 1048575)
        rfu = get_int_input("RFU (Reserved for future use)", 0, 31, default=0)
        epc = encode_epc(issuer_id, issuer_key_index, serial_number, rfu)
        print("\nEPC (58 bits):", format(epc, '058b'))
        print("EPC (hex, 15 digits):", format(epc, '015X'))
        print("EPC (hex, 0x prefix):", hex(epc))
        again = input("\nEncode another? (y/n): ").strip().lower()
        if again != 'y':
            break

if __name__ == "__main__":
    main() 