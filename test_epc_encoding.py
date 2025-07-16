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

import sys

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

def encode_epc96_icici(header, gs1, tag_supplier_id, serial_no, epc_validation=0):
    # [Header(8)][GS1(24)][TagSupplierID(5)][SerialNo(32)][EPCValidation(16)] = 85 bits, pad to 96 bits
    epc = (header & 0xFF) << (24+5+32+16)
    epc |= (gs1 & 0xFFFFFF) << (5+32+16)
    epc |= (tag_supplier_id & 0x1F) << (32+16)
    epc |= (serial_no & 0xFFFFFFFF) << 16
    epc |= (epc_validation & 0xFFFF)
    return epc

def decode_epc96_icici(epc):
    if isinstance(epc, str):
        epc = epc.strip()
        if epc.startswith('0x') or epc.startswith('0X'):
            epc = int(epc, 16)
        else:
            epc = int(epc)
    header = (epc >> 77) & 0xFF
    gs1 = (epc >> 53) & 0xFFFFFF
    tag_supplier_id = (epc >> 48) & 0x1F
    serial_no = (epc >> 16) & 0xFFFFFFFF
    epc_validation = epc & 0xFFFF
    return {
        'Header': header,
        'GS1': gs1,
        'Tag_Supplier_ID': tag_supplier_id,
        'Serial_No': serial_no,
        'EPC_Validation': epc_validation
    }

def encode_epc96_ihmcl(header, filter_val, partition, ihmcl_prefix, cch_id, tag_vendor_id, vehicle_id, future_use=0):
    # [Header(8)][Filter(3)][Partition(3)][IHMCL Prefix(24)][CCH ID(5)][Tag Vendor ID(5)][Vehicle ID(26)][Future Use(6)][Checksum(16)]
    # Checksum is calculated after all other fields are set
    epc = (header & 0xFF) << (3+3+24+5+5+26+6+16)
    epc |= (filter_val & 0x7) << (3+24+5+5+26+6+16)
    epc |= (partition & 0x7) << (24+5+5+26+6+16)
    epc |= (ihmcl_prefix & 0xFFFFFF) << (5+5+26+6+16)
    epc |= (cch_id & 0x1F) << (5+26+6+16)
    epc |= (tag_vendor_id & 0x1F) << (26+6+16)
    epc |= (vehicle_id & 0x3FFFFFF) << (6+16)
    epc |= (future_use & 0x3F) << 16
    # Checksum will be added later
    return epc

def add_checksum_epc96_ihmcl(epc):
    # Calculate checksum (Modulo 10) on the decimal representation of the EPC (excluding the last 16 bits)
    epc_no_checksum = epc >> 16
    dec_str = str(epc_no_checksum)
    # Modulo 10 algorithm: multiply odd/even positions by 3/1 from right
    total = 0
    for i, digit in enumerate(reversed(dec_str)):
        n = int(digit)
        if (i % 2) == 0:
            total += n * 3
        else:
            total += n
    check_digit = (10 - (total % 10)) % 10
    # Place checksum in last 16 bits (for demo, just use check_digit in lowest byte)
    epc_with_checksum = (epc & (~0xFFFF)) | check_digit
    return epc_with_checksum, check_digit

def decode_epc96_ihmcl(epc):
    if isinstance(epc, str):
        epc = epc.strip()
        if epc.startswith('0x') or epc.startswith('0X'):
            epc = int(epc, 16)
        else:
            epc = int(epc)
    header = (epc >> 88) & 0xFF
    filter_val = (epc >> 85) & 0x7
    partition = (epc >> 82) & 0x7
    ihmcl_prefix = (epc >> 58) & 0xFFFFFF
    cch_id = (epc >> 53) & 0x1F
    tag_vendor_id = (epc >> 48) & 0x1F
    vehicle_id = (epc >> 22) & 0x3FFFFFF
    future_use = (epc >> 16) & 0x3F
    checksum = epc & 0xFFFF
    return {
        'Header': header,
        'Filter': filter_val,
        'Partition': partition,
        'IHMCL_Prefix': ihmcl_prefix,
        'CCH_ID': cch_id,
        'Tag_Vendor_ID': tag_vendor_id,
        'Vehicle_ID': vehicle_id,
        'Future_Use': future_use,
        'Checksum': checksum
    }

def main():
    print("FASTag EPC Memory Encoder/Decoder (IHMCL/GS1/ICICI)")
    print("Segments: CCH_ID=1 (5b), Issuer_ID (20b), Key_Index (8b), Serial (20b), RFU (5b)")
    while True:
        print("\nChoose an option:")
        print("1. Encode EPC-58 (GS1)")
        print("2. Decode EPC-58 (GS1)")
        print("3. Encode EPC-96 (ICICI)")
        print("4. Decode EPC-96 (ICICI)")
        print("5. Encode EPC-96 (IHMCL)")
        print("6. Decode EPC-96 (IHMCL)")
        print("7. Exit")
        choice = input("Enter 1-7: ").strip()
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
            header = get_int_input("Header", 0, 255, default=91)
            gs1 = get_int_input("GS1 (24b, e.g. 8907048)", 0, 16777215, default=8907048)
            tag_supplier_id = get_int_input("Tag Supplier ID", 1, 31)
            serial_no = get_int_input("Unique Tag Serial No", 0, 0xFFFFFFFF)
            epc_validation = get_int_input("EPC Validation (future use)", 0, 0xFFFF, default=0)
            epc = encode_epc96_icici(header, gs1, tag_supplier_id, serial_no, epc_validation)
            print("\nEPC-96 (ICICI) (96 bits):", format(epc, '096b'))
            print("EPC-96 (ICICI) (hex, 24 digits):", format(epc, '024X'))
            print("EPC-96 (ICICI) (hex, 0x prefix):", hex(epc))
        elif choice == '4':
            epc_val = input("Enter EPC-96 (ICICI) value (hex or int): ").strip()
            try:
                fields = decode_epc96_icici(epc_val)
                print("\nDecoded EPC-96 (ICICI) fields:")
                for k, v in fields.items():
                    print(f"{k}: {v}")
            except Exception as e:
                print("Error decoding EPC-96 (ICICI):", e)
        elif choice == '5':
            header = get_int_input("Header", 0, 255, default=52)
            filter_val = get_int_input("Filter", 0, 7, default=0)
            partition = get_int_input("Partition", 0, 7, default=5)
            ihmcl_prefix = get_int_input("IHMCL Prefix", 0, 16777215, default=8907272)
            cch_id = get_int_input("CCH ID", 0, 31)
            tag_vendor_id = get_int_input("Tag Vendor ID", 0, 31)
            vehicle_id = get_int_input("Vehicle ID", 0, 67108863)
            future_use = get_int_input("Future Use", 0, 63, default=0)
            epc = encode_epc96_ihmcl(header, filter_val, partition, ihmcl_prefix, cch_id, tag_vendor_id, vehicle_id, future_use)
            epc_with_checksum, check_digit = add_checksum_epc96_ihmcl(epc)
            print(f"\nEPC-96 (IHMCL) (96 bits): {format(epc_with_checksum, '096b')}")
            print(f"EPC-96 (IHMCL) (hex, 24 digits): {format(epc_with_checksum, '024X')}")
            print(f"EPC-96 (IHMCL) (hex, 0x prefix): {hex(epc_with_checksum)}")
            print(f"Checksum (Modulo 10): {check_digit}")
        elif choice == '6':
            epc_val = input("Enter EPC-96 (IHMCL) value (hex or int): ").strip()
            try:
                fields = decode_epc96_ihmcl(epc_val)
                print("\nDecoded EPC-96 (IHMCL) fields:")
                for k, v in fields.items():
                    print(f"{k}: {v}")
            except Exception as e:
                print("Error decoding EPC-96 (IHMCL):", e)
        elif choice == '7':
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main() 