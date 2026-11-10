#!/usr/bin/env python3
"""Exhaustive reference scanner for DAP Neo patch justification.

Collects, across all 82 modules (code+data regions from extracted/):
  - BL and B.W branch targets (raw halfword decode)
  - literal words (any 4-byte LE value appearing anywhere in code/data)
  - MOVW/MOVT pairs to the same register within 6 halfwords (formed addrs)
Then answers, for a list of query addresses: how each is referenced.
Usage: refscan.py ADDR [ADDR...]  |  refscan.py --range LO HI (step 2)
"""
import glob, json, struct, sys, os
os.chdir(os.path.expanduser('~/workspace/fosi-dap-neo'))
man = json.load(open('extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}
regions = []  # (idx, kind, base, bytes)
for idx in range(82):
    for kind in ('code', 'data'):
        f = glob.glob(f'extracted/module_{idx:02d}_{kind}_*.bin')
        if not f: continue
        b = open(f[0], 'rb').read()
        if b: regions.append((idx, kind, mods[idx][kind + '_exec'], b))

def branch_targets():
    tgts = {}  # target -> list of (idx, site)
    for idx, kind, base, code in regions:
        if kind != 'code': continue
        for i in range(0, len(code) - 4, 2):
            hw1, hw2 = struct.unpack_from('<HH', code, i)
            if (hw1 & 0xf800) != 0xf000: continue
            cls = hw2 & 0xd000
            if cls not in (0xd000, 0x8000, 0x9000): continue
            s = (hw1 >> 10) & 1; imm10 = hw1 & 0x3ff
            j1 = (hw2 >> 13) & 1; j2 = (hw2 >> 11) & 1; imm11 = hw2 & 0x7ff
            i1 = (~(j1 ^ s)) & 1; i2 = (~(j2 ^ s)) & 1
            imm = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
            if imm & (1 << 24): imm -= (1 << 25)
            tgt = base + i + 4 + imm
            tgts.setdefault(tgt, []).append((idx, base + i))
    return tgts

def mov_pairs():
    formed = {}  # addr -> list of (idx, site)
    for idx, kind, base, code in regions:
        if kind != 'code': continue
        pending = {}  # rd -> (value_low, site)
        for i in range(0, len(code) - 4, 2):
            hw1, hw2 = struct.unpack_from('<HH', code, i)
            is_w = (hw1 & 0xfbf0) == 0xf240; is_t = (hw1 & 0xfbf0) == 0xf2c0
            if not (is_w or is_t): continue
            imm4 = (hw1 & 0xf) ; rd = (hw2 >> 8) & 0xf
            imm = (imm4 << 12) | (((hw1 >> 10) & 1) << 11) | (((hw2 >> 12) & 0x7) << 8) | (hw2 & 0xff)
            if is_w:
                pending[rd] = (imm, base + i)
            elif rd in pending:
                lo, site = pending.pop(rd)
                formed.setdefault((imm << 16) | lo, []).append((idx, site))
    return formed

def literal_hits(target):
    hits = []
    pat = struct.pack('<I', target)
    for idx, kind, base, buf in regions:
        start = 0
        while True:
            j = buf.find(pat, start)
            if j < 0: break
            hits.append((idx, kind, base + j))
            start = j + 1
    return hits

if __name__ == '__main__':
    bt = branch_targets(); mp = mov_pairs()
    if sys.argv[1] == '--range':
        lo, hi = int(sys.argv[2], 0), int(sys.argv[3], 0)
        addrs = list(range(lo, hi, 2))
    else:
        addrs = [int(x, 0) for x in sys.argv[1:]]
    for a in addrs:
        refs = []
        if a in bt: refs.append(f"BRANCH from {[(i, hex(s)) for i, s in bt[a]]}")
        if (a | 1) in bt: refs.append(f"BRANCH(thumb) from {[(i, hex(s)) for i, s in bt[a | 1]]}")
        lh = literal_hits(a) + literal_hits(a | 1)
        if lh: refs.append(f"LITERAL at {[(i, k, hex(s)) for i, k, s in lh]}")
        if a in mp: refs.append(f"MOVW/MOVT formed at {[(i, hex(s)) for i, s in mp[a]]}")
        if (a | 1) in mp: refs.append(f"MOVW/MOVT(thumb) formed at {[(i, hex(s)) for i, s in mp[a | 1]]}")
        print(f"{a:#010x}: {' ; '.join(refs) if refs else 'UNREFERENCED'}")
