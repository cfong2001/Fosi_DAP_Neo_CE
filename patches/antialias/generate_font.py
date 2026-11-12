#!/usr/bin/env python3
"""Redrawn 1-bit Latin glyphs for Font B, the 8x16 list and menu font.

The firmware draws text from 1-bit glyph records, so text cannot carry
antialiasing. What can change, as data alone, is the bitmaps. This
redraws Font B's Latin glyphs from Barlow SemiBold (the site's typeface,
vendored in docs/fonts) at 16 px, rasterised by FreeType with hinting
in 1-bit mode. The result is 2-pixel stems, even spacing and a cap
height of 11. Scripts other than Latin keep their stock glyphs.

Record layout (font_b, stock file offset 0x371726, 33 bytes per code
point): 16 rows of 16 bits, MSB first, then a tail byte. The measurer at
0x030627BE gives the advance:

  * ASCII letters: from the ink, by 0x03063E06 (leftmost + rightmost
    inked column + 2 over the top 10 rows). Glyphs are placed with
    their ink starting at column 0, so the advance is width + 1. A
    letter wider below row 9 than above it (A, z) is shifted right
    until that measure clears its ink.
  * Everything else: tail - 0x80 when the tail is above 0x80. Each
    redrawn glyph gets an explicit tail: width + 1; the space 4;
    . , : ; ! ? one extra column on each side; digits one tabular
    width so counters do not shift.

The baseline is row 12, one row above stock, so descenders get rows 13
to 15. Marks on capitals that would rise above row 0 are seated in the
rows above the cap, as the stock font does (seat_mark). A glyph whose
ink still leaves the 16 x 16 cell keeps its stock record (listed when
the generator runs).

Output: font-glyphs.json (theme runs at stock offsets, merged by
patches/full/build/build_theme.py) and mock/font_before_after.png.
Run from the repository root.
"""
import hashlib
import json
import unicodedata
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
FONT_B, STRIDE, ROWS = 0x371726, 33, 16
BASELINE = 12
FACE = ROOT / 'docs' / 'fonts' / 'Barlow-SemiBold.ttf'
SIZE = 16
SPACE = 4

CODEPOINTS = ([c for c in range(0x21, 0x7F)] +
              [c for c in range(0xA1, 0x100) if c != 0xAD] +
              list(range(0x100, 0x180)))


def ascii_letter(cp):
    return 0x41 <= cp <= 0x5A or 0x61 <= cp <= 0x7A


def raster(font, ch):
    """Ink as a set of (x, y) in cell coordinates, x shifted so the
    leftmost ink is column 0. None if the glyph has no ink."""
    im = Image.new('1', (48, 40), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    d.text((8, 8 + BASELINE + 1), ch, font=font, fill=1, anchor='ls')
    ink = [(x, y - 8) for y in range(40) for x in range(48) if im.getpixel((x, y))]
    if not ink:
        return None
    x0 = min(x for x, _ in ink)
    return {(x - x0, y) for x, y in ink}


def seat_mark(font, cp, ink):
    """Fit a glyph whose mark rises above the cell. The mark is the ink
    above the base letter's top row; its empty rows are dropped and it
    sits one row above the base (or touching it, if one row is all the
    room there is), keeping its bottom rows if it is still too tall.
    This is how the stock font fits Ä and É into 16 rows."""
    base = unicodedata.normalize('NFD', chr(cp))[0]
    if base == chr(cp):
        return None
    body = raster(font, base)
    if body is None:
        return None
    top = min(y for _, y in body)
    mark = sorted({y for _, y in ink if y < top})
    rest = {(x, y) for x, y in ink if y >= top}
    if not mark or any(y >= ROWS for _, y in rest):
        return None
    room = top
    gap = 1 if len(mark) <= room - 1 else 0
    keep = mark[-(room - gap):] if room - gap > 0 else []
    if not keep:
        return None
    first = top - gap - len(keep)
    remap = {y: first + i for i, y in enumerate(keep)}
    return rest | {(x, remap[y]) for x, y in ink if y in remap}


def record(ink, tail):
    rows = [0] * ROWS
    for x, y in ink:
        rows[y] |= 0x8000 >> x
    return b''.join(r.to_bytes(2, 'big') for r in rows) + bytes([tail])


def build():
    raw = (ROOT / 'DP3_V137.img').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == STOCK_SHA, 'stock SHA gate'
    font = ImageFont.truetype(str(FACE), SIZE)
    glyphs, skipped = {}, []
    inks = {cp: raster(font, chr(cp)) for cp in CODEPOINTS}
    digit_w = max(max(x for x, _ in inks[c]) + 1 for c in range(0x30, 0x3A))
    for cp, ink in inks.items():
        if ink is None:
            skipped.append((cp, 'no ink'))
            continue
        if any(y < 0 for _, y in ink):
            ink = seat_mark(font, cp, ink) or ink
        if any(not (0 <= x < 16 and 0 <= y < ROWS) for x, y in ink):
            skipped.append((cp, 'leaves the cell'))
            continue
        w = max(x for x, _ in ink) + 1
        if 0x30 <= cp <= 0x39:
            pad = (digit_w - w) // 2
            ink = {(x + pad, y) for x, y in ink}
            adv = digit_w + 1
        elif chr(cp) in '.,:;!?':
            ink = {(x + 1, y) for x, y in ink}      # one column each side
            adv = w + 3
        else:
            adv = w + 1
        if ascii_letter(cp):
            # The firmware measures letters over rows 0 to 9 only. A
            # letter that is wider below row 9 (A, z) would touch the
            # next one, so shift it right until the measured advance
            # leaves a clear column after the ink.
            if cp == 0x4C:
                # L: nothing of the bar is in rows 0 to 9, so the measure
                # sees only the stem. Stock lives with a 5-column overlap
                # into the next letter. Here the bar is trimmed to 6
                # columns and the glyph shifted until it clears.
                ink = {(x, y) for x, y in ink if x < 6}
            for k in range(8):
                shifted = {(x + k, y) for x, y in ink}
                top = [x for x, y in shifted if y < 10]
                if top and min(top) + max(top) + 2 >= max(x for x, _ in shifted) + 2:
                    ink = shifted
                    break
        stock_rec = raw[FONT_B + cp * STRIDE:FONT_B + (cp + 1) * STRIDE]
        tail = stock_rec[32] if ascii_letter(cp) else 0x80 + adv
        glyphs[cp] = record(ink, tail)
    space = bytearray(raw[FONT_B + 0x20 * STRIDE:FONT_B + 0x21 * STRIDE])
    space[32] = 0x80 + SPACE
    glyphs[0x20] = bytes(space)
    return raw, glyphs, skipped


def runs(raw, glyphs):
    out = []
    for cp in sorted(glyphs):
        off = FONT_B + cp * STRIDE
        old, new = raw[off:off + STRIDE], glyphs[cp]
        diff = [i for i in range(STRIDE) if old[i] != new[i]]
        if not diff:
            continue
        a, b = diff[0], diff[-1] + 1
        out.append({'offset': f'{off + a:#x}', 'expect': old[a:b].hex(),
                    'replace': new[a:b].hex()})
    return out


def advance(rec, cp):
    """The firmware's advance for a large-font record (0x030627BE)."""
    tail = rec[32]
    if ascii_letter(cp):
        cols = [x for y in range(10) for x in range(16)
                if int.from_bytes(rec[2 * y:2 * y + 2], 'big') & (0x8000 >> x)]
        return (min(cols) + max(cols) + 2) if cols else 0
    if tail == 0x20:
        return 16
    if tail > 0x80:
        return tail - 0x80
    if tail == 0x80 and cp >= 0x7F:
        return 16
    return 8


def sheet(raw, glyphs, path):
    lines = ['Flamenco Sketches.flac', 'Café del Mar  0123456789',
             'Ölgemälde, Dvořák, Łódź  gjpqy', 'Settings  Playback order  3:49']
    z = 3

    def render(get):
        im = Image.new('RGB', (240, 22 * len(lines) + 6), (0, 0, 0))
        for i, s in enumerate(lines):
            x = 6
            for ch in s:
                cp = ord(ch)
                rec = get(cp)
                for y in range(ROWS):
                    row = int.from_bytes(rec[2 * y:2 * y + 2], 'big')
                    for gx in range(16):
                        if row & (0x8000 >> gx) and x + gx < 240:
                            im.putpixel((x + gx, 4 + 22 * i + y), (255, 255, 255))
                x += advance(rec, cp)
        return im.resize((240 * z, im.height * z), Image.NEAREST)

    stock = render(lambda cp: raw[FONT_B + cp * STRIDE:FONT_B + (cp + 1) * STRIDE])
    new = render(lambda cp: glyphs.get(cp, raw[FONT_B + cp * STRIDE:FONT_B + (cp + 1) * STRIDE]))
    out = Image.new('RGB', (stock.width, stock.height * 2 + 8), (128, 128, 128))
    out.paste(stock, (0, 0))
    out.paste(new, (0, stock.height + 8))
    path.parent.mkdir(exist_ok=True)
    out.save(path)


def main():
    raw, glyphs, skipped = build()
    rs = runs(raw, glyphs)
    (HERE / 'font-glyphs.json').write_text(
        json.dumps({'version': 1, 'runs': rs}, indent=1) + '\n')
    sheet(raw, glyphs, HERE / 'mock' / 'font_before_after.png')
    print(f'{len(glyphs)} glyph records, {len(rs)} runs; kept stock: '
          + ', '.join(f'U+{cp:04X} ({why})' for cp, why in skipped))


if __name__ == '__main__':
    sys.exit(main())
