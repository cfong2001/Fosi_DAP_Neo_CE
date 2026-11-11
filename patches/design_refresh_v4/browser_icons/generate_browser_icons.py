#!/usr/bin/env python3
"""Design refresh v4, browser set: the music selection window icons.

Deterministic generator. The browser window (module 31) draws its
list rows with fills and text only; the icons it owns are the five
status families drawn by its helper at 0x0307E804 through the opaque
DrawImage (0x03063700) and the battery gauge drawn by its Service
handler at 0x0307DB60, also DrawImage. Because the draw path is
opaque (proven for DrawImage in ../prove_keying.py path H, and for
these resources in test_browser_opaque.py), every replaced resource
keeps the exact ground its stock art was authored on, measured per
resource from the stock pixels:

  lock, headphones, file and clock families: ground 0x2945 (the
    stock surround of every member, dark set; the light table
    entries 427..432 are pixel copies of the dark art in stock, so
    the strip ground is theme-invariant)
  small play and pause: ground 0x0000 dark / 0xFFFF light (the
    palette background; the only family stock authors per theme)
  battery level frames: field 0x18C3 dark / 0xFFFF light
  battery charging frames: field 0xF800 (the key colour; stock
    authors these for a keyed draw on another screen). The light
    charging frames key only the exterior of the outline, exactly
    as stock does (311 vs 316 differ in 18 exterior pixels only).

Glyphs are bare filled geometric primitives in the v4 language (8x
supersampled canvas, box downscale, threshold at half coverage; no
anti-aliasing colours are emitted). Ink is 0xFFFF on the dark set
and 0x0000 on the light set; the lock takes the theme accent
(0xF220, dark set only: the light lock entries 204/205 are 1x1
dummies in stock and are not replaced). Battery bars keep the
stock state colours: green 0x368B, with the dark set's one-bar
frame in amber 0xFE00 exactly as stock (146 and 151).

The blank members (38, 261, 265 and the light copies 427, 431) are
solid ground in stock; the generator emits the same solid ground,
so those five .bin files are byte-identical to stock by design.

Outputs (in this directory):
  icon_set_browser/asset_<id>.bin   big-endian RGB565, stock length
  icon_set_browser/mapping.json     per-id meaning and hashes
  browser-glyphs.json               theme-config runs for build.py
  sheets/stock_vs_browser_3x_dark.png, sheets/stock_vs_browser_3x_light.png
"""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image as FwImage  # noqa: E402

S = 8                      # supersample factor
KEY = 0xF800
INK_DARK, INK_LIGHT = 0xFFFF, 0x0000
ACC_DARK = 0xF220
STRIP = 0x2945             # status strip ground (stock surround)
FIELD_DARK = 0x18C3        # battery field, dark level frames
BAR_GREEN = 0x368B
BAR_AMBER = 0xFE00

# id -> spec dict. 'art' names the glyph painter; 'ground' is the
# field every non-glyph pixel takes; 'ink' the glyph colour.
# Battery entries are built by battery_spec() instead.
SPECS = {
    38:  dict(art='blank', ground=STRIP, ink=INK_DARK,
              meaning='lock blank (hold off)'),
    39:  dict(art='lock', ground=STRIP, ink=ACC_DARK,
              meaning='lock (hold on)'),
    143: dict(art='small-pause', ground=0x0000, ink=INK_DARK,
              meaning='small pause (status)'),
    144: dict(art='small-play', ground=0x0000, ink=INK_DARK,
              meaning='small play (status)'),
    261: dict(art='blank', ground=STRIP, ink=INK_DARK,
              meaning='headphones blank (not connected)'),
    262: dict(art='headphones', ground=STRIP, ink=INK_DARK,
              meaning='headphones (connected)'),
    263: dict(art='file-none', ground=STRIP, ink=INK_DARK,
              meaning='file none (no file / error)'),
    264: dict(art='file-present', ground=STRIP, ink=INK_DARK,
              meaning='file present'),
    265: dict(art='blank', ground=STRIP, ink=INK_DARK,
              meaning='clock blank (sleep timer off)'),
    266: dict(art='clock', ground=STRIP, ink=INK_DARK,
              meaning='clock (sleep timer set)'),
    309: dict(art='small-pause', ground=0xFFFF, ink=INK_LIGHT,
              meaning='small pause (status, light)'),
    310: dict(art='small-play', ground=0xFFFF, ink=INK_LIGHT,
              meaning='small play (status, light)'),
    # Light entries 427..432 are pixel copies of the dark art in
    # stock; the redrawn set preserves that invariant.
    427: dict(art='blank', ground=STRIP, ink=INK_DARK,
              meaning='headphones blank (light copy)'),
    428: dict(art='headphones', ground=STRIP, ink=INK_DARK,
              meaning='headphones (light copy)'),
    429: dict(art='file-none', ground=STRIP, ink=INK_DARK,
              meaning='file none (light copy)'),
    430: dict(art='file-present', ground=STRIP, ink=INK_DARK,
              meaning='file present (light copy)'),
    431: dict(art='blank', ground=STRIP, ink=INK_DARK,
              meaning='clock blank (light copy)'),
    432: dict(art='clock', ground=STRIP, ink=INK_DARK,
              meaning='clock (light copy)'),
}

BAR_RUNS = [(3, 6), (8, 11), (13, 16), (18, 21)]   # measured stock
BAR_ROWS = (3, 10)                                  # measured stock


def battery_spec(rid):
    """Battery frames: dark levels 145..149, dark charging
    150..154, light levels 311..315, light charging 316..320."""
    if 145 <= rid <= 154:
        level = (rid - 145) % 5
        charging = rid >= 150
        return dict(art='battery', level=level, charging=charging,
                    theme='dark',
                    field=KEY if charging else FIELD_DARK,
                    ink=INK_DARK,
                    bar=BAR_AMBER if level == 1 else BAR_GREEN,
                    meaning=f'battery {"charging" if charging else "level"}'
                            f' {level} (dark)')
    level = (rid - 311) % 5
    charging = rid >= 316
    return dict(art='battery', level=level, charging=charging,
                theme='light',
                field=KEY if charging else 0xFFFF,
                ink=INK_LIGHT, bar=BAR_GREEN,
                meaning=f'battery {"charging" if charging else "level"}'
                        f' {level} (light)')


for _rid in list(range(145, 155)) + list(range(311, 321)):
    SPECS[_rid] = battery_spec(_rid)

# Keyed two-colour stock sprites, redrawn with baked antialiasing
# inside their stock footprint. Over a key the fringe blends toward a
# fixed target: the black play-state pair (both themes) only reads on
# a light surface, so light grey; 298 is the light-theme twin of the
# speaker 132 and sits on the white light-theme ground.
LIGHT_SURFACE = 0xC618
for _rid, _art, _target, _what in (
        (189, 'mini-pause', LIGHT_SURFACE, 'mini pause (dark)'),
        (190, 'mini-play', LIGHT_SURFACE, 'mini play (dark)'),
        (355, 'mini-pause', LIGHT_SURFACE, 'mini pause (light)'),
        (356, 'mini-play', LIGHT_SURFACE, 'mini play (light)'),
        (298, 'speaker', 0xFFFF, 'speaker (light)')):
    SPECS[_rid] = dict(art=_art, ground=KEY, ink=0x0000, target=_target,
                       keyed=True, meaning=_what)


def rgb888(v):
    return (((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63,
            (v & 31) * 255 // 31)


class Canvas:
    """Float-coordinate shape canvas at supersample S, sized to the
    resource. Ink drawn white, knockouts drawn black."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new('L', (w * S, h * S), 0)
        self.d = ImageDraw.Draw(self.img)

    def _xy(self, pts):
        return [(x * S, y * S) for x, y in pts]

    def poly(self, pts, fill=255):
        self.d.polygon(self._xy(pts), fill=fill)

    def rect(self, box, fill=255):
        # box is an inclusive native-pixel span; PIL's rectangle
        # endpoint is the last covered supersample pixel
        x0, y0, x1, y1 = box
        self.d.rectangle([x0 * S, y0 * S, (x1 + 1) * S - 1,
                          (y1 + 1) * S - 1], fill=fill)

    def rrect(self, box, r, fill=255):
        x0, y0, x1, y1 = [c * S for c in box]
        self.d.rounded_rectangle([x0, y0, x1, y1], radius=r * S,
                                 fill=fill)

    def circle(self, cx, cy, r, fill=255):
        self.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S,
                        (cy + r) * S], fill=fill)

    def stroke(self, pts, width, fill=255):
        """Capsule stroke through a point list; consecutive points
        are interpolated so a two-point list draws a full segment."""
        r = width * S / 2
        sampled = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) * S))
            for i in range(n + 1):
                sampled.append((x0 + (x1 - x0) * i / n,
                                y0 + (y1 - y0) * i / n))
        if len(pts) == 1:
            sampled = pts
        for x, y in sampled:
            self.d.ellipse([(x * S - r), (y * S - r), (x * S + r),
                            (y * S + r)], fill=fill)

    def arc(self, cx, cy, r, a0, a1, width, fill=255):
        steps = max(8, int(abs(a1 - a0) * 2))
        pts = []
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.stroke(pts, width, fill=fill)

    def mask(self):
        """Per-pixel coverage, 0.0 to 1.0, from the 8x supersample."""
        small = self.img.resize((self.w, self.h), Image.BOX)
        px = small.load()
        return [[px[x, y] / 255 for x in range(self.w)]
                for y in range(self.h)]


def neutral(v):
    """RGB565 grey with the luminance (Rec. 601) of `v`."""
    r, g, b = rgb888(v)
    y = round(0.299 * r + 0.587 * g + 0.114 * b)
    return (y * 31 + 127) // 255 << 11 | (y * 63 + 127) // 255 << 5 | \
        (y * 31 + 127) // 255


def blend(ink, target, cov):
    a, b = rgb888(ink), rgb888(target)
    r, g, bl = (round(i * cov + j * (1 - cov)) for i, j in zip(a, b))
    w = (r * 31 + 127) // 255 << 11 | (g * 63 + 127) // 255 << 5 | \
        (bl * 31 + 127) // 255
    return w ^ 0x0020 if w == KEY else w


def bake(ink, under, cov, target=None):
    """One pixel with baked antialiasing. `under` is what the pixel
    is when uncovered: an opaque ground, or KEY for a transparent
    surround. Partial coverage blends the ink toward the ground
    itself when it is opaque (exact, since the sprite lands as
    drawn) and toward `target` (a neutral grey) over a key."""
    if cov < 1 / 16:
        return under
    if cov >= 15 / 16:
        return ink
    return blend(ink, under if under != KEY else target, cov)


def glyph_mask(art, w, h):
    """The glyph layer for one design at the resource's own size."""
    c = Canvas(w, h)
    if art == 'blank':
        pass
    elif art == 'lock':
        c.arc(7.5, 7.6, 3.6, 180, 360, 2.3)          # shackle
        c.rrect((2.4, 7.4, 12.6, 16.6), 1.7)          # body
        c.circle(7.5, 11.3, 1.15, fill=0)             # keyhole
        c.rrect((6.85, 11.3, 8.15, 13.9), 0.6, fill=0)
    elif art == 'small-pause':
        c.rrect((2.5, 1.6, 5.0, 10.4), 1.0)
        c.rrect((7.0, 1.6, 9.5, 10.4), 1.0)
    elif art == 'small-play':
        c.poly([(3.4, 1.6), (3.4, 10.4), (10.2, 6.0)])
    elif art == 'headphones':
        c.arc(9.5, 9.8, 6.6, 180, 360, 2.3)           # band
        c.rrect((1.0, 8.6, 4.4, 15.8), 1.5)           # pads
        c.rrect((14.6, 8.6, 18.0, 15.8), 1.5)
    elif art == 'file-none':
        c.rrect((2.2, 1.2, 11.8, 16.8), 1.2)          # doc outline
        c.rrect((3.8, 2.8, 10.2, 15.2), 0.8, fill=0)
        c.stroke([(5.2, 6.6), (8.8, 11.4)], 1.6)      # X
        c.stroke([(8.8, 6.6), (5.2, 11.4)], 1.6)
    elif art == 'file-present':
        c.rrect((2.2, 1.2, 11.8, 16.8), 1.2)          # doc, filled
        c.poly([(8.6, 1.2), (11.8, 4.4), (11.8, 1.2)], fill=0)  # fold
        c.rrect((6.3, 5.6, 7.9, 12.4), 0.7, fill=0)   # digit 1
        c.poly([(6.3, 5.6), (4.7, 7.6), (6.3, 8.0)], fill=0)
    elif art == 'mini-pause':                       # stock bars x 1..3, 8..10
        c.rrect((1.0, 0.0, 4.0, 12.0), 1.0)
        c.rrect((8.0, 0.0, 11.0, 12.0), 1.0)
    elif art == 'mini-play':                        # stock x 2..10, y 0..11
        c.poly([(2.0, -0.3), (2.0, 12.3), (11.4, 6.0)])
    elif art == 'speaker':                          # stock 8x14 cone
        c.poly([(0, 3), (3, 3), (6.4, 0), (8, 0), (8, 14), (6.4, 14),
                (3, 11), (0, 11)])
    elif art == 'clock':
        c.circle(9, 9, 7.4)                           # disc
        c.stroke([(9, 9), (9, 4.9)], 1.8, fill=0)     # hands
        c.stroke([(9, 9), (12.4, 11.2)], 1.8, fill=0)
        c.circle(9, 9, 0.8, fill=0)                   # hub
    else:
        raise KeyError(art)
    return c.mask()


def battery_words(spec, w, h):
    """Battery frame: outline layer + bar layer over the field.
    Dark body (0,0)-(23,13) with the terminal at x 24..25; light
    body (1,1)-(24,12) with the terminal at x 25..26 (measured
    stock outline boxes; the 28-wide light charging frame keeps
    the same body and adds one exterior column at the right)."""
    dark = spec['theme'] == 'dark'
    body = Canvas(w, h)
    if dark:
        bx0, by0, bx1, by1 = 0, 0, 23, 13
        nub = (24, 4, 25, 9)
        inner = (2, 2, 21, 11)
    else:
        bx0, by0, bx1, by1 = 1, 1, 24, 12
        nub = (25, 4, 26, 9)
        inner = (3, 3, 22, 10)
    # rounded shell with the stock 2 px wall and a rounded terminal;
    # the antialiasing is baked into the curves (bake())
    body.rrect((bx0, by0, bx1 + 1, by1 + 1), 2.6)
    body.rrect((nub[0] - 1, nub[1], nub[2] + 1, nub[3] + 1), 1.0)
    ix0, iy0, ix1, iy1 = inner
    body.rrect((ix0, iy0, ix1 + 1, iy1 + 1), 1.0, fill=0)
    outline = body.mask()
    # where the rounded shell's outer edge sits, for the light
    # charging frames' keyed exterior
    shell = Canvas(w, h)
    shell.rrect((bx0, by0, bx1 + 1, by1 + 1), 2.6)
    shell.rrect((nub[0] - 1, nub[1], nub[2] + 1, nub[3] + 1), 1.0)
    inside = shell.mask()
    target = neutral(FIELD_DARK if dark else 0xFFFF)
    words = []
    for y in range(h):
        for x in range(w):
            if any(a <= x <= b for a, b in BAR_RUNS[:spec['level']]) \
                    and BAR_ROWS[0] <= y <= BAR_ROWS[1]:
                under = spec['bar']
            elif spec['charging'] and not dark and inside[y][x] < 1 / 16:
                under = KEY                # light charging: exterior key
            elif spec['charging'] and not dark:
                under = 0xFFFF
            else:
                under = spec['field']
            words.append(bake(spec['ink'], under, outline[y][x], target))
    return words


def render(spec, w, h):
    if spec['art'] == 'battery':
        return battery_words(spec, w, h)
    mask = glyph_mask(spec['art'], w, h)
    target = spec.get('target', neutral(spec['ground']))
    return [bake(spec['ink'], spec['ground'], mask[y][x], target)
            for y in range(h) for x in range(w)]


def theme_runs(e, stock, words):
    """Theme-config runs for one resource: maximal runs of changed
    halfwords, merging gaps of up to 4 unchanged halfwords. Same
    construction as ../generate_glyphs.py."""
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
    out_dir = HERE / 'icon_set_browser'
    out_dir.mkdir(exist_ok=True)
    (HERE / 'sheets').mkdir(exist_ok=True)

    rendered = {}
    assets = []
    runs = []
    for rid in sorted(SPECS):
        spec = SPECS[rid]
        e = imgs[rid]
        w, h = e['width'], e['height']
        words = render(spec, w, h)
        assert len(words) * 2 == e['size'], (rid, len(words), e['size'])
        rendered[rid] = words
        data = struct.pack(f'>{len(words)}H', *words)
        (out_dir / f'asset_{rid}.bin').write_bytes(data)
        stock = raw[e['data_offset']:e['data_offset'] + e['size']]
        entry = {
            'id': rid, 'design': spec['meaning'], 'w': w, 'h': h,
            'size': len(data),
            'stock_sha256': hashlib.sha256(stock).hexdigest(),
            'new_sha256': hashlib.sha256(data).hexdigest(),
            'ink': f"{spec['ink']:#06x}",
            'ground': f"{spec.get('ground', spec.get('field')):#06x}",
            'ink_pixels': sum(1 for px in words
                              if px == spec['ink']),
        }
        if spec['art'] == 'battery':
            entry['bar'] = f"{spec['bar']:#06x}"
            entry['level'] = spec['level']
            entry['charging'] = spec['charging']
        assets.append(entry)
        runs.extend(theme_runs(e, stock, words))

    runs.sort(key=lambda r: int(r['offset'], 16))
    (out_dir / 'mapping.json').write_text(json.dumps({
        'stock_image_sha256': hashlib.sha256(raw).hexdigest(),
        'count': len(assets), 'assets': assets,
    }, indent=1) + '\n')
    (HERE / 'browser-glyphs.json').write_text(json.dumps({
        'version': 1, 'literal_sites': [], 'runs': runs,
    }, indent=1) + '\n')
    print(f'{len(assets)} resources, {len(runs)} runs')

    # ---- route (b) pixel audit -------------------------------------
    # Every pixel is its declared ground (or key), the ink, a battery
    # bar, or a baked blend of the ink toward its ground (toward the
    # neutral target over a key); blanks are pure ground; battery bar
    # runs match the level; no pixel is the key unless the stock
    # frame keyed it.
    for a in assets:
        spec = SPECS[a['id']]
        words = rendered[a['id']]
        if spec['art'] == 'battery':
            dark = spec['theme'] == 'dark'
            grounds = {spec['field'], spec['bar']}
            if spec['charging'] and not dark:
                grounds |= {KEY, 0xFFFF}
            target = neutral(FIELD_DARK if dark else 0xFFFF)
        else:
            grounds = {spec['ground']}
            target = spec.get('target', neutral(spec['ground']))
        allowed = set(grounds) | {spec['ink']}
        for g in grounds:
            for k in range(256):
                allowed.add(bake(spec['ink'], g, k / 255, target))
        used = set(words)
        assert used <= allowed, (a['id'], [hex(v) for v in used - allowed])
        if KEY in used:
            assert spec.get('charging') or spec.get('keyed'), a['id']
        w, h = a['w'], a['h']
        if spec['art'] == 'blank':
            assert used == {spec['ground']}, a['id']
        if spec['art'] == 'battery':
            bar_cols = [x for x in range(w)
                        if any(words[y * w + x] == spec['bar']
                               for y in range(h))]
            runs_seen = []
            for x in bar_cols:
                if runs_seen and x == runs_seen[-1][1] + 1:
                    runs_seen[-1][1] = x
                else:
                    runs_seen.append([x, x])
            assert [tuple(r) for r in runs_seen] == \
                list(BAR_RUNS[:spec['level']]), (a['id'], runs_seen)
    print('pixel audit: PASS (colour sets with baked blends, blanks, bar runs)')

    # ---- contact sheets: stock vs new at 3x -------------------------
    font = ImageFont.truetype(
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)

    def tile(words, w, h):
        t = Image.new('RGB', (w, h))
        tp = t.load()
        for i, v in enumerate(words):
            tp[i % w, i // w] = (255, 0, 255) if v == KEY else rgb888(v)
        return t

    for theme, ids in (
            ('dark', [38, 39, 143, 144, 145, 146, 147, 148, 149, 150,
                      151, 152, 153, 154, 261, 262, 263, 264, 265, 266]),
            ('light', [309, 310, 311, 312, 313, 314, 315, 316, 317,
                       318, 319, 320, 427, 428, 429, 430, 431, 432])):
        scale, cols = 3, 5
        cellw, cellh = 26 * scale + 6, 18 * scale + 22
        rows = (len(ids) + cols - 1) // cols
        sh = Image.new('RGB', (cols * cellw * 2 + 8,
                               rows * cellh + 24), (28, 28, 28))
        d = ImageDraw.Draw(sh)
        d.text((6, 4), f'stock (left) vs browser set (right), '
                       f'{theme} set, 3x; magenta = 0xF800',
               font=font, fill=(255, 255, 0))
        for k, rid in enumerate(ids):
            e = imgs[rid]
            stock_words = struct.unpack_from(
                f'>{e["size"] // 2}H', raw, e['data_offset'])
            x = (k % cols) * cellw * 2 + 8
            y = (k // cols) * cellh + 24
            sh.paste(tile(stock_words, e['width'], e['height'])
                     .resize((e['width'] * scale, e['height'] * scale),
                             Image.NEAREST), (x, y))
            sh.paste(tile(rendered[rid], e['width'], e['height'])
                     .resize((e['width'] * scale, e['height'] * scale),
                             Image.NEAREST), (x + cellw, y))
            d.text((x + 2, y + 18 * scale + 4), str(rid), font=font,
                   fill=(255, 255, 0))
        path = HERE / 'sheets' / f'stock_vs_browser_3x_{theme}.png'
        sh.save(path)
        print(path.name)


if __name__ == '__main__':
    main()
