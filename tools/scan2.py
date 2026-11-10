#!/usr/bin/env python3
"""Generic BL-target and literal scans across all 82 modules.
Usage: scan2.py bl 0xTARGET [0xTARGET2 ...]
       scan2.py lit 0xVALUE [0xVALUE2 ...]
Run from ~/workspace/fosi-dap-neo (needs ./extracted)."""
import struct, json, glob, sys
man=json.load(open('extracted/manifest.json'))
def code_of(idx):
    f=glob.glob(f'extracted/module_{idx:02d}_code_*.bin')
    if not f: return None,None
    m=[x for x in man['modules'] if x['index']==idx][0]
    return open(f[0],'rb').read(), m['code_exec']
def bl_scan(targets):
    for idx in range(82):
        code,base=code_of(idx)
        if code is None: continue
        for i in range(0,len(code)-4,2):
            hw1,hw2=struct.unpack_from('<HH',code,i)
            if (hw1 & 0xf800)==0xf000 and (hw2 & 0xf800)==0xf800:
                s=(hw1>>10)&1; imm10=hw1&0x3ff; j1=(hw2>>13)&1; j2=(hw2>>11)&1; imm11=hw2&0x7ff
                i1=(~(j1^s))&1; i2=(~(j2^s))&1
                imm=(s<<24)|(i1<<23)|(i2<<22)|(imm10<<12)|(imm11<<1)
                if imm>=(1<<24): imm-=(1<<25)
                t=base+i+4+imm
                if t in targets: print(f'  mod{idx} BL @{base+i:#010x} -> {t:#010x}')
def lit_scan(targets):
    for idx in range(82):
        for kind in ('code','data'):
            f=glob.glob(f'extracted/module_{idx:02d}_{kind}_*.bin')
            if not f: continue
            d=open(f[0],'rb').read()
            m=[x for x in man['modules'] if x['index']==idx][0]
            b=m[kind+'_exec']
            for t in targets:
                pat=struct.pack('<I',t); i=0
                while True:
                    j=d.find(pat,i)
                    if j<0: break
                    print(f'  mod{idx} {kind} literal {t:#010x} at exec {b+j:#010x}')
                    i=j+1
if __name__=='__main__':
    mode=sys.argv[1]; targets={int(a,0) for a in sys.argv[2:]}
    if mode=='bl': bl_scan(targets)
    elif mode=='lit': lit_scan(targets)
