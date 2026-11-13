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
  glyphs     text set from the image's own Font B records with the
             firmware's advance rule (0x030627BE, ported in
             patches/antialias/generate_font.py); the list layout around
             it (row height, margins, selection bar) is drawn
  ported     the CE cover treatment, format badge, no-art tile, progress
             bar colours and time line: Python ports of
             patches/player_ui/artwork.c (contrast factor 1.20, radius-10 corner mask, 56x20 badge at (132, 156),
             outline and music note, bar columns from the inverted
             ground) and typography.S (MM:SS in Font B at
             (7, 240) and (191, 240)), at the coordinates those routines use
  drawn      cover art, title and artist text, and the stock time labels,
             drawn by this script at approximate positions (the painter
             code that draws them needs a mounted card, so it cannot run
             offline)

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
GF = load_module('genfont', REPO / 'patches/antialias/generate_font.py')
DARK_GROUND = 0x10A2            # stock dark player ground (theater default)
BG = (13, 17, 23)               # figure background
CAPTION = (230, 230, 230)
SUB = (150, 160, 170)
FONT = REPO / 'docs/fonts/Barlow-Regular.ttf'
FONT_BOLD = REPO / 'docs/fonts/Barlow-SemiBold.ttf'
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
    def __init__(self, path, ce=False):
        self.ce = ce                # CE: letters advance by their tail (0190/0191)
        self.raw = Path(path).read_bytes()
        self.res = {e['id']: e for e in Firmware(self.raw).images()}

    def resource(self, rid):
        e = self.res[rid]
        w, h = e['width'], e['height']
        data = self.raw[e['data_offset']:e['data_offset'] + w * h * 2]
        img = Image.new('RGB', (w, h))
        img.putdata([rgb(v) for (v,) in struct.iter_unpack('>H', data)])
        return img

    def text(self, img, x, y, s, ink):
        """Set s with this image's Font B records and the firmware's
        advance rule; returns the end x."""
        base = Firmware(self.raw).sections['font_b']['offset']
        for ch in s:
            cp = ord(ch)
            rec = self.raw[base + cp * GF.STRIDE:base + (cp + 1) * GF.STRIDE]
            for gy in range(GF.ROWS):
                row = int.from_bytes(rec[2 * gy:2 * gy + 2], 'big')
                for gx in range(16):
                    if row & (0x8000 >> gx) and 0 <= x + gx < img.width \
                            and 0 <= y + gy < img.height:
                        img.putpixel((x + gx, y + gy), ink)
            x += GF.advance(rec, cp, self.ce)
        return x

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

def player(fw, ground, art, title, artist, light=False, b=0, play=1, ce=False,
           codec='FLAC'):
    """Full player screen: painter output plus art and text. Stock art and
    time are drawn; CE art, badge, placeholder and time follow the CE
    routines (see ce_cover, ce_badge, ce_placeholder, ce_time)."""
    img = fw.paint(ground, b=b, play=play, theme=1 if light else 0)
    d = ImageDraw.Draw(img)
    ink = (20, 20, 20) if light else (240, 240, 240)
    if ce:
        if art is not None:
            img.paste(ce_cover(art, ground), (48, 36))
        else:
            ce_placeholder(img, ink)
        ce_badge(fw, img, codec, light)
    elif art is not None:
        img.paste(art, (48, 36))
    else:
        d.rectangle([48, 36, 191, 179], outline=ink)
        d.text((120, 108), 'no art', fill=ink, font=font(12), anchor='mm')
    # CE time sits on a line at y = 240, so its drawn title and artist
    # move up to stay clear of it
    ty, ay = (200, 223) if ce else (206, 231)
    d.text((120, ty), title, fill=ink, font=font(17, True), anchor='mm')
    d.text((120, ay), artist, fill=ink, font=font(13), anchor='mm')
    if ce:
        ce_time(fw, img, ground, '01:12', '04:00', ink)
    else:
        d.text((6, 257), '1:12', fill=ink, font=font(11), anchor='lm')
        d.text((234, 257), '-2:48', fill=ink, font=font(11), anchor='rm')
    progress(fw, img, ground, light, 72 / 240)
    return img


# CE artwork compositor (patches/player_ui/artwork.c), ported.
EDGE = (7, 5, 4, 3, 2, 2, 1, 1, 0, 0)    # radius-10 corner inset per row


def inset(row, height):
    y = row if row < height // 2 else height - 1 - row
    return EDGE[y] if y < 10 else 0


def gain(v, top):
    v = int((120 * v - 10 * top + 50) / 100)     # C division truncates
    return max(0, min(top, v))


def contrast(word):
    return gain(word >> 11, 31) << 11 | gain((word >> 5) & 63, 63) << 5 | \
        gain(word & 31, 31)


def ce_cover(art, ground):
    """art_pixels over a square cover: contrast on every pixel inside the
    rounded mask, the theater ground outside it. The source pixels (and so
    the theater sample) are untouched."""
    out = Image.new('RGB', art.size)
    for y in range(art.height):
        n = inset(y, art.height)
        for x in range(art.width):
            w = ground if x < n or x >= art.width - n else \
                contrast(to565(*art.getpixel((x, y))))
            out.putpixel((x, y), rgb(w))
    return out


def ce_placeholder(img, ink):
    """art_placeholder in the normal box: a 2-pixel rounded outline and a
    music note, as the routine's fills."""
    d = ImageDraw.Draw(img)
    x, top, side = 48, 36, 144
    for y in range(side):
        n = inset(y, side)
        if y < 2 or y >= side - 2:
            d.line([(x + n, top + y), (x + side - 1 - n, top + y)], fill=ink)
        else:
            d.line([(x + n, top + y), (x + 1 + n, top + y)], fill=ink)
            d.line([(x + side - 2 - n, top + y), (x + side - 1 - n, top + y)], fill=ink)
    d.rectangle([121, 78, 125, 122], fill=ink)
    d.rectangle([125, 78, 139, 83], fill=ink)
    for y in range(10):
        n = 3 if y < 2 or y > 7 else 0
        d.line([(108 + n, 117 + y), (125 - n, 117 + y)], fill=ink)


def ce_badge(fw, img, label, light):
    """art_badge in the normal box: a 56x20 rounded tile at (132, 156) in
    palette cell 0, the label in Font B at (136, 158) in the text colour.
    The palette cell is taken as the theme's default ground."""
    x, y = 132, 156
    fill_ = rgb(0xFFFF if light else DARK_GROUND)
    d = ImageDraw.Draw(img)
    for r in range(20):
        n = inset(r, 20)
        d.line([(x + n, y + r), (x + 55 - n, y + r)], fill=fill_)
    fw.text(img, x + 4, y + 2, label, (0, 0, 0) if light else (255, 255, 255))


def ce_time(fw, img, ground, elapsed, total, ink):
    """player_time: each MM:SS string set in Font B on the 14-pixel line at
    y = 240, elapsed in (7..72), total in (191..239), each rectangle
    cleared to the ground first."""
    d = ImageDraw.Draw(img)
    for x0, x1, s in ((7, 72, elapsed), (191, 239, total)):
        d.rectangle([x0, 240, x1, 253], fill=rgb(ground))
        fw.text(img, x0, 240, s, ink)


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
    on, off_col = bar_columns(fw, ground, light)
    for i in range(148):
        img.paste(on if i < filled else off_col, (46 + i, 258))
    knob = fw.resource(220 + off)
    # keyed: the CE image draws the knob through the keyed helper (patch
    # 0118) and its corners are 0xF800; the stock knob has no key pixels
    mask = Image.new('L', knob.size)
    mask.putdata([0 if p == rgb(0xF800) else 255 for p in knob.getdata()])
    img.paste(knob, (min(filled + 42, 196), 254), mask)


def half(a, b):
    """Per-component average of two RGB565 words (artwork.c half)."""
    return ((a & 0xF7DE) >> 1) + ((b & 0xF7DE) >> 1)


def bar_columns(fw, ground, light):
    """The played and unplayed 1x6 columns: the image's resources 187
    and 188 (light: +166) on stock; on CE, bar_recolor's columns from the
    ground (played = inverse, unplayed = 3/8 of the way to it, rows 0
    and 5 blended halfway into the ground)."""
    if not fw.ce:
        off = 166 if light else 0
        return fw.resource(187 + off), fw.resource(188 + off)
    inv = ~ground & 0xFFFF
    mid = half(inv, ground)
    track = half(mid, half(mid, ground))
    cols = []
    for body, edge in ((inv, mid), (track, half(track, ground))):
        c = Image.new('RGB', (1, 6))
        c.putdata([rgb(edge)] + [rgb(body)] * 4 + [rgb(edge)])
        cols.append(c)
    return cols


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
    c = player(ce, ground, art, 'Ember Skyline', 'Demonstration Ensemble', ce=True)
    framed([s, c], ['Stock V137', 'CE standard image'],
           note='Status icon and transport row: real painter output (emulated). '
                f'CE ground 0x{ground:04X} from the theater algorithm; CE bar is the inverted ground.\n'
                'CE cover contrast, corners, badge and time follow the CE routines; '
                'cover art, title and artist drawn at approximate positions.'
           ).save(out / 'player.png')
    return ground


def fig_theater(ce, out):
    screens, caps = [], []
    for kind, title, codec in (('ember', 'Ember Skyline', 'FLAC'), ('tide', 'Low Tide', 'MP3'),
                               ('violet', 'Prism', 'OPUS')):
        art = cover(kind)
        g = theater_ground(art, light=False)
        screens.append(player(ce, g, art, title, 'Demonstration Ensemble', ce=True, codec=codec))
        caps.append(f'dark, ground 0x{g:04X}')
    art = cover('tide')
    g = theater_ground(art, light=True)
    screens.append(player(ce, g, art, 'Low Tide', 'Demonstration Ensemble', light=True,
                          ce=True, codec='MP3'))
    caps.append(f'light, ground 0x{g:04X}')
    screens.append(player(ce, DARK_GROUND, None, 'Untitled.wav', 'Unknown', ce=True,
                          codec='WAV'))
    caps.append('no art: theme default')
    framed(screens, caps, scale=1, gap=16,
           note='Ground = average of the top third of the original cover, mixed 55% toward black '
                '(dark) or 75% toward paper (light). CE contrast, corners and badge; bar in the inverted ground.'
           ).save(out / 'theater.png')


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
        if extra:
            fw.text(img, 11, 22, 'Ember Skyline', (240, 240, 240))
            fw.text(img, 11, 40, '1:12 / 4:00', (240, 240, 240))
        return img
    framed([screen(stock, False), screen(ce, True)],
           ['Stock: hold icon only', 'CE: title and elapsed / total'], scale=3, gap=24,
           note='Hold icon decoded from each image (exact). Text set in the CE image\'s '
                'Font B (glyphs) near the routine\'s rectangles (11, 24) and (11, 40).'
           ).save(out / 'lockscreen.png')


def fig_menus(stock, ce, out):
    rows = ['Music', 'Playlists', 'Albums', 'Artists', 'Settings',
            'Playback order', 'Language', 'Bluetooth', 'Sleep timer']
    files = ['01 So What.flac', '02 Freddie Freeloader.flac', '03 Blue in Green.flac',
             '04 All Blues.flac', '05 Flamenco Sketches.flac', 'Café del Mar.mp3',
             'Naïve Melody.flac', 'Dvořák - Largo.ogg', 'Łódź Nocturne.opus']

    def screen(fw, items, sel):
        img = Image.new('RGB', (240, 284), (0, 0, 0))
        d = ImageDraw.Draw(img)
        for i, t in enumerate(items):
            y = 6 + i * 31
            if i == sel:
                d.rectangle([0, y, 239, y + 27], fill=rgb(0xF220))
            fw.text(img, 12, y + 6, t, (255, 255, 255))
        return img

    framed([screen(stock, rows, 4), screen(ce, rows, 4),
            screen(stock, files, 2), screen(ce, files, 2)],
           ['Stock menu', 'CE menu', 'Stock file list', 'CE file list'], scale=2, gap=20,
           title='List and menu text (Font B)',
           note='Text set from each image\'s own Font B glyph records with the firmware\'s '
                'advance rule (glyphs); row layout and selection bar drawn.'
           ).save(out / 'menus.png')


def fig_screens(stock, ce, out):
    """Zoomed details of the baked screen art, stock beside CE."""
    def on_(fw, rid, ground):
        r = fw.resource(rid)
        under = Image.new('RGB', r.size, ground)
        e = fw.res[rid]
        px = struct.unpack_from(f'>{e["width"] * e["height"]}H', fw.raw, e['data_offset'])
        mask = Image.new('L', r.size, 0)
        mask.putdata([0 if v == 0xF800 else 255 for v in px])
        under.paste(r, (0, 0), mask)
        return under

    def bar(fw, light):
        g = 0xBEFA if light else 0x7222
        ground = rgb(g)
        img = Image.new('RGB', (240, 30), ground)
        off = 166 if light else 0
        on, off_col = bar_columns(fw, g, light)
        for i in range(148):
            img.paste(on if i < 62 else off_col, (46 + i, 12))
        knob = on_(fw, 220 + off, ground) if fw.ce else fw.resource(220 + off)
        img.paste(knob, (104, 8))
        return img

    rows = [('Low battery (137)', lambda fw: on_(fw, 137, (0, 0, 0)).crop((64, 90, 140, 134))),
            ('Low battery, light (303)',
             lambda fw: on_(fw, 303, (255, 255, 255)).crop((64, 83, 140, 127))),
            ('Powering off (294)', lambda fw: fw.resource(294).crop((60, 186, 180, 210))),
            ('Progress bar and knob', lambda fw: bar(fw, False).crop((70, 2, 150, 28))),
            ('Progress bar, light', lambda fw: bar(fw, True).crop((70, 2, 150, 28)))]
    z, gap, label_w = 4, 24, 230
    cells = [(t, f(stock), f(ce)) for t, f in rows]
    w = max(a.width for _, a, _ in cells) * z
    h = sum(a.height * z + gap for _, a, _ in cells)
    sheet = Image.new('RGB', (label_w + 2 * (w + gap) + gap, 90 + h + 40), BG)
    d = ImageDraw.Draw(sheet)
    d.text((gap, 14), 'Screens, dialogs and progress bar', fill=CAPTION, font=font(20, True))
    d.text((label_w, 52), 'Stock V137', fill=CAPTION, font=font(16, True))
    d.text((label_w + w + gap, 52), 'CE standard image', fill=CAPTION, font=font(16, True))
    y = 84
    for title, a_, b_ in cells:
        d.text((gap, y + a_.height * z // 2), title, fill=CAPTION, font=font(15), anchor='lm')
        sheet.paste(a_.resize((a_.width * z, a_.height * z), Image.NEAREST), (label_w, y))
        sheet.paste(b_.resize((b_.width * z, b_.height * z), Image.NEAREST),
                    (label_w + w + gap, y))
        y += a_.height * z + gap
    d.text((gap, y + 4), 'Resources decoded from each image (exact), 4x; keyed pixels over the '
           'screen behind them. Progress bar composed from 187/188 and knob 220 (light: +166) at '
           'module 27\'s coordinates; CE columns from the inverted ground.', fill=SUB, font=font(13))
    sheet.save(out / 'screens.png')


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
    stock, ce = Fw(a.stock), Fw(a.ce, ce=True)
    ground = fig_player(stock, ce, a.out)
    fig_theater(ce, a.out)
    fig_transport(stock, ce, ground, a.out)
    fig_splash(stock, ce, a.out)
    fig_browser(stock, ce, a.out)
    fig_lockscreen(stock, ce, a.out)
    fig_menus(stock, ce, a.out)
    fig_screens(stock, ce, a.out)
    fig_vorbis(a.out)
    for p in sorted(a.out.glob('*.png')):
        print(p, Image.open(p).size)


if __name__ == '__main__':
    main()
