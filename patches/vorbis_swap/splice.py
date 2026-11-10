import struct, hashlib, json

def parse(path):
    p = open(path,'rb').read()
    assert p[:8]==b'ECPATCH1'
    size, n = struct.unpack_from('<II', p, 72)
    m={}; pos=80
    for _ in range(n):
        off, ln = struct.unpack_from('<II', p, pos)
        for i,b in enumerate(p[pos+8:pos+8+ln]): m[off+i]=b
        pos += 8+ln
    return m

# Portable paths (tools/fosi_paths.py): .ecpatch dir from argv[1] >
# FOSI_ECPATCH_DIR > discovery; module bins live next to this script.
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import transplant  # noqa: F401  (bootstraps the repo tools path)
import fosi_paths
_ecp = fosi_paths.ecpatch_dir(fosi_paths.repo_root(HERE),
                              sys.argv[1] if len(sys.argv) > 1 else None)
if _ecp is None:
    raise SystemExit('ecpatch inputs not found (see DEPENDENCY.md)')
base = str(_ecp) + '/'
m52=parse(base+'HIFIEC52.ecpatch'); m56=parse(base+'HIFIEC56.ecpatch')

ECHO_MOD_BASE=0x142284; CODE_LEN=62936; DATA_LEN=53636
MOD_END=ECHO_MOD_BASE+CODE_LEN+DATA_LEN

code=bytearray((HERE/'module75_stock_code.bin').read_bytes())
data=bytearray((HERE/'module75_stock_data.bin').read_bytes())
assert len(code)==CODE_LEN and len(data)==DATA_LEN

FREED_CODE=(0x29d0,0xe054); FREED_D1=(0x3480,0x9888); FREED_D2=(0x98a0,0xd148)
def freed(kind,off):
    if kind=='code': return FREED_CODE[0]<=off<FREED_CODE[1]
    return (FREED_D1[0]<=off<FREED_D1[1]) or (FREED_D2[0]<=off<FREED_D2[1])

# sanity: does the Opus-only patch (52) touch module 77's region at all?
in52=[o for o in m52 if ECHO_MOD_BASE<=o<MOD_END]
print(f"positions inside Echo module-77 region changed by Opus-only HIFIEC52: {len(in52)}")

surgery=[]; violations=[]
for o in sorted(set(m56)|set(m52)):
    if not (ECHO_MOD_BASE<=o<MOD_END): continue
    if m56.get(o)==m52.get(o): continue
    mc=o-ECHO_MOD_BASE
    if mc<CODE_LEN: kind,off='code',mc
    else: kind,off='data',mc-CODE_LEN
    if not freed(kind,off): violations.append((o,kind,off))
    surgery.append((o,kind,off,m56[o]))
print(f"surgery positions: {len(surgery)}  violations of freed-region map: {len(violations)}")
for v in violations[:20]: print("  VIOLATION:", hex(v[0]), v[1], hex(v[2]))

for o,kind,off,b in surgery:
    (code if kind=='code' else data)[off]=b
(HERE/'module75_patched_code.bin').write_bytes(code)
(HERE/'module75_patched_data.bin').write_bytes(data)
patched=bytes(code)+bytes(data)
(HERE/'module75_patched.bin').write_bytes(patched)
stock=(HERE/'module75_stock_code.bin').read_bytes()+(HERE/'module75_stock_data.bin').read_bytes()
print("patched module sha256:", hashlib.sha256(patched).hexdigest())
print("stock   module sha256:", hashlib.sha256(stock).hexdigest())
# coverage stats
sc=[off for _,k,off,_ in surgery if k=='code']; sd=[off for _,k,off,_ in surgery if k=='data']
print(f"code bytes changed: {len(sc)} of {FREED_CODE[1]-FREED_CODE[0]} freed (range {min(sc):#x}..{max(sc):#x})")
print(f"data bytes changed: {len(sd)} of {(FREED_D1[1]-FREED_D1[0])+(FREED_D2[1]-FREED_D2[0])} freed (D1 {sum(1 for _,k,off,_ in surgery if k=='data' and off<0x9888)}, D2 {sum(1 for _,k,off,_ in surgery if k=='data' and off>=0x98a0)})")
json.dump({'surgery_positions':len(surgery),'violations':len(violations)}, open(HERE/'splice_stats.json','w'))
