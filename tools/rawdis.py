import sys, struct, glob, json
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
ROOT='/home/hatch/workspace/fosi-dap-neo'
man=json.load(open(f'{ROOT}/extracted/manifest.json')); mods={m['index']:m for m in man['modules']}
def load(idx,kind):
    f=glob.glob(f'{ROOT}/extracted/module_{idx:02d}_{kind}_*.bin'); return open(f[0],'rb').read() if f else b''
idx=int(sys.argv[1]); start=int(sys.argv[2],0); length=int(sys.argv[3],0)
m=mods[idx]; code=load(idx,'code'); base=m['code_exec']; data=load(idx,'data'); dbase=m['data_exec']
m0=mods[0]; segs=[(code,base),(data,dbase),(load(0,'code'),m0['code_exec']),(load(0,'data'),m0['data_exec'])]
def read(a,n):
    for buf,b in segs:
        if b<=a<b+len(buf): return buf[a-b:a-b+n]
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB|CS_MODE_MCLASS); md.skipdata=True
off=start-base
for ins in md.disasm(code[off:off+length], start):
    note=''
    if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
        try:
            imm=int(ins.op_str.split('#')[1].rstrip(']'),0); la=(ins.address+4 & ~3)+imm; v=read(la,4)
            if v: note=f'  ; [{la:#x}] = {struct.unpack("<I",v)[0]:#010x}'
        except Exception: pass
    print(f'{ins.address:08x}  {ins.bytes.hex(" "):<14} {ins.mnemonic:<8} {ins.op_str}{note}')
