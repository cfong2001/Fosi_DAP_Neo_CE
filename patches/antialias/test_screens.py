#!/usr/bin/env python3
"""Checks for the baked-antialiasing screens set (generate_screens.py).

  1. Regenerating reproduces the committed screens-glyphs.json and
     ../theme_editor/ce-mark.json byte for byte.
  2. The Standard image carries every generated resource exactly, and
     the knob repoint: the BL at 0x0307F79A in module 27 targets the
     keyed helper 0x03063A08.
  3. Emulated on that image (the keyed-transport Machine, real module 0
     code): the keyed helper draws knob 220 (dark) and 386 (light) as
     exactly their non-key pixels at the requested position.
  4. Dialog cards keep their size; outside the radius-16 corners every
     pixel is the key, and no key pixel appears anywhere else.

Usage: test_screens.py [CE_IMAGE]   (default release/DP3_V137_CE.img)
"""
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS  # noqa: E402

spec = importlib.util.spec_from_file_location(
    'kt', ROOT / 'patches' / 'design_refresh_v4' / 'test_keyed_transport.py')
KT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(KT)

KEY = 0xF800
fails = []


def check(name, ok, detail=''):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f': {detail}' if detail else ''))
    if not ok:
        fails.append(name)


def words(raw, e):
    return struct.unpack_from(f'>{e["width"] * e["height"]}H', raw, e['data_offset'])


def main():
    ce_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'release' / 'DP3_V137_CE.img'
    ce = ce_path.read_bytes()
    stock = (ROOT / 'DP3_V137.img').read_bytes()

    # 1. reproducible outputs
    outputs = [HERE / 'screens-glyphs.json', ROOT / 'patches' / 'theme_editor' / 'ce-mark.json']
    before = [p.read_bytes() for p in outputs]
    subprocess.run([sys.executable, str(HERE / 'generate_screens.py')], check=True,
                   capture_output=True)
    after = [p.read_bytes() for p in outputs]
    check('generator reproduces screens-glyphs.json and ce-mark.json', before == after)

    # 2. the image carries the art and the repoint
    S = {e['id']: e for e in Image(stock).images()}
    C = {e['id']: e for e in Image(ce).images()}
    runs = json.loads(outputs[0].read_text())['runs'] + json.loads(outputs[1].read_text())['runs']
    want = bytearray(stock)
    for r in runs:
        o = int(r['offset'], 16)
        want[o:o + len(bytes.fromhex(r['replace']))] = bytes.fromhex(r['replace'])
    ids = (137, 193, 203, 303, 359, 369, 294, 127, 293, 187, 188, 353, 354, 220, 386)
    bad = [i for i in ids
           if ce[C[i]['data_offset']:C[i]['data_offset'] + C[i]['size']] !=
           bytes(want[S[i]['data_offset']:S[i]['data_offset'] + S[i]['size']])]
    check(f'Standard image carries all {len(ids)} generated resources exactly', not bad, bad)
    im = Image(ce)
    off, _ = im.module_region(27, 'code')
    base = im.modules[27]['code_exec']
    site = 0x0307F79A
    ins = next(Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS).disasm(
        ce[off + site - base:off + site - base + 4], site))
    check('knob draw at 0x0307F79A is a BL to the keyed helper 0x03063A08',
          ins.mnemonic == 'bl' and int(ins.op_str.lstrip('#'), 0) == 0x03063A08,
          f'{ins.mnemonic} {ins.op_str}')

    # 3. emulated keyed draw of the knob, both themes
    for rid, theme in ((220, 0), (386, 1)):
        m = KT.Machine(ce, real_store=False)
        m.stage([220, 386])
        m.u.mem_write(KT.SAVEINFO + 0x2D8, bytes([theme]))
        x0, y0 = 100, 254
        m.call(KT.HELPER, 220, x0, y0)
        art = words(ce, C[rid])
        expect = {(x0 + i % 14, y0 + i // 14, v) for i, v in enumerate(art) if v != KEY}
        got = set(m.stores)
        check(f'keyed helper draws knob {rid} as exactly its {len(expect)} non-key pixels',
              got == expect and len(m.stores) == len(expect),
              f'{len(m.stores)} stores')

    # 4. dialog cards: key only outside the corners
    for rid in (137, 193, 203, 303, 359, 369):
        e = C[rid]
        w, h = e['width'], e['height']
        px = words(ce, e)
        stray = [(x, y) for y in range(h) for x in range(w)
                 if px[y * w + x] == KEY and not (
                     (x < 16 or x >= w - 16) and (y < 16 or y >= h - 16))]
        corner_keys = sum(px[y * w + x] == KEY for y in range(16) for x in range(16))
        check(f'card {rid}: key only in the corners ({corner_keys} in one corner)',
              not stray and 30 < corner_keys < 80, stray[:3])

    print('FAILED: ' + ', '.join(fails) if fails else 'all checks passed')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
