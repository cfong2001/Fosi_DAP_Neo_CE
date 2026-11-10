#!/usr/bin/env python3
"""Find module 33's pointer table into the 0x0308c694 window + nonzero data islands."""
import struct, glob, json
ROOT = '/home/hatch/workspace/fosi-dap-neo'
data = open(glob.glob(f'{ROOT}/extracted/module_33_data_*.bin')[0], 'rb').read()
DBASE = 0x030368c8
print(f"module33 data len {len(data):#x}")
# all u32 in stub window
hits = []
for o in range(0, len(data) - 3, 4):
    v = struct.unpack_from('<I', data, o)[0]
    if 0x0308c694 <= v < 0x0308c980:
        hits.append((o, v))
print(f"{len(hits)} u32 pointers into stub window:")
# compress runs
prev = None
for o, v in hits:
    print(f"  data+{o:#07x} (addr {DBASE+o:#010x}) = {v:#010x}  (stub+{v-0x0308c694:#x})")
# nonzero islands
print("\nnonzero islands in module33 data:")
o = 0
while o < len(data):
    if data[o] != 0:
        s = o
        while o < len(data) and (data[o] != 0 or (o + 16 < len(data) and any(data[o:o+16]))):
            o += 1
        print(f"  data+{s:#x}..{o:#x} (addr {DBASE+s:#x}) len {o-s:#x}")
    else:
        o += 1
