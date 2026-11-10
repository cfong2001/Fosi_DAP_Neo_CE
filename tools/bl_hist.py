#!/usr/bin/env python3
"""BL/BLX target histogram + literal refs for a module; also dump data head."""
import struct, glob, json, sys
from collections import Counter
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
ROOT = '/home/hatch/workspace/fosi-dap-neo'
man = json.load(open(f'{ROOT}/extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}

def load(idx, kind):
    f = glob.glob(f'{ROOT}/extracted/module_{idx:02d}_{kind}_*.bin')
    return open(f[0], 'rb').read() if f else b''

for idx in [int(x) for x in sys.argv[1:]]:
    m = mods[idx]
    code = load(idx, 'code'); base = m['code_exec']
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS); md.skipdata = True
    bls = Counter(); lits = Counter()
    for ins in md.disasm(code, base):
        if ins.mnemonic in ('bl', 'blx') and ins.op_str.startswith('#'):
            bls[int(ins.op_str[1:], 0)] += 1
        if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
            try:
                imm = int(ins.op_str.split('#')[1].rstrip(']'), 0)
                la = (ins.address + 4 & ~3) + imm
                for buf, b in ((code, base), (load(idx, 'data'), m['data_exec']),
                               (load(0, 'code'), mods[0]['code_exec']), (load(0, 'data'), mods[0]['data_exec'])):
                    if b <= la < b + len(buf):
                        lits[struct.unpack_from('<I', buf, la - b)[0]] += 1
                        break
            except Exception:
                pass
    print(f"== module {idx} BL targets: " + ', '.join(f'{a:#x}x{c}' for a, c in bls.most_common(18)))
    print(f"   literals: " + ', '.join(f'{a:#x}x{c}' for a, c in lits.most_common(18)))
