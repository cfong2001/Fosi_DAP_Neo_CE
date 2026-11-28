#!/usr/bin/env python3
"""Answer main-font glyph widths from a table in code instead of flash.

0x030627BE returns a character's advance. For the main font (class 0) it
reads the character's 34-byte record from flash at font base + 33 x code
and derives the width from the record's width code. Measuring a string
calls it once per character, and drawing calls it again, so in one
browser wheel step 49 of 55 flash reads come from this routine.

The width is fixed by the record, the code and two state checks: the
font class (context +0x24; class 1 is the 12-pixel font with 32-byte
records) and the byte at 0x030232B0, which selects a special case when it
is 8 or 10. Classes 0 and 2 share the 33-byte path and differ only in
which cell (0x03023270 or 0x03023274) the base comes from; the browser
uses class 2. This patch answers from a table when the class is not 1, the font base cell (0x03023280) holds Font B's header
offset minus 1, that byte is neither 8 nor 10, and the code is below 0x180
(ASCII, Latin-1 and Latin Extended-A). Every other call runs the stock
routine. The table is generated here by running the routine itself in
emulation for each code, reading the image's Font B (the 16 x 16 main
font; Font A is the 12-pixel class).

The code follows the system-disk cache (0290) in the same unreached
stock routine at 0x0306D450.
"""
from pathlib import Path
import hashlib
import struct
import sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_SP

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
WIDTH = 0x030627BE
RESUME = 0x030627C2
COPY = 0x03064314            # (source, destination, length) flash read
CTX, FONT_CELL, STATE = 0x0302385C, 0x03023280, 0x030232A0
CODES = 0x180
HOME, HOME_END = 0x0306D4BC, 0x0306D734   # after patch 0290's 108 bytes


def font_base(raw):
    """The font base cell's value for Font B, the 16 x 16 main font.

    Both the glyph routine and 0x030627BE read 34 bytes at cell + 33 x code
    and take rows from bytes 1 to 32 and the tail from byte 33, so the cell
    holds the header's Font B offset (0x80) minus 1. CE's redrawn records,
    written at the header offset, measure and draw correctly on hardware
    under that reading. If the cell holds anything else, the check fails
    and the stock routine runs.
    """
    return struct.unpack_from('<I', raw, 0x80)[0] - 1


def width_runner(raw):
    """Return f(code) that runs 0x030627BE from this image with class 0, Font B, state byte 0."""
    image = Image(raw)
    m = image.modules[0]
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    uc.mem_map(0x03000000, 0x100000)
    for kind, at in (('code', m['code_exec']), ('data', m['data_exec'])):
        offset, size = image.module_region(0, kind)
        uc.mem_write(at, raw[offset:offset + size])
    uc.mem_write(0x030FFF00, b'\xfe\xe7')
    uc.mem_write(CTX + 0x24, b'\0\0')
    uc.mem_write(FONT_CELL, struct.pack('<I', font_base(raw)))
    uc.mem_write(STATE + 0x10, b'\0')

    def hook(u, address, size, _):
        if address == 0x030FFF00:
            u.emu_stop()
        elif address == COPY:
            src, dst, n = (u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
            u.mem_write(dst, raw[src:src + n])
            u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))
    uc.hook_add(UC_HOOK_CODE, hook)

    def width(code, entry=WIDTH):
        uc.reg_write(UC_ARM_REG_R0, code)
        uc.reg_write(UC_ARM_REG_SP, 0x030F0000)
        uc.reg_write(UC_ARM_REG_LR, 0x030FFF01)
        uc.emu_start(entry | 1, 0x030FFF00, count=20000)
        return uc.reg_read(UC_ARM_REG_R0)
    return width


def table(raw):
    width = width_runner(raw)
    values = [width(code) for code in range(CODES)]
    assert all(v < 256 for v in values), max(values)
    return bytes(values)


def code(base, widths):
    source = f"""
    cmp.w r0, #{CODES:#x}
    bhs slow
    ldr r1, ={CTX:#x}
    ldrh r1, [r1, #0x24]
    cmp r1, #1
    beq slow
    ldr r1, ={FONT_CELL:#x}
    ldr r1, [r1]
    ldr r2, ={base:#x}
    cmp r1, r2
    bne slow
    ldr r1, ={STATE:#x}
    ldrb r1, [r1, #0x10]
    cmp r1, #8
    beq slow
    cmp r1, #10
    beq slow
    adr r1, widths
    ldrb r0, [r1, r0]
    bx lr
slow:
    push {{r4, r5, r6, lr}}
    mov r5, r0
    b.w {RESUME:#x}
    .ltorg
    .align 2
widths:
"""
    body, _ = Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(source, HOME)
    out = bytes(body) + widths
    assert HOME + len(out) <= HOME_END, len(out)
    return out


def entry_patch():
    body, _ = Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(f'b.w {HOME:#x}', WIDTH)
    return bytes(body)


def main():
    stock = (ROOT / 'DP3_V137.img').read_bytes()
    assert hashlib.sha256(stock).hexdigest() == STOCK_SHA
    # The table comes from the composed image, which carries CE's own width
    # rules (patch 0191), the redrawn fonts and the grown section offsets. Build from the release image
    # before this patch is added, or from any later image: the routine's
    # body after the entry is unchanged by this patch.
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'release/DP3_V137_CE.img'
    raw = source.read_bytes()
    image = Image(raw)
    offset, _ = image.module_region(0, 'code')
    base0 = image.modules[0]['code_exec']
    assert raw[offset + WIDTH - base0:offset + WIDTH - base0 + 4] == bytes.fromhex('70b50546'), \
        'build the table from an image without this patch'
    widths = table(raw)
    cave = code(font_base(raw), widths)
    soff, _ = Image(stock).module_region(0, 'code')
    sbase = Image(stock).modules[0]['code_exec']
    for name, address, blob, why in (
            ('0295-glyph-width-table', HOME, cave,
             'Width table and check in the unreached stock routine at 0x0306D450, after patch 0290.'),
            ('0296-glyph-width-hook', WIDTH, entry_patch(),
             'Enter the table check; it resumes the stock prologue for every other call.')):
        expect = stock[soff + address - sbase:soff + address - sbase + len(blob)]
        (HERE / (name + '.patch')).write_text(
            '# Generated by build_glyph_width.py.\n'
            f'name: {name}\nkind: module\nmodule: 0\nregion: code\naddress: {address:#x}\n'
            'gate: pinned stock bytes; width parity for every table code in test_glyph_width.py\n'
            f'expect: {expect.hex()}\nreplace: {blob.hex()}\nrationale: {why}\n')
        print(f'{name}: {len(blob)} bytes at {address:#x}')
    print('distinct widths:', sorted(set(widths)))


if __name__ == '__main__':
    main()
