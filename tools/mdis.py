#!/usr/bin/env python3
"""Per-module Thumb-2 disassembler: disasm a specific module's code at a given exec address.
Usage: mdis.py MODULE_INDEX START_ADDR LENGTH"""
import sys, struct, json
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
man=json.load(open('extracted/manifest.json'))  # produced by: tools/rknano_image.py DP3_V137.img unpack extracted
mods={m['index']:m for m in man['modules']}
import glob
def load(idx,kind):
    f=glob.glob(f'extracted/module_{idx:02d}_{kind}_*.bin')
    return open(f[0],'rb').read() if f else b''
def main():
    idx=int(sys.argv[1]); start=int(sys.argv[2],0); length=int(sys.argv[3],0) if len(sys.argv)>3 else 0x100
    m=mods[idx]; code=load(idx,'code'); base=m['code_exec']
    data=load(idx,'data'); dbase=m['data_exec']
    # also module 0 code/data for literal resolution across resident image
    def read(addr,n):
        for (buf,b) in ((code,base),(data,dbase)):
            if b<=addr<b+len(buf): return buf[addr-b:addr-b+n]
        m0=mods[0]
        for (buf,b) in ((load(0,'code'),m0['code_exec']),(load(0,'data'),m0['data_exec'])):
            if b<=addr<b+len(buf): return buf[addr-b:addr-b+n]
        return None
    off=start-base
    chunk=code[off:off+length]
    md=Cs(CS_ARCH_ARM, CS_MODE_THUMB|CS_MODE_MCLASS)
    for ins in md.disasm(chunk, start):
        note=''
        if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
            try:
                imm=int(ins.op_str.split('#')[1].rstrip(']'),0)
                litaddr=(ins.address+4 & ~3)+imm
                val=read(litaddr,4)
                if val: note=f'  ; [{litaddr:#x}] = {struct.unpack("<I",val)[0]:#010x}'
            except Exception: pass
        print(f'{ins.address:08x}  {ins.bytes.hex(" "):<14} {ins.mnemonic:<8} {ins.op_str}{note}')
if __name__=='__main__': main()
