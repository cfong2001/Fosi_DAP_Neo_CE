#!/usr/bin/env python3
"""Find call sites of the OS flag API where r0 is loaded with a specific flag id.
Usage: flagscan.py 0x189  — traces back up to 12 instructions before each BL to
0x0306723C(post)/0x03067258(test+clear)/0x0306727E(clear)/0x0306729C(test) and
reports sites whose r0 immediate matches the requested id.
Run from ~/workspace/fosi-dap-neo."""
import struct, json, glob, sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
man=json.load(open('extracted/manifest.json'))
FLAGFNS={0x0306723c:'post',0x03067258:'test_clear',0x0306727e:'clear',0x0306729c:'test'}
want=int(sys.argv[1],0)
def bl_target(code,base,i):
    hw1,hw2=struct.unpack_from('<HH',code,i)
    if (hw1 & 0xf800)==0xf000 and (hw2 & 0xf800)==0xf800:
        s=(hw1>>10)&1; imm10=hw1&0x3ff; j1=(hw2>>13)&1; j2=(hw2>>11)&1; imm11=hw2&0x7ff
        i1=(~(j1^s))&1; i2=(~(j2^s))&1
        imm=(s<<24)|(i1<<23)|(i2<<22)|(imm10<<12)|(imm11<<1)
        if imm>=(1<<24): imm-=(1<<25)
        return base+i+4+imm
    return None
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB|CS_MODE_MCLASS)
for idx in range(82):
    f=glob.glob(f'extracted/module_{idx:02d}_code_*.bin')
    if not f: continue
    code=open(f[0],'rb').read()
    m=[x for x in man['modules'] if x['index']==idx][0]
    base=m['code_exec']
    for i in range(0,len(code)-4,2):
        t=bl_target(code,base,i)
        if t in FLAGFNS:
            # disassemble the 32 bytes before the BL and find last r0 immediate
            start=max(0,i-40)
            r0imm=None; how=None
            for ins in md.disasm(code[start:i], base+start):
                ops=ins.op_str.replace(' ','')
                if ins.mnemonic in ('mov','movw','movs') and ops.startswith('r0,#'):
                    try: r0imm=int(ops.split('#')[1],0); how=f'{ins.mnemonic} @{ins.address:#x}'
                    except Exception: pass
                elif ins.mnemonic=='ldr' and ops.startswith('r0,[pc'):
                    try:
                        imm=int(ins.op_str.split('#')[1].rstrip(']'),0)
                        la=(ins.address+4 & ~3)+imm
                        # resolve within this module code or module0
                        val=None
                        if base<=la<base+len(code): val=struct.unpack_from('<I',code,la-base)[0]
                        if val is not None: r0imm=val; how=f'ldr lit @{ins.address:#x}'
                    except Exception: pass
            if r0imm==want:
                print(f'mod{idx} {FLAGFNS[t]} BL @{base+i:#010x}  r0=0x{want:x} via {how}')
