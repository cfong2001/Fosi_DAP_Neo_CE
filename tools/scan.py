#!/usr/bin/env python3
"""BL-target and literal scans across all 82 modules.
Expects ./extracted/ (from tools/rknano_image.py unpack) in the CWD."""
import struct, json, glob, sys
man=json.load(open('extracted/manifest.json'))
def code_of(idx):
    f=glob.glob(f'extracted/module_{idx:02d}_code_*.bin')
    if not f: return None,None
    m=[x for x in man['modules'] if x['index']==idx][0]
    return open(f[0],'rb').read(), m['code_exec']
def bl_scan(idx, targets):
    code,base=code_of(idx)
    if code is None: return
    for i in range(0,len(code)-4,2):
        hw1,hw2=struct.unpack_from('<HH',code,i)
        if (hw1 & 0xf800)==0xf000 and (hw2 & 0xf800)==0xf800:
            s=(hw1>>10)&1; imm10=hw1&0x3ff; j1=(hw2>>13)&1; j2=(hw2>>11)&1; imm11=hw2&0x7ff
            i1=(~(j1^s))&1; i2=(~(j2^s))&1
            imm=(s<<24)|(i1<<23)|(i2<<22)|(imm10<<12)|(imm11<<1)
            if imm>=(1<<24): imm-=(1<<25)
            t=base+i+4+imm
            if t in targets: print(f'  mod{idx} BL @{base+i:#x} -> {t:#x} ({targets[t]})')
def lit_scan(idx, targets):
    # find literal words equal to target anywhere in code+data
    for kind in ('code','data'):
        f=glob.glob(f'extracted/module_{idx:02d}_{kind}_*.bin')
        if not f: continue
        d=open(f[0],'rb').read()
        m=[x for x in man['modules'] if x['index']==idx][0]
        b=m[kind+'_exec']
        for t,name in targets.items():
            pat=struct.pack('<I',t); i=0
            while True:
                j=d.find(pat,i)
                if j<0: break
                print(f'  mod{idx} {kind} literal {name} {t:#x} at {b+j:#x}')
                i=j+1
print('== BL callers of codec-open 89e2e / 890ae / 89ad6 / 8875a / 89c86 dispatcher ==')
tg={0x03089e2e:'codec_open(89e2e)',0x030890ae:'FUN890ae',0x03089ad6:'FUN89ad6',0x0308875a:'FUN8875a(time print)',0x03089c86:'mod33 dispatcher',0x03051a46:'DAC_start'}
for i in range(82): bl_scan(i,tg)
print('== literal refs to DAC flag 03023125 / 03023151 / state 03023922 / 0302392c ==')
tg2={0x03023125:'DAC_on_flag',0x03023151:'flag_3151',0x03023922:'dec_state_3922',0x0302392c:'pos_392c',0x03023930:'pos_3930',0x0302314c:'flag_314c'}
for i in range(82): lit_scan(i,tg2)
