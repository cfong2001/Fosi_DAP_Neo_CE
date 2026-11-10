#!/usr/bin/env python3
"""Layout-generalized sibling of repo/tools/firmware_patch.py validate().

firmware_patch.validate() pins two stock-layout constants: total length
0xD00004 and duplicate-header offset 0xC94000. Any correctly rebuilt image
with an inserted segment (build.py --grow) violates both by construction,
so validate() refuses it at that check even though every structural
property validate() exists to protect (header mirror, trailer CRC, module
table, sections in bounds) holds. This module keeps every structural
check and derives the length expectations from the image itself. The
stock validator remains the gate for ungrown builds; this one is used
only when a build applied growths.

Demonstrated first in the insertion-rebuild workstream
(patches/framework/tools/insert_rebuild.py; analysis in
work/insert_tool/insert_tool.md) and cross-checked there against
nanitecfw's independent parser.
"""
import os
import sys
from pathlib import Path


def _tools_dir():
    here = Path(__file__).resolve()
    roots = [Path(os.environ['FOSI_REPO_ROOT'])] if os.environ.get('FOSI_REPO_ROOT') else []
    roots += [here.parent, *here.parents]
    for r in roots:
        for cand in (r / 'tools', r / 'repo' / 'tools'):
            if (cand / 'firmware_patch.py').exists():
                return cand
    raise SystemExit('cannot locate repo tools/ (set FOSI_REPO_ROOT)')


sys.path.insert(0, str(_tools_dir()))

from rknano_image import Image  # noqa: E402


def validate_grown(raw):
    im = Image(raw)
    info = im.summary()
    if not info['header_mirror_valid'] or not info['crc_valid']:
        raise ValueError('header mirror or trailer CRC failed')
    fw_len = im.u32(0x1F4)
    if fw_len + 0x200 > len(raw) - 4:
        raise ValueError('duplicate header offset outside image')
    if len(im.modules) != 82:
        raise ValueError('module count is not 82')
    for m in im.modules:
        for kind in ('code', 'data'):
            im.module_region(m['index'], kind)  # raises if outside image
    return im


if __name__ == '__main__':
    raw = Path(sys.argv[1]).read_bytes()
    validate_grown(raw)
    print(f'{sys.argv[1]}: validate_grown passed ({len(raw)} bytes)')
