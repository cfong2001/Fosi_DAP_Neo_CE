#!/usr/bin/env python3
"""Find code references (LDR literal / ADR / movw) to given addresses within one module's code.
Usage: adrscan.py MODULE_INDEX TARGET [TARGET...]"""
import sys, struct, json, glob, os
os.chdir(os.path.expanduser('~/workspace/fosi-dap-neo'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
man = json.load(open('extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}
idx = int(sys.argv[1]); targets = {int(x, 0) for x in sys.argv[2:]}
m = mods[idx]
code = open(glob.glob(f'extracted/module_{idx:02d}_code_*.bin')[0], 'rb').read()
base = m['code_exec']
data = b''
df = glob.glob(f'extracted/module_{idx:02d}_data_*.bin')
if df: data = open(df[0], 'rb').read()
dbase = m['data_exec']
def read(addr, n):
    for buf, b in ((code, base), (data, dbase)):
        if b <= addr < b + len(buf): return buf[addr-b:addr-b+n]
    return None
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.detail = False
for ins in md.disasm(code, base):
    hit = None
    if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
        try:
            imm = int(ins.op_str.split('#')[1].rstrip(']'), 0)
            la = (ins.address + 4 & ~3) + imm
            v = read(la, 4)
            if v and struct.unpack('<I', v)[0] in targets: hit = struct.unpack('<I', v)[0]
        except Exception: pass
    elif ins.mnemonic in ('adr',):
        try:
            imm = int(ins.op_str.split('#')[1], 0)
            t = (ins.address + 4 & ~3) + imm
            if t in targets: hit = t
        except Exception: pass
    if hit is not None:
        print(f'{ins.address:#010x}  {ins.mnemonic} {ins.op_str}  -> {hit:#x}')
