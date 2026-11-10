#!/usr/bin/env python3
"""Generate the site simulator's painter data and its reference hashes.

Runs the real player painter segment (modules 0, 18 and 27, under
Unicorn, through patches/design_refresh_v4/test_keyed_transport.py) on
the stock image and the CE standard image, for every transport state
in both themes, and records:

  docs/sim-data.mjs             what the painter draws: fills and
                                resource draws (id, x, y, keyed or not)
                                per image and state, plus the pinned
                                location and SHA-256 of each image's
                                resource section. No pixel data.
  tests/fixtures/sim-painter.json
                                the SHA-256 of each emulated 240x320
                                framebuffer, which tests/sim-core.test.mjs
                                requires docs/sim-core.mjs to reproduce
                                exactly from the same images.

Usage (from the repository root, with Unicorn and Capstone):

  python3 tools/gen_sim_data.py
"""
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
from rknano_image import Image  # noqa: E402

spec = importlib.util.spec_from_file_location(
    'keyed', REPO / 'patches/design_refresh_v4/test_keyed_transport.py')
KT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(KT)

IMAGES = {
    'stock': ('DP3_V137.img', REPO / 'DP3_V137.img'),
    'ce': ('release/DP3_V137_CE.img', REPO / 'release' / 'DP3_V137_CE.img'),
}
# Resources the painter segment can draw, in both themes (light = +166).
DARK_IDS = [155, 156] + list(range(157, 182)) + list(range(286, 290))
IDS = DARK_IDS + [i + 166 for i in DARK_IDS]
LIGHT_OFFSET = 166
# (state B, play): playing and paused on the first page, the second
# page, and the selection state (which the painter reaches with A = 1).
STATES = [(0, 1), (0, 0), (1, 1), (2, 1)]
DEFAULT_GROUND = {0: 0x10A2, 1: 0xFFFF}   # stock row band surrounds (155, 321)
THEATER_GROUND = 0x7222                   # a theater-derived ground
# Synthetic art for the theater check: word(x, y) = (x * MX + y * MY + C)
# & 0xFFFF, so the page's test can rebuild the same pixels.
THEATER_ARTS = [(144, 144, 7, 13, 0), (144, 144, 0, 0, 0x7BEF),
                (30, 18, 2113, 97, 4096), (16, 16, 1, 2048, 31)]


def theater_cases():
    # Load only the pure port functions: the module runs its harness at
    # import, so exec its source up to the emulator section.
    src = (REPO / 'patches/full/build/tests/test_theater_full.py').read_text()
    start = src.index('def port_average')
    end = src.index('# ------------------------------------------------ variant build')
    ns = {}
    exec(src[start:end], ns)
    cases = []
    for w, h, mx, my, c in THEATER_ARTS:
        rows = [[(x * mx + y * my + c) & 0xFFFF for x in range(w)]
                for y in range((h + 2) // 3)]
        for light in (False, True):
            cell, _, _ = ns['port_derived'](rows, light)
            cases.append({'width': w, 'height': h, 'mx': mx, 'my': my, 'c': c,
                          'light': light, 'ground': cell})
    return cases


def run(raw, theme, b, play, ground):
    m = KT.Machine(raw, real_store=True)
    m.stage(IDS)
    KT.fb_fill(m, ground)
    m.painter(state_a=1 if b == 2 else 0, state_b=b, play=play,
              theme=theme, ground=ground)
    fb = b''.join(bytes(m.u.mem_read(KT.fb_addr(m, 0, y), 480))
                  for y in range(320))
    ops = []
    for entry in m.drawlog:
        if entry[0] == 'fill':
            _, x0, y0, x1, y1, colour = entry
            if colour != ground:
                raise SystemExit(f'fill colour 0x{colour:04X} is not the ground')
            ops.append(['fill', x0, y0, x1, y1])
        else:
            _, fn, rid, x, y = entry
            ops.append(['draw', rid, x, y, fn == KT.HELPER])
    return ops, hashlib.sha256(fb).hexdigest()


def main():
    painter, sections, cases = {}, {}, []
    for name, (rel, path) in IMAGES.items():
        raw = path.read_bytes()
        start, length = struct.unpack_from('<II', raw, 0x14C)
        sections[name] = {
            'file': rel, 'image_sha256': hashlib.sha256(raw).hexdigest(),
            'offset': start, 'length': length,
            'sha256': hashlib.sha256(raw[start:start + length]).hexdigest()}
        ids = {e['id'] for e in Image(raw).images()}
        assert set(IDS) <= ids
        painter[name] = {}
        grounds = [None, THEATER_GROUND] if name == 'ce' else [None]
        for b, play in STATES:
            key = f'{b}:{play}'
            for theme in (0, 1):
                for g in grounds:
                    ground = DEFAULT_GROUND[theme] if g is None else g
                    ops, digest = run(raw, theme, b, play, ground)
                    # The draw list must not depend on theme or ground:
                    # the page replays one list for every combination.
                    if painter[name].setdefault(key, ops) != ops:
                        raise SystemExit(f'{name} {key}: draw list varies')
                    cases.append({'image': name, 'theme': theme, 'b': b,
                                  'play': play, 'ground': ground,
                                  'sha256': digest})
            print(name, key, painter[name][key])

    data = REPO / 'docs' / 'sim-data.mjs'
    data.write_text(
        '// Generated by tools/gen_sim_data.py from emulation of the real\n'
        '// player painter (modules 0, 18 and 27). Do not edit by hand.\n'
        '//\n'
        '// PAINTER[image]["B:play"] lists what the painter draws over the\n'
        '// ground for that transport state: ["fill", x0, y0, x1, y1] fills\n'
        '// with the ground (inclusive corners), ["draw", id, x, y, keyed]\n'
        '// draws a resource (keyed draws skip 0xF800 pixels). In the light\n'
        '// theme every resource id is offset by LIGHT_OFFSET.\n'
        '// SECTIONS pins where each image keeps its resource section and\n'
        '// the SHA-256 of those bytes; the page refuses anything else.\n'
        f'export const LIGHT_OFFSET = {LIGHT_OFFSET};\n'
        f'export const DEFAULT_GROUND = {json.dumps({"dark": DEFAULT_GROUND[0], "light": DEFAULT_GROUND[1]})};\n'
        f'export const SECTIONS = {json.dumps(sections, indent=2)};\n'
        f'export const PAINTER = {json.dumps(painter)};\n')
    fixture = REPO / 'tests' / 'fixtures' / 'sim-painter.json'
    fixture.parent.mkdir(exist_ok=True)
    fixture.write_text(json.dumps(
        {'generator': 'tools/gen_sim_data.py',
         'framebuffer': '240x320 little-endian RGB565 words, row-major',
         'cases': cases, 'theater': theater_cases()}, indent=1) + '\n')
    print(f'wrote {data} and {fixture} ({len(cases)} cases)')


if __name__ == '__main__':
    main()
