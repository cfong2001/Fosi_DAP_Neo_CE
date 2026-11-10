#!/usr/bin/env python3
"""Module-72 WMA-to-Opus transplant, as a reusable library.

Replaces the stock WMA decoder library inside Neo module 72 with
berettavexee's Opus plug-in (fixed-point libopus 1.5.2 plus a minimal
Ogg demuxer), keeping the Neo module's own runtime byte for byte.
Written against the framework transplant interface, same shape as
patches/vorbis_swap/transplant.py: drop this file into
patches/opus_swap/ and register 'opus72' in build.py's
TRANSPLANT_MODULES to use it from the unified build.

Why a splice works here (evidence: route.md in this directory):
Neo module 72 and the Echo Mini's module 74 are the same SDK build
of the WMA decoder module. Geometry is identical (code 0x162C0,
data 0x67C0, total 117,376 bytes) and every runtime landmark the
plug-in depends on sits at the same offset in both modules
(CodecFunc table and slot, FILE_OPS table, BSS base and clear
length, info block, runtime event-flag array). The plug-in was
linked into the WMA library's freed regions at those same offsets,
so its bytes rebase onto module 72 unchanged.

Method: write the surgery bytes isolated from HIFIEC52.ecpatch
onto a copy of the stock module, erasing nothing first.
HIFIEC52 is the Opus-only patch (the Vorbis surgery lives in
HIFIEC56 and is not in 52), so every byte it changes inside the
Echo module 74 file range is an Opus plug-in byte. The audit
refuses if any surgery byte falls outside the freed regions.

Why nothing is erased: an ECPATCH is a sparse diff against the
Echo stock module, so a byte where the plug-in's output equals
the Echo stock byte is absent from the diff. berettavexee's
rknanofw.py patch-opus erases the freed regions before writing
because it writes the complete plug-in ELF sections,
coincident bytes included; a diff-based construction has to
take the coincident bytes from the stock module underneath.
That works because the Neo and Echo stock modules are the same
SDK build: a byte the plug-in shares with Echo stock is, at
the same offset, the byte already present in Neo stock. The
first version of this tool erased the freed regions and then
wrote only the diff, zeroing 630 bytes the plug-in shares with
the stock library; the result faulted on open, and offline
harness validation caught it before the candidate shipped.
The corrected construction here reproduces the harness control
build byte for byte.

Inputs are NOT in this repo (binary, text-only push channel). The
.ecpatch source and its SHA-256 are pinned in DEPENDENCY.md terms
by the vorbis swap: berettavexee/echo-mini-opus commit
7d727fd4f30e68fecbf6566d3c3e64213e56e7f7, patch/HIFIEC52.ecpatch
SHA-256 acad5a624aacdceb3868a118b56959260f08ee9600ac5378d9f516e0872ccd03.
The hash is re-checked here on every run.

Licences: project surgery BSD-3-Clause (berettavexee); libopus
(C) Xiph.Org Foundation and contributors, BSD-style.
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

# Neo module 72 geometry (stock image, module_region-verified).
CODE_LEN, DATA_LEN = 0x162C0, 0x67C0
# Echo Mini module 74 file range inside the HIFIEC images: load
# 0x031537C0..0x03170240, file offset = load - 0x03050000 + 0x200
# (berettavexee REPORT.md section 2, codec_abi.h memory map).
ECHO_MOD74_BASE = 0x1039C0
# Regions the WMA library owned and the plug-in may occupy
# (berettavexee REPORT.md section 9, reach74.py call-graph walk;
# the kept hole 0x12800..0x12858 is runtime printf data).
FREED_CODE = ((0x2EC4, 0x10138), (0x110A4, 0x12800), (0x12858, 0x162C0))
FREED_DATA = ((0x3480, 0x67C0),)
CODECFUNC_SLOT_DATA_OFF = 0x347C   # CodecFunc[1], address 0x0102347C
CODECFUNC_EXPECT = 0x2EC5          # OpusCodec entry 0x2EC4 + Thumb bit
ECPATCH_NAME = 'HIFIEC52.ecpatch'
ECPATCH_SHA256 = 'acad5a624aacdceb3868a118b56959260f08ee9600ac5378d9f516e0872ccd03'
TRANSPLANT_NAME = 'opus72-wma-replacement'


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


def _in(ranges, off):
    return any(a <= off < b for a, b in ranges)


def patched_module72(stock_bytes, ecpatch_dir):
    """Return (code, data, stats) for module 72 with the WMA library
    replaced by the Opus plug-in. Raises on any audit failure."""
    ecpatch_dir = Path(ecpatch_dir)
    ep_path = ecpatch_dir / ECPATCH_NAME
    digest = hashlib.sha256(ep_path.read_bytes()).hexdigest()
    assert digest == ECPATCH_SHA256, \
        f'{ECPATCH_NAME} hash mismatch: {digest} (see DEPENDENCY pin)'

    im = Image(bytes(stock_bytes))
    co, cl = im.module_region(72, 'code')
    do, dl = im.module_region(72, 'data')
    assert (cl, dl) == (CODE_LEN, DATA_LEN), 'unexpected module 72 geometry'
    code = bytearray(stock_bytes[co:co + cl])
    data = bytearray(stock_bytes[do:do + dl])
    stock_code, stock_data = bytes(code), bytes(data)

    # The runtime entry the system already points at: the plug-in's
    # OpusCodec is linked at the same address as the WMA entry, so
    # the stock CodecFunc[1] word stays correct untouched.
    slot = struct.unpack_from('<I', data, CODECFUNC_SLOT_DATA_OFF)[0]
    assert slot == CODECFUNC_EXPECT, \
        f'CodecFunc[1] is {slot:#x}, expected {CODECFUNC_EXPECT:#x}'

    # Write the surgery bytes isolated from HIFIEC52 onto the
    # stock bytes. Nothing is erased first: the diff is sparse,
    # so bytes the plug-in shares with the Echo stock library
    # are absent from it and must come from the Neo stock bytes
    # underneath (same SDK build, same offsets; see docstring).
    m = parse_ecpatch(ep_path)
    applied = 0
    for o in sorted(m):
        if not (ECHO_MOD74_BASE <= o < ECHO_MOD74_BASE + CODE_LEN + DATA_LEN):
            continue
        mc = o - ECHO_MOD74_BASE
        kind, off = ('code', mc) if mc < CODE_LEN else ('data', mc - CODE_LEN)
        assert _in(FREED_CODE if kind == 'code' else FREED_DATA, off), \
            f'surgery outside freed region: {kind} {off:#x}'
        (code if kind == 'code' else data)[off] = m[o]
        applied += 1
    assert applied > 0, 'no surgery bytes found in the module range'

    # Kept-region audit: outside the freed regions the module must
    # remain byte-identical to stock (the runtime is the contract).
    for i in range(CODE_LEN):
        if not _in(FREED_CODE, i):
            assert code[i] == stock_code[i], f'kept code byte changed at {i:#x}'
    for i in range(DATA_LEN):
        if not _in(FREED_DATA, i):
            assert data[i] == stock_data[i], f'kept data byte changed at {i:#x}'
    slot = struct.unpack_from('<I', data, CODECFUNC_SLOT_DATA_OFF)[0]
    assert slot == CODECFUNC_EXPECT, 'CodecFunc[1] changed'

    module = bytes(code) + bytes(data)
    stats = {'surgery_bytes': applied,
             'module72_sha256': hashlib.sha256(module).hexdigest(),
             'module72_len': len(module),
             'code_file_offset': co, 'data_file_offset': do}
    return bytes(code), bytes(data), stats


def apply_transplant(image_bytes, ecpatch_dir=None):
    """Framework entry point: splice the patched module 72 into an
    image byte string. Returns (new_bytes, record) where record
    lists the claimed file ranges (the full module regions, as in
    the vorbis transplant) for disjointness checking."""
    if ecpatch_dir is None:
        ecpatch_dir = fosi_paths.ecpatch_dir(fosi_paths.repo_root(Path(__file__).parent))
    if ecpatch_dir is None:
        raise ValueError('ecpatch inputs not found; set --ecpatch-dir or '
                         'FOSI_ECPATCH_DIR (see DEPENDENCY.md)')
    code, data, stats = patched_module72(image_bytes, ecpatch_dir)
    raw = bytearray(image_bytes)
    co, do = stats['code_file_offset'], stats['data_file_offset']
    raw[co:co + len(code)] = code
    raw[do:do + len(data)] = data
    record = {'transplant': TRANSPLANT_NAME, 'module': 72,
              'surgery_bytes': stats['surgery_bytes'],
              'module72_sha256': stats['module72_sha256'],
              'ranges': [[co, co + len(code) - 1], [do, do + len(data) - 1]]}
    return bytes(raw), record


if __name__ == '__main__':
    img = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        Path(__file__).resolve().parents[2] / 'DP3_V137.img'
    epd = Path(sys.argv[2]) if len(sys.argv) > 2 else \
        Path(__file__).resolve().parents[2] / 'refs' / 'echo-mini-opus' / 'patch'
    stock = img.read_bytes()
    print('stock sha256:', hashlib.sha256(stock).hexdigest())
    code, data, st = patched_module72(stock, epd)
    out = Path(__file__).resolve().parent / 'module72_opus.bin'
    out.write_bytes(code + data)
    print('surgery bytes applied:', st['surgery_bytes'])
    print('module72_opus.bin len:', st['module72_len'])
    print('module72_opus.bin sha256:', st['module72_sha256'])
    print('written:', out)
