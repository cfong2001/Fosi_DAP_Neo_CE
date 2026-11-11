#!/usr/bin/env python3
"""Before/after sheet of every antialiased icon, read from the images.

Stock pixels come from DP3_V137.img and CE pixels from
release/DP3_V137_CE.img, so the sheet shows exactly what each image
carries. Keyed pixels (0xF800) are composited over the ground the
sprite is drawn on: the theme ground for the transport glyphs, light
grey for the black mini play state, white for the light speaker.
Opaque icons carry their own ground. Writes mock/icons_before_after.png.
"""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image as FW  # noqa: E402

KEY = 0xF800
GROUPS = (
    ('Transport (keyed, dark ground 0x7222)', [157, 158, 159, 167, 160, 161, 170, 171, 172, 173,
                                              178, 179, 180], 0x7222),
    ('Transport (keyed, light ground 0xBEFA)', [323, 324, 325, 333, 326, 327, 336, 337, 339,
                                               344, 345], 0xBEFA),
    ('Status and browser (opaque)', [39, 143, 144, 262, 263, 264, 266, 309, 310], None),
    ('Battery (dark levels, dark charging over 0x18C3)', [145, 146, 147, 148, 149, 150, 152,
                                                         154], 0x18C3),
    ('Battery (light levels, light charging over white)', [311, 312, 313, 314, 315, 316, 318,
                                                          320], 0xFFFF),
    ('Mini play state over light grey, speaker over white', [189, 190, 355, 356, 298], None),
)
GROUND_FOR = {189: 0xC618, 190: 0xC618, 355: 0xC618, 356: 0xC618, 298: 0xFFFF}


def rgb(v):
    return ((v >> 11) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31)


def tile(raw, e, ground):
    w, h = e['width'], e['height']
    px = struct.unpack_from(f'>{w * h}H', raw, e['data_offset'])
    t = Image.new('RGB', (w, h))
    t.putdata([rgb(ground if v == KEY else v) for v in px])
    return t


def main():
    stock = (ROOT / 'DP3_V137.img').read_bytes()
    ce = (ROOT / 'release' / 'DP3_V137_CE.img').read_bytes()
    S = {e['id']: e for e in FW(stock).images()}
    C = {e['id']: e for e in FW(ce).images()}
    z = 6
    hf = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
    lf = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
    rows = []
    for title, ids, ground in GROUPS:
        pairs = []
        for i in ids:
            g = GROUND_FOR.get(i, ground if ground is not None else 0x7BEF)
            pairs.append((i, tile(stock, S[i], g), tile(ce, C[i], g)))
        rows.append((title, pairs))
    W = 1900
    out = Image.new('RGB', (W, 6000), (128, 128, 128))
    d = ImageDraw.Draw(out)
    y = 10
    d.text((10, y), 'Each pair: stock (left), CE (right), 6x', fill=(240, 240, 240), font=lf)
    y += 24
    for title, pairs in rows:
        d.text((10, y), title, fill=(255, 255, 255), font=hf)
        y += 26
        x, rowh = 10, 0
        for i, a, b in pairs:
            pw = a.width * z * 2 + 16
            if x + pw > W - 10:
                x, y = 10, y + rowh + 8
                rowh = 0
            out.paste(a.resize((a.width * z, a.height * z), Image.NEAREST), (x, y + 16))
            out.paste(b.resize((b.width * z, b.height * z), Image.NEAREST),
                      (x + a.width * z + 4, y + 16))
            d.text((x, y), str(i), fill=(230, 230, 230), font=lf)
            x += pw + 14
            rowh = max(rowh, a.height * z + 20)
        y += rowh + 18
    out = out.crop((0, 0, W, y))
    path = Path(__file__).resolve().parent / 'mock' / 'icons_before_after.png'
    out.save(path)
    print(path)


if __name__ == '__main__':
    main()
