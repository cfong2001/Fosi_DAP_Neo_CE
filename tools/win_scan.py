#!/usr/bin/env python3
"""For each candidate module: dump data u32s pointing into own code (WIN test) + strings."""
import struct, glob, json, re, sys
ROOT = '/home/hatch/workspace/fosi-dap-neo'
man = json.load(open(f'{ROOT}/extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}

def load(idx, kind):
    f = glob.glob(f'{ROOT}/extracted/module_{idx:02d}_{kind}_*.bin')
    return open(f[0], 'rb').read() if f else b''

def strings(buf, minlen=4):
    out = []
    cur = b''
    for b in buf:
        if 32 <= b < 127:
            cur += bytes([b])
        else:
            if len(cur) >= minlen:
                out.append(cur.decode())
            cur = b''
    if len(cur) >= minlen:
        out.append(cur.decode())
    return out

targets = [int(x) for x in sys.argv[1:]] or [3,4,5,6,7,9,17,19,20,21,25,26,29,30,36,61,81]
for idx in targets:
    m = mods[idx]
    code, data = load(idx, 'code'), load(idx, 'data')
    cb, ce = m['code_exec'], m['code_exec'] + len(code)
    print(f"\n===== module {idx}: code @{cb:#x} len {len(code):#x}, data @{m['data_exec']:#x} len {len(data):#x}, bss {m['bss_len']:#x}")
    if data:
        for o in range(0, len(data) - 3, 4):
            v = struct.unpack_from('<I', data, o)[0]
            if cb <= (v & ~1) < ce or v == 0x0307d165:
                print(f"  data+{o:#04x} = {v:#010x} (code+{(v & ~1)-cb:#x})")
    ss = strings(code) + [s + ' [data]' for s in strings(data)]
    seen = set(); ss = [s for s in ss if not (s in seen or seen.add(s))]
    print("  strings:", ' | '.join(ss[:28]) if ss else '(none)')
