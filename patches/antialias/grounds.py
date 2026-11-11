#!/usr/bin/env python3
"""The baked-antialiasing transport sprites over several grounds.

The keyed draw path lands every non-key pixel as it is, so the fringe
baked into the v4 sprites is exact over the ground it was blended toward
(0x7222, the dark theme default) and approximate elsewhere. This sheet
shows hard-edged (thresholded) and baked sprites over that ground and
over theater grounds a cover could produce. Writes mock/grounds.png.
"""
import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'g', ROOT / 'patches' / 'design_refresh_v4' / 'generate_glyphs.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

NAMES = ('chev-left', 'prev', 'pause', 'next', 'repeat', 'info')
GROUNDS = ((0x7222, 'theme default 0x7222 (baked against)'), (0x0000, 'black cover'),
           (0x18E7, 'dark slate cover'), (0x4A69, 'grey cover'), (0x8800, 'red cover'),
           (0x2C4A, 'teal cover'))


NEUTRAL_DARK = g.FRINGE_DARK   # grey as bright as 0x7222


def tile(name, ground, target):
    c = g.draw_design(name)
    ink = g.ACC_DARK if name == 'info' else g.INK_DARK
    small = c.img.resize((32, 32), Image.BOX)
    t = Image.new('RGB', (32, 32), g.rgb888(ground))
    for i in range(1024):
        cov = small.getpixel((i % 32, i // 32)) / 255
        w = g.bake(ink, target, cov) if target is not None else (ink if cov >= 0.5 else g.KEY)
        if w != g.KEY:
            t.putpixel((i % 32, i // 32), g.rgb888(w))
    return t


def main():
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    z = 3
    row_h = 32 * z + 30
    cols = ((None, 'hard-edged (today)'), (g.GROUND_DARK, 'baked toward 0x7222 (theme ground)'),
            (NEUTRAL_DARK, f'baked toward {g.FRINGE_DARK:#06x} (neutral grey, shipped)'))
    W = 260 + len(cols) * (len(NAMES) * (32 * z + 4) + 10) + 20
    out = Image.new('RGB', (W, 40 + row_h * len(GROUNDS)), (245, 245, 242))
    d = ImageDraw.Draw(out)
    for b, (_, label) in enumerate(cols):
        d.text((260 + b * (len(NAMES) * (32 * z + 4) + 10), 10), label,
               fill=(30, 30, 30), font=f)
    for r, (ground, label) in enumerate(GROUNDS):
        y = 40 + r * row_h
        d.text((10, y + 40), label, fill=(30, 30, 30), font=f)
        for b, (target, _) in enumerate(cols):
            for k, n in enumerate(NAMES):
                x = 260 + b * (len(NAMES) * (32 * z + 4) + 10) + k * (32 * z + 4)
                out.paste(tile(n, ground, target).resize((32 * z, 32 * z), Image.NEAREST),
                          (x, y))
    path = Path(__file__).resolve().parent / 'mock' / 'grounds.png'
    out.save(path)
    print(path)


if __name__ == '__main__':
    main()
