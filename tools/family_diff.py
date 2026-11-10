#!/usr/bin/env python3
"""Byte-diff the 0x0308c694 stub family (modules 41,42,50-57) and dump data."""
import json, glob
ROOT = '/home/hatch/workspace/fosi-dap-neo'
man = json.load(open(f'{ROOT}/extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}

def load(idx, kind):
    f = glob.glob(f'{ROOT}/extracted/module_{idx:02d}_{kind}_*.bin')
    return open(f[0], 'rb').read() if f else b''

fam = [41, 42, 50, 51, 52, 53, 54, 55, 56, 57]
codes = {i: load(i, 'code') for i in fam}
datas = {i: load(i, 'data') for i in fam}
for i in fam:
    m = mods[i]
    print(f"mod {i}: code_len={len(codes[i]):#x} data_exec={m['data_exec']:#x} "
          f"data_len={len(datas[i]):#x} data={datas[i].hex()} sha={__import__('hashlib').sha256(codes[i]).hexdigest()[:10]}")

ref = codes[54]
print("\nDiffs vs module 54 code:")
for i in fam:
    c = codes[i]
    if c == ref:
        print(f"  mod {i}: IDENTICAL ({len(c):#x} bytes)")
        continue
    diffs = [(o, ref[o], c[o]) for o in range(min(len(c), len(ref))) if c[o] != ref[o]]
    print(f"  mod {i}: len {len(c):#x} vs {len(ref):#x}; {len(diffs)} byte diffs in common range:")
    for o, a, b in diffs[:40]:
        print(f"    off {o:#06x} (addr {0x0308c694+o:#010x}): mod54={a:#04x} mod{i}={b:#04x}")
    if len(c) != len(ref):
        tail = c[len(ref):] if len(c) > len(ref) else ref[len(c):]
        print(f"    length tail ({abs(len(c)-len(ref)):#x} bytes) nonzero={any(tail)}")
