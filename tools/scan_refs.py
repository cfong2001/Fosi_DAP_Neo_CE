#!/usr/bin/env python3
"""Scan all modules' code+data for u32 values in a target range (literal-pool refs)."""
import struct, glob, json, sys
ROOT = '/home/hatch/workspace/fosi-dap-neo'
man = json.load(open(f'{ROOT}/extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}
lo, hi = int(sys.argv[1], 0), int(sys.argv[2], 0)

def load(idx, kind):
    f = glob.glob(f'{ROOT}/extracted/module_{idx:02d}_{kind}_*.bin')
    return open(f[0], 'rb').read() if f else b''

for idx in sorted(mods):
    m = mods[idx]
    for kind in ('code', 'data'):
        buf = load(idx, kind)
        if not buf:
            continue
        base = m[f'{kind}_exec']
        for o in range(0, len(buf) - 3):
            v = struct.unpack_from('<I', buf, o)[0]
            if lo <= v < hi:
                print(f"mod {idx:2d} {kind}+{o:#07x} (addr {base+o:#010x}) = {v:#010x}")
