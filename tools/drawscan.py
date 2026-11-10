#!/usr/bin/env python3
"""Find DrawImage (0x03063700) call sites where r0 is set to one of the given
image IDs (immediate within the preceding 12 instructions).
Usage: drawscan.py 183 184 43 44 — run from ~/workspace/fosi-dap-neo."""
import struct, json, glob, sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
man=json.load(open('extracted/manifest.json'))
want={int(a,0) for a in sys.argv[1:]}
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB|CS_MODE_MCLASS)
def bl_target(code,base,i):
    hw1,hw2=struct.unpack_from('<HH',code,i)
    if (hw1 & 0xf800)==0xf000 and (hw2 & 0xf800)==0xf800:
        s=(hw1>>10)&1; imm10=hw1&0x3ff; j1=(hw2>>13)&1; j2=(hw2>>11)&1; imm11=hw2&0x7ff
        i1=(~(j1^s))&1; i2=(~(j2^s))&1
        imm=(s<<24)|(i1<<23)|(i2<<22)|(imm10<<12)|(imm11<<1)
        if imm>=(1<<24): imm-=(1<<25)
        return base+i+4+imm
    return None
for idx in range(82):
    f=glob.glob(f'extracted/module_{idx:02d}_code_*.bin')
    if not f: continue
    code=open(f[0],'rb').read()
    m=[x for x in man['modules'] if x['index']==idx][0]
    base=m['code_exec']
    for i in range(0,len(code)-4,2):
        if bl_target(code,base,i)==0x03063700:
            start=max(0,i-48)
            r0imm=None; how=None
            for ins in md.disasm(code[start:i], base+start):
                ops=ins.op_str.replace(' ','')
                if ins.mnemonic in ('mov','movw','movs') and ops.startswith('r0,#'):
                    try: r0imm=int(ops.split('#')[1],0); how=f'@{ins.address:#x}'
                    except Exception: pass
                elif ins.mnemonic in ('add','adds','addw') and ops.startswith('r0,r0,#'):
                    try:
                        if r0imm is not None: r0imm+=int(ops.split('#')[1],0); how=f'add @{ins.address:#x}'
                    except Exception: pass
            if r0imm in want:
                print(f'mod{idx} DrawImage @{base+i:#010x} id={r0imm} (set {how})')
