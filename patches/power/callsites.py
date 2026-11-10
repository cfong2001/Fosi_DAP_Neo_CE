#!/usr/bin/env python3
"""Find BL/BLX call sites to a target address across module code bins.
Usage: callsites.py TARGET_HEX [MODULE ...] (default: all modules)"""
import sys, json, glob
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS

man = json.load(open('extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}

def load(idx, kind):
    f = glob.glob(f'extracted/module_{idx:02d}_{kind}_*.bin')
    return open(f[0], 'rb').read() if f else b''

target = int(sys.argv[1], 0)
sel = [int(x) for x in sys.argv[2:]] or sorted(mods)
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.skipdata = True
for idx in sel:
    m = mods[idx]
    code = load(idx, 'code')
    base = m['code_exec']
    for ins in md.disasm(code, base):
        if ins.mnemonic in ('bl', 'blx') and ins.op_str.startswith('#'):
            try:
                t = int(ins.op_str[1:], 0)
            except ValueError:
                continue
            if t == target or t == target - 1:
                print(f'mod{idx:02d} {ins.address:#010x}: {ins.mnemonic} {ins.op_str}')
