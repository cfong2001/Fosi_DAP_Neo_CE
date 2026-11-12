#!/usr/bin/env python3
"""Checks for the redrawn Font B glyphs (generate_font.py).

  1. Regenerating reproduces font-glyphs.json byte for byte.
  2. The Standard image carries every redrawn record exactly, at its
     own font_b section offset.
  3. Advances follow the firmware's measurer (0x030627BE): each redrawn
     ASCII letter's ink-derived advance leaves 1 to 3 clear columns
     after its ink (the measure reads rows 0 to 9 only); every
     other redrawn glyph has a tail above 0x80; the ten digits share one
     advance; the space is 4.
  4. No redrawn glyph leaves the 16 x 16 cell, and descenders stay in
     rows 13 to 15.

Usage: test_font.py [CE_IMAGE]   (default release/DP3_V137_CE.img)
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

spec = importlib.util.spec_from_file_location('gf', HERE / 'generate_font.py')
GF = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GF)

fails = []


def check(name, ok, detail=''):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f': {detail}' if detail else ''))
    if not ok:
        fails.append(name)


def main():
    ce = (Path(sys.argv[1]) if len(sys.argv) > 1
          else ROOT / 'release' / 'DP3_V137_CE.img').read_bytes()
    out = HERE / 'font-glyphs.json'
    before = out.read_bytes()
    gen = subprocess.run([sys.executable, str(HERE / 'generate_font.py')],
                         capture_output=True, text=True)
    if gen.returncode:
        raise SystemExit(gen.stdout + gen.stderr)
    check('generator reproduces font-glyphs.json', out.read_bytes() == before)

    raw, glyphs, skipped = GF.build()
    base = Image(ce).sections['font_b']['offset']
    bad = [cp for cp, rec in glyphs.items()
           if ce[base + cp * GF.STRIDE:base + (cp + 1) * GF.STRIDE] != rec]
    check(f'Standard image carries all {len(glyphs)} redrawn records', not bad,
          [hex(c) for c in bad[:5]])
    runs = json.loads(before)['runs']
    check('one run per changed record', len(runs) == len(glyphs), f'{len(runs)} runs')

    def ink(rec):
        return [(x, y) for y in range(GF.ROWS) for x in range(16)
                if int.from_bytes(rec[2 * y:2 * y + 2], 'big') & (0x8000 >> x)]

    letters = [cp for cp in glyphs if GF.ascii_letter(cp)]
    gaps = {chr(cp): GF.advance(glyphs[cp], cp) - max(x for x, _ in ink(glyphs[cp])) - 1
            for cp in letters}
    wrong = {c: g for c, g in gaps.items() if not 1 <= g <= 3}
    check(f'{len(letters)} ASCII letters: the firmware advance leaves 1 to 3 clear '
          'columns after the ink', not wrong, wrong)
    others = [cp for cp in glyphs if not GF.ascii_letter(cp)]
    check(f'{len(others)} other glyphs carry an explicit tail',
          all(glyphs[cp][32] > 0x80 for cp in others))
    digits = {GF.advance(glyphs[c], c) for c in range(0x30, 0x3A)}
    check('digits share one advance', len(digits) == 1, digits)
    check('space advance is 4', GF.advance(glyphs[0x20], 0x20) == 4)
    desc = [chr(c) for c in (0x67, 0x6A, 0x70, 0x71, 0x79)
            if max(y for _, y in ink(glyphs[c])) not in (13, 14, 15)]
    check('descenders g j p q y reach rows 13 to 15', not desc, desc)
    check('only U+00B2, U+00B3 and U+0140 keep stock records',
          sorted(cp for cp, _ in skipped) == [0xB2, 0xB3, 0x140],
          [hex(cp) for cp, _ in skipped])

    print('FAILED: ' + ', '.join(fails) if fails else 'all checks passed')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
