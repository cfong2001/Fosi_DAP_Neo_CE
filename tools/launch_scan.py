#!/usr/bin/env python3
"""Scan all modules for (a) overlay-loader calls 0x03067870/0x0306777a with r0/r1 immediates;
(b) event-flag post 0x0306723c / wait 0x03067258 / clear 0x0306727e with r0 == 0x18b (and 0x1bd)."""
import glob, json
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
ROOT = '/home/hatch/workspace/fosi-dap-neo'
man = json.load(open(f'{ROOT}/extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}

def load(idx, kind):
    f = glob.glob(f'{ROOT}/extracted/module_{idx:02d}_{kind}_*.bin')
    return open(f[0], 'rb').read() if f else b''

LOADERS = {0x03067870: 'seg_load_03067870', 0x0306777a: 'load_0306777a'}
EVENTS = {0x0306723c: 'post', 0x03067258: 'wait/test', 0x0306727e: 'clear', 0x0306729c: 'test'}
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS); md.skipdata = True

def imm_before(insns, j, reg, window=8):
    val = None
    for k in range(max(0, j - window), j):
        p = insns[k]
        if p.mnemonic in ('movs', 'mov', 'mov.w', 'movw') and ',' in p.op_str:
            dst, src = [s.strip() for s in p.op_str.split(',', 1)]
            if dst == reg and src.startswith('#'):
                try: val = int(src[1:], 0)
                except ValueError: pass
    return val

for idx in sorted(mods):
    code = load(idx, 'code')
    if not code:
        continue
    base = mods[idx]['code_exec']
    insns = list(md.disasm(code, base))
    for j, ins in enumerate(insns):
        if ins.mnemonic not in ('bl', 'blx') or not ins.op_str.startswith('#'):
            continue
        tgt = int(ins.op_str[1:], 0)
        if tgt in LOADERS:
            r0 = imm_before(insns, j, 'r0'); r1 = imm_before(insns, j, 'r1')
            print(f"LOADER mod {idx:2d} @{ins.address:#x} -> {LOADERS[tgt]} r0={r0} r1={r1}")
        if tgt in EVENTS:
            r0 = imm_before(insns, j, 'r0')
            if r0 in (0x18b, 0x1bd, 0x1b2, 0x1b4):
                print(f"EVENT  mod {idx:2d} @{ins.address:#x} -> {EVENTS[tgt]} flag={r0:#x}")
print('done')
