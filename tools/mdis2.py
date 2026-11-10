#!/usr/bin/env python3
"""mdis with skipdata + module-0 literal fallback (robust variant of stage/tools/mdis.py).
Usage: mdis2.py MODULE_INDEX START_ADDR LENGTH"""
import sys, struct, json, glob, os
os.chdir(os.path.expanduser('~/workspace/fosi-dap-neo'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
man = json.load(open('extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}
idx = int(sys.argv[1]); start = int(sys.argv[2], 0); length = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x100
m = mods[idx]
def load(i, kind):
    f = glob.glob(f'extracted/module_{i:02d}_{kind}_*.bin')
    return open(f[0], 'rb').read() if f else b''
code = load(idx, 'code'); base = m['code_exec']
data = load(idx, 'data'); dbase = m['data_exec']
def read(addr, n):
    for (buf, b) in ((code, base), (data, dbase), (load(0, 'code'), mods[0]['code_exec']), (load(0, 'data'), mods[0]['data_exec'])):
        if b <= addr < b + len(buf): return buf[addr-b:addr-b+n]
    return None
off = start - base
chunk = code[off:off+length]
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.skipdata = True
for ins in md.disasm(chunk, start):
    note = ''
    if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
        try:
            imm = int(ins.op_str.split('#')[1].rstrip(']'), 0)
            la = (ins.address + 4 & ~3) + imm
            v = read(la, 4)
            if v: note = f'  ; [{la:#x}] = {struct.unpack("<I", v)[0]:#010x}'
        except Exception: pass
    print(f'{ins.address:08x}  {ins.bytes.hex(" "):<14} {ins.mnemonic:<8} {ins.op_str}{note}')
