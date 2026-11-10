import re, sys, glob
from pathlib import Path
ext=Path(__file__).resolve().parent.parent/"extracted"
def strs(data, minlen=4):
    out=[]
    for m in re.finditer(rb'[\x20-\x7e]{%d,}'%minlen, data):
        out.append((m.start(), m.group().decode()))
    # utf16le
    for m in re.finditer(rb'(?:[\x20-\x7e]\x00){%d,}'%minlen, data):
        try: out.append((m.start(), m.group().decode('utf-16-le')))
        except: pass
    return sorted(out)
if __name__=="__main__":
    pat=re.compile(sys.argv[1], re.I) if len(sys.argv)>1 else None
    for f in sorted(ext.glob("module_*_*.bin")):
        data=f.read_bytes()
        hits=[(o,s) for o,s in strs(data) if pat.search(s)] if pat else strs(data)
        if hits:
            print(f"=== {f.name} ({len(data)} bytes)")
            for o,s in hits[:200]: print(f"  +{o:#x}: {s!r}")
