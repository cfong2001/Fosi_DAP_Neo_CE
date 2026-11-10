#!/usr/bin/env python3
"""Decode the two USB MSC configuration descriptors found in module 12.

Reads descriptor bytes directly from the stock update image's load-address
mapped module data, not by scanning for coincidental byte patterns.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from rknano_image import Image

SHA256 = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
DATA_BASE = 0x030373e8
CONFIGS = {'full_speed': 0x030373f4, 'high_speed': 0x03037418}


def decode(img):
    if hashlib.sha256(img.raw).hexdigest() != SHA256:
        raise ValueError('release mismatch; descriptor addresses are pinned to V137')
    mod = img.modules[12]
    off, length = img.module_region(12, 'data')
    assert mod['data_exec'] == DATA_BASE
    data = img.raw[off:off+length]
    out = {}
    for label, address in CONFIGS.items():
        pos = address - DATA_BASE
        if not 0 <= pos < length-9 or data[pos:pos+2] != b'\x09\x02':
            raise ValueError(f'missing config descriptor for {label}')
        total = struct.unpack_from('<H', data, pos+2)[0]
        end = pos+total
        if end > len(data):
            raise ValueError('USB descriptor exceeds module 12 data')
        descriptors=[]
        while pos < end:
            n=data[pos]
            if n<2 or pos+n>end:
                raise ValueError('corrupt USB descriptor length')
            typ=data[pos+1]
            raw=data[pos:pos+n]
            rec={'type':typ,'length':n,'file_offset':f'0x{off+pos:x}',
                 'cpu_address':f'0x{DATA_BASE+pos:08x}','raw_hex':raw.hex(' ')}
            if typ==2 and n==9:
                rec.update(total_length=struct.unpack_from('<H',raw,2)[0],
                           num_interfaces=raw[4],configuration_value=raw[5],
                           attributes=raw[7],max_power_2ma=raw[8])
            if typ==4 and n==9:
                rec.update(interface=raw[2],alt_setting=raw[3],endpoints=raw[4],
                           usb_class=raw[5],usb_subclass=raw[6],usb_protocol=raw[7])
            if typ==5 and n in (7,8,9):
                rec.update(endpoint_address=f'0x{raw[2]:02x}',
                           transfer_type=raw[3]&3,max_packet_bytes=struct.unpack_from('<H',raw,4)[0]&0x7ff)
            descriptors.append(rec)
            pos+=n
        out[label] = descriptors
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path)
    a=p.parse_args()
    print(json.dumps(decode(Image(a.image.read_bytes())),indent=2))


if __name__=='__main__':
    main()
