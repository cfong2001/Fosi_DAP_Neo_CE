#!/usr/bin/env python3
"""Build the standalone Vorbis-only image: stock DP3_V137 + the
full-precision Tremor module 75 (transplant.py), dated 2026-10-23.

The unified build (patches/framework/build.py) produces this same
module as its `vorbis75` transplant step, alongside the DAC and clock
patches; this script remains for building/comparing the Vorbis change
in isolation. Expected output SHA-256 (pinned in DEPENDENCY.md):
aed16842d8daa569d06efdc18cd9e7eb298a0129fd38fdb2cdabaa7ec72cd10a

Paths resolve through tools/fosi_paths.py: --stock / FOSI_STOCK_IMAGE,
--ecpatch-dir / FOSI_ECPATCH_DIR, FOSI_REPO_ROOT. Nothing is hard-coded
to a development workspace.
"""
import argparse
import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import transplant  # noqa: E402  (bootstraps the repo tools path itself)
import fosi_paths  # noqa: E402
from rknano_image import Image, rk_crc32  # noqa: E402
from firmware_patch import validate, bcd_date, STOCK_SHA256  # noqa: E402

DATE = '20261023'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stock', type=Path, default=None,
                    help='stock image (default: FOSI_STOCK_IMAGE or discovery)')
    ap.add_argument('--ecpatch-dir', type=Path, default=None,
                    help='.ecpatch inputs (default: FOSI_ECPATCH_DIR or discovery)')
    ap.add_argument('--out', type=Path, default=Path('DP3_V137_vorbis.img'),
                    help='output image (written to the current directory)')
    ap.add_argument('--date', default=DATE, help='BCD header date YYYYMMDD')
    a = ap.parse_args()

    repo = fosi_paths.repo_root(Path(__file__).parent)
    stock_path = fosi_paths.stock_image_path(repo, a.stock)
    ecpatch_dir = fosi_paths.ecpatch_dir(repo, a.ecpatch_dir)
    if ecpatch_dir is None:
        ap.error('ecpatch inputs not found; pass --ecpatch-dir or set '
                 'FOSI_ECPATCH_DIR (see DEPENDENCY.md)')

    raw = bytearray(stock_path.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == STOCK_SHA256, 'not the pinned stock image'
    im = Image(bytes(raw))
    out_bytes, rec = transplant.apply_transplant(bytes(raw), ecpatch_dir)
    raw = bytearray(out_bytes)
    raw[:4] = bcd_date(a.date)
    fw_len = im.u32(0x1F4)
    raw[fw_len:fw_len + 0x200] = raw[:0x200]                       # header mirror
    struct.pack_into('<I', raw, len(raw) - 4, rk_crc32(bytes(raw[:-4])))
    out = bytes(raw)
    validate(out)                                                  # layout + mirror + CRC
    a.out.write_bytes(out)
    print(f'wrote {a.out}: sha256 {hashlib.sha256(out).hexdigest()}')
    print(f"transplant: {rec['transplant']} "
          f"({rec['surgery_bytes']} surgery bytes, "
          f"module75 sha256 {rec['module75_sha256'][:16]}…)")
    # diff confinement check vs stock
    stock = stock_path.read_bytes()
    co, cl = im.module_region(75, 'code')
    do, dl = im.module_region(75, 'data')
    diff = [i for i in range(len(out)) if out[i] != stock[i]]
    allowed = set(range(co, co + cl)) | set(range(do, do + dl)) | set(range(4)) \
        | set(range(fw_len, fw_len + 4)) | set(range(len(out) - 4, len(out)))
    bad = [i for i in diff if i not in allowed]
    print(f'diff bytes vs stock: {len(diff)}; outside module75/date/crc: {len(bad)}')
    assert not bad
    return 0


if __name__ == '__main__':
    sys.exit(main())
