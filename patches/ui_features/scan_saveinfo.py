#!/usr/bin/env python3
"""Sliding-window register-value tracker: report every memory access whose
effective address falls in [LO,HI), for one module's code bin.
Tracks: ldr reg,[pc,#imm] literal loads; movw/movt/mov reg,#imm;
add/sub reg, reg, #imm (reg derived from a tracked value).
Invalidates a register when it is written by anything else."""
import struct, json, glob, sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
man=json.load(open('extracted/manifest.json'))
mods={m['index']:m for m in man['modules']}
LO,HI=0x030232A0,0x030232A0+0x300
def load(idx,kind):
    f=glob.glob(f'extracted/module_{idx:02d}_{kind}_*.bin')
    return (open(f[0],'rb').read(), mods[idx][kind+'_exec']) if f else (b'',0)
def read32(idx,addr):
    for kind in ('code','data'):
        buf,b=load(idx,kind)
        if b<=addr<b+len(buf): return struct.unpack_from('<I',buf,addr-b)[0]
    buf,b=load(0,'code')
    if b<=addr<b+len(buf): return struct.unpack_from('<I',buf,addr-b)[0]
    buf,b=load(0,'data')
    if b<=addr<b+len(buf): return struct.unpack_from('<I',buf,addr-b)[0]
    return None
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB|CS_MODE_MCLASS); md.detail=True
idx=int(sys.argv[1]) if len(sys.argv)>1 else 0
code,base=load(idx,'code')
insns=list(md.disasm(code,base))
def regname(op):
    return ins.reg_name(op.reg) if op and op.type==1 else None
for j,ins in enumerate(insns):
    # seed: does this insn load a tracked constant into a reg?
    vals={}
    seeds=[]
    if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
        try:
            dst=ins.op_str.split(',')[0].strip()
            imm=int(ins.op_str.split('#')[1].rstrip(']').split()[0],0)
            la=(ins.address+4 & ~3)+imm
            v=read32(idx,la)
            if v is not None and LO-0x400 <= v < HI+0x400:
                seeds.append((dst,v))
        except Exception: pass
    if ins.mnemonic in ('movw','movt','mov','movs') and '#' in ins.op_str:
        try:
            dst=ins.op_str.split(',')[0].strip()
            v=int(ins.op_str.split('#')[1],0)
            if LO-0x400 <= v < HI+0x400: seeds.append((dst,v))
        except Exception: pass
    for dst,v0 in seeds:
        vals={dst:v0}
        for k in range(j+1,min(j+80,len(insns))):
            n=insns[k]
            ops=n.operands
            # memory access through tracked reg?
            for op in ops:
                if op.type==3:  # mem
                    breg=ins.reg_name(op.mem.base) if op.mem.base else None
                    if breg in vals:
                        ea=vals[breg]+op.mem.disp
                        if LO<=ea<HI:
                            kind='WRITE' if n.mnemonic.startswith(('str','stmd','stm')) else 'read'
                            print(f'mod{idx} @{n.address:#x} {kind} SAVEINFO+{ea-LO:#x} :: {n.mnemonic} {n.op_str}   (seed {dst}={v0:#x} @{ins.address:#x})')
            # track propagation / invalidation
            if ops and ops[0].type==1:
                d=ins.reg_name(ops[0].reg)
                if n.mnemonic in ('add','adds','sub','subs') and len(ops)>=3 and ops[1].type==1 and ins.reg_name(ops[1].reg) in vals and ops[2].type==2:
                    vals[d]=vals[ins.reg_name(ops[1].reg)] + (ops[2].imm if n.mnemonic.startswith('add') else -ops[2].imm)
                elif d in vals and n.mnemonic not in ('cmp','cmn','tst','str','strb','strh','push'):
                    if not (n.mnemonic.startswith('ldr') and '[pc' in n.op_str):
                        del vals[d]
            if n.mnemonic in ('bl','blx') and 'lr' in str(n.op_str):
                pass
        # end window
