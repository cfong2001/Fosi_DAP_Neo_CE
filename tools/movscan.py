#!/usr/bin/env python3
"""Scan a module for movw/movt immediates that build given high halves (e.g. 0x0100/0x0102).
Usage: movscan.py MODULE HI [HI...]  (hex high-half values)"""
import sys, json, glob, os
os.chdir(os.path.expanduser('~/workspace/fosi-dap-neo'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
man = json.load(open('extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}
idx = int(sys.argv[1]); his = {int(x, 0) for x in sys.argv[2:]}
m = mods[idx]
code = open(glob.glob(f'extracted/module_{idx:02d}_code_*.bin')[0], 'rb').read()
base = m['code_exec']
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.skipdata = True
for ins in md.disasm(code, base):
    if ins.mnemonic in ('movt', 'movw'):
        try:
            imm = int(ins.op_str.split('#')[1], 0)
        except Exception:
            continue
        if ins.mnemonic == 'movt' and imm in his:
            print(f'{ins.address:#010x}  {ins.mnemonic} {ins.op_str}')
