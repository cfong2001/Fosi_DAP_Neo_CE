#!/usr/bin/env python3
"""BT hunt: (a) GPIO helper calls with (port,pin) args across all modules;
(b) UART-base / 0x401x0000 literals; (c) any module referencing GPIO2.7 or pins 16/17 on port 2."""
import struct, glob, json
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
ROOT = '/home/hatch/workspace/fosi-dap-neo'
man = json.load(open(f'{ROOT}/extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}
GPIO_HELPERS = {0x030526f8: 'mux', 0x03056098: 'dir', 0x030560d2: 'level', 0x030560f2: 'read'}

def load(idx, kind):
    f = glob.glob(f'{ROOT}/extracted/module_{idx:02d}_{kind}_*.bin')
    return open(f[0], 'rb').read() if f else b''

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS); md.skipdata = True
for idx in sorted(mods):
    m = mods[idx]
    code = load(idx, 'code')
    if not code:
        continue
    base = m['code_exec']
    insns = list(md.disasm(code, base))
    hits = []
    for j, ins in enumerate(insns):
        if ins.mnemonic in ('bl', 'blx') and ins.op_str.startswith('#'):
            tgt = int(ins.op_str[1:], 0)
            if tgt in GPIO_HELPERS:
                r0 = r1 = None
                for k in range(max(0, j - 6), j):
                    p = insns[k]
                    if p.mnemonic in ('movs', 'mov', 'mov.w') and ',' in p.op_str:
                        dst, src = [s.strip() for s in p.op_str.split(',', 1)]
                        if src.startswith('#'):
                            try:
                                v = int(src[1:], 0)
                            except ValueError:
                                continue
                            if dst == 'r0': r0 = v
                            elif dst == 'r1': r1 = v
                hits.append((ins.address, GPIO_HELPERS[tgt], r0, r1))
    interesting = [h for h in hits if h[2] == 2 and h[3] in (7, 16, 17)]
    if interesting:
        print(f"mod {idx}: " + ', '.join(f'{a:#x} {f}({p},{pin})' for a, f, p, pin in interesting))
    # literal scan for UART-ish bases in code+data
    for kind in ('code', 'data'):
        buf = load(idx, kind)
        if not buf:
            continue
        b = m[f'{kind}_exec']
        for o in range(0, len(buf) - 3):
            v = struct.unpack_from('<I', buf, o)[0]
            if v in (0x40160000, 0x40170000, 0x60060000, 0x60070000, 0x40150000, 0x40130000, 0x40140000):
                print(f"mod {idx} {kind}+{o:#x} (addr {b+o:#x}) literal {v:#x}")
print("done")
