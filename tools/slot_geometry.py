#!/usr/bin/env python3
"""Compute flash-slot geometry implied by V137's original module-1 instructions.

This models specific code arithmetic, not boot ROM execution. The offsets are
logical device-3 sectors and must never be used as raw flash-write targets.
"""
import argparse
import json
from pathlib import Path
from rknano_image import Image

SHA256='fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
SECTOR_BYTES=512
SECONDARY_SEARCH_STEP_SECTORS=0x800
MAX_MISS_COUNT=0x14

def geometry(image):
    info=image.summary()
    if info['sha256'] != SHA256:
        raise ValueError('unsupported firmware release')
    length=image.u32(0x1f4)
    # Original Thumb: add 0x104000, shift by 9, AND 0xfffff800.
    base=((length+0x104000)>>9)&0xfffff800
    candidates=[base+i*SECONDARY_SEARCH_STEP_SECTORS for i in range(MAX_MISS_COUNT)]
    return {'firmware_sha256':SHA256,'mirror_offset_bytes':length,
            'slot1_logical_sector':0, 'slot2_first_logical_sector':base,
            'slot2_first_logical_offset_bytes':base*SECTOR_BYTES,
            'candidate_logical_sectors':candidates,
            'candidate_step_bytes':SECONDARY_SEARCH_STEP_SECTORS*SECTOR_BYTES,
            'notes':['logical device-3 addresses, not physical flash locations',
                     'first candidate is 0x6800 sectors for V137',
                     '20 misses maximum; not proof of 20 functional slots',
                     'the validator does not examine the CRC trailer']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path)
    a=p.parse_args()
    print(json.dumps(geometry(Image(a.image.read_bytes())),indent=2))

if __name__=='__main__':
    main()
