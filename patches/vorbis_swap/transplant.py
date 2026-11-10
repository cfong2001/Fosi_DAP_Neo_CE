#!/usr/bin/env python3
"""Module-75 Vorbis transplant, as a reusable library.

Isolates berettavexee's full-accuracy Tremor surgery from the Echo
Mini patch files and splices it into the Neo's module 75, keeping the
Neo's own runtime bytes. Used by:
  * build_image.py (standalone Vorbis-only image), and
  * patches/framework/build.py (the unified build's `vorbis75`
    transplant step).

Route and evidence: see vorbis_swap.md. Inputs are NOT in this repo
(binary, text-only push channel); DEPENDENCY.md pins their source and
SHA-256. Paths resolve through tools/fosi_paths.py — nothing here
knows where the development workspace lives.
"""
import hashlib
import os
import struct
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
import fosi_paths  # noqa: E402
from rknano_image import Image  # noqa: E402

ECHO_MOD_BASE = 0x142284          # Echo image offset of module 77 (code segment)
CODE_LEN, DATA_LEN = 62936, 53636
FREED = {'code': ((0x29D0, 0xE054),),
         'data': ((0x3480, 0x9888), (0x98A0, 0xD148))}
TRANSPLANT_NAME = 'vorbis75-full-precision'


def parse_ecpatch(path):
    """ECPATCH1 sparse binary diff -> {absolute_offset: byte}."""
    p = Path(path).read_bytes()
    assert p[:8] == b'ECPATCH1', path
    _, n = struct.unpack_from('<II', p, 72)
    m, pos = {}, 80
    for _ in range(n):
        off, ln = struct.unpack_from('<II', p, pos)
        for i, b in enumerate(p[pos + 8:pos + 8 + ln]):
            m[off + i] = b
        pos += 8 + ln
    return m


def patched_module75(stock_bytes, ecpatch_dir):
    """Return (code, data, stats) for module 75 with the surgery
    applied. Raises if any surgery byte falls outside the freed
    library regions (the splice audit from vorbis_swap.md)."""
    ecpatch_dir = Path(ecpatch_dir)
    im = Image(bytes(stock_bytes))
    co, cl = im.module_region(75, 'code')
    do, dl = im.module_region(75, 'data')
    assert (cl, dl) == (CODE_LEN, DATA_LEN), 'unexpected module 75 geometry'
    code = bytearray(stock_bytes[co:co + cl])
    data = bytearray(stock_bytes[do:do + dl])

    m52 = parse_ecpatch(ecpatch_dir / 'HIFIEC52.ecpatch')
    m56 = parse_ecpatch(ecpatch_dir / 'HIFIEC56.ecpatch')
    mod_end = ECHO_MOD_BASE + CODE_LEN + DATA_LEN
    applied = 0
    for o in sorted(set(m56) | set(m52)):
        if not (ECHO_MOD_BASE <= o < mod_end) or m56.get(o) == m52.get(o):
            continue
        mc = o - ECHO_MOD_BASE
        kind, off = ('code', mc) if mc < CODE_LEN else ('data', mc - CODE_LEN)
        assert any(a <= off < b for a, b in FREED[kind]), \
            f'surgery outside freed region: {kind} {off:#x}'
        (code if kind == 'code' else data)[off] = m56[o]
        applied += 1
    code = bytearray(_apply_rounding(bytes(code)))
    module = bytes(code) + bytes(data)
    stats = {'surgery_bytes': applied,
             'module75_sha256': hashlib.sha256(module).hexdigest(),
             'code_file_offset': co, 'data_file_offset': do}
    return bytes(code), bytes(data), stats


def _apply_rounding(code):
    """Post-step: the round-to-nearest output fix (rounding.py, a
    sibling of this file). Loaded by file location because this module
    is itself loaded by file location from the framework build. Both
    build paths (standalone and unified) call patched_module75(), so
    the fix cannot diverge between them."""
    import importlib.util
    path = Path(__file__).resolve().parent / 'rounding.py'
    spec = importlib.util.spec_from_file_location('vorbis_rounding', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.apply_rounding(code)


def apply_transplant(image_bytes, ecpatch_dir=None):
    """Framework entry point: splice the patched module 75 into an
    image byte string. Returns (new_bytes, record) where record lists
    the claimed file ranges (the full module regions — the transplant
    rewrites both segments wholesale) for disjointness checking."""
    if ecpatch_dir is None:
        ecpatch_dir = fosi_paths.ecpatch_dir(fosi_paths.repo_root(Path(__file__).parent))
    if ecpatch_dir is None:
        raise ValueError('ecpatch inputs not found; set --ecpatch-dir or '
                         'FOSI_ECPATCH_DIR (see DEPENDENCY.md)')
    code, data, stats = patched_module75(image_bytes, ecpatch_dir)
    raw = bytearray(image_bytes)
    co, do = stats['code_file_offset'], stats['data_file_offset']
    raw[co:co + len(code)] = code
    raw[do:do + len(data)] = data
    record = {'transplant': TRANSPLANT_NAME, 'module': 75,
              'surgery_bytes': stats['surgery_bytes'],
              'module75_sha256': stats['module75_sha256'],
              'ranges': [[co, co + len(code) - 1], [do, do + len(data) - 1]]}
    return bytes(raw), record
