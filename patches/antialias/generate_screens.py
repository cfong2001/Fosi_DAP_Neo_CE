#!/usr/bin/env python3
"""Baked antialiasing for full-screen art, dialogs and the progress bar.

Same technique as the icon sets (../design_refresh_v4/generate_glyphs.py,
browser_icons/generate_browser_icons.py): shapes and text are rendered at
coverage and blended into the pixels the firmware stores. Nothing in the
draw code changes. Every target keeps its stock size and byte length.

  dialog cards   137, 193, 203 (dark) and 303, 359, 369 (light): the
                 rounded corners (radius 16, keyed outside) get exact
                 curve coverage, blended toward the screen behind them
                 (black on the dark set, white on the light set)
  low battery    the battery and bolt inside 137 and 303, redrawn with a
                 rounded shell and terminal; opaque, so the edges blend
                 exactly into the card
  power off      "Powering off..." in 294, rendered as smooth text on
                 its white ground
  CE mark        the splash mark on 127 (black) and 293 (white), smooth
                 text in the accent; written to ../theme_editor/ce-mark.json
  progress knob  220 (dark) and 386 (light) as a keyed disc with a soft
                 edge; patches/full/patches/0118 draws it through the keyed
                 helper, so the cover-derived ground shows around it
                 instead of the stock art's baked dark square
  progress bar   the 1x6 columns the player repeats along the bar, 187/188
                 (dark) and 353/354 (light): the top and bottom rows are
                 softened toward a neutral grey as bright as the theme
                 ground. The columns are blitted opaque over a ground the
                 cover art can set, so a grey target is the safe one.

Outputs: screens-glyphs.json (theme runs, merged by the full build),
../theme_editor/ce-mark.json, and mock/screens_before_after.png.
Run from the repository root.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image as FW  # noqa: E402

STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
KEY = 0xF800
S = 8
SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
SANS_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def rgb888(v):
    return ((v >> 11) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31)


def to565(r, g, b):
    return (r * 31 + 127) // 255 << 11 | (g * 63 + 127) // 255 << 5 | (b * 31 + 127) // 255


def blend(ink, under, cov):
    a, b = rgb888(ink), rgb888(under)
    w = to565(*(round(i * cov + j * (1 - cov)) for i, j in zip(a, b)))
    return w ^ 0x0020 if w == KEY else w


def neutral(v):
    r, g, b = rgb888(v)
    y = round(0.299 * r + 0.587 * g + 0.114 * b)
    return to565(y, y, y)


class Layer:
    """Coverage canvas for one region, supersampled S times."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new('L', (w * S, h * S), 0)
        self.d = ImageDraw.Draw(self.img)

    def rrect(self, box, r, fill=255):
        x0, y0, x1, y1 = [c * S for c in box]
        self.d.rounded_rectangle([x0, y0, x1 - 1, y1 - 1], radius=r * S, fill=fill)

    def rect(self, box, fill=255):
        x0, y0, x1, y1 = [c * S for c in box]
        self.d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=fill)

    def poly(self, pts, fill=255):
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill)

    def text(self, xy, s, font_path, size, anchor):
        f = ImageFont.truetype(font_path, size * S)
        self.d.text((xy[0] * S, xy[1] * S), s, font=f, fill=255, anchor=anchor)

    def coverage(self):
        small = self.img.resize((self.w, self.h), Image.BOX)
        return [[small.getpixel((x, y)) / 255 for x in range(self.w)]
                for y in range(self.h)]


class Res:
    def __init__(self, raw, e):
        self.e = e
        self.w, self.h = e['width'], e['height']
        self.stock = list(struct.unpack_from(f'>{self.w * self.h}H', raw, e['data_offset']))
        self.px = list(self.stock)

    def get(self, x, y):
        return self.px[y * self.w + x]

    def set(self, x, y, v):
        self.px[y * self.w + x] = v

    def composite(self, x0, y0, layer, ink):
        """Ink over what is there now, by the layer's coverage."""
        cov = layer.coverage()
        for y in range(layer.h):
            for x in range(layer.w):
                c = cov[y][x]
                if c > 0:
                    under = self.get(x0 + x, y0 + y)
                    self.set(x0 + x, y0 + y, ink if c >= 15 / 16 else blend(ink, under, c))

    def runs(self):
        """Theme-config runs: changed halfwords, gaps of up to 4 merged."""
        changed = [i for i in range(len(self.px)) if self.px[i] != self.stock[i]]
        spans = []
        for i in changed:
            if spans and i - spans[-1][1] <= 5:
                spans[-1][1] = i
            else:
                spans.append([i, i])
        old = struct.pack(f'>{len(self.stock)}H', *self.stock)
        new = struct.pack(f'>{len(self.px)}H', *self.px)
        return [{'offset': f'{self.e["data_offset"] + 2 * a:#x}',
                 'expect': old[2 * a:2 * b + 2].hex(),
                 'replace': new[2 * a:2 * b + 2].hex()} for a, b in spans]


# ---- dialog cards ----------------------------------------------------------

CARDS = {137: (0x18C3, 0x0000), 193: (0x2124, 0x0000), 203: (0x18C3, 0x0000),
         303: (0xFFFF, 0xFFFF), 359: (0xDEDB, 0xFFFF), 369: (0xFFFF, 0xFFFF)}
RADIUS = 16


def card_corners(r, card, behind):
    """Exact radius-16 corners. Outside the curve stays the key;
    partial coverage blends the card toward the screen behind it."""
    w, h = r.w, r.h
    shape = Layer(w, RADIUS)
    shape.rrect((0, 0, w, 2 * RADIUS + 2), RADIUS)
    top = shape.coverage()
    for y in range(RADIUS):
        for x in list(range(RADIUS)) + list(range(w - RADIUS, w)):
            c = top[y][x]
            for yy in (y, h - 1 - y):
                if c < 1 / 16:
                    v = KEY
                elif c >= 15 / 16:
                    v = card
                else:
                    v = blend(card, behind, c)
                # only the corner fringe and the key region change; any
                # stock content that reaches into a corner is kept
                if r.stock[yy * w + x] in (KEY, card) or c < 1:
                    r.set(x, yy, v)


def low_battery(r, x0, y0, card, bolt):
    """60x27 low-battery icon: rounded 2 px shell, terminal, red charge
    bar, lightning bolt. Opaque: blends exactly into the card."""
    for y in range(27):
        for x in range(60):
            r.set(x0 + x, y0 + y, card)
    shell = Layer(60, 27)
    shell.rrect((0, 0, 56, 27), 3.2)
    shell.rrect((2, 2, 54, 25), 1.6, fill=0)
    shell.rrect((55, 8, 60, 19), 1.4)
    shell.rect((54, 8, 56, 19))
    r.composite(x0, y0, shell, 0xCE79)
    bar = Layer(60, 27)
    bar.rrect((4, 4, 8, 23), 0.6)
    r.composite(x0, y0, bar, 0xA800)
    b = Layer(60, 27)
    b.poly([(26.2, 4.6), (34.6, 4.6), (30.9, 11.8), (34.8, 11.8), (23.4, 23.6),
            (27.4, 15.6), (22.6, 15.6)])
    r.composite(x0, y0, b, bolt)


def text_block(r, box, ground, s, font_path, size, anchor_xy, anchor, ink):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            r.set(x, y, ground)
    t = Layer(x1 - x0, y1 - y0)
    t.text((anchor_xy[0] - x0, anchor_xy[1] - y0), s, font_path, size, anchor)
    r.composite(x0, y0, t, ink)


def progress_column(r, ink, ground):
    """Soft top and bottom rows on the 1x6 bar column."""
    target = neutral(ground)
    for y, c in enumerate((0.5, 1, 1, 1, 1, 0.5)):
        r.set(0, y, ink if c == 1 else blend(ink, target, c))


def knob(r, ink, ground):
    """The 14x14 progress knob as a keyed disc: outside the disc is the
    key, the edge blends toward a neutral grey as bright as the theme
    ground. Drawn keyed by patch 0118 (full build), over the bar area the
    player has just refilled with the ground."""
    disc = Layer(14, 14)
    disc.d.ellipse([0, 0, 14 * S - 1, 14 * S - 1], fill=255)
    cov = disc.coverage()
    target = neutral(ground)
    for y in range(14):
        for x in range(14):
            c = cov[y][x]
            r.set(x, y, KEY if c < 1 / 16 else ink if c >= 15 / 16 else blend(ink, target, c))


def main():
    raw = (ROOT / 'DP3_V137.img').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == STOCK_SHA, 'stock SHA gate'
    E = {e['id']: e for e in FW(raw).images()}
    out = {}

    for rid, ink, ground in ((220, 0xF220, 0x7222), (386, 0xFB20, 0xBEFA)):
        out[rid] = r = Res(raw, E[rid])
        knob(r, ink, ground)

    for rid, (card, behind) in CARDS.items():
        out[rid] = r = Res(raw, E[rid])
        card_corners(r, card, behind)
    low_battery(out[137], 72, 98, 0x18C3, 0xCE79)
    low_battery(out[303], 72, 91, 0xFFFF, 0xA800)

    out[294] = r = Res(raw, E[294])
    text_block(r, (50, 180, 190, 204), 0xFFFF, 'Powering off…', SANS, 12,
               (120, 197), 'ms', 0x0000)

    ce = {}
    for rid, ground in ((127, 0x0000), (293, 0xFFFF)):
        ce[rid] = r = Res(raw, E[rid])
        text_block(r, (200, 294, 238, 316), ground, 'CE', SANS_BOLD, 19,
                   (233, 312), 'rs', 0xF220)

    for rid, ground in ((187, 0x7222), (188, 0x7222), (353, 0xBEFA), (354, 0xBEFA)):
        out[rid] = r = Res(raw, E[rid])
        progress_column(r, r.stock[0], ground)

    for rid, r in list(out.items()) + list(ce.items()):
        assert len(r.px) == len(r.stock), rid

    runs = sorted((x for r in out.values() for x in r.runs()),
                  key=lambda x: int(x['offset'], 16))
    (HERE / 'screens-glyphs.json').write_text(json.dumps(
        {'version': 1, 'literal_sites': [], 'runs': runs}, indent=1) + '\n')
    ce_runs = sorted((x for r in ce.values() for x in r.runs()),
                     key=lambda x: int(x['offset'], 16))
    (ROOT / 'patches' / 'theme_editor' / 'ce-mark.json').write_text(json.dumps(
        {'version': 1, 'literal_sites': [], 'runs': ce_runs}, indent=2) + '\n')
    print(f'screens: {len(out)} resources, {len(runs)} runs; '
          f'CE mark: {len(ce_runs)} runs, '
          f'{sum(len(x["replace"]) // 2 for x in ce_runs)} bytes')
    sheet(out, ce)


def sheet(out, ce):
    """Stock and new crops at 5x, for review."""
    crops = [(137, (0, 0, 40, 30)), (137, (66, 92, 138, 130)), (303, (66, 85, 138, 123)),
             (359, (0, 0, 40, 30)), (294, (50, 180, 190, 204)), (127, (196, 292, 240, 318)),
             (293, (196, 292, 240, 318))]
    f = ImageFont.truetype(SANS, 13)
    z = 5
    W, y = 1500, 10
    img = Image.new('RGB', (W, 3000), (128, 128, 128))
    d = ImageDraw.Draw(img)
    pool = {**out, **ce}

    def tile(words, w, box):
        t = Image.new('RGB', (w, len(words) // w))
        t.putdata([(255, 0, 255) if v == KEY else rgb888(v) for v in words])
        return t.crop(box)

    for rid, box in crops:
        r = pool[rid]
        a, b = tile(r.stock, r.w, box), tile(r.px, r.w, box)
        d.text((10, y), f'{rid}: stock | CE', fill=(255, 255, 255), font=f)
        img.paste(a.resize((a.width * z, a.height * z), Image.NEAREST), (10, y + 18))
        img.paste(b.resize((b.width * z, b.height * z), Image.NEAREST),
                  (20 + a.width * z, y + 18))
        y += a.height * z + 30
    x = 10
    for rid in (187, 188, 353, 354):
        r = pool[rid]
        for k, words in enumerate((r.stock, r.px)):
            t = Image.new('RGB', (40, 6))
            t.putdata([rgb888(words[yy]) for yy in range(6) for _ in range(40)])
            img.paste(t.resize((40 * z, 6 * z), Image.NEAREST), (x, y + 18 + k * 36))
        d.text((x, y), f'{rid}: stock / CE', fill=(255, 255, 255), font=f)
        x += 40 * z + 20
    y += 100
    path = HERE / 'mock' / 'screens_before_after.png'
    img.crop((0, 0, W, y)).save(path)
    print(path)


if __name__ == '__main__':
    main()
