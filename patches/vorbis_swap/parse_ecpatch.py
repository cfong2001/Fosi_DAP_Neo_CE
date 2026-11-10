import struct, sys, hashlib

def parse(path):
    p = open(path,'rb').read()
    assert p[:8]==b'ECPATCH1', path
    h_in = p[8:40].hex(); h_out = p[40:72].hex()
    size, n = struct.unpack_from('<II', p, 72)
    recs=[]; pos=80
    for _ in range(n):
        off, ln = struct.unpack_from('<II', p, pos)
        recs.append((off, ln, p[pos+8:pos+8+ln]))
        pos += 8+ln
    return h_in, h_out, size, recs

# Portable paths (tools/fosi_paths.py): argv[1] > FOSI_ECPATCH_DIR > discovery.
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import transplant  # noqa: F401  (bootstraps the repo tools path)
import fosi_paths
_ecp = fosi_paths.ecpatch_dir(fosi_paths.repo_root(HERE),
                              sys.argv[1] if len(sys.argv) > 1 else None)
if _ecp is None:
    raise SystemExit('ecpatch inputs not found (see DEPENDENCY.md)')

for name in ['HIFIEC50','HIFIEC52','HIFIEC56','HIFIEC58']:
    h_in,h_out,size,recs = parse(_ecp / f'{name}.ecpatch')
    total = sum(l for _,l,_ in recs)
    print(f"{name}: in={h_in[:12]} out={h_out[:12]} size={size} nrec={len(recs)} changed_bytes={total}")
    # cluster ranges
    if recs:
        print(f"   span: {recs[0][0]:#x} .. {recs[-1][0]+recs[-1][1]:#x}")
