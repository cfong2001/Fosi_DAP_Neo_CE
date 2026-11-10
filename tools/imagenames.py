#!/usr/bin/env python3
"""Correlate image-resource names (ASCII manifest in the image section)
with image record IDs by order and by the (x,y) embedded in each name.
Run from ~/workspace/fosi-dap-neo."""
import sys, re
sys.path.insert(0,'repo/tools')
from rknano_image import Image
raw=open('DP3_V137.img','rb').read()
im=Image(raw)
imgs=list(im.images())
# name manifest: scan the whole file for printable ASCII runs that look like
# resource names: letters/digits/underscore ending with _(x,y) or plain names.
names=[]
for m in re.finditer(rb'[ -~]{4,}', raw):
    s=m.group().decode('ascii')
    if re.fullmatch(r'[A-Za-z0-9_]+_\(\d+,\d+\)', s) or re.fullmatch(r'A_[A-Za-z0-9_]+', s):
        names.append((m.start(), s))
print(f'{len(names)} candidate name strings, {len(imgs)} image records')
# The manifest is a contiguous block; find the densest region: names whose
# file offsets are increasing and close together. Print lock-related ones
# with their ordinal position among manifest names.
lock=[(i,off,s) for i,(off,s) in enumerate(names) if 'LOCK' in s or 'HOLD' in s]
for i,off,s in lock: print(f'manifest#{i} file@{off:#x} {s}')
# check ordinal==id hypothesis on a few entries via (x,y)
def xy(s):
    m=re.search(r'\((\d+),(\d+)\)$', s)
    return (int(m.group(1)), int(m.group(2))) if m else None
match=0; tot=0
for i,(off,s) in enumerate(names[:len(imgs)]):
    p=xy(s)
    if p is not None:
        tot+=1
        if imgs[i]['x']==p[0] and imgs[i]['y']==p[1]: match+=1
print(f'(x,y) agreement for first {len(imgs)} manifest names vs record ids: {match}/{tot}')
for i,off,s in lock:
    if i < len(imgs):
        e=imgs[i]
        print(f'  -> if id==manifest#: id {i}: {s} record w={e["width"]} h={e["height"]} x={e["x"]} y={e["y"]}')
