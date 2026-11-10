#!/usr/bin/env python3
"""Reproducible term search over DP3_V137.img.
Encodings: ASCII (case-insensitive), UTF-16LE, UTF-16BE.
Whole image + per extracted-module attribution (via extracted/manifest.json).
Usage: search_terms.py [image] [extracted_dir]
"""
import sys, json, re
from pathlib import Path
img_path = Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent.parent/"DP3_V137.img")
ext_dir  = Path(sys.argv[2] if len(sys.argv)>2 else Path(__file__).resolve().parent.parent/"extracted")
raw = img_path.read_bytes()
print(f"image {img_path} len={len(raw)} sha256=", end="")
import hashlib; print(hashlib.sha256(raw).hexdigest())

# module file ranges in image: recompute from rknano_image if available
sys.path.insert(0, str(Path.home()/"workspace/fosi-dap-neo/repo/tools"))
try:
    from rknano_image import Image
    im = Image(raw)
    ranges=[]
    for m in im.modules:
        for kind in ("code","data"):
            ln=m[kind+"_len"]
            if ln:
                off=im.file_offset(m[kind+"_load"]); ranges.append((off,off+ln,m["index"],kind))
except Exception as e:
    print("module ranges unavailable:",e); ranges=[]
def attribute(off):
    hits=[f"mod{idx}:{kind}" for a,b,idx,kind in ranges if a<=off<b]
    return ",".join(hits) if hits else "resource/header/other"

TERMS = ["m3u","m3u8","#EXTM3U",".pla",".pls","xspf","playlist","favourite","favorite",
         "recent","history","medialib","media lib","all songs","playlists",
         "*.mp3",".mp3",".flac",".ape",".dsd",".m4a",".wav",".lrc","cue"]
def encodings(term):
    yield "ascii", term.encode()
    yield "utf16le", term.encode("utf-16-le")
    yield "utf16be", term.encode("utf-16-be")

for term in TERMS:
    total=0
    for enc, pat in encodings(term):
        # case-insensitive: search lowercased haystack for ascii; for utf16, fold A-Z bytes pattern-wise by regex
        if enc=="ascii":
            hay=raw.lower(); needle=pat.lower()
            offs=[m.start() for m in re.finditer(re.escape(needle), hay)]
        else:
            # build regex allowing either case for each ASCII letter code unit
            units=[pat[i:i+2] for i in range(0,len(pat),2)]
            parts=[]
            for u in units:
                ch = u.decode("utf-16-le" if enc=="utf16le" else "utf-16-be")
                if ch.isalpha():
                    alts={ch.lower(), ch.upper()}
                    parts.append(b"(?:"+b"|".join(re.escape(a.encode("utf-16-le" if enc=="utf16le" else "utf-16-be")) for a in alts)+b")")
                else:
                    parts.append(re.escape(u))
            offs=[m.start() for m in re.finditer(b"".join(parts), raw)]
        if offs:
            total+=len(offs)
            for o in offs[:40]:
                ctx=raw[max(0,o-24):o+40]
                print(f"{term!r} {enc} @{o:#x} [{attribute(o)}] ctx={ctx!r}")
            if len(offs)>40: print(f"  ... and {len(offs)-40} more")
    print(f"TERM {term!r}: total_hits={total}")
