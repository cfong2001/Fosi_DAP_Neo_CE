#!/usr/bin/env python3
"""List call sites of given targets in a module, with the preceding mov-immediate context.
Usage: callsites.py MODULE TARGET [TARGET...]"""
import sys, json, glob, os
os.chdir(os.path.expanduser('~/workspace/fosi-dap-neo'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
man = json.load(open('extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}
idx = int(sys.argv[1]); targets = {int(x, 0) for x in sys.argv[2:]}
m = mods[idx]
code = open(glob.glob(f'extracted/module_{idx:02d}_code_*.bin')[0], 'rb').read()
base = m['code_exec']
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
insns = list(md.disasm(code, base))
for i, ins in enumerate(insns):
    if ins.mnemonic in ('bl', 'blx') and ins.op_str.startswith('#'):
        try: t = int(ins.op_str[1:], 0)
        except Exception: continue
        if t in targets:
            ctx = []
            for p in insns[max(0, i-6):i]:
                if p.mnemonic.startswith('mov') or p.mnemonic.startswith('ldr'):
                    ctx.append(f'{p.mnemonic} {p.op_str}')
            print(f'{ins.address:#010x} bl {t:#x}   ctx: {"; ".join(ctx)}')
