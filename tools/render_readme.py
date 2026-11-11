#!/usr/bin/env python3
"""Render the README figures from the stock and CE images.

Every figure says where its pixels come from:

  exact      resource pixels decoded from the firmware image (big-endian
             RGB565, the order the panel displays)
  emulated   the real player painter (modules 0, 18 and 27) run under
             Unicorn on that image; the status icon and transport row are
             its framebuffer output
  algorithm  the theater background computed with port_derived() from
             patches/full/build/tests/test_theater_full.py, the Python port
             that the test checks against the firmware's own trampoline
  composed   the progress bar: the image's own column and knob resources
             (187, 188, 220) placed at the coordinates module 27 uses
             (patches/ui_features/renderer/renderer.md)
  drawn      cover art, title and artist text and time labels, drawn by
             this script at approximate positions (the painter code that
             draws them needs a mounted card, so it cannot run offline)

Usage (from the repository root, with Unicorn, Capstone and Pillow):

  python3 tools/render_readme.py [--ce release/DP3_V137_CE.img] [--out media]
"""
import argparse
import importlib.util
import math
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
from rknano_image import Image as Firmware  # noqa: E402


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


KT = load_module('keyed', REPO / 'patches/design_refresh_v4/test_keyed_transport.py')
DARK_GROUND = 0x10A2            # stock dark player ground (theater default)
BG = (13, 17, 23)               # figure background
CAPTION = (230, 230, 230)
SUB = (150, 160, 170)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
TRANSPORT_IDS = [155, 156] + list(range(157, 182)) + list(range(286, 290))


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def rgb(v):
    return (((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63,
            (v & 31) * 255 // 31)


def to565(r, g, b):
    return ((r * 31 + 127) // 255) << 11 | ((g * 63 + 127) // 255) << 5 | \
        ((b * 31 + 127) // 255)


class Fw:
    def __init__(self, path):
        self.raw = Path(path).read_bytes()
        self.res = {e['id']: e for e in Firmware(self.raw).images()}

    def resource(self, rid):
        e = self.res[rid]
        w, h = e['width'], e['height']
        data = self.raw[e['data_offset']:e['data_offset'] + w * h * 2]
        img = Image.new('RGB', (w, h))
        img.putdata([rgb(v) for (v,) in struct.iter_unpack('>H', data)])
        return img

    def paint(self, ground, a=0, b=0, play=1, theme=0):
        """Run the real painter segment; return the 240x320 framebuffer."""
        m = KT.Machine(self.raw, real_store=True)
        m.stage(TRANSPORT_IDS)
        KT.fb_fill(m, ground)
        m.painter(state_a=a, state_b=b, play=play, theme=theme, ground=ground)
        px = []
        for y in range(320):
            row = m.u.mem_read(KT.fb_addr(m, 0, y), 480)
            px.extend(rgb(v) for (v,) in struct.iter_unpack('<H', row))
        img = Image.new('RGB', (240, 320))
        img.putdata(px)
        return img


# ---------------------------------------------------------------- art

def cover(kind, size=144):
    img = Image.new('RGB', (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        if kind == 'ember':
            c = (int(245 - 170 * t), int(140 - 115 * t), int(30 - 10 * t))
        elif kind == 'tide':
            c = (int(20 + 10 * t), int(150 - 90 * t), int(190 - 80 * t))
        else:  # 'violet'
            c = (int(200 - 120 * t), int(60 + 10 * t), int(210 - 90 * t))
        d.line([(0, y), (size, y)], fill=c)
    if kind == 'ember':
        d.ellipse([84, 60, 136, 112], fill=(246, 200, 140))
    elif kind == 'tide':
        for k in range(5):
            y0 = 70 + k * 14
            d.arc([-20, y0, size + 20, y0 + 40], 200, 340, fill=(200, 240, 245), width=3)
    else:
        d.polygon([(72, 24), (124, 120), (20, 120)], fill=(255, 220, 90))
    return img


def theater_ground(art, light):
    """port_derived over the top third of the scaled art (48 rows)."""
    port = load_module('theater_port', REPO / 'patches/full/build/tests/test_theater_full.py')
    rows = [[to565(*art.getpixel((x, y))) for x in range(art.width)]
            for y in range(math.ceil(art.height / 3))]
    cell, _, _ = port.port_derived(rows, light)
    return cell


# ---------------------------------------------------------------- screens

def player(fw, ground, art, title, artist, light=False, b=0, play=1):
    """Full player screen: painter output plus drawn art and text."""
    img = fw.paint(ground, b=b, play=play, theme=1 if light else 0)
    d = ImageDraw.Draw(img)
    ink = (20, 20, 20) if light else (240, 240, 240)
    if art is not None:
        img.paste(art, (48, 36))
    else:
        d.rectangle([48, 36, 191, 179], outline=ink)
        d.text((120, 108), 'no art', fill=ink, font=font(12), anchor='mm')
    d.text((120, 206), title, fill=ink, font=font(17, True), anchor='mm')
    d.text((120, 231), artist, fill=ink, font=font(13), anchor='mm')
    d.text((6, 257), '1:12', fill=ink, font=font(11), anchor='lm')
    d.text((234, 257), '-2:48', fill=ink, font=font(11), anchor='rm')
    progress(fw, img, ground, light, 72 / 240)
    return img


def progress(fw, img, ground, light, fraction):
    """The player's progress bar as module 27 draws it (renderer.md):
    a ground fill over (40, 254)..(201, 268), then one 1x6 column per
    position at (46 + i, 258) for 148 positions, the filled column
    (resource 187) up to the fraction of 147 and the empty column (188)
    after it, then the knob (220) at (min(fill + 42, 196), 254). The
    light theme takes the same ids plus 166."""
    off = 166 if light else 0
    ImageDraw.Draw(img).rectangle([40, 254, 201, 268], fill=rgb(ground))
    filled = round(fraction * 147)
    on, off_col = fw.resource(187 + off), fw.resource(188 + off)
    for i in range(148):
        img.paste(on if i < filled else off_col, (46 + i, 258))
    knob = fw.resource(220 + off)
    # keyed: the CE image draws the knob through the keyed helper (patch
    # 0118) and its corners are 0xF800; the stock knob has no key pixels
    mask = Image.new('L', knob.size)
    mask.putdata([0 if p == rgb(0xF800) else 255 for p in knob.getdata()])
    img.paste(knob, (min(filled + 42, 196), 254), mask)


def framed(screens, captions, scale=2, gap=24, title=None, note=None):
    w, h = screens[0].width * scale, screens[0].height * scale
    top = 44 if title else 12
    bottom = 60 if note else 16
    sheet = Image.new('RGB', (len(screens) * (w + gap) + gap, top + h + 30 + bottom), BG)
    d = ImageDraw.Draw(sheet)
    if title:
        d.text((gap, 12), title, fill=CAPTION, font=font(20, True))
    for i, (s, c) in enumerate(zip(screens, captions)):
        x = gap + i * (w + gap)
        sheet.paste(s.resize((w, h), Image.NEAREST), (x, top))
        d.text((x + w // 2, top + h + 15), c, fill=CAPTION, font=font(15), anchor='mm')
    if note:
        d.text((gap, top + h + 36), note, fill=SUB, font=font(13))
    return sheet


def row_strip(img, y0=268, y1=312):
    return img.crop((0, y0, 240, y1))


# ---------------------------------------------------------------- figures

def fig_player(stock, ce, out):
    art = cover('ember')
    ground = theater_ground(art, light=False)
    s = player(stock, DARK_GROUND, art, 'Ember Skyline', 'Demonstration Ensemble')
    c = player(ce, ground, art, 'Ember Skyline', 'Demonstration Ensemble')
    framed([s, c], ['Stock V137', 'CE standard image'],
           note='Status icon and transport row: real painter output on each image (emulated). '
                f'CE ground 0x{ground:04X} from the theater algorithm.\n'
                'Cover and text drawn by the renderer at approximate positions; progress bar from the image.'
           ).save(out / 'player.png')
    return ground


def fig_theater(ce, out):
    screens, caps = [], []
    for kind, title in (('ember', 'Ember Skyline'), ('tide', 'Low Tide'), ('violet', 'Prism')):
        art = cover(kind)
        g = theater_ground(art, light=False)
        screens.append(player(ce, g, art, title, 'Demonstration Ensemble'))
        caps.append(f'dark, ground 0x{g:04X}')
    art = cover('tide')
    g = theater_ground(art, light=True)
    screens.append(player(ce, g, art, 'Low Tide', 'Demonstration Ensemble', light=True))
    caps.append(f'light, ground 0x{g:04X}')
    screens.append(player(ce, DARK_GROUND, None, 'Untitled', 'No artwork'))
    caps.append('no art: theme default')
    framed(screens, caps, scale=1, gap=16,
           note='Ground = average of the top third of the cover, mixed 55% toward black (dark) '
                'or 75% toward paper (light).').save(out / 'theater.png')


def fig_transport(stock, ce, ground, out):
    rows = [('Playing (B = 0)', dict(b=0, play=1)),
            ('Paused (B = 0)', dict(b=0, play=0)),
            ('Second page (B = 1)', dict(b=1, play=1)),
            ('Selection (B = 2)', dict(b=2, play=1))]
    scale, gap = 3, 18
    w, h = 240 * scale, 44 * scale
    sheet = Image.new('RGB', (2 * w + 3 * gap + 190, 60 + len(rows) * (h + gap)), BG)
    d = ImageDraw.Draw(sheet)
    d.text((190 + gap + w // 2, 24), 'Stock V137', fill=CAPTION, font=font(17, True), anchor='mm')
    d.text((190 + 2 * gap + w + w // 2, 24), 'CE standard image', fill=CAPTION,
           font=font(17, True), anchor='mm')
    for i, (label, kw) in enumerate(rows):
        y = 48 + i * (h + gap)
        d.text((10, y + h // 2), label, fill=CAPTION, font=font(15), anchor='lm')
        a = 1 if kw['b'] == 2 else 0
        st = row_strip(stock.paint(DARK_GROUND, a=a, **kw))
        cs = row_strip(ce.paint(ground, a=a, **kw))
        sheet.paste(st.resize((w, h), Image.NEAREST), (190 + gap, y))
        sheet.paste(cs.resize((w, h), Image.NEAREST), (190 + 2 * gap + w, y))
    sheet.save(out / 'transport.png')


def fig_splash(stock, ce, out):
    screens = [stock.resource(127), ce.resource(127), stock.resource(293), ce.resource(293)]
    framed(screens, ['Stock, dark', 'CE, dark', 'Stock, light', 'CE, light'], scale=1, gap=16,
           note='Boot splash resources 127 and 293, decoded from each image (exact).'
           ).save(out / 'splash.png')


def fig_browser(stock, ce, out):
    groups = [('Battery', [145, 146, 147, 148, 149]),
              ('Charging', [150, 151, 152, 153, 154]),
              ('Hold', [39]), ('Play state', [143, 144]),
              ('Headphones', [262]), ('Sleep timer', [266])]
    scale, pad, label_w = 3, 8, 130
    span = max(sum(stock.resource(r).width * scale + pad for r in ids) for _, ids in groups)
    sheet = Image.new('RGB', (label_w + 2 * span + 60, 60 + len(groups) * 72), BG)
    d = ImageDraw.Draw(sheet)
    cols = (label_w, label_w + span + 40)
    d.text((cols[0], 20), 'Stock V137', fill=CAPTION, font=font(17, True))
    d.text((cols[1], 20), 'CE standard image', fill=CAPTION, font=font(17, True))
    for i, (label, ids) in enumerate(groups):
        y = 56 + i * 72
        d.text((10, y + 25), label, fill=CAPTION, font=font(15), anchor='lm')
        for col, fw in zip(cols, (stock, ce)):
            x = col
            for rid in ids:
                r = fw.resource(rid)
                r = r.resize((r.width * scale, r.height * scale), Image.NEAREST)
                sheet.paste(r, (x, y))
                x += r.width + pad
    sheet.save(out / 'browser_icons.png')


def fig_lockscreen(stock, ce, out):
    def screen(fw, extra):
        img = Image.new('RGB', (240, 64), rgb(0x2945))
        img.paste(fw.resource(39), (135, 4))
        d = ImageDraw.Draw(img)
        if extra:
            d.text((11, 24), 'Ember Skyline', fill=(240, 240, 240), font=font(13))
            d.text((11, 40), '1:12 / 4:00', fill=(240, 240, 240), font=font(13))
        return img
    framed([screen(stock, False), screen(ce, True)],
           ['Stock: hold icon only', 'CE: title and elapsed / total'], scale=3, gap=24,
           note='Hold icon decoded from each image (exact). Text drawn at the routine\'s '
                'rectangles (11, 24) and (11, 40); the firmware font differs.'
           ).save(out / 'lockscreen.png')


def fig_vorbis(out):
    """Vorbis SNR per file: stock vs CE (post rounding fix), both measured."""
    import json
    results = {r['file'][:-4]: r for r in json.loads(
        (REPO / 'patches/vorbis_swap/corpus/results.json').read_text())}
    after = {}
    for line in (REPO / 'patches/vorbis_swap/vorbis_rounding.md').read_text().splitlines():
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) == 6 and cells[0] in results:
            after[cells[0]] = float(cells[2])
    files = list(after)
    surface, ink, ink2, grid = (26, 26, 25), (240, 239, 236), (195, 194, 183), (56, 56, 53)
    stock_c, ce_c = (217, 89, 38), (57, 135, 229)          # validated dark pair
    left, top, bar, gap, group = 190, 92, 16, 2, 50
    width = 900
    plot_w = width - left - 90
    sheet = Image.new('RGB', (width, top + len(files) * group + 70), surface)
    d = ImageDraw.Draw(sheet)
    d.text((24, 18), 'Vorbis decode quality, signal-to-noise ratio (dB, higher is better)',
           fill=ink, font=font(18, True))
    for i, (label, c) in enumerate((('Stock V137', stock_c), ('CE (both images)', ce_c))):
        x = 24 + i * 190
        d.rounded_rectangle([x, 56, x + 14, 70], 3, fill=c)
        d.text((x + 22, 63), label, fill=ink2, font=font(14), anchor='lm')

    def xpos(db):
        return left + plot_w * db / 100
    for db in range(0, 101, 20):
        x = xpos(db)
        d.line([(x, top - 6), (x, top + len(files) * group - 10)], fill=grid, width=1)
        d.text((x, top + len(files) * group - 2), f'{db}', fill=ink2, font=font(12), anchor='mt')
    for i, f in enumerate(files):
        y = top + i * group
        d.text((left - 12, y + bar), f.replace('_', ' '), fill=ink, font=font(13), anchor='rm')
        for j, (val, c) in enumerate(((results[f]['stock']['snr_total_ir_db'], stock_c),
                                      (after[f], ce_c))):
            y0 = y + j * (bar + gap)
            d.rounded_rectangle([xpos(0), y0, xpos(val), y0 + bar], 4, fill=c)
            d.text((xpos(val) + 6, y0 + bar / 2), f'{val:.1f}', fill=ink, font=font(12), anchor='lm')
    d.text((24, sheet.height - 26),
           'Emulated decode of the pinned corpus, scored against the reference (in-range samples). '
           'CE values include the rounding fix.', fill=ink2, font=font(12))
    sheet.save(out / 'vorbis.png')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stock', type=Path, default=REPO / 'DP3_V137.img')
    ap.add_argument('--ce', type=Path, default=REPO / 'release' / 'DP3_V137_CE.img')
    ap.add_argument('--out', type=Path, default=REPO / 'media')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    stock, ce = Fw(a.stock), Fw(a.ce)
    ground = fig_player(stock, ce, a.out)
    fig_theater(ce, a.out)
    fig_transport(stock, ce, ground, a.out)
    fig_splash(stock, ce, a.out)
    fig_browser(stock, ce, a.out)
    fig_lockscreen(stock, ce, a.out)
    fig_vorbis(a.out)
    for p in sorted(a.out.glob('*.png')):
        print(p, Image.open(p).size)


if __name__ == '__main__':
    main()
