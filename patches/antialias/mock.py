#!/usr/bin/env python3
"""Before/after mockups for antialiased text and icons on the player.

Nothing here touches firmware. It renders two 240x320 screens (the
theater now-playing screen and a dark file list) three ways and writes a
comparison sheet:

  today      the device's 1-bit font glyphs (read from DP3_V137.img) and
             the v4 transport glyphs as shipped (thresholded at half
             coverage, so every pixel is ink or ground);
  smoothing  the same 1-bit glyphs with half-tone pixels added at the
             inside corners of diagonal steps (what a blitter change
             could do with the existing fonts), and the v4 glyphs
             antialiased from their 8x supersampled coverage;
  true AA    Latin text from a grayscale font at 16 coverage levels
             (DejaVu Sans here, standing in for whatever font would
             ship), other scripts still 1-bit, plus antialiased glyphs.

Every output pixel is quantized to RGB565, the panel's format, after
blending against the ground. Run from the repo root:

    python patches/antialias/mock.py   ->  patches/antialias/mock/*.png
"""
import hashlib
import importlib.util
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'mock'
STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
FONT_SMALL, FONT_LARGE = 0x16FB20, 0x371726      # 6x12 (stride 32), 8x16 (33)
DEJAVU = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
DEJAVU_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

spec = importlib.util.spec_from_file_location(
    'glyphs', ROOT / 'patches' / 'design_refresh_v4' / 'generate_glyphs.py')
glyphs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(glyphs)

RAW = (ROOT / 'DP3_V137.img').read_bytes()
assert hashlib.sha256(RAW).hexdigest() == STOCK_SHA, 'stock SHA gate'


def rgb565(c):
    r, g, b = c
    v = (r >> 3) << 11 | (g >> 2) << 5 | b >> 3
    return ((v >> 11) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31)


def from565(v):
    return ((v >> 11) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31)


class Screen:
    def __init__(self, ground):
        self.px = [[ground] * 240 for _ in range(320)]

    def fill(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(320, y1)):
            for x in range(max(0, x0), min(240, x1)):
                self.px[y][x] = c

    def blend(self, x, y, ink, a):
        if 0 <= x < 240 and 0 <= y < 320 and a > 0:
            bg = self.px[y][x]
            self.px[y][x] = rgb565(tuple(round(i * a + b * (1 - a))
                                         for i, b in zip(ink, bg)))

    def image(self):
        im = Image.new('RGB', (240, 320))
        im.putdata([rgb565(p) for row in self.px for p in row])
        return im


# ---- device fonts ---------------------------------------------------------

def glyph_bits(cp, large):
    """Bitmap rows and advance, following the firmware's measurer
    0x030627BE: Latin letters advance by (leftmost + rightmost inked
    column + 2) over the top 10 rows (8 in the small font); others by
    the record's width byte minus 0x80; 0x80 means the default cell for
    ASCII and the full cell above it."""
    base, stride, rows = (FONT_LARGE, 0x21, 16) if large else (FONT_SMALL, 0x20, 12)
    rec = RAW[base + cp * stride:base + cp * stride + stride]
    bits = [[(rec[2 * y] << 8 | rec[2 * y + 1]) >> (15 - x) & 1 for x in range(16)]
            for y in range(rows)]
    tail = rec[rows * 2]
    cell, full = (8, 16) if large else (6, 12)
    adv = cell
    if tail == 0x20 or (tail == 0x80 and cp >= 0x7F):
        adv = full
    elif tail > 0x80:
        adv = tail - 0x80
    if 0x1100 <= cp <= 0x11FF:
        adv = full
    if chr(cp).isascii() and chr(cp).isalpha():
        cols = [x for row in bits[:10 if large else 8] for x in range(16) if row[x]]
        adv = (min(cols) + max(cols) + 2) if cols else 2
    return bits, adv


def smooth(bits, weight=0.45):
    """Coverage map: set bits 1.0, plus `weight` at clear pixels that sit
    in the inside corner of a diagonal step (two orthogonal neighbours
    set, the diagonal between them clear)."""
    h, w = len(bits), len(bits[0])
    at = lambda x, y: bits[y][x] if 0 <= x < w and 0 <= y < h else 0
    cov = [[float(bits[y][x]) for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if bits[y][x]:
                continue
            for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                if at(x + dx, y) and at(x, y + dy) and not at(x + dx, y + dy):
                    cov[y][x] = weight
    return cov


def device_text(scr, x, y, text, ink, large=True, smoothed=False):
    for ch in text:
        bits, adv = glyph_bits(ord(ch), large)
        cov = smooth(bits) if smoothed else bits
        for gy, row in enumerate(cov):
            for gx, a in enumerate(row):
                scr.blend(x + gx, y + gy, ink, a)
        x += adv
    return x


def aa_text(scr, x, y, text, ink, large=True, bold=False):
    """Latin runs from the grayscale font (16 levels); anything outside
    Latin-1 falls back to the 1-bit device glyph."""
    size = 13 if large else 10
    f = ImageFont.truetype(DEJAVU_BOLD if bold else DEJAVU, size)
    for ch in text:
        if ord(ch) > 0xFF:
            x = device_text(scr, x, y, ch, ink, large)
            continue
        adv = round(f.getlength(ch))
        m = Image.new('L', (adv + 4, 16 if large else 12), 0)
        ImageDraw.Draw(m).text((0, 13 if large else 10), ch, font=f, fill=255,
                               anchor='ls')
        for gy in range(m.height):
            for gx in range(m.width):
                a = m.getpixel((gx, gy))
                scr.blend(x + gx, y + gy, ink, round(a / 17) / 15)
        x += adv
    return x


def text(scr, mode, x, y, s, ink, large=True, bold=False):
    if mode == 'aa':
        return aa_text(scr, x, y, s, ink, large, bold)
    return device_text(scr, x, y, s, ink, large, smoothed=(mode == 'smooth'))


def text_width(mode, s, large=True, bold=False):
    if mode == 'aa':
        f = ImageFont.truetype(DEJAVU_BOLD if bold else DEJAVU, 13 if large else 10)
        return sum(round(f.getlength(c)) if ord(c) <= 0xFF else glyph_bits(ord(c), large)[1]
                   for c in s)
    return sum(glyph_bits(ord(c), large)[1] for c in s)


# ---- icons ----------------------------------------------------------------

def icon(scr, x, y, name, ink, aa):
    c = glyphs.draw_design(name)
    small = c.img.resize((32, 32), Image.BOX)
    for gy in range(32):
        for gx in range(32):
            v = small.getpixel((gx, gy)) / 255
            scr.blend(x + gx, y + gy, ink, v if aa else float(v >= 0.5))


# ---- screens --------------------------------------------------------------

WHITE, BLACK = (255, 255, 255), (0, 0, 0)
ACCENT = from565(0xF220)
THEATER = from565(0x7222)


def now_playing(mode):
    scr = Screen(THEATER)
    aa_icons = mode != 'today'
    # cover art stand-in: a soft two-colour square
    for yy in range(40, 200):
        for xx in range(40, 200):
            t = ((xx - 40) + (yy - 40)) / 320
            scr.px[yy][xx] = rgb565((int(196 - 90 * t), int(120 - 40 * t), int(88 + 70 * t)))
    text(scr, mode, 6, 8, '12:41', WHITE, large=False)
    text(scr, mode, 200, 8, '86%', WHITE, large=False)
    for s, yy, large in (('Clair de Lune', 210, True), ('Claude Debussy', 230, False),
                         ('Suite bergamasque', 245, False)):
        w = text_width(mode, s, large)
        text(scr, mode, (240 - w) // 2, yy, s, WHITE, large)
    text(scr, mode, 6, 262, '1:24', WHITE, large=False)
    w = text_width(mode, '-3:49', large=False)
    text(scr, mode, 234 - w, 262, '-3:49', WHITE, large=False)
    scr.fill(6, 259, 236, 260, from565(0xBDF7))
    scr.fill(6, 259, 68, 260, WHITE)
    for k, name in enumerate(('chev-left', 'prev', 'pause', 'next', 'chev-right')):
        icon(scr, 4 + 50 * k, 282, name, WHITE, aa_icons)
    return scr.image()


def file_list(mode):
    scr = Screen(BLACK)
    text(scr, mode, 8, 6, 'Music / Jazz', WHITE, large=False)
    scr.fill(0, 22, 240, 23, from565(0x4208))
    names = ['01 So What.flac', '02 Freddie Freeloader.flac', '03 Blue in Green.flac',
             '04 All Blues.flac', '05 Flamenco Sketches.flac', 'Café del Mar.mp3',
             'Naïve Melody.flac', '夜に駆ける.flac', '月亮代表我的心.mp3', 'Ölgemälde.ogg']
    for i, n in enumerate(names):
        yy = 30 + i * 28
        if i == 2:
            scr.fill(0, yy - 6, 240, yy + 22, ACCENT)
        text(scr, mode, 12, yy, n, WHITE, large=True)
    return scr.image()


def zoom(im, box, k):
    c = im.crop(box)
    return c.resize((c.width * k, c.height * k), Image.NEAREST)


def sheet():
    modes = (('today', 'Today: 1-bit text, hard-edged icons'),
             ('smooth', 'Option A: smoothed 1-bit text, AA icons'),
             ('aa', 'Option B: grayscale Latin font, AA icons'))
    OUT.mkdir(exist_ok=True)
    screens = {}
    for m, _ in modes:
        screens[m] = (now_playing(m), file_list(m))
        screens[m][0].save(OUT / f'now_playing_{m}.png')
        screens[m][1].save(OUT / f'file_list_{m}.png')
    S = 2                                   # whole screens at 2x
    Z = 6                                   # detail crops at 6x
    col = 240 * S + 24
    title_h, zoom_h = 40, 3 * (24 * Z + 30)
    W, H = col * 3 + 24, title_h + 320 * S * 2 + 40 + zoom_h + 20
    out = Image.new('RGB', (W, H), (245, 245, 242))
    d = ImageDraw.Draw(out)
    hf = ImageFont.truetype(DEJAVU_BOLD, 18)
    lf = ImageFont.truetype(DEJAVU, 14)
    for i, (m, label) in enumerate(modes):
        x = 24 + i * col
        d.text((x, 12), label, fill=(30, 30, 30), font=hf)
        np_, fl = screens[m]
        out.paste(np_.resize((240 * S, 320 * S), Image.NEAREST), (x, title_h))
        out.paste(fl.resize((240 * S, 320 * S), Image.NEAREST), (x, title_h + 320 * S + 20))
        y = title_h + 320 * S * 2 + 40
        for box, what, src in (((60, 208, 180, 232), 'title, 6x', np_),
                               ((4, 282, 84, 306), 'transport icons, 6x', np_),
                               ((8, 108, 88, 132), 'list row, 6x', fl)):
            z = zoom(src, box, Z)
            z = z.crop((0, 0, min(z.width, 240 * S), z.height))
            d.text((x, y), what, fill=(80, 80, 80), font=lf)
            out.paste(z, (x, y + 20))
            y += z.height + 30
    out.save(OUT / 'antialias_sheet.png')
    return OUT / 'antialias_sheet.png'


if __name__ == '__main__':
    print(sheet())
