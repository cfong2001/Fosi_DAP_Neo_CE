#!/usr/bin/env python3
"""Key the light-theme play-mode icons' white surround.

The play-mode indicator (resources 286 to 289, light 452 to 455) is
drawn through the keyed helper 0x03063A08, which skips 0xF800 pixels
(design_v4.md, prove_keying.py). The dark icons carry a 0xF800
surround. The light icons carry a white (0xFFFF) one instead, which
stock never shows because its light player ground is also 0xFFFF.
Theater mode changes the ground, so on CE the light icons showed as
white boxes (found by the site simulator; the emulated painter shows
the same).

This script turns each light icon's border-connected 0xFFFF pixels
(4-connected flood fill from the edge) into 0xF800. Every white pixel
in these four icons is border-connected, so no glyph pixel changes;
the script asserts that. Output: play-mode-light.json, four runs at
stock offsets in the studio's run format, one per resource.

Usage (repository root): python3 patches/design_refresh_v4/play_mode_light/generate.py
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
from rknano_image import Image  # noqa: E402

STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
IDS = (452, 453, 454, 455)
WHITE, KEY = 0xFFFF, 0xF800


def surround(px, w, h):
    seen, stack = set(), [(x, y) for x in range(w) for y in (0, h - 1)] + \
        [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or px[y * w + x] != WHITE:
            continue
        seen.add((x, y))
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return seen


def main():
    raw = (REPO / 'DP3_V137.img').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == STOCK_SHA, 'stock SHA gate'
    entries = {e['id']: e for e in Image(raw).images()}
    runs = []
    for rid in IDS:
        e = entries[rid]
        w, h, off = e['width'], e['height'], e['data_offset']
        old = raw[off:off + e['size']]
        px = [v for (v,) in struct.iter_unpack('>H', old)]   # panel order
        keyed = surround(px, w, h)
        assert all(px[y * w + x] == WHITE for x, y in keyed)
        assert sum(1 for v in px if v == WHITE) == len(keyed), \
            f'resource {rid} has white glyph pixels; refusing'
        assert KEY not in px, f'resource {rid} already uses the key colour'
        new = list(px)
        for x, y in keyed:
            new[y * w + x] = KEY
        runs.append({'offset': hex(off), 'expect': old.hex(),
                     'replace': struct.pack(f'>{len(new)}H', *new).hex()})
        print(f'resource {rid}: {len(keyed)} of {w * h} pixels keyed')
    out = HERE / 'play-mode-light.json'
    out.write_text(json.dumps({'version': 1, 'literal_sites': [], 'runs': runs},
                              indent=1) + '\n')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
