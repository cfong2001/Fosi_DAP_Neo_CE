#!/usr/bin/env python3
"""Literal-word scan across all extracted modules for inter-core targets.
Usage: litscan.py [target ...]  (hex addrs; defaults to the core-1 set)
Searches code+data regions byte-wise for the LE word, reports module + exec addr.
Also reports near-miss words in the 0x0100xxxx / 0x6008xxxx ranges when no exact given."""
import struct, json, glob, sys, os
os.chdir(os.path.expanduser('~/workspace/fosi-dap-neo'))
man = json.load(open('extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}

def region(idx, kind):
    f = glob.glob(f'extracted/module_{idx:02d}_{kind}_*.bin')
    if not f: return None, None
    return open(f[0], 'rb').read(), mods[idx][kind + '_exec']

def scan(targets):
    for idx in range(82):
        for kind in ('code', 'data'):
            d, b = region(idx, kind)
            if d is None: continue
            for t in targets:
                pat = struct.pack('<I', t)
                i = 0
                while True:
                    j = d.find(pat, i)
                    if j < 0: break
                    print(f'  mod{idx:02d} {kind} @{b+j:#010x} = {t:#010x}')
                    i = j + 1

if __name__ == '__main__':
    if len(sys.argv) > 1:
        tg = [int(x, 0) for x in sys.argv[1:]]
    else:
        tg = [0x01000000, 0x01020000, 0x01022000, 0x60082000, 0x60085000,
              0x60050000, 0x60051000, 0x60042000, 0x0304ad70, 0x030368d8]
    scan(tg)
