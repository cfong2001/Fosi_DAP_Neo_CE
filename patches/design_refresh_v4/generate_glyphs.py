#!/usr/bin/env python3
"""Design refresh v4: transparent transport glyphs for the player row.

Deterministic generator. Every glyph is drawn from geometric
primitives on an 8x supersampled canvas and downscaled by box filter
to per-pixel coverage. The antialiasing is baked into the sprite:
coverage under 1/16 is the key colour 0xF800 (transparent on the
keyed draw path), coverage of 15/16 or more is the ink, and every
pixel in between is the ink pre-blended, in RGB565, toward a neutral
grey as bright as the set's theme ground (0x7222 dark, 0xBEFA light).
The keyed path cannot blend at run time and the theater ground comes
from cover art, so a neutral fringe is the target that stays clean on
any ground (patches/antialias/mock/grounds.png compares the choices).

Meanings follow the stock resources (see icon_set_v3/mapping.json
and the stock contact sheets): keycap and bare presentations of
one meaning get the same bare glyph. Ink is the palette foreground
(0xFFFF on the dark set, 0x0000 on the light set); the accent is
kept only on the two icons the stock bare row itself draws in the
accent (quote and info: dark 178/179 and 165/166, light 344/345
and 331/332), in the theme accent (0xF220 dark, 0xFB20 light).
Every other pixel is 0xF800, the surround resource 286 uses with
the keyed helper.

The set also covers the pre-rendered transport row composites
(155, 156 and light 321, 322; 240 by 32, 15360 bytes): the same
designs composited at the stock slot positions (x = 4 + 50 * k)
on a 0xF800 field. Two slots are left keyed on purpose; see
COMPOSITES below for the painter evidence.

Outputs (in this directory):
  icon_set_v4/asset_<id>.bin   big-endian RGB565, stock byte length
  icon_set_v4/mapping.json     per-id meaning and hashes
  v4-glyphs.json               theme-config runs for build.py
  sheets/stock_vs_v4_3x_dark.png, sheets/stock_vs_v4_3x_light.png
  sheets/v4_native_dark_0x7222.png, sheets/v4_native_light_0xbefa.png
"""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image as FwImage  # noqa: E402

S = 8                      # supersample factor
KEY = 0xF800
INK_DARK, INK_LIGHT = 0xFFFF, 0x0000
ACC_DARK, ACC_LIGHT = 0xF220, 0xFB20
GROUND_DARK, GROUND_LIGHT = 0x7222, 0xBEFA


def neutral(ground):
    """RGB565 grey with the luminance (Rec. 601) of `ground`."""
    r, g, b = (((ground >> 11) & 31) * 255 // 31, ((ground >> 5) & 63) * 255 // 63,
               (ground & 31) * 255 // 31)
    y = round(0.299 * r + 0.587 * g + 0.114 * b)
    return (y * 31 + 127) // 255 << 11 | (y * 63 + 127) // 255 << 5 | (y * 31 + 127) // 255


# The fringe is blended toward a neutral grey as bright as the theme
# ground, not the ground itself: in theater mode the ground comes from
# the cover art, and a grey fringe reads as plain edge softening on any
# ground where a tinted one shows as an outline.
FRINGE_DARK, FRINGE_LIGHT = neutral(GROUND_DARK), neutral(GROUND_LIGHT)

# id -> (design slug, accent?)
FAMILY = {
    157: ('chev-left', 0), 158: ('prev', 0), 159: ('play', 0),
    160: ('next', 0), 161: ('chev-right', 0), 162: ('chev-left', 0),
    163: ('repeat', 0), 164: ('minus', 0), 165: ('quote', 1),
    166: ('info', 1), 167: ('pause', 0), 168: ('pause', 0),
    169: ('play', 0), 170: ('repeat', 0), 171: ('repeat-arrows', 0),
    172: ('repeat-one', 0), 173: ('shuffle', 0), 174: ('repeat', 0),
    175: ('repeat-arrows', 0), 176: ('repeat-one', 0),
    177: ('shuffle', 0), 178: ('quote', 1), 179: ('info', 1),
    180: ('plus', 0), 181: ('plus', 0),
}
for dark_id in list(FAMILY):
    FAMILY[dark_id + 166] = FAMILY[dark_id]

# Row composites: id -> (slug, [slot designs at x = 4 + 50 * k]).
# A slot is None where the painter always overlays that slot in
# the states that draw the composite, so a baked glyph would show
# through the keyed overlay in the overlay's other state:
#   155 (B = 0) slot 2: the B = 0 path (cbz at 0x0307F80C) always
#     draws 168/169 over the centre. The stock composite's baked
#     centre is pixel-identical to resource 169's play glyph and
#     is never visible in stock; keyed, it would sit around the
#     pause bars. The overlay is the centre glyph.
#   156 (B = 1) slot 1: on the B != 0 path the segment always
#     draws the play-mode repeat family (174..177) at x = 54.
#     The visible glyph is the mode's variant, not the baked
#     repeat.
# 156 slot 2 (minus) is baked: the plus overlay (180) is drawn
# only when the playback-context query at 0x030640BC returns
# zero (and A != 8), and the v4 minus ink is an exact subset of
# the v4 plus ink, so the two compose to a clean plus; where the
# overlay is suppressed the minus shows, as in stock. Slots 3
# and 4 of 156 are baked with the same designs the segment draws
# over them in the media states (178, 179), so those overlays
# redraw identical ink.
COMPOSITES = {
    155: ('transport-row-b0',
          [('chev-left', 0), ('prev', 0), None, ('next', 0),
           ('chev-right', 0)]),
    156: ('transport-row-b1',
          [('chev-left', 0), None, ('minus', 0), ('quote', 1),
           ('info', 1)]),
}
for dark_id in list(COMPOSITES):
    COMPOSITES[dark_id + 166] = COMPOSITES[dark_id]


def rgb888(v):
    return (((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63,
            (v & 31) * 255 // 31)


class Canvas:
    """Float-coordinate shape canvas at supersample S. Ink drawn
    white, knockouts drawn black, on a black field."""

    def __init__(self):
        self.img = Image.new('L', (32 * S, 32 * S), 0)
        self.d = ImageDraw.Draw(self.img)

    def _xy(self, pts):
        return [(x * S, y * S) for x, y in pts]

    def poly(self, pts, fill=255):
        self.d.polygon(self._xy(pts), fill=fill)

    def rrect(self, box, r, fill=255):
        x0, y0, x1, y1 = [c * S for c in box]
        self.d.rounded_rectangle([x0, y0, x1, y1], radius=r * S,
                                 fill=fill)

    def circle(self, cx, cy, r, fill=255):
        self.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S,
                        (cy + r) * S], fill=fill)

    def stroke(self, pts, width, fill=255):
        """Capsule stroke through a point list (already sampled)."""
        r = width * S / 2
        for x, y in pts:
            self.d.ellipse([(x * S - r), (y * S - r), (x * S + r),
                            (y * S + r)], fill=fill)

    def arc(self, cx, cy, r, a0, a1, width, fill=255):
        """Arc stroke, angles in degrees, 0 = east, increasing
        clockwise on screen (y down)."""
        steps = max(8, int(abs(a1 - a0) * 2))
        pts = []
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.stroke(pts, width, fill)
        return pts[-1]

    def arrowhead(self, cx, cy, r, ang, fill=255):
        """Filled triangle head at the arc point for angle `ang`,
        pointing along the direction of increasing angle."""
        a = math.radians(ang)
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a)      # tangent, +angle way
        nx, ny = math.cos(a), math.sin(a)       # radial
        tip = (px + tx * 5.6, py + ty * 5.6)
        b1 = (px - tx * 2.0 + nx * 4.3, py - ty * 2.0 + ny * 4.3)
        b2 = (px - tx * 2.0 - nx * 4.3, py - ty * 2.0 - ny * 4.3)
        self.poly([tip, b1, b2], fill=fill)

    def finish(self, ink, ground):
        """32x32 RGB565 words with the antialiasing baked in against
        `ground` (see the module docstring)."""
        small = self.img.resize((32, 32), Image.BOX)
        px = small.load()
        words = []
        for y in range(32):
            for x in range(32):
                words.append(bake(ink, ground, px[x, y] / 255))
        return words


def bake(ink, ground, cov):
    if cov < 1 / 16:
        return KEY
    if cov >= 15 / 16:
        return ink
    a, b = rgb888(ink), rgb888(ground)
    r, g, bl = (round(i * cov + j * (1 - cov)) for i, j in zip(a, b))
    w = (r * 31 + 127) // 255 << 11 | (g * 63 + 127) // 255 << 5 | (bl * 31 + 127) // 255
    return w ^ 0x0020 if w == KEY else w


def bezier(p0, p1, p2, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def draw_design(name):
    c = Canvas()
    if name == 'play':
        # optically centred: centroid of the triangle at x = 16.2
        c.poly([(12, 6.5), (12, 25.5), (24.5, 16)])
    elif name == 'pause':
        c.rrect((10, 6.5, 14.3, 25.5), 2.1)
        c.rrect((17.7, 6.5, 22, 25.5), 2.1)
    elif name == 'prev':
        c.rrect((7, 6.5, 10.8, 25.5), 1.5)
        c.poly([(23, 6.5), (23, 25.5), (11.8, 16)])
    elif name == 'next':
        c.poly([(9, 6.5), (9, 25.5), (20.2, 16)])
        c.rrect((21.2, 6.5, 25, 25.5), 1.5)
    elif name == 'chev-left':
        c.poly([(20.5, 5.5), (10, 16), (20.5, 26.5), (20.5, 21.3),
                (15.2, 16), (20.5, 10.7)])
    elif name == 'chev-right':
        c.poly([(11.5, 5.5), (22, 16), (11.5, 26.5), (11.5, 21.3),
                (16.8, 16), (11.5, 10.7)])
    elif name == 'repeat':
        c.arc(16, 16, 9.3, 60, 282, 3.9)
        c.arrowhead(16, 16, 9.3, 282)
    elif name == 'repeat-arrows':
        c.arc(16, 16, 9.3, 200, 298, 3.9)
        c.arrowhead(16, 16, 9.3, 298)
        c.arc(16, 16, 9.3, 20, 118, 3.9)
        c.arrowhead(16, 16, 9.3, 118)
    elif name == 'repeat-one':
        c.arc(16, 16, 9.3, 60, 282, 3.9)
        c.arrowhead(16, 16, 9.3, 282)
        c.rrect((15.1, 12.2, 16.9, 19.8), 0.9)          # digit stem
        c.poly([(15.1, 12.2), (13.2, 14.6), (15.1, 15.0)])  # flag
    elif name == 'shuffle':
        c.stroke(bezier((6.5, 9), (15, 10), (22.5, 20.5)), 3.6)
        c.stroke(bezier((6.5, 23), (15, 22), (22.5, 11.5)), 3.6)
        c.poly([(27.5, 20.5), (21.6, 17.3), (21.6, 23.7)])
        c.poly([(27.5, 11.5), (21.6, 8.3), (21.6, 14.7)])
    elif name == 'minus':
        c.rrect((8, 14, 24, 18), 2)
    elif name == 'plus':
        c.rrect((14, 6.5, 18, 25.5), 1.8)
        c.rrect((6.5, 14, 25.5, 18), 1.8)
    elif name == 'quote':
        c.rrect((5.5, 7, 26.5, 22.5), 4)
        c.poly([(10, 22.5), (10, 27.5), (16.5, 22.5)])
        c.poly([(11.4, 11.6), (14.0, 11.6), (13.4, 15.8),
                (10.8, 15.8)], fill=0)
        c.poly([(18.6, 11.6), (21.2, 11.6), (20.6, 15.8),
                (18.0, 15.8)], fill=0)
    elif name == 'info':
        c.circle(16, 16, 10.5)
        c.circle(16, 11.6, 1.6, fill=0)
        c.rrect((14.85, 14.6, 17.15, 21.2), 1.15, fill=0)
    else:
        raise KeyError(name)
    return c


def theme_runs(e, stock, words):
    """Theme-config runs for one resource: maximal runs of changed
    halfwords, merging gaps of up to 4 unchanged halfwords."""
    old = struct.unpack(f'>{len(words)}H', stock)
    changed = [i for i in range(len(words)) if old[i] != words[i]]
    spans = []
    for i in changed:
        if spans and i - spans[-1][1] <= 5:
            spans[-1][1] = i
        else:
            spans.append([i, i])
    data = struct.pack(f'>{len(words)}H', *words)
    return [{
        'offset': f'{e["data_offset"] + 2 * a:#x}',
        'expect': stock[2 * a:2 * b + 2].hex(),
        'replace': data[2 * a:2 * b + 2].hex(),
    } for a, b in spans]


def main():
    raw = (ROOT / 'DP3_V137.img').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == \
        'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
    im = FwImage(raw)
    imgs = {e['id']: e for e in im.images()}
    out_dir = HERE / 'icon_set_v4'
    out_dir.mkdir(exist_ok=True)
    (HERE / 'sheets').mkdir(exist_ok=True)

    rendered = {}      # id -> list of 1024 colour words
    assets = []
    runs = []
    for rid in sorted(FAMILY):
        design, accent = FAMILY[rid]
        light = rid >= 323
        ink = (ACC_LIGHT if accent else INK_LIGHT) if light else \
              (ACC_DARK if accent else INK_DARK)
        words = draw_design(design).finish(
            ink, FRINGE_LIGHT if light else FRINGE_DARK)
        rendered[rid] = words
        e = imgs[rid]
        assert (e['width'], e['height'], e['size']) == (32, 32, 2048), rid
        data = struct.pack('>1024H', *words)
        (out_dir / f'asset_{rid}.bin').write_bytes(data)
        stock = raw[e['data_offset']:e['data_offset'] + e['size']]
        assets.append({
            'id': rid, 'design': design, 'w': 32, 'h': 32,
            'size': len(data),
            'stock_sha256': hashlib.sha256(stock).hexdigest(),
            'new_sha256': hashlib.sha256(data).hexdigest(),
            'ink': f'{ink:#06x}', 'key': f'{KEY:#06x}',
            'ink_pixels': sum(1 for w in words if w != KEY),
        })
        runs.extend(theme_runs(e, stock, words))

    for rid in sorted(COMPOSITES):
        slug, slots = COMPOSITES[rid]
        light = rid >= 321
        ink = INK_LIGHT if light else INK_DARK
        accent_ink = ACC_LIGHT if light else ACC_DARK
        e = imgs[rid]
        assert (e['width'], e['height'], e['size']) == \
            (240, 32, 15360), rid
        words = [KEY] * (240 * 32)
        for k, slot in enumerate(slots):
            if slot is None:
                continue
            design, accent = slot
            tile = draw_design(design).finish(
                accent_ink if accent else ink,
                FRINGE_LIGHT if light else FRINGE_DARK)
            x0 = 4 + 50 * k
            for i, w in enumerate(tile):
                words[(i // 32) * 240 + x0 + i % 32] = w
        data = struct.pack('>7680H', *words)
        (out_dir / f'asset_{rid}.bin').write_bytes(data)
        stock = raw[e['data_offset']:e['data_offset'] + e['size']]
        assets.append({
            'id': rid, 'design': slug, 'w': 240, 'h': 32,
            'size': len(data),
            'stock_sha256': hashlib.sha256(stock).hexdigest(),
            'new_sha256': hashlib.sha256(data).hexdigest(),
            'ink': f'{ink:#06x}', 'key': f'{KEY:#06x}',
            'ink_pixels': sum(1 for w in words if w != KEY),
            'slots': [None if s is None else s[0] for s in slots],
        })
        runs.extend(theme_runs(e, stock, words))

    runs.sort(key=lambda r: int(r['offset'], 16))
    (out_dir / 'mapping.json').write_text(json.dumps({
        'stock_image_sha256': hashlib.sha256(raw).hexdigest(),
        'count': len(assets), 'assets': assets,
    }, indent=1) + '\n')
    (HERE / 'v4-glyphs.json').write_text(json.dumps({
        'version': 1, 'literal_sites': [], 'runs': runs,
    }, indent=1) + '\n')
    print(f'{len(assets)} resources, {len(runs)} runs')

    # ---- contact sheets -------------------------------------------------
    font = ImageFont.truetype(
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)

    def tile_from_words(words):
        t = Image.new('RGB', (32, 32))
        tp = t.load()
        for i, w in enumerate(words):
            tp[i % 32, i // 32] = rgb888(w)
        return t

    def composite(words, ground):
        t = Image.new('RGB', (32, 32), rgb888(ground))
        tp = t.load()
        for i, w in enumerate(words):
            if w != KEY:
                tp[i % 32, i // 32] = rgb888(w)
        return t

    for theme, ids, ground in (
            ('dark', list(range(157, 182)), GROUND_DARK),
            ('light', list(range(323, 348)), GROUND_LIGHT)):
        scale, cols = 3, 5
        cell = 32 * scale + 6
        rows = (len(ids) + cols - 1) // cols
        sh = Image.new('RGB', (cols * cell * 2 + 8,
                               rows * (cell + 30) + 24), (28, 28, 28))
        d = ImageDraw.Draw(sh)
        d.text((6, 4), f'stock (left) vs v4 over {ground:#06x} '
                       f'(right), {theme} set', font=font,
               fill=(255, 255, 0))
        for k, rid in enumerate(ids):
            e = imgs[rid]
            stock_words = struct.unpack_from('>1024H', raw,
                                             e['data_offset'])
            x = (k % cols) * cell * 2 + 8
            y = (k // cols) * (cell + 30) + 24
            sh.paste(tile_from_words(stock_words)
                     .resize((32 * scale, 32 * scale), Image.NEAREST),
                     (x, y))
            sh.paste(composite(rendered[rid], ground)
                     .resize((32 * scale, 32 * scale), Image.NEAREST),
                     (x + cell, y))
            d.text((x + 2, y + cell + 2), str(rid), font=font,
                   fill=(255, 255, 0))
        path = HERE / 'sheets' / f'stock_vs_v4_3x_{theme}.png'
        sh.save(path)
        print(path.name)

    for theme, ground in (('dark', GROUND_DARK), ('light', GROUND_LIGHT)):
        ids = sorted(FAMILY)
        cols, cell = 10, 40
        rows = (len(ids) + cols - 1) // cols
        sh = Image.new('RGB', (cols * cell, rows * (cell + 10)),
                       rgb888(ground))
        d = ImageDraw.Draw(sh)
        for k, rid in enumerate(ids):
            x, y = (k % cols) * cell, (k // cols) * (cell + 10)
            sh.paste(composite(rendered[rid], ground), (x + 4, y))
            d.text((x + 4, y + 33), str(rid), font=font,
                   fill=(255, 255, 0))
        path = HERE / 'sheets' / f'v4_native_{theme}_{ground:#06x}.png'
        sh.save(path)
        print(path.name)


if __name__ == '__main__':
    main()
