#!/usr/bin/env python3
"""Build the control variant of the Opus transplant: the HIFIEC52 diff
applied to the stock module 72 bytes WITHOUT transplant.py's zero-first
step.

transplant.py zeroes the freed code and data regions and then writes
only the bytes listed in the ECPATCH. The ECPATCH is a sparse diff
against the Echo stock module, so every byte where the plug-in equals
Echo stock is absent from it and ends up 0x00 in the candidate. This
script isolates that single difference: same diff, same regions, no
zeroing. It exists as diagnostics for the harness validation in
results.md, not as a build tool.

Usage: build_control.py [stock_image] [ecpatch] [out]
Defaults resolve inside the local tree (DP3_V137.img at the repo root,
refs/echo-mini-opus/patch/HIFIEC52.ecpatch, module72_opus_onstock.bin
written next to this script).
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]                      # ~/workspace/fosi-dap-neo
sys.path.insert(0, str(WS))
sys.path.insert(0, str(WS / 'work/opus_transplant'))

import transplant as T                    # noqa: E402  (sets up the tools path)
from rknano_image import Image           # noqa: E402


def main():
    img_path = Path(sys.argv[1]) if len(sys.argv) > 1 else WS / 'DP3_V137.img'
    ecp_path = Path(sys.argv[2]) if len(sys.argv) > 2 else \
        WS / 'refs/echo-mini-opus/patch/HIFIEC52.ecpatch'
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else HERE / 'module72_opus_onstock.bin'
    stock = img_path.read_bytes()
    im = Image(bytes(stock))
    co, cl = im.module_region(72, 'code')
    do, dl = im.module_region(72, 'data')
    assert (cl, dl) == (T.CODE_LEN, T.DATA_LEN), (cl, dl)
    code = bytearray(stock[co:co + cl])
    data = bytearray(stock[do:do + dl])
    diff = T.parse_ecpatch(ecp_path)
    applied = 0
    for o in sorted(diff):
        if not (T.ECHO_MOD74_BASE <= o < T.ECHO_MOD74_BASE + T.CODE_LEN + T.DATA_LEN):
            continue
        mc = o - T.ECHO_MOD74_BASE
        kind, off = ('code', mc) if mc < T.CODE_LEN else ('data', mc - T.CODE_LEN)
        assert T._in(T.FREED_CODE if kind == 'code' else T.FREED_DATA, off), hex(off)
        (code if kind == 'code' else data)[off] = diff[o]
        applied += 1
    blob = bytes(code) + bytes(data)
    out_path.write_bytes(blob)
    print(f'applied {applied} diff bytes, no zeroing')
    print(f'wrote {out_path} ({len(blob)} bytes)')
    print('sha256:', hashlib.sha256(blob).hexdigest())


if __name__ == '__main__':
    main()
