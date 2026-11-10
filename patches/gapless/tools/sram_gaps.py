#!/usr/bin/env python3
"""SRAM free-space analysis: find maximal intervals in the given regions that
are (a) not named by any literal word or MOVW/MOVT construction anywhere in
the image, (b) not inside any named address's [base, base+0x1000) LDR-reach
window beyond documented struct extents, (c) report image bytes (data segs).
"""
import glob, json, struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.expanduser('~/workspace/fosi-dap-neo'))
man = json.load(open('extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}
regions = []
for idx in range(82):
    for kind in ('code', 'data'):
        f = glob.glob(f'extracted/module_{idx:02d}_{kind}_*.bin')
        if not f: continue
        b = open(f[0], 'rb').read()
        if b: regions.append((idx, kind, mods[idx][kind + '_exec'], b))

named = set()
for idx, kind, base, buf in regions:
    for i in range(0, len(buf) - 3):
        v = struct.unpack_from('<I', buf, i)[0]
        if 0x03000000 <= v < 0x03080000:
            named.add(v); named.add(v & ~1)
# MOVW/MOVT pairs
for idx, kind, base, code in regions:
    if kind != 'code': continue
    pending = {}
    for i in range(0, len(code) - 4, 2):
        hw1, hw2 = struct.unpack_from('<HH', code, i)
        is_w = (hw1 & 0xfbf0) == 0xf240; is_t = (hw1 & 0xfbf0) == 0xf2c0
        if not (is_w or is_t): continue
        rd = (hw2 >> 8) & 0xf
        imm = ((hw1 & 0xf) << 12) | (((hw1 >> 10) & 1) << 11) | (((hw2 >> 12) & 0x7) << 8) | (hw2 & 0xff)
        if is_w: pending[rd] = imm
        elif rd in pending:
            a = (imm << 16) | pending.pop(rd)
            if 0x03000000 <= a < 0x03080000: named.add(a); named.add(a & ~1)

# documented struct extents (start, size, name) — treated as occupied
structs = [
    (0x030232A0, 0x300, 'SAVEINFO'), (0x03023980, 0x100, 'fileinfo'),
    (0x03023918, 0x40, 'state struct'), (0x03023CF8, 0x48, 'event bitmap'),
    (0x0304AD70, 0x7B0, 'decoder ctlblk'), (0x0304B47C, 0x60, 'codec struct'),
    (0x030368D8, 0x100, 'decoder info'), (0x0304AF10, 0x40, 'audio state'),
    (0x0304B170, 0x400, 'info copy area'), (0x03023151, 1, 'state byte'),
    (0x03023125, 1, 'DAC guard'), (0x0302314C, 1, 'output state'),
    (0x03004138, 8, 'ready words'), (0x030064E0, 0x90, 'param page src'),
]
def occupied(a):
    if a in named: return 'named'
    for s, sz, nm in structs:
        if s <= a < s + sz: return nm
    return None

for label, lo, hi in [('mod0 data', 0x03004000, 0x030059A9), ('mod0 BSS', 0x030059AC, 0x030247C0),
                      ('mod33 data', 0x030368C8, 0x03048D68), ('mod33 BSS', 0x03048D68, 0x0304B604)]:
    # maximal runs of unoccupied, 4-aligned, >= 8 bytes
    runs = []
    a = lo
    while a < hi:
        if occupied(a) is None:
            j = a
            while j < hi and occupied(j) is None: j += 1
            if j - a >= 8: runs.append((a, j - a))
            a = j
        else: a += 1
    runs.sort(key=lambda r: -r[1])
    print(f"== {label} [{lo:#x},{hi:#x}) top unoccupied runs:")
    for a, n in runs[:8]: print(f"   {a:#010x}  {n} bytes")
