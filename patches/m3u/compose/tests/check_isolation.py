#!/usr/bin/env python3
"""Segment isolation check for the composed grown build.

Compares the grown image (default manifest + transplants + patches
0033/0040 + module 31 code grown by payload.bin) against the
equivalent ungrown build (default manifest + transplants only),
segment by segment through the image records:

  - every module except 31: code and data segments byte-identical;
  - module 31 data: byte-identical;
  - module 31 code: grown == ungrown code with the payload appended,
    except exactly the two 4-byte hook sites inside the stock-length
    prefix (patch 0040 at 0x0307DF1A, patch 0033 at 0x0307E89E),
    whose grown bytes must equal the patches' replacement bytes and
    whose ungrown bytes must equal the stock expect bytes.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'repo' / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'framework' / 'tools'))

from rknano_image import Image          # noqa: E402
from validate_grown import validate_grown  # noqa: E402

HERE = Path(__file__).resolve().parent
GROWN = (HERE.parent / 'out' / 'grown.img').read_bytes()
UNGROWN = (HERE.parent / 'out' / 'ungrown.img').read_bytes()
PAYLOAD = (HERE.parent / 'payload.bin').read_bytes()

SITES = {0x0307DF1A: ('fff76df9', '00f095bf', 'patch 0040'),
         0x0307E89E: ('e4f72fbf', '01f0edbf', 'patch 0033')}


def main():
    validate_grown(GROWN)
    print('validate_grown(grown.img): passed')
    gi, ui = Image(GROWN), Image(UNGROWN)
    assert len(gi.modules) == len(ui.modules)
    failures = []
    for m in ui.modules:
        i = m['index']
        for kind in ('code', 'data'):
            uo, ul = ui.module_region(i, kind)
            go, gl = gi.module_region(i, kind)
            ub = UNGROWN[uo:uo + ul]
            gb = GROWN[go:go + gl]
            if i == 31 and kind == 'code':
                if gl != ul + len(PAYLOAD):
                    failures.append(f'module 31 code length {gl} != '
                                    f'{ul} + {len(PAYLOAD)}')
                    continue
                if gb[ul:] != PAYLOAD:
                    failures.append('module 31 code tail != payload.bin')
                prefix_g, prefix_u = gb[:ul], ub
                diffs = [k for k in range(ul) if prefix_g[k] != prefix_u[k]]
                expect_diffs = []
                base = m['code_exec']
                for addr, (exp, rep, name) in SITES.items():
                    rel = addr - base
                    eb, rb = bytes.fromhex(exp), bytes.fromhex(rep)
                    expect_diffs += [rel + k for k in range(4)
                                     if eb[k] != rb[k]]
                    if prefix_u[rel:rel + 4].hex() != exp:
                        failures.append(f'{name}: ungrown bytes at '
                                        f'{addr:#x} are '
                                        f'{prefix_u[rel:rel + 4].hex()}, '
                                        f'expected stock {exp}')
                    if prefix_g[rel:rel + 4].hex() != rep:
                        failures.append(f'{name}: grown bytes at '
                                        f'{addr:#x} are '
                                        f'{prefix_g[rel:rel + 4].hex()}, '
                                        f'expected replace {rep}')
                if sorted(diffs) != sorted(expect_diffs):
                    failures.append(f'module 31 code prefix differs at '
                                    f'{len(diffs)} bytes, expected exactly '
                                    f'the 8 hook-site bytes')
                else:
                    print('module 31 code: stock prefix identical except '
                          'the two hook sites (8 bytes); tail == payload')
            else:
                if gb != ub:
                    failures.append(f'module {i} {kind} differs')
    if failures:
        for f in failures:
            print('FAIL:', f)
        return 1
    print(f'isolation holds: {len(ui.modules)} modules compared; '
          f'length {len(UNGROWN)} -> {len(GROWN)} '
          f'(+{len(GROWN) - len(UNGROWN)})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
