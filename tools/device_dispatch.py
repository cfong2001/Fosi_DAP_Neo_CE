#!/usr/bin/env python3
"""Resolve the stock firmware's two-entry block-device dispatch table.

The address of the constant table is read from the original literal pool at
0x03067b50. The table layout and the two lookup slots are based on the Thumb
instructions at 0x030678b0 and the indirect BLX calls at 0x030678ca/0x03067912.
This tool never opens a host block device.
"""
import argparse
import json
import struct
from pathlib import Path
from rknano_image import Image

SHA256 = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
ADDR_TABLE_PTR_LITERAL = 0x03067b50
TABLE_STRIDE = 0x28
SLOTS = 2


def code_at(img, address):
    m = img.modules[0]
    if not m['code_exec'] <= address < m['code_exec'] + m['code_len']:
        raise ValueError(f'0x{address:08x} not in module0 code')
    start, _ = img.module_region(0, 'code')
    return start + address - m['code_exec']


def u32_cpu(img, address):
    return struct.unpack_from('<I', img.raw, code_at(img, address))[0]


def decode(img):
    if img.summary()['sha256'] != SHA256:
        raise ValueError('Firmware release mismatch; table and instruction addresses would be unsafe')
    ptr = u32_cpu(img, ADDR_TABLE_PTR_LITERAL)
    result = []
    for slot in range(SLOTS):
        address = ptr + slot * TABLE_STRIDE
        vals = struct.unpack_from('<10I', img.raw, code_at(img, address))
        record = {'slot':slot, 'table_address':f'0x{address:08x}',
                  'device_id':vals[9] & 0xffff,
                  'device_flags':vals[9] >> 16,
                  'operations':{}}
        for index, name in enumerate(('init', 'read', 'write', 'control',
                                      'optional_4','optional_5',
                                      'optional_6','optional_7','optional_8')):
            v=vals[index]
            record['operations'][name]=(f'0x{v:08x}' if v else None)
        result.append(record)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path)
    p.add_argument('--device',type=int,help='restrict output to logical device ID')
    a=p.parse_args()
    items=decode(Image(a.image.read_bytes()))
    if a.device is not None:
        items=[r for r in items if r['device_id']==a.device]
    print(json.dumps(items,indent=2))


if __name__ == '__main__':
    main()
