#!/usr/bin/env python3
"""Detail-operand register tracker over one module's code bin.
Seeds from literal-pool loads and movw/movt pairs; propagates mov/add/sub;
reports every memory access with computed EA inside [LO,HI).
Usage: scan2.py MODULE LO HI [WINDOW]"""
import struct, json, glob, sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from capstone.arm import ARM_OP_REG, ARM_OP_IMM, ARM_OP_MEM
man=json.load(open('extracted/manifest.json'))
mods={m['index']:m for m in man['modules']}
idx=int(sys.argv[1]); LO=int(sys.argv[2],0); HI=int(sys.argv[3],0)
WIN=int(sys.argv[4]) if len(sys.argv)>4 else 800
def load(i,kind):
    f=glob.glob(f'extracted/module_{i:02d}_{kind}_*.bin')
    return (open(f[0],'rb').read(), mods[i][kind+'_exec']) if f else (b'',0)
code,base=load(idx,'code')
def read32(addr):
    for i in (idx,0):
        for kind in ('code','data'):
            buf,b=load(i,kind)
            if b<=addr<b+len(buf): return struct.unpack_from('<I',buf,addr-b)[0]
    return None
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB|CS_MODE_MCLASS); md.detail=True
insns=list(md.disasm(code,base))
PC=md.reg_name(15) if False else 'pc'
def rn(op): return ins_reg(op)
def ins_reg(op): return op.reg
# use md.reg_name via a live insn context: capstone gives reg ids; convert with ins.reg_name(op.reg) at use sites
out=[]
for j,ins in enumerate(insns):
    seeds={}
    ops=ins.operands
    if ins.mnemonic.startswith('ldr') and len(ops)>=2 and ops[1].type==ARM_OP_MEM and ins.reg_name(ops[1].mem.base)=='pc':
        la=(ins.address+4 & ~3)+ops[1].mem.disp
        v=read32(la)
        if v is not None and LO-0x1000<=v<HI+0x1000:
            seeds[ins.reg_name(ops[0].reg)]=v
    if ins.mnemonic=='movw' and len(ops)>=2 and ops[1].type==ARM_OP_IMM:
        # look ahead for movt same reg within 3 insns
        for k in range(j+1,min(j+4,len(insns))):
            n=insns[k]
            if n.mnemonic=='movt' and n.operands and ins.reg_name(n.operands[0].reg)==ins.reg_name(ops[0].reg) and n.operands[1].type==ARM_OP_IMM:
                v=(n.operands[1].imm<<16)|ops[1].imm
                if LO-0x1000<=v<HI+0x1000: seeds[ins.reg_name(ops[0].reg)]=v
    if not seeds: continue
    for dst,v0 in list(seeds.items()):
        vals={dst:v0}
        srcimm={}
        for k in range(j+1,min(j+1+WIN,len(insns))):
            n=insns[k]; nops=n.operands
            # report memory accesses
            for op in nops:
                if op.type==ARM_OP_MEM and op.mem.base:
                    breg=n.reg_name(op.mem.base)
                    if breg in vals:
                        ea=vals[breg]+op.mem.disp
                        if LO<=ea<HI:
                            w='WRITE' if n.mnemonic.startswith(('str','stm')) else 'read'
                            extra=''
                            if w=='WRITE' and nops and nops[0].type==ARM_OP_REG:
                                sr=n.reg_name(nops[0].reg)
                                if sr in srcimm: extra=f' stored-imm={srcimm[sr]:#x}'
                            out.append(f'@{n.address:#x} {w} EA={ea:#x} (off {ea-LO:+#x}) :: {n.mnemonic} {n.op_str} [seed {dst}={v0:#x} @{ins.address:#x}]{extra}')
            if not nops or nops[0].type!=ARM_OP_REG: continue
            d=n.reg_name(nops[0].reg)
            bm=n.mnemonic.split('.')[0]
            for cc in ('eq','ne','hs','lo','mi','pl','vs','vc','hi','ls','ge','lt','gt','le'):
                if bm.endswith(cc): bm=bm[:-2]; break
            if bm in ('mov','movs') and len(nops)>=2 and nops[1].type==ARM_OP_REG and n.reg_name(nops[1].reg) in vals:
                vals[d]=vals[n.reg_name(nops[1].reg)]
            elif bm in ('add','adds','sub','subs') and len(nops)>=3 and nops[1].type==ARM_OP_REG and n.reg_name(nops[1].reg) in vals and nops[2].type==ARM_OP_IMM:
                vals[d]=vals[n.reg_name(nops[1].reg)] + (nops[2].imm if bm.startswith('add') else -nops[2].imm)
            elif bm in ('mov','movs','movw') and len(nops)>=2 and nops[1].type==ARM_OP_IMM:
                srcimm[d]=nops[1].imm
                if d in vals: del vals[d]
            elif d in vals and bm not in ('cmp','cmn','tst','str','strb','strh','strd','stm','push','nop'):
                del vals[d]
seen=set()
for line in out:
    if line not in seen:
        seen.add(line); print(line)
