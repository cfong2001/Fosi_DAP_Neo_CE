import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent))
from rknano_image import Image
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
import struct
_img = _P(sys.argv[2]) if len(sys.argv) > 2 else _P(__file__).resolve().parent.parent / 'DP3_V137.img'
IMG=Image(_img.read_bytes())
idx=int(sys.argv[1]); m=IMG.modules[idx]
off,_=IMG.module_region(idx,'code'); code=IMG.raw[off:off+m['code_len']]; base=m['code_exec']
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB|CS_MODE_MCLASS)
out=[]
for ins in md.disasm(code, base):
    note=''
    if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
        try:
            imm=int(ins.op_str.split('#')[1].rstrip(']'),0)
            la=(ins.address+4 & ~3)+imm
            # read from this module code region
            lo=la-base
            if 0<=lo<len(code)-3:
                v=struct.unpack_from('<I',code,lo)[0]; note=f'  ; [{la:#x}]={v:#010x}'
        except Exception: pass
    if ins.mnemonic in ('adr',):
        try:
            imm=int(ins.op_str.split('#')[1],0); note=f'  ; -> {imm:#x}'
        except Exception: pass
    out.append(f'{ins.address:08x}  {ins.bytes.hex(" "):<14} {ins.mnemonic:<8} {ins.op_str}{note}')
Path(f'/tmp/mod{idx}.dis').write_text("\n".join(out))
print(f"module {idx}: {len(out)} insns -> /tmp/mod{idx}.dis")
