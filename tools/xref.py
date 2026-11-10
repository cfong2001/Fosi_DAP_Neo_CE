#!/usr/bin/env python3
"""Register-tracked xrefs: find where a register is loaded with one of the
target addresses (literal pool) and what memory accesses [reg, #off] follow
within the next N instructions (until the register is redefined).
Usage: xref.py 0xADDR [0xADDR2 ...] [--window 16]
Run from ~/workspace/fosi-dap-neo."""
import struct, json, glob, sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
man=json.load(open('extracted/manifest.json'))
args=[a for a in sys.argv[1:] if not a.startswith('--')]
targets={int(a,0) for a in args}
window=16
if '--window' in sys.argv: window=int(sys.argv[sys.argv.index('--window')+1])
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB|CS_MODE_MCLASS)
md.detail=False
def seg(idx,kind):
    f=glob.glob(f'extracted/module_{idx:02d}_{kind}_*.bin')
    if not f: return None,None
    m=[x for x in man['modules'] if x['index']==idx][0]
    return open(f[0],'rb').read(), m[kind+'_exec']
for idx in range(82):
    code,base=seg(idx,'code')
    if code is None: continue
    data,dbase=seg(idx,'data')
    m0c,m0b=seg(0,'code'); m0d,m0db=seg(0,'data')
    def read32(addr):
        for buf,b in ((code,base),(data,dbase),(m0c,m0b),(m0d,m0db)):
            if buf is not None and b<=addr<b+len(buf):
                return struct.unpack_from('<I',buf,addr-b)[0]
        return None
    insns=list(md.disasm(code, base))
    for j,ins in enumerate(insns):
        if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
            try:
                reg=ins.op_str.split(',')[0].strip()
                imm=int(ins.op_str.split('#')[1].rstrip(']'),0)
                la=(ins.address+4 & ~3)+imm
                val=read32(la)
            except Exception:
                continue
            if val in targets:
                uses=[]
                for k in range(j+1, min(j+1+window, len(insns))):
                    n=insns[k]
                    if f'{reg},' in n.op_str.split('[')[0] and n.mnemonic.startswith(('mov','ldr','str','add','sub')) and ('[' not in n.op_str or not n.op_str.startswith(reg)):
                        # reg redefined (as destination) — stop unless it's an add/sub on itself
                        if n.mnemonic in ('mov','movw','movs','ldr') :
                            break
                    if f'[{reg}' in n.op_str or f'[{reg},' in n.op_str or n.op_str.endswith(f', {reg}') is False and f' {reg}]' in n.op_str:
                        uses.append(f'{n.address:#x}: {n.mnemonic} {n.op_str}')
                    if n.mnemonic.startswith('str') and f', {reg}' in n.op_str:
                        uses.append(f'{n.address:#x}: {n.mnemonic} {n.op_str} (addr reg as base ptr store)')
                print(f'mod{idx} @{ins.address:#010x} {reg} <- {val:#010x}')
                for u in uses: print(f'    {u}')
