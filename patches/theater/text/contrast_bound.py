#!/usr/bin/env python3
"""Verify a stock-palette contrast strategy for a future theater background.

Runs the V137 palette routine and the player's title-pen setup in Unicorn,
then checks a monotonic RGB565 background bound. It does not patch firmware,
prove artwork buffer geometry, or validate antialiasing or device behavior.
"""
import hashlib
import math
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_SP

raw = Path(os.environ.get('FOSI_STOCK_IMAGE', ROOT / 'DP3_V137.img')).read_bytes()
if hashlib.sha256(raw).hexdigest() != 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef':
    raise ValueError('stock image SHA-256 mismatch')
im = Image(raw)


def stock_title_pen(theme):
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    for i in (0, 27):
        off, size = im.module_region(i, 'code')
        u.mem_write(im.modules[i]['code_exec'], raw[off:off + size])
    u.mem_write(0x030232a0 + 0x2d8, bytes([theme]))
    u.reg_write(UC_ARM_REG_SP, 0x030f0000)
    u.reg_write(UC_ARM_REG_LR, 0x030ef001)
    u.emu_start(0x030655bd, 0x030ef000, count=100)
    palette_word = struct.unpack('<H', u.mem_read(0x030235b6, 2))[0]
    # Execute only the player's pen setup, stopping before the title draw.
    u.emu_start(0x0307fa65, 0x0307fa78, count=100)
    pen_word = struct.unpack('<H', u.mem_read(0x0302385c, 2))[0]
    return palette_word, pen_word


def quantized(v, bits):
    scale = (1 << bits) - 1
    return ((v * scale + 127) // 255) * 255 // scale


def linear(v):
    v /= 255
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    return sum(c * linear(v) for c, v in zip((0.2126, 0.7152, 0.0722), rgb))


def main():
    assert stock_title_pen(0) == (0xffff, 0xffff)
    assert stock_title_pen(1) == (0, 0)
    # Integer rounding of channel * .45 for dark and channel * .25 plus
    # .75 of each proposed paper channel for light. RGB565 conversion is
    # monotonic per channel. Therefore the
    # all-white source is the highest-luminance possible dark ground, while
    # the all-black source is the lowest-luminance possible light ground.
    def dark(v): return (45 * v + 50) // 100
    def light(v, paper): return (25 * v + 75 * paper + 50) // 100
    for bits in (5, 6):
        for mix in (dark, lambda v: light(v, 255),
                    lambda v: light(v, 242), lambda v: light(v, 237),
                    lambda v: light(v, 230)):
            values = [quantized(mix(v), bits) for v in range(256)]
            assert values == sorted(values)
    max_dark = [quantized(dark(255), bits) for bits in (5, 6, 5)]
    min_light = [quantized(light(0, 255), bits) for bits in (5, 6, 5)]
    min_paper = [quantized(light(0, paper), bits)
                 for paper, bits in zip((242, 237, 230), (5, 6, 5))]
    dark_ratio = 1.05 / (luminance(max_dark) + 0.05)
    light_ratio = (luminance(min_light) + 0.05) / 0.05
    paper_ratio = (luminance(min_paper) + 0.05) / 0.05
    assert math.isfinite(dark_ratio) and dark_ratio >= 4.5
    assert math.isfinite(light_ratio) and light_ratio >= 4.5
    assert math.isfinite(paper_ratio) and paper_ratio >= 4.5
    print(f'PASS: stock title pen white/black; worst dark {max_dark} {dark_ratio:.2f}:1, '
          f'worst light/white {min_light} {light_ratio:.2f}:1, '
          f'light/paper {min_paper} {paper_ratio:.2f}:1')


if __name__ == '__main__':
    main()
