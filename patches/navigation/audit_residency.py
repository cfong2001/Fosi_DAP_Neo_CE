#!/usr/bin/env python3
"""Inventory module ranges intersecting proposed navigation stubs.

All ranges are half-open execution addresses from the pinned stock
image. This is an address census, not a runtime scheduling proof.
"""
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image

raw = (ROOT / 'DP3_V137.img').read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
im = Image(raw)

# Module 24 grows by 26 bytes; module 31 already grows by 7,168 bytes
# for its composed bridge before the 68-byte candidate is appended.
regions = [('module 24 candidate', 0x0307edec, 0x0307ee06),
           ('module 31 candidate', 0x03080a48, 0x03080a8c)]
for label, start, end in regions:
    print(f'{label}: {start:#010x}..{end:#010x} (end exclusive)')
    overlaps = []
    for m in im.modules:
        for kind in ('code', 'data', 'bss'):
            lo, length = m[kind + '_exec'], m[kind + '_len']
            if length and lo < end and start < lo + length:
                overlaps.append((m['index'], kind))
                print(f"  module {m['index']:02d} {kind}: {lo:#010x}..{lo+length:#010x}")
    # Known relevant resident/service segments must stay disjoint. The
    # remaining overlapping windows are not assumed mutually exclusive
    # merely because their addresses overlap.
    for concurrent in (0, 18, 19, 20, 23, 24, 25, 26, 33):
        assert all(index != concurrent for index, kind in overlaps), (label, concurrent)
    print('  Modules 0, 18–20, 23–26 and 33: no overlap')

assert im.modules[24]['code_exec'] + im.modules[24]['code_len'] == regions[0][1]
assert im.modules[31]['code_exec'] + im.modules[31]['code_len'] + 7168 == regions[1][1]
print('PASS: extents match the candidate build geometry; runtime overlay sequencing remains unverified')
