#!/usr/bin/env python3
"""BL-scan all modules for targets inside an address range.
Usage: blrange.py LO HI"""
import struct, json, glob, sys, os
os.chdir(os.path.expanduser('~/workspace/fosi-dap-neo'))
man = json.load(open('extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}
lo, hi = int(sys.argv[1], 0), int(sys.argv[2], 0)
from collections import Counter
cnt = Counter()
for idx in range(82):
    f = glob.glob(f'extracted/module_{idx:02d}_code_*.bin')
    if not f: continue
    code = open(f[0], 'rb').read(); base = mods[idx]['code_exec']
    for i in range(0, len(code) - 4, 2):
        hw1, hw2 = struct.unpack_from('<HH', code, i)
        if (hw1 & 0xf800) == 0xf000 and (hw2 & 0xf800) == 0xf800:
            s = (hw1 >> 10) & 1; imm10 = hw1 & 0x3ff; j1 = (hw2 >> 13) & 1; j2 = (hw2 >> 11) & 1; imm11 = hw2 & 0x7ff
            i1 = (~(j1 ^ s)) & 1; i2 = (~(j2 ^ s)) & 1
            imm = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
            if imm >= (1 << 24): imm -= (1 << 25)
            t = base + i + 4 + imm
            if lo <= t < hi:
                cnt[t] += 1
                print(f'  mod{idx:02d} BL @{base+i:#010x} -> {t:#010x}')
print('summary:', {hex(k): v for k, v in sorted(cnt.items())})
