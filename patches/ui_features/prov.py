#!/usr/bin/env python3
"""For a given module+address of a strb, walk backwards up to N insns and
report the last writer of the stored register."""
import json, glob, sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from capstone.arm import ARM_OP_REG, ARM_OP_IMM, ARM_OP_MEM
man=json.load(open('extracted/manifest.json'))
mods={m['index']:m for m in man['modules']}
def load(i,kind):
    f=glob.glob(f'extracted/module_{i:02d}_{kind}_*.bin')
    return (open(f[0],'rb').read(), mods[i][kind+'_exec']) if f else (b'',0)
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB|CS_MODE_MCLASS); md.detail=True
sites=[(12,0x0307f0b8),(21,0x0307d45a),(21,0x0307d49a),(24,0x0307e9fc),(24,0x0307ea72),(25,0x0307ea9a),(25,0x0307eac6),(27,0x0307e17a),(32,0x0307daa2)]
for idx,addr in sites:
    code,base=load(idx,'code')
    insns=list(md.disasm(code,base))
    pos=[k for k,i in enumerate(insns) if i.address==addr]
    if not pos: print(f'mod{idx} @{addr:#x}: not found'); continue
    j=pos[0]; ins=insns[j]
    sr=ins.reg_name(ins.operands[0].reg)
    print(f'mod{idx} @{addr:#x}: {ins.mnemonic} {ins.op_str}  (stored reg {sr})')
    found=False
    for k in range(j-1,max(0,j-500),-1):
        n=insns[k]
        if n.operands and n.operands[0].type==ARM_OP_REG and n.reg_name(n.operands[0].reg)==sr and not n.mnemonic.startswith(('str','cmp','push')):
            print(f'    last write to {sr}: @{n.address:#x} {n.mnemonic} {n.op_str}')
            found=True; break
        if n.mnemonic.startswith('push'):
            print(f'    reaches prologue @{n.address:#x} {n.mnemonic} {n.op_str} with no write found')
            found=True; break
    if not found: print('    no writer within 500 insns')
