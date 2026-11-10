import struct
from collections import defaultdict

def parse(path):
    p = open(path,'rb').read()
    size, n = struct.unpack_from('<II', p, 72)
    m={}; pos=80
    for _ in range(n):
        off, ln = struct.unpack_from('<II', p, pos)
        for i,b in enumerate(p[pos+8:pos+8+ln]): m[off+i]=b
        pos += 8+ln
    return m

# Portable paths (tools/fosi_paths.py): argv[1] > FOSI_ECPATCH_DIR > discovery.
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
m52=parse(base+'HIFIEC52.ecpatch'); m56=parse(base+'HIFIEC56.ecpatch'); m58=parse(base+'HIFIEC58.ecpatch')

def clusters(positions):
    ps=sorted(positions); out=[]
    for p in ps:
        if out and p-out[-1][1]<=16: out[-1][1]=p
        else: out.append([p,p])
    return out

# positions where 56 differs from 52 (changed by 56 relative to 52's output)
diff56 = {o for o in set(m56)|set(m52) if m56.get(o)!=m52.get(o)}
print("56-vs-52 differing positions:", len(diff56))
for a,b in clusters(diff56):
    print(f"  cluster {a:#010x} .. {b:#010x}  len={b-a+1}")
diff58 = {o for o in set(m58)|set(m56) if m58.get(o)!=m56.get(o)}
print("58-vs-56 differing positions:", len(diff58))
for a,b in clusters(diff58):
    print(f"  cluster {a:#010x} .. {b:#010x}  len={b-a+1}")
